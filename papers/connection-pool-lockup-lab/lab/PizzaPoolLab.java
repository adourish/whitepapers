import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariPoolMXBean;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * A pizza shop's order service, on an in-memory database, to show how a database connection
 * pool locks up when one request needs two connections at the same time.
 *
 * The shape being tested:
 *  - The till sends "set the ready time" for every pizza on an order in one call.
 *  - The order service updates every pizza in one transaction (connection 1).
 *  - For each pizza that already has a ready time, it saves a change-history snapshot on a
 *    SECOND connection from the same pool. If that connection does not come, the error is
 *    logged and ignored, so the snapshot is lost and the request carries on.
 *  - The till tries a failed call up to 5 times, 1 second apart.
 *
 * Waits and network time are scaled down so a run takes about a minute.
 * The threads only stand in for staff pressing "send" at the same time. They are test
 * scaffolding, not a pattern to copy. With -Dthreads=virtual (Java 21 and later) each person is
 * a virtual thread instead, to show whether the Java version or thread type changes the result.
 * The same source runs on Java 17 and Java 21.
 */
public class PizzaPoolLab {

    // ---- Settings (override with -Dname=value) -------------------------------------------------
    static final int POOL_SIZE = Integer.getInteger("pool", 5);              // connections in the pool
    static final long POOL_WAIT_MS = Long.getLong("poolWaitMs", 2000);       // wait for a free connection
    static final long ROUND_TRIP_MS = Long.getLong("roundTripMs", 40);       // network time per query
    static final int PIZZAS = Integer.getInteger("pizzas", 10);              // pizzas per order
    static final int STAFF = Integer.getInteger("staff", POOL_SIZE + 1);     // people pressing send at once
    static final int TILL_TRIES = Integer.getInteger("tries", 5);            // how often the till tries
    static final long TILL_RETRY_PAUSE_MS = Long.getLong("retryPauseMs", 1000);
    static final String THREADS = System.getProperty("threads", "platform"); // platform or virtual

    enum Snapshot { SECOND_CONNECTION, SAME_CONNECTION }

    static HikariDataSource pool;

    // ---- Results of one scenario ---------------------------------------------------------------
    static final AtomicInteger requestsOk = new AtomicInteger();
    static final AtomicInteger requestsFailed = new AtomicInteger();
    static final AtomicInteger staffGaveUp = new AtomicInteger();
    static final AtomicInteger retries = new AtomicInteger();
    static final AtomicInteger snapshotsLost = new AtomicInteger();
    static final AtomicLong longestRequestMs = new AtomicLong();
    static volatile int peakInUse, peakWaiting;

    public static void main(String[] args) throws Exception {
        System.out.println("Pizza shop connection pool lab");
        System.out.printf("Java %s (%s), %s threads%n", System.getProperty("java.version"),
                System.getProperty("java.vendor"), THREADS);
        System.out.printf("Pool %d connections, wait for a connection %d ms, %d ms per database round trip,%n",
                POOL_SIZE, POOL_WAIT_MS, ROUND_TRIP_MS);
        System.out.printf("%d pizzas per order, the till tries %d times, %d ms apart.%n%n",
                PIZZAS, TILL_TRIES, TILL_RETRY_PAUSE_MS);

        pool = createPool();
        createTables();

        String only = System.getProperty("scenario", "all");
        if (want(only, "1")) scenario("1. One person, pizzas already have a ready time (control)",
                1, true, Snapshot.SECOND_CONNECTION);
        if (want(only, "2")) scenario("2. " + STAFF + " people, first send, no ready times yet (control)",
                STAFF, false, Snapshot.SECOND_CONNECTION);
        if (want(only, "3")) scenario("3. " + STAFF + " people, second send, pizzas already have a ready time (the problem)",
                STAFF, true, Snapshot.SECOND_CONNECTION);
        if (want(only, "4")) blockingScenario();
        if (want(only, "5")) scenario("5. Fix: same as 3, snapshot on the same connection",
                STAFF, true, Snapshot.SAME_CONNECTION);
        if (want(only, "6")) scenario("6. Fix under heavier load: " + (STAFF * 2) + " people, second send",
                STAFF * 2, true, Snapshot.SAME_CONNECTION);

        pool.close();
    }

    static boolean want(String only, String n) {
        return only.equals("all") || List.of(only.split(",")).contains(n);
    }

    // ---- Set up --------------------------------------------------------------------------------

    static HikariDataSource createPool() {
        HikariConfig c = new HikariConfig();
        // LOCK_TIMEOUT: how long a session waits for a row another session has locked
        c.setJdbcUrl("jdbc:h2:mem:pizza;DB_CLOSE_DELAY=-1;LOCK_TIMEOUT=120000");
        c.setMaximumPoolSize(POOL_SIZE);
        c.setMinimumIdle(POOL_SIZE);
        c.setConnectionTimeout(Math.max(250, POOL_WAIT_MS));
        c.setPoolName("order-pool");
        return new HikariDataSource(c);
    }

    static void createTables() throws SQLException {
        try (Connection c = pool.getConnection(); Statement s = c.createStatement()) {
            s.execute("CREATE TABLE order_pizza (order_id INT, pizza_num INT, ready_time TIMESTAMP, oven VARCHAR(40),"
                    + " PRIMARY KEY (order_id, pizza_num))");
            s.execute("CREATE TABLE pizza_snapshot (id IDENTITY, order_id INT, pizza_num INT, ready_time TIMESTAMP)");
            s.execute("CREATE TABLE pizza_history (order_id INT, pizza_num INT, remarks VARCHAR(2000),"
                    + " PRIMARY KEY (order_id, pizza_num))");
        }
    }

    /** Gives each person their own order, so only the pool (not row locks) is shared. */
    static void loadOrders(int orders, int pizzas, boolean withReadyTimes) throws SQLException {
        try (Connection c = pool.getConnection(); Statement s = c.createStatement()) {
            s.execute("DELETE FROM order_pizza");
            s.execute("DELETE FROM pizza_snapshot");
            s.execute("DELETE FROM pizza_history");
            try (PreparedStatement p = c.prepareStatement("INSERT INTO order_pizza VALUES (?, ?, ?, 'OVEN 1')")) {
                for (int o = 1; o <= orders; o++) {
                    for (int z = 1; z <= pizzas; z++) {
                        p.setInt(1, o);
                        p.setInt(2, z);
                        p.setTimestamp(3, withReadyTimes ? new java.sql.Timestamp(System.currentTimeMillis()) : null);
                        p.executeUpdate();
                    }
                }
            }
        }
    }

    // ---- The order service ---------------------------------------------------------------------

    /** Sets the ready time for every pizza on the order, in one transaction. */
    static void setReadyTimes(int orderId, int pizzas, Snapshot mode) throws SQLException {
        try (Connection tx = pool.getConnection()) {            // the transaction's connection
            tx.setAutoCommit(false);
            try {
                for (int pizza = 1; pizza <= pizzas; pizza++) {
                    boolean hasReadyTime = readPizza(tx, orderId, pizza);
                    if (hasReadyTime) {
                        if (mode == Snapshot.SECOND_CONNECTION) {
                            snapshotOnSecondConnection(orderId, pizza);
                        } else {
                            insertSnapshot(tx, orderId, pizza);
                        }
                    }
                    upsertHistory(tx, orderId, pizza);
                    updatePizza(tx, orderId, pizza);
                }
                roundTrip();
                tx.commit();
            } catch (SQLException e) {
                tx.rollback();
                throw e;
            }
        }
    }

    /** The defect: takes its own connection from the same pool, and ignores any error. */
    static void snapshotOnSecondConnection(int orderId, int pizza) {
        try (Connection second = pool.getConnection()) {        // a second connection, while holding the first
            insertSnapshot(second, orderId, pizza);              // runs outside the main transaction
        } catch (SQLException e) {
            snapshotsLost.incrementAndGet();                     // logged and ignored: the snapshot is lost
        }
    }

    static boolean readPizza(Connection c, int orderId, int pizza) throws SQLException {
        roundTrip();
        try (PreparedStatement p = c.prepareStatement(
                "SELECT ready_time FROM order_pizza WHERE order_id = ? AND pizza_num = ?")) {
            p.setInt(1, orderId);
            p.setInt(2, pizza);
            try (ResultSet r = p.executeQuery()) {
                return r.next() && r.getTimestamp(1) != null;
            }
        }
    }

    static void insertSnapshot(Connection c, int orderId, int pizza) throws SQLException {
        roundTrip();
        try (PreparedStatement p = c.prepareStatement(
                "INSERT INTO pizza_snapshot (order_id, pizza_num, ready_time)"
                        + " SELECT order_id, pizza_num, ready_time FROM order_pizza WHERE order_id = ? AND pizza_num = ?")) {
            p.setInt(1, orderId);
            p.setInt(2, pizza);
            p.executeUpdate();
        }
    }

    static void upsertHistory(Connection c, int orderId, int pizza) throws SQLException {
        roundTrip();
        try (PreparedStatement p = c.prepareStatement(
                "MERGE INTO pizza_history KEY (order_id, pizza_num) VALUES (?, ?, 'Ready time changed')")) {
            p.setInt(1, orderId);
            p.setInt(2, pizza);
            p.executeUpdate();
        }
    }

    static void updatePizza(Connection c, int orderId, int pizza) throws SQLException {
        roundTrip();
        try (PreparedStatement p = c.prepareStatement(
                "UPDATE order_pizza SET ready_time = CURRENT_TIMESTAMP WHERE order_id = ? AND pizza_num = ?")) {
            p.setInt(1, orderId);
            p.setInt(2, pizza);
            p.executeUpdate();                                   // this row stays locked until commit
        }
    }

    static void roundTrip() {
        sleep(ROUND_TRIP_MS);
    }

    // ---- The till ------------------------------------------------------------------------------

    /** The till: tries a failed call up to 5 times, 1 second apart. */
    static void tillSend(int orderId, int pizzas, Snapshot mode) {
        for (int attempt = 1; attempt <= TILL_TRIES; attempt++) {
            long start = System.currentTimeMillis();
            try {
                setReadyTimes(orderId, pizzas, mode);
                requestsOk.incrementAndGet();
                longestRequestMs.accumulateAndGet(System.currentTimeMillis() - start, Math::max);
                return;
            } catch (SQLException e) {
                requestsFailed.incrementAndGet();
                longestRequestMs.accumulateAndGet(System.currentTimeMillis() - start, Math::max);
                if (attempt < TILL_TRIES) {
                    retries.incrementAndGet();
                    sleep(TILL_RETRY_PAUSE_MS);
                }
            }
        }
        staffGaveUp.incrementAndGet();
    }

    // ---- Scenarios -----------------------------------------------------------------------------

    static void scenario(String title, int staff, boolean pizzasHaveReadyTimes, Snapshot mode) throws Exception {
        System.out.println("== " + title);
        loadOrders(staff, PIZZAS, pizzasHaveReadyTimes);
        reset();
        long start = System.currentTimeMillis();
        Thread watcher = startPoolWatcher();

        CountDownLatch go = new CountDownLatch(1);
        List<Thread> people = new ArrayList<>();
        for (int u = 1; u <= staff; u++) {
            final int orderId = u;
            people.add(startPerson("person-" + u, () -> {
                await(go);
                tillSend(orderId, PIZZAS, mode);
            }));
        }
        go.countDown();                                          // everyone presses send together
        for (Thread t : people) t.join();
        watcher.interrupt();

        report(System.currentTimeMillis() - start, staff);
    }

    /** Scenario 4: one big update holds row locks; the kitchen screen waits on one of those pizzas. */
    static void blockingScenario() throws Exception {
        int bigOrder = Math.max(PIZZAS, 50);
        System.out.println("== 4. One person updates " + bigOrder + " pizzas; the kitchen screen changes one of them meanwhile");
        loadOrders(1, bigOrder, true);
        reset();

        long start = System.currentTimeMillis();
        Thread big = startPerson("person-a", () -> tillSend(1, bigOrder, Snapshot.SECOND_CONNECTION));
        sleep(Math.max(200, ROUND_TRIP_MS * 10));                // let it lock the first pizzas

        long waitStart = System.currentTimeMillis();
        try (Connection other = pool.getConnection()) {          // the kitchen screen moving pizza 1 to oven 2
            other.setAutoCommit(false);
            try (PreparedStatement p = other.prepareStatement(
                    "UPDATE order_pizza SET oven = 'OVEN 2' WHERE order_id = 1 AND pizza_num = 1")) {
                p.executeUpdate();                               // waits for the row lock
            }
            other.commit();
        }
        long waited = System.currentTimeMillis() - waitStart;
        big.join();
        long total = System.currentTimeMillis() - start;

        System.out.printf("   The big update took %.1f s.%n", total / 1000.0);
        System.out.printf("   The kitchen screen waited %.1f s to change one pizza (blocked by the big update's lock).%n",
                waited / 1000.0);
        System.out.println("   Result: " + (waited > total / 2
                ? "BLOCKED - the kitchen screen had to wait for the whole update to finish."
                : "not blocked") + "\n");
    }

    /** Starts one person as a platform thread, or as a virtual thread on Java 21 and later. */
    static Thread startPerson(String name, Runnable work) throws Exception {
        if (THREADS.equals("virtual")) {
            // Called by reflection so the same source still compiles and runs on Java 17
            return (Thread) Thread.class.getMethod("startVirtualThread", Runnable.class).invoke(null, work);
        }
        Thread t = new Thread(work, name);
        t.start();
        return t;
    }

    // ---- Measuring -----------------------------------------------------------------------------

    static void reset() {
        requestsOk.set(0);
        requestsFailed.set(0);
        staffGaveUp.set(0);
        retries.set(0);
        snapshotsLost.set(0);
        longestRequestMs.set(0);
        peakInUse = 0;
        peakWaiting = 0;
    }

    static Thread startPoolWatcher() {
        HikariPoolMXBean m = pool.getHikariPoolMXBean();
        Thread t = new Thread(() -> {
            while (!Thread.currentThread().isInterrupted()) {
                peakInUse = Math.max(peakInUse, m.getActiveConnections());
                peakWaiting = Math.max(peakWaiting, m.getThreadsAwaitingConnection());
                try {
                    Thread.sleep(20);
                } catch (InterruptedException e) {
                    return;
                }
            }
        }, "pool-watcher");
        t.setDaemon(true);
        t.start();
        return t;
    }

    static void report(long elapsedMs, int staff) {
        System.out.printf("   Took %.1f s. Longest single request %.1f s.%n", elapsedMs / 1000.0, longestRequestMs.get() / 1000.0);
        System.out.printf("   Pool: at most %d of %d connections in use, at most %d requests waiting for one.%n",
                peakInUse, POOL_SIZE, peakWaiting);
        System.out.printf("   Requests: %d finished, %d failed, %d till retries, %d of %d people gave up.%n",
                requestsOk.get(), requestsFailed.get(), retries.get(), staffGaveUp.get(), staff);
        System.out.printf("   History snapshots lost (error ignored): %d.%n", snapshotsLost.get());

        String verdict;
        if (snapshotsLost.get() > 0) {
            verdict = "PROBLEM - the pool ran out: requests waited for a second connection that never came.";
        } else if (staffGaveUp.get() > 0) {
            verdict = "PROBLEM - some people never got through.";
        } else if (requestsFailed.get() > 0) {
            verdict = "BUSY - the pool was full for a moment and some requests had to try again, "
                    + "but everyone got through.";
        } else {
            verdict = "OK - every request finished.";
        }
        if (peakInUse >= 2 && staff == 1) {
            verdict += " Note: one request used " + peakInUse + " connections at once.";
        }
        System.out.println("   Result: " + verdict + "\n");
    }

    // ---- Small helpers -------------------------------------------------------------------------

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    static void await(CountDownLatch l) {
        try {
            l.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
