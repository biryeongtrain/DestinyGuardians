package kim.biryeong.destiny.test;

import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.ClassAbilityCast;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.ability.jump.JumpAbilities;
import kim.biryeong.destiny.ability.jump.JumpPhysics.Kind;
import kim.biryeong.destiny.ability.titan.TitanAbilities;
import kim.biryeong.destiny.ability.warlock.WarlockAbilities;
import kim.biryeong.destiny.ability.warlock.WarlockClassAbility;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.ClassAbilityTiming;
import kim.biryeong.destiny.guardian.*;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.Holder;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Actual outbound packets from accepted abilities, progressed by the normal server hooks.
 * Stationary owners are deliberately absent from world/player-list ticking; only the spectator
 * ear joins level.players(). No global tick/clear, registry changes, tuning edits or audio mocks.
 * Death/disconnect exercise the registered Fabric callbacks; menu coverage starts at cleanup.
 * This verifies server delivery/codec semantics, not client audibility or native key input.
 */
public final class ClassJumpAudioW270GameTests {
    private static final String FLOOR = "destiny-test:floor";

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static ServerPlayer owner(GameTestHelper h, GuardianClass cls, Vec3 position) {
        var p = TestPlayers.create(h, position, -90, 0, "W270_" + cls);
        var data = Guardians.data(p);
        data.setGuardianClass(cls);
        data.setLoadout(cls, switch (cls) {
            case HUNTER -> HunterAbilities.preset(Element.ARC);
            case TITAN -> TitanAbilities.preset(Element.ARC);
            case WARLOCK -> WarlockAbilities.preset(Element.ARC);
            default -> throw new IllegalArgumentException("Unsupported fixture class " + cls);
        });
        p.setOnGround(false);
        TestCleanup.register(h, () -> {
            // Retire this fake's airborne epoch, including movement samples, on pass AND failure.
            p.setHealth(0);
            TestPlayers.remove(p);
        });
        return p;
    }

    private static ServerPlayer ear(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(6.5, 3, 6.5), 0, 0, "W270_Ear");
        p.setGameMode(GameType.SPECTATOR);
        h.getLevel().players().add(p);
        TestCleanup.register(h, () -> {
            h.getLevel().players().remove(p);
            TestPlayers.remove(p);
        });
        TestPlayers.drain(p);
        return p;
    }

    private static void selectJump(ServerPlayer p, Identifier id) {
        var data = Guardians.data(p);
        data.setLoadout(data.guardianClass(), data.loadout().orElseThrow().with(AbilitySlot.JUMP, id));
    }

    private static void accepted(GameTestHelper h, ServerPlayer p, AbilitySlot slot) {
        check(h, AbilityService.use(p, slot) == AbilityService.Result.OK, "Selected " + slot + " accepted");
    }

    private static <T> List<T> packets(List<Packet<?>> wire, Class<T> type) {
        return wire.stream().filter(type::isInstance).map(type::cast).toList();
    }

    private static void silent(GameTestHelper h, List<Packet<?>> wire) {
        check(h, packets(wire, ClientboundSoundPacket.class).isEmpty()
                        && packets(wire, ClientboundSoundEntityPacket.class).isEmpty()
                        && packets(wire, ClientboundStopSoundPacket.class).isEmpty(),
                "No positional/entity sound or stop on this connection");
    }

    private static void at(GameTestHelper h, ClientboundSoundPacket sound, String key, Vec3 position) {
        check(h, sound.getSound().value().location().equals(Identifier.fromNamespaceAndPath("destiny", key))
                        && sound.getSource() == SoundSource.PLAYERS && sound.getVolume() > 0,
                "Expected audible player event " + key);
        check(h, Math.abs(sound.getX() - position.x) <= .125
                        && Math.abs(sound.getY() - position.y) <= .125
                        && Math.abs(sound.getZ() - position.z) <= .125,
                "Event uses its actual origin within vanilla 1/8-block wire precision: " + key);
    }

    private static void oneAt(GameTestHelper h, List<Packet<?>> wire, String key, Vec3 position) {
        var sounds = packets(wire, ClientboundSoundPacket.class);
        check(h, sounds.size() == 1, "Exactly one positional cue for " + key);
        at(h, sounds.getFirst(), key, position);
        check(h, packets(wire, ClientboundSoundEntityPacket.class).isEmpty()
                        && packets(wire, ClientboundStopSoundPacket.class).isEmpty(),
                "One-shot has no attached duplicate or stop");
    }

    private static ClientboundSoundEntityPacket start(GameTestHelper h, ServerPlayer p, ServerPlayer listener) {
        accepted(h, p, AbilitySlot.JUMP);
        var wire = TestPlayers.outbound(listener);
        var sounds = packets(wire, ClientboundSoundEntityPacket.class);
        check(h, sounds.size() == 1, "Exactly one attached start, without an unproven sustain layer");
        var sound = sounds.getFirst();
        String root = Guardians.data(p).guardianClass() == GuardianClass.TITAN
                ? "jump.titan.lift.voice." : "jump.warlock.glide.voice.";
        var event = sound.getSound().value().location();
        check(h, event.getNamespace().equals("destiny") && event.getPath().startsWith(root),
                "Start selects the correct class alias");
        String suffix = event.getPath().substring(root.length());
        check(h, suffix.matches("[0-9]+") && Integer.parseInt(suffix) < 32,
                "Alias belongs to the 32 voice slots");
        check(h, sound.getId() == p.getId() && sound.getSound().kind() == Holder.Kind.DIRECT
                        && sound.getSource() == SoundSource.PLAYERS && sound.getVolume() > 0 && sound.getPitch() == 1f,
                "Inline event follows the caster entity with fixed pitch");
        check(h, packets(wire, ClientboundSoundPacket.class).isEmpty()
                        && packets(wire, ClientboundStopSoundPacket.class).isEmpty(),
                "Start has no positional duplicate or premature stop");
        return sound;
    }

    private static void stopped(GameTestHelper h, List<Packet<?>> wire, ClientboundSoundEntityPacket... starts) {
        var stops = packets(wire, ClientboundStopSoundPacket.class);
        check(h, stops.size() == starts.length, "Exactly one stop per retired activation");
        for (var start : starts) {
            check(h, stops.stream().filter(s -> start.getSound().value().location().equals(s.getName())
                            && s.getSource() == SoundSource.PLAYERS).count() == 1,
                    "Stop targets only that activation's event and player channel");
        }
        check(h, packets(wire, ClientboundSoundPacket.class).isEmpty()
                        && packets(wire, ClientboundSoundEntityPacket.class).isEmpty(),
                "Retirement never starts or repeats a clip");
    }

    private static List<ServerPlayer> continuousPair(GameTestHelper h) {
        return List.of(owner(h, GuardianClass.TITAN, new Vec3(2.5, 3, 3.5)),
                owner(h, GuardianClass.WARLOCK, new Vec3(2.5, 3, 8.5)));
    }

    private static void inactive(GameTestHelper h, ServerPlayer p) {
        check(h, !JumpAbilities.active(p, Kind.LIFT) && !JumpAbilities.active(p, Kind.GLIDE),
                "Owner has no active continuous jump");
    }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_isolated", maxTicks = 20)
    public void hunterAndBlinkEmitOnlyAcceptedOneShotsAtTheirActualOrigins(GameTestHelper h) {
        var listener = ear(h);
        var p = owner(h, GuardianClass.HUNTER, new Vec3(2.5, 3, 6.5));
        selectJump(p, JumpAbilities.HUNTER_HIGH);
        p.setOnGround(true);
        check(h, AbilityService.use(p, AbilitySlot.JUMP) == AbilityService.Result.FAILED, "Grounded press rejected");
        silent(h, TestPlayers.outbound(listener));
        p.setOnGround(false);
        accepted(h, p, AbilitySlot.JUMP);
        oneAt(h, TestPlayers.outbound(listener), "jump.hunter", p.position());
        check(h, AbilityService.use(p, AbilitySlot.JUMP) == AbilityService.Result.FAILED, "Same-tick duplicate rejected");
        silent(h, TestPlayers.outbound(listener));
        blinkPackets(h, listener);
        h.runAfterDelay(2, () -> {
            check(h, AbilityService.use(p, AbilitySlot.JUMP) == AbilityService.Result.FAILED, "Spent airborne jump rejected");
            silent(h, TestPlayers.outbound(listener));
            h.succeed();
        });
    }

    private static void blinkPackets(GameTestHelper h, ServerPlayer listener) {
        var p = owner(h, GuardianClass.HUNTER, new Vec3(2.5, 3, 3.5));
        selectJump(p, JumpAbilities.HUNTER_BLINK);
        var before = p.position();
        accepted(h, p, AbilitySlot.JUMP);
        var wire = TestPlayers.outbound(listener);
        var sounds = packets(wire, ClientboundSoundPacket.class);
        check(h, sounds.size() == 2 && before.distanceTo(p.position()) > .25, "Successful blink moves and emits two cues");
        at(h, sounds.get(0), "jump.blink.out", before);
        at(h, sounds.get(1), "jump.blink.in", p.position());
        check(h, packets(wire, ClientboundSoundEntityPacket.class).isEmpty()
                        && packets(wire, ClientboundStopSoundPacket.class).isEmpty(), "Blink uses only two positional one-shots");
        var blocked = owner(h, GuardianClass.HUNTER, new Vec3(2.65, 3, 8.5));
        selectJump(blocked, JumpAbilities.HUNTER_BLINK);
        h.setBlock(3, 3, 8, Blocks.STONE);
        h.setBlock(3, 4, 8, Blocks.STONE);
        var wallOrigin = blocked.position();
        check(h, AbilityService.use(blocked, AbilitySlot.JUMP) == AbilityService.Result.FAILED
                        && blocked.position().equals(wallOrigin), "Full-height wall rejects movement");
        silent(h, TestPlayers.outbound(listener));
    }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_isolated", maxTicks = 25)
    public void continuousStartsRoundTripCodecAndStopOnSecondPressOrLandingWithoutRestarts(GameTestHelper h) {
        var listener = ear(h);
        var owners = continuousPair(h);
        var starts = new ArrayList<ClientboundSoundEntityPacket>();
        var landingOwners = continuousPair(h);
        var landingStarts = new ArrayList<ClientboundSoundEntityPacket>();
        for (var p : owners) {
            var sound = start(h, p, listener);
            starts.add(sound);
            var buffer = new RegistryFriendlyByteBuf(Unpooled.buffer(), h.getLevel().registryAccess());
            try {
                ClientboundSoundEntityPacket.STREAM_CODEC.encode(buffer, sound);
                var decoded = ClientboundSoundEntityPacket.STREAM_CODEC.decode(buffer);
                check(h, decoded.getSound().kind() == Holder.Kind.DIRECT
                                && decoded.getSound().value().location().equals(sound.getSound().value().location())
                                && decoded.getId() == p.getId() && decoded.getSource() == sound.getSource()
                                && decoded.getVolume() == sound.getVolume() && decoded.getPitch() == sound.getPitch()
                                && decoded.getSeed() == sound.getSeed() && buffer.readableBytes() == 0,
                        "Actual outbound packet survives vanilla inline entity-sound codec");
            } finally { buffer.release(); }
            check(h, AbilityService.use(p, AbilitySlot.JUMP) == AbilityService.Result.FAILED, "Duplicate press cannot restart or stop");
            silent(h, TestPlayers.outbound(listener));
        }
        h.runAfterDelay(4, () -> {
            silent(h, TestPlayers.outbound(listener));
            for (int i = 0; i < owners.size(); i++) {
                accepted(h, owners.get(i), AbilitySlot.JUMP);
                stopped(h, TestPlayers.outbound(listener), starts.get(i));
                inactive(h, owners.get(i));
            }
            for (var p : landingOwners) {
                landingStarts.add(start(h, p, listener));
                p.setOnGround(true);
            }
        });
        h.runAfterDelay(8, () -> {
            stopped(h, TestPlayers.outbound(listener), landingStarts.toArray(ClientboundSoundEntityPacket[]::new));
            landingOwners.forEach(p -> inactive(h, p));
        });
        h.runAfterDelay(12, () -> { silent(h, TestPlayers.outbound(listener)); h.succeed(); });
    }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_isolated", maxTicks = 20)
    public void menuLoadoutDeathAndDisconnectCancelOnlyOwnedPlayback(GameTestHelper h) {
        var listener = ear(h);
        var owners = continuousPair(h);
        var lift = start(h, owners.get(0), listener);
        var glide = start(h, owners.get(1), listener);
        AbilityService.cleanup(owners.get(0)); // Menu/service cleanup contract, not a synthetic GUI open.
        stopped(h, TestPlayers.outbound(listener), lift);
        check(h, CharacterLoadouts.selectSubclass(owners.get(1), Element.SOLAR) == null,
                "Real loadout service accepts subclass change");
        stopped(h, TestPlayers.outbound(listener), glide);
        owners.forEach(p -> { inactive(h, p); AbilityService.cleanup(p); });
        var departing = continuousPair(h);
        var dead = departing.get(0);
        var disconnected = departing.get(1);
        var deathVoice = start(h, dead, listener);
        var disconnectVoice = start(h, disconnected, listener);
        dead.setHealth(0);
        ServerLivingEntityEvents.AFTER_DEATH.invoker().afterDeath(dead, dead.damageSources().generic());
        stopped(h, TestPlayers.outbound(listener), deathVoice);
        ServerPlayConnectionEvents.DISCONNECT.invoker().onPlayDisconnect(disconnected.connection, h.getLevel().getServer());
        stopped(h, TestPlayers.outbound(listener), disconnectVoice);
        departing.forEach(p -> { inactive(h, p); AbilityService.cleanup(p); });
        h.runAfterDelay(5, () -> { silent(h, TestPlayers.outbound(listener)); h.succeed(); });
    }


    @GameTest(structure = FLOOR, environment = "destiny-test:w90_isolated", maxTicks = 130)
    public void sameKindAliasesStayIndependentUntilNaturalFuelExpiry(GameTestHelper h) {
        var listener = ear(h);
        var survivors = new ArrayList<ServerPlayer>();
        var remaining = new ArrayList<ClientboundSoundEntityPacket>();
        for (var cls : List.of(GuardianClass.TITAN, GuardianClass.WARLOCK)) {
            var a = owner(h, cls, new Vec3(2.5, 3, 3.5));
            var b = owner(h, cls, new Vec3(4.5, 3, 3.5));
            var first = start(h, a, listener);
            var second = start(h, b, listener);
            check(h, !first.getSound().value().location().equals(second.getSound().value().location()),
                    "Concurrent same-kind casters reserve different event keys");
            AbilityService.cleanup(a);
            stopped(h, TestPlayers.outbound(listener), first);
            survivors.add(b);
            remaining.add(second);
        }
        h.runAfterDelay(5, () -> {
            silent(h, TestPlayers.outbound(listener));
            for (int i = 0; i < survivors.size(); i++) {
                var p = survivors.get(i);
                check(h, JumpAbilities.active(p, i == 0 ? Kind.LIFT : Kind.GLIDE), "Other caster remains active after ticks");

            }
        });
        // Production caps fuel at 100 ticks. Retain every packet through real server progression.
        h.runAfterDelay(110, () -> {
            stopped(h, TestPlayers.outbound(listener), remaining.toArray(ClientboundSoundEntityPacket[]::new));
            survivors.forEach(p -> {
                inactive(h, p);
                check(h, AbilityService.use(p, AbilitySlot.JUMP) == AbilityService.Result.FAILED,
                        "Expired airborne fuel cannot start another voice");
            });
            silent(h, TestPlayers.outbound(listener));
        });
        h.runAfterDelay(115, () -> { silent(h, TestPlayers.outbound(listener)); h.succeed(); });
    }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_isolated", maxTicks = 25)
    public void gamblerAndMarksmanSoundAtAcceptanceNotAtDelayedContactAndRejectSilently(GameTestHelper h) {
        var listener = ear(h);
        for (var element : List.of(Element.ARC, Element.SOLAR)) {
            var p = owner(h, GuardianClass.HUNTER, new Vec3(2.5, 1, element == Element.ARC ? 3.5 : 8.5));
            Guardians.data(p).setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(element));
            p.setOnGround(true);
            accepted(h, p, AbilitySlot.CLASS_ABILITY);
            oneAt(h, TestPlayers.outbound(listener), element == Element.ARC
                    ? "class.hunter.dodge.gambler" : "class.hunter.dodge.marksman", p.position());
            check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.COOLDOWN,
                    "Second dodge rejected on cooldown");
            silent(h, TestPlayers.outbound(listener));
        }
        h.runAfterDelay(8, () -> {
            silent(h, TestPlayers.outbound(listener)); // Also rejects a delayed legacy hunter.dodge cue.
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_isolated", maxTicks = 520)
    public void healingRiftPrecastPrecedesContactAndOnlyNaturalExpiryEmitsEnd(GameTestHelper h) {
        var listener = ear(h);
        // Rift validates real collision support; do not rely on floor.nbt covering these positions.
        for (int x : new int[]{2, 6, 10}) h.setBlock(x, 0, 6, Blocks.STONE);
        var natural = owner(h, GuardianClass.WARLOCK, new Vec3(2.5, 1, 6.5));
        var cancelledBefore = owner(h, GuardianClass.WARLOCK, new Vec3(6.5, 1, 6.5));
        var cancelledAfter = owner(h, GuardianClass.WARLOCK, new Vec3(10.5, 1, 6.5));
        check(h, AbilityService.use(natural, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.FAILED,
                "Airborne rift rejected before precast");
        silent(h, TestPlayers.outbound(listener));
        var owners = List.of(natural, cancelledBefore, cancelledAfter);
        for (var p : owners) {
            p.setOnGround(true);
            p.setHealth(12);
            accepted(h, p, AbilitySlot.CLASS_ABILITY);
            oneAt(h, TestPlayers.outbound(listener), "class.warlock.rift.precast", p.position());
            check(h, ClassAbilityCast.active(p) && !WarlockClassAbility.active(p), "Precast precedes field contact");
        }
        AbilityService.cleanup(cancelledBefore);
        silent(h, TestPlayers.outbound(listener));
        // Keep only these fixtures' modeled camera input alive, as in ClassAbilityW255GameTests.
        h.onEachTick(() -> owners.forEach(p -> {
            if (SuperCamera.active(p)) p.connection.handleMovePlayer(
                    new ServerboundMovePlayerPacket.Rot(p.getYRot(), p.getXRot(), true, false));
        }));
        int contact = ClassAbilityTiming.of("class_warlock_healing").contactTicks();
        h.runAfterDelay(Math.max(1, contact - 2), () -> {
            silent(h, TestPlayers.outbound(listener));
            owners.forEach(p -> check(h, !WarlockClassAbility.active(p), "No field before authored contact"));
        });
        h.runAfterDelay(contact + 2, () -> {
            check(h, WarlockClassAbility.active(natural) && WarlockClassAbility.active(cancelledAfter)
                            && !WarlockClassAbility.active(cancelledBefore), "Only uncancelled casts create healing fields");
            var wire = TestPlayers.outbound(listener);
            var sounds = packets(wire, ClientboundSoundPacket.class);
            check(h, sounds.size() == 2, "Exactly two healing contact cues, no cancelled ghost or early end");
            for (var p : List.of(natural, cancelledAfter)) {
                var origin = WarlockClassAbility.origin(p);
                var matching = sounds.stream().filter(s -> Math.abs(s.getX() - origin.x) <= .125).toList();
                check(h, matching.size() == 1, "One contact cue per actual field origin");
                at(h, matching.getFirst(), "class.warlock.rift.healing", origin);
            }
            check(h, packets(wire, ClientboundSoundEntityPacket.class).isEmpty()
                            && packets(wire, ClientboundStopSoundPacket.class).isEmpty(), "Rift contacts are positional one-shots");
            AbilityService.cleanup(cancelledAfter);
            silent(h, TestPlayers.outbound(listener));
        });
        // Production caps field lifetime at 400 ticks; do not rewrite age or invoke a global tick.
        h.runAfterDelay(contact + 410, () -> {
            oneAt(h, TestPlayers.outbound(listener), "class.warlock.rift.end", natural.position().add(0, .04, 0));
            owners.forEach(p -> check(h, !WarlockClassAbility.active(p), "All expired/cancelled fields retired"));
            owners.forEach(AbilityService::cleanup);
            silent(h, TestPlayers.outbound(listener));
            h.succeed();
        });
    }
}
