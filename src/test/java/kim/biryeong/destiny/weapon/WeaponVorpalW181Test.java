package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure source snapshots plus explicit static mapping/authority checks. Actual entities and paid
 * runtime damage are master's native actualGT coverage, not simulated as a Minecraft success here.
 */
class WeaponVorpalW181Test {
    private static String source() throws Exception {
        return Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponVorpal.java"));
    }

    @Test void noneAndNullTargetStayNeutral() {
        assertEquals(1f, WeaponVorpal.Token.NONE.multiplierForTarget(true));
        assertEquals(1f, WeaponVorpal.Token.NONE.multiplierForTarget(false));
        assertEquals(1f, WeaponVorpal.Token.NONE.multiplier(null));
        assertEquals(1f, WeaponVorpal.multiplier(null, null));
        assertSame(WeaponVorpal.Token.NONE, WeaponVorpal.capture(null));
    }

    @Test void everySourceSnapshotFreezesExactScalarAndConditionalTargetBonus() {
        for (var roll : VorpalProfile.rolls()) {
            var entry = VorpalW181Test.entry(roll.id());
            var token = WeaponVorpal.snapshotSource(entry, roll);
            assertNotSame(WeaponVorpal.Token.NONE, token);
            assertEquals(VorpalProfile.multiplier(entry), token.multiplierForTarget(true));
            assertEquals(1f, token.multiplierForTarget(false));
            assertEquals(1f, token.multiplier(null));
            // Rechecking a different target never consumes, stacks or refreshes source credit.
            assertEquals(VorpalProfile.multiplier(entry), token.multiplierForTarget(true));
        }
    }

    @Test void wrongSourceSelectionEnhancedSocketPoolAndDefaultCannotMintToken() {
        var e = VorpalW181Test.entry("canis_major");
        var r = VorpalProfile.rolls().stream().filter(x -> x.id().equals(e.id())).findFirst().orElseThrow();
        for (var bad : Arrays.asList(null,
                new WeaponPerks.Roll(null, r.hash(), r.socket(), r.perkHash(), r.plugSetHash()),
                new WeaponPerks.Roll(r.id(), r.hash(), r.socket(), 3418165135L, r.plugSetHash()),
                new WeaponPerks.Roll(r.id(), r.hash(), r.socket()-1, r.perkHash(), r.plugSetHash()),
                new WeaponPerks.Roll(r.id(), r.hash()+1, r.socket(), r.perkHash(), r.plugSetHash()),
                new WeaponPerks.Roll(r.id(), r.hash(), r.socket(), r.perkHash(), r.plugSetHash()+1),
                VorpalProfile.rolls().getFirst()))
            assertSame(WeaponVorpal.Token.NONE, WeaponVorpal.snapshotSource(e, bad));
        assertSame(WeaponVorpal.Token.NONE, WeaponVorpal.snapshotSource(null, r));
        assertSame(WeaponVorpal.Token.NONE, WeaponVorpal.snapshotSource(VorpalW181Test.entry("ace_of_spades"), r));
    }

    @Test void paidSnapshotsSurviveLaterSourceChoiceAndAmmoChangesWithoutFreshCredit() {
        var before = VorpalProfile.rolls().getFirst();
        var paid = WeaponVorpal.snapshotSource(VorpalW181Test.entry(before.id()), before);
        // A subsequent paid source is separate. A cleared/edited selection yields NONE for NEW work.
        var heavy = VorpalProfile.rolls().stream().filter(r -> r.id().equals("canis_major")).findFirst().orElseThrow();
        var next = WeaponVorpal.snapshotSource(VorpalW181Test.entry(heavy.id()), heavy);
        assertEquals(1.20f, paid.multiplierForTarget(true));
        assertEquals(1.10f, next.multiplierForTarget(true));
        assertSame(WeaponVorpal.Token.NONE, WeaponVorpal.snapshotSource(VorpalW181Test.entry(before.id()), null));
        assertEquals(1.20f, paid.multiplierForTarget(true));
        assertEquals(1f, paid.multiplierForTarget(false));
    }

    @Test void tokenStoresOnlyFinalImmutableSourceValuesNoMutableLifecycleReferences() throws Exception {
        assertTrue(Modifier.isFinal(WeaponVorpal.Token.class.getModifiers()));
        for (var ctor : WeaponVorpal.Token.class.getDeclaredConstructors()) assertTrue(Modifier.isPrivate(ctor.getModifiers()));
        var field = WeaponVorpal.Token.class.getDeclaredField("source");
        assertTrue(Modifier.isFinal(field.getModifiers()));
        assertTrue(Modifier.isPrivate(field.getModifiers()));
        assertTrue(field.getType().isRecord());
        assertEquals(Set.of(WeaponCatalog.Entry.class, WeaponPerks.Roll.class, float.class),
            Arrays.stream(field.getType().getRecordComponents()).map(c -> c.getType()).collect(java.util.stream.Collectors.toSet()));
        String multiplier = source().split("public float multiplier\\(LivingEntity target\\)")[1].split("// Pure scalar")[0];
        assertTrue(multiplier.contains("eligibleTarget(target)"));
        assertFalse(multiplier.contains("capture("));
        assertFalse(multiplier.contains("selected("));
        assertFalse(multiplier.contains("getMainHandItem"));
    }

    @Test void staticTargetMappingExplicitlyChecksMobBossTagsAndNativeBosses() throws Exception {
        String target = source().split("static boolean eligibleTarget")[1].split("public static Token capture")[0];
        for (String required : List.of("target == null", "target instanceof Player", "target instanceof ArmorStand",
                "!target.isAlive()", "target.isRemoved()", "target.isSpectator()", "target instanceof WitherBoss",
                "target instanceof EnderDragon", "target instanceof Mob &&", "contains(\"destiny_boss\")", "contains(\"destiny_vehicle\")"))
            assertTrue(target.contains(required), required);
        for (String forbidden : List.of("getHealth(", "getMaxHealth(", "getName(", "getDisplayName(", "inSuper(", "Combat.isEnemy"))
            assertFalse(target.contains(forbidden), forbidden);
    }

    @Test void staticCaptureChecksAuthorityAndUsesSharedSelectedReadOnlyBoundary() throws Exception {
        String capture = source().split("public static Token capture")[1].split("static Token snapshotSource")[0];
        for (String required : List.of("player == null", "!player.isAlive()", "player.isRemoved()", "player.isSpectator()",
                "player.hasDisconnected()", "AbilityService.inSuper(player)", "WeaponLoadout.canUse(player)",
                "getMainHandItem()", "getItem(i) == stack", "WeaponLoadout.equipped(player)", "e.stack() == stack",
                "WeaponItems.entry(stack)", "WeaponPerks.selected(stack, VorpalProfile.ID)", "selection.isEmpty()", "snapshotSource(entry.get(), selection.get())"))
            assertTrue(capture.contains(required), required);
        for (String forbidden : List.of("WeaponPerks.select(", "setAttached(", "putLong(", "setHealth(", "SESSIONS", "getTickCount("))
            assertFalse(source().contains(forbidden), forbidden);
    }
}
