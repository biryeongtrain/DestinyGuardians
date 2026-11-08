package kim.biryeong.destiny.activity.strike;

import java.util.Collection;
import java.util.UUID;
import java.util.function.Predicate;

/** Explicit personal departure releases admission without weakening a retained member's readiness. */
public final class StrikeAdmission {
    private StrikeAdmission() { }
    public static int count(Collection<StrikeRoster.Member> roster, Predicate<UUID> retained) {
        return (int) roster.stream().filter(m -> retained.test(m.id())).count();
    }
    public static boolean ready(Collection<StrikeRoster.Member> roster, Predicate<UUID> retained) {
        return count(roster, retained) > 0 && roster.stream().filter(m -> retained.test(m.id()))
                .allMatch(m -> m.connected() && m.ready() && !m.expired());
    }
}
