package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Scoped event/snapshot/lifecycle regressions, not per-frame numerical perk mirrors. */
class HeadseekerW202Test {
    private static final int WINDOW = HeadseekerProfile.DURATION_TICKS;

    @Test void onlyConfirmedPositiveDirectNonprecisionActivatesAtTheActualEventTime() {
        var c = new HeadseekerCycle();
        var paid = c.capture(100);
        assertEquals(0, c.remaining(100), "payment or a miss cannot arm the perk");
        for (float actual : new float[]{0, -1, Float.NaN, Float.POSITIVE_INFINITY})
            assertFalse(c.confirmed(100, paid, false, actual));
        assertFalse(c.confirmed(100, paid, true, 5));
        assertFalse(c.confirmed(101, paid, false, 5), "cannot replay a stale hitscan emission");
        assertFalse(c.confirmed(100, null, false, 5));
        assertEquals(0, c.remaining(100));
        assertTrue(c.confirmed(100, paid, false, 5), "invalid callbacks do not consume real credit");
        assertEquals(WINDOW, c.remaining(100));
        assertFalse(c.confirmed(100, paid, false, 5), "duplicate callback cannot count again");
    }

    @Test void refreshUsesTheNewBodyHitAndPrecisionNeverRefreshes() {
        var c = new HeadseekerCycle();
        assertTrue(c.confirmed(50, c.capture(50), false, 1));
        var precision = c.capture(53);
        assertTrue(c.boosted(53, precision));
        assertFalse(c.confirmed(53, precision, true, 2));
        assertEquals(WINDOW - 3, c.remaining(53));
        assertTrue(c.confirmed(55, c.capture(55), false, 1));
        assertEquals(WINDOW, c.remaining(55));
        assertTrue(c.remaining(50 + WINDOW) > 0, "refreshed window passes the original deadline");
        assertEquals(0, c.remaining(55 + WINDOW));
    }

    @Test void sameEmissionCannotRetroactivelyBoostItsPrecisionButNextPaidEmissionCan() {
        var c = new HeadseekerCycle();
        var mixed = c.capture(20);
        assertFalse(c.boosted(20, mixed));
        assertTrue(c.confirmed(20, mixed, false, 1));
        assertFalse(c.boosted(20, mixed), "body-to-precision within one trace uses the pre-trace snapshot");
        var next = c.capture(20);
        assertTrue(c.boosted(20, next), "a separate paid emission may snapshot the earned window");
        assertFalse(c.boosted(21, next), "these direct hitscan tokens cannot be reused in a later tick");
    }

    @Test void deadlineIsExclusiveAndRepeatedPureQueriesCannotExtendOrBindTheWindow() {
        var c = new HeadseekerCycle();
        for (int i = 0; i < 100; i++) assertEquals(0, c.remaining(100));
        assertTrue(c.confirmed(100, c.capture(100), false, 1));
        for (int i = 0; i < 100; i++) assertEquals(1, c.remaining(100 + WINDOW - 1));
        assertTrue(c.boosted(100 + WINDOW - 1, c.capture(100 + WINDOW - 1)));
        assertFalse(c.boosted(100 + WINDOW, c.capture(100 + WINDOW)));
        assertEquals(0, c.remaining(100 + WINDOW));
        assertTrue(c.confirmed(100 + WINDOW, c.capture(100 + WINDOW), false, 1));
        assertEquals(WINDOW, c.remaining(100 + WINDOW), "a new real body hit starts a fresh expired window");
    }

    @Test void timeRollbackOverflowAndSourceClearCannotReviveAnOldEmission() {
        var c = new HeadseekerCycle();
        assertTrue(c.confirmed(40, c.capture(40), false, 1));
        var active = c.capture(41);
        assertEquals(0, c.remaining(39));
        c.update(39);
        assertFalse(c.boosted(41, active));
        assertEquals(0, c.remaining(41));
        var fresh = c.capture(42);
        assertTrue(c.confirmed(42, fresh, false, 1));
        var beforeClear = c.capture(42);
        c.clear();
        assertFalse(c.boosted(42, beforeClear));
        assertFalse(c.confirmed(42, beforeClear, false, 1));
        assertEquals(0, c.remaining(42));
        assertNull(c.capture(-1));
        var overflow = c.capture(Long.MAX_VALUE);
        assertFalse(c.confirmed(Long.MAX_VALUE, overflow, false, 1));
        assertEquals(0, c.remaining(Long.MAX_VALUE));
        assertFalse(new HeadseekerCycle().confirmed(42, fresh, false, 1), "another cycle cannot adopt a token");
    }

    @Test void formulaIncreasesOnlyPrecisionBonusForTheKnownSourceMultiplier() {
        // body 100 -> total precision 150. Bonus is 50, so the extra is 10, not 30.
        assertEquals(160f, HeadseekerCycle.precisionDamage(150, 1.5, true), .0001f);
        assertEquals(220f, HeadseekerCycle.precisionDamage(200, 2, true), .0001f);
        assertEquals(150f, HeadseekerCycle.precisionDamage(150, 1.5, false));
        assertEquals(100f, HeadseekerCycle.precisionDamage(100, 1, true));
        for (double invalid : new double[]{0, .5, Double.NaN, Double.POSITIVE_INFINITY})
            assertEquals(150f, HeadseekerCycle.precisionDamage(150, invalid, true));
        assertEquals(0f, HeadseekerCycle.precisionDamage(0, 2, true));
        assertEquals(Float.MAX_VALUE, HeadseekerCycle.precisionDamage(Float.MAX_VALUE, 2, true));
    }

    @Test void everyIdentityBoundaryRejectsAdoptionAndRevocationIsPermanent() {
        Object owner = new Object(), level = new Object(), stack = new Object(), data = new Object();
        Object runtime = new Object(), guardianClass = new Object();
        var id = new WeaponHeadseeker.Identity(owner, level, stack, data, runtime, guardianClass, true, 2);
        var lease = new WeaponHeadseeker.Lease(id, 10);
        assertTrue(lease.valid(id, 10));
        var changes = List.of(
            new WeaponHeadseeker.Identity(new Object(), level, stack, data, runtime, guardianClass, true, 2),
            new WeaponHeadseeker.Identity(owner, new Object(), stack, data, runtime, guardianClass, true, 2),
            new WeaponHeadseeker.Identity(owner, level, new Object(), data, runtime, guardianClass, true, 2),
            new WeaponHeadseeker.Identity(owner, level, stack, new Object(), runtime, guardianClass, true, 2),
            new WeaponHeadseeker.Identity(owner, level, stack, data, new Object(), guardianClass, true, 2),
            new WeaponHeadseeker.Identity(owner, level, stack, data, runtime, new Object(), true, 2),
            new WeaponHeadseeker.Identity(owner, level, stack, data, runtime, guardianClass, false, 2),
            new WeaponHeadseeker.Identity(owner, level, stack, data, runtime, guardianClass, true, 3));
        for (var changed : changes) assertFalse(lease.valid(changed, 10));
        assertFalse(lease.valid(id, 9));
        lease.observe(12);
        assertFalse(lease.valid(id, 11));
        lease.revoke();
        lease.observe(12);
        assertFalse(lease.valid(id, 12), "same-tick return/edit/reselect cannot heal a revoked lease");
    }

    @Test void acceptedStowFenceBlocksOutgoingSourceEvenBeforeAnySessionAndUntilNextTick() {
        Object owner = new Object(), a = new Object(), b = new Object();
        var fences = new IdentityHashMap<Object, WeaponHeadseeker.StowFence>();
        fences.put(a, new WeaponHeadseeker.StowFence(owner, a, 20));
        fences.put(b, new WeaponHeadseeker.StowFence(owner, b, 20));
        assertTrue(fences.get(a).blocks(owner, a, 20), "away/back cannot replace the earlier outgoing fence");
        assertTrue(fences.get(b).blocks(owner, b, 20));
        assertFalse(fences.get(a).blocks(new Object(), a, 20));
        assertFalse(fences.get(a).blocks(owner, new Object(), 20));
        assertFalse(fences.get(a).blocks(owner, a, 21));
    }

    @Test void sourceProfileInitializesFromCanonicalJsonAndRejectsForgedSameIdEntry() throws Exception {
        var stream = getClass().getResourceAsStream("/destiny/weapons/w30.json");
        assertNotNull(stream);
        try (stream) {
            var raw = JsonParser.parseString(new String(stream.readAllBytes(), StandardCharsets.UTF_8));
            var gson = new Gson();
            for (var row : raw.getAsJsonArray()) {
                var entry = gson.fromJson(row, WeaponCatalog.Entry.class);
                if (!HeadseekerProfile.supports(entry.id())) continue;
                assertTrue(HeadseekerProfile.supports(entry));
                var forged = new WeaponCatalog.Entry(entry.id(), entry.family(), "forged", entry.name(),
                        entry.source_frame_label(), entry.item_model());
                assertFalse(HeadseekerProfile.supports(forged));
            }
        }
        assertFalse(HeadseekerProfile.supports((WeaponCatalog.Entry)null));
        assertThrows(UnsupportedOperationException.class, () -> HeadseekerProfile.rolls().clear());
    }
}
