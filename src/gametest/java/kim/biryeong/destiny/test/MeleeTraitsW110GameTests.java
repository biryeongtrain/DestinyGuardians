package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
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

/** Real paid shots and accepted Hunter ability windups, reserve conservation and visible HUD graph. */
public final class MeleeTraitsW110GameTests {
    private static final String FLOOR="destiny-test:w109_arena", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static void near(GameTestHelper h,float actual,float expected,String why) {
        check(h,Math.abs(actual-expected)<.025f,why+": expected "+expected+", got "+actual);
    }
    private static final class Fixture {
        final GameTestHelper h;
        final List<ServerPlayer> players=new ArrayList<>();
        final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h=h;
            TestCleanup.register(h,()->{
                targets.forEach(Husk::discard);
                players.forEach(p->{p.stopUsingItem();WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
            });
            h.onEachTick(()->players.forEach(TestPlayers::drain));
        }
        ServerPlayer player() {
            var p=TestPlayers.hunter(h,Element.ARC,new Vec3(24,1,24),-90,0,"W110_"+UUID.randomUUID().toString().substring(0,8));
            p.setAttached(WeaponLoadout.ENABLED,true);p.setNoGravity(true);p.setOnGround(true);players.add(p);return p;
        }
        ItemStack equip(ServerPlayer p,String id,String perk) {
            var e=WeaponCatalog.find(id).orElseThrow();var gun=WeaponItems.create(e);
            if(perk!=null)check(h,WeaponPerks.select(gun,perk),"Exact optional source socket "+id+"/"+perk);
            var profile=WeaponProfile.forEntry(e);WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),profile.reserve()));
            int slot=WeaponCharacteristics.of(e).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);return gun;
        }
        Husk target(double x,double z) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,1.8,z));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);return t;
        }
        float fire(ServerPlayer p,Husk target) {
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            var gun=p.getMainHandItem();var profile=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
            int before=WeaponItems.magazine(gun,profile).rounds();float hp=target.getHealth();
            check(h,profile.chargeTicks()==0&&WeaponRuntime.beginUse(p),"Real paid instant trigger");WeaponRuntime.releaseUse(p,gun);
            check(h,WeaponItems.magazine(gun,profile).rounds()==before-1,"Exactly one paid cartridge");
            float damage=hp-target.getHealth();check(h,damage>0,"Production target took actual HP damage");return damage;
        }
        void chain(ServerPlayer p,int next,Runnable done) {
            var t=target(30,24);fire(p,t);t.discard();
            if(next==3)done.run();else h.runAfterDelay(6,()->chain(p,next+1,done));
        }
        void flanks() { target(24,29);target(24,19); }
    }
    private static long nodes(ServerPlayer p,String id) {
        return DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(WeaponPerkHud.PREFIX+id+"_")).count();
    }


    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun,WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow())); }
    private static void rounds(ItemStack gun,int count,int reserve) { WeaponItems.save(gun,new WeaponMagazine(WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()),count,reserve)); }
    private static void melee(GameTestHelper h,ServerPlayer p) {
        Guardians.data(p).setCooldown(AbilitySlot.MELEE,0);
        check(h,AbilityService.use(p,AbilitySlot.MELEE)==AbilityService.Result.OK,"Real accepted powered melee ability");
    }
    private static void both(GameTestHelper h,ItemStack gun) {
        check(h,WeaponPerks.select(gun,"grave_robber")&&WeaponPerks.select(gun,"swashbuckler"),"Different trait sockets coexist");
    }

    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void exactEightAndNineSocketsNoImplicitSelectionOrFamilyExpansion(GameTestHelper h) {
        var f=new Fixture(h);f.player();
        for(String id:List.of("swashbuckler","grave_robber")) {
            int count=0;
            for(var entry:WeaponCatalog.all()) {
                var gun=WeaponItems.create(entry);check(h,WeaponPerks.selected(gun,id).isEmpty(),"New weapon starts unselected");
                var pool=id.equals("swashbuckler")?SwashbucklerProfile.rolls():GraveRobberProfile.rolls();
                boolean eligible=pool.stream().anyMatch(r->r.id().equals(entry.id()));
                check(h,WeaponPerks.select(gun,id)==eligible,"Only pinned exact weapon socket: "+entry.id());
                if(eligible)count++;
            }
            check(h,count==(id.equals("swashbuckler")?8:9),"Exact base socket count");
        }
        var gun=f.equip(f.players.getFirst(),"steelfeather_repeater",null);both(h,gun);
        check(h,WeaponPerks.selected(gun,"swashbuckler").orElseThrow().socket()==4
                &&WeaponPerks.selected(gun,"grave_robber").orElseThrow().socket()==3,"Independent columns");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=45,environment=ENV)
    public void actualWeaponKillGivesOneStackAndNextEmissionDamage(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"steelfeather_repeater","swashbuckler");
        var baseline=f.target(30,24);float damage=f.fire(p,baseline);baseline.discard();
        check(h,WeaponSwashbuckler.stacks(p)==0,"Nonlethal gun hit never grants stacks");
        h.runAfterDelay(6,()->{
            var victim=f.target(30,24);victim.setHealth(1);f.fire(p,victim);
            check(h,!victim.isAlive()&&WeaponSwashbuckler.stacks(p)==1,"Real paid final blow gives one stack");
            check(h,WeaponSwashbuckler.remaining(p)==90,"4.5 second initial deadline");
            h.runAfterDelay(6,()->{
                var next=f.target(30,24);near(h,f.fire(p,next),damage*1.067f,"Next paid damage uses stack1 snapshot");
                check(h,WeaponSwashbuckler.remaining(p)==84,"Ordinary damage never refreshes stack clock");h.succeed();
            });
        });
    }

    @GameTest(structure=FLOOR,maxTicks=45,environment=ENV)
    public void poweredNonlethalContactRefillsFromReserveButDoesNotGiveSwashbuckler(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"steelfeather_repeater",null);both(h,gun);
        rounds(gun,2,7);int capacity=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()).magazine();var target=f.target(25.8,24);melee(h,p);
        check(h,ammo(gun).rounds()==2,"Acceptance is not a hit/refill");
        h.runAfterDelay(8,()->{
            check(h,target.isAlive()&&target.getHealth()<1000,"Actual nonlethal Arc contact");
            check(h,ammo(gun).rounds()==capacity&&ammo(gun).reserve()==0,"Primary documented infinite reserve fills actual capacity");
            check(h,WeaponSwashbuckler.stacks(p)==0,"Melee hit without kill grants no damage stacks");
            check(h,!WeaponRuntime.reloading(p)&&WeaponKillClip.remaining(p)==0,"Trait refill is not a reload callback");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=50,environment=ENV)
    public void realArcKillGivesAllFiveWithActualDamageAndEightHudNodes(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"steelfeather_repeater",null);both(h,gun);
        var baseTarget=f.target(30,24);float base=f.fire(p,baseTarget);baseTarget.discard();rounds(gun,1,20);
        var victim=f.target(25.8,24);victim.setHealth(1);melee(h,p);
        h.runAfterDelay(10,()->{
            check(h,!victim.isAlive()&&WeaponSwashbuckler.stacks(p)==5,"Real Hunter kill instantly grants max stacks");
            check(h,ammo(gun).rounds()==WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()).magazine()&&ammo(gun).reserve()==0,"Same contact refills the primary magazine from infinite reserves");
            CombatHud.update(p);check(h,nodes(p,"swashbuckler")==8,"Actual x5/timer HUD graph");
            h.runAfterDelay(16,()->{
                var next=f.target(30,24);near(h,f.fire(p,next),base*1.333f,"Five stacks multiply actual paid damage by1.333");h.succeed();
            });
        });
    }

    @GameTest(structure=FLOOR,maxTicks=55,environment=ENV)
    public void swapDuringRealMeleeWindupNeverRewardsReplacementGun(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var original=f.equip(p,"steelfeather_repeater",null);both(h,original);rounds(original,1,10);
        var t=f.target(25.8,24);t.setHealth(1);melee(h,p);
        var replacement=WeaponItems.create(WeaponCatalog.find("steelfeather_repeater").orElseThrow());both(h,replacement);rounds(replacement,2,10);
        p.getInventory().setItem(9,original);p.getInventory().setItem(p.getInventory().getSelectedSlot(),replacement);WeaponRuntime.tickPlayer(p);
        h.runAfterDelay(10,()->{
            check(h,!t.isAlive(),"Ability itself still contacts after weapon swap");
            check(h,ammo(original).rounds()==1&&ammo(replacement).rounds()==2,"No source or replacement refill");
            check(h,WeaponSwashbuckler.stacks(p)==0,"No replacement receives old melee kill credit");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=50,environment=ENV)
    public void sameTickTraitClearReselectRevokesAcceptedCastCredit(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"steelfeather_repeater",null);both(h,gun);rounds(gun,1,10);
        var t=f.target(25.8,24);t.setHealth(1);melee(h,p);WeaponPerks.clear(gun);both(h,gun);
        h.runAfterDelay(10,()->{
            check(h,!t.isAlive(),"Delayed actual damage still happens");
            check(h,ammo(gun).rounds()==1&&WeaponSwashbuckler.stacks(p)==0,"Old cast token cannot revive after exact edit");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=130,environment=ENV)
    public void actualPoweredHitsRespectThreeSecondRefillLockAcrossSelectionEdits(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"dust_rock_blues","grave_robber");rounds(gun,1,2);
        var t=f.target(25.8,24);melee(h,p);
        h.runAfterDelay(12,()->{
            check(h,t.getHealth()<1000&&ammo(gun).rounds()==3&&ammo(gun).reserve()==0,"First powered hit transfers two finite cartridges");rounds(gun,1,2);
            WeaponPerks.clear(gun);WeaponPerks.select(gun,"grave_robber");melee(h,p);
            h.runAfterDelay(12,()->{
                check(h,ammo(gun).rounds()==1,"Edit never bypasses owner cooldown");
                h.runAfterDelay(45,()->{melee(h,p);h.runAfterDelay(10,()->{
                    check(h,ammo(gun).rounds()==3&&ammo(gun).reserve()==0,"Later real hit past60ticks refills");h.succeed();
                });});
            });
        });
    }

    @GameTest(structure=FLOOR,maxTicks=55,environment=ENV)
    public void zeroReserveValidContactSpendsLocalLockWithoutInventingAmmo(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"dust_rock_blues","grave_robber");rounds(gun,1,0);
        var target=f.target(25.8,24);melee(h,p);
        h.runAfterDelay(12,()->{
            check(h,target.getHealth()<1000&&ammo(gun).rounds()==1&&ammo(gun).reserve()==0,"No reserve invented");
            rounds(gun,1,2);melee(h,p);h.runAfterDelay(12,()->{
                check(h,ammo(gun).rounds()==1&&ammo(gun).reserve()==2,"No-transfer proc still spends documented local cooldown");h.succeed();
            });
        });
    }

    @GameTest(structure=FLOOR,maxTicks=125,environment=ENV)
    public void swashbucklerAllStacksExpireTogetherAndHudFullyRemoves(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"steelfeather_repeater","swashbuckler");var t=f.target(25.8,24);t.setHealth(1);melee(h,p);
        h.runAfterDelay(8,()->{
            int remaining=WeaponSwashbuckler.remaining(p);check(h,WeaponSwashbuckler.stacks(p)==5&&remaining>0,"Five stacks live");
            h.runAfterDelay(remaining-1,()->check(h,WeaponSwashbuckler.stacks(p)==5,"All five on last live tick"));
            h.runAfterDelay(remaining,()->{CombatHud.update(p);
                check(h,WeaponSwashbuckler.stacks(p)==0&&nodes(p,"swashbuckler")==0,"All expire at deadline, not one-stack decay");h.succeed();});
        });
    }

    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void sameTickNativeStowReturnClearsLiveStacksButNotPaidSnapshot(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"steelfeather_repeater","swashbuckler");var t=f.target(25.8,24);t.setHealth(1);melee(h,p);
        h.runAfterDelay(10,()->{
            var token=WeaponSwashbuckler.capture(p);near(h,token.multiplier(),1.333f,"Actual earned captured snapshot");
            int selected=p.getInventory().getSelectedSlot();int away=selected==0?1:0;WeaponRuntime.selectedSlotChanging(p,away);
            p.getInventory().setSelectedSlot(away);WeaponRuntime.selectedSlotChanging(p,selected);p.getInventory().setSelectedSlot(selected);
            check(h,WeaponSwashbuckler.stacks(p)==0,"Same-tick stow not sampled away");near(h,token.multiplier(),1.333f,"Paid source snapshot unchanged by stow");
            WeaponPerks.clear(gun);WeaponPerks.select(gun,"swashbuckler");near(h,token.multiplier(),1,"Real selection edit revokes old snapshot");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void genericAbilityAndSuperKillsNeverMasqueradeAsMelee(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"steelfeather_repeater",null);both(h,gun);rounds(gun,1,10);
        var a=f.target(26,24);a.setHealth(1);Combat.damage(p.level(),p,a,100,Element.ARC,AmmoGeneration.ABILITY);
        var b=f.target(27,24);b.setHealth(1);Combat.damage(p.level(),p,b,100,Element.ARC,AmmoGeneration.SUPER);
        check(h,!a.isAlive()&&!b.isAlive()&&WeaponSwashbuckler.stacks(p)==0&&ammo(gun).rounds()==1,"No generic playerAttack/onKill guess");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=45,environment=ENV)
    public void copyingBuffedWeaponNeverCopiesLiveRuntimeStackState(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"steelfeather_repeater","swashbuckler");var t=f.target(25.8,24);t.setHealth(1);melee(h,p);
        h.runAfterDelay(10,()->{
            check(h,WeaponSwashbuckler.stacks(p)==5,"Original earned live buff");
            var copy=gun.copy();p.getInventory().setItem(9,gun);p.getInventory().setItem(p.getInventory().getSelectedSlot(),copy);WeaponRuntime.tickPlayer(p);
            check(h,WeaponSwashbuckler.stacks(p)==0,"Copied item state is not runtime identity");h.succeed();
        });
    }
    private static void weaponKills(Fixture f,ServerPlayer p,int left,Runnable done) {
        var t=f.target(30,24);t.setHealth(1);f.fire(p,t);
        if(left==1)done.run();else f.h.runAfterDelay(6,()->weaponKills(f,p,left-1,done));
    }
    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void fivePaidWeaponKillsReachCapAndNextKillRefreshesWithoutOverflow(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"steelfeather_repeater","swashbuckler");
        weaponKills(f,p,5,()->{
            check(h,WeaponSwashbuckler.stacks(p)==5&&WeaponSwashbuckler.remaining(p)==90,"Five actual source kills");
            h.runAfterDelay(6,()->weaponKills(f,p,1,()->{
                check(h,WeaponSwashbuckler.stacks(p)==5&&WeaponSwashbuckler.remaining(p)==90,"Cap is five and real sixth kill refreshes");h.succeed();
            }));
        });
    }
    @GameTest(structure=FLOOR,maxTicks=60,environment=ENV)
    public void realSolarKnifeNonlethalDirectHitRefillsFiniteSpecialAmmo(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();Guardians.data(p).setLoadout(GuardianClass.HUNTER,
                kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(Element.SOLAR));
        var gun=f.equip(p,"dust_rock_blues","grave_robber");rounds(gun,1,2);var t=f.target(28,24);melee(h,p);
        h.runAfterDelay(18,()->{
            check(h,t.isAlive()&&t.getHealth()<1000,"Real launched knife direct contact, not injected confirmation");
            check(h,ammo(gun).rounds()==3&&ammo(gun).reserve()==0&&ammo(gun).total()==3,"Finite special ammo conserved across ranged melee hit");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=50,environment=ENV)
    public void sameTickStowDuringActualMeleeRevokesPendingSourcesEvenAfterReturn(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"steelfeather_repeater",null);both(h,gun);rounds(gun,1,0);
        var t=f.target(25.8,24);t.setHealth(1);melee(h,p);
        int selected=p.getInventory().getSelectedSlot(),away=selected==0?1:0;WeaponRuntime.selectedSlotChanging(p,away);
        p.getInventory().setSelectedSlot(away);WeaponRuntime.selectedSlotChanging(p,selected);p.getInventory().setSelectedSlot(selected);
        h.runAfterDelay(10,()->{
            check(h,!t.isAlive(),"Actual ability still kills");
            check(h,WeaponSwashbuckler.stacks(p)==0&&ammo(gun).rounds()==1,"Neither cast source revives after same-tick stow");h.succeed();
        });
    }

}
