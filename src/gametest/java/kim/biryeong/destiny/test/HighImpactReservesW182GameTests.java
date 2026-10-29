package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.hud.CombatHud;
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
import java.util.function.*;

/** Actual paid cartridges and delayed bolt routing; no native input or formula-only damage claim. */
public final class HighImpactReservesW182GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="high_impact_reserves";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static WeaponCatalog.Entry find(Predicate<WeaponCatalog.Entry> filter) {
        return HighImpactReservesProfile.rolls().stream().map(r->WeaponCatalog.find(r.id()).orElseThrow()).filter(filter).findFirst().orElseThrow();
    }
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final WeaponCatalog.Entry entry;final WeaponProfile profile;
        final List<Husk> targets=new ArrayList<>();ItemStack gun;boolean charging,mutateSharedAfterPayment,editedDuringShot;int initial;
        Fixture(GameTestHelper h,WeaponCatalog.Entry e) {
            this.h=h;entry=e;profile=WeaponProfile.forEntry(e);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W182_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            h.onEachTick(()->{
                p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);p.getRandom().setSeed(0x5DEECE66DL);
                // Server API fixture supplies the real two-hand use heartbeat while charging.
                // beginUse alone is not a held native item/lease and cannot advance this charge.
                if(charging)check(h,WeaponRuntime.heartbeatUse(p),"Charging heartbeat accepted");
                WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
                if(charging&&WeaponItems.magazine(gun,profile).rounds()<initial){
                    charging=false;WeaponRuntime.releaseUse(p,gun);
                    if(mutateSharedAfterPayment){
                        check(h,profile.sharedBurstAmmo()&&WeaponItems.magazine(gun,profile).rounds()==initial-1,"One real cartridge paid before deliberate edit/refill fixture");
                        WeaponPerks.clear(gun);WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),0));
                        editedDuringShot=true;mutateSharedAfterPayment=false;
                    }
                }
                // Isolate paid damage: cancel a newly started last-shot auto reload before credit.
                // Runtime starts it only after all shared bolts terminate; primary reserve is infinite.
                if(WeaponRuntime.reloading(p))WeaponRuntime.cancelUseForSkill(p);
            });
            TestCleanup.register(h,()->{targets.forEach(t->t.discard());WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void shot(boolean selected,int rounds,boolean editAfterLaunch,Consumer<Float> done) {
            WeaponRuntime.cleanup(p);targets.forEach(t->t.discard());targets.clear();editedDuringShot=false;gun=WeaponItems.create(entry);
            if(selected)check(h,WeaponPerks.select(gun,ID),"Official optional HIR socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,rounds,0));initial=rounds;
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponRuntime.tickPlayer(p);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1.8,6));targets.add(t);t.setNoAi(true);t.setNoGravity(true);
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(5000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(5000);float health=t.getHealth();
            check(h,beginUse(p),"Actual trigger accepted "+entry.id());charging=profile.chargeTicks()>0;
            if(!charging)WeaponRuntime.releaseUse(p,gun);
            if(editAfterLaunch){check(h,!charging&&profile.mode()==WeaponProfile.Mode.PROJECTILE,"Already paid delayed projectile");WeaponPerks.clear(gun);WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),0));p.getInventory().setSelectedSlot(7);WeaponRuntime.tickPlayer(p);}
            h.startSequence().thenIdle(Math.max(40,profile.chargeTicks()+30)).thenExecute(()->{
                check(h,!charging,"Charge paid and release consumed");
                int paid=profile.sharedBurstAmmo()?1:Math.min(profile.burst(),rounds);
                if(!editAfterLaunch&&!editedDuringShot)check(h,WeaponItems.magazine(gun,profile).rounds()==rounds-paid,"Exact paid cartridge count, no reserve refill");
                float loss=health-t.getHealth();check(h,loss>0&&Float.isFinite(loss),"Actual target HP loss");
                check(h,WeaponRuntime.activeProjectiles(p)==0,"Flight terminal");CombatHud.update(p);
                check(h,DisplayHud.getHuds(p).keySet().stream().noneMatch(k->k.startsWith("destiny:hud_perk_high_impact")),"No fake timed HUD for magazine passive");done.accept(loss);
            });
        }
    }
    static WeaponCatalog.Entry single(){return find(e->{var p=WeaponProfile.forEntry(e);return p.mode()==WeaponProfile.Mode.HITSCAN&&p.burst()==1&&p.chargeTicks()==0;});}
    static void ratio(GameTestHelper h,int rounds,boolean stow,WeaponCatalog.Entry e) {
        var f=new Fixture(h,e);float expected=HighImpactReservesProfile.multiplier(e,rounds,f.profile.magazine());
        f.shot(false,rounds,false,base->f.shot(true,rounds,stow,buffed->{check(h,Math.abs(buffed/base-expected)<.003,"Actual paid ratio uses true pre-consumption count: "+buffed+"/"+base+" expected "+expected);h.succeed();}));
    }
    @GameTest(structure=FLOOR,maxTicks=150,environment=ENV) public void fullMagazineSelectedDoesNotGainLowAmmoBonus(GameTestHelper h){var e=single();ratio(h,WeaponProfile.forEntry(e).magazine(),false,e);}
    @GameTest(structure=FLOOR,maxTicks=150,environment=ENV) public void lowerHalfPaidHitscanUsesPriorRoundCount(GameTestHelper h){var e=single();ratio(h,Math.max(1,WeaponProfile.forEntry(e).magazine()/2),false,e);}
    @GameTest(structure=FLOOR,maxTicks=150,environment=ENV) public void finalPaidRoundRetainsBonusAfterMagazineBecomesEmpty(GameTestHelper h){ratio(h,1,false,single());}
    @GameTest(structure=FLOOR,maxTicks=250,environment=ENV) public void sharedFusionCartridgeFreezesAllDelayedBolts(GameTestHelper h){var e=find(x->x.family().equals("fusion_rifle")&&WeaponProfile.forEntry(x).sharedBurstAmmo());ratio(h,1,false,e);}
    @GameTest(structure=FLOOR,maxTicks=180,environment=ENV) public void ordinaryPulseBulletsCaptureEachActuallyPaidCount(GameTestHelper h){
        var e=find(x->x.family().equals("pulse_rifle")&&!WeaponProfile.forEntry(x).sharedBurstAmmo());var f=new Fixture(h,e);int rounds=f.profile.magazine()/2+1;
        double expected=java.util.stream.IntStream.range(0,Math.min(f.profile.burst(),rounds)).mapToDouble(i->HighImpactReservesProfile.multiplier(e,rounds-i,f.profile.magazine())).average().orElseThrow();
        f.shot(false,rounds,false,base->f.shot(true,rounds,false,buffed->{check(h,Math.abs(buffed/base-expected)<.003,"Each paid pulse bullet re-evaluates its own pre-round count, not one trigger snapshot");h.succeed();}));
    }
    @GameTest(structure=FLOOR,maxTicks=250,environment=ENV) public void alreadyPaidFusionBoltsDoNotBorrowLaterSocketOrRefilledAmmo(GameTestHelper h){
        var e=find(x->x.family().equals("fusion_rifle")&&WeaponProfile.forEntry(x).sharedBurstAmmo());var f=new Fixture(h,e);
        float expected=HighImpactReservesProfile.multiplier(e,1,f.profile.magazine());
        f.shot(false,1,false,base->{f.mutateSharedAfterPayment=true;f.shot(true,1,false,buffed->{
            check(h,f.editedDuringShot&&WeaponPerks.selected(f.gun,ID).isEmpty(),"Deliberate socket-clear/refill happened after payment");
            check(h,Math.abs(buffed/base-expected)<.003,"All already-funded delayed bolts keep immutable original low-ammo token after socket clear and fixture refill");h.succeed();
        });});
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV) public void alreadyPaidSourceTokenIsImmutableAndAbilityRemainsUnmodified(GameTestHelper h){
        var e=single();var f=new Fixture(h,e);
        f.shot(true,1,false,loss->{
            // The controlled fixture has really paid its one cartridge; this is an API/source boundary test,
            // not another damage emission or proof of a selectable projectile pool.
            var token=WeaponHighImpactReserves.capture(f.p,1,f.profile.magazine());float expected=HighImpactReservesProfile.multiplier(e,1,f.profile.magazine());
            check(h,Math.abs(token.multiplier()-expected)<.0001,"Owned selected source at explicit paid-count boundary");
            WeaponPerks.clear(f.gun);WeaponItems.save(f.gun,new WeaponMagazine(f.profile,f.profile.magazine(),0));
            check(h,Math.abs(token.multiplier()-expected)<.0001,"Token never consults later selected socket or refilled ammunition");
            check(h,WeaponHighImpactReserves.capture(f.p,1,f.profile.magazine()).multiplier()==1,"New unselected source cannot borrow previous cartridge token");
            var t=f.targets.getFirst();float before=t.getHealth();
            kim.biryeong.destiny.combat.Combat.damage(f.p.level(),f.p,t,10,Element.ARC,kim.biryeong.destiny.weapon.AmmoGeneration.ABILITY);
            check(h,Math.abs(before-t.getHealth()-10)<.002,"Actual ability transaction is not multiplied by selected/previous HIR source");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void exactOptionalCatalogSocketsNoDefault(GameTestHelper h){
        var ids=HighImpactReservesProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet());
        for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);check(h,WeaponPerks.selected(s,ID).isEmpty(),"No default");check(h,WeaponPerks.select(s,ID)==ids.contains(e.id()),"Exact official base selection "+e.id());}check(h,!ids.isEmpty(),"Nonempty real pool");h.succeed();
    }
}
