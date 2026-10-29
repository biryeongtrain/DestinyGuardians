package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Scoped W194 event, reload, ADS and powered-sword regressions.
 * These are headless server actions, not native input, screenshots or animation validation. */
public final class PerksW194GameTests {
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final List<Husk> targets=new ArrayList<>();
        ItemStack gun;WeaponCatalog.Entry entry;WeaponProfile profile;int slot;
        Fixture(GameTestHelper h) {
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W194_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);AmmoEconomy.cleanup(p);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void equip(String id,String perk) {
            entry=WeaponCatalog.find(id).orElseThrow();gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,perk),"Exact base socket "+id+"/"+perk);
            profile=WeaponProfile.forEntry(entry);WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),profile.reserve()));
            slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            tick();
        }
        void tick() { WeaponRuntime.tickPlayer(p);TestPlayers.drain(p); }
        void select(int index) { p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(index));TestPlayers.drain(p); }
        Husk target(float hp,boolean precision) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,precision?1:1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(hp);return t;
        }
        WeaponMagazine ammo() { return WeaponItems.magazine(gun,profile); }
        int rounds() { return WeaponItems.magazine(gun,profile).rounds(); }
        void face() { p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);p.getRandom().setSeed(0x5DEECE66DL); }
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=35)
    public void mulliganRealMissRefundsPaidRoundWithoutReloadOrQueryProc(GameTestHelper h) {
        var f=new Fixture(h);f.equip("patron_of_lost_causes","mulligan");
        WeaponItems.save(f.gun,new WeaponMagazine(f.profile,1,0));
        f.face();f.p.getRandom().setSeed(0); // Two W241 dispersion draws, then reward roll 15 < primary 20 percent.
        check(h,WeaponRuntime.beginUse(f.p),"Real paid single-round trigger accepted");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,f.rounds()==1,"Miss returns one paid cartridge into loaded magazine");
        var before=f.gun.get(net.minecraft.core.component.DataComponents.CUSTOM_DATA);
        for(int i=0;i<5;i++){WeaponRuntime.ammunition(f.p);WeaponItems.magazine(f.gun,f.profile);}
        check(h,before.equals(f.gun.get(net.minecraft.core.component.DataComponents.CUSTOM_DATA)),"Queries cannot generate or save ammo");
        f.tick();check(h,!WeaponRuntime.reloading(f.p),"Refunded last shot prevents empty auto-reload");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=30)
    public void mulliganInvulnerableGeometryContactIsHitAndOneTokenNeverRerolls(GameTestHelper h) {
        var f=new Fixture(h);f.equip("hammerhead","mulligan");var target=f.target(1000,false);target.setPermanentlyInvulnerable(true);
        int before=f.rounds();f.face();f.p.getRandom().setSeed(0x5DEECE66DL); // Near-axis real invulnerable contact.
        check(h,WeaponRuntime.beginUse(f.p),"Paid shot accepted");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,f.rounds()==before-1&&target.getHealth()==1000,"Actual entity contact counts as hit even without actual damage");
        var ammo=f.ammo();check(h,ammo.consume(),"Explicit paid token fixture");WeaponItems.save(f.gun,ammo);
        var token=WeaponMulligan.capture(f.p,f.entry);f.p.getRandom().setSeed(2);
        check(h,WeaponMulligan.resolved(f.p,token,false)==1,"One authorized deterministic refund");
        int loaded=f.rounds();check(h,WeaponMulligan.resolved(f.p,token,false)==0&&f.rounds()==loaded,"Duplicate token cannot refund or roll again");
        var invalid=WeaponMulligan.capture(f.p,f.entry);WeaponPerks.clear(f.gun);
        check(h,WeaponMulligan.resolved(f.p,invalid,false)==0,"Roll removal rejects the old source before grant");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=65)
    public void noDistractionsUsesExistingAdsClockAndPerkEditCannotCarryEarnedBuff(GameTestHelper h) {
        var f=new Fixture(h);f.equip("beloved","no_distractions");ads(f.p,true);f.tick();h.onEachTick(f::tick);
        h.startSequence().thenIdle(19).thenExecute(()->check(h,!WeaponAiming.noDistractions(f.p),"Actual ADS interval has not reached existing activation boundary"));
        h.startSequence().thenIdle(21).thenExecute(()->{
            check(h,WeaponAiming.noDistractions(f.p),"Exact base roll activates existing ADS flinch resistance");
            WeaponPerks.clear(f.gun);check(h,!WeaponAiming.noDistractions(f.p),"Removing trait removes benefit immediately");
            check(h,WeaponPerks.select(f.gun,"no_distractions"),"Original exact trait may be selected again");
            check(h,!WeaponAiming.noDistractions(f.p),"Edit-away/back cannot inherit the earned clock");
            h.startSequence().thenIdle(21).thenExecute(()->{
                check(h,WeaponAiming.noDistractions(f.p),"New owned interval may earn again");
                ads(f.p,false);WeaponAiming.releasedAim(f.p);check(h,!WeaponAiming.noDistractions(f.p),"Actual ADS release removes benefit");h.succeed();
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=160)
    public void killingTallyActualKillBuffsNextPaidEmissionAndAcceptedReloadResetsStacks(GameTestHelper h) {
        var f=new Fixture(h);f.equip("fixed_odds","killing_tally");var corpse=f.target(1,false);f.face();
        check(h,WeaponRuntime.beginUse(f.p),"Actual paid shot");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,!corpse.isAlive()&&WeaponKillingTally.stacks(f.p)==1,"Actual final blow gives one stack");
        CombatHud.update(f.p);
        check(h,kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(f.p)
                .containsKey("destiny:hud_perk_killing_tally_label"),"W199 real kill shows count HUD");
        var next=f.target(1000,false);h.onEachTick(f::tick);
        h.startSequence().thenIdle((int)Math.ceil(f.profile.cadenceTicks())+2).thenExecute(()->{
            f.face();check(h,WeaponRuntime.beginUse(f.p),"Next paid shot");WeaponRuntime.releaseUse(f.p,f.gun);
            check(h,Math.abs((1000-next.getHealth())-f.profile.damage()*1.1)<.01,"First kill cannot self-buff; next emission receives one multiplier");
            check(h,WeaponRuntime.reload(f.p)&&WeaponKillingTally.stacks(f.p)==0,"Real accepted reload removes live stacks");
            CombatHud.update(f.p);
            check(h,!kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(f.p)
                    .containsKey("destiny:hud_perk_killing_tally_label"),"W199 accepted reload removes stale count HUD");
            h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=160)
    public void sympatheticArsenalActualSourceReloadRefillsStowedFiniteAmmoOnlyOnce(GameTestHelper h) {
        var f=new Fixture(h);f.equip("cold_denial","sympathetic_arsenal");var corpse=f.target(1,false);
        var buddyEntry=WeaponCatalog.find("beloved").orElseThrow();var buddy=WeaponItems.create(buddyEntry);var buddyProfile=WeaponProfile.forEntry(buddyEntry);
        WeaponItems.save(buddy,new WeaponMagazine(buddyProfile,0,3));f.p.getInventory().setItem(1,buddy);
        f.face();check(h,WeaponRuntime.beginUse(f.p),"Actual paid source shot");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,!corpse.isAlive(),"Actual source kill");h.onEachTick(f::tick);
        h.startSequence().thenIdle((int)Math.ceil(f.profile.cadenceTicks())+3).thenExecute(()->{
            check(h,WeaponRuntime.reload(f.p),"Actual timed reload after final burst accepted");
            int phase=WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration();
            check(h,WeaponItems.magazine(buddy,buddyProfile).rounds()==0,"No early refill on reload acceptance");
            h.startSequence().thenIdle(phase+1).thenExecute(()->{
                var ammo=WeaponItems.magazine(buddy,buddyProfile);
                check(h,ammo.rounds()==3&&ammo.reserve()==0&&ammo.total()==3,"Other weapon receives only its finite available reserve");
                f.tick();f.tick();check(h,WeaponItems.magazine(buddy,buddyProfile).rounds()==3,"Completion replay never repeats stowed refill");h.succeed();
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=120)
    public void relentlessStrikesActualPaidSwordContactsGenerateOneAndEmptySwordCannotProc(GameTestHelper h) {
        var f=new Fixture(h);f.equip("abide_the_return","relentless_strikes");var target=f.target(1000,false);
        target.setPos(h.absoluteVec(new Vec3(4.5,1,6)));int before=f.rounds();h.onEachTick(f::tick);
        for(int i=0;i<3;i++) {
            int index=i;
            h.startSequence().thenIdle(1+i*20).thenExecute(()->{
                f.p.setPos(h.absoluteVec(new Vec3(2.5,1,6)));f.face();
                check(h,WeaponRuntime.onPunch(f.p),"Accepted sword input "+index);
            });
        }
        h.startSequence().thenIdle(55).thenExecute(()->{
            check(h,target.getHealth()<1000&&f.rounds()==before-3+1,"Three real powered contacts spend three and generate one");
            WeaponItems.save(f.gun,new WeaponMagazine(f.profile,0,0));
            f.p.setPos(h.absoluteVec(new Vec3(2.5,1,6)));f.face();WeaponRuntime.onPunch(f.p);
            h.startSequence().thenIdle(12).thenExecute(()->{check(h,f.rounds()==0,"Empty unpowered swipe cannot generate ammo");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=100)
    public void tirelessBladeFirstPoweredKillRewardsButStowDoesNotRearmFirstKill(GameTestHelper h) {
        var f=new Fixture(h);f.equip("abide_the_return","tireless_blade");var first=f.target(1,false);first.setPos(h.absoluteVec(new Vec3(4.5,1,6)));
        int before=f.rounds();h.onEachTick(f::tick);f.face();check(h,WeaponRuntime.onPunch(f.p),"First real powered swipe accepted");
        h.startSequence().thenIdle(10).thenExecute(()->{
            check(h,!first.isAlive()&&f.rounds()==before,"First spawn kill refunds its paid cartridge");
            int other=f.slot==0?1:0;f.p.getInventory().setItem(other,new ItemStack(Items.STONE));f.select(other);f.tick();f.select(f.slot);f.tick();
            h.startSequence().thenIdle(25).thenExecute(()->{
                var second=f.target(1,false);second.setPos(h.absoluteVec(new Vec3(4.5,1,6)));f.p.setPos(h.absoluteVec(new Vec3(2.5,1,6)));f.face();
                check(h,WeaponRuntime.onPunch(f.p),"Second powered swipe accepted");
                h.startSequence().thenIdle(10).thenExecute(()->{check(h,!second.isAlive()&&f.rounds()==before-1,"Stow cannot renew first-kill reward; next kill advances ordinary pair");h.succeed();});
            });
        });
    }
}
