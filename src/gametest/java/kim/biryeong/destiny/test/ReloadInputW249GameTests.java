package kim.biryeong.destiny.test;

import kim.biryeong.destiny.inventory.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.*;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.world.item.*;
import net.minecraft.world.item.crafting.display.RecipeDisplayId;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real server handlers and encoded clientbound bytes; not native-key or framebuffer evidence. */
public final class ReloadInputW249GameTests {
    private static void check(GameTestHelper h, boolean ok, String why) { h.assertTrue(ok, Component.literal(why)); }
    private static InventoryWireW92 wire(GameTestHelper h, String id, boolean full) {
        var w = new InventoryWireW92(h, new Vec3(5,4,5));
        var p=w.player; p.setAttached(WeaponLoadout.ENABLED, false);
        var e=WeaponCatalog.find(id).orElseThrow(); var item=WeaponItems.create(e);
        var profile=WeaponProfile.forEntry(e);
        WeaponItems.save(item,new WeaponMagazine(profile,full?profile.magazine():1,80));
        p.getInventory().setSelectedSlot(4);p.getInventory().setItem(4,item);
        p.getInventory().setItem(5,new ItemStack(Items.DIAMOND,3));
        WeaponRuntime.tickPlayer(p);w.full();w.discard();return w;
    }
    private static void action(InventoryWireW92 w, boolean all, boolean shift) {
        w.player.setShiftKeyDown(shift);
        w.player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(all?
                ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS:ServerboundPlayerActionPacket.Action.DROP_ITEM,
                BlockPos.ZERO,Direction.UP));
    }
    private static void restored(GameTestHelper h, InventoryWireW92 w, ItemStack source) {
        var packets=w.capture();
        int slot=w.player.inventoryMenu.findSlot(w.player.getInventory(),4).orElseThrow();
        var updates=packets.stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast).filter(x->x.getSlot()==slot).toList();
        check(h,!updates.isEmpty(),"Cancelled client prediction receives explicit selected-slot repair");
        var item=updates.getLast().getItem();
        check(h,!item.isEmpty()&&item.getCount()==1&&!item.is(WeaponCombatItem.INSTANCE)
                &&item.has(DataComponents.ITEM_MODEL),"Wire repair contains projected vanilla weapon, not an empty stack");
        check(h,w.player.getMainHandItem()==source&&w.player.getInventory().getItem(5).getCount()==3,
                "Repair preserves authoritative stack identity and adjacent inventory");
    }
    @GameTest(structure="destiny-test:w78_floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void fullMagazineAndNoReserveRejectionsRepairPredictedDrop(GameTestHelper h) {
        var w=wire(h,"ace_of_spades",true);var item=w.player.getMainHandItem();var before=item.copy();
        action(w,false,false);check(h,!WeaponRuntime.reloading(w.player),"Full magazine rejects reload");restored(h,w,item);
        check(h,ItemStack.matches(item,before),"Full-mag rejection changes no components or ammo");
        w=wire(h,"izanagis_burden",false);item=w.player.getMainHandItem();
        var profile=WeaponProfile.forEntry(WeaponItems.entry(item).orElseThrow());
        WeaponItems.save(item,new WeaponMagazine(profile,0,0));w.full();w.discard();
        action(w,true,true);check(h,!WeaponRuntime.reloading(w.player)&&!WeaponScreen.active(w.player),"Empty reserve ShiftQ rejects without opening menu");
        restored(h,w,item);h.succeed();
    }
    @GameTest(structure="destiny-test:w78_floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void shiftQReloadsAndRepeatedReloadStillRepairs(GameTestHelper h) {
        var w=wire(h,"ace_of_spades",false);var item=w.player.getMainHandItem();
        action(w,false,true);check(h,WeaponRuntime.reloading(w.player)&&!WeaponScreen.active(w.player),"ShiftQ starts reload instead of equipment screen");restored(h,w,item);
        action(w,false,false);check(h,WeaponRuntime.reloading(w.player),"Repeated Q keeps reload");restored(h,w,item);h.succeed();
    }
    @GameTest(structure="destiny-test:w78_floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void izanagiShiftQAndCtrlQBothHone(GameTestHelper h) {
        var a=wire(h,"izanagis_burden",true);action(a,false,true);
        check(h,WeaponRuntime.reloading(a.player)&&WeaponIzanagi.honing(a.player)&&!WeaponScreen.active(a.player),"Izanagi ShiftQ hones");restored(h,a,a.player.getMainHandItem());
        var b=wire(h,"izanagis_burden",true);action(b,true,false);
        check(h,WeaponRuntime.reloading(b.player)&&WeaponIzanagi.honing(b.player),"Existing CtrlQ honing remains supported");restored(h,b,b.player.getMainHandItem());h.succeed();
    }
    @GameTest(structure="destiny-test:w78_floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void menuQStaysOpenAndRepairsHiddenCarrier(GameTestHelper h) {
        var w=wire(h,"ace_of_spades",true);check(h,WeaponScreen.open(w.player),"Open menu fixture");
        TestCleanup.register(h,()->WeaponScreen.close(w.player));w.discard();action(w,false,false);
        check(h,WeaponScreen.active(w.player)&&!WeaponRuntime.reloading(w.player),"Q neither closes screen nor starts a reload inside menu");
        int slot=w.player.inventoryMenu.findSlot(w.player.getInventory(),4).orElseThrow();
        check(h,w.capture().stream().filter(ClientboundContainerSetSlotPacket.class::isInstance).map(ClientboundContainerSetSlotPacket.class::cast)
            .anyMatch(x->x.getSlot()==slot),"Even a menu-suppressed drop repairs predicted hotbar slot");h.succeed();
    }
    @GameTest(structure="destiny-test:w78_floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void recipeGenerationTogglesOnceAndDoesNotUnlockRealRecipe(GameTestHelper h) {
        var w=wire(h,"ace_of_spades",true);var p=w.player;
        TestCleanup.register(h,()->WeaponScreen.close(p));
        var settings=p.getRecipeBook().getBookSettings().copy();
        var recipe=net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.RECIPE,net.minecraft.resources.Identifier.withDefaultNamespace("crafting_table"));
        boolean unlocked=p.getRecipeBook().contains(recipe);
        p.connection.handleContainerClose(new ServerboundContainerClosePacket(p.inventoryMenu.containerId));
        var added=w.capture().stream().filter(ClientboundRecipeBookAddPacket.class::isInstance).map(ClientboundRecipeBookAddPacket.class::cast).toList();
        check(h,added.size()==1&&added.getFirst().replace(),"Native close replaces client book with page-one beacons");
        var ids=added.getFirst().entries().stream().map(x->x.contents().id()).toList();
        check(h,ids.size()==4&&ids.stream().distinct().count()==4,"Four crafting tabs have distinct synthetic displays");
        p.connection.handleRecipeBookSeenRecipePacket(new ServerboundRecipeBookSeenRecipePacket(ids.getFirst()));
        check(h,WeaponScreen.active(p),"Seen recipe opens custom menu");
        var generated=w.capture().stream().filter(ClientboundRecipeBookAddPacket.class::isInstance).map(ClientboundRecipeBookAddPacket.class::cast).toList();
        var next=generated.stream().filter(x->x.entries().stream().anyMatch(e->e.contents().id().index()>=0x3f000000)).reduce((a,b)->b).orElseThrow();
        for(var id:ids)p.connection.handleRecipeBookSeenRecipePacket(new ServerboundRecipeBookSeenRecipePacket(id));
        check(h,WeaponScreen.active(p),"Queued stale/duplicate seen packets cannot close newly opened screen");
        p.connection.handleRecipeBookSeenRecipePacket(new ServerboundRecipeBookSeenRecipePacket(next.entries().getFirst().contents().id()));
        check(h,!WeaponScreen.active(p),"Next inventory generation closes custom menu; old="+ids+" new="+next.entries().stream().map(e->e.contents().id()).toList());
        for(var type:net.minecraft.world.inventory.RecipeBookType.values())
            check(h,p.getRecipeBook().getBookSettings().isOpen(type)==settings.isOpen(type)
                &&p.getRecipeBook().getBookSettings().isFiltering(type)==settings.isFiltering(type),"Server recipe settings remain unchanged for "+type);
        check(h,p.getRecipeBook().contains(recipe)==unlocked,"Client beacon never unlocks crafting_table");
        p.level().getServer().getCommands().performPrefixedCommand(p.createCommandSourceStack(),"메뉴");
        check(h,WeaponScreen.active(p),"Korean menu command opens without operator permission");
        p.level().getServer().getCommands().performPrefixedCommand(p.createCommandSourceStack(),"메뉴");
        check(h,!WeaponScreen.active(p),"Korean menu command also closes");
        check(h,!InventoryMenuRedirect.seen(p,new RecipeDisplayId(0)),"Ordinary recipe packet keeps vanilla behavior");
        p.getRecipeBook().remove(recipe); w.discard();
        p.getRecipeBook().addRecipes(List.of(p.level().getServer().getRecipeManager().byKey(recipe).orElseThrow()),p);
        var unlock=w.capture().stream().filter(ClientboundRecipeBookAddPacket.class::isInstance).map(ClientboundRecipeBookAddPacket.class::cast).toList();
        var finalBook=unlock.getLast();
        check(h,finalBook.replace()&&finalBook.entries().size()==4&&finalBook.entries().stream().allMatch(e->e.contents().id().index()>=0x3f000000),"Real recipe unlock keeps all four beacons on first page");
        w.discard();
        p.openMenu(new net.minecraft.world.SimpleMenuProvider((id,inv,who)->new net.minecraft.world.inventory.CraftingMenu(id,inv),Component.literal("W249 crafting")));
        var restored=w.capture().stream().filter(ClientboundRecipeBookAddPacket.class::isInstance).map(ClientboundRecipeBookAddPacket.class::cast).toList();
        check(h,restored.stream().anyMatch(x->x.replace()&&x.entries().stream().noneMatch(e->e.contents().id().index()>=0x3f000000)),"Opening real crafting table restores the authoritative recipe book");
        check(h,!WeaponScreen.active(p),"External crafting never opens equipment HUD");
        p.connection.handleContainerClose(new ServerboundContainerClosePacket(p.containerMenu.containerId));w.discard();
        var denied=p.openMenu(new net.minecraft.world.SimpleMenuProvider((id,inv,who)->null,Component.literal("W249 locked")));
        check(h,denied.isEmpty(),"Rejected external provider opens no native menu");
        var rearmed=w.capture().stream().filter(ClientboundRecipeBookAddPacket.class::isInstance).map(ClientboundRecipeBookAddPacket.class::cast).filter(ClientboundRecipeBookAddPacket::replace).reduce((a,b)->b).orElseThrow();
        p.connection.handleRecipeBookSeenRecipePacket(new ServerboundRecipeBookSeenRecipePacket(rearmed.entries().getFirst().contents().id()));
        check(h,WeaponScreen.active(p),"E detection survives an external menu-open failure");h.succeed();
    }
    @GameTest(structure="destiny-test:w78_floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void vanillaNonweaponStillDrops(GameTestHelper h) {
        var w=wire(h,"ace_of_spades",true);w.player.getInventory().setItem(4,new ItemStack(Items.DIRT,3));w.full();w.discard();
        action(w,false,false);check(h,w.player.getMainHandItem().getCount()==2,"Normal vanilla item still drops once");h.succeed();
    }
}
