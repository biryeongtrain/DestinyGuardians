package kim.biryeong.destiny.test;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.TextDisplayElement;
import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.destiny.fx.WeaponDamageNumbers;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.network.protocol.game.GameProtocols;
import net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.List;

/** W43 sidecar regressions. Register this class in the gametest entrypoint separately. */
public final class WeaponDamageNumbersW43GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String GLOBAL_CAP_PROPERTY = "destiny.test.w43.globalCap";
    // Fabric 26.3 joins class/method with '_' and converts camel case to snake case.
    private static final String GLOBAL_CAP_TEST_ID = "destiny-test:weapon_damage_numbers_w43game_tests_"
            + "global_cap_evicts_and_destroys_oldest_holders";

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h) {
        WeaponDamageNumbers.init();
        var owner = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, 0);
        TestCleanup.register(h, () -> {
            WeaponDamageNumbers.cleanup(owner);
            TestPlayers.remove(owner);
        });
        return owner;
    }

    // Observe actual Polymer holders without adding test/debug methods to the production API.
    private static Object field(Class<?> type, Object receiver, String name) {
        try {
            var field = type.getDeclaredField(name);
            field.setAccessible(true);
            return field.get(receiver);
        } catch (ReflectiveOperationException e) {
            throw new AssertionError("W43 fixture field " + name, e);
        }
    }

    private static List<ElementHolder> numbers(ServerPlayer owner) {
        var result = new ArrayList<ElementHolder>();
        var queue = (Iterable<?>) field(WeaponDamageNumbers.class, null, "NUMBERS");
        for (var value : queue) {
            if (field(value.getClass(), value, "owner") == owner) result.add((ElementHolder) value);
        }
        return result;
    }

    private static int constant(String name) {
        return (int) field(WeaponDamageNumbers.class, null, name);
    }

    private static void tick(GameTestHelper h) {
        try {
            var tick = WeaponDamageNumbers.class.getDeclaredMethod("tick", MinecraftServer.class);
            tick.setAccessible(true);
            tick.invoke(null, h.getLevel().getServer());
        } catch (InvocationTargetException e) {
            throw new AssertionError("W43 display tick", e.getCause());
        } catch (ReflectiveOperationException e) {
            throw new AssertionError("W43 display tick fixture", e);
        }
    }

    private static TextDisplayElement text(ElementHolder holder) {
        return (TextDisplayElement) holder.getElements().getFirst();
    }

    private static void flatten(Packet<?> packet, List<Packet<?>> result) {
        if (packet instanceof BundlePacket<?> bundle) {
            for (var child : bundle.subPackets()) flatten(child, result);
        } else {
            result.add(packet);
        }
    }

    private static List<Packet<?>> outbound(ServerPlayer owner) {
        var result = new ArrayList<Packet<?>>();
        for (var packet : TestPlayers.outbound(owner)) flatten(packet, result);
        return result;
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void ownerAloneWatchesAndReceivesRealDisplayPackets(GameTestHelper h) {
        var owner = player(h);
        var nearby = player(h);
        TestPlayers.drain(owner);
        TestPlayers.drain(nearby);
        WeaponDamageNumbers.confirm(owner, h.getLevel(), owner.position(), 4.4f, false);
        check(h, WeaponDamageNumbers.active(owner) == 1, "Confirmed damage creates one display");
        var holder = numbers(owner).getFirst();
        check(h, holder.getAttachment() instanceof ManualAttachment, "Private number uses manual attachment");
        check(h, holder.getWatchingPlayers().size() == 1 && holder.getWatchingPlayers().contains(owner.connection),
                "Only the exact owner's connection watches the entity IDs");
        check(h, !holder.startWatching(nearby), "A nearby connection cannot opt into the private holder");
        var ids = holder.getEntityIds();
        check(h, outbound(owner).stream().anyMatch(packet -> packet instanceof ClientboundAddEntityPacket add
                        && ids.contains(add.getId()) && add.getType() == EntityTypes.TEXT_DISPLAY),
                "Owner receives an actual text display spawn packet");
        check(h, outbound(nearby).stream().noneMatch(packet -> packet instanceof ClientboundAddEntityPacket add
                        && ids.contains(add.getId())), "Bystander receives none of the private entity spawns");
        WeaponDamageNumbers.cleanup(owner);
        check(h, holder.getAttachment() == null && holder.getWatchingPlayers().isEmpty(), "Cleanup detaches and unwatches");
        check(h, outbound(owner).stream().anyMatch(packet -> packet instanceof ClientboundRemoveEntitiesPacket remove
                        && remove.entityIds().intStream().anyMatch(ids::contains)), "Owner receives actual removal packet");
        check(h, !holder.startWatching(owner), "Destroyed numbers cannot resume watching");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void textRoundsObservedMinecraftHpAndKeepsBodyWhitePrecisionYellow(GameTestHelper h) {
        var owner = player(h);
        float hp = owner.getHealth(), absorption = owner.getAbsorptionAmount();
        Vec3 position = owner.position(), velocity = owner.getDeltaMovement();
        WeaponDamageNumbers.confirm(owner, h.getLevel(), position, .01f, false);
        WeaponDamageNumbers.confirm(owner, h.getLevel(), position, 2.5f, true);
        WeaponDamageNumbers.confirm(owner, h.getLevel(), position, Float.MAX_VALUE, false);
        var holders = numbers(owner);
        var body = text(holders.get(0));
        var precision = text(holders.get(1));
        check(h, body.getText().getString().equals("1") && precision.getText().getString().equals("3"),
                "Positive sub-HP delta shows minimum 1; observed 2.5 HP rounds to 3");
        check(h, TextColor.WHITE.equals(body.getText().getStyle().getColor())
                        && TextColor.YELLOW.equals(precision.getText().getStyle().getColor()),
                "Body text is white and precision text is yellow");
        check(h, text(holders.get(2)).getText().getString().equals(Integer.toString(Integer.MAX_VALUE)),
                "Extreme finite damage keeps a bounded integer string");
        check(h, body.getBackground() == 0 && !body.getDefaultBackground() && !body.getSeeThrough(),
                "No opaque panel or through-wall hit marker");
        check(h, owner.getHealth() == hp && owner.getAbsorptionAmount() == absorption
                        && owner.position().equals(position) && owner.getDeltaMovement().equals(velocity),
                "Display feedback does not change health, absorption, position or motion");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void invalidOrUnconfirmedDamageAndUnsafeImpactsCreateNothing(GameTestHelper h) {
        var owner = player(h);
        check(h, WeaponDamageNumbers.active(owner) == 0, "Without confirmation there are no numbers");
        for (float damage : new float[]{0, -0.0f, -1, Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY}) {
            WeaponDamageNumbers.confirm(owner, h.getLevel(), owner.position(), damage, true);
        }
        for (var impact : new Vec3[]{null, new Vec3(Double.NaN, 1, 0), new Vec3(0, Double.POSITIVE_INFINITY, 0),
                new Vec3(0, 1, Double.NEGATIVE_INFINITY), new Vec3(Double.MAX_VALUE, 1, 0),
                new Vec3(0, 10_000, 0), new Vec3(29_000_000, 64, 29_000_000)}) {
            WeaponDamageNumbers.confirm(owner, h.getLevel(), impact, 2, false);
        }
        var unloaded = new net.minecraft.core.BlockPos(29_000_000, 64, 29_000_000);
        check(h, !h.getLevel().hasChunkAt(unloaded), "Rejected remote impact never loads a chunk");
        WeaponDamageNumbers.confirm(null, h.getLevel(), owner.position(), 2, false);
        WeaponDamageNumbers.confirm(owner, null, owner.position(), 2, false);
        owner.setGameMode(GameType.SPECTATOR);
        WeaponDamageNumbers.confirm(owner, h.getLevel(), owner.position(), 2, false);
        owner.setGameMode(GameType.SURVIVAL);
        check(h, WeaponDamageNumbers.active(owner) == 0 && numbers(owner).isEmpty(),
                "Invalid values, missing owner/level and spectator confirmation produce no holders");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void ownerCapEvictsAndDestroysOldestHolder(GameTestHelper h) {
        int perOwner = constant("MAX_PER_OWNER");
        check(h, perOwner > 0 && perOwner <= 24, "Owner scene limit stays bounded");
        var firstOwner = player(h);
        WeaponDamageNumbers.confirm(firstOwner, h.getLevel(), firstOwner.position(), 1, false);
        var oldest = numbers(firstOwner).getFirst();
        for (int i = 0; i < perOwner + 2; i++) {
            WeaponDamageNumbers.confirm(firstOwner, h.getLevel(), firstOwner.position(), 1, false);
        }
        check(h, WeaponDamageNumbers.active(firstOwner) == perOwner && oldest.getAttachment() == null
                        && oldest.getWatchingPlayers().isEmpty(), "Per-owner overflow destroys the oldest actual holder");
        h.succeed();
    }

    // Default runs deliberately do no cap work here. Actual cap coverage requires BOTH server JVM flags:
    // -Ddestiny.test.w43.globalCap=true
    // -Dfabric-api.gametest.filter=destiny-test:weapon_damage_numbers_w43game_tests_global_cap_evicts_and_destroys_oldest_holders
    // manualOnly cannot be used: the 26.3 headless runner excludes it even with an exact filter.
    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void globalCapEvictsAndDestroysOldestHolders(GameTestHelper h) {
        if (!Boolean.getBoolean(GLOBAL_CAP_PROPERTY)) {
            h.succeed();
            return;
        }
        check(h, GLOBAL_CAP_TEST_ID.equals(System.getProperty("fabric-api.gametest.filter")),
                "Global-cap opt-in requires an exact single-test filter; a shared batch must never evict other tests' displays");
        int perOwner = constant("MAX_PER_OWNER"), global = constant("MAX_GLOBAL");
        check(h, global >= perOwner && global <= 256, "Global scene limit stays bounded");
        var firstOwner = player(h);
        for (int i = 0; i < perOwner; i++) {
            WeaponDamageNumbers.confirm(firstOwner, h.getLevel(), firstOwner.position(), 1, false);
        }
        var globalOldest = numbers(firstOwner).getFirst();
        var owners = new ArrayList<ServerPlayer>();
        owners.add(firstOwner);
        for (int i = 0; i < global / perOwner + 1; i++) {
            var owner = player(h);
            owners.add(owner);
            for (int j = 0; j < perOwner; j++) {
                WeaponDamageNumbers.confirm(owner, h.getLevel(), owner.position(), 1, false);
            }
        }
        int count = owners.stream().mapToInt(WeaponDamageNumbers::active).sum();
        check(h, count == global && globalOldest.getAttachment() == null && globalOldest.getWatchingPlayers().isEmpty(),
                "Global overflow destroys the oldest holder without exceeding the bound");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void lifetimeUsesSixteenServerTicksAndFloatsUpOncePerTick(GameTestHelper h) {
        var owner = player(h);
        WeaponDamageNumbers.confirm(owner, h.getLevel(), owner.position(), 3, false);
        var holder = numbers(owner).getFirst();
        float startY = text(holder).getTranslation().y();
        h.runAfterDelay(5, () -> {
            tick(h);
            float y = text(holder).getTranslation().y();
            check(h, y > startY, "Number floats upward on server ticks");
            tick(h);
            tick(h);
            check(h, text(holder).getTranslation().y() == y && WeaponDamageNumbers.active(owner) == 1,
                    "Repeated same-tick updates cannot accelerate rise or consume lifetime");
        });
        int lifetime = constant("LIFETIME_TICKS");
        h.runAfterDelay(lifetime - 1, () -> {
            tick(h);
            check(h, WeaponDamageNumbers.active(owner) == 1, "Number survives until its full lifetime");
        });
        h.runAfterDelay(lifetime, () -> {
            tick(h);
            check(h, WeaponDamageNumbers.active(owner) == 0 && holder.getAttachment() == null
                            && holder.getWatchingPlayers().isEmpty(), "Tick 16 destroys holder, attachment and watcher");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void cleanupAndOldRespawnSessionCannotEraseReplacementWithSameUuid(GameTestHelper h) {
        var oldOwner = player(h);
        var replacement = player(h);
        var other = player(h);
        var originalUuid = replacement.getUUID();
        try {
            replacement.setUUID(oldOwner.getUUID());
            for (var owner : List.of(oldOwner, replacement, other)) {
                WeaponDamageNumbers.confirm(owner, h.getLevel(), owner.position(), 2, false);
            }
            var oldHolder = numbers(oldOwner).getFirst();
            WeaponDamageNumbers.cleanup(oldOwner);
            WeaponDamageNumbers.cleanup(oldOwner);
            check(h, oldHolder.getAttachment() == null && WeaponDamageNumbers.active(oldOwner) == 0,
                    "Old-session cleanup is idempotent and releases its holder");

            WeaponDamageNumbers.confirm(oldOwner, h.getLevel(), oldOwner.position(), 2, false);
            check(h, numbers(oldOwner).size() == 1, "Respawn fixture has a live old-session display before the event");
            var respawnHolder = numbers(oldOwner).getFirst();
            // A same-level alive respawn isolates listener/object ownership. A death respawn
            // invokes TowerSpawnWorld.teleport, legitimately invalidating level-bound displays.
            ServerPlayerEvents.AFTER_RESPAWN.invoker().afterRespawn(oldOwner, replacement, true);
            check(h, respawnHolder.getAttachment() == null && respawnHolder.getWatchingPlayers().isEmpty()
                            && numbers(oldOwner).isEmpty(), "Respawn event itself destroys the old-session holder");
            check(h, WeaponDamageNumbers.active(replacement) == 1 && WeaponDamageNumbers.active(other) == 1,
                    "Replacement with the same UUID and unrelated owner retain their displays");

            // Keep the death-respawn listener branch covered as well. Its tower transfer
            // may invalidate the replacement's level-bound holder, but never another owner.
            WeaponDamageNumbers.confirm(oldOwner, h.getLevel(), oldOwner.position(), 2, false);
            var deathHolder = numbers(oldOwner).getFirst();
            var replacementHolder = numbers(replacement).getFirst();
            var displayLevel = replacement.level();
            ServerPlayerEvents.AFTER_RESPAWN.invoker().afterRespawn(oldOwner, replacement, false);
            check(h, deathHolder.getAttachment() == null && deathHolder.getWatchingPlayers().isEmpty()
                            && numbers(oldOwner).isEmpty(), "Death respawn also destroys the old-session holder");
            check(h, WeaponDamageNumbers.active(other) == 1,
                    "Death respawn and any tower transfer preserve the unrelated owner's display");
            if (replacement.level() != displayLevel || replacement.isChangingDimension()) {
                check(h, WeaponDamageNumbers.active(replacement) == 0
                                && replacementHolder.getAttachment() == null
                                && replacementHolder.getWatchingPlayers().isEmpty(),
                        "A transferred replacement releases its old-level holder and watcher");
            } else {
                check(h, WeaponDamageNumbers.active(replacement) == 1,
                        "Without a level transfer death respawn also preserves replacement identity ownership");
            }
        } finally {
            replacement.setUUID(originalUuid);
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void deadDisconnectedSpectatorAndChangedConnectionOwnersAreCleaned(GameTestHelper h) {
        var dead = player(h);
        var disconnected = player(h);
        var spectator = player(h);
        var changed = player(h);
        for (var owner : List.of(dead, disconnected, spectator, changed)) {
            WeaponDamageNumbers.confirm(owner, h.getLevel(), owner.position(), 2, false);
        }
        var deadHolder = numbers(dead).getFirst();
        dead.hurtServer(h.getLevel(), dead.damageSources().genericKill(), 10_000);
        check(h, dead.isDeadOrDying() && deadHolder.getAttachment() == null, "Actual death event destroys the display immediately");
        ServerPlayConnectionEvents.DISCONNECT.invoker().onPlayDisconnect(disconnected.connection, h.getLevel().getServer());
        check(h, numbers(disconnected).isEmpty(), "Disconnect event removes transient displays");
        // Closing the EmbeddedChannel additionally exercises the tick guard, without an event.
        WeaponDamageNumbers.confirm(disconnected, h.getLevel(), disconnected.position(), 2, false);
        TestPlayers.remove(disconnected);
        WeaponDamageNumbers.confirm(disconnected, h.getLevel(), disconnected.position(), 2, false);
        spectator.setGameMode(GameType.SPECTATOR);
        var original = changed.connection;
        var oldSessionHolder = numbers(changed).getFirst();
        var server = h.getLevel().getServer();
        var connection = new Connection(PacketFlow.SERVERBOUND);
        var channel = new EmbeddedChannel(connection);
        try {
            var cookie = CommonListenerCookie.createInitial(changed.getGameProfile(), false);
            var replacement = new ServerGamePacketListenerImpl(server, connection, changed, cookie);
            connection.setupInboundProtocol(GameProtocols.SERVERBOUND_TEMPLATE.bind(
                    RegistryFriendlyByteBuf.decorator(server.registryAccess()), replacement), replacement);
            changed.connection = replacement;
            replacement.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());
            check(h, replacement != original && replacement.getPlayer() == changed && replacement.isAcceptingMessages()
                            && !changed.hasDisconnected() && changed.isAlive() && !changed.isSpectator(),
                    "Replacement is a live, eligible listener for the same player, not another player's listener");
            check(h, !oldSessionHolder.startWatching(changed), "An old-session holder cannot enroll the new owner listener");
            tick(h);
            check(h, numbers(disconnected).isEmpty() && numbers(spectator).isEmpty() && numbers(changed).isEmpty(),
                    "Closed connection, spectator and replaced listener invalidate existing displays");
            check(h, oldSessionHolder.getAttachment() == null && oldSessionHolder.getWatchingPlayers().isEmpty(),
                    "Captured-session mismatch destroys and unwatches the old holder");

            WeaponDamageNumbers.confirm(changed, h.getLevel(), changed.position(), 2, false);
            check(h, numbers(changed).size() == 1, "The same player can confirm damage through the valid replacement listener");
            var newSessionHolder = numbers(changed).getFirst();
            ServerPlayConnectionEvents.DISCONNECT.invoker().onPlayDisconnect(original, server);
            check(h, numbers(changed).size() == 1 && newSessionHolder.getAttachment() != null
                            && newSessionHolder.getWatchingPlayers().size() == 1
                            && newSessionHolder.getWatchingPlayers().contains(replacement),
                    "A late old-listener disconnect preserves the new session's owner-only holder");
        } finally {
            WeaponDamageNumbers.cleanup(changed);
            changed.connection = original;
            channel.finishAndReleaseAll();
        }
        WeaponDamageNumbers.confirm(dead, h.getLevel(), dead.position(), 2, false);
        check(h, WeaponDamageNumbers.active(dead) == 0, "A dead owner cannot create another number");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void levelChangeEventAndTickGuardReleaseOldLevelDisplays(GameTestHelper h) {
        var eventOwner = player(h);
        var tickOwner = player(h);
        var from = h.getLevel();
        var other = from.getServer().getAllLevels().iterator();
        net.minecraft.server.level.ServerLevel to = null;
        while (other.hasNext()) {
            var level = other.next();
            if (level != from) { to = level; break; }
        }
        check(h, to != null, "An alternate test level is available");
        for (var owner : List.of(eventOwner, tickOwner)) {
            WeaponDamageNumbers.confirm(owner, from, owner.position(), 2, false);
        }
        var eventHolder = numbers(eventOwner).getFirst();
        var tickHolder = numbers(tickOwner).getFirst();
        try {
            eventOwner.setServerLevel(to);
            ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.invoker().afterChangeLevel(eventOwner, from, to);
            check(h, eventHolder.getAttachment() == null, "Level-change event immediately destroys old-level display");
            tickOwner.setServerLevel(to);
            WeaponDamageNumbers.confirm(tickOwner, from, tickOwner.position(), 2, false);
            tick(h);
            check(h, tickHolder.getAttachment() == null && WeaponDamageNumbers.active(tickOwner) == 0,
                    "Tick guard rejects wrong-level confirmation and removes stale level state");
        } finally {
            eventOwner.setServerLevel(from);
            tickOwner.setServerLevel(from);
        }
        h.succeed();
    }
}
