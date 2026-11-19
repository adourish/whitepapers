# Stopping the Kitchen Ticket Hang: Java 21, Time Limits, Circuit Breakers and Bulkheads Compared

## A lab test of seven options, from the Java 21 upgrade to configuration-only changes on Java 17

**Classification:** Internal: Engineering Reference
**Prepared by:** the engineering team
**Date:** 2026-11-12
**Version:** 1.7
**Status:** Published
**System:** a pizza shop's kitchen ticket printing path (the ticket service calling the order-data service)
**Related work:** the change request to add time limits to outbound calls, and the ordering system's performance review
**Lab code:** [lab/](lab/)
**Raw results:** [lab/results/results.json](lab/results/results.json)

---

## Executive summary

This paper is about a pizza shop's ordering system. When an order comes in, staff press Print to print the kitchen tickets. People pressing Print sometimes wait until the cloud front door gives up at 29 seconds and shows an error (HTTP 504, "the server took too long"). Behind that error, the ticket service is waiting on the order-data service with **no time limit at all**. The team asked whether moving from Java 17 to Java 21, whose new "virtual threads" make waiting cheaper, would fix this.

We built two small apps shaped like the real print path and ran 113 scenarios, 233 runs in all, on both Java versions, with and without time limits, and with a circuit breaker and a bulkhead. Every cell of the tables below was measured.

**The answer: time limits fix the hang, and they work on Java 17. Java 21 does not fix it on its own.**

- **Java 21 made nothing faster.** Normal load, overload and PDF-like work gave the same numbers on both versions, within run-to-run variation.
- **Java 21's virtual threads keep the service alive when order-data stops answering, but no print finishes.** Without limits, the stuck calls pile up without end: 3,000 calls and 456 MB of memory after 5 minutes.
- **Time limits are what end the hang.** Every scenario that ends cleanly has a time limit in it.
- **On Java 17, time limits make the failure clean and short, but they cannot keep the service fully responsive during a full stall.** Each stuck call holds one of Tomcat's 200 worker threads until its limit runs out. With a 30-second limit the service froze, as it does with no limit. With a 10-second limit every request ended at 10 s with a clear error, but only 6 of 14 health checks were answered while order-data was stalled. Quick calls need short limits: the shorter the limit, the less of the service a stall takes.
- **Java 21 virtual threads carry a new risk.** With a database driver that holds a lock while it waits, as older Oracle drivers do, throughput fell from 72 to 12 a second. Java 17 was not affected.
- **Plain Java 21, without virtual threads, behaves exactly like Java 17** in all nine scenarios of the options table, with or without time limits.
- **A circuit breaker keeps Java 17 answering through a long stall** (530 of 538 health checks in 5 minutes), with no Java upgrade. It must count only time-outs and failed connections: set to count every error, it halved good prints under overload.
- **A bulkhead closes the last gap on Java 17.** Capping calls to order-data in progress at once at 60 kept every health check answered from the first second of a stall (77 of 77, and 588 of 588 over 5 minutes), with no loss of prints under normal load, overload or slow work. The cap must sit just above what order-data can take at once: where order-data took more, the cap refused good prints. Java 17 with time limits, a circuit breaker and a bulkhead did as well as Java 21 with virtual threads, without the lock risk.

### Team assessment and recommendations

Each engineering team member chooses a first, second and third pick from options a to g in the results table below, and gives the reason for the order. In the Word copy, each pick is a list to choose from and the rationale is a box to type in.

**What the lab results point to:** option b now, then f and g (the circuit breaker, then the bulkhead), all on Java 17. Upgrade to Java 21 for support and security, and turn on virtual threads only after a test with the shop's real Oracle driver.
**Status:** Published

| Member | First pick | Second pick | Third pick | Rationale |
|---|---|---|---|---|
| Member 1 | | | | |
| Member 2 | | | | |
| Member 3 | | | | |
| Member 4 | | | | |
| Member 5 | | | | |
| Member 6 | | | | |
| Member 7 | | | | |

### Results by option

**The options:**
- **a.** Stay on Java 17, change nothing.
- **b.** Stay on Java 17 and add the MVP time limits: 2 s to connect, 30 s to wait on the print path (option A of the change request).
- **c.** Upgrade to Java 21 and change nothing (virtual threads off).
- **d.** Upgrade to Java 21 and add the same time limits as b.
- **e.** Upgrade to Java 21, turn on virtual threads, and add the same time limits and a circuit breaker.
- **f.** Stay on Java 17 and add the time limits and a circuit breaker.
- **g.** Stay on Java 17 and add the time limits, a circuit breaker and a bulkhead.

The **circuit breaker** (Resilience4j 2.2.0) watches the last 20 calls to order-data. Once 10 or more have been made and half of them failed, it stops calling order-data for 5 seconds and answers every print at once with a named error ("service unavailable", HTTP 503, `WORK_DATA_UNAVAILABLE`). Then it lets 3 calls through to test whether order-data is back. **It counts only time-outs and failed connections.** A first version that counted every error opened under overload, because order-data's "too busy" refusals counted as failures, and good prints fell from 19.2 to 9.6 a second on both Java versions.

The **bulkhead** caps how many calls to order-data can be in progress at once, here 60. One more call fails at once with a named error ("service unavailable", HTTP 503, `WORK_DATA_CALL_LIMIT_REACHED`) instead of waiting, so a stall can hold only 60 of Tomcat's 200 worker threads. It is Resilience4j's counting bulkhead, which starts no threads of its own. Section K of the detailed results shows how the cap was sized.

**How to read the table:**
- **PASS:** prints succeed, or fail fast with a clear error, and the service keeps answering.
- **PARTIAL:** the service keeps answering, but people still wait until they give up, or good work is refused.
- **FAIL:** the service freezes, slows sharply, or grows without limit.
- Numbers are prints answered a second, unless the cell says otherwise.
- A **health check** is a simple request, sent twice a second, that calls nothing else. It shows whether the service can answer at all.

| Scenario | a. Java 17, no changes | b. Java 17, time limits | c. Java 21, no changes | d. Java 21, time limits | e. Java 21 virtual threads, time limits, breaker | f. Java 17, time limits, breaker | g. Java 17, time limits, breaker, bulkhead |
|---|---|---|---|---|---|---|---|
| **1. Normal load** (40 people) | **PASS**: 12.3 | **PASS**: 12.4 | **PASS**: 12.4 | **PASS**: 12.3 | **PASS**: 12.3 | **PASS**: 12.3 | **PASS**: 12.8; none refused |
| **2. Overload** (150 people) | **PARTIAL**: 18.7; the rest refused | **PARTIAL**: 19.2 | **PARTIAL**: 19.2 | **PARTIAL**: 19.2 | **PARTIAL**: 18.9 | **PARTIAL**: 19.3 | **PARTIAL**: 19.4 |
| **3. Order-data stops answering** (300 people, 40 s) | **FAIL**: froze; 0 to 1 of 12 health checks answered | **FAIL**: froze; 1 to 2 of 13 | **FAIL**: froze; 1 of 13 | **FAIL**: froze; 2 of 13 | **PARTIAL**: 76 to 77 of 77 answered; people still wait 29 s until the breaker opens, then up to 1,158 fast errors | **PARTIAL**: 19 to 20 of 28 answered; frozen for about the first 30 s, then about 2,900 fast errors | **PASS**: 76 to 77 of 77 answered; 63 to 72 people waited 29 s, the rest got a fast named error |
| **4. Order-data stops answering for 5 minutes** | **FAIL**: froze; 1 of 86 | **FAIL**: froze; 2 of 87 | **FAIL**: froze; 1 of 86 | **FAIL**: froze; 1 of 86 | **PASS**: 587 of 587 answered; 70,321 fast errors | **PASS**: 530 of 538 answered; 79,303 fast errors | **PASS**: 588 of 588 answered |
| **5. Order-data slow** (answers after 20 s) | **PASS**: 3.6 | **PASS**: 3.6 | **PASS**: 3.4 | **PASS**: 3.6 | **PASS**: 3.6 | **PASS**: 3.6 | **PASS**: 3.6; none refused |
| **6. Order-data not running** | **PASS**: 1,000 fast errors | **PASS**: 1,000 | **PASS**: 1,000 | **PASS**: 1,000 | **PASS**: 1,000; 941 refused by the breaker without a call | **PASS**: 1,000; 941 refused by the breaker without a call | **PASS**: 1,000; 941 refused by the breaker without a call |
| **7. Order-data's address does not answer** | **PARTIAL**: about 21 s each; 100 errors in 30 s | **PASS**: 2 s each; 500 errors | **PARTIAL**: about 21 s; 100 errors | **PASS**: 2 s; 500 errors | **PASS**: 1,379 errors, most refused at once by the breaker | **PASS**: 1,379 errors, most refused at once | **PASS**: 1,379 errors, most refused at once |
| **8. Database driver holds a lock while it waits** (as older Oracle drivers do) | **PASS**: 72.3 | **PASS**: 73.2 | **PASS**: 72.8 | **PASS**: 72.6 | **FAIL**: 10.2; 82 people gave up | **PASS**: 73.3 | **PARTIAL**: 44.0; 4,060 refused, because order-data here takes 100 calls at once and the cap is 60 |
| **9. PDF-like processor work** (100 people) | **PASS**: 21.8 | **PASS**: 19.8 | **PASS**: 20.2 | **PASS**: 21.0 | **PASS**: 20.0 | **PASS**: 20.5 (a later batch) | **PARTIAL**: 1,163 refused, because 100 people at once is over the cap of 60 (a later batch) |

Stall and overload figures are the middle of 3 runs. The 5-minute stall, down, unreachable, lock and PDF-like figures for c to g are single runs. The PDF-like row for a to e was run in one batch, because the laptop's speed changes between batches. A third batch put Java 17 first and gave it 30 to 32 a second, with every other option at 20 to 23: the first runs of a batch are faster. So no option is faster at PDF-like work. The third batch is kept in `results/logs/pdf-like-third-batch.json`. In column e, the overload, stall, 5-minute stall and slow rows use the final breaker that counts only time-outs. The other rows used the first breaker, which makes no difference there: those runs have no "too busy" refusals.

**Other results, in the detailed results below:**
- Java 21 with virtual threads but no time limits keeps answering health checks in a stall, but stuck calls pile up without end: 3,000 calls and 456 MB of memory after 5 minutes (sections C and D).
- A 10 s limit on Java 17 ends every request at 10 s with a clear error, but only 6 of 14 health checks were answered during a stall (section C). A 10 s limit on 20-second work fails every request (section E).
- The ticket service on Java 21 with order-data on Java 17 behaved like Java 21 on both (section C).
- A bigger database pool helps only up to what the database can serve: 21.2, 31.4 and 31.9 a second for pools of 25, 50 and 100 when the database works on 40 calls at once (section G).
- Apache HttpClient at its default of 5 connections per address cut prints to 6.7 a second, about a tenth (section J).

**What each option means**

**a. Stay on Java 17, change nothing**
- Normal, slow and PDF-like work are fine: 12.3, 3.6 and 21.8 prints a second.
- When order-data stalls, the whole ticket service freezes. It answered 1 of 86 health checks in a 5-minute stall, and every person waits until the front door gives up at 29 s.
- A order-data address that does not answer takes about 21 s per call to fail, because there is no connect limit.

**b. Stay on Java 17, add the MVP time limits**
- Same speed as a in every scenario, and down or unreachable order-data fails in 2 s with a named error.
- The print call keeps its 30 s limit, so a stall still freezes the service (2 of 87). A 10 s limit on quick reads helps only partly (6 of 14 health checks, section C).
- It is the base that f and g build on.

**c. Upgrade to Java 21, change nothing**
- Behaves the same as a in all nine scenarios: the same freeze (1 of 86) and the same 21 s failures.
- No faster: 12.4, 19.2 and 20.2 a second against 12.3, 18.7 and 21.8.
- The upgrade work buys support and security updates, but no part of the fix.

**d. Upgrade to Java 21, add the same time limits as b**
- Behaves the same as b in all nine scenarios: fast named errors for down or unreachable order-data, and the same freeze during a stall (1 of 86).
- No risk from the lock-holding driver (72.6 a second), because virtual threads stay off.
- The upgrade adds work and testing, but nothing to the fix beyond what b gives.

**e. Upgrade to Java 21, virtual threads, time limits and a circuit breaker**
- Answers every health check in a stall: 76 to 77 of 77 in 40 s, and 587 of 587 in 5 minutes. Down and unreachable order-data are refused at once.
- With a database driver that holds a lock while it waits, prints fell from 72.6 to 10.2 a second and 82 people gave up. The real Oracle driver (`ojdbc8` 19.3) must be tested before virtual threads go on.
- The breaker must count only time-outs and failed connections; counting every error halved good prints under overload (9.6 against 19.2).

**f. Stay on Java 17, add the time limits and a circuit breaker**
- Keeps answering through a long stall (530 of 538 health checks in 5 minutes), with no upgrade and no lock risk (73.3 a second).
- The first 30 s of a stall are still frozen (19 to 20 of 28), because the breaker needs to see enough time-outs before it opens.
- No loss of prints under normal load, overload or slow work.

**g. Stay on Java 17, add the time limits, a circuit breaker and a bulkhead**
- Answers every health check from the first second of a stall (76 to 77 of 77, and 588 of 588 over 5 minutes), matching e without the Java 21 upgrade or its lock risk.
- No loss of prints under normal load, overload or slow work.
- The cap must sit just above what order-data can take at once. Where order-data took more than 60 (rows 8 and 9), the cap refused good prints, so it must change whenever order-data's limits change.

### MVP recommendations

The MVP (minimum viable product: the smallest change that fixes the problem) needs **no Java upgrade and no new code beyond configuration**. It is option b.

1. **Give every outbound call a 2-second connect limit,** in the shared HTTP client setup (`CommonRestTemplateConfig`). Without one, a call to an address that never answers waits about 21 seconds for Windows to give up; with it, 2 seconds (row 7).
2. **Give quick read calls a short wait limit, about 10 seconds, well under the front door's 29,** with a separate client or a per-call setting. A 30-second limit is longer than the front door's 29, so people see the front door's error and not ours (rows 3 and 4, section C).
3. **Keep a long wait limit, 30 seconds or more, only on the large print writes that must finish,** with a separate client. 20-second writes succeed under a 30-second limit and all fail under a 10-second one (row 5, section E).
4. **Turn a time-limit error into a clear, named error** in the ticket service: HTTP 504 with an error code such as `OUTBOUND_CALL_GAVE_UP`, not a hang or a generic 500 (rows 6 and 7).
5. **Stay on Java 17 for this fix.** The limits work the same on Java 17, and Java 21 made no row faster (rows 1, 2, 5 and 9).
6. **Do not change the database pool size, or swap HTTP clients, as part of this fix.** The pool helps only up to the database's own limit, and Apache HttpClient's defaults cut throughput to a tenth (sections G and J).

**After the MVP (not needed to fix the hang):**

- **Add a circuit breaker (option f)** that stops calling order-data for a few seconds after repeated time-outs. Count only time-outs and failed connections; counting every error halved good prints under overload.
- **Add a bulkhead with it (option g)**, using Resilience4j's counting `Bulkhead`, not `ThreadPoolBulkhead`. Set the cap just above what order-data can take at once (section K).
- **Upgrade to Java 21 for support and security, not for speed.** Turn on virtual threads only after a test against the shop's real Oracle database with the real driver (`ojdbc8` 19.3), because of row 8. Java 24 removes this kind of lock problem ([JEP 491](https://openjdk.org/jeps/491)).
- **Redesign the large writes to answer at once with "accepted, come back later" (HTTP 202)** and do the work through a queue or workflow service, such as Amazon SQS or AWS Step Functions. Then no person waits on a long write at all, and the long limit in recommendation 3 can go.

---

## Problem statement

The print path makes three calls in a row: the ticket service asks order-data to make the tickets, then waits, then asks it to mark them printed. The shared HTTP client (`SimpleClientHttpRequestFactory`) is built with no connect limit and no wait limit. In Java, a limit of 0 means "wait forever" ([URLConnection.setReadTimeout](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/net/URLConnection.html#setReadTimeout(int))).

When order-data is slow or stuck:

1. The person waits until the cloud front door gives up at about 29 seconds.
2. The ticket service keeps waiting after the person has gone, holding one of Tomcat's worker threads. Spring Boot's Tomcat allows 200 by default ([`server.tomcat.threads.max`](https://docs.spring.io/spring-boot/appendix/application-properties/index.html#application-properties.server.server.tomcat.threads.max)).
3. Once all 200 are waiting, the service cannot answer anything, even requests that have nothing to do with printing.

A change request proposes time limits. One constraint applies: large write calls must still be allowed to finish, because people rely on that today.

Java 21 brought virtual threads ([JEP 444](https://openjdk.org/jeps/444)). These are threads that cost almost nothing while they wait, so the 200-thread limit stops mattering. The question was whether this upgrade would make time limits unnecessary.

---

## Method

### What we built

Two small Spring Boot apps, a stand-in database, and a load generator. Each copies the shape of the real code. In the lab code, `notice-app` is the ticket service and `work-data-app` is the order-data service; the code keeps those short names.

![A load generator (people who give up after 29 seconds) and a health check twice a second call notice-app, which makes two numbered calls to work-data-app, 1. make the tickets and 2. mark them printed, which makes 4 round trips per ticket of 60 milliseconds each to an H2 database standing in for the shop's Oracle database; three panels list the switches set for each run, the five kinds of trouble caused on purpose, and what is measured.](assets/lab-setup-apps.png)

*Both pictures in this section are drawn by `assets/build_lab_setup.py` from the lab's own files.*

| Part | Stands in for | How it copies the real one |
|---|---|---|
| `notice-app` | The ticket service, which prints kitchen tickets for orders | `generatePrintNotices` makes call 1, then call 3, as the real ticket service's print code does. The HTTP client is built three ways: today's client with no limits, the same client with limits, or Apache HttpClient 5 with a connection pool. |
| `work-data-app` | The order-data service, which holds the orders | `createNotices` hands the work to a `printNoticeExecutor` and waits for it, as the real order-data print controller does. The executor has the same shape as the real `AsyncConfig`: 15 threads normally, up to 25, 30 queued, and a full executor refuses the work. A Hikari database pool of 25 with a 30-second wait, as in the real `application.properties`. |
| H2 server | The shop's database (Oracle) | A separate process. A database function, `WAN_SLEEP(60)`, makes each round trip take 60 ms, like the 40 to 80 ms trip across the WAN (wide area network) to the database today. An optional setting caps how many calls it works on at once. |
| `LoadTest.java` | People pressing Print | Each simulated person presses Print, waits up to 29 seconds, and presses again; after an error, they wait 1 second first. A separate health check runs twice a second. Both apps' counters are sampled every 2 seconds. |

The executor is copied because today's code has it. **This paper does not recommend it as a pattern.**

### How each run works

![For every one of its 108 runs, run_lab.py does eight lettered steps (start the database, start order-data, start notice-app with that run's switches, warm up, switch on the fault, run the load, collect the counts, stop everything), and 59 of the runs are repeated 3 times with the middle result reported and written to results.json and RESULTS.md.](assets/lab-setup-run.png)

`run_lab.py` runs every scenario the same way:

1. Start a fresh H2 server, a fresh work-data-app and a fresh notice-app, on the chosen Java version and settings.
2. Warm up with 5 people for 8 seconds; this is not counted.
3. If the scenario needs it, tell order-data to stop answering (`/admin/stall?on=true`) or to answer slowly (`&ms=20000`).
4. Run the load for 30 to 45 seconds, or 5 minutes for the long stall.
5. Stop everything and record the results.

Core scenarios ran 3 times, and the middle result is reported. Every run's raw numbers are in `results.json`.

### What "time limits" means in the lab

| Setting | No time limits (today) | With time limits (option A of the change request) | Too-short limit |
|---|---|---|---|
| `lab.client.connect-timeout-ms` | 0 (wait forever) | 2000 | 2000 |
| `lab.client.read-timeout-ms` | 0 (wait forever) | 30000 | 10000 |

These map directly to `SimpleClientHttpRequestFactory.setConnectTimeout` and `setReadTimeout` ([Spring Framework documentation](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/http/client/SimpleClientHttpRequestFactory.html)).

---

## Environment

| Item | Value |
|---|---|
| Machine | One laptop: Intel Core Ultra 7 165U, 14 processors, 31 GB memory |
| Operating system | Windows 11 Pro |
| Java 17 | Eclipse Temurin OpenJDK 17.0.21+9 |
| Java 21 | Oracle Java SE 21.0.12.1 LTS |
| Spring Boot | 3.2.4, the same as the shop's live services, with embedded Tomcat 10.1.19 at its default of 200 threads |
| Database pool | HikariCP 5.0.1 |
| Database stand-in | H2 2.2.224 in server mode |
| HTTP client options | Spring `SimpleClientHttpRequestFactory` (today's), and Apache HttpClient 5 |
| Circuit breaker and bulkhead | Resilience4j 2.2.0 (`resilience4j-circuitbreaker`, `resilience4j-bulkhead`) |
| Build | Apache Maven 3.9.16; both apps compiled for Java 17, so the same jar files run on both versions |
| Run script | Python 3.13 |
| Memory per app | `-Xmx1g` (at most 1 GB) |
| Garbage collector | G1 (the default) unless the row says ZGC (`-XX:+UseZGC -XX:+ZGenerational`, [JEP 439](https://openjdk.org/jeps/439)) |

**Read the numbers as comparisons between runs, not predictions for production.** Everything ran on one laptop, so the apps and the load generator shared the same processors.

---

## Detailed results

### A. Does Java 21 make the normal path faster? No.

| Run | Prints a second (3 runs) | Middle wait | Slowest 1 in 20 |
|---|---|---:|---:|
| Java 17 | 12.3, 12.8, 12.3 | 3.8 s | 3.9 s |
| Java 21 | 12.4, 12.3, 12.3 | 3.8 s | 3.9 s |
| Java 21, virtual threads | 12.3, 12.3, 12.3 | 3.8 s | 3.9 s |

12.3 a second is exactly 15 requests at a time divided by 1.26 seconds each. The executor runs only its 15 core threads until its queue of 30 is full. That is how Java's `ThreadPoolExecutor` works ([Java documentation](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)). The executor sets the speed, not the Java version.

### B. Overload: the executor refuses work on both versions

| Run | Prints a second (3 runs) | Requests refused |
|---|---|---:|
| Java 17 | 18.7, 18.7, 19.2 | about 2,500 a run |
| Java 21, virtual threads | 18.7, 18.9, 18.8 | about 2,350 a run |

Virtual threads do not get past an executor that is full.

### C. Order-data stops answering

| Run | Health checks answered | Most calls stuck in the ticket service at once | Memory |
|---|---|---:|---:|
| Java 17, no limits | 0 to 1 of 12 | 73 to 186 (frozen, so it could not count further) | n/a |
| Java 21 virtual, no limits | 77 of 77 | 600 | 106 to 113 MB |
| Java 17, 30 s limits | 1 to 2 of 13 | 200 | n/a |
| Java 21 virtual, 30 s limits | 77 of 77 | 560 to 594 | 111 to 114 MB |
| Java 17, 10 s limit | 6 of 14 (all 3 runs) | 200 | 61 to 63 MB |
| Java 21 virtual, 10 s limit | 77 of 77 | 300 | 126 to 134 MB |

With a 30-second limit, almost no clear errors were returned, because the simulated person gave up at 29 seconds, first. This is what will happen behind the real front door.

With the 10-second limit on Java 21, order-data had 1,200 calls in progress at the end of the run. **A time limit protects the caller, not the service it calls**: order-data keeps working on requests nobody is waiting for, so a stall that ends leaves it a backlog to clear.

**Mixed versions.** With the ticket service on Java 21 with virtual threads and order-data on Java 17, a stall gave the same picture as Java 21 on both: 77 of 77 health checks answered and 600 stuck calls without limits, and 76 of 76 answered with 30 s limits. At normal load it gave 12.3 prints a second.

### D. The 5-minute stall: do stuck calls keep growing?

Stuck calls in the ticket service, sampled every 2 seconds (every 15th sample shown):

| Minute | 0 | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 3.5 | 4 | 4.5 | 5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Java 21 virtual, no limits | 35 | 600 | 900 | 1,200 | 1,500 | 1,800 | 2,100 | 2,400 | 2,700 | 3,000 | 3,000 |
| Java 21 virtual, 30 s limits | 205 | 287 | 300 | 300 | 300 | 300 | 300 | 300 | 300 | 300 | 300 |

Memory rose from 57 MB to 456 MB without limits, and stayed between 107 and 179 MB with them. Without limits, the service would run out of memory given enough time. On Java 17 the service answered 1 health check out of 86 in the 5 minutes without limits, and 2 out of 87 with 30-second limits.

### E. Slow but working, and a limit that is too short

| Run | Prints a second | Middle wait | Result |
|---|---:|---:|---|
| Java 17, no limits | 3.6 | 21.6 s | Slow prints finish |
| Java 21 virtual, no limits | 3.6 | 21.8 s | Slow prints finish |
| Java 17, 30 s limits | 3.6 | 21.7 s | Slow prints finish |
| Java 21 virtual, 30 s limits | 3.4 | 21.8 s | Slow prints finish |
| Java 17, 10 s limit | 0 | n/a | All 300 failed with a clear error |
| Java 21 virtual, 10 s limit | 0 | n/a | All 300 failed with a clear error |

While the ticket service was giving up at 10 seconds, order-data had 150 calls in progress for 60 people. **A client time limit does not stop the work on the other side.** Order-data keeps working after the caller has gone, but the second call, "mark them printed", is never made. This is why the long limit must stay on the large writes until they are redesigned.

### F. Order-data down or unreachable

| Run | Errors in the run | How fast |
|---|---:|---|
| Order-data not running, with or without limits, either version | 1,000 in 20 s | At once: the connection is refused |
| Address does not answer, no limits, either version | 100 in 30 s | After about 21 s, when Windows gives up on its own |
| Address does not answer, 2 s connect limit, either version | 500 in 30 s | At 2 s |

### G. Database pool, when the database can serve only 40 at once

| Pool size | Prints a second (3 runs) | Middle wait |
|---:|---|---:|
| 25 (Java 17) | 21.8 | 9.2 s |
| 25 | 21.4, 21.0, 21.2 | 9.2 s |
| 50 | 31.2, 32.1, 31.4 | 6.1 s |
| 100 | 31.9, 31.8, 32.0 | 6.4 s |

Going from 50 to 100 added nothing, because the database was already full. Round 1, with no cap on the database, rose in step with the pool: 10 → 10, 25 → 21, 50 → 38, 100 → 70 a second. HikariCP's own guidance is to size the pool to the database, not to the number of callers ([About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)).

### H. Pinning: a driver that holds a lock while it waits

| Run | Prints a second (3 runs) | People who gave up |
|---|---|---:|
| Java 21 virtual, no lock | 72.1, 71.8, 71.7 | 0 |
| Java 21 virtual, lock held while waiting | 12.0, 12.8, 11.8 | 16 to 53 |
| Java 17, lock held while waiting | 72.3 | 0 |
| Java 21 virtual, lock held, 30 s limits | 13.1, 13.9, 12.8 | 15 to 18 |
| Java 17, lock held, 30 s limits | 73.2 | 0 |

On Java 21, a virtual thread that waits inside a `synchronized` block is "pinned". It keeps one of the few real threads underneath busy, so the others cannot run ([JEP 444, "Pinning"](https://openjdk.org/jeps/444)). Java's own pinning trace (`-Djdk.tracePinnedThreads=short`) reported it during the run. The lab copies the behaviour with `synchronized (connection)`. Whether the shop's real driver, `ojdbc8` 19.3, does this must be tested against the real database.

### I. PDF-like processor work

| Run | Prints a second (3 runs) | Middle wait |
|---|---|---:|
| Java 17, G1 | 22.0, 21.1, 19.9 | 4.8 s |
| Java 21, G1 | 20.7, 20.7, 21.1 | 5.2 s |
| Java 21, generational ZGC | 19.7, 20.0, 20.5 | 5.1 s |
| Java 21 virtual, G1 | 20.0, 20.0, 20.0 | 5.3 s |
| Java 17, G1, 30 s limits | 19.7 | 5.2 s |
| Java 21 virtual, G1, 30 s limits | 20.0 | 5.5 s |

Each ticket built and compressed about 2 MB of PDF-like text, about 60 ms of processor time. All six runs sit between 19.7 and 22.0 a second, so neither Java 21 nor ZGC was faster.

These were run again in one batch. An earlier batch gave 18 to 21 a second, and one run gave 30. The laptop's speed changes with its temperature and its other load, so **only compare processor-heavy runs from the same batch.**

### J. HTTP client connection pool

| Client | Prints a second | Middle wait |
|---|---:|---:|
| Today's simple client | 70.1 | 1.4 s |
| Apache HttpClient 5, defaults | 6.7 | 27.0 s |
| Apache HttpClient 5, 100 per address | 73.0 | 1.4 s |

At its defaults, Apache HttpClient 5 allows 25 connections in all and 5 per address. In the run, 95 requests waited for those 5 connections. These defaults are set in `PoolingHttpClientConnectionManager` ([source](https://github.com/apache/httpcomponents-client/blob/master/httpclient5/src/main/java/org/apache/hc/client5/http/impl/io/PoolingHttpClientConnectionManager.java)).

### K. Sizing the bulkhead

Without a bulkhead (option f), the circuit breaker cannot act until it has seen enough time-outs, so the first 30 seconds of a stall still froze Java 17: every one of Tomcat's 200 worker threads was stuck waiting on order-data. A **bulkhead** caps how many calls to order-data can be in progress at once. One more call over the cap fails at once with a named error ("service unavailable", HTTP 503, `WORK_DATA_CALL_LIMIT_REACHED`) instead of waiting. A stall can then hold only as many threads as the cap, and the rest stay free.

The lab uses Resilience4j's counting bulkhead (`Bulkhead`, also called a semaphore bulkhead). It runs on the caller's own thread and starts no threads of its own. Resilience4j's other kind, `ThreadPoolBulkhead`, runs each call on a thread pool of its own, which this design avoids.

All runs are Java 17 with the MVP time limits and the circuit breaker that counts only time-outs.

| Scenario | No bulkhead (option f) | Bulkhead, cap of 50 | Bulkhead, cap of 60 (option g) |
|---|---|---|---|
| **Normal load** (40 people) | **PASS**: 12.3 a second | **PASS**: 12.3; none refused | **PASS**: 12.8; none refused |
| **Overload** (150 people) | **PARTIAL**: 19.3 a second | **PARTIAL**: 16.3; good prints refused | **PARTIAL**: 19.4 |
| **Order-data stops answering** (300 people, 40 s) | **PARTIAL**: 19 to 20 of 28 health checks answered; 303 people waited 29 s | **PASS**: 77 of 77 answered; 53 to 55 people waited 29 s; the rest got a fast named error | **PASS**: 76 to 77 of 77 answered; 63 to 72 people waited 29 s |
| **Order-data stops answering for 5 minutes** | **PASS**: 530 of 538 answered | **PASS**: 587 of 587 | **PASS**: 588 of 588 |
| **Order-data slow** (60 people, 20 s each) | **PASS**: 3.6 a second | **PARTIAL**: 3.1; 450 good prints refused | **PASS**: 3.6; none refused |

**Size the cap from what order-data can take, not from what the ticket service can send.** Order-data works on about 55 calls at once (its worker pool plus its queue) and refuses the rest. A cap of 50 sat below that, so it turned away prints order-data could have done. A cap of 60 sat just above it and cost nothing. Two runs show the other side: where order-data was set up to take 100 calls at once (the lock-holding driver run) or 100 people were busy at once (the PDF-like run), the cap of 60 refused good prints (4,060 and 1,163). The cap must move whenever order-data's own limits change. The production cap must come from the real order-data's limits and the real peak number of prints in progress, not from this laptop.

---

## Limits of this study

- **H2 is not Oracle.** The lab copies the round-trip time, not Oracle's behaviour under load or its driver. Row 10 copies the lock behaviour on purpose; it does not prove that `ojdbc8` 19.3 does it.
- **One laptop.** The apps, the database and the load generator shared 14 processors, so absolute numbers do not carry over to production.
- **Not tested:**
  - the parallel groups inside "make the tickets" (the lab handles each request's tickets one after another)
  - raising Tomcat's thread limit
  - the bulkhead on Java 21 with virtual threads, where stuck calls do not use up a limited thread pool
  - the bulkhead and the circuit breaker together against down or unreachable order-data, and with the lock-holding driver
  - real PDF generation
- **Single runs:** the 5-minute stalls with a bulkhead, the 5-minute stall, down, unreachable, lock and PDF-like runs for options c, d and e, the uncapped pool numbers from round 1, the 5-minute stalls, the down, unreachable and mixed runs, the 10 s limit on slow work for Java 21, and the limits versions of rows 10 (Java 17) and 11.

---

## How to reproduce

### What you need

- JDK 17 and JDK 21 (any vendor)
- Apache Maven 3.9 or later
- Python 3.10 or later
- About 3 hours for every scenario
- Free ports: 18084, 18093 and 19092

### Steps

```bash
cd lab

# 1. Build both apps (compiled for Java 17, so they run on both versions)
JAVA_HOME=<path to JDK 21> mvn -q -B package -DskipTests

# 2. Tell the script where the JDKs are, if they are not in the default places
export JDK17=<path to JDK 17>
export JDK21=<path to JDK 21>

# 3. Run every scenario (about 3 hours)
python run_lab.py

# Or run only some scenarios: any run whose name contains one of the words
python run_lab.py stall pin
```

Results are written to `results/results.json` (every run, with every repeat) and `results/RESULTS.md` (a table of the middle runs). Each app's log goes to `results/logs/`.

`run_lab.py` expects the H2 jar at `~/.m2/repository/com/h2database/h2/2.2.224/`. Maven puts it there during step 1.

### Trying one scenario by hand

```bash
# database stand-in
java -cp ~/.m2/repository/com/h2database/h2/2.2.224/h2-2.2.224.jar:work-data-app/target/classes \
     org.h2.tools.Server -tcp -tcpPort 19092 -ifNotExists

# work-data, on Java 21 with virtual threads
$JDK21/bin/java -jar work-data-app/target/work-data-app-1.0.0.jar --spring.threads.virtual.enabled=true

# notice-app, with option A limits
$JDK21/bin/java -jar notice-app/target/notice-app-1.0.0.jar --spring.threads.virtual.enabled=true \
     --lab.client.connect-timeout-ms=2000 --lab.client.read-timeout-ms=30000

# make work-data stop answering, then put 300 people on it for 40 seconds
curl -X POST "http://localhost:18093/admin/stall?on=true"
$JDK21/bin/java loadtest/LoadTest.java --url "http://localhost:18084/notice/api/generatePrintNotices?notices=5" \
     --users 300 --seconds 40 --timeout 29 --probe http://localhost:18084/notice/api/ping \
     --stats http://localhost:18084/admin/stats,http://localhost:18093/admin/stats
```

On Windows, use `;` in place of `:` in the `-cp` path.

### Settings you can change

| Setting | App | Default | What it does |
|---|---|---|---|
| `spring.threads.virtual.enabled` | both | false | Virtual threads (Java 21 only) |
| `lab.client.connect-timeout-ms` | ticket | 0 (none) | Connect limit |
| `lab.client.read-timeout-ms` | ticket | 0 (none) | Wait-for-answer limit |
| `lab.client.breaker` | ticket | false | Turn on the circuit breaker |
| `lab.client.breaker.record` | ticket | all | `all` (every error counts as a failure) or `timeouts` (only time-outs and failed connections) |
| `lab.client.bulkhead` | ticket | 0 (none) | Most calls to order-data in progress at once; one more fails at once |
| `lab.client.kind` | ticket | simple | `simple` (today's client) or `pooled` (Apache HttpClient 5) |
| `lab.client.pool.max-total`, `lab.client.pool.max-per-route` | ticket | 25, 5 | Apache pool limits |
| `lab.workdata.mode` | order-data | executor | `executor` (today's code) or `inline` (work on the request thread) |
| `spring.datasource.hikari.maximum-pool-size` | order-data | 25 | Database pool size |
| `lab.db.latency-ms` | order-data | 60 | Time for each database round trip |
| `lab.db.round-trips-per-notice` | order-data | 4 | Round trips for each ticket |
| `lab.db.hold-lock` | order-data | false | Hold a lock while waiting on the database, to copy pinning |
| `lab.cpu.kb-per-notice` | order-data | 0 | PDF-like processor work for each ticket |
| `-Dlab.db.sessions` | H2 server | no cap | How many calls the database works on at once |

---

## Code used

All code is in [lab/](lab/).

| File | What it is |
|---|---|
| [`pom.xml`](lab/pom.xml) | Parent build: Spring Boot 3.2.4, compiled for Java 17 |
| [`notice-app/.../NoticeApp.java`](lab/notice-app/src/main/java/lab/notice/NoticeApp.java) | The ticket stand-in: the HTTP client built three ways, the print endpoint, the health check and the counters |
| [`work-data-app/.../WorkDataApp.java`](lab/work-data-app/src/main/java/lab/workdata/WorkDataApp.java) | The order-data stand-in: the executor, the database round trips, the stall switch, the lock switch, the PDF-like work and the counters |
| [`work-data-app/.../WanSleep.java`](lab/work-data-app/src/main/java/lab/workdata/WanSleep.java) | Runs inside H2: makes each database call take as long as a WAN round trip, with an optional cap on calls at once |
| [`loadtest/LoadTest.java`](lab/loadtest/LoadTest.java) | The people pressing Print, the health check, and sampling both apps' counters |
| [`run_lab.py`](lab/run_lab.py) | Every scenario, run the same way, with the results tables written out |

The key lines.

How the HTTP client gets its limits (notice-app). A value of 0 leaves the limit off, as today:

```java
SimpleClientHttpRequestFactory f = new SimpleClientHttpRequestFactory();
if (connectMs > 0) f.setConnectTimeout(connectMs);
if (readMs > 0) f.setReadTimeout(readMs);
return new RestTemplate(f);
```

How a time-limit error becomes a clear error (notice-app):

```java
} catch (ResourceAccessException e) {
    // the client's own limit ran out (read, connect, or waiting for a pooled connection)
    return ResponseEntity.status(504).body(Map.of("error", "OUTBOUND_CALL_GAVE_UP " + e.getMessage()));
}
```

How the circuit breaker and the bulkhead are set up and used (notice-app). The bulkhead is `Bulkhead.of("work-data", BulkheadConfig.custom().maxConcurrentCalls(bulkheadMax).maxWaitDuration(Duration.ZERO).build())`:

```java
CircuitBreakerConfig.Builder cfg = CircuitBreakerConfig.custom()
        .failureRateThreshold(50)
        .slidingWindowSize(20)
        .minimumNumberOfCalls(10)
        .waitDurationInOpenState(Duration.ofSeconds(5))
        .permittedNumberOfCallsInHalfOpenState(3);
// only time-outs and failed connections count, so work-data saying "too busy" does not open it
if ("timeouts".equals(record)) cfg.recordExceptions(ResourceAccessException.class);
...
// the bulkhead sits outside the breaker, so a call it refuses never counts for or against the breaker
Runnable guarded = breaker == null ? calls : () -> breaker.executeRunnable(calls);
if (bulkhead != null) bulkhead.executeRunnable(guarded); else guarded.run();
...
} catch (CallNotPermittedException e) {
    // the breaker is open: fail at once without calling work-data
    return ResponseEntity.status(503).body(Map.of("error", "WORK_DATA_UNAVAILABLE"));
}
```

How the lab copies a driver that holds a lock while it waits (work-data-app):

```java
synchronized (c) {
    for (int r = 0; r < times; r++) {
        st.execute("CALL WAN_SLEEP(" + latencyMs + ")");
    }
}
```

---

## Sources

**Java and the platform**
- [JEP 444: Virtual Threads (Java 21)](https://openjdk.org/jeps/444), including the section on pinning
- [JEP 491: Synchronize Virtual Threads without Pinning (Java 24)](https://openjdk.org/jeps/491)
- [JEP 439: Generational ZGC (Java 21)](https://openjdk.org/jeps/439)
- [Java 17 `URLConnection.setReadTimeout`: 0 means wait forever](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/net/URLConnection.html#setReadTimeout(int))
- [Java 17 `ThreadPoolExecutor`: queues before it grows past its core size](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)

**Spring and libraries**
- [Spring Boot 3.2 release notes: virtual threads support](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.2-Release-Notes)
- [Spring Boot application properties: `server.tomcat.threads.max` (default 200)](https://docs.spring.io/spring-boot/appendix/application-properties/index.html#application-properties.server.server.tomcat.threads.max)
- [Spring Framework `SimpleClientHttpRequestFactory`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/http/client/SimpleClientHttpRequestFactory.html)
- [Apache HttpClient 5 `PoolingHttpClientConnectionManager` source: default pool limits](https://github.com/apache/httpcomponents-client/blob/master/httpclient5/src/main/java/org/apache/hc/client5/http/impl/io/PoolingHttpClientConnectionManager.java)
- [Resilience4j CircuitBreaker documentation](https://resilience4j.readme.io/docs/circuitbreaker): sliding window, failure rate, open and half-open states, `recordExceptions`
- [Resilience4j Bulkhead documentation](https://resilience4j.readme.io/docs/bulkhead): the counting (semaphore) bulkhead and the thread pool bulkhead
- [HikariCP: About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)
- [H2 Database: user-defined functions](https://h2database.com/html/features.html#user_defined_functions)

**Internal**
- The change request to add time limits to outbound calls, with its option A developer kit
- The ordering system's performance review
- The live services' source, read for the lab's shape: `CommonRestTemplateConfig`, the ticket service's print code, the order-data print controller, `AsyncConfig`, and the order-data service's `application.properties`

---

## Document version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-11-11 | First version: 35 scenarios, 66 runs on Java 17 and Java 21, results table and MVP recommendations |
| 1.1 | 2026-11-11 | Every cell of the table measured (20 more scenarios). Java 17 with a 10 s limit changed from PASS to PARTIAL. A circuit breaker added after the MVP. PDF-like runs repeated in one batch |
| 1.2 | 2026-11-11 | The five options (a to e) measured side by side: 44 more scenarios, 88 more runs. Circuit breaker tested on Java 17 and Java 21; it must count only time-outs. Plain Java 21 confirmed to behave like Java 17 |
| 1.3 | 2026-11-12 | Bulkhead tested on Java 17 with caps of 50 and 60 (9 more scenarios, 23 more runs). Lab setup picture generated in place of the Mermaid diagram |
| 1.4 | 2026-11-12 | Renamed to cover every fix tested, not only Java 21. Prepared by the engineering team. Team assessment and recommendations table added to the executive summary. Two generated pictures of the testing setup: how the lab is set up, and how each test was run |
| 1.5 | 2026-11-12 | Bulkhead column added to the five-options table; the bulkhead of 60 run on every scenario (5 more scenarios, 7 more runs). It refuses good prints wherever order-data takes more than 60 calls at once |
| 1.6 | 2026-11-12 | One results table for all seven options; the circuit breaker and the bulkhead are options f and g. The older four-column table and the separate summary tables folded into lists or the detailed results; bulkhead sizing moved to section K |
| 1.7 | 2026-11-19 | Made generic for public release: written as a pizza shop's kitchen ticket printing, with no client, system or people's names. No numbers changed |
