package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;

/** Pure policy tests; main also supports an in-memory JDK-only smoke run without Gradle/Minecraft. */
class WeaponHitStateW223Test {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    @Test
    void invalidDamageCannotCreateOrRefreshEvenAKill() {
        var idle = WeaponHitState.idle();
        var hit = idle.confirm(20, 1, false);
        for (float damage : new float[] {0, -1, Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY}) {
            check(idle.confirm(21, damage, true) == idle, "invalid damage created a kill");
            check(hit.confirm(23, damage, true) == hit, "invalid damage refreshed or promoted a hit");
        }
        check(hit.cueAt(24) == WeaponHitState.Cue.NONE, "invalid events extended expiry");
        check(idle.confirm(1, Float.MIN_VALUE, false).cueAt(1) == WeaponHitState.Cue.HIT,
                "finite positive observed loss must qualify");
    }

    @Test
    void exactBoundariesAndOrdinaryRefresh() {
        var hit = WeaponHitState.idle().confirm(100, 3, false);
        check(hit.cueAt(99) == WeaponHitState.Cue.NONE, "future hit leaked backward");
        check(hit.cueAt(100) == WeaponHitState.Cue.HIT, "hit did not appear immediately");
        check(hit.cueAt(103) == WeaponHitState.Cue.HIT, "hit expired early");
        check(hit.cueAt(104) == WeaponHitState.Cue.NONE, "hit outlived finite duration");
        var refreshed = hit.confirm(103, 2, false);
        check(refreshed.cueAt(106) == WeaponHitState.Cue.HIT, "actual ordinary hit did not refresh");
        check(refreshed.cueAt(107) == WeaponHitState.Cue.NONE, "refreshed hit did not expire");
    }

    @Test
    void pelletOrderCannotDowngradeOrExtendKill() {
        var hitFirst = WeaponHitState.idle().confirm(50, 2, false).confirm(50, 2, true);
        var killFirst = WeaponHitState.idle().confirm(50, 2, true).confirm(50, 2, false);
        for (long now = 50; now <= 58; now++) {
            check(hitFirst.cueAt(now) == killFirst.cueAt(now), "same-tick pellet order changed emphasis");
        }
        var aggregated = killFirst;
        for (long now = 50; now < 57; now++) {
            for (int pellet = 0; pellet < 32; pellet++) aggregated = aggregated.confirm(now, 1, false);
            check(aggregated == killFirst, "ordinary pellet queued or extended active kill");
        }
        check(aggregated.cueAt(56) == WeaponHitState.Cue.KILL, "later pellet lost kill emphasis");
        check(aggregated.cueAt(57) == WeaponHitState.Cue.NONE, "ordinary hit kept red alive");
        check(aggregated.confirm(57, 1, false).cueAt(57) == WeaponHitState.Cue.HIT,
                "ordinary hit after expiry must become white");
    }

    @Test
    void anotherActualKillCanRefreshButSameTickDeduplicates() {
        var kill = WeaponHitState.idle().confirm(10, 1, true);
        check(kill.confirm(10, 5, true) == kill, "same-tick kill duplicated state");
        var second = kill.confirm(15, 2, true);
        check(second.cueAt(21) == WeaponHitState.Cue.KILL, "second actual kill did not refresh");
        check(second.cueAt(22) == WeaponHitState.Cue.NONE, "second kill outlived its duration");
    }

    @Test
    void samplingIsPureAndOwnersHaveIndependentState() {
        var a = WeaponHitState.idle().confirm(10, 1, true);
        var b = WeaponHitState.idle().confirm(11, 1, false);
        for (int i = 0; i < 1000; i++) check(a.cueAt(16) == WeaponHitState.Cue.KILL, "read consumed cue");
        check(a.cueAt(17) == WeaponHitState.Cue.NONE, "read refreshed cue");
        check(a.cueAt(10) == WeaponHitState.Cue.KILL, "query mutated immutable state");
        check(b.cueAt(15) == WeaponHitState.Cue.NONE, "other owner acquired kill lifetime");
        check(a.cueAt(15) == WeaponHitState.Cue.KILL, "other owner changed kill");
    }

    @Test
    void rollbackAndLongOverflowDoNotFabricateAVisibleCue() {
        var kill = WeaponHitState.idle().confirm(100, 1, true);
        check(kill.cueAt(99) == WeaponHitState.Cue.NONE, "clock rollback showed old cue");
        var fresh = kill.confirm(90, 1, false);
        check(fresh.cueAt(90) == WeaponHitState.Cue.HIT, "new actual hit after rollback inherited kill");
        var edge = WeaponHitState.idle().confirm(Long.MAX_VALUE - 2, 1, true);
        check(edge.cueAt(Long.MAX_VALUE) == WeaponHitState.Cue.KILL, "near-limit age overflowed");
        check(edge.cueAt(Long.MIN_VALUE) == WeaponHitState.Cue.NONE, "wrapped clock revived cue");
        check(WeaponHitState.idle().confirm(Long.MIN_VALUE, 1, false).cueAt(Long.MAX_VALUE)
                == WeaponHitState.Cue.NONE, "age overflow revived ancient hit");
    }

    @Test
    void bindingRejectsEveryReplacementEvenWhenTokensAreValueEqual() {
        Object player = new String("player"), connection = new String("connection");
        Object level = new String("level"), server = new String("server");
        var binding = new WeaponHitState.Binding(player, connection, level, server);
        check(binding.matches(player, connection, level, server), "exact binding rejected");
        check(!binding.matches(new String("player"), connection, level, server), "replacement player accepted");
        check(!binding.matches(player, new String("connection"), level, server), "replacement connection accepted");
        check(!binding.matches(player, connection, new String("level"), server), "replacement level accepted");
        check(!binding.matches(player, connection, level, new String("server")), "replacement server accepted");
        check(!binding.matches(player, null, level, server), "null connection accepted");
    }

    public static void main(String[] args) {
        var tests = new WeaponHitStateW223Test();
        tests.invalidDamageCannotCreateOrRefreshEvenAKill();
        tests.exactBoundariesAndOrdinaryRefresh();
        tests.pelletOrderCannotDowngradeOrExtendKill();
        tests.anotherActualKillCanRefreshButSameTickDeduplicates();
        tests.samplingIsPureAndOwnersHaveIndependentState();
        tests.rollbackAndLongOverflowDoNotFabricateAVisibleCue();
        tests.bindingRejectsEveryReplacementEvenWhenTokensAreValueEqual();
        System.out.println("W223 pure policy: 7 tests passed");
    }
}
