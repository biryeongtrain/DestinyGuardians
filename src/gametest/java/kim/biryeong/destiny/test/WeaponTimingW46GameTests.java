package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

public final class WeaponTimingW46GameTests {
    private static void check(GameTestHelper h,boolean ok,String text){h.assertTrue(ok,Component.literal(text));}
    private static ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});return p;
    }
    private static ItemStack equip(ServerPlayer p,String id,int rounds,int reserve) {
        var e=WeaponCatalog.find(id).orElseThrow();var stack=WeaponItems.create(e);
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,reserve));
        p.setItemInHand(InteractionHand.MAIN_HAND,stack);return stack;
    }
    private static WeaponProfile profile(String id){return WeaponProfile.forEntry(WeaponCatalog.find(id).orElseThrow());}
    private static WeaponMagazine ammo(ItemStack s){return WeaponItems.magazine(s,WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow()));}
    private static Husk target(GameTestHelper h){
        var e=h.spawn(EntityTypes.HUSK,new Vec3(7.5,1.8,6.5));e.setNoAi(true);e.setNoGravity(true);
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);e.setHealth(1000);TestCleanup.register(h, e::discard);return e;
    }

    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void all63LiveStacksAndHudUseOfficialBaseCapacityWithoutRefillingSavedRounds(GameTestHelper h){
        var p=player(h);
        for(var e:WeaponCatalog.all()){
            var f=WeaponProfile.forEntry(e);var stats=WeaponCharacteristics.of(e).stats();
            int capacity=e.family().equals("bow")?1:stats.get("3871231066");
            check(h,f.magazine()==capacity,"Exact pinned base capacity: "+e.id());
            var stack=WeaponItems.create(e);p.setItemInHand(InteractionHand.MAIN_HAND,stack);
            CombatHud.update(p);var before=stack.copy();
            var hud=AmmoHud.current(p).orElseThrow();
            check(h,hud.rounds()==capacity&&hud.capacity()==capacity,"Live HUD uses actual capacity: "+e.id());
            CombatHud.update(p);check(h,ItemStack.matches(before,stack),"HUD is read-only: "+e.id());
            WeaponItems.save(stack,new WeaponMagazine(f,1,0));
            check(h,AmmoHud.current(p).orElseThrow().rounds()==1,"New capacity never invents missing saved rounds");
        }
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor",maxTicks=60, environment = "destiny-test:w90_isolated")
    public void stormchaserLastOneAmmoCompletesThreeRealHitsAfterHeartbeatRelease(GameTestHelper h){
        var p=player(h);var t=target(h);var stack=equip(p,"stormchaser",1,0);var f=profile("stormchaser");
        check(h,f.sharedBurstAmmo()&&f.burst()==3,"Three bolts, one charge ammunition");
        WeaponRuntime.heartbeatUse(p);
        for(int i=1;i<=f.chargeTicks()+12;i++){
            int tick=i;
            h.runAfterDelay(i,()->{
                if(tick<f.chargeTicks()&&tick%4==0)WeaponRuntime.heartbeatUse(p);
                WeaponRuntime.tickPlayer(p);
            });
        }
        h.runAfterDelay(f.chargeTicks()+13,()->{
            check(h,ammo(stack).rounds()==0&&ammo(stack).reserve()==0,"Only one unit consumed");
            check(h,Math.abs((1000-t.getHealth())-3*f.damage())<.01,"All three queued body hits survive input release");
            check(h,!WeaponRuntime.reloading(p),"No free refill on last unit");
            CombatHud.update(p);check(h,AmmoHud.current(p).orElseThrow().rounds()==0,"HUD shows empty only once");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=100, environment = "destiny-test:w90_isolated")
    public void sharedBurstSkillCancellationNeverCreatesRefundOrLaterBolts(GameTestHelper h){
        var p=player(h);var t=target(h);var stack=equip(p,"stormchaser",1,0);var f=profile("stormchaser");
        WeaponRuntime.heartbeatUse(p);
        for(int i=1;i<=f.chargeTicks();i++){
            int tick=i;h.runAfterDelay(i,()->{if(tick%4==0)WeaponRuntime.heartbeatUse(p);WeaponRuntime.tickPlayer(p);});
        }
        h.runAfterDelay(f.chargeTicks()+1,()->{
            check(h,ammo(stack).rounds()==0,"First bolt spent its one unit");WeaponRuntime.cancelUseForSkill(p);
        });
        h.runAfterDelay(f.chargeTicks()+15,()->{
            check(h,ammo(stack).rounds()==0,"Cancelling a burst cannot refund its trigger");
            check(h,Math.abs((1000-t.getHealth())-f.damage())<.01,"Skill cancellation stops unexecuted later bolts");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=150, environment = "destiny-test:w90_isolated")
    public void shellInsertUpdatesActualHudThenSwapCancelsWithoutSpendingAnotherReserve(GameTestHelper h){
        var p=player(h);var stack=equip(p,"dust_rock_blues",0,3);var f=profile("dust_rock_blues");
        check(h,f.shellReload(),"Shotgun owns shell reload policy");check(h,WeaponRuntime.reload(p),"Reload starts");
        for(int i=1;i<=f.reloadTicks()+1;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(f.reloadTicks()+2,()->{
            check(h,ammo(stack).rounds()==1&&ammo(stack).reserve()==2,"Only first actual shell transferred");
            CombatHud.update(p);check(h,AmmoHud.current(p).orElseThrow().rounds()==1&&WeaponRuntime.reloading(p),"HUD follows each insert");
            p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);WeaponRuntime.tickPlayer(p);
            p.setItemInHand(InteractionHand.MAIN_HAND,stack);
        });
        h.runAfterDelay(f.reloadTicks()*3+4,()->{
            WeaponRuntime.tickPlayer(p);check(h,ammo(stack).rounds()==1&&ammo(stack).reserve()==2,"Cancelled future inserts spend nothing");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=150, environment = "destiny-test:w90_isolated")
    public void heldEmptyTriggerCannotAutoInterruptShellReloadButFreshPressCan(GameTestHelper h){
        var p=player(h);var stack=equip(p,"dust_rock_blues",0,3);var f=profile("dust_rock_blues");
        WeaponRuntime.heartbeatUse(p);
        for(int i=1;i<=f.reloadTicks();i++){
            int tick=i;h.runAfterDelay(i,()->{if(tick%4==0)WeaponRuntime.heartbeatUse(p);WeaponRuntime.tickPlayer(p);});
        }
        h.runAfterDelay(f.reloadTicks()+1,()->{
            check(h,ammo(stack).rounds()==1&&ammo(stack).reserve()==2&&WeaponRuntime.reloading(p),"Held empty trigger never fires its newly inserted shell");
        });
        h.runAfterDelay(f.reloadTicks()+8,()->{
            check(h,WeaponRuntime.heartbeatUse(p),"New press after release interrupts shell reload");
            check(h,ammo(stack).rounds()==0&&ammo(stack).reserve()==2&&!WeaponRuntime.reloading(p),"Interrupted shot uses the inserted unit, no reserve refund");h.succeed();
        });
    }
}
