package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import static org.junit.jupiter.api.Assertions.*;

/** Production pure ability projection tests; source guard checks are explicitly static.
 * No native/server claim: master's actualGT owns attachments, real items, use/recharge and reload lifetime.
 */
class WeaponSurplusW183Test {
    private static final AbilitySlot[] POWERED={AbilitySlot.GRENADE,AbilitySlot.MELEE,AbilitySlot.CLASS_ABILITY};
    private static Identifier id(String name) { return Identifier.fromNamespaceAndPath("surplus_test",name); }
    private static Ability ability(String name,GuardianClass cls,AbilitySlot slot) {
        return new Ability(id(name),cls,slot,Element.KINETIC,10,name) {
            public boolean activate(ServerPlayer player) { throw new AssertionError("Query must never activate"); }
        };
    }
    private static GuardianData data(Map<AbilitySlot,Identifier> ids) {
        var d=new GuardianData();d.setGuardianClass(GuardianClass.HUNTER);
        d.setLoadout(GuardianClass.HUNTER,new Loadout(ids));return d;
    }
    private static Function<Identifier,Optional<Ability>> lookup(Map<Identifier,Ability> registered) {
        return key->Optional.ofNullable(registered.get(key));
    }
    private static Map<Identifier,Ability> registered() {
        var map=new HashMap<Identifier,Ability>();
        for(var slot:AbilitySlot.values()) {
            var a=ability(slot.name().toLowerCase(Locale.ROOT),GuardianClass.HUNTER,slot);map.put(a.id(),a);
        }
        return map;
    }
    private static Map<AbilitySlot,Identifier> equipped(Map<Identifier,Ability> abilities) {
        var ids=new EnumMap<AbilitySlot,Identifier>(AbilitySlot.class);
        for(var a:abilities.values())ids.put(a.slot(),a.id());return ids;
    }
    private static String source() throws Exception {
        return Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponSurplus.java"));
    }
    @Test void absentDataNoneAndAbsentActiveLoadoutAreNeutralWithoutRegistryReads() {
        Function<Identifier,Optional<Ability>> fail=key->{throw new AssertionError("No lookup");};
        assertEquals(0,WeaponSurplus.chargedAbilities(null,fail));
        var d=new GuardianData();assertEquals(0,WeaponSurplus.chargedAbilities(d,fail));
        d.setGuardianClass(GuardianClass.HUNTER);assertEquals(0,WeaponSurplus.chargedAbilities(d,fail));
        d.setLoadout(GuardianClass.HUNTER,new Loadout(Map.of()));assertEquals(0,WeaponSurplus.chargedAbilities(d,fail));
    }
    @Test void allEightActualPoweredCooldownCombinationsCountOncePerSlotOnly() {
        var registry=registered();var d=data(equipped(registry));
        for(int mask=0;mask<8;mask++) {
            for(int i=0;i<3;i++)d.setCooldown(POWERED[i],(mask&(1<<i))==0?40:0);
            d.setCooldown(AbilitySlot.SUPER,0);d.setCooldown(AbilitySlot.JUMP,0);d.setSuperEnergy(1);
            assertEquals(Integer.bitCount(mask),WeaponSurplus.chargedAbilities(d,lookup(registry)));
        }
    }
    @Test void everyMissingUnregisteredAndWrongIdentityAbilityIsExcluded() {
        var registry=registered();var ids=equipped(registry);var d=data(ids);
        assertEquals(3,WeaponSurplus.chargedAbilities(d,lookup(registry)));
        for(var slot:POWERED) {
            var absent=new EnumMap<AbilitySlot,Identifier>(ids);absent.remove(slot);
            assertEquals(2,WeaponSurplus.chargedAbilities(data(absent),lookup(registry)));
            var unregistered=new HashMap<>(registry);unregistered.remove(ids.get(slot));
            assertEquals(2,WeaponSurplus.chargedAbilities(d,lookup(unregistered)));
            var wrongId=new HashMap<>(registry);wrongId.put(ids.get(slot),ability("foreign",GuardianClass.HUNTER,slot));
            assertEquals(2,WeaponSurplus.chargedAbilities(d,lookup(wrongId)));
        }
    }
    @Test void allForeignClassesAndForeignSlotsFailEvenWhenIdIsRegisteredAndEquipped() {
        var registry=registered();var ids=equipped(registry);var d=data(ids);
        for(var slot:POWERED) {
            String name=slot.name().toLowerCase(Locale.ROOT);
            for(var cls:GuardianClass.values()) if(cls!=GuardianClass.HUNTER) {
                var wrong=new HashMap<>(registry);wrong.put(ids.get(slot),ability(name,cls,slot));
                assertEquals(2,WeaponSurplus.chargedAbilities(d,lookup(wrong)),cls+" "+slot);
            }
            for(var other:AbilitySlot.values()) if(other!=slot) {
                var wrong=new HashMap<>(registry);wrong.put(ids.get(slot),ability(name,GuardianClass.HUNTER,other));
                assertEquals(2,WeaponSurplus.chargedAbilities(d,lookup(wrong)),other+" "+slot);
            }
        }
    }
    @Test void liveCooldownExpiryAbilityUseAndClassOrLoadoutChangesReadImmediately() {
        var registry=registered();var ids=equipped(registry);var d=data(ids);
        assertEquals(3,WeaponSurplus.chargedAbilities(d,lookup(registry)));
        d.setCooldown(AbilitySlot.GRENADE,1);assertEquals(2,WeaponSurplus.chargedAbilities(d,lookup(registry)));
        d.tickCooldowns();assertEquals(3,WeaponSurplus.chargedAbilities(d,lookup(registry)));
        d.setCooldown(AbilitySlot.MELEE,400);assertEquals(2,WeaponSurplus.chargedAbilities(d,lookup(registry)));
        d.setLoadout(GuardianClass.HUNTER,new Loadout(Map.of()));assertEquals(0,WeaponSurplus.chargedAbilities(d,lookup(registry)));
        d.setLoadout(GuardianClass.HUNTER,new Loadout(ids));d.setGuardianClass(GuardianClass.WARLOCK);
        assertEquals(0,WeaponSurplus.chargedAbilities(d,lookup(registry)));
        d.setLoadout(GuardianClass.WARLOCK,new Loadout(ids));assertEquals(0,WeaponSurplus.chargedAbilities(d,lookup(registry)));
        d.setGuardianClass(GuardianClass.NONE);assertEquals(0,WeaponSurplus.chargedAbilities(d,lookup(registry)));
    }
    @Test void repeatedAbilityQueriesDoNotTickCooldownActivateOrChangeAnyGuardianData() {
        var registry=registered();var d=data(equipped(registry));d.setCooldown(AbilitySlot.MELEE,7);d.setSuperEnergy(.5f);
        var before=d.cooldownsView();var loadout=d.loadout();var reads=new AtomicInteger();
        for(int i=0;i<100;i++)assertEquals(2,WeaponSurplus.chargedAbilities(d,key->{reads.incrementAndGet();return lookup(registry).apply(key);}));
        assertEquals(200,reads.get());assertEquals(before,d.cooldownsView());assertEquals(loadout,d.loadout());
        assertEquals(.5f,d.superEnergy());assertEquals(GuardianClass.HUNTER,d.guardianClass());
    }
    @Test void staticRealSourceGuardsUseAttachedDataExactRollAndObjectIdentity() throws Exception {
        String text=source();
        for(String required:List.of("p != null", "p.isAlive()", "!p.isRemoved()", "!p.isSpectator()", "!p.hasDisconnected()",
            "Guardians.runtimeIfPresent(p)", "r.superSession == null", "p.getAttachedOrElse(Guardians.DATA, null)",
            "AbilityRegistry::get", "ability.slot() == slot", "ability.guardianClass() == data.guardianClass()",
            "id.equals(ability.id())", "data.cooldown(slot) > 0", "GuardianClass.NONE", "WeaponItems.entry(stack)",
            "WeaponPerks.selected(stack, SurplusProfile.ID)", "SurplusProfile.rolls().contains(roll)",
            "entry.id().equals(roll.id())", "WeaponLoadout.equipped(p)", "e.stack() == stack", "getItem(i) == stack",
            "p.getMainHandItem() != stack", "p.getInventory().getItem(slot) != stack", "WeaponLoadout.canUse(p)"))
            assertTrue(text.contains(required),required);
        for(String forbidden:List.of("Guardians.data(","Guardians.runtime(","getAttachedOrCreate", "setAttached(",
            "setCooldown(","tickCooldowns(",".activate(","WeaponPerks.select(","WeaponRuntime.","SESSIONS", "getTickCount(",
            "isSprinting(","getDeltaMovement(","putLong(","stack.copy(", "static final Map"))
            assertFalse(text.contains(forbidden),forbidden);
    }
    @Test void staticIncomingHandlingHasNoSelectedMainHandOrCanUseRequirement() throws Exception {
        String text=source();String body=text.split("public static int handlingTicks")[1].split("public static int adsTicks")[0];
        assertTrue(body.contains("source(p, stack, false)"));assertFalse(body.contains("canUse("));
        assertFalse(body.contains("getMainHandItem()"));assertFalse(body.contains("getSelectedSlot()"));
        assertTrue(body.contains("chargedAbilities(p)"));
        assertTrue(text.contains("source(p, p.getMainHandItem(), true)"));
    }
    @Test void staticTimingOnlyProvenCompanionsAndNoAlreadyRoundedBaseMultiplication() throws Exception {
        String text=source();
        for(String required:List.of("SurplusProfile.compatible(entry, id, r)","FrenzyProfile.ID", "AdrenalineJunkieProfile.ID",
            "ThreatDetectorProfile.ID","RapidHitProfile.ID","SnapshotAimProfile.ID", "entering && co(",
            "WeaponFrenzy.ownedRemaining(p, stack)","WeaponAdrenalineJunkie.ownedRemaining(p, stack)",
            "RapidHitProfile.durationMultiplier(rapid)","SurplusProfile.reloadPlan(entry, bonus, scalar, base)"))
            assertTrue(text.contains(required),required);
        for(String forbidden:List.of("OutlawProfile", "FeedingFrenzyProfile", "PerpetualMotionProfile", "StatsForAllProfile",
            "base.firstTicks() *", "base.intervalTicks() *", "base *", "damageMultiplier(", "durationTicks("))
            assertFalse(text.contains(forbidden),forbidden);
    }
}
