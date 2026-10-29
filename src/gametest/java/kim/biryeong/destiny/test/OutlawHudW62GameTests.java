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
import net.minecraft.world.phys.Vec3;

/** Explicit injected kill-token HUD fixtures; actual precision-kill gameplay is covered separately. */
public final class OutlawHudW62GameTests {
    private static final String FLOOR="destiny-test:floor";
    private static void check(GameTestHelper h,boolean ok,String text) { h.assertTrue(ok,Component.literal(text)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2,1,6),0,0);
        var dual=OutlawProfile.rolls().stream().filter(a->KillClipProfile.rolls().stream().anyMatch(b->a.id().equals(b.id())&&a.socket()!=b.socket())).findFirst().orElseThrow();
        var entry=WeaponCatalog.find(dual.id()).orElseThrow();var gun=WeaponItems.create(entry);var profile=WeaponProfile.forEntry(entry);
        check(h,WeaponPerks.select(gun,OutlawProfile.ID)&&WeaponPerks.select(gun,KillClipProfile.ID),"Independent exact official sockets");
        WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine()-1,Math.max(1,profile.reserve())));
        p.setItemInHand(InteractionHand.MAIN_HAND,gun);
        TestCleanup.register(h, ()->{CombatHud.remove(p);WeaponRuntime.cleanup(p);TestPlayers.remove(p);});return p;
    }
    private static ItemDisplayHud node(ServerPlayer p,String name) {return (ItemDisplayHud)DisplayHud.getHud(p,WeaponPerkHud.PREFIX+name);}
    private static long count(ServerPlayer p) {return DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(WeaponPerkHud.PREFIX)).count();}
    private static void outlaw(ServerPlayer p) {WeaponOutlaw.killed(p,WeaponOutlaw.capture(p),true);}
    private static void both(GameTestHelper h,ServerPlayer p) {
        outlaw(p);WeaponKillClip.killed(p,WeaponKillClip.capture(p));
        check(h,WeaponRuntime.reloadFromMarksmanDodge(p)==1,"HUD fixture pays actual missing cartridge");
    }
    @GameTest(structure=FLOOR,maxTicks=150, environment = "destiny-test:w90_isolated")
    public void simultaneousBuffsHaveIndependentCountdownAndReuseOutlawEntityWhenOtherRowExpires(GameTestHelper h) {
        var p=player(h);both(h,p);CombatHud.update(p);
        check(h,count(p)==12&&WeaponOutlaw.remaining(p)==120&&WeaponKillClip.remaining(p)==100,"Two real-duration rows, bounded12nodes");
        var label=node(p,"outlaw_label");int id=label.getEntityId();
        check(h,label.getLocation().y()==746&&node(p,"label").getLocation().y()==778,"Rows do not overlap");
        check(h,label.getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/perk_outlaw_w62")
                &&node(p,"outlaw_ones").getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/ammo_digit_6"),"Original label and actual0:06");
        var item=label.getItemDisplay().getItemStack();var before=p.getMainHandItem().copy();
        for(int i=0;i<30;i++)CombatHud.update(p);
        check(h,label.getItemDisplay().getItemStack()==item&&ItemStack.matches(before,p.getMainHandItem())
                &&WeaponOutlaw.remaining(p)==120,"Cached reads mutate neither native display item nor gameplay");
        h.runAfterDelay(100,()->{
            CombatHud.update(p);check(h,count(p)==6&&WeaponKillClip.remaining(p)==0&&WeaponOutlaw.remaining(p)==20,"Only expired KC row removed");
            check(h,node(p,"outlaw_label")==label&&label.getEntityId()==id&&label.getLocation().y()==778,"Remaining row shifts without respawn");
            check(h,node(p,"outlaw_ones").getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/ammo_digit_1"),"Actual0:01, not restart0:06");
        });
        h.runAfterDelay(120,()->{CombatHud.update(p);check(h,count(p)==0&&WeaponOutlaw.remaining(p)==0,"No lingering0:00 or restarted row");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=40, environment = "destiny-test:w90_isolated")
    public void singleOutlawBuffIsVisibleForNonGuardiansButSelectionAloneNeverCreatesARow(GameTestHelper h) {
        var p=player(h);CombatHud.update(p);var before=p.getMainHandItem().copy();
        check(h,count(p)==0&&WeaponOutlaw.remaining(p)==0,"Selected official trait alone grants nothing");
        outlaw(p);CombatHud.update(p);
        check(h,count(p)==6&&node(p,"outlaw_label").getLocation().y()==778,"Non-Guardian buff survives removeAbilities and uses bottom row");
        WeaponPerkHud.update(p);check(h,ItemStack.matches(before,p.getMainHandItem())&&WeaponKillClip.remaining(p)==0,"No counterfeit reload/KC activation from HUD");
        CombatHud.remove(p);check(h,count(p)==0,"Explicit teardown clears both row namespaces");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=40, environment = "destiny-test:w90_isolated")
    public void sameTickStowOrTraitClearRemovesBothRowsWithoutTouchingAnotherOwner(GameTestHelper h) {
        var p=player(h);var other=player(h);both(h,p);both(h,other);CombatHud.update(p);CombatHud.update(other);
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));CombatHud.update(p);
        check(h,count(p)==0&&count(other)==12,"Same-tick native slot handler resets only original owner");
        var gun=other.getMainHandItem();var profile=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());var rounds=WeaponItems.magazine(gun,profile).total();
        WeaponPerks.clear(gun);CombatHud.update(other);
        check(h,count(other)==0&&WeaponItems.magazine(gun,profile).total()==rounds,"Clearing traits removes stale rows without ammo mutation");h.succeed();
    }
}
