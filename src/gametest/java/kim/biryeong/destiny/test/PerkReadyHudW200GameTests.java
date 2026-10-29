package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.*;

/** Actual runtime observations and DisplayHud registry cleanup; no native/visual evidence claim. */
public final class PerkReadyHudW200GameTests {
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    private static void check(GameTestHelper h, boolean ok, String text) {
        h.assertTrue(ok, Component.literal(text));
    }
    private static final class Fixture {
        final ServerPlayer p;
        final ItemStack gun;
        final WeaponCatalog.Entry entry;
        final WeaponProfile profile;
        final int slot;
        Fixture(GameTestHelper h) {
            p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, 6), -90, 0,
                    "W200Hud_" + UUID.randomUUID().toString().substring(0, 6));
            Guardians.runtime(p);
            p.setNoGravity(true); p.setOnGround(true); p.setAttached(WeaponLoadout.ENABLED, false);
            entry = WeaponCatalog.find("beloved").orElseThrow();
            gun = WeaponItems.create(entry);
            check(h, WeaponPerks.select(gun, "box_breathing"), "Exact canonical base Box Breathing roll");
            profile = WeaponProfile.forEntry(entry);
            WeaponItems.save(gun, new WeaponMagazine(profile, 1, 0));
            slot = WeaponCharacteristics.of(entry).slot().hotbar();
            p.getInventory().setItem(slot, gun); p.getInventory().setSelectedSlot(slot);
            TestCleanup.register(h, () -> {
                WeaponRuntime.cleanup(p); WeaponBoxBreathing.cleanup(p);
                WeaponPerkHud.remove(p); TestPlayers.remove(p);
            });
            tick();
        }
        void tick() { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); }
    }
    private static List<String> boxNodes(ServerPlayer p) {
        return DisplayHud.getHuds(p).keySet().stream()
                .filter(id -> id.startsWith(WeaponPerkHud.PREFIX + "box_breathing_")).sorted().toList();
    }
    /** Snapshot private ownership/cycle fields to detect accidental writes, not to inject readiness. */
    private static Map<String, Object> boxState(ServerPlayer p) {
        try {
            Field sessions = WeaponBoxBreathing.class.getDeclaredField("SESSIONS");
            sessions.setAccessible(true);
            var owners = (Map<?, ?>) sessions.get(null);
            var sources = (Map<?, ?>) owners.get(p.getUUID());
            var result = new LinkedHashMap<String, Object>();
            result.put("sourceCount", sources == null ? 0 : sources.size());
            var source = sources == null ? null : sources.get(p.getMainHandItem());
            if (source == null) return result;
            for (Field field : source.getClass().getDeclaredFields()) {
                if (Modifier.isStatic(field.getModifiers())) continue;
                field.setAccessible(true);
                var value = field.get(source);
                result.put(field.getName(), value);
                if (value instanceof BoxBreathingCycle cycle) {
                    for (Field clock : BoxBreathingCycle.class.getDeclaredFields()) {
                        if (Modifier.isStatic(clock.getModifiers())) continue;
                        clock.setAccessible(true); result.put("cycle." + clock.getName(), clock.get(cycle));
                    }
                }
            }
            return result;
        } catch (ReflectiveOperationException error) { throw new AssertionError(error); }
    }
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=75)
    public void realReadyLabelPollsArePureAndInvalidLiveInputsHideWithoutPruningTheCycle(GameTestHelper h) {
        var f = new Fixture(h);
        ads(f.p,true); f.tick(); h.onEachTick(f::tick);
        h.startSequence().thenIdle(32).thenExecute(() -> {
            check(h, WeaponAiming.aimInput(f.p) && WeaponBoxBreathing.ready(f.p), "Actual ADS writer earned readiness");
            var before = boxState(f.p); var item = f.gun.copy();
            WeaponPerkHud.update(f.p);
            var nodes = boxNodes(f.p);
            check(h, nodes.equals(List.of(WeaponPerkHud.PREFIX + "box_breathing_label",
                    WeaponPerkHud.PREFIX + "box_breathing_marker")), "Label and marker only, no countdown/count");
            var label = (ItemDisplayHud) DisplayHud.getHud(f.p, nodes.getFirst());
            check(h, label.getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/perk_box_breathing_w200"),
                    "Original W200 resource label is used by the real DisplayHud node");
            for (int i = 0; i < 10; i++) { WeaponBoxBreathing.ready(f.p); WeaponPerkHud.update(f.p); }
            check(h, before.equals(boxState(f.p)) && ItemStack.matches(item, f.gun), "Polling cannot write session, ADS cycle or item");
            check(h, DisplayHud.getHud(f.p, nodes.getFirst()) == label, "Stable observer reuses the actual native node");
            f.gun.setCount(2);
            check(h, !WeaponBoxBreathing.ready(f.p), "Stacked original is not a ready source");
            f.gun.setCount(1);
            check(h, WeaponBoxBreathing.ready(f.p) && before.equals(boxState(f.p)), "Invalid count read did not clear earned cycle");
            WeaponItems.save(f.gun, new WeaponMagazine(f.profile, 0, 0));
            check(h, !WeaponBoxBreathing.ready(f.p), "Empty live magazine cannot advertise readiness");
            WeaponItems.save(f.gun, new WeaponMagazine(f.profile, 1, 0));
            check(h, WeaponBoxBreathing.ready(f.p) && before.equals(boxState(f.p)), "Ammo observation did not consume/clear cycle");
            ads(f.p,false);
            check(h, !WeaponBoxBreathing.ready(f.p), "Actual left-click release revokes readiness immediately");
            var released = boxState(f.p);
            for (int i=0;i<10;i++) { WeaponBoxBreathing.ready(f.p); WeaponPerkHud.update(f.p); }
            check(h, released.equals(boxState(f.p)) && boxNodes(f.p).isEmpty(), "Passive reads cannot mutate or rearm the released cycle");
            h.startSequence().thenIdle(3).thenExecute(() -> {
                ads(f.p,true);
                check(h, WeaponAiming.requested(f.p) && !WeaponBoxBreathing.ready(f.p), "Fresh accepted toggle cannot inherit the released ready window");
            }).thenIdle(32).thenExecute(() -> {
                check(h, WeaponBoxBreathing.ready(f.p), "New continuous ADS interval earns readiness again");
                f.p.getInventory().setItem(f.slot, f.gun.copy());
                check(h, !WeaponBoxBreathing.ready(f.p), "Equal copied item has no original source session");
                f.p.getInventory().setItem(f.slot, f.gun);
                check(h, !WeaponBoxBreathing.ready(f.p), "Actual inventory replacement/stow hook revokes old readiness; reinsertion cannot revive it");
                WeaponAiming.releasedAim(f.p);
                WeaponPerkHud.update(f.p);
                check(h, !WeaponBoxBreathing.ready(f.p) && boxNodes(f.p).isEmpty(), "Accepted release revokes cycle and removes actual nodes");
                h.succeed();
            });
        });
    }
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=75)
    public void observerDoesNotBindAndPaidLastRoundStillUsesPreparedTokenWhileHudDisappears(GameTestHelper h) {
        var f = new Fixture(h);
        ads(f.p,true); f.tick();
        WeaponBoxBreathing.cleanup(f.p);
        var absent = boxState(f.p);
        for (int i = 0; i < 10; i++) { check(h, !WeaponBoxBreathing.ready(f.p), "Read cannot bind missing session"); WeaponPerkHud.update(f.p); }
        check(h, absent.equals(boxState(f.p)) && boxNodes(f.p).isEmpty(), "Missing source stays unbound after HUD polling");
        f.tick(); h.onEachTick(f::tick);
        h.startSequence().thenIdle(32).thenExecute(() -> {
            check(h, WeaponBoxBreathing.ready(f.p), "Only accepted runtime writer established new ready cycle");
            WeaponPerkHud.update(f.p); check(h, boxNodes(f.p).size() == 2, "Earned row exists before payment");
            // Same accepted boundary contract as WeaponRuntime: real ammo payment precedes capture.
            var ammo = WeaponItems.magazine(f.gun, f.profile);
            check(h, ammo.consume(), "Pay actual last round"); WeaponItems.save(f.gun, ammo);
            var paid = WeaponBoxBreathing.capture(f.p, f.entry, 1, WeaponAiming.aimInput(f.p));
            var consumed = boxState(f.p);
            for (int i = 0; i < 10; i++) { WeaponPerkHud.update(f.p); check(h, !WeaponBoxBreathing.ready(f.p), "Paid last round leaves no ready HUD"); }
            check(h, consumed.equals(boxState(f.p)) && boxNodes(f.p).isEmpty(), "Post-payment HUD queries do not mutate consumed cycle");
            check(h, WeaponBoxBreathing.precisionMultiplier(f.p, paid) > 1, "HUD polling preserves prepared paid-shot token on empty magazine");
            WeaponPerkHud.remove(f.p); h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=75)
    public void actualNativeStowAndTraitEditRemoveReadinessAndOnlyTheirOwnedNodes(GameTestHelper h) {
        var f = new Fixture(h);
        ads(f.p,true); f.tick(); h.onEachTick(f::tick);
        h.startSequence().thenIdle(32).thenExecute(() -> {
            check(h, WeaponBoxBreathing.ready(f.p), "Actual runtime prepared the source");
            WeaponPerkHud.update(f.p);
            int other = f.slot == 0 ? 1 : 0;
            f.p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(other));
            f.p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(f.slot));
            WeaponPerkHud.update(f.p);
            check(h, !WeaponBoxBreathing.ready(f.p) && boxNodes(f.p).isEmpty(), "Same-tick real slot transaction cannot resurrect row");
            WeaponPerks.clear(f.gun); WeaponPerkHud.update(f.p);
            check(h, !WeaponBoxBreathing.ready(f.p) && boxNodes(f.p).isEmpty(), "Cleared canonical roll is not a ready source");
            h.succeed();
        });
    }
}
