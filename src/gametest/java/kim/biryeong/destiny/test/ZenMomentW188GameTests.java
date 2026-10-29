package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
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

/** Actual paid-damage and Player.actuallyHurt integration, not token injection or native input.
 * Zen visual shake is not substituted by changing real recoil direction/stability/accuracy.
 */
public final class ZenMomentW188GameTests {
    static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    static void check(GameTestHelper h,boolean ok,String text){h.assertTrue(ok,Component.literal(text));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final WeaponCatalog.Entry entry;
        final WeaponProfile profile;final ItemStack gun;final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h){
            this.h=h;
            entry=ZenMomentProfile.rolls().stream().map(r->WeaponCatalog.find(r.id()).orElseThrow()).distinct()
                .filter(e->{var a=WeaponProfile.forEntry(e);return a.mode()==WeaponProfile.Mode.HITSCAN&&a.chargeTicks()==0&&a.burst()==1;})
                .sorted(Comparator.comparingInt(e->e.id().equals("gnawing_hunger")?0:1)).findFirst().orElseThrow();
            profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W188_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            p.getAttribute(Attributes.ARMOR).setBaseValue(0);p.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
            p.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ZenMomentProfile.ID),"Exact official base trait socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),profile.reserve()));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            kim.biryeong.destiny.guardian.Guardians.runtime(p);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->TestPlayers.drain(p));
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        WeaponMagazine ammo(){return WeaponItems.magazine(gun,profile);}
        Husk target(){
            targets.forEach(Husk::discard);targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.setHealth(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);return t;
        }
        void fire(){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            int before=ammo().rounds();check(h,WeaponRuntime.beginUse(p),"Real trigger accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,ammo().rounds()==before-1,"One paid cartridge");
        }
        void hit(){var t=target();fire();check(h,t.getHealth()<1000&&t.isAlive(),"Real positive nonfinal body damage");}
        int gap(){return (int)Math.ceil(profile.cadenceTicks())+2;}
        float flinch(Husk attacker){
            p.setHealth(20);p.setAbsorptionAmount(0);p.damageCooldownTime=0;p.setXRot(0);
            WeaponAiming.cleanup(p);WeaponAiming.tick(p);TestPlayers.drain(p);
            p.hurtServer(p.level(),p.damageSources().mobAttack(attacker),2);
            check(h,p.getHealth()<20,"Actual incoming HP damage");return -p.getXRot();
        }
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void actualPaidBodyHitActivatesAndExpiresWithoutFakeHud(GameTestHelper h){
        var f=new Fixture(h);check(h,WeaponZenMoment.flinchScalar(f.p)==1,"Selected alone inert");f.hit();
        check(h,WeaponZenMoment.flinchScalar(f.p)<1,"Actual damage grants resistance");int ticks=WeaponZenMoment.remaining(f.p);
        check(h,ticks>0&&ticks<80,"Bounded actual effect window");CombatHud.update(f.p);
        check(h,DisplayHud.getHuds(f.p).keySet().stream().noneMatch(k->k.contains("zen_moment")),"No invented original HUD timer/counter");
        long hitTick=f.p.level().getServer().getTickCount();boolean[] before={false};
        h.onEachTick(()->{
            long elapsed=f.p.level().getServer().getTickCount()-hitTick;
            if(elapsed==ticks-1){check(h,WeaponZenMoment.flinchScalar(f.p)<1&&WeaponZenMoment.remaining(f.p)==1,"Server tick before deadline remains active: elapsed="+elapsed+", remaining="+WeaponZenMoment.remaining(f.p)+", scalar="+WeaponZenMoment.flinchScalar(f.p));before[0]=true;}
            if(elapsed==ticks){check(h,before[0]&&WeaponZenMoment.flinchScalar(f.p)==1&&WeaponZenMoment.remaining(f.p)==0,"Exact server deadline, no query refresh: before="+before[0]+", elapsed="+elapsed+", remaining="+WeaponZenMoment.remaining(f.p)+", scalar="+WeaponZenMoment.flinchScalar(f.p));h.succeed();}
        });
    }
    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void immuneAndMissArePaidButDoNotActivate(GameTestHelper h){
        var f=new Fixture(h);var t=f.target();t.setPermanentlyInvulnerable(true);f.fire();
        check(h,t.getHealth()==1000&&WeaponZenMoment.flinchScalar(f.p)==1,"Blocked damage not a hit credit");t.discard();
        h.runAfterDelay(f.gap(),()->{f.fire();check(h,WeaponZenMoment.remaining(f.p)==0,"Paid miss cannot grant");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void abilityDamageAndTraitSelectionHaveNoCredit(GameTestHelper h){
        var f=new Fixture(h);var t=f.target();Combat.damage(f.p,t,2,Element.SOLAR);
        check(h,t.getHealth()<1000&&WeaponZenMoment.remaining(f.p)==0,"Actual ability damage does not borrow paid weapon source");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void clearReselectAndCopiedReplacementRetireSource(GameTestHelper h){
        var f=new Fixture(h);f.hit();check(h,WeaponPerks.clear(f.gun),"Actual trait edit");
        check(h,WeaponZenMoment.flinchScalar(f.p)==1,"Immediate edit retirement");check(h,WeaponPerks.select(f.gun,ZenMomentProfile.ID),"Reselect");
        check(h,WeaponZenMoment.remaining(f.p)==0,"Same-tick reselect cannot resurrect earned source");
        f.p.getInventory().setItem(f.p.getInventory().getSelectedSlot(),f.gun.copy());WeaponRuntime.tickPlayer(f.p);
        check(h,WeaponZenMoment.flinchScalar(f.p)==1,"Copied stack has no earned runtime");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void realIncomingDamageUsesResistanceWithoutChangingDamageOrAmmo(GameTestHelper h){
        var f=new Fixture(h);var attacker=f.target();float base=f.flinch(attacker);check(h,base>0,"Baseline incoming rotation exists");
        f.hit();attacker=f.targets.getFirst();float scalar=WeaponZenMoment.flinchScalar(f.p);check(h,scalar<1,"Earned before hit");
        int rounds=f.ammo().rounds();float reduced=f.flinch(attacker);
        check(h,Math.abs(reduced-base*scalar)<.0005f,"Actual Player.actuallyHurt rotation composes scalar before camera budget");
        check(h,f.p.getHealth()==18&&f.ammo().rounds()==rounds,"No incoming damage resistance or free ammo");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void stowingStopsHeldResistanceAndCleanupIsNeutral(GameTestHelper h){
        var f=new Fixture(h);f.hit();f.p.getInventory().setSelectedSlot((f.p.getInventory().getSelectedSlot()+1)%9);WeaponRuntime.tickPlayer(f.p);
        check(h,WeaponZenMoment.flinchScalar(f.p)==1,"Stowed source cannot grant held resistance");WeaponRuntime.cleanup(f.p);
        check(h,WeaponZenMoment.remaining(f.p)==0,"Owner cleanup neutral");h.succeed();
    }
}
