# Results

Written by `lab/run_lab.py`. Do not edit by hand.

Settings: the defaults (5 connections, 10 pizzas, 6 people). Each run repeated 3 times; the middle result is shown.

| Scenario | java-17 (Java 17.0.21, platform threads) | java-21 (Java 21.0.12.1, platform threads) | java-21-virtual (Java 21.0.12.1, virtual threads) |
|---|---|---|---|
| 1. One person, pizzas already have a ready time (control) | OK: 2.0 s, 1 of 1 through, 0 snapshots lost, 0 retries, 0 gave up | OK: 2.0 s, 1 of 1 through, 0 snapshots lost, 0 retries, 0 gave up | OK: 2.0 s, 1 of 1 through, 0 snapshots lost, 0 retries, 0 gave up |
| 2. 6 people, first send, no ready times yet (control) | OK: 3.0 s, 6 of 6 through, 0 snapshots lost, 0 retries, 0 gave up | OK: 2.9 s, 6 of 6 through, 0 snapshots lost, 0 retries, 0 gave up | OK: 2.9 s, 6 of 6 through, 0 snapshots lost, 0 retries, 0 gave up |
| 3. 6 people, second send, pizzas already have a ready time (the problem) | PROBLEM: 21.6 s, 5 of 6 through, 50 snapshots lost, 4 retries, 1 gave up | PROBLEM: 21.6 s, 5 of 6 through, 50 snapshots lost, 4 retries, 1 gave up | PROBLEM: 21.6 s, 5 of 6 through, 50 snapshots lost, 4 retries, 1 gave up |
| 4. One person updates 50 pizzas; the kitchen screen changes one of them meanwhile | BLOCKED: kitchen screen waited 9.1 of 9.5 s | BLOCKED: kitchen screen waited 9.2 of 9.6 s | BLOCKED: kitchen screen waited 9.1 of 9.6 s |
| 5. Fix: same as 3, snapshot on the same connection | OK: 3.9 s, 6 of 6 through, 0 snapshots lost, 0 retries, 0 gave up | OK: 3.9 s, 6 of 6 through, 0 snapshots lost, 0 retries, 0 gave up | OK: 3.9 s, 6 of 6 through, 0 snapshots lost, 0 retries, 0 gave up |
| 6. Fix under heavier load: 12 people, second send | BUSY: 5.9 s, 12 of 12 through, 0 snapshots lost, 2 retries, 0 gave up | BUSY: 5.9 s, 12 of 12 through, 0 snapshots lost, 2 retries, 0 gave up | BUSY: 5.9 s, 12 of 12 through, 0 snapshots lost, 2 retries, 0 gave up |

Raw output: [java-17.txt](java-17.txt), [java-21.txt](java-21.txt), [java-21-virtual.txt](java-21-virtual.txt)
