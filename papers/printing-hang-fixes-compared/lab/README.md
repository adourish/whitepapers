# Java 17 or Java 21 lab: would Java 21 fix the kitchen ticket printing waits?

The lab copies a pizza shop's kitchen ticket printing: `notice-app` stands in for the ticket service, which prints kitchen tickets for orders, and `work-data-app` stands in for the order-data service.

**Run on 2026-11-11** on one laptop (14 processors). Numbers are for comparing runs with each other, not for predicting production.

## Round 3: the five options side by side (`opt-*` runs)

- **a. Java 17, no changes:** fine at normal load; froze in a stall (1 of 86 pings in 5 minutes); about 21 s to fail on an address that does not answer.
- **b. Java 17, MVP time limits (2 s connect, 30 s wait):** same speed; down or unreachable fail in 2 s; still froze in a stall (2 of 87).
- **c. Java 21, no changes:** the same as a in all nine scenarios. No faster.
- **d. Java 21, MVP time limits:** the same as b in all nine scenarios. Unaffected by the lock-holding driver (72.6 a second).
- **e. Java 21 virtual, time limits and a circuit breaker:** answered every ping in a stall (587 of 587 in 5 minutes), but fell to 10.2 a second with the lock-holding driver.
- **Java 17, time limits and a circuit breaker:** 530 of 538 pings in a 5-minute stall; frozen only for about the first 30 s. Down and unreachable refused at once; lock-holding driver unaffected (73.3 a second).
- **The circuit breaker must count only time-outs** (`lab.client.breaker.record=timeouts`). Counting every error, it opened under overload and halved good prints (9.6 against 19.2 a second).
- PDF-like work was rerun in one batch for all five: 19.8 to 21.8 a second.
- **Bulkhead on Java 17** (`lab.client.bulkhead`, Resilience4j's counting bulkhead, with time limits and the time-outs-only breaker): a cap of 60 calls to order-data at once answered every ping from the first second of a stall (77 of 77; 588 of 588 over 5 minutes) and lost no prints (overload 19.4, slow 3.6 a second). A cap of 50 was below what order-data takes at once (about 55) and refused good prints (overload 16.3, slow 3.1). Size the cap just above order-data's own limit: where order-data was set up to take 100 at once (lock-holding driver run) or 100 people were busy (PDF-like run), the cap of 60 refused good prints (4,060 and 1,163).

## Round 2 (3 repeats, harder cases) — what changed

Round 2 confirmed round 1 and added these. Full write-up: the white paper [../README.md](../README.md) (a Word copy is in `../exports/`). Table: [results/RESULTS.md](results/RESULTS.md).

- **30-second limits (option A) are not enough on Java 17.** The service still froze during a stall (1 to 2 of 13 pings answered), because each stuck call holds a Tomcat thread for 30 seconds. And 30 s is longer than the front door's 29 s, so people see the front door's error first. Quick reads need short limits; keep 30 s only for the large writes.
- **Slow but valid work (20 s) still succeeds under 30 s limits** (3.4 to 3.6 a second); under a 10 s limit every request failed.
- **5-minute stall on Java 21 virtual:** with no limits, stuck calls grew from 300 to 3,000 and memory from 57 to 456 MB; with limits, flat at 300 and about 160 MB.
- **Connect limit matters:** an address that never answers took about 21 s to fail without one, 2 s with one.
- **Database capped at 40 calls at once:** pool 25, 50, 100 gave 21.2, 31.4, 31.9 a second. A pool past the database's limit adds nothing.
- **Pinning:** with a driver that holds a lock while it waits, Java 21 virtual fell from 72 to 12 a second; Java 17 was unaffected at 72. The pinning trace reported it.
- **PDF-like work** (rerun in one batch): Java 17 21.1, Java 21 G1 20.7, ZGC 20.0, Java 21 virtual 20.0 a second. No gain. Compare processor-heavy runs only within one batch; the laptop varies.
- **Fill-in runs (`fill-*`), so every cell of the white paper table is measured.** Java 17 with a 10 s limit during a stall: every request ends at 10 s with a clear error, but only 6 of 14 pings answered. Java 21 virtual: 77 of 77. Java 17, 5-minute stall with 30 s limits: froze (2 of 87). Pinning with limits: 13.1 a second on 21 virtual, 73.2 on 17. Down and unreachable behave the same on both versions.
- **Mixed versions** (ticket on 21 virtual, order-data on 17) ran normally.

## In short (round 1)

- **Java 21 on its own changed nothing on this waiting-bound path.** The same apps gave the same throughput on Java 17, Java 21, and Java 21 with virtual threads (12.3 a second in every case). The lab does almost no processor work, so it says nothing about work that keeps the processor busy, such as making PDFs, where Java 21's faster garbage collection could help.
- **Virtual threads stop the ticket service freezing when order-data stops answering, but they don't fix the calls.**
  - Java 17: the service froze, and 11 of 12 pings failed.
  - Java 21 with virtual threads: every ping was answered, but every print request still hung until the person gave up.
  - The abandoned calls also piled up inside the service: 600 after 40 seconds, and the count only grows.
- **A time limit on the call (the change request) is the fix, on either Java.** With a 10-second limit, every request ended with a clear "gave up" (HTTP 504).
  - On Java 17 the service still froze while more than 200 requests (Tomcat's thread limit) were each waiting their 10 seconds.
  - On Java 21 with virtual threads it stayed responsive.
- **The real limits are `printNoticeExecutor` and the database pool, not the Java version.**
  - The executor runs only 15 at a time until its queue of 30 fills. Beyond that it refuses the work, on any Java.
  - With the executor removed, throughput followed the database pool size exactly:

    | Database pool | Answered a second |
    |---:|---:|
    | 10 | 10 |
    | 25 | 21 |
    | 50 | 38 |
    | 100 | 70 |

- **Trap: Apache HttpClient's default pool allows 5 connections per address.** Switching the client to it without raising that limit cut throughput from 70 to 6.7 a second, with a middle wait of 27 seconds.
- **Not tested: the Oracle driver.** H2 stands in for Oracle, so this lab cannot show "pinning". Older Oracle drivers, such as the shop's `ojdbc8` 19.3, hold locks while waiting on the network. On Java 21 a virtual thread holding such a lock is stuck to one of the few real threads underneath until Java 24, and that could cancel the benefit. No pinning was seen here, with the H2 driver. This must be tested against the dev Oracle database before choosing virtual threads.

## What it is

Two small Spring Boot 3.2.4 apps (the same Spring Boot as the shop's live services), compiled for Java 17 so the same jars run on both JDKs.

| Part | Stands in for | Shaped like |
|---|---|---|
| `notice-app` | The ticket service | `generatePrintNotices` calls order-data to make the tickets, then to mark them printed, as the real ticket service's print code does. The client is today's shared client with no limits (`CommonRestTemplateConfig.java:84-98`), or one with limits, or Apache HttpClient 5 with a pool |
| `work-data-app` | The order-data service | `createNotices` hands the work to `printNoticeExecutor` (15 core, 25 max, 30 queued, refuses when full; `AsyncConfig.java:21-34`) and waits, as the real order-data print controller does. A Hikari pool of 25 with a 30-second wait (`application.properties:74-79`). Each ticket makes 4 database round trips |
| H2 server | The shop's database (Oracle) | A separate process. `WAN_SLEEP(60)` makes each round trip take 60 ms, as the WAN does (40 to 80 ms) |
| `loadtest/LoadTest.java` | People pressing Print | Each person waits up to 29 seconds, like the cloud front door. A probe asks the ticket app for a page that calls nothing, twice a second, to see whether it can still answer |

## Results

The full table is in [results/RESULTS.md](results/RESULTS.md), and the raw numbers are in [results/results.json](results/results.json).

| Run | Java | Answered a second | Middle wait | Pings answered | What it shows |
|---|---|---:|---:|---:|---|
| Normal, 40 people | 17 / 21 / 21 virtual | 12.3 / 12.3 / 12.3 | 3.8 s | all | No difference. 12.3 a second matches 15 running at once (15 ÷ 1.26 s each): the executor grows past 15 only when its queue of 30 is full |
| Overload, 150 people | 17 / 21 virtual | 17.9 / 18.4 | 3.5 / 4.1 s | all | Same. The executor refused the rest of the work on both. The count of refusals (58,446 and 34,290) is not comparable: a refused person asks again at once, so it measures how fast they retried |
| Order-data stalls, no limit | 17 | 0 | – | 1 of 12 | The ticket service froze. It also returned 97 "gave up" errors and 7 refused connections that this lab cannot yet explain |
| Order-data stalls, no limit | 21 virtual | 0 | – | 77 of 77 | Still answering, but 600 stuck calls piled up |
| Order-data stalls, 10 s limit | 17 | 0 (900 clean "gave up") | – | 4 of 13 | Fails cleanly, but froze while more than 200 requests were waiting |
| Order-data stalls, 10 s limit | 21 virtual | 0 (1,200 clean "gave up") | – | 77 of 77 | Fails cleanly and stays responsive |
| No executor, 200 people, pool 25 | 17 / 21 virtual | 21.4 / 20.8 | 9.2 / 9.3 s | all | The database pool is the limit, the same on both |
| No executor, 200 people, pool 10 / 50 / 100 | 21 virtual | 10.1 / 38.3 / 70.5 | 21.2 / 4.8 / 2.7 s | all | Throughput follows the pool size |
| HTTP client: simple / Apache default / Apache 100 per address | 21 virtual | 70.0 / 6.7 / 70.0 | 1.4 / 26.9 / 1.4 s | all | Apache's default 5 per address strangles it |

## What this means for the shop's services

1. **Add the time limits from the change request first.** It fixes the hanging calls on Java 17 or 21. Nothing else here does.
2. **Upgrade to Java 21 for support and security, not speed, on the waiting parts.** On its own it changed no number in this lab. Its effect on PDF generation is untested.
3. **Virtual threads are a setting, not code:** `spring.threads.virtual.enabled=true` on Java 21. They help a service stay responsive while it waits.
   - They are only worth it after the time limits are in, and after a test with the real Oracle driver.
   - They don't get past `printNoticeExecutor` or the database pool.
   - With Tomcat's 200-thread cap gone, more requests reach the database pool at once.
4. **Raising the database pool helps throughput only while Oracle can take the extra sessions.** On-prem database capacity is unknown, so agree any pool change with the DBA (database administrator).
5. **If a client is switched to Apache HttpClient** (for example to add time limits), raise its per-address limit above the default 5.

## Still to test

- **The real Oracle driver** (`ojdbc8` 19.3, and a newer one such as `ojdbc11` 21.9) against the shop's test database, using `SELECT 1 FROM dual` in place of `WAN_SLEEP`, with `-Djdk.tracePinnedThreads=short`.
- **The parallel groups inside "make the tickets"**, which this lab leaves out. Each request here works through its tickets one after another.

## How to run it

```
JAVA_HOME=<JDK 21> mvn -q package -DskipTests     # builds both apps
python run_lab.py                                 # every run, about 3 hours
python run_lab.py stall                           # only the stall runs
```

`run_lab.py` expects JDK 17 at `~\tools\jdk-17.0.21+9` and JDK 21 at `C:\Program Files\Java\jdk-21.0.12.1`. Set `JDK17` and `JDK21` to change these. Each run starts a fresh pair of apps, and the app logs go to `results/logs/`, which git ignores.
