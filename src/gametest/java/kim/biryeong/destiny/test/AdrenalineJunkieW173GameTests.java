package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.*;
import kim.biryeong.destiny.guardian.*;
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

/** Real server paid shots and accepted grenade/projectile/DoT paths, not native-input evidence. */
public final class AdrenalineJunkieW173GameTests {
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="adrenaline_junkie";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final ItemStack gun;final WeaponCatalog.Entry entry;
        final WeaponProfile profile;final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h){this(h,Element.ARC,"ammit_ar2");}
        Fixture(GameTestHelper h,Element element,String id){
            this.h=h;entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,element,new Vec3(2.5,1,6),-90,0,"W173_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Actual exact base AJ socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->{WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);});
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);Statuses.forget(p);TestPlayers.remove(p);});
        }
        Husk target(float hp){return target(8.5,1.8,hp);}
        Husk target(double x,double y,float hp){
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,y,6));targets.add(t);t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(hp);return t;
        }
        float fire(Husk t){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            int rounds=WeaponItems.magazine(gun,profile).rounds();float before=t.getHealth();
            check(h,WeaponRuntime.beginUse(p),"Actual paid weapon use accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,WeaponItems.magazine(gun,profile).rounds()==rounds-1,"One actual paid cartridge");
            return before-t.getHealth();
        }
        void stow(){
            var other=WeaponItems.create(WeaponCatalog.find("austringer").orElseThrow());
            p.getInventory().setItem(0,other);p.getInventory().setSelectedSlot(0);WeaponRuntime.tickPlayer(p);
        }
        void cast(){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(35);Guardians.data(p).setCooldown(AbilitySlot.GRENADE,0);
            check(h,AbilityService.use(p,AbilitySlot.GRENADE)==AbilityService.Result.OK,"Real Hunter grenade accepted");
        }
        void state(int stacks){check(h,WeaponAdrenalineJunkie.ownedStacks(p,gun)==stacks,"Original source x"+stacks+" got"+WeaponAdrenalineJunkie.ownedStacks(p,gun));}
        void hud(boolean live){CombatHud.update(p);check(h,DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith("destiny:hud_perk_adrenaline_junkie_")).count()==(live?8:0),"Actual eight-node count/timer HUD");}
    }
    @GameTest(structure=FLOOR,maxTicks=135,environment=ENV)
    public void paidKillOneNextEmissionDamageAndRealHudExpires(GameTestHelper h){
        var f=new Fixture(h);var baseline=f.target(1000);float damage=f.fire(baseline);check(h,damage>0,"Actual baseline hit");baseline.discard();f.state(0);
        h.runAfterDelay(8,()->{var victim=f.target(1);f.fire(victim);check(h,!victim.isAlive(),"Actual paid final blow");f.state(1);check(h,WeaponAdrenalineJunkie.remaining(f.p)==90,"Exact4.5s");f.hud(true);
            h.runAfterDelay(8,()->{var next=f.target(1000);float boosted=f.fire(next);check(h,Math.abs(boosted/damage-1.067)<.001,"Next emission not killing emission gets1.067");f.state(1);});
            h.runAfterDelay(90,()->{f.state(0);f.hud(false);h.succeed();});
        });
    }
    static void castKill(GameTestHelper h,Element element,boolean stowed,float hp){
        var f=new Fixture(h,element,"ammit_ar2");var copy=f.gun.copy();f.p.getInventory().setItem(9,copy);
        var victim=f.target(6,1,hp);if(stowed)f.stow();f.cast();f.state(0);
        h.runAfterDelay(element==Element.SOLAR?45:30,()->{
            check(h,!victim.isAlive(),"Real "+element+" grenade projectile/field/fire final blow");f.state(5);
            check(h,WeaponAdrenalineJunkie.ownedStacks(f.p,copy)==0,"Backpack copy excluded");
            if(stowed){check(h,WeaponAdrenalineJunkie.stacks(f.p)==0,"Held unrelated source has no HUD");f.hud(false);f.p.getInventory().setSelectedSlot(1);WeaponRuntime.tickPlayer(f.p);}
            check(h,WeaponAdrenalineJunkie.remaining(f.p)>0,"Original window survived ordinary stow");f.hud(true);h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=60,environment=ENV) public void actualArcGrenadeKillsForStowedOriginalNotBackpack(GameTestHelper h){castKill(h,Element.ARC,true,1);}
    @GameTest(structure=FLOOR,maxTicks=70,environment=ENV) public void actualVoidFieldPulseGivesFive(GameTestHelper h){castKill(h,Element.VOID,false,1);}
    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV) public void actualSolarScorchFireFinalBlowGivesFive(GameTestHelper h){castKill(h,Element.SOLAR,true,8);}
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void genericMeleeSuperEnvironmentAndNonlethalGrenadeNeverBorrowCredit(GameTestHelper h){
        var f=new Fixture(h);WeaponAdrenalineJunkie.capture(f.p);
        for(var element:List.of(Element.ARC,Element.SOLAR,Element.VOID)){var t=f.target(1);Combat.damage(f.p,t,5,element);f.state(0);t.discard();}
        var t=f.target(1);t.hurtServer(f.p.level(),t.damageSources().fall(),10);f.state(0);t.discard();
        var token=WeaponAdrenalineJunkie.grenadeAccepted(f.p);var healthy=f.target(1000);
        WeaponAdrenalineJunkie.grenadeDamage(f.p,token,f.p.level(),healthy,1,Element.ARC);f.state(0);
        var invulnerable=f.target(1);invulnerable.setPermanentlyInvulnerable(true);
        WeaponAdrenalineJunkie.grenadeDamage(f.p,token,f.p.level(),invulnerable,100,Element.ARC);f.state(0);
        check(h,invulnerable.isAlive(),"Rejected damage not final blow");f.hud(false);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void acceptedOriginalGrenadeCannotBuffCopiedReplacedEditedOrCleanedSource(GameTestHelper h){
        var f=new Fixture(h);var token=WeaponAdrenalineJunkie.grenadeAccepted(f.p);
        var copy=f.gun.copy();f.p.getInventory().setItem(1,copy);WeaponRuntime.tickPlayer(f.p);
        var victim=f.target(1);WeaponAdrenalineJunkie.grenadeDamage(f.p,token,f.p.level(),victim,10,Element.ARC);
        check(h,WeaponAdrenalineJunkie.ownedStacks(f.p,copy)==0,"Copied source never borrows old accepted grenade");
        f.p.getInventory().setItem(1,f.gun);WeaponRuntime.tickPlayer(f.p);f.state(0);
        var edited=WeaponAdrenalineJunkie.grenadeAccepted(f.p);WeaponPerks.clear(f.gun);WeaponPerks.select(f.gun,ID);
        WeaponAdrenalineJunkie.grenadeDamage(f.p,edited,f.p.level(),f.target(1),10,Element.ARC);f.state(0);
        var cleaned=WeaponAdrenalineJunkie.grenadeAccepted(f.p);WeaponRuntime.cleanup(f.p);
        WeaponAdrenalineJunkie.grenadeDamage(f.p,cleaned,f.p.level(),f.target(1),10,Element.ARC);f.state(0);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void actualGrenadeFiveRefreshDeduplicationHandlingAndAdsNoReloadBonus(GameTestHelper h){
        var f=new Fixture(h,Element.ARC,"farewell");
        var token=WeaponAdrenalineJunkie.grenadeAccepted(f.p);var corpse=f.target(1);
        WeaponAdrenalineJunkie.grenadeDamage(f.p,token,f.p.level(),corpse,10,Element.ARC);f.state(5);
        int reload=WeaponProfile.forEntry(f.entry).reloadTicks();
        check(h,WeaponAdrenalineJunkie.handlingTicks(f.p,f.gun,true,99)==AdrenalineJunkieProfile.timing(f.entry).readyTicks(),"Real +20handling adapter");
        check(h,WeaponAdrenalineJunkie.adsTicks(f.p,f.entry,99,true)==AdrenalineJunkieProfile.adsTicks(f.entry,false),"Raw ADS curve");
        h.runAfterDelay(5,()->{
            WeaponAdrenalineJunkie.grenadeKilled(f.p,token,corpse);
            check(h,WeaponAdrenalineJunkie.remaining(f.p)==85,"Same corpse callback cannot refresh");
            WeaponAdrenalineJunkie.grenadeDamage(f.p,token,f.p.level(),f.target(1),10,Element.ARC);
            check(h,WeaponAdrenalineJunkie.remaining(f.p)==90,"Distinct real kill refreshes max window");
            WeaponItems.save(f.gun,new WeaponMagazine(f.profile,0,100));
            check(h,WeaponRuntime.reload(f.p)&&WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==reload,"No invented reload bonus");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void exactFiveSocketsOptionalIncludingSwordAndExclusiveColumn(GameTestHelper h){
        var ids=Set.of("ammit_ar2","long_arm","farewell","goldtusk","nezarec_s_whisper");int count=0;
        for(var e:WeaponCatalog.all()){
            var stack=WeaponItems.create(e);check(h,WeaponPerks.selected(stack,ID).isEmpty(),"Optional no default");
            check(h,WeaponPerks.select(stack,ID)==ids.contains(e.id()),"Exact selected catalog membership "+e.id());
            if(ids.contains(e.id()))count++;
        }
        check(h,count==5,"No enhanced/family expansion; Goldtusk included");
        var stack=WeaponItems.create(WeaponCatalog.find("farewell").orElseThrow());
        check(h,WeaponPerks.select(stack,ID)&&WeaponPerks.select(stack,FrenzyProfile.ID)&&WeaponPerks.selected(stack,ID).isEmpty(),"Same official socket is exclusive");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void nonGrenadeScorchOverwriteAndGuardianLifecycleRevokeOldGrenadeCredit(GameTestHelper h){
        var f=new Fixture(h,Element.SOLAR,"ammit_ar2");
        var token=WeaponAdrenalineJunkie.grenadeAccepted(f.p);var victim=f.target(1);
        Statuses.scorch(f.p,victim,100,token);
        Statuses.scorch(f.p,victim,100); // Actual later non-grenade scorch replaces attribution.
        victim.damageCooldownTime=0;victim.hurtServer(f.p.level(),victim.damageSources().onFire(),10);
        check(h,!victim.isAlive(),"Real fire final blow after attribution replacement");f.state(0);
        var retired=WeaponAdrenalineJunkie.grenadeAccepted(f.p);
        var oldRuntime=Guardians.runtime(f.p);Guardians.forget(f.p);
        Guardians.data(f.p).setGuardianClass(GuardianClass.HUNTER);
        Guardians.data(f.p).setLoadout(GuardianClass.HUNTER,kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(Element.SOLAR));
        Guardians.runtime(f.p);
        check(h,oldRuntime!=Guardians.runtime(f.p),"Actual new Guardian runtime lifecycle; persistent data retained");
        WeaponAdrenalineJunkie.grenadeDamage(f.p,retired,f.p.level(),f.target(1),10,Element.SOLAR);f.state(0);h.succeed();
    }
}
