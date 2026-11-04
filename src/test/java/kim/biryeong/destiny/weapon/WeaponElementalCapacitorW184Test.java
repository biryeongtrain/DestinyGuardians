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

/** Pure production selector and static authority guards. Real attachment, item identity,
 * paid-hit companion hooks and accepted runtime reload are master actualGT responsibilities.
 */
class WeaponElementalCapacitorW184Test {
    private static Identifier id(String name) { return Identifier.fromNamespaceAndPath("ec_test",name); }
    private static Ability ability(String name, GuardianClass cls, AbilitySlot slot, Element element) {
        return new Ability(id(name),cls,slot,element,10,name) {
            public boolean activate(ServerPlayer p) { throw new AssertionError("Read must never activate"); }
        };
    }
    private static GuardianData data(Identifier superId) {
        var d=new GuardianData();d.setGuardianClass(GuardianClass.HUNTER);
        d.setLoadout(GuardianClass.HUNTER,new Loadout(superId==null?Map.of():Map.of(AbilitySlot.SUPER,superId)));return d;
    }
    private static Function<Identifier,Optional<Ability>> registry(Ability a) {
        return key->key.equals(a.id())?Optional.of(a):Optional.empty();
    }
    private static String source() throws Exception {
        return Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponElementalCapacitor.java"));
    }
    @Test void missingNoneNullClassLoadoutAndSuperAreNeutralWithoutLookup() {
        Function<Identifier,Optional<Ability>> fail=key->{throw new AssertionError("Must not lookup");};
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(null,fail));
        var d=new GuardianData();assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,fail));
        d.setGuardianClass(null);assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,fail));
        d.setGuardianClass(GuardianClass.HUNTER);assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,fail));
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(data(null),fail));
    }
    @Test void exactEquippedSuperElementOnlyDespiteSolarOtherAbilitiesAndEnergyCooldownChanges() {
        for(var element:Element.values()) {
            var superAbility=ability("super",GuardianClass.HUNTER,AbilitySlot.SUPER,element);
            var d=data(superAbility.id());
            var ids=new EnumMap<AbilitySlot,Identifier>(AbilitySlot.class);ids.put(AbilitySlot.SUPER,superAbility.id());
            var map=new HashMap<Identifier,Ability>();map.put(superAbility.id(),superAbility);
            for(var slot:AbilitySlot.values()) if(slot!=AbilitySlot.SUPER) {
                var a=ability(slot.name().toLowerCase(Locale.ROOT),GuardianClass.HUNTER,slot,Element.SOLAR);
                ids.put(slot,a.id());map.put(a.id(),a);
            }
            d.setLoadout(GuardianClass.HUNTER,new Loadout(ids));
            var reads=new AtomicInteger();Function<Identifier,Optional<Ability>> registry=key->{reads.incrementAndGet();assertEquals(superAbility.id(),key);return Optional.ofNullable(map.get(key));};
            for(float energy:new float[]{0,.5f,1})for(int cooldown:new int[]{0,1,400}) {
                d.setSuperEnergy(energy);for(var slot:AbilitySlot.values())d.setCooldown(slot,cooldown);
                assertEquals(element,WeaponElementalCapacitor.equippedSuperElement(d,registry));
            }
            assertEquals(9,reads.get());
        }
    }
    @Test void wrongRegisteredIdUnregisteredWrongSlotWrongClassAndNullElementFailClosed() {
        var good=ability("super",GuardianClass.HUNTER,AbilitySlot.SUPER,Element.ARC);var d=data(good.id());
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,key->Optional.empty()));
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,key->Optional.of(ability("foreign",GuardianClass.HUNTER,AbilitySlot.SUPER,Element.ARC))));
        for(var slot:AbilitySlot.values()) if(slot!=AbilitySlot.SUPER) {
            var wrong=ability("super",GuardianClass.HUNTER,slot,Element.ARC);
            assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,registry(wrong)),slot.toString());
        }
        for(var cls:GuardianClass.values())if(cls!=GuardianClass.HUNTER) {
            var wrong=ability("super",cls,AbilitySlot.SUPER,Element.ARC);
            assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,registry(wrong)),cls.toString());
        }
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,registry(ability("super",GuardianClass.HUNTER,AbilitySlot.SUPER,null))));
    }
    @Test void registeredNonSuperEquippedInSuperSlotIsNotAnEquivalentElementSource() {
        var grenade=ability("solar_grenade",GuardianClass.HUNTER,AbilitySlot.GRENADE,Element.SOLAR);
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(data(grenade.id()),registry(grenade)));
        var d=new GuardianData();d.setGuardianClass(GuardianClass.HUNTER);
        var a=ability("arc_super",GuardianClass.HUNTER,AbilitySlot.SUPER,Element.ARC);
        d.setLoadout(GuardianClass.HUNTER,new Loadout(Map.of(AbilitySlot.GRENADE,a.id())));
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,registry(a)));
    }
    @Test void liveSuperSlotOrActiveClassChangesImmediatelyAndHundredReadsDoNotMutate() {
        var arc=ability("arc_super",GuardianClass.HUNTER,AbilitySlot.SUPER,Element.ARC);
        var solar=ability("solar_super",GuardianClass.HUNTER,AbilitySlot.SUPER,Element.SOLAR);
        var d=data(arc.id());var map=Map.of(arc.id(),arc,solar.id(),solar);
        Function<Identifier,Optional<Ability>> registry=key->Optional.ofNullable(map.get(key));
        d.setSuperEnergy(.25f);d.setCooldown(AbilitySlot.SUPER,500);var loadout=d.loadout().orElseThrow();var cooldowns=d.cooldownsView();
        for(int i=0;i<100;i++)assertEquals(Element.ARC,WeaponElementalCapacitor.equippedSuperElement(d,registry));
        assertSame(loadout,d.loadout().orElseThrow());assertEquals(cooldowns,d.cooldownsView());assertEquals(.25f,d.superEnergy());
        d.setLoadout(GuardianClass.HUNTER,new Loadout(Map.of(AbilitySlot.SUPER,solar.id())));
        assertEquals(Element.SOLAR,WeaponElementalCapacitor.equippedSuperElement(d,registry));
        d.setGuardianClass(GuardianClass.TITAN);assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,registry));
        d.setLoadout(GuardianClass.TITAN,new Loadout(Map.of(AbilitySlot.SUPER,solar.id())));
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.equippedSuperElement(d,registry));
        d.setGuardianClass(GuardianClass.HUNTER);assertEquals(Element.SOLAR,WeaponElementalCapacitor.equippedSuperElement(d,registry));
    }
    @Test void nullOwnerWrappersPreserveExactPriorCompanionValues() {
        var base=new WeaponReloadPolicy.Plan(27,27,0);
        assertSame(base,WeaponElementalCapacitor.plan(null,null,base));
        assertEquals(3,WeaponElementalCapacitor.adsTicks(null,null,3,true));
        assertEquals(4,WeaponElementalCapacitor.handlingTicks(null,null,false,4));
        assertEquals(Element.KINETIC,WeaponElementalCapacitor.element(null));
        assertEquals(0,WeaponElementalCapacitor.stabilityBonus(null));
    }
    @Test void staticReadOnlyExistingAttachmentOwnerAndHeldIdentityGuards() throws Exception {
        String text=source();
        for(String required:List.of("p.isAlive()","!p.isRemoved()","!p.isSpectator()","!p.hasDisconnected()",
            "Guardians.runtimeIfPresent(p)","r.superSession == null","p.getAttachedOrElse(Guardians.DATA, null)",
            "AbilityRegistry::get","e.stack() == stack","p.getInventory().getItem(i) == stack",
            "p.getMainHandItem() != stack","p.getInventory().getItem(slot) != stack","!WeaponLoadout.canUse(p)",
            "ElementalCapacitorProfile.rolls().contains(roll)","entry.id().equals(roll.id())")) assertTrue(text.contains(required),required);
        for(String forbidden:List.of("getAttachedOrCreate","Guardians.data(","Guardians.runtime(","AbilityService.equipped(",
            "AbilityService.inSuper(",".setAttached(",".setCooldown(",".setLoadout(",".activate(",".superEnergy(",".cooldown(",
            "System.currentTimeMillis","new Session","SESSIONS",".update(","damageMultiplier(")) assertFalse(text.contains(forbidden),forbidden);
    }
    @Test void staticIncomingOutgoingHandlingIndependentOfSelectedAndHeldOtherQueries() throws Exception {
        String text=source();String handling=text.split("public static int handlingTicks")[1].split("public static int adsTicks")[0];
        assertTrue(handling.contains("source(p, stack, false)"));assertTrue(handling.contains("superElement(p)"));
        assertFalse(handling.contains("getMainHandItem"));assertFalse(handling.contains("getSelectedSlot"));
        assertTrue(text.contains("source(p, p.getMainHandItem(), true)"));
        assertTrue(text.contains("source(p, stack, true)"));assertTrue(text.contains("if (bonus == 0) return base;"));
    }
    @Test void staticExactCompanionsRawCombinationNoHiddenSurplusOrOutlawAndNoRoundingPriorBase() throws Exception {
        String text=source();
        for(String required:List.of("ElementalCapacitorProfile.compatible(entry, id, r)","RapidHitProfile.ID","FeedingFrenzyProfile.ID",
            "WeaponRapidHit.stacks(p)","WeaponFeedingFrenzy.stacks(p)","RapidHitProfile.durationMultiplier(count)",
            "FeedingFrenzyProfile.durationMultiplier(count)","bonus += reload.effectiveReloadStat() - reload.baseReloadStat()",
            "ElementalCapacitorProfile.reloadPlan(entry, bonus, scalar, base)")) assertTrue(text.contains(required),required);
        for(String forbidden:List.of("SurplusProfile.","WeaponSurplus.","OutlawProfile.","WeaponOutlaw.","base.firstTicks() *",
            "base.intervalTicks() *","base *","durationTicks(","new HashMap","static final Map")) assertFalse(text.contains(forbidden),forbidden);
    }
}
