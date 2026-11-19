# When One Request Needs Two Connections: How a Connection Pool Locks Up

## A lab test on Java 17 and Java 21, using a made-up pizza shop

**Classification:** Internal: Engineering Reference
**Prepared by:** the engineering team
**Date:** 2026-11-19
**Version:** 1.0
**Status:** Published
**Lab code:** [lab/](lab/)
**Results:** [results/RESULTS.md](results/RESULTS.md) (raw figures in [results/results.json](results/results.json))

---

## In short

- **The problem:** a request holds one database connection for its transaction, then asks the same pool for a second one. When as many people send at once as there are connections, every request holds one and waits for another, so nobody can finish. The pool locks up.
- **The Java version makes no difference.** Java 17, Java 21, and Java 21 with virtual threads gave the same result in every scenario, three repeats each.
- **The fix is in the code, not the platform:** do all the work on the one connection the request already holds.
- **Retries make it worse.** The till tries a failed call 5 times, so a full pool gets more requests, not fewer.
- **One long transaction also blocks other screens.** While one big order is being updated, the kitchen screen waited 9.1 of the 9.6 seconds just to change one pizza.

![The problem and the fix side by side. Left: five requests each hold one of five connections and wait for a second that never comes, and a sixth gets none; 50 history snapshots are lost and 1 of 6 people gives up, taking 21.6 seconds. Right: each request does its work on one connection and gives it back; all 6 finish in 3.9 seconds with nothing lost.](assets/pool-problem-and-fix.png)

*Drawn by [assets/build_pool_problem.py](assets/build_pool_problem.py) from [results/results.json](results/results.json).*

---

## 1. The shop and the shape being tested

The pizza shop has two parts:

- **The till:** staff press "send" to set the ready time for every pizza on an order, all in one call. If the call fails, the till tries again, up to 5 times, 1 second apart.
- **The order service:** takes that call and updates every pizza in **one database transaction** (a group of changes saved together or not at all). It uses a **connection pool**: a fixed number of open database connections shared by every request.

For each pizza that **already has a ready time**, the order service also saves a **history snapshot** (a copy of the old value). The defect is how it does that:

1. It already holds connection 1 for the transaction.
2. It asks the pool for **connection 2** to write the snapshot.
3. If connection 2 doesn't come in time, it logs the error and carries on, so the snapshot is lost without anyone noticing.

The first send for an order is fine, because no pizza has a ready time yet, so no second connection is needed. **Sending again** is what triggers it.

## 2. How the lab works

- One Java file, [lab/PizzaPoolLab.java](lab/PizzaPoolLab.java), with an in-memory H2 database and a HikariCP pool. No servers to install.
- Waits are scaled down so a run takes about a minute: 5 connections, 2 seconds to wait for a free connection, 40 ms per database round trip, 10 pizzas per order, 6 people.
- Each person runs on their own thread so that everyone presses send at the same moment. That is test scaffolding only, not a pattern to copy.
- [lab/run_lab.py](lab/run_lab.py) runs the same file three ways, three times each, and reports the middle result:
  - Java 17 (17.0.21)
  - Java 21 (21.0.12.1)
  - Java 21 with each person on a **virtual thread** (Java 21's lightweight threads)

## 3. Results

| Scenario | Java 17 | Java 21 | Java 21, virtual threads |
|---|---|---|---|
| 1. One person, pizzas already have a ready time | OK, but one request used 2 connections at once | Same | Same |
| 2. 6 people, first send | OK, 2.9 to 3.0 s | Same | Same |
| 3. 6 people, second send (**the problem**) | **Locked up:** 21.6 s, 50 snapshots lost, 4 retries, 1 of 6 gave up | Same | Same |
| 4. One 50-pizza update while the kitchen screen edits one pizza | **Blocked:** the screen waited 9.1 s of 9.5 s | Same (9.2 of 9.6 s) | Same (9.1 of 9.6 s) |
| 5. The fix, same load as 3 | OK: all 6 in 3.9 s, nothing lost | Same | Same |
| 6. The fix under twice the load (12 people) | Busy: 2 retries, all 12 got through in 5.9 s | Same | Same |

Full table, every repeat: [results/RESULTS.md](results/RESULTS.md).

One Java 17 repeat of scenario 6 took 8.0 s with 9 retries. The other two took 5.8 and 5.9 s with 2 retries, the same as Java 21. That first run was the Java start-up warming up, not a difference between versions.

### Why the Java version can't help

- The lock-up is about **counting**: 5 connections, 6 requests, each needing 2. No Java version changes that sum.
- **Virtual threads** make waiting cheap, but a virtual thread waiting for a connection is still waiting. They let more people wait at once. They don't make more connections.
- The scenarios with no lock-up (2, 5, 6) are limited by database round trips, not by Java, so they also came out the same.

## 4. What to do

In order, most important first:

1. **Use one connection per request.** Write the snapshot inside the same transaction, on the connection already held (scenario 5). This removes the lock-up on its own.
2. **Never ignore a failed write.** If the snapshot can't be saved, the request should fail and say so. A lost history record with only a log line is a silent data problem.
3. **Make the till try less.** A read can fail fast and show a clear message. A write should try at most once or twice, with a growing pause between tries.
4. **Keep transactions short.** Update the pizzas in one statement for the whole order, or in small groups, so row locks are held for milliseconds, not seconds (scenario 4).
5. **Put time limits on everything:** how long to wait for a connection, how long a query may run, and how long a transaction may stay open. A request that will never finish should end with a clear error, not hold a connection.
6. **Give separate jobs separate pools.** If a busy lookup screen shares the same pool as the order updates, one can starve the other. A small pool of its own for each kind of work is called a **bulkhead** (from the walls that stop one flooded section of a ship sinking the rest). Most application servers can do this in configuration, with no new code.
7. **Watch the pool.** Alert on "requests waiting for a connection" above zero for more than a few seconds. That number rose to 6 in scenario 3 before anything else showed a problem.

## 5. A related pattern to look for: one call per line

The same shop has a second, slower version of the problem. For an order of 1,000 pizzas, a screen that makes 3 lookups **per pizza** sends 3,000 calls to the order service, and each holds a connection while it runs. Look for loops that call the database or another service once per line, and replace them with one call for the whole order that returns everything at once.

## 6. What this lab doesn't show

- **That a real outage was caused by this.** For that you need the server logs, thread dumps (a snapshot of what every thread was doing) and the database's record of who was blocking whom.
- **Real sizes.** The numbers are scaled down. Try `python lab/run_lab.py -Dpool=20 -Dpizzas=50 -Dstaff=21` to see the same shape at a larger size.
- **Other databases and drivers.** H2 stands in for a production database. Locking and driver behaviour differ in the detail, not in the counting.

## 7. Run it yourself

Needs Python 3.8+, Java 17 and Java 21, and three jars in the local Maven cache (H2 2.2.224, HikariCP 5.0.1, SLF4J API 2.0.18). If a jar is missing, the script prints the `mvn` command to fetch it.

```powershell
python papers/connection-pool-lockup-lab/lab/run_lab.py                 # all scenarios, 3 repeats
python papers/connection-pool-lockup-lab/lab/run_lab.py --repeats 1 -Dscenario=3,5
python papers/connection-pool-lockup-lab/assets/build_pool_problem.py   # redraw the picture
```

Point the script at your JDKs with `JAVA17_HOME` and `JAVA21_HOME` if it can't find them.

| File | What it does |
|---|---|
| [lab/PizzaPoolLab.java](lab/PizzaPoolLab.java) | The till, the order service, the six scenarios and the counters |
| [lab/run_lab.py](lab/run_lab.py) | Runs it on each Java, repeats, writes the results |
| [assets/build_pool_problem.py](assets/build_pool_problem.py) | Draws the picture from the results |
| [results/](results/) | `RESULTS.md`, `results.json` and the raw output of every run |
