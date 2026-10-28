package kim.biryeong.destiny.sound;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Pack-backed one-shots, encoded inline: no custom registry synchronization on vanilla clients. */
public final class DestinySounds {
    public static final double AUDIBLE_RADIUS = 32;
    private static final Set<String> EVENTS = load();
    private static final boolean QA_TRACE = Boolean.getBoolean("destiny.sound.qa");
    private DestinySounds() { }

    private static Set<String> load() {
        var stream = DestinySounds.class.getResourceAsStream("/assets/destiny/sounds.json");
        if (stream == null) throw new IllegalStateException("Missing Destiny sound definitions");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var root = JsonParser.parseReader(reader).getAsJsonObject();
            var keys = new TreeSet<String>();
            for (var e : root.entrySet()) {
                if (!e.getKey().matches("[a-z0-9_.]+")
                        || !e.getValue().getAsJsonObject().has("sounds")
                        || e.getValue().getAsJsonObject().getAsJsonArray("sounds").isEmpty())
                    throw new IllegalStateException("Invalid sound definition: " + e.getKey());
                keys.add(e.getKey());
            }
            return Collections.unmodifiableSet(keys);
        } catch (java.io.IOException failure) {
            throw new IllegalStateException("Unreadable Destiny sounds", failure);
        }
    }

    public static Set<String> events() { return EVENTS; }
    public static boolean has(String key) { return EVENTS.contains(key); }

    /** Public to test the actual vanilla inline codec, not an invented registry substitute. */
    public static ClientboundSoundPacket packet(String key, Vec3 position, SoundSource source,
                                                float volume, long seed) {
        if (!has(key)) throw new IllegalArgumentException("Unmapped Destiny sound: " + key);
        if (!Double.isFinite(position.x) || !Double.isFinite(position.y) || !Double.isFinite(position.z)
                || !Float.isFinite(volume) || volume <= 0 || volume > 1)
            throw new IllegalArgumentException("Invalid sound position/volume");
        return new ClientboundSoundPacket(Holder.direct(SoundEvent.createFixedRangeEvent(
                DestinyGuardians.id(key), (float) AUDIBLE_RADIUS)), source,
                position.x, position.y, position.z, volume, 1f, seed);
    }

    public static boolean canHear(ServerPlayer listener, ServerLevel level, Vec3 position) {
        return listener.level() == level && listener.position().distanceToSqr(position) <= AUDIBLE_RADIUS * AUDIBLE_RADIUS;
    }

    /** True means mapped and dispatched (possibly zero nearby listeners), not audible-output proof. */
    public static boolean at(ServerLevel level, Vec3 position, String key, float volume) {
        if (!has(key)) return false;
        var packet = packet(key, position, SoundSource.PLAYERS, volume, level.getRandom().nextLong());
        for (var listener : level.players()) if (canHear(listener, level, position)) send(listener, packet);
        return true;
    }

    private static void send(ServerPlayer listener, ClientboundSoundPacket packet) {
        listener.connection.send(packet);
        // Explicit QA only; a server queue log is not evidence of client decode or acoustic output.
        if (QA_TRACE) DestinyGuardians.LOGGER.info("[W33 sound QA] receiver={} event={} x={} y={} z={}",
                listener.getScoreboardName(), packet.getSound().value().location(), packet.getX(), packet.getY(), packet.getZ());
    }

    public static boolean weapon(ServerPlayer player, String family, String action) {
        return at(player.level(), player.getEyePosition(), "weapon." + family + "." + action, .8f);
    }

    /** Named-source alias only for an exact catalog ID; all other models use their documented family source. */
    public static String weaponKey(kim.biryeong.destiny.weapon.WeaponCatalog.Entry entry, String action) {
        String exact = "weapon." + entry.id() + "." + action;
        return has(exact) ? exact : "weapon." + entry.family() + "." + action;
    }

    public static boolean weapon(ServerPlayer player, kim.biryeong.destiny.weapon.WeaponCatalog.Entry entry, String action) {
        return at(player.level(), player.getEyePosition(), weaponKey(entry, action), .8f);
    }

    public static boolean hunter(ServerLevel level, Vec3 position, Element element, String action, float volume) {
        return at(level, position, "hunter." + element.getSerializedName() + "." + action, volume);
    }

    /** Explicit native fallback only when the supplied archive has no selected mapping. */
    public static void hunterOrVanilla(ServerLevel level, Vec3 position, Element element, String action,
                                       SoundEvent fallback, float volume, float fallbackPitch) {
        if (!hunter(level, position, element, action, volume))
            kim.biryeong.destiny.fx.Fx.sound(level, position, fallback, volume, fallbackPitch);
    }

    public static void orVanilla(ServerLevel level, Vec3 position, String key,
                                 SoundEvent fallback, float volume, float fallbackPitch) {
        if (!at(level, position, key, volume))
            kim.biryeong.destiny.fx.Fx.sound(level, position, fallback, volume, fallbackPitch);
    }

    /** Personal HUD edge only. Never broadcasts another player's full-charge notification. */
    public static boolean ready(ServerPlayer player) {
        return personal(player, "ui.super_ready", .65f);
    }

    public static boolean personal(ServerPlayer player, String key, float volume) {
        if (!has(key)) return false;
        send(player, packet(key, player.getEyePosition(), SoundSource.PLAYERS,
                volume, player.level().getRandom().nextLong()));
        return true;
    }
}
