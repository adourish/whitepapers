package lab.notice;

import java.lang.management.ManagementFactory;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.bulkhead.BulkheadConfig;
import io.github.resilience4j.bulkhead.BulkheadFullException;
import io.github.resilience4j.circuitbreaker.CallNotPermittedException;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import org.apache.hc.client5.http.config.ConnectionConfig;
import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManagerBuilder;
import org.apache.hc.core5.util.Timeout;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

/**
 * Stands in for the ticket service, which prints a pizza shop's kitchen tickets: generatePrintNotices
 * calls work-data (the order-data service) to make the tickets, then to mark them printed.
 *
 * The client is built three ways, chosen per run:
 * - simple, no limits: today's shared client (CommonRestTemplateConfig.java:84-98)
 * - simple, with limits: option A of the change request
 * - pooled: Apache HttpClient 5 with a connection pool, to show its pool limits
 */
@SpringBootApplication
public class NoticeApp {
    public static void main(String[] args) {
        SpringApplication.run(NoticeApp.class, args);
    }
}

@Configuration
class ClientConfig {
    static volatile PoolingHttpClientConnectionManager pool;

    @Bean
    RestTemplate workDataRestTemplate(@Value("${lab.client.kind:simple}") String kind,
                                      @Value("${lab.client.connect-timeout-ms:0}") int connectMs,
                                      @Value("${lab.client.read-timeout-ms:0}") int readMs,
                                      @Value("${lab.client.pool.max-total:25}") int maxTotal,
                                      @Value("${lab.client.pool.max-per-route:5}") int maxPerRoute,
                                      @Value("${lab.client.pool.wait-ms:180000}") int poolWaitMs) {
        if ("pooled".equals(kind)) {
            // 25 in all and 5 per address are HttpClient 5's own defaults; 3 minutes is its default
            // wait for a free connection
            ConnectionConfig.Builder cc = ConnectionConfig.custom();
            if (connectMs > 0) cc.setConnectTimeout(Timeout.ofMilliseconds(connectMs));
            if (readMs > 0) cc.setSocketTimeout(Timeout.ofMilliseconds(readMs));
            pool = PoolingHttpClientConnectionManagerBuilder.create()
                    .setMaxConnTotal(maxTotal)
                    .setMaxConnPerRoute(maxPerRoute)
                    .setDefaultConnectionConfig(cc.build())
                    .build();
            RequestConfig rc = RequestConfig.custom()
                    .setConnectionRequestTimeout(Timeout.ofMilliseconds(poolWaitMs)).build();
            return new RestTemplate(new HttpComponentsClientHttpRequestFactory(
                    HttpClients.custom().setConnectionManager(pool).setDefaultRequestConfig(rc).build()));
        }
        SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
        if (connectMs > 0) f.setConnectTimeout(connectMs);
        if (readMs > 0) f.setReadTimeout(readMs);
        return new RestTemplate(f);
    }
}

@RestController
class NoticeController {
    private final RestTemplate rest;
    private final String workData;

    private final AtomicInteger inFlight = new AtomicInteger();
    private final AtomicInteger peakInFlight = new AtomicInteger();
    private final AtomicInteger gaveUp = new AtomicInteger();
    private final AtomicInteger downstreamErrors = new AtomicInteger();

    private final AtomicInteger breakerRefused = new AtomicInteger();
    private final CircuitBreaker breaker;     // null when lab.client.breaker=false
    private final AtomicInteger bulkheadRefused = new AtomicInteger();
    private final Bulkhead bulkhead;          // null when lab.client.bulkhead=0

    NoticeController(RestTemplate rest, @Value("${lab.work-data.url:http://localhost:18093}") String workData,
                     @Value("${lab.client.breaker:false}") boolean useBreaker,
                     @Value("${lab.client.breaker.record:all}") String record,
                     @Value("${lab.client.bulkhead:0}") int bulkheadMax) {
        this.rest = rest;
        this.workData = workData;
        // Resilience4j defaults, except a smaller window so it reacts within a few seconds: after 10 calls,
        // if half or more failed, stop calling work-data for 5 seconds, then let 3 calls through to test it.
        // Slow calls that succeed do not count, so valid 20-second writes never open it.
        CircuitBreakerConfig.Builder cfg = CircuitBreakerConfig.custom()
                .failureRateThreshold(50)
                .slidingWindowSize(20)
                .minimumNumberOfCalls(10)
                .waitDurationInOpenState(Duration.ofSeconds(5))
                .permittedNumberOfCallsInHalfOpenState(3);
        // "timeouts": only time-outs and failed connections count, so work-data saying "too busy" does not open it
        if ("timeouts".equals(record)) cfg.recordExceptions(ResourceAccessException.class);
        this.breaker = useBreaker ? CircuitBreaker.of("work-data", cfg.build()) : null;
        // Counting bulkhead: at most bulkheadMax calls to work-data in progress at once; one more fails at once
        // instead of waiting. It runs on the caller's thread and starts no threads of its own.
        this.bulkhead = bulkheadMax > 0 ? Bulkhead.of("work-data", BulkheadConfig.custom()
                .maxConcurrentCalls(bulkheadMax).maxWaitDuration(Duration.ZERO).build()) : null;
    }

    @PostMapping("/notice/api/generatePrintNotices")
    ResponseEntity<Map<String, Object>> generatePrintNotices(@RequestParam(defaultValue = "5") int notices) {
        peakInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
        long start = System.nanoTime();
        Runnable calls = () -> {
            rest.postForObject(workData + "/api/print-notices/createNotices?notices=" + notices, null, Map.class);
            rest.postForObject(workData + "/api/print-notices/updateNotices", null, Map.class);
        };
        try {
            // the bulkhead sits outside the breaker, so a call it refuses never counts for or against the breaker
            Runnable guarded = breaker == null ? calls : () -> breaker.executeRunnable(calls);
            if (bulkhead != null) bulkhead.executeRunnable(guarded); else guarded.run();
            return ResponseEntity.ok(Map.of("ms", (System.nanoTime() - start) / 1_000_000));
        } catch (BulkheadFullException e) {
            // already as many calls to work-data in progress as allowed
            bulkheadRefused.incrementAndGet();
            return ResponseEntity.status(503).body(Map.of("error", "WORK_DATA_CALL_LIMIT_REACHED"));
        } catch (CallNotPermittedException e) {
            // the breaker is open: fail at once without calling work-data
            breakerRefused.incrementAndGet();
            return ResponseEntity.status(503).body(Map.of("error", "WORK_DATA_UNAVAILABLE"));
        } catch (ResourceAccessException e) {
            // the client's own limit ran out (read, connect, or waiting for a pooled connection)
            gaveUp.incrementAndGet();
            return ResponseEntity.status(504).body(Map.of("error", "OUTBOUND_CALL_GAVE_UP " + e.getMessage()));
        } catch (HttpStatusCodeException e) {
            downstreamErrors.incrementAndGet();
            return ResponseEntity.status(502).body(Map.of("error", "work-data answered " + e.getStatusCode()));
        } finally {
            inFlight.decrementAndGet();
        }
    }

    /** Does not call anything: shows whether this service can still answer at all. */
    @GetMapping("/notice/api/ping")
    Map<String, Object> ping() {
        return Map.of("ok", true);
    }

    @GetMapping("/admin/stats")
    Map<String, Object> stats() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("java", Runtime.version().toString());
        m.put("virtualThreads", Thread.currentThread().toString().contains("Virtual"));
        m.put("inFlight", inFlight.get());
        m.put("peakInFlight", peakInFlight.get());
        m.put("gaveUp", gaveUp.get());
        m.put("downstreamErrors", downstreamErrors.get());
        m.put("breakerRefused", breakerRefused.get());
        m.put("bulkheadRefused", bulkheadRefused.get());
        m.put("heapUsedMb", ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed() / 1_048_576);
        m.put("platformThreads", ManagementFactory.getThreadMXBean().getThreadCount());
        m.put("peakPlatformThreads", ManagementFactory.getThreadMXBean().getPeakThreadCount());
        if (ClientConfig.pool != null) {
            m.put("httpPoolLeased", ClientConfig.pool.getTotalStats().getLeased());
            m.put("httpPoolPending", ClientConfig.pool.getTotalStats().getPending());
        }
        return m;
    }
}
