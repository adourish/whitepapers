package lab.workdata;

import java.lang.management.ManagementFactory;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;
import java.util.zip.Deflater;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.atomic.AtomicInteger;

import javax.sql.DataSource;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.TaskRejectedException;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariPoolMXBean;

/**
 * Stands in for the order-data service on a pizza shop's kitchen ticket printing path.
 *
 * Shaped like the real one:
 * - createNotices hands the work to "printNoticeExecutor" and waits for it, as
 *   the real order-data print controller does. Same pool shape as AsyncConfig.java:21-34:
 *   15 core, 25 max, 30 queued, and a full pool refuses the work (AbortPolicy).
 * - Each notice borrows one database connection from a Hikari pool of 25 with a 30-second wait,
 *   as application.properties:74-79 sets, and makes several round trips on it.
 * - Each round trip is a call to WAN_SLEEP on a separate H2 server, so the thread waits on a
 *   socket for the West Coast round trip, as it does with Oracle.
 *
 * The executor is here to copy today's code, not as a pattern to follow.
 */
@SpringBootApplication
public class WorkDataApp {
    public static void main(String[] args) {
        SpringApplication.run(WorkDataApp.class, args);
    }
}

@Configuration
class WorkDataConfig {
    @Bean(name = "printNoticeExecutor")
    ThreadPoolTaskExecutor printNoticeExecutor(@Value("${lab.executor.core:15}") int core,
                                               @Value("${lab.executor.max:25}") int max,
                                               @Value("${lab.executor.queue:30}") int queue) {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(core);
        executor.setMaxPoolSize(max);
        executor.setQueueCapacity(queue);
        executor.setThreadNamePrefix("Print-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.AbortPolicy());
        executor.initialize();
        return executor;
    }
}

@RestController
class WorkDataController {
    private final DataSource dataSource;
    private final ThreadPoolTaskExecutor executor;
    private final String mode;
    private final int latencyMs;
    private final int roundTrips;
    private final boolean holdLock;
    private final int cpuKb;

    private volatile boolean stall;
    private volatile long stallMs = 600_000;

    private final AtomicInteger inFlight = new AtomicInteger();
    private final AtomicInteger peakInFlight = new AtomicInteger();
    private final AtomicInteger rejected = new AtomicInteger();
    private final AtomicInteger poolTimeouts = new AtomicInteger();
    private final AtomicInteger peakPoolWaiting = new AtomicInteger();
    private final AtomicInteger peakPoolActive = new AtomicInteger();

    WorkDataController(DataSource dataSource, ThreadPoolTaskExecutor executor,
                       @Value("${lab.workdata.mode:executor}") String mode,
                       @Value("${lab.db.latency-ms:60}") int latencyMs,
                       @Value("${lab.db.round-trips-per-notice:4}") int roundTrips,
                       @Value("${lab.db.hold-lock:false}") boolean holdLock,
                       @Value("${lab.cpu.kb-per-notice:0}") int cpuKb) throws SQLException {
        this.dataSource = dataSource;
        this.executor = executor;
        this.mode = mode;
        this.latencyMs = latencyMs;
        this.roundTrips = roundTrips;
        this.holdLock = holdLock;
        this.cpuKb = cpuKb;
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement()) {
            st.execute("CREATE ALIAS IF NOT EXISTS WAN_SLEEP FOR 'lab.workdata.WanSleep.sleep'");
        }
    }

    /** "Make the tickets": the call the ticket service (notice-app) waits on (call 1 of 3). */
    @PostMapping("/api/print-notices/createNotices")
    ResponseEntity<Map<String, Object>> createNotices(@RequestParam(defaultValue = "5") int notices) throws InterruptedException {
        peakInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
        try {
            if (stall) {
                Thread.sleep(stallMs);      // a service that has stopped answering
            }
            if ("inline".equals(mode)) {
                return ResponseEntity.ok(makeNotices(notices));
            }
            try {
                return ResponseEntity.ok(CompletableFuture.supplyAsync(() -> makeNotices(notices), executor).join());
            } catch (TaskRejectedException e) {
                rejected.incrementAndGet();
                return ResponseEntity.status(503).body(Map.of("error", "printNoticeExecutor full"));
            }
        } catch (CompletionException | IllegalStateException e) {
            return ResponseEntity.status(503).body(Map.of("error", String.valueOf(e.getCause() != null ? e.getCause() : e)));
        } finally {
            inFlight.decrementAndGet();
        }
    }

    /** "Mark the notices printed" (call 3 of 3): one round trip. */
    @PostMapping("/api/print-notices/updateNotices")
    Map<String, Object> updateNotices() {
        roundTrip(1);
        return Map.of("updated", true);
    }

    private Map<String, Object> makeNotices(int notices) {
        for (int i = 0; i < notices; i++) {
            roundTrip(roundTrips);
            if (cpuKb > 0) {
                pdfLikeWork(cpuKb);
            }
        }
        return Map.of("notices", notices);
    }

    private void roundTrip(int times) {
        HikariPoolMXBean pool = ((HikariDataSource) dataSource).getHikariPoolMXBean();
        peakPoolWaiting.accumulateAndGet(pool.getThreadsAwaitingConnection(), Math::max);
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement()) {
            peakPoolActive.accumulateAndGet(pool.getActiveConnections(), Math::max);
            if (holdLock) {
                // Older JDBC drivers, such as ojdbc8 19.3, hold a lock on the connection while they
                // wait for the database. On Java 21 a virtual thread waiting inside a lock is
                // "pinned": it keeps one of the few carrier threads busy until the answer comes.
                synchronized (c) {
                    for (int r = 0; r < times; r++) {
                        st.execute("CALL WAN_SLEEP(" + latencyMs + ")");
                    }
                }
            } else {
                for (int r = 0; r < times; r++) {
                    st.execute("CALL WAN_SLEEP(" + latencyMs + ")");
                }
            }
        } catch (SQLException e) {
            poolTimeouts.incrementAndGet();     // Hikari gave up waiting for a connection
            throw new IllegalStateException("no database connection: " + e.getMessage(), e);
        }
    }

    /** Processor work shaped like building a PDF page: lots of short text, then compressed. */
    static int pdfLikeWork(int kb) {
        StringBuilder sb = new StringBuilder(kb * 1024 + 128);
        ThreadLocalRandom r = ThreadLocalRandom.current();
        while (sb.length() < kb * 1024) {
            sb.append("BT /F1 10 Tf 72 ").append(r.nextInt(720)).append(" Td (Notice line ").append(r.nextLong()).append(") Tj ET\n");
        }
        byte[] in = sb.toString().getBytes(java.nio.charset.StandardCharsets.ISO_8859_1);
        Deflater d = new Deflater();
        d.setInput(in);
        d.finish();
        byte[] out = new byte[in.length];
        int n = d.deflate(out);
        d.end();
        return n;
    }

    @GetMapping("/api/ping")
    Map<String, Object> ping() {
        return Map.of("ok", true);
    }

    @PostMapping("/admin/stall")
    Map<String, Object> stall(@RequestParam boolean on, @RequestParam(defaultValue = "600000") long ms) {
        stall = on;
        stallMs = ms;
        return Map.of("stall", on, "ms", ms);
    }

    @GetMapping("/admin/stats")
    Map<String, Object> stats() {
        HikariPoolMXBean pool = ((HikariDataSource) dataSource).getHikariPoolMXBean();
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("java", Runtime.version().toString());
        m.put("virtualThreads", Thread.currentThread().toString().contains("Virtual"));
        m.put("mode", mode);
        m.put("inFlight", inFlight.get());
        m.put("peakInFlight", peakInFlight.get());
        m.put("executorRejected", rejected.get());
        m.put("poolTimeouts", poolTimeouts.get());
        m.put("poolSize", ((HikariDataSource) dataSource).getMaximumPoolSize());
        m.put("peakPoolActive", peakPoolActive.get());
        m.put("peakPoolWaiting", peakPoolWaiting.get());
        m.put("poolActiveNow", pool.getActiveConnections());
        m.put("heapUsedMb", ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed() / 1_048_576);
        m.put("platformThreads", ManagementFactory.getThreadMXBean().getThreadCount());
        m.put("peakPlatformThreads", ManagementFactory.getThreadMXBean().getPeakThreadCount());
        return m;
    }
}
