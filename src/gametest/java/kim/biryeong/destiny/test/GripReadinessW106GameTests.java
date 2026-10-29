package kim.biryeong.destiny.test;

import com.mojang.brigadier.exceptions.CommandSyntaxException;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.commands.CommandSource;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/** Actual commands, actual stack identities and natural server ticks. W105's immediate post-grip
 * denial is expected Handling behavior; these are fixture/observation regressions, not a rebalance.
 * Server item callbacks below do not establish native pixels, mouse input, wire decoding or audio.
 */
public final class GripReadinessW106GameTests {
    private static final String FLOOR = "destiny-test:w78_floor", ENV = "destiny-test:w90_isolated";
    private static final String RECLUSE = "the_recluse";
    private static final String STATUS = "destiny debug weapon-presentation-status @s";

    private record Actor(ServerPlayer player, ItemStack original, ItemStack offhand) {}

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    /** Captures the real console command's output without adding the embedded player to PlayerList. */
    private static final class Output implements CommandSource {
        final List<String> lines = new ArrayList<>();
        @Override public void sendSystemMessage(Component message) { lines.add(message.getString()); }
        @Override public boolean acceptsSuccess() { return true; }
        @Override public boolean acceptsFailure() { return true; }
        @Override public boolean shouldInformAdmins() { return false; }
    }

    private static int execute(ServerPlayer player, String command, Output output) {
        var server = player.level().getServer();
        // TestPlayers are deliberately absent from PlayerList. A console source supplies OP
        // permission; withEntity makes the explicit <player> selector @s resolve this exact owner.
        var source = server.createCommandSourceStack().withEntity(player)
                .withLevel(player.level()).withPosition(player.position()).withSource(output);
        try {
            return server.getCommands().getDispatcher().execute(command, source);
        } catch (CommandSyntaxException failure) {
            throw new AssertionError("Real command failed: /" + command, failure);
        }
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
    }

    private static void rounds(GameTestHelper h, ItemStack stack, int expected) {
        var magazine = ammo(stack);
        check(h, magazine.rounds() == expected && magazine.reserve() == 0 && magazine.overflow() == 0,
                "Actual stack has " + expected + " rounds, zero finite reserve and zero overflow");
    }

    private static void readiness(GameTestHelper h, ServerPlayer player, long remaining, WeaponSwapCycle.Phase phase) {
        check(h, WeaponHandling.readiness(player).equals(Optional.of(new WeaponHandling.Readiness(remaining, phase))),
                "Owned current stack readiness is " + phase + ":" + remaining);
    }

    /** Every query is checked in the same server tick, including the exact debug sentinel/value. */
    private static void queries(GameTestHelper h, ServerPlayer player) {
        var tick = player.level().getServer().getTickCount();
        var stack = player.getMainHandItem();
        var before = stack.copy();
        var ready = WeaponHandling.readiness(player);
        var presentation = WeaponHandling.presentation(player);
        var ammunition = WeaponRuntime.ammunition(player);
        boolean reloading = WeaponRuntime.reloading(player), using = player.isUsingItem();
        String handling = ready.map(value -> value.phase() + ":" + value.remainingTicks()).orElse("unobserved");
        for (int i = 0; i < 4; i++) {
            var output = new Output();
            check(h, execute(player, STATUS, output) == 1 && output.lines.size() == 1,
                    "Actual OP debug command returns one status line");
            check(h, output.lines.getFirst().contains(" handling=" + handling + " grip="),
                    "Debug reports the exact read-only Handling value, including unobserved");
            check(h, player.level().getServer().getTickCount() == tick
                            && player.getMainHandItem() == stack && ItemStack.matches(before, stack)
                            && WeaponHandling.readiness(player).equals(ready)
                            && WeaponHandling.presentation(player).equals(presentation)
                            && WeaponRuntime.ammunition(player).equals(ammunition)
                            && WeaponRuntime.reloading(player) == reloading && player.isUsingItem() == using,
                    "Repeated readiness/debug queries never bind, tick, advance deadlines, grant ammo or input");
        }
    }

    private static void use(ServerPlayer player) {
        WeaponCombatItem.INSTANCE.use(player.level(), player, InteractionHand.MAIN_HAND);
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long started;
        final List<Actor> actors = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h;
            started = h.getLevel().getServer().getTickCount();
            for (int x = 0; x <= 16; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            for (int y = 4; y <= 10; y++) for (int z = 0; z < 32; z++) h.setBlock(16, y, z, Blocks.STONE);
            h.onEachTick(() -> {
                for (var actor : actors) {
                    var player = actor.player();
                    var origin = h.absoluteVec(Vec3.ZERO);
                    var box = player.getBoundingBox();
                    check(h, player.level() == h.getLevel() && box.minX > origin.x && box.maxX < origin.x + 48
                                    && box.minY > origin.y + 3 && box.maxY < origin.y + 12
                                    && box.minZ > origin.z && box.maxZ < origin.z + 32,
                            "Complete owned player AABB stays within W90's raised isolated fixture");
                    TestPlayers.drain(player);
                }
            });
        }

        Actor actor(WeaponModels.Grip grip, int rounds) {
            var player = TestPlayers.create(h, new Vec3(3, 4, 8 + actors.size() * 8), -90, 0,
                    "W106_" + UUID.randomUUID().toString().substring(0, 8));
            // Register separately so TestCleanup still runs remaining teardown if one system fails.
            TestCleanup.register(h, () -> TestPlayers.remove(player));
            TestCleanup.register(h, () -> WeaponReticleHud.remove(player));
            TestCleanup.register(h, () -> CombatHud.remove(player));
            TestCleanup.register(h, () -> WeaponRuntime.cleanup(player));
            TestCleanup.register(h, () -> { player.setShiftKeyDown(false); player.stopUsingItem(); });
            player.setNoGravity(true);
            player.setOnGround(true);
            player.setAttached(WeaponLoadout.ENABLED, false);
            var entry = WeaponCatalog.find(RECLUSE).orElseThrow();
            var stack = WeaponModels.withGrip(WeaponItems.create(entry), grip).orElseThrow();
            WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, 0));
            var offhand = new ItemStack(Items.EMERALD, 4);
            player.setItemInHand(InteractionHand.MAIN_HAND, stack);
            player.setItemInHand(InteractionHand.OFF_HAND, offhand);
            var actor = new Actor(player, stack, offhand);
            actors.add(actor);
            check(h, !WeaponLoadout.enabled(player) && WeaponLoadout.canUse(player), "Actual standalone policy");
            return actor;
        }

        void at(int elapsed, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == started, "Register deadlines during initialization");
            h.runAfterDelay(elapsed, () -> {
                check(h, h.getLevel().getServer().getTickCount() - started == elapsed,
                        "Exact natural server elapsed tick " + elapsed);
                action.run();
            });
        }
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 10)
    public void readinessAndDebugDistinguishUnobservedFromBoundZeroWithoutObservingReplacement(GameTestHelper h) {
        var f = new Fixture(h);
        var actor = f.actor(WeaponModels.Grip.NATIVE, 41);
        var player = actor.player();
        Guardians.forget(player);
        check(h, Guardians.runtimeIfPresent(player).isEmpty(), "Fresh observation has no Guardian runtime");
        check(h, WeaponHandling.readiness(player).isEmpty(), "Initial observation is explicitly absent");
        queries(h, player);
        check(h, Guardians.runtimeIfPresent(player).isEmpty(), "Readiness and full diagnostics do not initialize Guardian runtime");
        // As in W105: a rejected full-mag reload establishes a real equipped state without a shot.
        check(h, !WeaponRuntime.reload(player) && !WeaponRuntime.reloading(player), "Full-mag bootstrap cannot reload");
        readiness(h, player, 0, WeaponSwapCycle.Phase.NONE);
        check(h, WeaponHandling.presentation(player).isEmpty(), "Ready gameplay binding needs no cosmetic swap");
        Guardians.forget(player);
        queries(h, player);
        check(h, Guardians.runtimeIfPresent(player).isEmpty(), "An observed Handling binding still cannot create Guardian runtime");

        var replacement = WeaponModels.withGrip(actor.original(), WeaponModels.Grip.NATIVE).orElseThrow();
        check(h, replacement != actor.original() && ItemStack.matches(replacement, actor.original()),
                "Even an equal-component withGrip result is a different actual stack");
        player.setItemInHand(InteractionHand.MAIN_HAND, replacement);
        check(h, WeaponHandling.readiness(player).isEmpty(), "Same-tick current-stack mismatch is unobserved, never ready zero");
        queries(h, player);
        player.setItemInHand(InteractionHand.MAIN_HAND, actor.original());
        readiness(h, player, 0, WeaponSwapCycle.Phase.NONE);
        check(h, WeaponHandling.presentation(player).isEmpty(), "Queries did not bind the transient replacement or invent a swap");

        player.setGameMode(GameType.SPECTATOR);
        check(h, WeaponHandling.readiness(player).isEmpty(), "Ineligible owner has no readiness");
        queries(h, player);
        player.setGameMode(GameType.SURVIVAL);
        readiness(h, player, 0, WeaponSwapCycle.Phase.NONE);
        for (var ordinary : List.of(ItemStack.EMPTY, new ItemStack(Items.STONE),
                WeaponModels.create(WeaponCatalog.find(RECLUSE).orElseThrow()))) {
            player.setItemInHand(InteractionHand.MAIN_HAND, ordinary);
            check(h, WeaponHandling.readiness(player).isEmpty(), "Empty, ordinary and preview items have no combat readiness");
            queries(h, player);
        }
        player.setItemInHand(InteractionHand.MAIN_HAND, actor.original());
        readiness(h, player, 0, WeaponSwapCycle.Phase.NONE);
        WeaponRuntime.cleanup(player);
        check(h, WeaponHandling.readiness(player).isEmpty(), "Lifecycle cleanup retires the actual binding");
        queries(h, player);
        rounds(h, actor.original(), 41);
        rounds(h, replacement, 41);
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 60)
    public void nativeGripCommandReplacementBlocksUntilExactDeadlineThenFreshUsePaysOnlyReplacement(GameTestHelper h) {
        commandReplacement(h, WeaponModels.Grip.NATIVE);
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 60)
    public void twoHandGripCommandReplacementBlocksUntilExactDeadlineThenFreshHeartbeatPaysOnlyReplacement(GameTestHelper h) {
        commandReplacement(h, WeaponModels.Grip.TWO_HAND);
    }

    private static void commandReplacement(GameTestHelper h, WeaponModels.Grip target) {
        var f = new Fixture(h);
        var actor = f.actor(target == WeaponModels.Grip.NATIVE ? WeaponModels.Grip.TWO_HAND : WeaponModels.Grip.NATIVE, 41);
        var player = actor.player();
        check(h, WeaponHandling.readiness(player).isEmpty(), "Initial equipped state is unobserved");
        check(h, !WeaponRuntime.reload(player), "Full-mag bootstrap has no sacrificial shot or reload");
        readiness(h, player, 0, WeaponSwapCycle.Phase.NONE);
        String grip = target == WeaponModels.Grip.NATIVE ? "native" : "two_hand";
        check(h, execute(player, "destiny weapon grip " + grip + " @s", new Output()) == 1,
                "Real /destiny weapon grip " + grip + " <player> succeeds via server dispatcher");
        var replacement = player.getMainHandItem();
        check(h, replacement != actor.original() && replacement.is(WeaponCombatItem.INSTANCE)
                        && WeaponItems.entry(replacement).equals(WeaponItems.entry(actor.original()))
                        && WeaponModels.twoHanded(replacement) == (target == WeaponModels.Grip.TWO_HAND),
                "Command replaces the actual stack with the same combat weapon and requested grip");
        check(h, WeaponHandling.readiness(player).isEmpty(), "Command's same-tick replacement has not been observed");
        queries(h, player);
        var outgoing = WeaponHandlingProfile.of(WeaponItems.entry(actor.original()).orElseThrow());
        var incoming = WeaponHandlingProfile.of(WeaponItems.entry(replacement).orElseThrow());
        check(h, outgoing.supported() && incoming.supported(), "Both profiles have real Handling timing");
        int stow = outgoing.stowTicks(), delay = stow + incoming.readyTicks();
        check(h, delay > stow && delay + 1 < 60, "Exact profile sum fits test timeout");

        use(player); // Native beginUse or the actual two-hand heartbeat branch, intentionally denied.
        readiness(h, player, delay, WeaponSwapCycle.Phase.STOW);
        check(h, !player.isUsingItem() && !WeaponRuntime.reloading(player), "Tick-zero rejected input cannot create a held shot/reload");
        rounds(h, replacement, 41);
        rounds(h, actor.original(), 41);
        queries(h, player);
        f.at(stow, () -> {
            readiness(h, player, incoming.readyTicks(), WeaponSwapCycle.Phase.READY);
            rounds(h, replacement, 41);
            queries(h, player);
        });
        f.at(delay - 1, () -> {
            readiness(h, player, 1, WeaponSwapCycle.Phase.READY);
            queries(h, player);
            use(player);
            check(h, !player.isUsingItem() && !WeaponRuntime.reloading(player), "Boundary-minus-one input is still denied");
            rounds(h, replacement, 41);
            rounds(h, actor.original(), 41);
        });
        f.at(delay, () -> {
            readiness(h, player, 0, WeaponSwapCycle.Phase.NONE);
            queries(h, player);
            rounds(h, replacement, 41); // Expiration and both denied inputs must not synthesize fire.
            use(player); // A separate fresh item callback at the exact gameplay deadline.
            check(h, player.getMainHandItem() == replacement && player.getOffhandItem() == actor.offhand()
                            && actor.offhand().is(Items.EMERALD) && actor.offhand().getCount() == 4
                            && !WeaponLoadout.enabled(player), "Only actual selected standalone weapon participates");
            rounds(h, replacement, 40);
            rounds(h, actor.original(), 41);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 160)
    public void emptyTriggerReloadsOriginalStackToFortyOneThenIndependentFreshUseSpendsOneForBothGrips(GameTestHelper h) {
        var f = new Fixture(h);
        var entry = WeaponCatalog.find(RECLUSE).orElseThrow();
        var profile = WeaponProfile.forEntry(entry);
        int duration = profile.firstReloadTicks();
        check(h, profile.magazine() == 41 && profile.infiniteReserve() && profile.reserve() == 0
                        && !profile.shellReload() && profile.roundsPerInsert() == 0
                        && duration == profile.reloadTicks() && duration > 8 && duration + 3 < 160,
                "Existing Recluse whole-magazine infinite-reserve policy, with its unchanged deadline");
        for (var grip : WeaponModels.Grip.values()) {
            var actor = f.actor(grip, 0);
            var player = actor.player();
            check(h, WeaponHandling.readiness(player).isEmpty(), "Empty weapon initially unobserved");
            queries(h, player);
            use(player);
            readiness(h, player, 0, WeaponSwapCycle.Phase.NONE);
            check(h, WeaponRuntime.reloading(player) && WeaponRuntime.reloadOwnedBy(player, actor.original())
                            && !player.isUsingItem(), "Real empty trigger starts owned reload without a held native/heartbeat shot");
            rounds(h, actor.original(), 0);
            queries(h, player);
            f.at(duration - 1, () -> {
                check(h, player.getMainHandItem() == actor.original() && WeaponRuntime.reloading(player),
                        "Original actual stack still owns the pending transaction before deadline");
                rounds(h, actor.original(), 0);
                queries(h, player);
            });
            f.at(duration, () -> {
                // If natural runtime processing has not yet committed the due reload, a debug
                // query must not do that work itself. Compare whichever state this tick owns.
                check(h, player.getMainHandItem() == actor.original(), "Reload deadline retains actual stack identity");
                queries(h, player);
            });
            // Natural END_SERVER_TICK processing may follow GameTest callbacks at the deadline.
            // Observe after that tick, as in W105; no tickPlayer/update or fabricated clock advance.
            f.at(duration + 1, () -> {
                check(h, player.getMainHandItem() == actor.original() && !WeaponRuntime.reloading(player)
                                && !WeaponRuntime.reloadOwnedBy(player, actor.original()) && !player.isUsingItem(),
                        "Natural reload completion retires ownership on the original stack without latent input");
                rounds(h, actor.original(), 41);
                readiness(h, player, 0, WeaponSwapCycle.Phase.NONE);
                queries(h, player);
            });
            f.at(duration + 2, () -> {
                rounds(h, actor.original(), 41); // A further quiet tick still cannot spend a round.
                use(player); // Independent native press / heartbeat after the old lease expired.
                check(h, player.getMainHandItem() == actor.original() && !WeaponRuntime.reloading(player)
                                && !WeaponLoadout.enabled(player) && WeaponLoadout.canUse(player)
                                && player.getOffhandItem() == actor.offhand(),
                        "Fresh input spends only the original standalone combat stack, preserving offhand");
                rounds(h, actor.original(), 40);
                // This is the synchronous single-edge debit only. A two-hand SMG lease can
                // legitimately produce later automatic shots until its real six-tick expiry.
            });
        }
        f.at(duration + 3, h::succeed);
    }
}
