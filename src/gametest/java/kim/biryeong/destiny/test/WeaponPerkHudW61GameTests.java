package kim.biryeong.destiny.test;

import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.Map;
import java.util.stream.Collectors;

/** Buff-feed server nodes only, not framebuffer/native evidence. Token calls are explicit HUD fixtures. */
public final class WeaponPerkHudW61GameTests {
    private static final String FLOOR="destiny-test:floor";
    private static void check(GameTestHelper h,boolean ok,String text) { h.assertTrue(ok,Component.literal(text)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2,1,6),0,0);
        var entry=WeaponCatalog.find("duke_mk_44").orElseThrow();
        var gun=WeaponItems.create(entry);WeaponPerks.select(gun,KillClipProfile.ID);
        WeaponItems.save(gun,new WeaponMagazine(WeaponProfile.forEntry(entry),1,0));
        p.setItemInHand(InteractionHand.MAIN_HAND,gun);
        TestCleanup.register(h, ()->{CombatHud.remove(p);WeaponRuntime.cleanup(p);TestPlayers.remove(p);});return p;
    }
    private static ItemDisplayHud node(ServerPlayer p,String suffix) {
        return (ItemDisplayHud)DisplayHud.getHud(p,WeaponPerkHud.PREFIX+suffix);
    }
    private static long count(ServerPlayer p) {
        return DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(WeaponPerkHud.PREFIX)).count();
    }
    private static void activate(GameTestHelper h,ServerPlayer p) {
        WeaponKillClip.killed(p,WeaponKillClip.capture(p));
        check(h,WeaponRuntime.reloadFromMarksmanDodge(p)>0,"HUD fixture uses actual paid magazine transfer after injected kill token");
        check(h,WeaponKillClip.remaining(p)==100,"Exact fresh duration");
    }
    @GameTest(structure=FLOOR,maxTicks=130, environment = "destiny-test:w90_isolated")
    public void actualRemainingDrivesCountdownWithStableCachedDisplayNodesAndNoItemMutation(GameTestHelper h) {
        var p=player(h);activate(h,p);var before=p.getMainHandItem().copy();CombatHud.update(p);
        check(h,count(p)==6,"Six bounded pack-backed buff feed nodes");
        check(h,node(p,"label").getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/perk_kill_clip_w61"),"Original raster label, not debug text");
        check(h,node(p,"ones").getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/ammo_digit_5"),"Five seconds, never premature 4");
        check(h,node(p,"label").getLocation().y()<816&&node(p,"label").getAlignment()==DisplayHud.HudAlignment.LEFT,"Buff feed above ability cluster");
        var nodes=DisplayHud.getHuds(p).entrySet().stream().filter(e->e.getKey().startsWith(WeaponPerkHud.PREFIX))
                .collect(Collectors.toMap(Map.Entry::getKey,e->(ItemDisplayHud)e.getValue()));
        // getItem() intentionally returns a defensive copy; inspect the actual native display stack.
        var stacks=nodes.entrySet().stream().collect(Collectors.toMap(Map.Entry::getKey,e->e.getValue().getItemDisplay().getItemStack()));
        for(int i=0;i<20;i++)CombatHud.update(p);
        for(var e:nodes.entrySet())check(h,DisplayHud.getHud(p,e.getKey())==e.getValue()&&e.getValue().getItemDisplay().getItemStack()==stacks.get(e.getKey()),"Unchanged HUD reads do not replace native display items");
        check(h,ItemStack.matches(before,p.getMainHandItem())&&WeaponKillClip.remaining(p)==100,"Queries alter neither gameplay duration nor ammo/components");
        h.runAfterDelay(20,()->{
            CombatHud.update(p);check(h,WeaponKillClip.remaining(p)==80,"Authoritative duration elapsed");
            check(h,node(p,"ones").getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/ammo_digit_4"),"Countdown uses actual remaining ticks");
            for(var e:nodes.entrySet())check(h,DisplayHud.getHud(p,e.getKey())==e.getValue(),"Countdown reuses entity identity");
        });
        h.runAfterDelay(100,()->{CombatHud.update(p);check(h,count(p)==0&&WeaponKillClip.remaining(p)==0,"No stale 0:00 row at expiry");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=40, environment = "destiny-test:w90_isolated")
    public void readsDoNotInventKillsOrReloadsAndPendingKillIsNotAnActiveBuff(GameTestHelper h) {
        var p=player(h);var before=p.getMainHandItem().copy();
        for(int i=0;i<20;i++){CombatHud.update(p);WeaponPerkHud.update(p);}
        check(h,count(p)==0&&ItemStack.matches(before,p.getMainHandItem()),"Selected perk alone is not a buff");
        WeaponKillClip.killed(p,WeaponKillClip.capture(p));CombatHud.update(p);
        check(h,count(p)==0&&WeaponKillClip.remaining(p)==0,"Kill without successful reload has no label");
        WeaponRuntime.reloadFromMarksmanDodge(p);CombatHud.update(p);check(h,count(p)==6,"Successful reload creates row");
        WeaponPerks.clear(p.getMainHandItem());CombatHud.update(p);check(h,count(p)==0,"Removed trait hides stale row immediately");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=40, environment = "destiny-test:w90_isolated")
    public void stowSpectatorDeathAndExplicitCleanupRemoveAllPerkNodesPerOwner(GameTestHelper h) {
        var p=player(h);var other=player(h);activate(h,p);activate(h,other);CombatHud.update(p);CombatHud.update(other);
        var gun=p.getMainHandItem();p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));CombatHud.update(p);
        check(h,p.getMainHandItem()==gun&&count(p)==0&&count(other)==6,"Same-tick native handler stow removes only owner row");
        other.setGameMode(GameType.SPECTATOR);CombatHud.update(other);check(h,count(other)==0,"Spectator clears row");
        var dead=player(h);activate(h,dead);CombatHud.update(dead);dead.setHealth(0);CombatHud.update(dead);
        check(h,count(dead)==0,"Death clears row");
        var clean=player(h);activate(h,clean);CombatHud.update(clean);CombatHud.remove(clean);
        check(h,count(clean)==0,"Explicit HUD teardown clears feed");h.succeed();
    }
}
