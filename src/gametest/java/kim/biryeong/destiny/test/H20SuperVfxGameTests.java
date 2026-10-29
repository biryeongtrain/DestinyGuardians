package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.fx.SuperVfx;
import kim.biryeong.destiny.guardian.Element;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** H20 cosmetic lifecycle integration. Embedded players are not proof of client rendering/visibility. */
public final class H20SuperVfxGameTests {
    private static final String FLOOR = "destiny-test:floor";

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static ServerPlayer owner(GameTestHelper h) {
        ServerPlayer player = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(player));
        return player;
    }

    private static boolean phase(ServerPlayer owner, String phase) {
        return SuperVfx.lifecycleSnapshots().stream().anyMatch(s -> s.owner().equals(owner.getUUID())
                && s.kind().equals("EQUIP") && s.phase().equals(phase));
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void propLifecycleIsOwnerIsolatedAndDoesNotChangeBeamContract(GameTestHelper h) {
        ServerPlayer a = owner(h), b = owner(h);
        try {
            check(h, SuperVfx.materialize(a, Element.VOID), "Void materializes");
            check(h, SuperVfx.materialize(a, Element.VOID), "Re-entry replaces, not duplicates");
            check(h, SuperVfx.materialize(b, Element.ARC), "Other owner has independent cue");
            check(h, SuperVfx.lifecycleCount(a) == 1 && SuperVfx.lifecycleCount(b) == 1, "One cue each");
            SuperVfx.charge(a, .75);
            check(h, phase(a, "CHARGE") && phase(b, "FORM"), "Charging affects only Void owner");
            SuperVfx.cancelOwned(a);
            SuperVfx.cancelOwned(a);
            check(h, SuperVfx.lifecycleCount(a) == 0 && SuperVfx.lifecycleCount(b) == 1, "Idempotent owner cleanup");
            check(h, SuperVfx.activeCount(a) == 0 && SuperVfx.activeCount(b) == 0,
                    "H20 accents allocate no Polymer beam holders");
            h.succeed();
        } finally { TestPlayers.remove(a); TestPlayers.remove(b); }
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void invalidInputsCannotAllocateOrCorruptLifecycle(GameTestHelper h) {
        ServerPlayer p = owner(h);
        try {
            check(h, !SuperVfx.materialize(null, Element.VOID), "Null owner rejected");
            check(h, !SuperVfx.materialize(p, null) && !SuperVfx.materialize(p, Element.KINETIC), "Unsupported props rejected");
            check(h, !SuperVfx.voidRelease(p, p.position(), Vec3.ZERO), "Zero direction rejected");
            check(h, !SuperVfx.voidRelease(p, p.position(), new Vec3(Double.NaN, 0, 0)), "NaN rejected");
            check(h, !SuperVfx.voidRelease(p, p.position().add(5, 0, 0), new Vec3(1, 0, 0)), "Remote release origin rejected");
            check(h, !SuperVfx.followArrow(p, null), "Null projectile rejected");
            check(h, !SuperVfx.anchor(p, new Vec3(Double.NaN, 0, 0), 10), "Invalid anchor rejected");
            check(h, SuperVfx.lifecycleCount(p) == 0, "No retained invalid cues");
            SuperVfx.materialize(p, Element.VOID);
            SuperVfx.charge(p, Double.NaN);
            check(h, phase(p, "FORM"), "Nonfinite charge does not change stage");
            SuperVfx.charge(p, 10);
            check(h, phase(p, "CHARGE"), "Finite overshoot is safely clamped");
            h.succeed();
        } finally { TestPlayers.remove(p); }
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void releaseSurvivesNormalSessionEndButStillExpires(GameTestHelper h) {
        ServerPlayer p = owner(h);
        SuperVfx.materialize(p, Element.VOID);
        check(h, SuperVfx.voidRelease(p, p.getEyePosition(), p.getLookAngle()), "Release accepted");
        SuperVfx.dematerialize(p, Element.VOID);
        SuperVfx.dematerialize(p, Element.VOID);
        check(h, phase(p, "RELEASE"), "Normal session end cannot truncate release snap");
        h.runAfterDelay(8, () -> {
            check(h, SuperVfx.lifecycleCount(p) == 0, "Release expires in seven normal server ticks");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarDissolveAndDimensionCleanupUseNormalManagerTicks(GameTestHelper h) {
        // The 24-cue pool is global, not scoped to this test's players or structure. Parallel
        // super timing fixtures legitimately evict an older healthy control at capacity.
        // Allocate NOTHING while waiting for a full quiet window, rather than clearing others'
        // cues, refreshing our survivor, accepting its eviction, or retrying failed assertions.
        long[] idleSince = {-1};
        h.startSequence().thenWaitUntil(() -> {
            var cues = SuperVfx.lifecycleSnapshots();
            if (!cues.isEmpty()) idleSince[0] = -1;
            else if (idleSince[0] < 0) idleSince[0] = h.getTick();
            check(h, idleSince[0] >= 0 && h.getTick() - idleSince[0] >= 8,
                    "Waiting for eight consecutive idle H20 pool ticks; active cues=" + cues.size());
        }).thenExecute(() -> {
            ServerPlayer solar = owner(h), moved = owner(h), healthy = owner(h);
            check(h, SuperVfx.materialize(solar, Element.SOLAR), "Solar cue accepted");
            check(h, SuperVfx.materialize(moved, Element.ARC), "Dimension control cue accepted");
            check(h, SuperVfx.materialize(healthy, Element.VOID), "Healthy control cue accepted");
            check(h, SuperVfx.lifecycleCount(solar) == 1 && SuperVfx.lifecycleCount(moved) == 1
                    && SuperVfx.lifecycleCount(healthy) == 1, "Exactly one initial cue per fixture owner");
            check(h, SuperVfx.lifecycleSnapshots().size() == 3, "Isolated scenario begins with three of 24 cue slots");
            SuperVfx.dematerialize(solar, Element.SOLAR);
            check(h, phase(solar, "DISSOLVE"), "Solar begins a bounded final shimmer");
            var other = h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER)
                    ? Level.OVERWORLD : Level.NETHER);
            check(h, other != null, "Second dimension required");
            moved.setServerLevel(other);
            h.runAfterDelay(6, () -> {
                check(h, SuperVfx.lifecycleCount(solar) == 0, "Dissolve expires after five ticks");
                check(h, SuperVfx.lifecycleCount(moved) == 0, "World change drops cue");
                check(h, SuperVfx.lifecycleCount(healthy) == 1,
                        "Healthy owner's cue remains; pool=" + SuperVfx.lifecycleSnapshots());
                check(h, phase(healthy, "FORM"), "Healthy control did not restart or enter dissolve");
                for (ServerPlayer p : List.of(solar, moved, healthy)) {
                    check(h, SuperVfx.activeCount(p) == 0, "Lifecycle cleanup allocates no beam holders");
                    check(h, SuperVfx.lifecycleParticleCount(p) <= 24, "Owner particle budget remains bounded");
                }
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void arrowObserverEndsWithRealProjectileWithoutOwningGameplay(GameTestHelper h) {
        ServerPlayer p = owner(h);
        int[] impacts = {0};
        // High above the floor: no fixture geometry should terminate the projectile before its TTL.
        Vec3 start = p.position().add(0, 5, 0);
        SimProjectile arrow = SimProjectile.launch(p, start, new Vec3(.2, 0, 0), 0, 4,
                new ItemStack(Items.ARROW), .2f, Element.VOID.color(), hit -> impacts[0]++);
        check(h, SuperVfx.followArrow(p, arrow), "Observes actual SimProjectile");
        SuperVfx.dematerialize(p, Element.VOID);
        check(h, SuperVfx.lifecycleCount(p) == 1 && !arrow.isDone(), "Normal prop end leaves flight intact");
        h.runAfterDelay(6, () -> {
            check(h, arrow.isDone() && impacts[0] == 1, "Only real projectile tick invokes its impact exactly once");
            check(h, SuperVfx.lifecycleCount(p) == 0, "Observer removed when projectile completes");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void anchorAccentsShareLifetimeAndScopedCancellationButNotBeamSlots(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> check(h,
                BetterModel.model(HunterVfx.Kind.VOID_ANCHOR.modelName()).isPresent(), "Waiting for anchor renderer"))
                .thenExecute(() -> {
                    ServerPlayer a = owner(h), b = owner(h);
                    Vec3 first = a.position(), second = first.add(0, 0, 2);
                    check(h, SuperVfx.anchor(a, first, 10) && SuperVfx.anchor(a, second, 10), "Two real anchor models");
                    check(h, SuperVfx.anchor(b, first, 10), "Other owner's anchor");
                    check(h, SuperVfx.lifecycleCount(a) == 2 && SuperVfx.lifecycleCount(b) == 1, "Anchor accent cues");
                    SuperVfx.cancelLinks(a, first);
                    check(h, SuperVfx.lifecycleCount(a) == 1 && SuperVfx.lifecycleCount(b) == 1,
                            "Scoped end preserves second anchor and other owner");
                    for (int i = 0; i < 5; i++) check(h,
                            SuperVfx.anchor(a, first.add(i + 1, 0, 3), 10), "Additional bounded anchor");
                    check(h, SuperVfx.lifecycleCount(a) == 4, "Owner retains at most four accent cues");
                    check(h, SuperVfx.activeCount(a) == 0, "Accents use no beam slot");
                    h.runAfterDelay(11, () -> {
                        check(h, SuperVfx.lifecycleCount(a) == 0 && SuperVfx.lifecycleCount(b) == 0,
                                "Anchor accents expire independently of gameplay tasks");
                        h.succeed();
                    });
                });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void repeatedSameTickManagerCallsDoNotMultiplyParticleEmission(GameTestHelper h) {
        ServerPlayer p = owner(h);
        try {
            SuperVfx.materialize(p, Element.VOID);
            SuperVfx.charge(p, 1);
            var server = p.level().getServer();
            SuperVfx.tick(server);
            int emitted = SuperVfx.lifecycleParticleCount(p);
            check(h, emitted > 0 && emitted <= 24, "Small authored particle-point budget");
            for (int i = 0; i < 10; i++) SuperVfx.tick(server);
            check(h, SuperVfx.lifecycleParticleCount(p) == emitted, "At most one frame per server tick");
            h.succeed();
        } finally { TestPlayers.remove(p); }
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void globalCueAndParticleCapsEvictOldestWithoutAllocatingDisplays(GameTestHelper h) {
        // No fixtures while waiting: never clear/evict effects belonging to another running test.
        h.startSequence().thenWaitUntil(() -> check(h, SuperVfx.lifecycleSnapshots().isEmpty(), "Waiting for idle H20 cues"))
                .thenExecute(() -> {
                    List<ServerPlayer> players = new ArrayList<>();
                    try {
                        for (int i = 0; i < 26; i++) {
                            ServerPlayer p = owner(h);
                            players.add(p);
                            SuperVfx.materialize(p, Element.VOID);
                            SuperVfx.charge(p, 1);
                        }
                        check(h, SuperVfx.lifecycleSnapshots().size() == 24, "Global ceiling is 24 particle-only cues");
                        check(h, SuperVfx.lifecycleCount(players.get(0)) == 0 && SuperVfx.lifecycleCount(players.get(1)) == 0,
                                "Two globally oldest cues evicted");
                        SuperVfx.tick(h.getLevel().getServer());
                        int points = players.stream().mapToInt(SuperVfx::lifecycleParticleCount).sum();
                        check(h, points > 0 && points <= 192, "24 full charges request 240 points but the cap admits <=192");
                        for (ServerPlayer p : players) {
                            check(h, SuperVfx.lifecycleParticleCount(p) <= 24, "Owner emission cap");
                            check(h, SuperVfx.activeCount(p) == 0, "No hidden display allocations");
                        }
                        h.succeed();
                    } finally { players.forEach(TestPlayers::remove); }
                });
    }

    @GameTest(structure = FLOOR, maxTicks = 450, environment = "destiny-test:w90_isolated")
    public void abandonedEquipHasWatchdogEvenWithoutSessionEnd(GameTestHelper h) {
        ServerPlayer p = owner(h);
        SuperVfx.materialize(p, Element.ARC);
        h.runAfterDelay(421, () -> {
            check(h, SuperVfx.lifecycleCount(p) == 0, "Forgotten integration hook cannot retain cue past 420 ticks");
            h.succeed();
        });
    }
}
