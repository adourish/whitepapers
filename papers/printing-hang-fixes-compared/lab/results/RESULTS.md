# Lab results, round 2

Written by `run_lab.py`; do not edit by hand. -1 means no request finished. A person who gets an error waits 1 second before pressing Print again.

| Run | What it tests | Java | Threads | Repeats | Answered OK a second (range) | Middle wait (ms) | Slowest 1 in 20 (ms) | Other outcomes, middle repeat | Pings answered | Peak calls stuck in notice | Peak notice memory (MB) | Peak DB connections in use | Pinned-thread reports |
|---|---|---|---|---:|---|---:|---:|---|---|---:|---:|---:|---:|
| `normal-17` | Normal load, 40 people | 17 | platform | 3 | 12.3 (12.3 to 12.8) | 3789 | 3929 | none | 58 of 58 | 40 | 49 | 25 | 0 |
| `normal-21` | Normal load, 40 people | 21 | platform | 3 | 12.3 (12.3 to 12.4) | 3793 | 3878 | none | 58 of 58 | 40 | 37 | 24 | 0 |
| `normal-21-virtual` | Normal load, 40 people | 21 | virtual | 3 | 12.3 (12.3 to 12.3) | 3802 | 3948 | none | 58 of 58 | 40 | 36 | 25 | 0 |
| `overload-17` | 150 people: more than printNoticeExecutor holds | 17 | platform | 3 | 18.7 (18.7 to 19.2) | 3364 | 4440 | HTTP 502: 2472 | 56 of 56 | 150 | 147 | 25 | 0 |
| `overload-21-virtual` | 150 people: more than printNoticeExecutor holds | 21 | virtual | 3 | 18.8 (18.7 to 18.9) | 3522 | 5350 | HTTP 502: 2386 | 58 of 58 | 150 | 197 | 25 | 0 |
| `stall-no-limit-17` | Work-data stops answering; no limit (today) | 17 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | person gave up at 29 s: 600 | 1 of 12 | 186 | 46 | 5 | 0 |
| `stall-no-limit-21-virtual` | Work-data stops answering; no limit (today) | 21 | virtual | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 504: 83, person gave up at 29 s: 600 | 77 of 77 | 600 | 113 | 5 | 0 |
| `stall-option-a-17` | Work-data stops answering; option A limits (30 s) | 17 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | person gave up at 29 s: 600 | 1 of 12 | - | - | - | 0 |
| `stall-option-a-21-virtual` | Work-data stops answering; option A limits (30 s) | 21 | virtual | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | person gave up at 29 s: 600 | 77 of 77 | 594 | 113 | 5 | 0 |
| `slow-option-a-17` | Work-data answers after 20 s; option A limits (30 s) | 17 | platform | 3 | 3.6 (3.4 to 3.6) | 21584 | 23321 | HTTP 502: 5 | 88 of 88 | 60 | 28 | 25 | 0 |
| `slow-option-a-21-virtual` | Work-data answers after 20 s; option A limits (30 s) | 21 | virtual | 3 | 3.4 (3.0 to 3.4) | 21883 | 23372 | HTTP 502: 5 | 88 of 88 | 60 | 35 | 25 | 0 |
| `slow-limit-10-17` | Work-data answers after 20 s; a 10 s limit (too short) | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 300 | 88 of 88 | 60 | 39 | 25 | 0 |
| `down-option-a-17` | Work-data is not running; option A limits | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 1000 | 39 of 39 | 50 | 49 | - | 0 |
| `unreachable-no-limit-17` | Work-data's address does not answer at all; no connect limit | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 100 | 59 of 59 | 50 | 26 | 0 | 0 |
| `unreachable-option-a-17` | Work-data's address does not answer at all; 2 s connect limit | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 500 | 58 of 58 | 50 | 40 | 0 | 0 |
| `long-stall-no-limit-17` | 5-minute stall; no limit | 17 | platform | 1 | 0.0 | -1 | -1 | ConnectException: 29, person gave up at 29 s: 3000 | 1 of 86 | 75 | 28 | 5 | 0 |
| `long-stall-no-limit-21-virtual` | 5-minute stall; no limit | 21 | virtual | 1 | 0.0 | -1 | -1 | ConnectException: 8, person gave up at 29 s: 3000 | 588 of 588 | 3000 | 456 | 5 | 0 |
| `long-stall-option-a-21-virtual` | 5-minute stall; option A limits | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 504: 13, person gave up at 29 s: 3000 | 589 of 589 | 587 | 179 | 5 | 0 |
| `mixed-normal` | Notice on 21 virtual, work-data on 17; normal load | 21 (work-data 17) | virtual | 3 | 12.3 (12.3 to 12.3) | 3805 | 3955 | none | 59 of 59 | 40 | 37 | 25 | 0 |
| `mixed-stall-option-a` | Notice on 21 virtual, work-data on 17; work-data stops answering; option A | 21 (work-data 17) | virtual | 1 | 0.0 | -1 | -1 | person gave up at 29 s: 600 | 76 of 76 | 600 | 114 | - | 0 |
| `dbcap40-pool25-17` | No executor; database works on 40 at once; pool 25 | 17 | platform | 1 | 21.8 | 9209 | 20122 | none | 50 of 50 | 200 | 82 | 25 | 0 |
| `dbcap40-pool25-21-virtual` | No executor; database works on 40 at once; pool 25 | 21 | virtual | 3 | 21.2 (21.0 to 21.4) | 9248 | 21406 | none | 58 of 58 | 200 | 132 | 25 | 0 |
| `dbcap40-pool50-21-virtual` | No executor; database works on 40 at once; pool 50 | 21 | virtual | 3 | 31.4 (31.2 to 32.1) | 6147 | 12470 | none | 58 of 58 | 200 | 156 | 50 | 0 |
| `dbcap40-pool100-21-virtual` | No executor; database works on 40 at once; pool 100 | 21 | virtual | 3 | 31.9 (31.8 to 32.0) | 6392 | 10743 | none | 58 of 58 | 200 | 165 | 100 | 0 |
| `pin-off-21-virtual` | No executor, pool 100; driver without a lock | 21 | virtual | 3 | 71.8 (71.7 to 72.1) | 2652 | 4536 | none | 58 of 58 | 200 | 171 | 100 | 0 |
| `pin-on-21-virtual` | No executor, pool 100; driver holds a lock while it waits | 21 | virtual | 3 | 12.0 (11.8 to 12.8) | 12693 | 27385 | person gave up at 29 s: 53 | 58 of 58 | 200 | 87 | 53 | 0 |
| `pin-on-17` | No executor, pool 100; driver holds a lock while it waits | 17 | platform | 1 | 72.3 | 2642 | 4673 | none | 54 of 54 | 200 | 84 | 100 | 0 |
| `pin-on-21-virtual-traced` | As pin-on, with the pinning trace on (counts reports) | 21 | virtual | 1 | 11.4 | 5156 | 8480 | none | 19 of 19 | 50 | 36 | 49 | 4 |
| `cpu-17` | PDF-like processor work, 100 people; G1 collector | 17 | platform | 3 | 21.8 (20.1 to 31.3) | 4837 | 6904 | none | 53 of 53 | 100 | 68 | 100 | 0 |
| `cpu-21` | PDF-like processor work, 100 people; G1 collector | 21 | platform | 3 | 20.7 (20.7 to 21.1) | 5068 | 6560 | none | 51 of 51 | 100 | 45 | 100 | 0 |
| `cpu-21-zgc` | PDF-like processor work, 100 people; generational ZGC | 21 | platform + ZGC | 3 | 20.0 (19.7 to 20.5) | 5112 | 7632 | none | 54 of 54 | 100 | 182 | 100 | 0 |
| `cpu-21-virtual` | PDF-like processor work, 100 people; G1, virtual threads | 21 | virtual | 3 | 20.0 (20.0 to 20.0) | 5322 | 5858 | none | 56 of 56 | 100 | 88 | 100 | 0 |
| `httppool-simple-21-virtual` | HTTP client: today's simple client | 21 | virtual | 1 | 70.1 | 1406 | 1521 | none | 58 of 58 | 100 | 171 | 100 | 0 |
| `httppool-default-21-virtual` | HTTP client: Apache pool at its defaults (5 per address) | 21 | virtual | 1 | 6.7 | 27013 | 27488 | none | 58 of 58 | 100 | 39 | 5 | 1 |
| `httppool-100-21-virtual` | HTTP client: Apache pool, 100 per address | 21 | virtual | 1 | 73.0 | 1383 | 1431 | none | 58 of 58 | 100 | 192 | 100 | 1 |
| `fill-normal-option-a-17` | Normal load, 40 people; option A limits | 17 | platform | 3 | 12.4 (12.3 to 12.5) | 3736 | 3868 | none | 58 of 58 | 40 | 52 | 25 | 0 |
| `fill-normal-option-a-21-virtual` | Normal load, 40 people; option A limits | 21 | virtual | 3 | 12.8 (12.3 to 13.8) | 3789 | 3907 | none | 59 of 59 | 40 | 37 | 25 | 0 |
| `fill-overload-option-a-17` | 150 people; option A limits | 17 | platform | 3 | 19.2 (19.1 to 19.2) | 3275 | 4042 | HTTP 502: 2611 | 58 of 58 | 111 | 173 | 25 | 0 |
| `fill-overload-option-a-21-virtual` | 150 people; option A limits | 21 | virtual | 3 | 19.0 (18.9 to 19.1) | 3516 | 5433 | HTTP 502: 2378 | 58 of 58 | 139 | 199 | 25 | 0 |
| `fill-stall-limit-10-17` | Work-data stops answering; 10 s read limit | 17 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 504: 900 | 6 of 14 | 200 | 63 | 5 | 0 |
| `fill-stall-limit-10-21-virtual` | Work-data stops answering; 10 s read limit | 21 | virtual | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 504: 1200 | 77 of 77 | 300 | 126 | 5 | 0 |
| `fill-long-stall-option-a-17` | 5-minute stall; option A limits | 17 | platform | 1 | 0.0 | -1 | -1 | ConnectException: 7, person gave up at 29 s: 3000 | 2 of 87 | 5 | 18 | 5 | 0 |
| `fill-slow-no-limit-17` | Work-data answers after 20 s; no limit | 17 | platform | 3 | 3.6 (3.6 to 3.6) | 21608 | 23157 | HTTP 502: 5 | 88 of 88 | 60 | 49 | 25 | 0 |
| `fill-slow-no-limit-21-virtual` | Work-data answers after 20 s; no limit | 21 | virtual | 3 | 3.6 (3.5 to 3.7) | 21785 | 23010 | HTTP 502: 5 | 88 of 88 | 60 | 35 | 25 | 0 |
| `fill-slow-limit-10-21-virtual` | Work-data answers after 20 s; a 10 s limit (too short) | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 504: 300 | 88 of 88 | 60 | 33 | 25 | 0 |
| `fill-down-no-limit-17` | Work-data is not running; no limit | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 1000 | 39 of 39 | 50 | 39 | - | 0 |
| `fill-down-no-limit-21-virtual` | Work-data is not running; no limit | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 504: 1000 | 39 of 39 | 50 | 38 | - | 0 |
| `fill-down-option-a-21-virtual` | Work-data is not running; option A limits | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 504: 1000 | 39 of 39 | 50 | 36 | - | 0 |
| `fill-unreachable-no-limit-21-virtual` | Work-data's address does not answer at all; no connect limit | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 504: 100 | 58 of 58 | 50 | 36 | 0 | 0 |
| `fill-unreachable-option-a-21-virtual` | Work-data's address does not answer at all; 2 s connect limit | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 504: 500 | 58 of 58 | 50 | 37 | 0 | 0 |
| `fill-pin-on-option-a-17` | No executor, pool 100; driver holds a lock; option A limits | 17 | platform | 1 | 73.2 | 2578 | 4833 | none | 56 of 56 | 200 | 172 | 100 | 0 |
| `fill-pin-on-option-a-21-virtual` | No executor, pool 100; driver holds a lock; option A limits | 21 | virtual | 3 | 13.1 (12.8 to 13.9) | 18115 | 23887 | person gave up at 29 s: 18 | 58 of 58 | 200 | 82 | 47 | 0 |
| `fill-cpu-option-a-17` | PDF-like processor work, 100 people; option A limits | 17 | platform | 1 | 19.8 | 5226 | 7723 | none | 53 of 53 | 100 | 118 | 100 | 0 |
| `fill-cpu-option-a-21-virtual` | PDF-like processor work, 100 people; option A limits | 21 | virtual | 1 | 20.0 | 5486 | 6268 | none | 56 of 56 | 100 | 86 | 100 | 0 |
| `fill-mixed-stall-no-limit` | Notice on 21 virtual, work-data on 17; work-data stops answering; no limit | 21 (work-data 17) | virtual | 1 | 0.0 | -1 | -1 | person gave up at 29 s: 600 | 77 of 77 | 600 | 104 | - | 0 |
| `opt-c-normal` | Normal load, 40 people; Java 21, no changes | 21 | platform | 3 | 12.4 (12.3 to 12.7) | 3805 | 3903 | none | 59 of 59 | 40 | 37 | 25 | 0 |
| `opt-c-overload` | 150 people; Java 21, no changes | 21 | platform | 3 | 19.2 (19.1 to 19.2) | 3287 | 4114 | HTTP 502: 2624 | 58 of 58 | 95 | 111 | 25 | 0 |
| `opt-c-stall` | Work-data stops answering; Java 21, no changes | 21 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | person gave up at 29 s: 600 | 1 of 13 | - | - | - | 0 |
| `opt-c-long-stall` | 5-minute stall; Java 21, no changes | 21 | platform | 1 | 0.0 | -1 | -1 | person gave up at 29 s: 3000 | 1 of 86 | 195 | 44 | - | 0 |
| `opt-c-slow` | Work-data answers after 20 s; Java 21, no changes | 21 | platform | 3 | 3.4 (3.2 to 3.6) | 21669 | 23439 | HTTP 502: 5 | 87 of 87 | 60 | 33 | 25 | 0 |
| `opt-c-down` | Work-data is not running; Java 21, no changes | 21 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 1000 | 39 of 39 | 50 | 37 | - | 0 |
| `opt-c-unreachable` | Work-data's address does not answer at all; Java 21, no changes | 21 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 100 | 59 of 59 | 50 | 36 | 0 | 0 |
| `opt-c-pin` | No executor, pool 100; driver holds a lock; Java 21, no changes | 21 | platform | 1 | 72.8 | 2607 | 4784 | none | 54 of 54 | 200 | 161 | 100 | 0 |
| `opt-c-cpu` | PDF-like processor work, 100 people; Java 21, no changes | 21 | platform | 1 | 20.2 | 5275 | 7161 | none | 49 of 49 | 100 | 69 | 98 | 0 |
| `opt-d-normal` | Normal load, 40 people; Java 21, MVP limits | 21 | platform | 3 | 12.3 (12.3 to 12.3) | 3841 | 3968 | none | 59 of 59 | 40 | 38 | 25 | 0 |
| `opt-d-overload` | 150 people; Java 21, MVP limits | 21 | platform | 3 | 19.2 (19.1 to 19.2) | 3230 | 3944 | HTTP 502: 2626 | 58 of 58 | 97 | 105 | 25 | 0 |
| `opt-d-stall` | Work-data stops answering; Java 21, MVP limits | 21 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | person gave up at 29 s: 600 | 2 of 13 | 65 | 33 | 5 | 0 |
| `opt-d-long-stall` | 5-minute stall; Java 21, MVP limits | 21 | platform | 1 | 0.0 | -1 | -1 | person gave up at 29 s: 3000 | 1 of 86 | - | - | - | 0 |
| `opt-d-slow` | Work-data answers after 20 s; Java 21, MVP limits | 21 | platform | 3 | 3.6 (3.2 to 3.6) | 21643 | 23139 | HTTP 502: 5 | 88 of 88 | 60 | 35 | 25 | 0 |
| `opt-d-down` | Work-data is not running; Java 21, MVP limits | 21 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 1000 | 39 of 39 | 50 | 37 | - | 0 |
| `opt-d-unreachable` | Work-data's address does not answer at all; Java 21, MVP limits | 21 | platform | 1 | 0.0 | -1 | -1 | HTTP 504: 500 | 59 of 59 | 50 | 36 | 0 | 0 |
| `opt-d-pin` | No executor, pool 100; driver holds a lock; Java 21, MVP limits | 21 | platform | 1 | 72.6 | 2620 | 4800 | none | 54 of 54 | 200 | 168 | 100 | 0 |
| `opt-d-cpu` | PDF-like processor work, 100 people; Java 21, MVP limits | 21 | platform | 1 | 21.0 | 5086 | 6510 | none | 49 of 49 | 100 | 68 | 100 | 0 |
| `opt-e-normal` | Normal load, 40 people; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 3 | 12.3 (12.3 to 12.3) | 3826 | 3973 | none | 59 of 59 | 40 | 40 | 25 | 0 |
| `opt-e-overload` | 150 people; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 3 | 9.6 (9.6 to 9.6) | 2583 | 3429 | HTTP 502: 178, HTTP 503: 3600 | 59 of 59 | 150 | 105 | 25 | 0 |
| `opt-e-stall` | Work-data stops answering; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 503: 375, person gave up at 29 s: 564 | 77 of 77 | 561 | 127 | 5 | 0 |
| `opt-e-long-stall` | 5-minute stall; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 503: 70324, person gave up at 29 s: 631 | 587 of 587 | 586 | 210 | 5 | 0 |
| `opt-e-slow` | Work-data answers after 20 s; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 3 | 3.4 (2.8 to 3.6) | 21840 | 23234 | HTTP 502: 5 | 88 of 88 | 60 | 37 | 25 | 0 |
| `opt-e-down` | Work-data is not running; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 503: 941, HTTP 504: 59 | 39 of 39 | 50 | 35 | - | 0 |
| `opt-e-unreachable` | Work-data's address does not answer at all; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 1 | 0.0 | -1 | -1 | HTTP 503: 1317, HTTP 504: 62 | 59 of 59 | 50 | 39 | 0 | 0 |
| `opt-e-pin` | No executor, pool 100; driver holds a lock; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 1 | 10.2 | 18078 | 23817 | person gave up at 29 s: 82 | 58 of 58 | 200 | 85 | 100 | 0 |
| `opt-e-cpu` | PDF-like processor work, 100 people; Java 21 virtual, MVP limits, circuit breaker | 21 | virtual | 1 | 20.0 | 5448 | 6122 | none | 57 of 57 | 100 | 90 | 100 | 0 |
| `opt-b-breaker-normal` | Normal load, 40 people; Java 17, MVP limits, circuit breaker | 17 | platform | 3 | 12.3 (12.3 to 12.3) | 3751 | 3892 | none | 59 of 59 | 40 | 31 | 25 | 0 |
| `opt-b-breaker-stall` | Work-data stops answering; Java 17, MVP limits, circuit breaker | 17 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 503: 2985, person gave up at 29 s: 303 | 20 of 28 | 200 | 73 | - | 0 |
| `opt-b-breaker-long-stall` | 5-minute stall; Java 17, MVP limits, circuit breaker | 17 | platform | 1 | 0.0 | -1 | -1 | ConnectException: 7, HTTP 503: 79333, person gave up at 29 s: 324 | 531 of 539 | 200 | 108 | - | 0 |
| `opt-b-breaker-slow` | Work-data answers after 20 s; Java 17, MVP limits, circuit breaker | 17 | platform | 3 | 3.5 (3.5 to 3.6) | 21747 | 23197 | HTTP 502: 5 | 88 of 88 | 60 | 27 | 25 | 0 |
| `opt-b-breaker-overload` | 150 people; Java 17, MVP limits, circuit breaker | 17 | platform | 3 | 9.6 (9.6 to 9.6) | 2389 | 3642 | HTTP 502: 150, HTTP 503: 3665 | 58 of 58 | 97 | 76 | 25 | 0 |
| `opt-b-breaker-timeouts-overload` | 150 people; Java 17, MVP limits, circuit breaker counting only time-outs | 17 | platform | 3 | 19.3 (19.2 to 19.4) | 3238 | 3870 | HTTP 502: 2635 | 58 of 58 | 111 | 86 | 25 | 0 |
| `opt-e-timeouts-overload` | 150 people; Java 21 virtual, MVP limits, circuit breaker counting only time-outs | 21 | virtual | 3 | 18.9 (18.8 to 18.9) | 3601 | 5509 | HTTP 502: 2377 | 59 of 59 | 117 | 187 | 25 | 0 |
| `opt-b-breaker-timeouts-stall` | Work-data stops answering; Java 17, MVP limits, circuit breaker counting only time-outs | 17 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 503: 2985, person gave up at 29 s: 303 | 20 of 28 | 200 | 118 | - | 0 |
| `opt-e-timeouts-stall` | Work-data stops answering; Java 21 virtual, MVP limits, circuit breaker counting only time-outs | 21 | virtual | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 503: 375, person gave up at 29 s: 564 | 77 of 77 | 561 | 129 | 5 | 0 |
| `opt-b-breaker-timeouts-long-stall` | 5-minute stall; Java 17, MVP limits, circuit breaker counting only time-outs | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 503: 79303, person gave up at 29 s: 324 | 530 of 538 | 200 | 108 | 5 | 0 |
| `opt-e-timeouts-long-stall` | 5-minute stall; Java 21 virtual, MVP limits, circuit breaker counting only time-outs | 21 | virtual | 1 | 0.0 | -1 | -1 | ConnectException: 13, HTTP 503: 70321, person gave up at 29 s: 627 | 587 of 587 | 600 | 150 | 5 | 0 |
| `opt-b-breaker-timeouts-slow` | Work-data answers after 20 s; Java 17, MVP limits, circuit breaker counting only time-outs | 17 | platform | 3 | 3.6 (3.4 to 3.7) | 21559 | 23114 | HTTP 502: 5 | 88 of 88 | 60 | 27 | 25 | 0 |
| `opt-e-timeouts-slow` | Work-data answers after 20 s; Java 21 virtual, MVP limits, circuit breaker counting only time-outs | 21 | virtual | 3 | 3.6 (3.2 to 3.6) | 21822 | 23093 | HTTP 502: 5 | 88 of 88 | 60 | 37 | 25 | 0 |
| `opt-b-breaker-timeouts-down` | Work-data is not running; Java 17, MVP limits, circuit breaker counting only time-outs | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 503: 941, HTTP 504: 59 | 39 of 39 | 50 | 72 | - | 0 |
| `opt-b-breaker-timeouts-unreachable` | Work-data's address does not answer at all; Java 17, MVP limits, circuit breaker counting only time-outs | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 503: 1317, HTTP 504: 62 | 59 of 59 | 50 | 63 | 0 | 0 |
| `opt-b-breaker-timeouts-pin` | No executor, pool 100; driver holds a lock; Java 17, MVP limits, circuit breaker counting only time-outs | 17 | platform | 1 | 73.3 | 2617 | 4565 | none | 55 of 55 | 200 | 87 | 100 | 0 |
| `opt-b-breaker-timeouts-cpu` | PDF-like processor work, 100 people; Java 17, MVP limits, circuit breaker counting only time-outs | 17 | platform | 1 | 20.5 | 5048 | 7347 | none | 56 of 56 | 100 | 72 | 100 | 0 |
| `opt-b-bulkhead-normal` | Normal load, 40 people; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 50 | 17 | platform | 3 | 12.3 (12.3 to 12.3) | 3825 | 3973 | none | 59 of 59 | 40 | 100 | 25 | 0 |
| `opt-b-bulkhead-overload` | 150 people; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 50 | 17 | platform | 3 | 16.3 (16.3 to 16.3) | 3393 | 3836 | HTTP 503: 2900 | 57 of 57 | 59 | 154 | 25 | 0 |
| `opt-b-bulkhead-stall` | Work-data stops answering; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 50 | 17 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 503: 10226, person gave up at 29 s: 54 | 77 of 77 | 61 | 173 | 5 | 0 |
| `opt-b-bulkhead-long-stall` | 5-minute stall; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 50 | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 503: 86130, person gave up at 29 s: 93 | 587 of 587 | 60 | 183 | 5 | 0 |
| `opt-b-bulkhead-slow` | Work-data answers after 20 s; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 50 | 17 | platform | 3 | 3.1 (3.1 to 3.1) | 21423 | 24207 | HTTP 503: 450 | 88 of 88 | 58 | 36 | 25 | 0 |
| `opt-b-bulkhead60-overload` | 150 people; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 3 | 19.4 (19.2 to 19.5) | 3126 | 3807 | HTTP 502: 670, HTTP 503: 2014 | 58 of 58 | 69 | 152 | 25 | 0 |
| `opt-b-bulkhead60-stall` | Work-data stops answering; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 3 | 0.0 (0.0 to 0.0) | -1 | -1 | HTTP 503: 9847, person gave up at 29 s: 63 | 76 of 76 | 78 | 153 | 5 | 0 |
| `opt-b-bulkhead60-long-stall` | 5-minute stall; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 503: 85798, person gave up at 29 s: 104 | 588 of 588 | 70 | 86 | 5 | 0 |
| `opt-b-bulkhead60-slow` | Work-data answers after 20 s; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 3 | 3.6 (3.5 to 3.6) | 21561 | 23335 | HTTP 502: 5 | 88 of 88 | 60 | 32 | 25 | 0 |
| `opt-b-bulkhead60-normal` | Normal load, 40 people; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 3 | 12.8 (12.8 to 12.8) | 3742 | 3823 | none | 59 of 59 | 40 | 98 | 25 | 0 |
| `opt-b-bulkhead60-down` | Work-data is not running; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 503: 941, HTTP 504: 59 | 39 of 39 | 50 | 59 | - | 0 |
| `opt-b-bulkhead60-unreachable` | Work-data's address does not answer at all; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 1 | 0.0 | -1 | -1 | HTTP 503: 1317, HTTP 504: 62 | 59 of 59 | 50 | 71 | 0 | 0 |
| `opt-b-bulkhead60-pin` | No executor, pool 100; driver holds a lock; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 1 | 44.0 | 1364 | 1456 | HTTP 503: 4060 | 57 of 57 | 71 | 151 | 60 | 0 |
| `opt-b-bulkhead60-cpu` | PDF-like processor work, 100 people; Java 17, MVP limits, circuit breaker counting only time-outs, bulkhead of 60 | 17 | platform | 1 | 28.0 | 2134 | 2802 | HTTP 503: 1163 | 57 of 57 | 68 | 165 | 60 | 0 |

## Calls stuck in the ticket service (notice-app) during the 5-minute stalls, every 30 seconds

| Run | Stuck calls |
|---|---|
| `long-stall-no-limit-17` | 75 |
| `long-stall-no-limit-21-virtual` | 35, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000 |
| `long-stall-option-a-21-virtual` | 205, 287, 300, 300, 300, 300, 300, 300, 300, 300 |
| `fill-long-stall-option-a-17` | 0 |
| `opt-c-long-stall` | 195 |
| `opt-e-long-stall` | 71, 286, 3, 6, 6, 6, 6, 6, 3, 3 |
| `opt-b-breaker-long-stall` | 18, 3, 3, 3 |
| `opt-b-breaker-timeouts-long-stall` | 39, 3, 3, 3 |
| `opt-e-timeouts-long-stall` | 66, 300, 4, 3, 6, 3, 3, 3, 3, 4 |
| `opt-b-bulkhead-long-stall` | 50, 13, 3, 6, 6, 3, 3, 4, 3, 0 |
| `opt-b-bulkhead60-long-stall` | 60, 20, 3, 3, 3, 3, 3, 3, 3, 0 |
