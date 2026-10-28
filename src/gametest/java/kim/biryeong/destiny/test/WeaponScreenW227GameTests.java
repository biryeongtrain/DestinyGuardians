package kim.biryeong.destiny.test;

import kim.biryeong.destiny.inventory.WeaponScreen;
import kim.biryeong.destiny.inventory.WeaponScreenPresentation;
import net.minecraft.core.component.DataComponents;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.phys.Vec3;

public final class WeaponScreenW227GameTests {
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=30)
    public void equipmentScreenBlocksCombatAndRestoresMovementWithoutInventoryCopies(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, 2.5), 0, 0, "W227_screen");
        p.setOnGround(true); p.setNoGravity(true);
        var entry = WeaponCatalog.find("ammit_ar2").orElseThrow();
        var gun = WeaponItems.create(entry); p.getInventory().setItem(1, gun); p.getInventory().setSelectedSlot(1);
        TestCleanup.register(h, () -> { WeaponScreen.close(p); WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        double speed = p.getAttributeValue(Attributes.MOVEMENT_SPEED), jump = p.getAttributeValue(Attributes.JUMP_STRENGTH);
        int rounds = WeaponItems.magazine(gun, WeaponProfile.forEntry(entry)).rounds();
        h.assertTrue(WeaponScreen.open(p), Component.literal("Equipment opens without a container screen"));
        h.assertTrue(p.containerMenu == p.inventoryMenu && WeaponScreen.active(p), Component.literal("No SGUI or substitute inventory"));
        int menuSlot = java.util.stream.IntStream.range(0, p.inventoryMenu.slots.size())
                .filter(i -> p.inventoryMenu.slots.get(i).container == p.getInventory()
                        && p.inventoryMenu.slots.get(i).getContainerSlot() == 1).findFirst().orElseThrow();
        var originalModel = gun.get(DataComponents.ITEM_MODEL);
        var originalName = gun.get(DataComponents.ITEM_NAME);
        var outgoing = new ClientboundContainerSetSlotPacket(p.inventoryMenu.containerId, 17, menuSlot, gun.copy());
        var projected = (ClientboundContainerSetSlotPacket) WeaponScreenPresentation.project(p, outgoing);
        h.assertTrue(projected != outgoing && !projected.getItem().isEmpty()
                && projected.getItem().getCount() == gun.getCount()
                && kim.biryeong.destiny.DestinyGuardians.id("weapon_sword_hand_empty").equals(projected.getItem().get(DataComponents.ITEM_MODEL))
                && projected.getItem().get(DataComponents.ITEM_NAME).getString().isEmpty()
                && projected.getStateId() == 17 && projected.getSlot() == menuSlot,
                Component.literal("Recipient hotbar carrier hidden without removing native use item"));
        h.assertTrue(java.util.Objects.equals(originalModel, gun.get(DataComponents.ITEM_MODEL))
                && java.util.Objects.equals(originalName, gun.get(DataComponents.ITEM_NAME))
                && java.util.Objects.equals(originalModel, outgoing.getItem().get(DataComponents.ITEM_MODEL)),
                Component.literal("Presentation never mutates source inventory or packet snapshots"));
        var foreign = new ClientboundContainerSetSlotPacket(123, 17, menuSlot, gun.copy());
        h.assertTrue(WeaponScreenPresentation.project(p, foreign) == foreign, Component.literal("Foreign menus preserved"));
        h.assertTrue(!WeaponRuntime.beginUse(p) && !WeaponRuntime.heartbeatUse(p)
                && !InputRouter.dispatch(p, GuardianAction.GRENADE), Component.literal("Use and abilities blocked"));
        p.connection.handlePlayerInput(new ServerboundPlayerInputPacket(new Input(false, false, false, true, false, false, false)));
        h.assertTrue(p.getLastClientInput().equals(Input.EMPTY), Component.literal("Native WASD is routed to screen, not locomotion"));
        p.connection.handlePunch(new ServerboundPunchPacket());
        h.assertTrue(WeaponScreen.active(p) && p.getInventory().getItem(1) == gun
                && WeaponItems.magazine(gun, WeaponProfile.forEntry(entry)).rounds() == rounds,
                Component.literal("Native click cannot fire or copy weapon"));
        WeaponScreen.close(p);
        h.assertTrue(WeaponScreenPresentation.project(p, outgoing) == outgoing, Component.literal("Close restores ordinary item presentation"));
        h.assertTrue(!WeaponScreen.active(p) && p.getAttributeValue(Attributes.MOVEMENT_SPEED) == speed
                && p.getAttributeValue(Attributes.JUMP_STRENGTH) == jump,
                Component.literal("Only owned movement modifiers removed"));
        h.assertTrue(DisplayHud.getHuds(p).keySet().stream().noneMatch(k -> k.startsWith("destiny:equipment_w227_")),
                Component.literal("All owned menu displays retired"));
        h.succeed();
    }
}
