package lab.workdata;

import java.util.concurrent.Semaphore;

/**
 * Runs inside the H2 server process, not in the app. A call to WAN_SLEEP(60) makes the database
 * take 60 ms to answer, standing in for one round trip across the WAN to the Oracle database
 * (40 to 80 ms each). The app's thread waits on the socket the whole time, as it does with Oracle.
 */
public final class WanSleep {
    /**
     * How many calls the database works on at once (-Dlab.db.sessions on the H2 server). The rest
     * queue, as they would on a busy Oracle server. Unset means no limit.
     */
    private static final Semaphore SESSIONS = new Semaphore(Integer.getInteger("lab.db.sessions", 1_000_000), true);

    private WanSleep() {
    }

    public static int sleep(int ms) throws InterruptedException {
        SESSIONS.acquire();
        try {
            Thread.sleep(ms);
        } finally {
            SESSIONS.release();
        }
        return ms;
    }
}
