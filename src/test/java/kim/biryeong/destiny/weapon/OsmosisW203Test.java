package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.junit.jupiter.api.Test;
import static kim.biryeong.destiny.weapon.WeaponCharacteristics.Damage.*;
import static org.junit.jupiter.api.Assertions.*;

/** New behavior only: tick-free success/refill episodes, revocation and strict pinned resources.
 * Does not select through the coordinator-owned, not-yet-integrated trait registry or run MC. */
class OsmosisW203Test {
    private static WeaponProfile profile(int capacity, boolean primary) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN, 1, 1, capacity, primary ? 0 : 20,
                20, 20, 0, 1, 1, 0, 0, 0, 0, false, primary);
    }
    private static String resource() throws Exception {
        try (var input = OsmosisW203Test.class.getResourceAsStream("/destiny/weapons/w203-osmosis.json")) {
            assertNotNull(input);
            return new String(input.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
    @Test void acceptanceAndRepeatedPureReadsCannotActivateOrMoveAmmo() {
        var cycle = new OsmosisCycle();
        var ammo = new WeaponMagazine(profile(5, false), 0, 10);
        var accepted = cycle.accepted(ARC);
        assertNotNull(accepted);
        for (int i = 0; i < 100; i++) {
            assertFalse(cycle.active());
            assertEquals(KINETIC, cycle.damage(KINETIC));
            assertEquals(SOLAR, cycle.damage(SOLAR), "inactive result is the caller's canonical element");
            assertEquals(0, ammo.rounds());
        }
        assertEquals(3, cycle.abilityUsed(accepted, ammo, 5));
        assertEquals(3, ammo.rounds()); assertEquals(7, ammo.reserve());
        assertTrue(cycle.active()); assertEquals(ARC, cycle.damage(KINETIC));
        for (int i = 0; i < 100; i++) assertEquals(ARC, cycle.damage(KINETIC));
        assertEquals(0, cycle.abilityUsed(accepted, ammo, 5), "successful use token is one-shot");
        assertEquals(3, ammo.rounds());
    }
    @Test void laterAcceptedGrenadeChangesElementWithoutASecondRefillAndReplayCannotRevertIt() {
        var cycle = new OsmosisCycle();
        var ammo = new WeaponMagazine(profile(10, false), 0, 20);
        var first = cycle.accepted(ARC);
        assertEquals(5, cycle.abilityUsed(first, ammo, 10));
        assertTrue(ammo.consume(4));
        var second = cycle.accepted(VOID);
        assertEquals(ARC, cycle.damage(KINETIC), "acceptance alone does not change an active episode");
        assertEquals(0, cycle.abilityUsed(second, ammo, 10));
        assertEquals(VOID, cycle.damage(KINETIC));
        assertEquals(1, ammo.rounds()); assertEquals(15, ammo.reserve());
        assertEquals(0, cycle.abilityUsed(first, ammo, 10));
        assertEquals(VOID, cycle.damage(KINETIC));
    }
    @Test void fullMagazineUseStillConvertsAndSpendsTheOnlyRefillOpportunity() {
        var cycle = new OsmosisCycle();
        var ammo = new WeaponMagazine(profile(5, false), 5, 10);
        assertEquals(0, cycle.abilityUsed(cycle.accepted(SOLAR), ammo, 5));
        assertTrue(cycle.active()); assertEquals(SOLAR, cycle.damage(KINETIC));
        assertEquals(10, ammo.reserve());
        assertTrue(ammo.consume(5));
        assertEquals(0, cycle.abilityUsed(cycle.accepted(VOID), ammo, 5));
        assertEquals(0, ammo.rounds()); assertEquals(10, ammo.reserve());
        assertEquals(VOID, cycle.damage(KINETIC));
    }
    @Test void zeroReserveUseCannotBankARefillForALaterPickup() {
        var cycle = new OsmosisCycle();
        var ammo = new WeaponMagazine(profile(5, false), 0, 0);
        assertEquals(0, cycle.abilityUsed(cycle.accepted(ARC), ammo, 5));
        assertEquals(ARC, cycle.damage(KINETIC));
        assertEquals(5, ammo.addReserve(5));
        assertEquals(0, cycle.abilityUsed(cycle.accepted(SOLAR), ammo, 5));
        assertEquals(0, ammo.rounds()); assertEquals(5, ammo.reserve());
        cycle.clear();
        assertEquals(3, cycle.abilityUsed(cycle.accepted(SOLAR), ammo, 5));
        assertEquals(2, ammo.reserve());
    }
    @Test void partialFiniteReserveTransferConservesAmmoAndNeverOverfills() {
        var cycle = new OsmosisCycle();
        var ammo = new WeaponMagazine(profile(5, false), 1, 2);
        long total = ammo.total();
        assertEquals(2, cycle.abilityUsed(cycle.accepted(VOID), ammo, 5));
        assertEquals(total, ammo.total()); assertEquals(3, ammo.rounds()); assertEquals(0, ammo.reserve());
        cycle.clear();
        assertEquals(0, cycle.abilityUsed(cycle.accepted(ARC), ammo, 5));
        assertEquals(total, ammo.total());
        var nearFull = new WeaponMagazine(profile(5, false), 4, 10);
        cycle.clear();
        assertEquals(1, cycle.abilityUsed(cycle.accepted(SOLAR), nearFull, 5));
        assertEquals(5, nearFull.rounds()); assertEquals(9, nearFull.reserve());
    }
    @Test void primaryInfiniteReserveStillHasABoundedMagazineAndUsesCeilingCartridges() {
        var cycle = new OsmosisCycle();
        var ammo = new WeaponMagazine(profile(5, true), 0, 0);
        assertEquals(3, cycle.abilityUsed(cycle.accepted(ARC), ammo, 5));
        assertEquals(3, ammo.rounds()); assertEquals(0, ammo.reserve());
        cycle.clear();
        assertEquals(2, cycle.abilityUsed(cycle.accepted(VOID), ammo, 5));
        assertEquals(5, ammo.rounds());
        assertEquals(0, OsmosisProfile.refillRounds(0));
        assertEquals(1, OsmosisProfile.refillRounds(1));
        assertEquals(2, OsmosisProfile.refillRounds(4));
        assertEquals(1073741824, OsmosisProfile.refillRounds(Integer.MAX_VALUE));
    }
    @Test void stowEditAndReplacementClearRevokePendingTokensAndResetTheEpisode() {
        var cycle = new OsmosisCycle();
        var ammo = new WeaponMagazine(profile(10, false), 0, 20);
        assertEquals(5, cycle.abilityUsed(cycle.accepted(SOLAR), ammo, 10));
        var pending = cycle.accepted(VOID);
        cycle.clear();
        assertFalse(cycle.active()); assertEquals(KINETIC, cycle.damage(KINETIC));
        assertEquals(0, cycle.abilityUsed(pending, ammo, 10));
        assertFalse(cycle.active());
        assertEquals(5, cycle.abilityUsed(cycle.accepted(ARC), ammo, 10));
        assertEquals(10, ammo.rounds()); assertEquals(10, ammo.reserve());
    }
    @Test void foreignOrInvalidTokensCannotActivateAnotherSource() {
        var source = new OsmosisCycle(); var replacement = new OsmosisCycle();
        var ammo = new WeaponMagazine(profile(5, false), 0, 10);
        var token = source.accepted(VOID);
        assertEquals(0, replacement.abilityUsed(token, ammo, 5));
        assertFalse(replacement.active()); assertEquals(0, ammo.rounds());
        assertNull(source.accepted(null)); assertNull(source.accepted(KINETIC));
        assertEquals(0, source.abilityUsed(null, ammo, 5));
        source.clear();
        assertEquals(0, source.abilityUsed(token, ammo, 5));
        assertFalse(source.active());
    }
    @Test void everyOriginalIdentityIsRequiredAndRevocationCannotHealOnReturn() {
        Object owner = new Object(), world = new Object(), stack = new Object(), data = new Object();
        Object runtime = new Object(), guardianClass = new Object();
        var original = new WeaponOsmosis.Identity(owner, world, stack, data, runtime, guardianClass, true, 0);
        var lease = new WeaponOsmosis.Lease(original, 10);
        var changes = List.of(
            new WeaponOsmosis.Identity(new Object(), world, stack, data, runtime, guardianClass, true, 0),
            new WeaponOsmosis.Identity(owner, new Object(), stack, data, runtime, guardianClass, true, 0),
            new WeaponOsmosis.Identity(owner, world, new Object(), data, runtime, guardianClass, true, 0),
            new WeaponOsmosis.Identity(owner, world, stack, new Object(), runtime, guardianClass, true, 0),
            new WeaponOsmosis.Identity(owner, world, stack, data, new Object(), guardianClass, true, 0),
            new WeaponOsmosis.Identity(owner, world, stack, data, runtime, new Object(), true, 0),
            new WeaponOsmosis.Identity(owner, world, stack, data, runtime, guardianClass, false, 0),
            new WeaponOsmosis.Identity(owner, world, stack, data, runtime, guardianClass, true, 1));
        assertTrue(lease.valid(original, 10));
        for (var changed : changes) assertFalse(lease.valid(changed, 10));
        assertFalse(lease.valid(original, 9));
        lease.observe(12); assertFalse(lease.valid(original, 11));
        lease.revoke(); lease.observe(12); assertFalse(lease.valid(original, 12));
        var fence = new WeaponOsmosis.StowFence(owner, stack, 12);
        assertTrue(fence.blocks(owner, stack, 12));
        assertFalse(fence.blocks(new Object(), stack, 12), "same UUID replacement object cannot inherit old fence");
        assertFalse(fence.blocks(owner, new Object(), 12));
        assertFalse(fence.blocks(owner, stack, 13));
    }
    @Test void exactResourceLoadsWithoutSelectingTheUnintegratedTraitRegistry() throws Exception {
        OsmosisProfile.validateResource(resource());
        assertEquals(Set.of("patron_of_lost_causes", "seventh_seraph_officer_revolver", "steelfeather_repeater"),
                OsmosisProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet()));
        assertEquals(3, OsmosisProfile.rolls().size());
        assertTrue(OsmosisProfile.rolls().stream().allMatch(r -> r.perkHash() == 1774574192L && r.socket() == 4));
        try (var input = getClass().getResourceAsStream("/destiny/weapons/w30.json")) {
            assertNotNull(input);
            for (var raw : JsonParser.parseString(new String(input.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonArray()) {
                var entry = new Gson().fromJson(raw, WeaponCatalog.Entry.class);
                if (!OsmosisProfile.supports(entry.id())) continue;
                assertTrue(OsmosisProfile.supports(entry));
                assertFalse(OsmosisProfile.supports(new WeaponCatalog.Entry(entry.id(), entry.family(), "forged",
                        entry.name(), entry.source_frame_label(), entry.item_model())));
            }
        }
        assertFalse(OsmosisProfile.supports((WeaponCatalog.Entry)null));
        assertFalse(OsmosisProfile.supports("not_a_source"));
        assertThrows(UnsupportedOperationException.class, () -> OsmosisProfile.rolls().clear());
    }
    @Test void resourceRejectsUnknownMechanicsEnhancedHashesForgedPoolsAndIncompleteSources() throws Exception {
        var root = JsonParser.parseString(resource()).getAsJsonObject();
        for (String field : List.of("hash", "socket", "perkHash", "plugSetHash")) {
            var bad = root.deepCopy(); bad.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, 1);
            assertThrows(IllegalStateException.class, () -> OsmosisProfile.validateResource(bad.toString()), field);
        }
        var badMechanics = root.deepCopy(); badMechanics.getAsJsonObject("perk").addProperty("trigger", "grenade_release");
        assertThrows(IllegalStateException.class, () -> OsmosisProfile.validateResource(badMechanics.toString()));
        var missing = root.deepCopy(); missing.getAsJsonArray("weapons").remove(0);
        assertThrows(IllegalStateException.class, () -> OsmosisProfile.validateResource(missing.toString()));
        var duplicate = root.deepCopy(); duplicate.getAsJsonArray("weapons").add(duplicate.getAsJsonArray("weapons").get(0).deepCopy());
        assertThrows(IllegalStateException.class, () -> OsmosisProfile.validateResource(duplicate.toString()));
        var extra = root.deepCopy(); extra.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("enhanced", true);
        assertThrows(IllegalStateException.class, () -> OsmosisProfile.validateResource(extra.toString()));
    }
}
