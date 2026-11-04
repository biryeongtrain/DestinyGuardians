package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.TextDisplayElement;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.function.Predicate;

/**
 * Owner-only, cosmetic feedback for confirmed weapon damage. All calls use the server thread.
 * Numbers are rounded Minecraft HP (including lost absorption), not original Destiny 2 damage units.
 * This class never deals damage, awards resources, or creates hit markers.
 */
public final class WeaponDamageNumbers {
    private static final int LIFETIME_TICKS = 16;
    private static final int MAX_PER_OWNER = 24;
    private static final int MAX_GLOBAL = 256;
    private static final float RISE_PER_TICK = .025f;
    // One bounded queue avoids UUID-keyed state surviving replacement players or server instances.
    private static final ArrayDeque<NumberHolder> NUMBERS = new ArrayDeque<>();
    private static boolean initialized;

    private WeaponDamageNumbers() {}

    public static void init() {
        if (initialized) return;
        initialized = true;
        ServerTickEvents.END_SERVER_TICK.register(WeaponDamageNumbers::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) ->
                removeIf(number -> number.owner == handler.getPlayer() && number.session == handler));
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
            if (entity instanceof ServerPlayer owner) cleanup(owner);
        });
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((owner, from, to) -> cleanup(owner));
        ServerPlayerEvents.AFTER_RESPAWN.register((oldOwner, newOwner, alive) -> cleanup(oldOwner));
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> removeIf(number -> number.level.getServer() == server));
    }

    /**
     * Call only AFTER observing an actual decrease in the target's HP plus absorption.
     * Pass that observed positive delta, never requested/base damage or a hit prediction.
     * The color flag also accepts actual debuffed body hits (yellow), not a precision-perk claim.
     * Confirmation is the caller's responsibility: this display-only API cannot verify a target.
     */
    public static void confirm(ServerPlayer owner, ServerLevel level, Vec3 impact,
                               float actualDamage, boolean precision) {
        if (!initialized || !Float.isFinite(actualDamage) || actualDamage <= 0
                || level == null || !level.getServer().isSameThread()) return;
        if (!eligible(owner, level) || !safeImpact(level, impact)) return;
        prune(level.getServer(), false);

        if (active(owner) >= MAX_PER_OWNER) {
            for (var it = NUMBERS.iterator(); it.hasNext();) {
                var number = it.next();
                if (number.owner == owner) {
                    it.remove();
                    number.destroy();
                    break;
                }
            }
        }
        if (NUMBERS.size() >= MAX_GLOBAL) NUMBERS.removeFirst().destroy();

        var number = new NumberHolder(owner, level, impact, actualDamage, precision);
        // ManualAttachment never enrolls nearby players. Explicit watching is additionally guarded
        // by the exact owner connection in NumberHolder.startWatching.
        new ManualAttachment(number, level, () -> impact);
        if (number.startWatching(owner)) {
            NUMBERS.addLast(number);
            number.tick();
        } else {
            number.destroy();
        }
    }

    /** Idempotent; an old player object's cleanup cannot erase a replacement session's numbers. */
    public static void cleanup(ServerPlayer owner) {
        if (owner == null || !owner.level().getServer().isSameThread()) return;
        removeIf(number -> number.owner == owner);
    }

    /** Number of live displays belonging to this exact player/session, with no gameplay side effects. */
    public static int active(ServerPlayer owner) {
        if (owner == null || !owner.level().getServer().isSameThread()) return 0;
        prune(owner.level().getServer(), false);
        int count = 0;
        for (var number : NUMBERS) if (number.owner == owner) count++;
        return count;
    }

    private static boolean eligible(ServerPlayer owner, ServerLevel level) {
        if (owner == null || owner.level() != level || !owner.isAlive() || owner.isDeadOrDying()
                || owner.isRemoved() || owner.isSpectator() || owner.isChangingDimension()
                || owner.hasDisconnected() || owner.connection == null
                || owner.connection.getPlayer() != owner || !owner.connection.isAcceptingMessages()) return false;
        var current = level.getServer().getPlayerList().getPlayer(owner.getUUID());
        return current == null || current == owner;
    }

    private static boolean safeImpact(ServerLevel level, Vec3 impact) {
        if (impact == null || !Double.isFinite(impact.x) || !Double.isFinite(impact.y)
                || !Double.isFinite(impact.z)) return false;
        var pos = BlockPos.containing(impact);
        return level.isInWorldBounds(pos) && level.getWorldBorder().isWithinBounds(pos)
                && level.hasChunkAt(pos);
    }

    private static void tick(MinecraftServer server) {
        prune(server, true);
    }

    private static void prune(MinecraftServer server, boolean animate) {
        for (var it = NUMBERS.iterator(); it.hasNext();) {
            var number = it.next();
            if (number.level.getServer() != server) continue;
            // Server ticks, rather than level game time or packet frequency, own the lifetime.
            int age = server.getTickCount() - number.createdTick;
            if (age < 0 || age >= LIFETIME_TICKS || !eligible(number.owner, number.level)
                    || number.owner.connection != number.session || !safeImpact(number.level, number.impact)
                    || number.getAttachment() == null || !number.getWatchingPlayers().contains(number.session)) {
                it.remove();
                number.destroy();
            } else if (animate && number.lastAnimatedTick != server.getTickCount()) {
                number.lastAnimatedTick = server.getTickCount();
                number.layout(age);
                number.text.startInterpolation();
                number.tick();
            }
        }
    }

    private static void removeIf(Predicate<NumberHolder> predicate) {
        for (var it = NUMBERS.iterator(); it.hasNext();) {
            var number = it.next();
            if (predicate.test(number)) {
                it.remove();
                number.destroy();
            }
        }
    }

    /** Reserve only against this exact connection's CURRENT visible boxes. A fixed lift is
     * owned by the holder and rises with it; existing numbers never jump when another hit arrives.
     * Projecting current world anchors also catches separate nearby targets and different ranges
     * on the same sight line, unlike grouping by exact hit coordinates or only the current tick. */
    private static double lift(ServerPlayer owner, ServerLevel level, Vec3 impact, boolean precision, int digits) {
        var eye=owner.getEyePosition();
        if (!Double.isFinite(eye.x)||!Double.isFinite(eye.y)||!Double.isFinite(eye.z)
                || !Double.isFinite(owner.getYRot()) || !Double.isFinite(owner.getXRot()) || Math.abs(owner.getXRot())>90)
            return 0;
        var view=new DamageNumberLayout.View(new DamageNumberLayout.Point(eye.x,eye.y,eye.z),owner.getYRot(),owner.getXRot());
        var desired=DamageNumberLayout.project(view,new DamageNumberLayout.Point(impact.x,impact.y,impact.z),precision,0,0,digits);
        if (desired.isEmpty()) return 0;
        var occupied=new ArrayList<DamageNumberLayout.Box>();
        int now=level.getServer().getTickCount();
        for (var number:NUMBERS) {
            if (number.owner!=owner || number.session!=owner.connection || number.level!=level) continue;
            int age=now-number.createdTick;
            DamageNumberLayout.project(view,new DamageNumberLayout.Point(number.impact.x,number.impact.y,number.impact.z),
                    number.precision,age,number.lift,number.digits)
                    .ifPresent(p->occupied.add(DamageNumberLayout.relativeSweep(p,age,desired.get().angularScale())));
        }
        var projected=desired.get();
        double difference=DamageNumberLayout.packUp(projected.box(),occupied,DamageNumberLayout.GAP*projected.angularScale()).y()
                -projected.box().y();
        double result=difference/projected.angularScale();
        return Double.isFinite(result)&&result>=0?result:0;
    }

    private static final class NumberHolder extends ElementHolder {
        private final ServerPlayer owner;
        private final ServerGamePacketListenerImpl session;
        private final ServerLevel level;
        private final Vec3 impact;
        private final int createdTick;
        private final TextDisplayElement text;
        private final boolean precision;
        private final double lift;
        private final int digits;
        private int lastAnimatedTick;

        private NumberHolder(ServerPlayer owner, ServerLevel level, Vec3 impact,
                             float actualDamage, boolean precision) {
            this.owner = owner;
            this.session = owner.connection;
            this.level = level;
            this.impact = impact;
            this.precision = precision;
            this.createdTick = level.getServer().getTickCount();
            this.lastAnimatedTick = createdTick;
            // Math.round(float) saturates at Integer.MAX_VALUE, keeping even extreme finite
            // deltas to a bounded integer string; positive sub-HP damage still shows 1.
            String value=Integer.toString(Math.max(1,Math.round(actualDamage)));
            this.digits=value.length();
            this.lift=lift(owner,level,impact,precision,digits);
            text = new TextDisplayElement(Component.literal(value)
                    .withStyle(precision ? ChatFormatting.YELLOW : ChatFormatting.WHITE));
            text.setBillboardMode(Display.BillboardConstraints.CENTER);
            layout(0);
            text.setBrightness(new Brightness(15, 15));
            text.setBackground(0);
            text.setDefaultBackground(false);
            text.setShadow(true);
            text.setSeeThrough(false);
            text.setLineWidth(160);
            text.setViewRange(2);
            text.setInterpolationDuration(1);
            addElement(text);
        }

        /** Approximately fixed angular size, rather than unreadable one-pixel glyphs at range.
         * This uses the owner's eye, not exact client FOV/camera data; bounded server-side approximation. */
        private void layout(int age) {
            float distanceScale = (float)(Math.clamp(owner.getEyePosition().distanceTo(impact), 4, 96) / 7);
            text.setScale(new Vector3f((float)DamageNumberLayout.SCALE * distanceScale));
            // CENTER billboard rotates before its transform: these are screen-local axes.
            text.setTranslation(new Vector3f((precision ? .18f : -.18f) * distanceScale,
                    (float)(DamageNumberLayout.BASE_Y + age * RISE_PER_TICK + lift) * distanceScale, 0));
        }

        @Override
        public boolean startWatching(ServerGamePacketListenerImpl watcher) {
            return getAttachment() != null && watcher == session && owner.connection == session && eligible(owner, level)
                    && super.startWatching(watcher);
        }
    }
}
