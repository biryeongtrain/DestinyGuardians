package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.List;

import static kim.biryeong.destiny.weapon.WeaponBowWindow.Phase.*;

/** Native SERVER use and real HUD entities, not native-client visual/performance evidence.
 * Perfect/late feedback is informational: it neither fires nor changes the release damage.
 * Explicit Tempo lifecycle fixtures isolate accepted-duration policy; they do not claim earned procs.
 */
public final class WeaponBowWindowW74GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String SLAB = "whispering_slab";
    private record Bow(ServerPlayer player, ItemStack stack, WeaponCatalog.Entry entry, WeaponProfile base) {}

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        return p;
    }

    private static Bow bow(GameTestHelper h, String id, double z) {
        var p = player(h, z);
        var entry = WeaponCatalog.find(id).orElseThrow();
        var stack = WeaponItems.create(entry);
        int slot = WeaponCharacteristics.of(entry).slot().hotbar();
        p.getInventory().setItem(slot, stack);
        p.getInventory().setSelectedSlot(slot);
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
        return new Bow(p, stack, entry, WeaponProfile.forEntry(entry));
    }

    private static void drive(GameTestHelper h, Bow... bows) {
        h.onEachTick(() -> {
            for (var b : bows) {
                WeaponRuntime.tickPlayer(b.player);
                TestPlayers.drain(b.player);
            }
        });
    }

    private static int rounds(Bow b) { return WeaponItems.magazine(b.stack, b.base).rounds(); }

    private static void use(GameTestHelper h, Bow b) {
        WeaponCombatItem.INSTANCE.use(h.getLevel(), b.player, InteractionHand.MAIN_HAND);
        check(h, b.player.isUsingItem() && b.player.getUseItem() == b.stack,
                "Native server use holds the exact ordinary bow stack");
    }

    private static void idle(GameTestHelper h, ServerPlayer p, String reason) {
        check(h, WeaponRuntime.bowDrawState(p).equals(WeaponBowWindow.idle()), reason);
    }

    private static void state(GameTestHelper h, Bow b, WeaponBowWindow.Phase phase,
                              float progress, long age, int window) {
        var observed = WeaponRuntime.bowDrawState(b.player);
        check(h, observed.phase() == phase && Math.abs(observed.progress() - progress) < 1e-6f
                        && observed.fullDrawAge() == age && observed.windowTicks() == window,
                b.entry.id() + " expected " + phase + "/" + progress + "/" + age + "/" + window
                        + ", observed " + observed);
    }

    /** Lifecycle-only fixture: use the real selected socket and production token validation. */
    private static void lifecycleTempo(GameTestHelper h, Bow b) {
        check(h, WeaponPerks.select(b.stack, "archers_tempo"), "Explicit official Tempo socket selection");
        WeaponArcherTempo.update(b.player);
        var token = WeaponArcherTempo.capture(b.player);
        WeaponArcherTempo.confirmed(b.player, token, true);
        check(h, WeaponArcherTempo.remaining(b.player) == 60, "Explicit lifecycle token starts sixty ticks");
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void bothNativeBowsHaveExactDrawingPerfectAndLateBoundariesAndNeverAutoRelease(GameTestHelper h) {
        var winds = bow(h, "biting_winds", 3);
        var slab = bow(h, SLAB, 9);
        drive(h, winds, slab);
        for (var b : List.of(winds, slab)) {
            idle(h, b.player, "Loaded but unstarted bow has no phase");
            use(h, b);
            int draw = b.base.chargeTicks(), window = b == winds ? 9 : 14;
            state(h, b, DRAWING, 0, -1, window);
            h.runAfterDelay(draw - 1, () -> state(h, b, DRAWING, (draw - 1f) / draw, -1, window));
            h.runAfterDelay(draw, () -> state(h, b, PERFECT, 1, 0, window));
            h.runAfterDelay(draw + window - 1, () -> state(h, b, PERFECT, 1, window - 1, window));
            h.runAfterDelay(draw + window, () -> state(h, b, LATE, 1, window, window));
            h.runAfterDelay(70, () -> {
                state(h, b, LATE, 1, 70 - draw, window);
                var before = b.stack.copy();
                for (int i = 0; i < 24; i++) WeaponRuntime.bowDrawState(b.player);
                check(h, b.player.isUsingItem() && b.player.getUseItem() == b.stack && rounds(b) == 1
                                && WeaponRuntime.activeProjectiles(b.player) == 0 && !WeaponRuntime.reloading(b.player)
                                && ItemStack.matches(before, b.stack),
                        "Late hold and repeated reads neither force release, spend/refill ammo, nor change the item");
            });
        }
        h.runAfterDelay(72, h::succeed);
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void lifecycleTempoNineTickOriginAndAcceptedDurationSurviveMidDrawProcAndExpiry(GameTestHelper h) {
        var fast = bow(h, SLAB, 2);
        var mid = bow(h, SLAB, 6);
        var expiry = bow(h, SLAB, 10);
        drive(h, fast, mid, expiry);
        lifecycleTempo(h, fast);
        lifecycleTempo(h, expiry);
        use(h, fast);
        use(h, mid);
        h.runAfterDelay(2, () -> lifecycleTempo(h, mid));
        h.runAfterDelay(8, () -> state(h, fast, DRAWING, 8 / 9f, -1, 14));
        h.runAfterDelay(9, () -> {
            state(h, fast, PERFECT, 1, 0, 14);
            state(h, mid, DRAWING, 9 / 12f, -1, 14);
        });
        h.runAfterDelay(12, () -> state(h, mid, PERFECT, 1, 0, 14));
        h.runAfterDelay(22, () -> state(h, fast, PERFECT, 1, 13, 14));
        h.runAfterDelay(23, () -> state(h, fast, LATE, 1, 14, 14));
        h.runAfterDelay(55, () -> {
            check(h, WeaponArcherTempo.remaining(expiry.player) == 5, "Accept accelerated draw before expiry");
            use(h, expiry);
        });
        h.runAfterDelay(61, () -> {
            check(h, WeaponArcherTempo.remaining(expiry.player) == 0, "Tempo expires during accepted draw");
            state(h, expiry, DRAWING, 6 / 9f, -1, 14);
        });
        h.runAfterDelay(64, () -> state(h, expiry, PERFECT, 1, 0, 14));
        h.runAfterDelay(77, () -> state(h, expiry, PERFECT, 1, 13, 14));
        h.runAfterDelay(78, () -> {
            state(h, expiry, LATE, 1, 14, 14);
            for (var b : List.of(fast, mid, expiry))
                check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0,
                        "Accepted-duration feedback never emits a shot");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void realNockBufferIsIdleAndBothBowsStartFreshChargeAtActualCompletion(GameTestHelper h) {
        var winds = bow(h, "biting_winds", 3);
        var slab = bow(h, SLAB, 9);
        drive(h, winds, slab);
        for (var b : List.of(winds, slab)) {
            use(h, b);
            int shotAt = 16, nock = b.base.firstReloadTicks(), draw = b.base.chargeTicks();
            int window = b == winds ? 9 : 14;
            h.runAfterDelay(shotAt, () -> {
                b.player.releaseUsingItem();
                check(h, rounds(b) == 0 && WeaponRuntime.activeProjectiles(b.player) == 1,
                        "Real release alone pays and emits one arrow");
                WeaponRuntime.tickPlayer(b.player);
                check(h, WeaponRuntime.reloading(b.player), "Actual shot-caused automatic nock started");
                idle(h, b.player, "Release retires accepted draw");
            });
            h.runAfterDelay(shotAt + 1, () -> {
                use(h, b);
                idle(h, b.player, "Native held buffer during nock has no accepted draw");
            });
            h.runAfterDelay(shotAt + nock - 1, () -> {
                check(h, rounds(b) == 0, "Nock cannot finish early");
                var before = b.stack.copy();
                for (int i = 0; i < 24; i++) idle(h, b.player, "Reads cannot age or finish buffered draw");
                check(h, rounds(b) == 0 && ItemStack.matches(before, b.stack), "Reads cannot finish pending nock");
            });
            h.runAfterDelay(shotAt + nock, () -> {
                // Observe after the production tick, independent of GameTest callback/driver ordering.
                WeaponRuntime.tickPlayer(b.player);
                check(h, rounds(b) == 1 && !WeaponRuntime.reloading(b.player), "Real nock deadline transfers one arrow");
                state(h, b, DRAWING, 0, -1, window);
            });
            h.runAfterDelay(shotAt + nock + 1, () -> state(h, b, DRAWING, 1f / draw, -1, window));
            h.runAfterDelay(shotAt + nock + draw, () -> state(h, b, PERFECT, 1, 0, window));
            h.runAfterDelay(shotAt + nock + draw + window, () -> {
                state(h, b, LATE, 1, window, window);
                check(h, rounds(b) == 1 && b.player.isUsingItem() && !WeaponRuntime.reloading(b.player)
                                && WeaponRuntime.activeProjectiles(b.player) == 0,
                        "Buffered late hold never emits a second arrow");
            });
        }
        h.runAfterDelay(100, h::succeed);
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void qSkillAndActualStowCancelPerfectPhaseAndStaleReleaseWithoutGhostArrows(GameTestHelper h) {
        var q = bow(h, SLAB, 2);
        var skill = bow(h, SLAB, 6);
        var stow = bow(h, SLAB, 10);
        var bows = List.of(q, skill, stow);
        drive(h, q, skill, stow);
        for (var b : bows) use(h, b);
        stow.player.getInventory().setItem(7, new ItemStack(Items.STONE));
        h.runAfterDelay(12, () -> {
            for (var b : bows) state(h, b, PERFECT, 1, 0, 14);
            check(h, InputRouter.onPlayerAction(q.player, ServerboundPlayerActionPacket.Action.DROP_ITEM),
                    "Actual Q route consumes let-down");
            WeaponRuntime.cancelUseForSkill(skill.player);
            stow.player.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(7));
            check(h, stow.player.getMainHandItem().is(Items.STONE), "Actual slot packet stows exact bow");
            for (var b : bows) {
                idle(h, b.player, "Cancellation immediately hides old perfect phase");
                b.player.releaseUsingItem();
                WeaponRuntime.releaseUse(b.player, b.stack);
                check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0
                                && !WeaponRuntime.reloading(b.player), "Stale release cannot pay or fire");
            }
        });
        h.runAfterDelay(40, () -> {
            for (var b : bows) {
                idle(h, b.player, "No delayed draw survives cancellation");
                check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0
                                && !WeaponRuntime.reloading(b.player), "No ghost arrow or nock after cancellation");
            }
            use(h, q);
            use(h, skill);
            state(h, q, DRAWING, 0, -1, 14);
            state(h, skill, DRAWING, 0, -1, 14);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 45, environment = "destiny-test:w90_isolated")
    public void sameTickRealOffhandAwayBackRetiresPhaseAndNewPressStartsAtZero(GameTestHelper h) {
        var b = bow(h, SLAB, 6);
        Guardians.data(b.player).setGuardianClass(GuardianClass.NONE);
        b.player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.STONE));
        drive(h, b);
        lifecycleTempo(h, b);
        use(h, b);
        h.runAfterDelay(9, () -> {
            state(h, b, PERFECT, 1, 0, 14);
            for (int i = 0; i < 2; i++) b.player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
            check(h, b.player.getMainHandItem() == b.stack && b.player.getOffhandItem().is(Items.STONE)
                            && !b.player.isUsingItem(), "Two real packets return exact stack within one server tick");
            idle(h, b.player, "Returned stack cannot inherit old full phase");
            check(h, WeaponArcherTempo.remaining(b.player) == 0, "Actual stow retires Tempo as in W73");
            use(h, b);
            state(h, b, DRAWING, 0, -1, 14);
            check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0,
                    "Same-tick fresh use has no inherited charge or emission");
        });
        h.runAfterDelay(20, () -> state(h, b, DRAWING, 11 / 12f, -1, 14));
        h.runAfterDelay(21, () -> {
            state(h, b, PERFECT, 1, 0, 14);
            check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0, "Only new base duration completes");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void queriesNeverBindMissingRuntimeAndRequireRealNativeUseOfExactMainHandStack(GameTestHelper h) {
        var p = player(h, 6);
        var entry = WeaponCatalog.find(SLAB).orElseThrow();
        var stack = WeaponItems.create(entry);
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        var before = stack.copy();
        for (int i = 0; i < 24; i++) idle(h, p, "Missing runtime stays idle");
        p.startUsingItem(InteractionHand.MAIN_HAND);
        idle(h, p, "Native use alone cannot create accepted runtime draw");
        check(h, ItemStack.matches(before, stack) && !WeaponBowPresentation.active(stack),
                "Reads do not bind presentation, write components, or refill ammo");
        p.stopUsingItem();
        check(h, WeaponRuntime.beginUse(p), "Accept actual runtime charge without native consumption fixture");
        idle(h, p, "Accepted runtime charge alone still requires native use");
        p.startUsingItem(InteractionHand.MAIN_HAND);
        check(h, WeaponRuntime.bowDrawState(p).phase() == DRAWING, "Both runtime acceptance and exact native use authorize phase");
        p.stopUsingItem();
        idle(h, p, "Native cancellation is visible immediately before any runtime tick");
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.STONE));
        p.startUsingItem(InteractionHand.OFF_HAND);
        before = stack.copy();
        for (int i = 0; i < 24; i++) idle(h, p, "Different native-use item cannot borrow main-hand accepted draw");
        check(h, ItemStack.matches(before, stack) && WeaponRuntime.activeProjectiles(p) == 0,
                "Rejected queries leave accepted stack and projectile count untouched");
        p.stopUsingItem();
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 70, environment = "destiny-test:w90_isolated")
    public void copiesSavedNbtAndExactStackTradeCannotCarryLivePerfectPhase(GameTestHelper h) {
        var b = bow(h, SLAB, 3);
        var recipient = bow(h, SLAB, 9);
        drive(h, b, recipient);
        use(h, b);
        h.runAfterDelay(12, () -> {
            state(h, b, PERFECT, 1, 0, 14);
            var ops = h.getLevel().registryAccess().createSerializationContext(NbtOps.INSTANCE);
            var decoded = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, b.stack).getOrThrow()).getOrThrow();
            var copy = b.stack.copy();
            for (var replacement : List.of(copy, decoded)) {
                b.player.setItemInHand(InteractionHand.MAIN_HAND, replacement);
                var saved = replacement.copy();
                idle(h, b.player, "Equal serialized bow is a different exact runtime stack");
                b.player.stopUsingItem();
                b.player.startUsingItem(InteractionHand.MAIN_HAND);
                for (int i = 0; i < 16; i++) idle(h, b.player, "Copied/saved selectors never authorize phase");
                check(h, ItemStack.matches(saved, replacement), "Read cannot repair, bind, or mutate replacement");
            }
            b.player.stopUsingItem();
            b.player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            WeaponRuntime.tickPlayer(b.player);
            recipient.player.setItemInHand(InteractionHand.MAIN_HAND, b.stack);
            recipient.player.startUsingItem(InteractionHand.MAIN_HAND);
            idle(h, recipient.player, "Trading exact stack transfers no owner runtime clock");
            recipient.player.stopUsingItem();
            WeaponRuntime.tickPlayer(recipient.player);
            var traded = new Bow(recipient.player, b.stack, b.entry, b.base);
            int ready = Math.toIntExact(WeaponHandling.remaining(recipient.player));
            check(h, ready > 0, "Actual stack trade retains normal equip readiness deadline");
            WeaponCombatItem.INSTANCE.use(h.getLevel(), recipient.player, InteractionHand.MAIN_HAND);
            check(h, !recipient.player.isUsingItem(), "Trade cannot bypass equip readiness with an early press");
            idle(h, recipient.player, "Rejected early press does not authorize a new draw clock");
            check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0
                            && WeaponRuntime.activeProjectiles(recipient.player) == 0, "Neither replacement nor trade emits an arrow");
            h.runAfterDelay(ready - 1, () -> {
                check(h, WeaponHandling.blocked(recipient.player), "One tick before actual equip deadline remains blocked");
                idle(h, recipient.player, "Trade waiting time cannot age a bow draw");
            });
            h.runAfterDelay(ready, () -> {
                use(h, traded);
                state(h, traded, DRAWING, 0, -1, 14);
                check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(recipient.player) == 0,
                        "First accepted traded draw starts at zero without firing");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 35, environment = "destiny-test:w90_isolated")
    public void eligibilityReadsRejectWrongOwnerDimensionSpectatorSuperAndCleanupWithoutMutation(GameTestHelper h) {
        var b = bow(h, SLAB, 3);
        var other = player(h, 9);
        var originalUuid = other.getUUID();
        drive(h, b);
        use(h, b);
        h.runAfterDelay(12, () -> {
            state(h, b, PERFECT, 1, 0, 14);
            other.setItemInHand(InteractionHand.MAIN_HAND, b.stack);
            try {
                other.setUUID(b.player.getUUID());
                other.startUsingItem(InteractionHand.MAIN_HAND);
                var before = b.stack.copy();
                idle(h, other, "UUID collision does not confer exact ServerPlayer ownership");
                state(h, b, PERFECT, 1, 0, 14);
                check(h, ItemStack.matches(before, b.stack), "Wrong-owner query cannot cancel or rebind legitimate state");
            } finally {
                // Restore even on assertion failure, before TestPlayers.remove uses the connection UUID.
                other.stopUsingItem();
                other.setUUID(originalUuid);
                other.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            }

            var foreign = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                    .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
            b.player.setServerLevel(foreign);
            idle(h, b.player, "Dimension mismatch immediately rejects old draw");
            b.player.setServerLevel(h.getLevel());
            state(h, b, PERFECT, 1, 0, 14);
            b.player.setGameMode(GameType.SPECTATOR);
            idle(h, b.player, "Spectator cannot expose active bow phase");
            b.player.setGameMode(GameType.SURVIVAL);
            AbilityService.startSuper(b.player, new SuperSession() {
                public boolean tick() { return true; }
                public void primary() {}
                public void end() {}
                public float remaining() { return 1; }
            });
            check(h, AbilityService.inSuper(b.player), "Explicit lifecycle session marks actual super eligibility");
            idle(h, b.player, "Super session hides ordinary bow phase");
            AbilityService.endSuper(b.player);
            WeaponRuntime.cleanup(b.player);
            idle(h, b.player, "Cleanup retires accepted runtime draw");
            check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0,
                    "Eligibility transitions and rejected reads never spend or release arrow");
            h.succeed();
        });
    }

    private static ItemDisplayHud frame(Bow b) {
        return (ItemDisplayHud) DisplayHud.getHud(b.player, WeaponReticleHud.FRAME_ID);
    }

    private static ItemDisplayHud center(Bow b) {
        return (ItemDisplayHud) DisplayHud.getHud(b.player, WeaponReticleHud.CENTER_ID);
    }

    private static int color(ItemDisplayHud hud) {
        return hud.getItemDisplay().getItemStack().get(DataComponents.CUSTOM_MODEL_DATA).colors().getFirst();
    }

    private static void hud(GameTestHelper h, Bow b, float width, int tint) {
        WeaponReticleHud.update(b.player, 0, 0, false);
        var frame = frame(b);
        check(h, frame != null && Math.abs(frame.getScale().x() - width) < .001f
                        && Math.abs(frame.getScale().y() - width) < .001f && color(frame) == tint,
                "Authored phase feedback has expected actual frame transform/color: " + width + "/" + tint);
        check(h, center(b).getScale().x() == 4 && center(b).getScale().y() == 4
                        && center(b).getLocation().x() == 960 && center(b).getLocation().y() == 540,
                "Native HUD aim point keeps its fixed four-pixel transform");
    }

    @GameTest(structure = FLOOR, maxTicks = 45, environment = "destiny-test:w90_isolated")
    public void authoredNativeReticleShrinksDuringDrawColorsPerfectAndRestsWhenLateWithStableEntities(GameTestHelper h) {
        var b = bow(h, SLAB, 6);
        drive(h, b);
        hud(h, b, 44, 0xF1F3F5);
        var frame = frame(b);
        var center = center(b);
        int frameId = frame.getEntityId(), centerId = center.getEntityId();
        use(h, b);
        h.runAfterDelay(6, () -> hud(h, b, 36.5f, 0xF1F3F5));
        h.runAfterDelay(12, () -> hud(h, b, 28.5f, 0xF6D66B));
        h.runAfterDelay(25, () -> hud(h, b, 28.5f, 0xF6D66B));
        h.runAfterDelay(26, () -> {
            hud(h, b, 44, 0xD6A36F);
            check(h, frame(b) == frame && center(b) == center
                            && frame.getEntityId() == frameId && center.getEntityId() == centerId,
                    "Draw/perfect/late transitions reuse both native display entities");
            check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0 && b.player.isUsingItem(),
                    "Authored feedback cannot force a release or spend ammo");
            WeaponRuntime.cancelUseForSkill(b.player);
            hud(h, b, 44, 0xF1F3F5);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 45, environment = "destiny-test:w90_isolated")
    public void stablePerfectAndLateReticleReadsReuseNativeItemsAndSendNoMetadataOrGameplayChanges(GameTestHelper h) {
        var b = bow(h, "biting_winds", 6);
        drive(h, b);
        use(h, b);
        for (int at : new int[]{14, 23}) h.runAfterDelay(at, () -> {
            WeaponReticleHud.update(b.player, 0, 0, false);
            var frame = frame(b);
            var dot = center(b);
            var nativeFrame = frame.getItemDisplay().getItemStack();
            var nativeDot = dot.getItemDisplay().getItemStack();
            var scale = frame.getScale();
            var before = b.stack.copy();
            var phase = WeaponRuntime.bowDrawState(b.player);
            TestPlayers.drain(b.player);
            for (int i = 0; i < 24; i++) {
                WeaponReticleHud.update(b.player, 0, 0, false);
                check(h, phase.equals(WeaponRuntime.bowDrawState(b.player)), "HUD reads do not restart phase age");
            }
            check(h, frame(b) == frame && center(b) == dot && frame.getScale().equals(scale)
                            && frame.getItemDisplay().getItemStack() == nativeFrame
                            && dot.getItemDisplay().getItemStack() == nativeDot,
                    "Stable perfect/late feedback reuses native entities, transforms and cached items");
            check(h, TestPlayers.outbound(b.player).isEmpty(), "Unchanged phase reticle queues no packets");
            check(h, ItemStack.matches(before, b.stack) && rounds(b) == 1
                            && WeaponRuntime.activeProjectiles(b.player) == 0 && !WeaponRuntime.reloading(b.player),
                    "Repeated cosmetic queries never mutate components, ammo, nock or projectiles");
        });
        h.runAfterDelay(25, h::succeed);
    }
}
