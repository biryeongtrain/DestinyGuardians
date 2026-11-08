package kim.biryeong.destiny.strike;

import kim.biryeong.destiny.activity.strike.Strikes;
import kim.biryeong.destiny.strike.devils.DevilsLair;
import kim.biryeong.destiny.strike.exodus.ExodusCrash;

/**
 * The strikes this mod ships. A new strike adds one line here; the finder listing, the personal-exit command and the
 * combat/ability gates all read {@link Strikes}. Runs before the finder builds its catalog.
 */
public final class StrikeLineup {
    private static boolean registered;
    private StrikeLineup() { }

    public static void register() {
        if (registered) return;
        registered = true;
        Strikes.register(DevilsLair.COORDINATOR);
        Strikes.register(ExodusCrash.COORDINATOR);
    }
}
