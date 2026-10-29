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

/** Scoped W195 event, reload, ADS and powered-sword regressions.
 * These are headless server actions, not native input, screenshots or animation validation. */
public final class PerksW195GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static void hud(GameTestHelper h,ServerPlayer p,String perk,boolean active) {
        CombatHud.update(p);
        check(h,kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p)
                .containsKey("destiny:hud_perk_"+perk+"_label")==active,
                "W199 actual "+perk+" HUD visibility="+active);
    }
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final List<Husk> targets=new ArrayList<>();
        ItemStack gun;WeaponCatalog.Entry entry;WeaponProfile profile;int slot;
        Fixture(GameTestHelper h) {
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W195_"+UUID.randomUUID().toString().substring(0,8));
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
        void face() { p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0); }
    }
    @GameTest(structure="destiny-test:w78_floor",environment=ENV,maxTicks=110)
    public void openingShotActualFirstPaidBulletHasItsOwnRangeAndCooldownCannotBeReadiedByQueries(GameTestHelper h) {
        var f=new Fixture(h);f.equip("duke_mk_44","opening_shot");
        // Range witness stays inside the existing 48-block loaded firing deck.
        f.p.setPos(h.absoluteVec(new Vec3(3,4,6)));
        double distance=WeaponBallistics.of(f.entry).start()+2;
        var target=f.target(1000,false);target.setPos(f.p.position().add(distance,0.8,0));
        f.face();
        var from=f.p.getEyePosition();var hit=target.getBoundingBox().inflate(.03).clip(from,from.add(40,0,0)).orElseThrow();
        check(h,f.p.level().clip(new net.minecraft.world.level.ClipContext(from,hit,net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,f.p)).getType()==net.minecraft.world.phys.HitResult.Type.MISS,"Loaded deck supplies clear actual shot corridor");
        check(h,beginUse(f.p),"First paid shot accepted");WeaponRuntime.releaseUse(f.p,f.gun);
        float first=1000-target.getHealth();check(h,first>0,"Real first bullet hits target beyond base falloff start");
        h.onEachTick(f::tick);
        h.startSequence().thenIdle((int)Math.ceil(f.profile.cadenceTicks())+2).thenExecute(()->{
            target.setHealth(1000);target.damageCooldownTime=0;f.face();
            check(h,beginUse(f.p),"Second paid bullet");WeaponRuntime.releaseUse(f.p,f.gun);
            float second=1000-target.getHealth();check(h,second>0&&first>second,"Only accepted opening shot extends actual damage falloff");
            int ammo=f.rounds();for(int i=0;i<5;i++){WeaponRuntime.ammunition(f.p);WeaponAiming.ballistics(f.p,f.entry);}
            check(h,ammo==f.rounds(),"Forecast reads cannot generate ammunition or a paid emission");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=75)
    public void boxBreathingConsumesPreparedEffectOnTheActualLastRoundAndActualReleaseCancelsNextWindow(GameTestHelper h) {
        var f=new Fixture(h);f.equip("beloved","box_breathing");
        WeaponItems.save(f.gun,new WeaponMagazine(f.profile,1,0));var target=f.target(1000,true);
        ads(f.p,true);f.tick();h.onEachTick(f::tick);
        h.startSequence().thenIdle(32).thenExecute(()->{
            f.face();check(h,beginUse(f.p),"Prepared actual last-round shot accepted");WeaponRuntime.releaseUse(f.p,f.gun);
            double unbuffed=f.profile.damage()*WeaponBallistics.of(f.entry).precision();
            check(h,f.rounds()==0&&1000-target.getHealth()>unbuffed+0.1,"Prepared weakspot effect survives post-payment empty magazine and buffs actual precision damage");
            ads(f.p,false);WeaponAiming.releasedAim(f.p);f.tick();
            WeaponItems.save(f.gun,new WeaponMagazine(f.profile,1,0));
            h.startSequence().thenIdle(3).thenExecute(()->{
                ads(f.p,true);f.tick();check(h,WeaponAiming.requested(f.p),"Fresh left click after debounce enters a new ADS interval");
            });
            h.startSequence().thenIdle((int)Math.ceil(f.profile.cadenceTicks())+2).thenExecute(()->{
                target.setHealth(1000);target.damageCooldownTime=0;f.face();
                check(h,beginUse(f.p),"Fresh ADS shot accepted");WeaponRuntime.releaseUse(f.p,f.gun);
                check(h,Math.abs(1000-target.getHealth()-unbuffed)<0.1,"Release/press cannot inherit the consumed prepared effect");h.succeed();
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=90)
    public void whirlwindActualPaidHitsBuffNextContactAndActualGuardClearsProgress(GameTestHelper h) {
        var f=new Fixture(h);f.equip("abide_the_return","whirlwind_blade");var target=f.target(1000,false);
        target.setPos(h.absoluteVec(new Vec3(4.5,1,6)));h.onEachTick(f::tick);f.face();WeaponRuntime.onPunch(f.p);
        h.startSequence().thenIdle(12).thenExecute(()->{
            check(h,WeaponWhirlwindBlade.stacks(f.p)==1,"First real powered contact advances once");
            hud(h,f.p,"whirlwind_blade",true);
            float first=1000-target.getHealth();
            h.startSequence().thenIdle(12).thenExecute(()->{
                target.setHealth(1000);target.damageCooldownTime=0;f.p.setPos(h.absoluteVec(new Vec3(2.5,1,6)));f.face();WeaponRuntime.onPunch(f.p);
                h.startSequence().thenIdle(12).thenExecute(()->{
                    check(h,1000-target.getHealth()>first&&WeaponWhirlwindBlade.stacks(f.p)==2,"Next actual contact gets pre-own-hit stack and advances once");
                    f.p.setShiftKeyDown(true);
                    // SwordCycle accepts one input sample per server tick. A HUD read
                    // in this callback must not make a duplicate tick apply new input.
                    h.startSequence().thenIdle(1).thenExecute(()->{
                        f.tick();
                        check(h,WeaponRuntime.swordStatus(f.p).orElseThrow().guarding(),"Next real tick accepts guard input");
                        check(h,WeaponWhirlwindBlade.stacks(f.p)==0,"Actual owned sword guarding removes stacks");
                        hud(h,f.p,"whirlwind_blade",false);
                        h.succeed();
                    });
                });
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=75)
    public void enGardeRealReadyWindowExpiresWithoutRearmingWhileTheSameSwordIsHeld(GameTestHelper h) {
        var f=new Fixture(h);f.equip("abide_the_return","en_garde");var target=f.target(1000,false);
        target.setPos(h.absoluteVec(new Vec3(4.5,1,6)));f.face();
        check(h,WeaponEnGarde.remaining(f.p)>0,"Initial actual usable original sword establishes one ready window");
        hud(h,f.p,"en_garde",true);
        h.onEachTick(f::tick);WeaponRuntime.onPunch(f.p);
        h.startSequence().thenIdle(12).thenExecute(()->check(h,1000-target.getHealth()>f.profile.damage(),"Paid contact uses accepted ready-window damage"));
        h.startSequence().thenIdle(40).thenExecute(()->{
            check(h,WeaponEnGarde.remaining(f.p)==0,"Same original cannot continually rearm after expiry");
            hud(h,f.p,"en_garde",false);
            f.tick();f.tick();check(h,WeaponEnGarde.remaining(f.p)==0,"Repeated runtime observation is not a new ready event");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=100)
    public void dynamicSwayCountsPaidContinuousFireAndRealReleaseRemovesTheChain(GameTestHelper h) {
        var f=new Fixture(h);f.equip("ammit_ar2","dynamic_sway_reduction");f.face();int before=f.rounds();
        check(h,WeaponRuntime.heartbeatUse(f.p),"Actual automatic heartbeat trigger");
        h.onEachTick(()->{WeaponRuntime.heartbeatUse(f.p);f.tick();});
        h.startSequence().thenIdle(36).thenExecute(()->{
            int spent=before-f.rounds();check(h,spent>=10&&WeaponDynamicSway.stacks(f.p)==10,"Only paid held-fire emissions reach maximum chain");
            hud(h,f.p,"dynamic_sway",true);
            WeaponRuntime.releaseUse(f.p,f.gun);
            check(h,WeaponDynamicSway.stacks(f.p)==0,"Real native release clears continuous-fire state");
            hud(h,f.p,"dynamic_sway",false);
            h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=85)
    public void assassinsBladeActualKillKeepsMovementAcrossStowAndForeignModifierSurvivesCleanup(GameTestHelper h) {
        var f=new Fixture(h);f.equip("abide_the_return","assassins_blade");var target=f.target(1,false);
        target.setPos(h.absoluteVec(new Vec3(4.5,1,6)));var speed=f.p.getAttribute(Attributes.MOVEMENT_SPEED);double baseline=speed.getValue();
        h.onEachTick(f::tick);f.face();WeaponRuntime.onPunch(f.p);
        h.startSequence().thenIdle(12).thenExecute(()->{
            check(h,!target.isAlive()&&WeaponAssassinsBlade.remaining(f.p)>0,"Real sword final blow activates original source buff");f.tick();
            hud(h,f.p,"assassins_blade",true);
            check(h,speed.getValue()>baseline,"Actual native walking modifier installed");
            int other=f.slot==0?1:0;f.p.getInventory().setItem(other,new ItemStack(Items.STONE));f.select(other);f.tick();
            check(h,WeaponAssassinsBlade.remaining(f.p)>0&&speed.getValue()>baseline,"Buff and movement remain while original sword is stowed");
            hud(h,f.p,"assassins_blade",true);
            f.p.setSprinting(true);f.tick();check(h,speed.getModifier(WeaponPerkMovement.ID)==null,"Walking mapping does not boost native sprint");f.p.setSprinting(false);f.tick();
            var own=speed.getModifier(WeaponPerkMovement.ID);check(h,own!=null,"Walking mapping restored while buff lives");
            speed.removeModifier(WeaponPerkMovement.ID);
            var foreign=new net.minecraft.world.entity.ai.attributes.AttributeModifier(WeaponPerkMovement.ID,.2,net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
            speed.addTransientModifier(foreign);f.tick();WeaponRuntime.cleanup(f.p);
            hud(h,f.p,"assassins_blade",false);
            check(h,speed.getModifier(WeaponPerkMovement.ID)==foreign,"Foreign same-ID replacement survives tick and cleanup");
            speed.removeModifier(WeaponPerkMovement.ID);h.succeed();
        });
    }
}
