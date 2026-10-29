package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Server lifecycle/real Polymer route, separate from framebuffer or native Q tests. */
public final class AceReloadW157GameTests {
    static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    static final Identifier MODEL = WeaponGripGameTests.projected(Identifier.parse("destiny:weapon_reload_w157/ace_of_spades"));
    static void check(GameTestHelper h, boolean yes, String why) { h.assertTrue(yes, Component.literal(why)); }
    static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, 0);
        var entry = WeaponCatalog.find("ace_of_spades").orElseThrow();
        var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), 5, 0));
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); CombatHud.remove(p); TestPlayers.remove(p); });
        return p;
    }
    static ItemStack wire(ServerPlayer p, ItemStack s) {
        var context = ((PacketContextProvider)(Object)p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(s, context, p.level().registryAccess());
    }
    static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow()); }

    @GameTest(structure = FLOOR, maxTicks = 150, environment = ENV)
    public void w198DenseSourceBankPublishesMoreThanTwentyOnePosesOnTheRealReload(GameTestHelper h) {
        var p = player(h); var stack = p.getMainHandItem(); int duration = profile(stack).reloadTicks();
        var samples = new java.util.HashSet<Float>();
        check(h, WeaponRuntime.reload(p), "Real source-derived reload admitted");
        for (int tick = 1; tick < duration; tick++) h.runAfterDelay(tick, () -> {
            WeaponRuntime.tickPlayer(p);
            if (WeaponReloadPresentation.ownedBy(p, stack)) {
                var rendered = wire(p, stack);
                check(h, MODEL.equals(rendered.get(DataComponents.ITEM_MODEL)), "Dense sample keeps live wire route");
                samples.add(rendered.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1));
            }
        });
        h.runAfterDelay(duration + 2, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, samples.size() > 21, "Actual packet selectors must exceed old21 pose cadence; got="+samples.size());
            check(h, !WeaponRuntime.reloading(p) && !WeaponReloadPresentation.active(stack), "Same commit deadline and cleanup");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 150, environment = ENV)
    public void actualReloadOwnsMotionUntilExistingRecoveryAndKeepsCanonicalIdentity(GameTestHelper h) {
        var p = player(h); var s = p.getMainHandItem(); var profile = profile(s);
        var canonical = s.get(DataComponents.ITEM_MODEL);
        check(h, WeaponRuntime.reload(p), "Real Ace reload accepted");
        check(h, WeaponReloadPresentation.ownedBy(p, s) && MODEL.equals(wire(p, s).get(DataComponents.ITEM_MODEL)), "Owner gets the new animated carrier");
        check(h, canonical.equals(s.get(DataComponents.ITEM_MODEL)), "Live reload preserves server canonical identity");
        var copy = s.copy();
        check(h, !WeaponReloadPresentation.active(copy)
                && WeaponGripGameTests.projected(canonical).equals(wire(p, copy).get(DataComponents.ITEM_MODEL)),
                "A persisted copy has no live authority or reload wire route");
        for (int i = 1; i <= profile.reloadTicks() + 1; i++) h.runAfterDelay(i, () -> WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(profile.reloadTicks() / 2, () -> {
            float progress = s.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1);
            check(h, progress > .2f && progress < .8f && WeaponReloadPresentation.ownedBy(p, s), "Same real server deadline drives intermediate model sample");
        });
        h.runAfterDelay(profile.reloadTicks() + 2, () -> {
            check(h, !WeaponRuntime.reloading(p) && !WeaponReloadPresentation.active(s), "Recovery retires presentation");
            check(h, WeaponGripGameTests.projected(canonical).equals(wire(p, s).get(DataComponents.ITEM_MODEL)) && canonical.equals(s.get(DataComponents.ITEM_MODEL)), "Canonical identity and idle route restored");
            check(h, WeaponItems.magazine(s, profile).rounds() == 13, "Only existing ammunition lifecycle refills Ace");
            h.succeed();
        });
    }
    @GameTest(structure = FLOOR, maxTicks = 15, environment = ENV)
    public void earlySkillCancellationAndStackReplacementCannotLeaveCylinderOpen(GameTestHelper h) {
        var p = player(h); var s = p.getMainHandItem();
        check(h, WeaponRuntime.reload(p), "Accepted reload");
        WeaponRuntime.cancelUseForSkill(p);
        check(h, !WeaponReloadPresentation.active(s) && !WeaponReloadPresentation.ownedBy(p, s), "Skill retires owner immediately");
        check(h, s.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1) == -1 && WeaponGripGameTests.projected(s.get(DataComponents.ITEM_MODEL)).equals(wire(p, s).get(DataComponents.ITEM_MODEL)), "Cancellation cannot retain open-cylinder graph");
        check(h, WeaponItems.magazine(s, profile(s)).rounds() == 5, "Early visual cancellation cannot pay ammunition");
        check(h, WeaponRuntime.reload(p), "Second real reload accepted");
        var copied = s.copy(); p.setItemInHand(InteractionHand.MAIN_HAND, copied); WeaponRuntime.tickPlayer(p);
        check(h, !WeaponReloadPresentation.active(s) && !WeaponReloadPresentation.active(copied), "Old owner and copied data cannot animate replacement");
        h.succeed();
    }
    @GameTest(structure = FLOOR, maxTicks = 10, environment = ENV)
    public void previewCannotAuthorizeReloadAndSelectorDoesNotOverwriteIndependentData(GameTestHelper h) {
        var p = player(h); var s = p.getMainHandItem();
        s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(9f, .7f, 5f, .3f), List.of(true), List.of("hip", "other"), List.of(0x123456)));
        WeaponReloadPresentation.update(s, true, .5f);
        var data = s.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, data.floats().equals(List.of(9f, .5f, 5f, .3f)) && data.flags().equals(List.of(true)) && data.strings().equals(List.of("hip", "other")) && data.colors().equals(List.of(0x123456)), "Only reload slot1 changes");
        check(h, !WeaponReloadPresentation.ownedBy(p, s), "Legacy helper identity alone has no transport authority");
        WeaponReloadPresentation.clear(s);
        var preview = WeaponModels.create(WeaponCatalog.find("ace_of_spades").orElseThrow());
        var before = preview.copy(); WeaponReloadPresentation.update(preview, true, .5f);
        check(h, !WeaponReloadPresentation.active(preview) && ItemStack.matches(before, preview), "Preview untouched");
        check(h, WeaponItems.magazine(s, profile(s)).rounds() == 5, "Cosmetic selector never credits rounds");
        h.succeed();
    }
}
