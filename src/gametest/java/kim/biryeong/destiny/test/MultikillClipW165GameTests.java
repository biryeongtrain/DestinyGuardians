package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
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

/** Actual production paid shots, ammo insertion and HUD graph; not keyboard or framebuffer evidence. */
public final class MultikillClipW165GameTests {
    static final String FLOOR="destiny-test:w109_arena", ENV="destiny-test:w90_isolated";
    static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    static void near(GameTestHelper h,float a,float b,String why){check(h,Math.abs(a-b)<.035f,why+": "+a+" != "+b);}
    static final class Fixture {
        final GameTestHelper h; final ServerPlayer p; final ItemStack gun; final WeaponProfile profile;
        final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h){
            this.h=h; p=TestPlayers.hunter(h,Element.ARC,new Vec3(24,1,24),-90,0,"W165_"+UUID.randomUUID().toString().substring(0,8));
            p.setAttached(WeaponLoadout.ENABLED,true);p.setNoGravity(true);p.setOnGround(true);
            var e=WeaponCatalog.find("gnawing_hunger").orElseThrow();profile=WeaponProfile.forEntry(e);gun=WeaponItems.create(e);
            check(h,WeaponPerks.select(gun,"multikill_clip"),"Exact official Gnawing socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),profile.reserve()));
            int slot=WeaponCharacteristics.of(e).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
            h.onEachTick(()->{WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);});
        }
        Husk target(float hp){
            targets.forEach(Husk::discard);targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(30,1.8,24));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(hp);return t;
        }
        float fire(Husk target){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            int rounds=ammo().rounds();float before=target.getHealth();
            check(h,WeaponRuntime.beginUse(p),"Production instant-use trigger accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,ammo().rounds()==rounds-1,"Exactly one paid cartridge");
            float result=before-target.getHealth();check(h,result>0,"Actual HP damage confirmed");return result;
        }
        WeaponMagazine ammo(){return WeaponItems.magazine(gun,profile);}
        void kills(int n,Runnable done){fire(target(1));if(n==1)done.run();else h.runAfterDelay(profile.intervalTicks()+2,()->kills(n-1,done));}
        void reload(Runnable done){
            check(h,WeaponRuntime.reload(p),"Actual reload accepted");
            check(h,WeaponMultikillClip.stacks(p)==0,"No buff on reload windup");
            h.succeedWhen(()->{check(h,!WeaponRuntime.reloading(p),"Await actual reload recovery");done.run();});
        }
        long nodes(){return DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(WeaponPerkHud.PREFIX+"multikill_clip_")).count();}
    }

    @GameTest(structure=FLOOR,maxTicks=160,environment=ENV)
    public void paidKillRealReloadDamageAndHud(GameTestHelper h){
        var f=new Fixture(h);float baseline=f.fire(f.target(1000));
        h.runAfterDelay(f.profile.intervalTicks()+2,()->f.kills(1,()->{
            check(h,WeaponMultikillClip.stacks(f.p)==0,"Kill alone is not buff");
            f.reload(()->{
                check(h,WeaponMultikillClip.stacks(f.p)==1,"Reload grants one stack");
                check(h,f.ammo().rounds()==f.profile.magazine(),"Primary credit follows existing ammo path");
                near(h,f.fire(f.target(1000)),baseline*1.17f,"Next paid shot gains17percent");
                WeaponPerkHud.update(f.p);check(h,f.nodes()==8,"Actual stacked timer graph has8nodes");h.succeed();
            });
        }));
    }

    @GameTest(structure=FLOOR,maxTicks=160,environment=ENV)
    public void threeDistinctPaidFinalBlowsGrantFifty(GameTestHelper h){
        var f=new Fixture(h);float baseline=f.fire(f.target(1000));
        h.runAfterDelay(f.profile.intervalTicks()+2,()->f.kills(3,()->f.reload(()->{
            check(h,WeaponMultikillClip.stacks(f.p)==3,"Three distinct paid final blows");
            near(h,f.fire(f.target(1000)),baseline*1.5f,"Next emission gains50percent");h.succeed();
        })));
    }

    @GameTest(structure=FLOOR,maxTicks=210,environment=ENV)
    public void weakerRetriggerOverwritesRatherThanMax(GameTestHelper h){
        var f=new Fixture(h);f.kills(3,()->{
            check(h,WeaponRuntime.reloadFromMarksmanDodge(f.p)>0,"Real instant ammo credit");
            check(h,WeaponMultikillClip.stacks(f.p)==3,"Three-stack instant reload policy");
            h.runAfterDelay(f.profile.intervalTicks()+2,()->f.kills(1,()->{
                check(h,WeaponRuntime.reloadFromMarksmanDodge(f.p)>0,"Second real ammo credit");
                check(h,WeaponMultikillClip.stacks(f.p)==1,"One overwrites three, no max retention");h.succeed();
            }));
        });
    }

    @GameTest(structure=FLOOR,maxTicks=120,environment=ENV)
    public void cancellationAndNoKillReloadCannotFabricateBuff(GameTestHelper h){
        var f=new Fixture(h);f.fire(f.target(1000));
        check(h,WeaponRuntime.reload(f.p),"Reload without kill");WeaponRuntime.cancelUseForSkill(f.p);
        check(h,WeaponMultikillClip.stacks(f.p)==0,"Cancelled zero-kill windup has no buff");
        check(h,f.ammo().rounds()==f.profile.magazine()-1,"Cancelled reload has no ammo credit");
        h.runAfterDelay(f.profile.intervalTicks()+2,()->f.kills(1,()->{
            check(h,WeaponRuntime.reload(f.p),"Qualifying reload begins");WeaponRuntime.cancelUseForSkill(f.p);
            check(h,WeaponMultikillClip.stacks(f.p)==0,"Qualifying kill still needs actual credit");h.succeed();
        }));
    }

    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void acceptedStowClearsLiveAndPendingButSourceEditRevokesSnapshot(GameTestHelper h){
        var f=new Fixture(h);f.kills(1,()->{
            WeaponRuntime.reloadFromMarksmanDodge(f.p);
            var shot=WeaponMultikillClip.capture(f.p);near(h,shot.multiplier(),1.17f,"Captured paid-source value");
            WeaponRuntime.selectedSlotChanging(f.p,0);
            check(h,WeaponMultikillClip.stacks(f.p)==0,"Even same-tick accepted stow clears live buff");
            near(h,shot.multiplier(),1.17f,"In-flight source value survives ordinary stow");
            WeaponPerkHud.update(f.p);check(h,f.nodes()==0,"No stale HUD after stow");
            WeaponPerks.clear(f.gun);near(h,shot.multiplier(),1,"Real saved roll edit revokes old source");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=135,environment=ENV)
    public void buffExpiresAndHudReadsNeverExtendIt(GameTestHelper h){
        var f=new Fixture(h);f.kills(1,()->{
            WeaponRuntime.reloadFromMarksmanDodge(f.p);check(h,WeaponMultikillClip.stacks(f.p)==1,"Active base buff");
            for(int i=1;i<=100;i++)h.runAfterDelay(i,()->WeaponPerkHud.update(f.p));
            h.runAfterDelay(101,()->{check(h,WeaponMultikillClip.stacks(f.p)==0&&WeaponMultikillClip.remaining(f.p)==0,"100tick base expiry");
                WeaponPerkHud.update(f.p);check(h,f.nodes()==0,"No retained stack/timer nodes");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void copiedStackAndLifecycleReplacementRevokeSource(GameTestHelper h){
        var f=new Fixture(h);f.kills(1,()->{
            WeaponRuntime.reloadFromMarksmanDodge(f.p);var token=WeaponMultikillClip.capture(f.p);
            near(h,token.multiplier(),1.17f,"Original stack source active");
            var replacement=f.gun.copy();f.p.getInventory().setItem(f.p.getInventory().getSelectedSlot(),replacement);
            WeaponRuntime.tickPlayer(f.p);near(h,token.multiplier(),1,"Dropped exact source cannot fund delayed damage");
            check(h,WeaponPerks.selected(replacement,"multikill_clip").isPresent(),"Persisted optional roll copied");
            check(h,WeaponMultikillClip.stacks(f.p)==0,"Copied roll is not a copied runtime buff");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void fullMagazineInstantReloadCannotActivateWithoutCredit(GameTestHelper h){
        var f=new Fixture(h);f.kills(1,()->{
            // Fixture preparation only: force full ammunition without calling a reload reward hook.
            WeaponItems.save(f.gun,new WeaponMagazine(f.profile,f.profile.magazine(),f.profile.reserve()));
            check(h,WeaponRuntime.reloadFromMarksmanDodge(f.p)==0,"Full primary has zero actual transfer");
            check(h,WeaponMultikillClip.stacks(f.p)==0,"No positive ammo insertion means no activation");h.succeed();
        });
    }

}
