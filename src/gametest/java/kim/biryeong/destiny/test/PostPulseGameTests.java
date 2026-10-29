package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.fx.PostEffects;
import kim.biryeong.destiny.guardian.Element;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** Embedded live owners and normal server ticks; never clears another test's pulse slots. */
public final class PostPulseGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Vec3 OWNER_POS = new Vec3(2.5, 1, 6.5);
    private static final Identifier ACTIVE = PostEffects.superEffect(Element.VOID);
    private static final Identifier UNRELATED = Identifier.parse("minecraft:creeper");

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static Identifier pulseId(Element element, boolean impact) {
        return Identifier.parse("destiny:super/" + element.getSerializedName()
                + (impact ? "_impact_pulse" : "_activation_pulse"));
    }

    private static void hasOnly(GameTestHelper h, ServerPlayer owner, Identifier... expected) {
        List<Identifier> actual = owner.getPostEffects();
        check(h, actual.size() == expected.length && actual.containsAll(List.of(expected)),
                "Expected only " + List.of(expected) + ", got " + actual);
    }

    private static void baseline(ServerPlayer owner) {
        owner.addPostEffect(ACTIVE);
        owner.addPostEffect(UNRELATED);
    }

    /** Cleanup on assertion failures as well as completion; no global clearAll during parallel tests. */
    private static final class Owners implements AutoCloseable {
        private final GameTestHelper h;
        private final List<ServerPlayer> players = new ArrayList<>();
        private boolean closed;

        private Owners(GameTestHelper h) {
            this.h = h;
            TestCleanup.register(h, this::close);
        }

        private ServerPlayer create() {
            ServerPlayer player = TestPlayers.create(h, OWNER_POS, -90, 0);
            players.add(player);
            return player;
        }

        private void guarded(Runnable action) {
            try {
                action.run();
            } catch (RuntimeException | Error failure) {
                close();
                throw failure;
            }
        }

        private void after(int ticks, Runnable action) {
            h.runAfterDelay(ticks, () -> guarded(action));
        }

        private void complete(Runnable assertions) {
            try {
                assertions.run();
                h.succeed();
            } finally {
                close();
            }
        }

        @Override
        public void close() {
            if (closed) return;
            closed = true;
            for (ServerPlayer player : players) {
                try {
                    PostEffects.cancel(player);
                } finally {
                    TestPlayers.remove(player);
                }
            }
        }
    }

    private static void scenario(GameTestHelper h, Consumer<Owners> assertions) {
        Owners owners = new Owners(h);
        owners.guarded(() -> assertions.accept(owners));
    }

    private static void normalTickLifetime(GameTestHelper h, boolean impact, boolean duplicate) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create();
            var server = h.getLevel().getServer();
            int ttl = impact ? PostEffects.IMPACT_PULSE_TICKS : PostEffects.ACTIVATION_PULSE_TICKS;
            Identifier pulse = pulseId(Element.ARC, impact);
            baseline(owner);
            check(h, server.getPlayerList().getPlayer(owner.getUUID()) == null,
                    "Fixture must exercise live embedded owners outside PlayerList");
            PostEffects.pulse(owner, Element.ARC, impact);
            hasOnly(h, owner, ACTIVE, UNRELATED, pulse);
            int startedAt = server.getTickCount();

            owners.after(1, () -> hasOnly(h, owner, ACTIVE, UNRELATED, pulse));
            if (duplicate) {
                owners.after(ttl - 2, () -> {
                    for (int i = 0; i < 16; i++) PostEffects.pulse(owner, Element.ARC, impact);
                    hasOnly(h, owner, ACTIVE, UNRELATED, pulse);
                });
            }
            owners.after(ttl - 1, () -> {
                check(h, server.getTickCount() - startedAt == ttl - 1, "Use elapsed normal server ticks");
                hasOnly(h, owner, ACTIVE, UNRELATED, pulse);
            });
            // GameTest callbacks run before END_SERVER_TICK; allow that tick's expiry pass to complete.
            owners.after(ttl + 1, () -> owners.complete(() -> {
                check(h, server.getTickCount() - startedAt == ttl + 1, "No synthetic manager ticks");
                hasOnly(h, owner, ACTIVE, UNRELATED);
            }));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void activationExpiresOnNormalServerTicks(GameTestHelper h) {
        normalTickLifetime(h, false, false);
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void impactExpiresOnNormalServerTicks(GameTestHelper h) {
        normalTickLifetime(h, true, false);
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void duplicateActivationDoesNotExtendLifetime(GameTestHelper h) {
        normalTickLifetime(h, false, true);
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void duplicateImpactDoesNotExtendLifetime(GameTestHelper h) {
        normalTickLifetime(h, true, true);
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void impactReplacesActivationOnceAndKeepsItsOwnDeadline(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create();
            baseline(owner);
            Identifier activation = pulseId(Element.SOLAR, false);
            Identifier impact = pulseId(Element.SOLAR, true);
            PostEffects.pulse(owner, Element.SOLAR, false);
            hasOnly(h, owner, ACTIVE, UNRELATED, activation);
            owners.after(1, () -> {
                hasOnly(h, owner, ACTIVE, UNRELATED, activation);
                PostEffects.pulse(owner, Element.SOLAR, true);
                hasOnly(h, owner, ACTIVE, UNRELATED, impact);
                // Neither a second impact nor a fresh activation/element may replace this impact.
                owners.after(2, () -> {
                    PostEffects.pulse(owner, Element.SOLAR, true);
                    PostEffects.pulse(owner, Element.VOID, true);
                    PostEffects.pulse(owner, Element.ARC, false);
                    hasOnly(h, owner, ACTIVE, UNRELATED, impact);
                });
                owners.after(PostEffects.IMPACT_PULSE_TICKS - 1,
                        () -> hasOnly(h, owner, ACTIVE, UNRELATED, impact));
                owners.after(PostEffects.IMPACT_PULSE_TICKS + 1, () -> owners.complete(() ->
                        hasOnly(h, owner, ACTIVE, UNRELATED)));
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void cancelAndAbilityCleanupPreserveOtherOwnerAndUnrelatedEffects(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create();
            ServerPlayer other = owners.create();
            baseline(owner);
            baseline(other);
            Identifier activation = pulseId(Element.ARC, false);
            Identifier otherPulse = pulseId(Element.SOLAR, false);
            PostEffects.pulse(owner, Element.ARC, false);
            PostEffects.pulse(other, Element.SOLAR, false);
            hasOnly(h, owner, ACTIVE, UNRELATED, activation);
            hasOnly(h, other, ACTIVE, UNRELATED, otherPulse);
            PostEffects.cancel(owner);
            PostEffects.cancel(owner);
            hasOnly(h, owner, ACTIVE, UNRELATED);
            hasOnly(h, other, ACTIVE, UNRELATED, otherPulse);

            PostEffects.pulse(owner, Element.ARC, false);
            hasOnly(h, owner, ACTIVE, UNRELATED, activation);
            AbilityService.cleanup(owner);
            owners.complete(() -> {
                hasOnly(h, owner, ACTIVE, UNRELATED);
                hasOnly(h, other, ACTIVE, UNRELATED, otherPulse);
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void deathDimensionChangeAndDisconnectExpireOnlyInvalidOwners(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer dead = owners.create();
            ServerPlayer moved = owners.create();
            ServerPlayer disconnected = owners.create();
            ServerPlayer healthy = owners.create();
            Identifier pulse = pulseId(Element.VOID, false);
            for (ServerPlayer player : List.of(dead, moved, disconnected, healthy)) {
                baseline(player);
                PostEffects.pulse(player, Element.VOID, false);
                hasOnly(h, player, ACTIVE, UNRELATED, pulse);
            }
            ServerLevel other = h.getLevel().getServer().getLevel(
                    h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
            check(h, other != null && other != h.getLevel(), "A second dimension is required");
            dead.setHealth(0); // No death event/explicit cancel: manager must observe invalidation.
            moved.setServerLevel(other);
            disconnected.disconnect();
            owners.after(2, () -> owners.complete(() -> {
                check(h, !dead.isAlive() && disconnected.hasDisconnected(), "Invalidation controls must hold");
                for (ServerPlayer player : List.of(dead, moved, disconnected)) {
                    hasOnly(h, player, ACTIVE, UNRELATED);
                }
                hasOnly(h, healthy, ACTIVE, UNRELATED, pulse);
                // Dead/disconnected owners cannot create a fresh pulse either.
                PostEffects.pulse(dead, Element.ARC, false);
                PostEffects.pulse(disconnected, Element.ARC, true);
                hasOnly(h, dead, ACTIVE, UNRELATED);
                hasOnly(h, disconnected, ACTIVE, UNRELATED);
            }));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void preexistingManualPulseIsNotOwnedAndKineticIsNoOp(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create();
            baseline(owner);
            Identifier manual = pulseId(Element.ARC, false);
            owner.addPostEffect(manual);
            PostEffects.pulse(owner, Element.ARC, false);
            PostEffects.pulse(owner, Element.KINETIC, false);
            PostEffects.pulse(owner, Element.KINETIC, true);
            PostEffects.cancel(owner);
            hasOnly(h, owner, ACTIVE, UNRELATED, manual);
            owners.after(PostEffects.ACTIVATION_PULSE_TICKS + 1, () -> owners.complete(() ->
                    hasOnly(h, owner, ACTIVE, UNRELATED, manual)));
        });
    }
}
