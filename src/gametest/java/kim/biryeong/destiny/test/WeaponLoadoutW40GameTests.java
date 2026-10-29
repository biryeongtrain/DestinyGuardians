package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.minigamelib.displayhud.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.Vec3;

public final class WeaponLoadoutW40GameTests {
    private static void check(GameTestHelper h,boolean ok,String message) { h.assertTrue(ok,Component.literal(message)); }
    private ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2,1,6),0,0);
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p);TestPlayers.remove(p);});
        return p;
    }
    private ItemStack item(String id,int rounds,int reserve) {
        var e=WeaponCatalog.find(id).orElseThrow();var stack=WeaponItems.create(e);
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,reserve));return stack;
    }
    private ItemStack equip(GameTestHelper h,ServerPlayer p,String id,int rounds,int reserve) {
        var stack=item(id,rounds,reserve);p.getInventory().setItem(4,stack);p.getInventory().setSelectedSlot(4);
        check(h,WeaponLoadout.equipHeld(p)==null,"Equip actual owned "+id);return stack;
    }
    private ItemDisplayHud hud(ServerPlayer p,String id) { return (ItemDisplayHud)DisplayHud.getHud(p,AmmoHud.PREFIX+id); }
    private String model(ServerPlayer p,String id) { return hud(p,id).getItem().get(DataComponents.ITEM_MODEL).toString(); }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void nonOpOwnedEquipMovesItemsWithoutMintingAndSendsCanonicalSelection(GameTestHelper h) throws Exception {
        var p=player(h);var owned=item("austringer",7,0);p.getInventory().setItem(4,owned);p.getInventory().setSelectedSlot(4);
        TestPlayers.drain(p);
        int result=h.getLevel().getServer().getCommands().getDispatcher().execute("destiny loadout equip",p.createCommandSourceStack());
        check(h,result==1&&WeaponLoadout.enabled(p),"Ordinary player can equip owned weapon, no OP spawn");
        check(h,p.getInventory().getSelectedSlot()==0&&p.getMainHandItem()==owned&&p.getInventory().getItem(4).isEmpty(),"Original reference moved exactly once");
        check(h,TestPlayers.outbound(p).stream().anyMatch(packet->packet instanceof ClientboundSetHeldSlotPacket),"Real selected-slot packet sent");
        check(h,WeaponItems.magazine(owned,WeaponProfile.forEntry(WeaponItems.entry(owned).orElseThrow())).rounds()==7,"Existing magazine preserved");
        check(h,WeaponLoadout.equipped(p).size()==1,"Only actual owned slot appears");
        check(h,!WeaponLoadout.select(p,WeaponSlot.POWER),"Empty slot cannot be selected by UI command");
        check(h,WeaponLoadout.select(p,WeaponSlot.KINETIC),"Owned selection succeeds without item mutation");
        CombatHud.update(p);check(h,hud(p,"stowed_0_panel")==null,"No fabricated empty secondary rows");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void threeActualSlotsDriveMainAndTwoStowedRowsAndNativeSlotPacketSwitch(GameTestHelper h) {
        var p=player(h);equip(h,p,"austringer",7,0);equip(h,p,"nezarec_s_whisper",2,3);equip(h,p,"bad_omens",1,6);
        CombatHud.update(p);
        check(h,WeaponLoadout.equipped(p).size()==3,"Three different real bucket weapons");
        check(h,model(p,"weapon").endsWith("/ammo_weapon_w112_bad_omens"),"Selected power weapon");
        check(h,hud(p,"stowed_0_infinity")!=null,"Actual primary infinite total");
        check(h,model(p,"stowed_1_total_0").endsWith("/ammo_digit_5"),"Stowed special total=2+3");
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));WeaponRuntime.tickPlayer(p);CombatHud.update(p);
        check(h,p.getMainHandItem()==p.getInventory().getItem(1)&&WeaponLoadout.canUse(p),"Vanilla slot packet selects energy weapon");
        check(h,model(p,"weapon").endsWith("/ammo_weapon_w112_nezarec_s_whisper"),"Current row updates to real selected weapon");
        check(h,model(p,"damage").endsWith("/ammo_damage_arc"),"Actual item damage glyph, not guessed by ammo");
        check(h,model(p,"stowed_1_total_0").endsWith("/ammo_digit_7"),"Stowed rocket total=1+6");
        check(h,hud(p,"ammo_type").getItem().get(DataComponents.CUSTOM_MODEL_DATA).getColor(0)==WeaponAmmoType.SPECIAL.color(),"Special green, independent of Arc");
        check(h,DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(AmmoHud.PREFIX)&&!k.startsWith(AmmoHud.PREFIX+"glaive_")&&!k.startsWith(kim.biryeong.destiny.hud.AmmoMeterHud.PREFIX)).count()<=26,"Three rows stay within bounded node budget; new meter nodes have their own six-node assertion");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void fullDestinationProtectsOrdinaryItemsAndSwapPreservesBothMagazines(GameTestHelper h) {
        var p=player(h);var diamond=new ItemStack(Items.DIAMOND,3);
        p.getInventory().setItem(1,diamond);var glaive=item("nezarec_s_whisper",2,3);
        p.getInventory().setItem(4,glaive);p.getInventory().setSelectedSlot(4);
        check(h,WeaponLoadout.equipHeld(p)!=null,"Occupied ordinary item blocks transaction");
        check(h,p.getInventory().getItem(1)==diamond&&p.getInventory().getItem(4)==glaive&&!WeaponLoadout.enabled(p),"No state or inventory mutation on error");
        p.getInventory().setItem(1,ItemStack.EMPTY);
        var old=equip(h,p,"austringer",7,0);var replacement=item("duke_mk_44",3,0);
        p.getInventory().setItem(4,replacement);p.getInventory().setSelectedSlot(4);
        check(h,WeaponLoadout.equipHeld(p)==null,"Replacing same bucket swaps actual references");
        check(h,p.getInventory().getItem(0)==replacement&&p.getInventory().getItem(4)==old,"Old weapon preserved in source storage slot");
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(4));
        check(h,!WeaponRuntime.beginUse(p),"Carried backup outside equipped buckets cannot bypass three-slot loadout");
        check(h,WeaponItems.magazine(old,WeaponProfile.forEntry(WeaponItems.entry(old).orElseThrow())).rounds()==7,"Blocked extra gun consumes nothing");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor",maxTicks=110, environment = "destiny-test:w90_isolated")
    public void nativeSlotChangeCancelsSpecialReloadWithoutTouchingEitherReserve(GameTestHelper h) {
        var p=player(h);var special=equip(h,p,"nezarec_s_whisper",2,3);var primary=equip(h,p,"austringer",7,0);
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
        check(h,!WeaponRuntime.reload(p),"W58: reload denied during actual ready transition");
        h.runAfterDelay(WeaponHandling.remaining(p),()->{
            check(h,WeaponRuntime.reload(p),"Start finite special reload after readying");
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));WeaponRuntime.tickPlayer(p);
            h.runAfterDelay(48,()->{
                p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));WeaponRuntime.tickPlayer(p);CombatHud.update(p);
                check(h,AmmoHud.current(p).orElseThrow().rounds()==2&&AmmoHud.current(p).orElseThrow().reserve()==3,"Cancelled finite reload cannot complete in stowed slot");
                check(h,WeaponItems.magazine(primary,WeaponProfile.forEntry(WeaponItems.entry(primary).orElseThrow())).rounds()==7,"Other weapon unchanged");
                h.succeed();
            });
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=60, environment = "destiny-test:w90_isolated")
    public void emptyPrimaryRefillsOnlyAtServerDeadlineEvenWithZeroSavedReserve(GameTestHelper h) {
        var p=player(h);equip(h,p,"austringer",0,0);
        check(h,!WeaponRuntime.beginUse(p)&&WeaponRuntime.reloading(p),"Empty primary trigger starts actual reload");
        CombatHud.update(p);check(h,hud(p,"infinity")!=null&&hud(p,"reserve_0")==null,"Honest infinite policy, not fake reserve digits");
        var profile=WeaponProfile.forEntry(WeaponCatalog.find("austringer").orElseThrow());
        h.runAfterDelay(37,()->{WeaponRuntime.tickPlayer(p);check(h,AmmoHud.current(p).orElseThrow().rounds()==0,"No magazine refill before explicit Austringer credit38");});
        h.runAfterDelay(38,()->{WeaponRuntime.tickPlayer(p);check(h,AmmoHud.current(p).orElseThrow().rounds()==profile.magazine()&&WeaponRuntime.reloading(p),"Credit38 fills Primary while recovery53 remains active");});
        h.runAfterDelay(profile.reloadTicks()-1,()->{WeaponRuntime.tickPlayer(p);check(h,AmmoHud.current(p).orElseThrow().rounds()==profile.magazine()&&WeaponRuntime.reloading(p),"Credited ammunition persists through final recovery tick");});
        h.runAfterDelay(profile.reloadTicks()+1,()->{
            WeaponRuntime.tickPlayer(p);CombatHud.update(p);
            check(h,AmmoHud.current(p).orElseThrow().rounds()==profile.magazine()&&!WeaponRuntime.reloading(p),"Deadline produces full primary magazine");
            check(h,AmmoHud.current(p).orElseThrow().reserve()==0,"No fabricated finite reserve data");
            h.succeed();
        });
    }
}
