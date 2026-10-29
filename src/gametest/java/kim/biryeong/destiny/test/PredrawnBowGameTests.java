package kim.biryeong.destiny.test;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.input.GuardianAction;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.tracker.EntityTracker;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.IntConsumer;

/**
 * Equipped Shadowshot sessions observed through BetterModel's actual native equipment displays.
 * Embedded owners receive one tickPlayer call per real server tick; global animation, projectile,
 * camera and task ticks remain owned by the server. Assertions run in GameTest callbacks, never Tasks.
 * Model identity/removal is covered here; cord pixels and hand contact require the visual gate.
 */
public final class PredrawnBowGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Identifier DRAWN = DestinyGuardians.id("shadow_bow_h28_drawn");
    private static final Identifier RELEASED = DestinyGuardians.id("shadow_bow_h28");

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static void loaded(GameTestHelper h, Runnable action) {
        h.startSequence().thenWaitUntil(() -> check(h,
                BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(), "Waiting for H22 hunter limb"))
                .thenExecute(() -> {
                    for (int x = 1; x <= 9; x++) {
                        for (int z = 1; z <= 9; z++) h.setBlock(x, 0, z, Blocks.STONE);
                    }
                    action.run();
                });
    }

    /** Read-only, pinned to the inspected PlayerAnimations / BetterModel 3.5.1 fields. */
    private static Object field(Class<?> type, Object receiver, String name) {
        try {
            var field = type.getDeclaredField(name);
            field.setAccessible(true);
            return field.get(receiver);
        } catch (ReflectiveOperationException e) {
            throw new AssertionError("Cannot inspect actual equipped bow: " + type.getName() + "." + name, e);
        }
    }

    private static Map<?, ?> playbacks() {
        return (Map<?, ?>) field(PlayerAnimations.class, null, "ACTIVE");
    }

    private static EntityTracker activeTracker(ServerPlayer player) {
        Object playback = Objects.requireNonNull(playbacks().get(player.getUUID()), "Actual limb playback missing");
        return (EntityTracker) field(playback.getClass(), playback, "tracker");
    }

    private static Display.ItemDisplay equipment(GameTestHelper h, EntityTracker tracker, String boneName) {
        var bone = tracker.bone(b -> b.name().rawName().equals(boneName));
        check(h, bone != null && bone.getDisplay() != null, "Actual equipment display exists: " + boneName);
        var display = bone.getDisplay();
        // ModelDisplayEntityImpl.item() writes this native entity's synced ItemStack directly.
        // Inspect that rendered stack, rather than Playback.equipment or the requested SuperVisuals item.
        return (Display.ItemDisplay) field(display.getClass(), display, "display");
    }

    private static final class Fixture {
        final GameTestHelper h;
        final ServerPlayer player;
        final EntityTracker tracker;
        final Display.ItemDisplay left, right;
        final List<ItemStack> inventory = new ArrayList<>();
        final int selectedSlot;
        final long initialFrames;
        final Set<SimProjectile> arrows = Collections.newSetFromMap(new IdentityHashMap<>());

        Fixture(GameTestHelper h) {
            this.h = h;
            player = TestPlayers.hunter(h, Element.VOID, new Vec3(4.5, 1, 4.5), 35, -18);
            TestCleanup.register(h, () -> TestPlayers.remove(player));
            check(h, !h.getLevel().getServer().getPlayerList().getPlayers().contains(player),
                    "Embedded owner must not also receive a PlayerList ability tick");
            player.setOnGround(true);
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK, 2));
            player.getMainHandItem().set(DataComponents.CUSTOM_NAME, Component.literal("Unchanged real hand"));
            player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.DIAMOND, 3));
            player.getInventory().setItem(9, new ItemStack(Items.ARROW, 17));
            player.getInventory().setItem(17, new ItemStack(Items.OBSIDIAN, 11));
            selectedSlot = player.getInventory().getSelectedSlot();
            for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
                inventory.add(player.getInventory().getItem(slot).copy());
            }
            Guardians.data(player).setSuperEnergy(1);
            check(h, AbilityService.use(player, AbilitySlot.SUPER) == AbilityService.Result.OK,
                    "Real equipped Void super activation succeeds");
            check(h, AbilityService.inSuper(player) && PlayerAnimations.isPlaying(player),
                    "Activation creates both a real session and limb playback");
            tracker = activeTracker(player); // Never getOrCreate a substitute tracker in the test.
            left = equipment(h, tracker, "pli_left_item");
            right = equipment(h, tracker, "pri_right_item");
            initialFrames = PlayerAnimations.serverFrames(player);
            drawn("Activation, before any primary");
            unchangedInventory();
        }

        void step() {
            if (SuperCamera.active(player)) {
                check(h, SuperCamera.move(player,
                        new ServerboundMovePlayerPacket.Rot(player.getYRot(), player.getXRot(), false, false)),
                        "Connected rotation heartbeat accepted during the automatic windup");
                player.connection.tick();
            } else player.doTick();
            AbilityService.tickPlayer(player);
            unchangedInventory();
            observeArrows();
            TestPlayers.drain(player);
        }

        void primary() {
            check(h, AbilityService.perform(player, GuardianAction.PRIMARY), "PRIMARY routes to actual Void session");
        }

        void model(Identifier expected, String phase) {
            ItemStack actual = left.getItemStack();
            check(h, !tracker.isClosed() && activeTracker(player) == tracker,
                    phase + ": original equipped tracker remains active");
            check(h, actual.is(Items.STICK) && actual.getCount() == 1
                            && expected.equals(actual.get(DataComponents.ITEM_MODEL)),
                    phase + ": native left display model expected " + expected
                            + ", got " + actual.get(DataComponents.ITEM_MODEL));
            check(h, right.getItemStack().isEmpty(), phase + ": actual draw hand has no duplicate equipped item");
        }

        void drawn(String phase) {
            model(DRAWN, phase);
            check(h, AbilityService.inSuper(player), phase + ": session remains active before release");
            check(h, SimProjectile.activeCount(player) == 0 && arrows.isEmpty(), phase + ": no early arrow");
        }

        void unchangedInventory() {
            var actual = player.getInventory();
            check(h, actual.getSelectedSlot() == selectedSlot && actual.getContainerSize() == inventory.size(),
                    "Visual bow must preserve inventory shape and selected slot");
            for (int slot = 0; slot < inventory.size(); slot++) {
                check(h, ItemStack.matches(inventory.get(slot), actual.getItem(slot)),
                        "Visual bow must preserve item, count and components in real inventory slot " + slot);
            }
        }

        void observeArrows() {
            for (Object value : (List<?>) field(SimProjectile.class, null, "ACTIVE")) {
                SimProjectile projectile = (SimProjectile) value;
                if (field(SimProjectile.class, projectile, "owner") == player && !projectile.isDone()) {
                    arrows.add(projectile);
                }
            }
        }

        void restored() {
            check(h, tracker.isClosed() && !playbacks().containsKey(player.getUUID())
                            && !PlayerAnimations.isPlaying(player) && !SuperCamera.active(player),
                    "Closed playback cannot reopen or re-equip the bow");
            restoredHand(left.getItemStack(), player.getOffhandItem(), "left");
            restoredHand(right.getItemStack(), player.getMainHandItem(), "right");
            unchangedInventory();
        }

        void restoredHand(ItemStack display, ItemStack real, String hand) {
            // BetterModel may add display tint components. The equipped item/model/count must still
            // map back to the live inventory, including its original custom name, with no super model.
            check(h, ItemStack.isSameItem(display, real) && display.getCount() == real.getCount()
                            && Objects.equals(display.get(DataComponents.ITEM_MODEL), real.get(DataComponents.ITEM_MODEL))
                            && Objects.equals(display.get(DataComponents.CUSTOM_NAME), real.get(DataComponents.CUSTOM_NAME)),
                    "Closed " + hand + " display restores the actual inventory equipment");
        }

        void cancelled() {
            check(h, !AbilityService.inSuper(player), "Cancelled session stays absent");
            restored();
            check(h, SimProjectile.activeCount(player) == 0 && arrows.isEmpty(), "Cancellation cannot launch a delayed arrow");
        }
    }

    private static void ticks(GameTestHelper h, List<Fixture> fixtures, int total, IntConsumer afterTick) {
        tick(h, fixtures, h.getLevel().getServer().getTickCount(), 1, total, afterTick);
    }

    private static void tick(GameTestHelper h, List<Fixture> fixtures, int start, int elapsed, int total,
                             IntConsumer afterTick) {
        h.runAfterDelay(1, () -> {
            check(h, h.getLevel().getServer().getTickCount() - start == elapsed,
                    "Exactly one fixture step per actual server tick: " + elapsed);
            fixtures.forEach(Fixture::step);
            afterTick.accept(elapsed);
            if (elapsed == total) h.succeed();
            else tick(h, fixtures, start, elapsed + 1, total, afterTick);
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void automaticCastKeepsActualBowDrawnThenRestoresAfterRecovery(GameTestHelper h) {
        loaded(h, () -> {
            Fixture f = new Fixture(h);
            ticks(h, List.of(f), 100, elapsed -> {
                if (elapsed < 7) f.drawn("Automatic windup tick " + elapsed);
                else {
                    check(h, !AbilityService.inSuper(f.player) && f.arrows.size() == 1,
                            "Activation alone releases exactly once, with no long aiming hold");
                    if (PlayerAnimations.isPlaying(f.player)) f.model(RELEASED, "Automatic follow-through");
                    else f.restored();
                    if (elapsed == 7) check(h, PlayerAnimations.serverFrames(f.player) > f.initialFrames,
                            "Automatic cast exercised the naturally ticking BetterModel pipeline before cleanup");
                    if (elapsed == 100) f.restored();
                }
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void everyPreReleaseTickStaysDrawnThenSevenEquipsRestAndLaunchesExactlyOneArrow(GameTestHelper h) {
        loaded(h, () -> {
            Fixture f = new Fixture(h);
            f.primary();
            f.drawn("PRIMARY at T");
            ticks(h, List.of(f), 60, elapsed -> {
                if (elapsed < 7) {
                    f.drawn("Pre-release T+" + elapsed);
                    f.primary(); // Repeated accepted routing must not restart the draw or duplicate the arrow.
                    f.drawn("Repeated PRIMARY at T+" + elapsed);
                } else {
                    check(h, !AbilityService.inSuper(f.player), "Actual session ends at T+7");
                    check(h, f.arrows.size() == 1, "Exactly one distinct real projectile across release/recovery");
                    if (elapsed == 7) {
                        check(h, SimProjectile.activeCount(f.player) == 1, "Exactly one live arrow at T+7");
                        f.model(RELEASED, "T+7 removes the nocked arrow using the existing rest item");
                    } else if (PlayerAnimations.isPlaying(f.player)) {
                        f.model(RELEASED, "Recovery never re-nocks an arrow at T+" + elapsed);
                    } else f.restored();
                    check(h, !AbilityService.perform(f.player, GuardianAction.PRIMARY),
                            "Post-release PRIMARY cannot start another arrow");
                    if (elapsed == 60) f.restored();
                }
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void cancelReadyAndDrawStagesCannotReequipOrLaunchDelayedArrow(GameTestHelper h) {
        loaded(h, () -> {
            List<Fixture> fixtures = new ArrayList<>();
            int[] cancelAt = {0, 1, 4, 6};
            for (int cancelTick : cancelAt) {
                Fixture f = new Fixture(h);
                fixtures.add(f);
                if (cancelTick == 0) {
                    AbilityService.endSuper(f.player);
                    f.cancelled();
                } else {
                    f.drawn("Before planned cancellation at T+" + cancelTick);
                }
            }
            ticks(h, fixtures, 60, elapsed -> {
                for (int i = 0; i < fixtures.size(); i++) {
                    Fixture f = fixtures.get(i);
                    if (elapsed <= cancelAt[i]) f.drawn("Pending cancellation T+" + elapsed);
                    if (elapsed == cancelAt[i]) AbilityService.endSuper(f.player);
                    if (elapsed >= cancelAt[i]) {
                        f.cancelled();
                        check(h, !AbilityService.perform(f.player, GuardianAction.PRIMARY),
                                "PRIMARY cannot resurrect a cancelled session");
                    }
                }
            });
        });
    }
}
