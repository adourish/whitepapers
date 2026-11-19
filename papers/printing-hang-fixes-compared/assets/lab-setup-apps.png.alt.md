# Alt text for lab-setup-apps.png

**Short alt:** Diagram: How the lab is set up, 5 parts and 2 steps.

**Long description:**

Diagram: How the lab is set up.
A load generator (people who give up after 29 seconds) and a health check twice a second call notice-app (port 18084), which calls work-data-app (port 18093), which calls an H2 database server standing in for the shop's Oracle database (port 19092). For each run, run_lab.py sets switches on notice-app (Java 17 or 21, virtual threads on or off, time limits none, 2 + 10 or 2 + 30, a circuit breaker counting every error or counting only time-outs, a bulkhead of off, 50 or 60) and on work-data-app (database pool 25, 50 or 100, a driver that holds a lock while it waits, PDF-like processor work). It causes trouble on purpose: work-data stops answering for 40 seconds or 5 minutes, answers after 20 seconds, is not running, or sits at an address that does not answer, or 150 people press Print. It measures prints answered OK per second, how long people waited, health checks answered, named errors (time limit HTTP 504, breaker or bulkhead HTTP 503), and stuck calls, threads and memory read from both apps every 2 seconds.
It shows People pressing Print, Health check, notice-app, work-data-app and H2 database server.

The steps, in order:

1. Notice-app asks work-data-app to make the tickets; work-data-app makes 4 round trips per ticket to the H2 database, 60 milliseconds each.
2. Notice-app asks work-data-app to mark them printed.
