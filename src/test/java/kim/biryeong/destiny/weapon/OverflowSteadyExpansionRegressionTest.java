package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import org.objectweb.asm.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Regression for component-aware pickup transactions and expanded canonical initialization. */
class OverflowSteadyExpansionRegressionTest {
    @Test void componentExpandedOverflowTargetsUseEffectiveCapacityAndFiniteFunds() {
        for (String id : List.of("krait", "submission")) {
            var entry = WeaponCatalog.find(id).orElseThrow();
            var base = WeaponProfile.forEntry(entry);
            assertTrue(OverflowProfile.supports(entry));
            for (String component : List.of("extended_mag", "appended_mag", "tactical_mag")) {
                int effective = WeaponComponents.magazine(base.magazine(), WeaponComponents.find(component).orElseThrow().stat("magazine"));
                assertTrue(effective > base.magazine());
                int target = WeaponOverflow.target(entry, effective);
                assertEquals(2*effective, target);
                // Finite fixture exercises the same reloadOverflow operation used by real pickup.
                var finite = new WeaponProfile(WeaponProfile.Mode.HITSCAN,1,1,effective,500,20,20,
                        0,1,1,0,0,0,0,false,false);
                var ammo = new WeaponMagazine(finite,effective,effective);
                long total=ammo.total();
                assertEquals(effective,ammo.reloadOverflow(target));
                assertEquals(target,ammo.rounds());assertEquals(0,ammo.reserve());assertEquals(total,ammo.total());
                assertEquals(0,ammo.reloadOverflow(target));
                var saved = new WeaponMagazine(finite,ammo.rounds(),ammo.reserve(),ammo.overflow(),ammo.loadedLimit());
                assertEquals(target,saved.rounds());assertEquals(total,saved.total());
                var limited = new WeaponMagazine(finite,effective,3);
                assertEquals(3,limited.reloadOverflow(target));assertEquals(effective+3,limited.rounds());
                assertEquals(0,limited.reserve());
            }
        }
    }
    @Test void actualPickupCallsStackAwareTargetRatherThanEntryOnlyTarget() throws Exception {
        List<String> targets=new ArrayList<>();
        try(var in=getClass().getClassLoader().getResourceAsStream("kim/biryeong/destiny/weapon/AmmoEconomy.class")) {
            assertNotNull(in);
            new ClassReader(in).accept(new ClassVisitor(Opcodes.ASM9) {
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String sig,String[] ex) {
                    if(!name.equals("grant"))return null;
                    return new MethodVisitor(Opcodes.ASM9) {
                        @Override public void visitMethodInsn(int op,String owner,String name,String desc,boolean itf) {
                            if(owner.equals("kim/biryeong/destiny/weapon/WeaponOverflow")&&name.equals("target"))targets.add(desc);
                        }
                    };
                }
            },ClassReader.SKIP_FRAMES|ClassReader.SKIP_DEBUG);
        }
        assertEquals(List.of("(Lnet/minecraft/world/item/ItemStack;Lkim/biryeong/destiny/weapon/WeaponCatalog$Entry;)I"),targets);
    }
    @Test void expandedCatalogCannotPoisonSteadyHandsInitializationAndUsesOwnCurveRows() {
        assertEquals(170,SteadyHandsProfile.initialTicks());
        assertEquals(24,LegendaryWeapons.ids().size());
        for(String id:LegendaryWeapons.ids()) {
            var entry=WeaponCatalog.find(id).orElseThrow();
            assertTrue(SteadyHandsProfile.handlingSupported(entry),id);
            assertTrue(SteadyHandsProfile.adsSupported(entry),id);
        }
        var entry=WeaponCatalog.find("krait").orElseThrow();
        var ready=LegendaryWeapons.field(entry.id(),"curves").getAsJsonObject("ready");
        double seconds=ready.get("evpp").getAsDouble()*10000+ready.get("vpp").getAsDouble()*100+ready.get("offset").getAsDouble();
        assertEquals(Math.max(1,(int)Math.ceil(seconds*.825*20)),SteadyHandsProfile.handlingTicks(entry,true,1));
        var forged=new WeaponCatalog.Entry(entry.id(),entry.family(),"forged",entry.name(),entry.source_frame_label(),entry.item_model());
        assertFalse(SteadyHandsProfile.handlingSupported(forged));
    }
}
