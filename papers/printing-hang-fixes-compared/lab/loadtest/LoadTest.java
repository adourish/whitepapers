import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Closed-loop load: N people press Print over and over until the time is up. Each waits up to
 * --timeout seconds, like the cloud front door's 29 seconds. At the same time a probe asks the
 * ticket service (notice-app) for /ping every half second, which calls nothing, to see whether the service can
 * still answer at all. Stats from both apps are sampled every 2 seconds and the peaks kept.
 *
 *   java LoadTest.java --url http://localhost:18084/notice/api/generatePrintNotices?notices=5
 *        --users 100 --seconds 30 --timeout 29 --probe http://localhost:18084/notice/api/ping
 *        --stats http://localhost:18084/admin/stats,http://localhost:18093/admin/stats --out r.json
 */
public class LoadTest {
    public static void main(String[] a) throws Exception {
        Map<String, String> arg = new TreeMap<>();
        for (int i = 0; i + 1 < a.length; i += 2) arg.put(a[i].replace("--", ""), a[i + 1]);
        String url = arg.get("url");
        int users = Integer.parseInt(arg.getOrDefault("users", "50"));
        int seconds = Integer.parseInt(arg.getOrDefault("seconds", "30"));
        int timeout = Integer.parseInt(arg.getOrDefault("timeout", "29"));
        String probe = arg.get("probe");
        String[] stats = arg.getOrDefault("stats", "").split(",");
        // a person who gets an error waits this long before pressing Print again
        long pauseAfterError = Long.parseLong(arg.getOrDefault("pause-after-error-ms", "1000"));
        // stats to keep every 2 seconds, not only the peak, such as notice.inFlight
        List<String> seriesKeys = List.of(arg.getOrDefault("series", "").split(","));
        Map<String, List<Long>> series = new ConcurrentHashMap<>();

        ExecutorService pool = Executors.newFixedThreadPool(users + 4);
        HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).executor(pool).build();
        long end = System.currentTimeMillis() + seconds * 1000L;

        List<Long> okMs = Collections.synchronizedList(new ArrayList<>());
        Map<String, AtomicInteger> outcomes = new ConcurrentHashMap<>();
        AtomicInteger probeOk = new AtomicInteger(), probeFail = new AtomicInteger();
        AtomicLong probeMax = new AtomicLong();
        Map<String, Long> peaks = new ConcurrentHashMap<>();
        Map<String, String> last = new ConcurrentHashMap<>();

        List<Thread> workers = new ArrayList<>();
        for (int u = 0; u < users; u++) {
            Thread t = new Thread(() -> {
                while (System.currentTimeMillis() < end) {
                    long s = System.nanoTime();
                    String key;
                    try {
                        HttpResponse<String> r = client.send(HttpRequest.newBuilder(URI.create(url))
                                .timeout(Duration.ofSeconds(timeout)).POST(HttpRequest.BodyPublishers.noBody()).build(),
                                HttpResponse.BodyHandlers.ofString());
                        key = "HTTP " + r.statusCode();
                        if (r.statusCode() == 200) okMs.add((System.nanoTime() - s) / 1_000_000);
                    } catch (HttpTimeoutException e) {
                        key = "person gave up at " + timeout + " s";
                    } catch (Exception e) {
                        key = e.getClass().getSimpleName();
                    }
                    outcomes.computeIfAbsent(key, k -> new AtomicInteger()).incrementAndGet();
                    if (!"HTTP 200".equals(key)) sleep(pauseAfterError);
                }
            });
            t.start();
            workers.add(t);
        }

        Thread prober = new Thread(() -> {
            while (System.currentTimeMillis() < end) {
                long s = System.nanoTime();
                try {
                    HttpResponse<String> r = client.send(HttpRequest.newBuilder(URI.create(probe))
                            .timeout(Duration.ofSeconds(3)).GET().build(), HttpResponse.BodyHandlers.ofString());
                    if (r.statusCode() == 200) probeOk.incrementAndGet(); else probeFail.incrementAndGet();
                } catch (Exception e) {
                    probeFail.incrementAndGet();
                }
                probeMax.accumulateAndGet((System.nanoTime() - s) / 1_000_000, Math::max);
                sleep(500);
            }
        });
        Thread sampler = new Thread(() -> {
            Pattern num = Pattern.compile("\"(\\w+)\":(\\d+)");
            while (System.currentTimeMillis() < end + 1000) {
                for (int i = 0; i < stats.length; i++) {
                    if (stats[i].isBlank()) continue;
                    try {
                        String body = client.send(HttpRequest.newBuilder(URI.create(stats[i]))
                                .timeout(Duration.ofSeconds(3)).GET().build(), HttpResponse.BodyHandlers.ofString()).body();
                        last.put(i == 0 ? "notice" : "workData", body);
                        Matcher m = num.matcher(body);
                        while (m.find()) {
                            String k = (i == 0 ? "notice." : "workData.") + m.group(1);
                            peaks.merge(k, Long.parseLong(m.group(2)), Math::max);
                            if (seriesKeys.contains(k)) series.computeIfAbsent(k, x -> Collections.synchronizedList(new ArrayList<>())).add(Long.parseLong(m.group(2)));
                        }
                    } catch (Exception e) {
                        peaks.merge(i == 0 ? "notice.statsUnanswered" : "workData.statsUnanswered", 1L, Long::sum);
                    }
                }
                sleep(2000);
            }
        });
        if (probe != null) prober.start();
        sampler.start();
        for (Thread t : workers) t.join((seconds + timeout + 10) * 1000L);
        prober.join(10_000);
        sampler.join(10_000);

        List<Long> sorted = new ArrayList<>(okMs);
        Collections.sort(sorted);
        StringBuilder j = new StringBuilder("{");
        j.append("\"users\":").append(users).append(",\"seconds\":").append(seconds).append(",\"timeout\":").append(timeout);
        j.append(",\"ok\":").append(sorted.size());
        j.append(",\"okPerSecond\":").append(String.format("%.1f", sorted.size() / (double) seconds));
        j.append(",\"p50\":").append(pct(sorted, 50)).append(",\"p95\":").append(pct(sorted, 95)).append(",\"max\":").append(pct(sorted, 100));
        j.append(",\"outcomes\":{");
        String sep = "";
        for (Map.Entry<String, AtomicInteger> e : new TreeMap<>(outcomes).entrySet()) {
            j.append(sep).append('"').append(e.getKey()).append("\":").append(e.getValue().get());
            sep = ",";
        }
        j.append("},\"probeOk\":").append(probeOk.get()).append(",\"probeFail\":").append(probeFail.get());
        j.append(",\"probeMaxMs\":").append(probeMax.get()).append(",\"peaks\":{");
        sep = "";
        for (Map.Entry<String, Long> e : new TreeMap<>(peaks).entrySet()) {
            j.append(sep).append('"').append(e.getKey()).append("\":").append(e.getValue());
            sep = ",";
        }
        j.append("},\"series\":{");
        sep = "";
        for (Map.Entry<String, List<Long>> e : new TreeMap<>(series).entrySet()) {
            j.append(sep).append('"').append(e.getKey()).append("\":").append(e.getValue());
            sep = ",";
        }
        j.append("}}");
        System.out.println(j);
        if (arg.containsKey("out")) java.nio.file.Files.writeString(java.nio.file.Path.of(arg.get("out")), j.toString());
        pool.shutdownNow();
        pool.awaitTermination(2, TimeUnit.SECONDS);
        System.exit(0);
    }

    static long pct(List<Long> s, int p) {
        if (s.isEmpty()) return -1;
        return s.get(Math.min(s.size() - 1, (int) Math.ceil(p / 100.0 * s.size()) - 1));
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
