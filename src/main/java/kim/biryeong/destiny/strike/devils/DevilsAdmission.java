package kim.biryeong.destiny.strike.devils;

import java.util.Collection;
import java.util.UUID;
import java.util.function.Predicate;

/** Explicit personal departure releases admission without weakening a retained member's readiness. */
final class DevilsAdmission {
    private DevilsAdmission() { }
    static int count(Collection<DevilsRoster.Member> roster, Predicate<UUID> retained) {
        return (int) roster.stream().filter(m -> retained.test(m.id())).count();
    }
    static boolean ready(Collection<DevilsRoster.Member> roster, Predicate<UUID> retained) {
        return count(roster, retained) > 0 && roster.stream().filter(m -> retained.test(m.id()))
                .allMatch(m -> m.connected() && m.ready() && !m.expired());
    }
}
