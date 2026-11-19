# Lab results

Written by `run_lab.py`. Do not edit by hand. -1 means no request finished.

| Run | What it tests | Java | Threads | Answered OK | OK a second | Middle wait (ms) | Slowest 1 in 20 (ms) | Other outcomes | Ping answered | Ping failed | Peak requests waiting in notice | Peak work-data DB connections in use | Peak waiting for a DB connection | Pinned-thread reports |
|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `normal-17` | Normal load, 40 people | 17 | platform | 370 | 12.3 | 3792 | 3927 | none | 58 | 0 | 40 | 25 | 4 | 0 |
| `normal-21` | Normal load, 40 people | 21 | platform | 370 | 12.3 | 3803 | 3882 | none | 58 | 0 | 40 | 25 | 5 | 0 |
| `normal-21-virtual` | Normal load, 40 people | 21 | virtual | 370 | 12.3 | 3785 | 3918 | none | 58 | 0 | 40 | 25 | 5 | 0 |
| `overload-17` | 150 people: more than printNoticeExecutor holds (25 running, 30 queued) | 17 | platform | 537 | 17.9 | 3519 | 5492 | HTTP 502: 58446, HTTP 504: 25 | 53 | 0 | 150 | 25 | 32 | 0 |
| `overload-21-virtual` | 150 people: more than printNoticeExecutor holds (25 running, 30 queued) | 21 | virtual | 553 | 18.4 | 4065 | 7689 | HTTP 502: 34290, HTTP 504: 1 | 53 | 0 | 150 | 25 | 68 | 0 |
| `stall-no-limit-17` | Work-data stops answering; no time limit on the client (today) | 17 | platform | 0 | 0.0 | -1 | -1 | ConnectException: 7, HTTP 504: 97, person gave up at 29 s: 600 | 1 | 11 | 86 | 0 | 0 | 0 |
| `stall-no-limit-21-virtual` | Work-data stops answering; no time limit on the client (today) | 21 | virtual | 0 | 0.0 | -1 | -1 | person gave up at 29 s: 600 | 77 | 0 | 600 | 0 | 0 | 0 |
| `stall-limit-17` | Work-data stops answering; 10-second read limit (the change request) | 17 | platform | 0 | 0.0 | -1 | -1 | HTTP 504: 900 | 4 | 9 | 200 | 0 | 0 | 0 |
| `stall-limit-21-virtual` | Work-data stops answering; 10-second read limit (the change request) | 21 | virtual | 0 | 0.0 | -1 | -1 | HTTP 504: 1200 | 77 | 0 | 300 | 0 | 0 | 0 |
| `dbpool-25-17` | No executor; 200 people reach a database pool of 25 | 17 | platform | 643 | 21.4 | 9203 | 20308 | person gave up at 29 s: 4 | 47 | 0 | 200 | 25 | 184 | 0 |
| `dbpool-10-21-virtual` | No executor; 200 people reach a database pool of 10 | 21 | virtual | 302 | 10.1 | 21222 | 27104 | person gave up at 29 s: 117 | 57 | 0 | 288 | 10 | 279 | 0 |
| `dbpool-25-21-virtual` | No executor; 200 people reach a database pool of 25 | 21 | virtual | 623 | 20.8 | 9292 | 20341 | person gave up at 29 s: 6 | 56 | 0 | 205 | 25 | 182 | 0 |
| `dbpool-50-21-virtual` | No executor; 200 people reach a database pool of 50 | 21 | virtual | 1148 | 38.3 | 4819 | 11402 | none | 57 | 0 | 200 | 50 | 157 | 0 |
| `dbpool-100-21-virtual` | No executor; 200 people reach a database pool of 100 | 21 | virtual | 2116 | 70.5 | 2708 | 4752 | none | 58 | 0 | 200 | 100 | 105 | 0 |
| `httppool-simple-21-virtual` | HTTP client: today's simple client (no pool limit) | 21 | virtual | 2100 | 70.0 | 1410 | 1765 | none | 58 | 0 | 100 | 100 | 7 | 0 |
| `httppool-default-21-virtual` | HTTP client: Apache pool at its defaults (5 per address) | 21 | virtual | 200 | 6.7 | 26890 | 28040 | none | 57 | 0 | 100 | 5 | 3 | 0 |
| `httppool-100-21-virtual` | HTTP client: Apache pool, 100 per address | 21 | virtual | 2101 | 70.0 | 1387 | 1703 | none | 58 | 0 | 100 | 100 | 7 | 0 |
