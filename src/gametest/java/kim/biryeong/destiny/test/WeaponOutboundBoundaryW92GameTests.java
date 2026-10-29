package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Trust-boundary/payload tests, NOT outbound-byte or framebuffer proof.
 * Actual encoder/menu integration is separately exercised by the wire suite.
 */
public final class WeaponOutboundBoundaryW92GameTests {
    private static void check(GameTestHelper h, boolean yes, String why) {
        h.assertTrue(yes, Component.literal(why));
    }
    private record Fixture(ServerPlayer player, ItemStack stack, int slot) {}
    private static ServerPlayer player(GameTestHelper h, int z) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, z), 0, 90);
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel()); p.stopUsingItem(); ads(p, false);
            WeaponRuntime.cleanup(p); WeaponPerkHud.remove(p); CombatHud.remove(p); TestPlayers.remove(p);
        });
        p.setNoGravity(true); p.setAttached(WeaponLoadout.ENABLED, false);
        return p;
    }
    private static int slot(ServerPlayer p) {
        for (int i = 0; i < p.inventoryMenu.slots.size(); i++) {
            var s = p.inventoryMenu.slots.get(i);
            if (s.container == p.getInventory() && s.getContainerSlot() == p.getInventory().getSelectedSlot()) return i;
        }
        throw new IllegalStateException("No actual selected inventory slot");
    }
    private static Fixture reload(GameTestHelper h) {
        var p = player(h, 4);
        var e = WeaponCatalog.find("izanagis_burden").orElseThrow();
        var s = WeaponItems.create(e);
        s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(
                List.of(17f, 9f, 8f, -1f, 7f, 6f, 91f, 73f),
                List.of(true, false, true), List.of("hip", "keep"), List.of(0x123456)));
        WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), 1, 5));
        p.getInventory().setItem(0, s); p.getInventory().setSelectedSlot(0); WeaponRuntime.tickPlayer(p);
        check(h, WeaponRuntime.reloadHoned(p) && WeaponIzanagiPresentation.ownedBy(p, s),
                "Real owned Honed transaction, no synthetic charge/binding");
        return new Fixture(p, s, slot(p));
    }
    private static ItemStack project(Fixture f, ItemStack snapshot) {
        return WeaponOutboundPresentation.projectSlot(f.player, f.player.inventoryMenu, f.slot, snapshot);
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated")
    public void exactOriginalRecipientProjectsOnlyPayloadPreservesCanonicalAndRoundtrip(GameTestHelper h) {
        var f = reload(h); var live = f.stack; var before = live.copy(); var snapshot = live.copy();
        var out = project(f, snapshot);
        check(h, out != snapshot && out.is(Items.CROSSBOW)
                && out.get(DataComponents.ITEM_MODEL).equals(projected(WeaponIzanagiPresentation.model(live))),
                "Vetted live original projects W91 model into vanilla two-hand carrier");
        check(h, ItemStack.matches(before, live) && ItemStack.matches(before, snapshot),
                "Authoritative stack and supplied snapshot remain component-exact");
        check(h, !WeaponIzanagiPresentation.active(snapshot) && !WeaponIzanagiPresentation.active(out)
                && WeaponIzanagi.charge(live) == 0, "Transport never grants copied authority or unpaid charge");
        var a = live.get(DataComponents.CUSTOM_MODEL_DATA); var b = out.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, a.floats().equals(b.floats()) && a.strings().equals(b.strings())
                && a.colors().equals(b.colors()) && b.flags().equals(List.of(true)),
                "Selector6/ADS3/pose0/other data preserved; carrier grip remains existing Polymer contract");
        var context = ((PacketContextProvider) (Object) f.player.connection).getPacketContext();
        check(h, PolymerItemUtils.getPolymerItemStack(out, context, h.getLevel().registryAccess()) == out,
                "Already projected carrier is not double-converted");
        var restored = PolymerItemUtils.getRealItemStack(out, context, h.getLevel().registryAccess());
        check(h, ItemStack.matches(restored, live) && !WeaponIzanagiPresentation.active(restored),
                "Polymer real-item roundtrip preserves canonical components, not live authority");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated")
    public void staleWrongSlotForeignMenuDonorAndReplacementNeverGrantBindings(GameTestHelper h) {
        var f = reload(h); var snapshot = f.stack.copy(); var stale = snapshot.copy();
        stale.set(DataComponents.CUSTOM_NAME, Component.literal("stale"));
        check(h, project(f, stale) == stale, "Snapshot equality can only reject stale data");
        f.player.getInventory().setItem(1, snapshot);
        check(h, WeaponOutboundPresentation.projectSlot(f.player, f.player.inventoryMenu,
                f.slot + 1, snapshot) == snapshot, "Component-equal unselected slot is not authority");
        check(h, WeaponOutboundPresentation.projectSlot(f.player, f.player.inventoryMenu, -1, snapshot) == snapshot
                && WeaponOutboundPresentation.projectSlot(f.player, f.player.inventoryMenu, 999, snapshot) == snapshot,
                "Invalid packet index cannot acquire a binding");
        var donor = player(h, 8);
        donor.getInventory().setItem(0, f.stack); donor.getInventory().setSelectedSlot(0);
        check(h, WeaponIzanagiPresentation.active(f.stack) && !WeaponIzanagiPresentation.ownedBy(donor, f.stack),
                "Even an exact-object alias does not transfer original owner authority");
        check(h, WeaponOutboundPresentation.projectSlot(donor, donor.inventoryMenu, slot(donor), snapshot) == snapshot
                && WeaponOutboundPresentation.projectSlot(f.player, donor.inventoryMenu, slot(donor), snapshot) == snapshot,
                "Foreign recipient/menu are rejected independently of component equality");
        f.player.getInventory().setItem(0, snapshot);
        check(h, !WeaponIzanagiPresentation.active(snapshot) && project(f, snapshot.copy()).is(WeaponCombatItem.INSTANCE),
                "Replacement copy cannot revive retired binding or become a client carrier");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated")
    public void missingRecipientContextAndChangedLevelFailClosedWithoutMutation(GameTestHelper h) {
        var f = reload(h); var snapshot = f.stack.copy();
        var context = ((PacketContextProvider) (Object) f.player.connection).getPacketContext();
        var old = context.get(PacketContext.GAME_PROFILE);
        @SuppressWarnings("unchecked") var key = (PacketContext.Key<com.mojang.authlib.GameProfile>) PacketContext.GAME_PROFILE;
        try {
            context.set(key, null);
            check(h, project(f, snapshot) == snapshot, "Missing native login metadata fails closed");
        } finally { context.set(key, old); }
        var nether = h.getLevel().getServer().getLevel(Level.NETHER);
        check(h, nether != null && nether != h.getLevel(), "Independent native level fixture exists");
        try {
            f.player.setServerLevel(nether);
            check(h, project(f, snapshot) == snapshot && !WeaponIzanagiPresentation.active(f.stack),
                    "Old-level live binding cannot authorize transport");
        } finally { f.player.setServerLevel(h.getLevel()); }
        check(h, ItemStack.matches(snapshot, f.stack), "Rejected projection is mutation-free");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated")
    public void payloadFreezesAtValidSendTimeAndCleanupNeverRebindsCopiedData(GameTestHelper h) {
        var f = reload(h); var snapshot = f.stack.copy(); var frozen = project(f, snapshot); var exact = frozen.copy();
        var snapshots = new ArrayList<ItemStack>();
        for (var slot : f.player.inventoryMenu.slots) snapshots.add(slot.getItem().copy());
        var before = snapshots.stream().map(ItemStack::copy).toList();
        var projected = WeaponOutboundPresentation.projectContent(f.player, f.player.inventoryMenu, snapshots);
        check(h, projected != snapshots && projected.get(f.slot).is(Items.CROSSBOW),
                "Initial-content payload projects selected slot in a new list");
        for (int i = 0; i < snapshots.size(); i++) check(h, ItemStack.matches(before.get(i), snapshots.get(i)),
                "Shared initial snapshots untouched at index " + i);
        WeaponRuntime.cleanup(f.player);
        check(h, ItemStack.matches(exact, frozen) && !WeaponIzanagiPresentation.active(frozen)
                && !WeaponIzanagiPresentation.active(f.stack),
                "Already sent snapshot remains frozen, never a source of gameplay authority");
        var current = f.stack.copy();
        check(h, project(f, current) == current && project(f, snapshot) == snapshot,
                "Later current/old snapshots cannot resurrect a cleaned route");
        h.succeed();
    }
}
