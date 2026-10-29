package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.hud.CombatHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual production paid transactions; master registers/runs the isolated server gate. */
public final class UnrelentingW200GameTests {
    private static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static final class Fixture {
        final GameTestHelper h; final ServerPlayer p; final List<Husk> targets=new ArrayList<>();
        ItemStack gun; WeaponProfile profile; int slot;
        Fixture(GameTestHelper h,String id) {
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W200u_"+UUID.randomUUID().toString().substring(0,7));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            p.getFoodData().setFoodLevel(17); // Prevent unrelated native food regeneration.
            gun=WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
            check(h,WeaponPerks.select(gun,"unrelenting"),"Exact legal base Unrelenting socket "+id);
            var entry=WeaponItems.entry(gun).orElseThrow();profile=WeaponProfile.forEntry(entry);
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),0));
            slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            tick();p.setHealth(4);
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);WeaponUnrelenting.cleanup(p);
                AmmoEconomy.cleanup(p);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void tick() { WeaponRuntime.tickPlayer(p);TestPlayers.drain(p); }
        void stow() {
            int next=slot==0?1:0;p.getInventory().setItem(next,new ItemStack(Items.STONE));
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(next));TestPlayers.drain(p);
        }
        Husk target(boolean powerful,boolean sword) {
            targets.forEach(Husk::discard);targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(sword?4.5:8.5,sword?1:1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1);
            if(powerful)t.entityTags().add("destiny_boss");return t;
        }
        void fire() {
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);
            int before=WeaponItems.magazine(gun,profile).rounds();
            check(h,WeaponRuntime.beginUse(p),"Real production trigger accepts paid round");WeaponRuntime.releaseUse(p,gun);
            check(h,WeaponItems.magazine(gun,profile).rounds()==before-1,"Exactly one cartridge paid");TestPlayers.drain(p);
        }
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=90)
    public void threeActualPaidFinalBlowsStartHealingAcrossStowAndActualDamageStopsIt(GameTestHelper h) {
        var f=new Fixture(h,"farewell");h.onEachTick(f::tick);
        var first=f.target(false,false);f.fire();
        check(h,!first.isAlive()&&!WeaponUnrelenting.active(f.p)&&f.p.getHealth()==4,"First actual rank-and-file kill only advances progress");
        int gap=(int)Math.ceil(f.profile.cadenceTicks())+2;
        h.runAfterDelay(gap,()->{
            var second=f.target(false,false);f.fire();
            check(h,!second.isAlive()&&!WeaponUnrelenting.active(f.p)&&f.p.getHealth()==4,"Second paid kill still does not heal");
            h.runAfterDelay(gap,()->{
                var third=f.target(false,false);f.fire();
                float procHP=f.p.getHealth();
                check(h,!third.isAlive()&&procHP>4&&WeaponUnrelenting.active(f.p),"Third positive actual final blow heals and begins own regen");
                for(int i=0;i<5;i++)check(h,WeaponUnrelenting.active(f.p),"Pure repeated observer stays active");
                check(h,f.p.getHealth()==procHP,"HUD observers never heal");
                f.stow();
                h.runAfterDelay(3,()->{
                    check(h,WeaponUnrelenting.active(f.p)&&f.p.getHealth()>procHP,"Original source regen persists real hotbar stow");
                    f.p.setPermanentlyInvulnerable(true);
                    f.p.hurtServer(f.p.level(),f.p.damageSources().generic(),1);
                    check(h,WeaponUnrelenting.active(f.p),"Denied damage attempt does not stop regen");
                    f.p.setPermanentlyInvulnerable(false);f.p.damageCooldownTime=0;
                    float before=f.p.getHealth();f.p.hurtServer(f.p.level(),f.p.damageSources().generic(),1);
                    check(h,f.p.getHealth()<before&&!WeaponUnrelenting.active(f.p),"Actual hurtServer loss interrupts through product damage callback");
                    float stopped=f.p.getHealth();
                    h.runAfterDelay(3,()->{check(h,f.p.getHealth()==stopped,"No own healing restarts after damage");h.succeed();});
                });
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=65)
    public void actualPaidRocketRetainsSourceAuthorityAfterStowAndStowedEditRevokesOwnRegen(GameTestHelper h) {
        var f=new Fixture(h,"code_duello");h.onEachTick(f::tick);var target=f.target(true,false);
        f.fire();f.stow();
        h.runAfterDelay(12,()->{
            check(h,!target.isAlive()&&f.p.getHealth()>4&&WeaponUnrelenting.active(f.p),"Actual paid in-flight rocket final blow retains original stowed source");
            f.p.addEffect(new MobEffectInstance(MobEffects.REGENERATION,200,0));
            var foreign=f.p.getEffect(MobEffects.REGENERATION);
            WeaponPerks.clear(f.gun);
            check(h,!WeaponUnrelenting.active(f.p),"Real stowed source socket edit immediately revokes own regen");
            check(h,f.p.getEffect(MobEffects.REGENERATION)==foreign,"Unrelenting cleanup preserves unrelated vanilla regeneration");
            h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=65)
    public void realPoweredGoldtuskFinalBlowStartsRegenAndCountOneOriginalReplacementRevokesIt(GameTestHelper h) {
        var f=new Fixture(h,"goldtusk");h.onEachTick(f::tick);var target=f.target(true,true);
        f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);WeaponRuntime.onPunch(f.p);
        h.runAfterDelay(12,()->{
            check(h,!target.isAlive()&&WeaponUnrelenting.active(f.p)&&f.p.getHealth()>4,"Actual paid powered-sword final blow activates own healing");
            var original=f.gun;f.p.getInventory().setItem(f.slot,original.copy());
            check(h,!WeaponUnrelenting.active(f.p),"Equal component copy cannot retain original identity authority");
            WeaponUnrelenting.update(f.p);f.p.getInventory().setItem(f.slot,original);
            check(h,!WeaponUnrelenting.active(f.p),"Reinserting removed original cannot revive old epoch");
            h.succeed();
        });
    }
}
