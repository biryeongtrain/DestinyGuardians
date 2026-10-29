package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.combat.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.function.Consumer;

/** Actual paid weapon transactions, not a mathematical token-only damage test or native input. */
public final class VorpalW181GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="vorpal_weapon";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final WeaponCatalog.Entry entry;final WeaponProfile profile;
        final List<Husk> targets=new ArrayList<>();ItemStack gun;boolean charging;int initial;
        Fixture(GameTestHelper h,WeaponAmmoType ammo) {this(h,ammo,false);}
        Fixture(GameTestHelper h,WeaponAmmoType ammo,boolean projectile) {
            this.h=h;
            entry=VorpalProfile.rolls().stream().map(x->WeaponCatalog.find(x.id()).orElseThrow())
                    .filter(e->WeaponCharacteristics.of(e).ammo()==ammo)
                    .filter(e->!projectile||WeaponProfile.forEntry(e).mode()==WeaponProfile.Mode.PROJECTILE)
                    .filter(e->{var a=WeaponProfile.forEntry(e);return a.mode()!=WeaponProfile.Mode.MELEE&&a.burst()==1;})
                    .sorted(java.util.Comparator.comparingInt(e->WeaponProfile.forEntry(e).mode()==WeaponProfile.Mode.HITSCAN?0:1))
                    .findFirst().orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W181_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            h.onEachTick(()->{
                p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);p.getRandom().setSeed(0x5DEECE66DL);
                if(charging)check(h,WeaponRuntime.heartbeatUse(p),"Actual charge heartbeat remains accepted");
                WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
                if(charging&&WeaponItems.magazine(gun,profile).rounds()<initial){charging=false;WeaponRuntime.releaseUse(p,gun);}
            });
            TestCleanup.register(h,()->{targets.forEach(t->{Statuses.forget(t);t.discard();});WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        Husk target(boolean boss){
            targets.forEach(t->{Statuses.forget(t);t.discard();});targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1.8,6));targets.add(t);t.setNoAi(true);t.setNoGravity(true);
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(5000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(5000);if(boss)t.addTag("destiny_boss");return t;
        }
        void equip(boolean selected){
            WeaponRuntime.cleanup(p);gun=WeaponItems.create(entry);
            if(selected)check(h,WeaponPerks.select(gun,ID),"Actual optional official base Vorpal socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponRuntime.tickPlayer(p);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
        }
        void shot(boolean selected,boolean boss,boolean stow,Consumer<Float> done){
            equip(selected);var t=target(boss);float health=t.getHealth();initial=WeaponItems.magazine(gun,profile).rounds();
            check(h,beginUse(p),"Real trigger accepted "+entry.id());
            charging=profile.chargeTicks()>0;
            if(!charging)WeaponRuntime.releaseUse(p,gun);
            if(stow){check(h,!charging&&profile.mode()==WeaponProfile.Mode.PROJECTILE,"Delayed outgoing projectile fixture");
                WeaponPerks.clear(gun);p.getInventory().setSelectedSlot(7);WeaponRuntime.tickPlayer(p);}
            h.startSequence().thenIdle(Math.max(35,profile.chargeTicks()+25)).thenExecute(()->{
                check(h,!charging&&WeaponItems.magazine(gun,profile).rounds()==initial-1,"Exactly one real cartridge funded transaction");
                float loss=health-t.getHealth();check(h,loss>0&&Float.isFinite(loss),"Actual target lost HP, not token arithmetic");
                check(h,WeaponRuntime.activeProjectiles(p)==0,"Paid flight reached terminal target before comparison");
                CombatHud.update(p);check(h,DisplayHud.getHuds(p).keySet().stream().noneMatch(k->k.startsWith("destiny:hud_perk_vorpal")),"No invented timed/counting HUD for passive conditional damage");
                done.accept(loss);
            });
        }
    }
    static void ratio(GameTestHelper h,WeaponAmmoType ammo,float expected){
        var f=new Fixture(h,ammo);
        f.shot(false,true,false,base->f.shot(true,true,false,buffed->{
            check(h,Math.abs(buffed/base-expected)<.002,"Real paid "+ammo+" boss multiplier "+buffed+"/"+base);
            f.shot(true,false,false,normal->f.shot(false,false,false,control->{
                check(h,Math.abs(normal-control)<.003,"Normal Mob with5000HP is not automatically a boss");h.succeed();}));
        }));
    }
    @GameTest(structure=FLOOR,maxTicks=300,environment=ENV) public void primaryPaidBossAndNormalDamage(GameTestHelper h){ratio(h,WeaponAmmoType.PRIMARY,1.2f);}
    @GameTest(structure=FLOOR,maxTicks=300,environment=ENV) public void specialPaidBossAndNormalDamage(GameTestHelper h){ratio(h,WeaponAmmoType.SPECIAL,1.15f);}
    @GameTest(structure=FLOOR,maxTicks=300,environment=ENV) public void heavyPaidBossAndNormalDamage(GameTestHelper h){ratio(h,WeaponAmmoType.HEAVY,1.1f);}
    @GameTest(structure=FLOOR,maxTicks=150,environment=ENV)
    public void actualPaidProjectileRetainsOriginalTraitAfterStowAndEdit(GameTestHelper h){
        var f=new Fixture(h,WeaponAmmoType.HEAVY,true);
        f.shot(false,true,false,base->f.shot(true,true,true,enhanced->{
            check(h,Math.abs(enhanced/base-1.1f)<.002,"Actual outgoing paid heavy flight retains source before socket clear/stow");h.succeed();}));
    }
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void exactOptionalSocketsNoDefaultOrUnboundedSavedTrait(GameTestHelper h){
        var ids=VorpalProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet());int n=0;
        for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);check(h,WeaponPerks.selected(s,ID).isEmpty(),"No free default");
            check(h,WeaponPerks.select(s,ID)==ids.contains(e.id()),"Official base pool only "+e.id());if(ids.contains(e.id()))n++;}
        check(h,n==ids.size()&&n>0,"Actual catalog selectable pool nonempty");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void liveSnapshotIsPureAndRetiresForFutureSourceWithoutChangingPaidToken(GameTestHelper h){
        var f=new Fixture(h,WeaponAmmoType.PRIMARY);f.equip(true);var boss=f.target(true);
        var paid=WeaponVorpal.capture(f.p);check(h,Math.abs(paid.multiplier(boss)-1.2f)<.0001,"Captured eligible source");
        WeaponPerks.clear(f.gun);check(h,WeaponVorpal.capture(f.p).multiplier(boss)==1,"Future damage cannot borrow cleared choice");
        check(h,Math.abs(paid.multiplier(boss)-1.2f)<.0001,"Paid immutable source survives edit");
        boss.removeTag("destiny_boss");check(h,paid.multiplier(boss)==1,"Target eligibility resolved at impact, not source capture");
        boss.addTag("destiny_vehicle");check(h,Math.abs(paid.multiplier(boss)-1.2f)<.0001,"Explicit living vehicle mapping");
        float before=boss.getHealth();Combat.damage(f.p.level(),f.p,boss,10,Element.ARC,AmmoGeneration.ABILITY);
        check(h,Math.abs(before-boss.getHealth()-10)<.001,"Ability is not routed through passive weapon damage");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void realNativeBossClassesQualifyButTaggedPlayerArmorStandAndCorpseDoNot(GameTestHelper h){
        var f=new Fixture(h,WeaponAmmoType.PRIMARY);f.equip(true);var token=WeaponVorpal.capture(f.p);
        var wither=h.spawn(EntityTypes.WITHER,new Vec3(10,3,10));wither.setNoAi(true);
        var dragon=h.spawn(EntityTypes.ENDER_DRAGON,new Vec3(14,8,14));dragon.setNoAi(true);
        var stand=h.spawn(EntityTypes.ARMOR_STAND,new Vec3(8,1,8));stand.addTag("destiny_boss");
        TestCleanup.register(h,()->{wither.discard();dragon.discard();stand.discard();});
        check(h,Math.abs(token.multiplier(wither)-1.2f)<.0001&&Math.abs(token.multiplier(dragon)-1.2f)<.0001,"Actual native boss entity instances qualify without custom tags");
        f.p.addTag("destiny_boss");check(h,token.multiplier(f.p)==1&&token.multiplier(stand)==1,"Even tagged Player/ArmorStand cannot qualify");
        var dead=f.target(true);dead.setHealth(0);check(h,token.multiplier(dead)==1,"Corpse is not an eligible target");
        wither.discard();dragon.discard();stand.discard();h.succeed();
    }

}
