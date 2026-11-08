package kim.biryeong.destiny.activity.strike;

import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;

/**
 * Where a player stood before entering a strike. The record is persistent, so a restart, a crash or a reconnect after
 * the temporary world was deleted still brings the player home. One instance per strike: the attachment id
 * is the strike's own, so strikes never read each other's records.
 */
public final class StrikeReturn {
    private final AttachmentType<String> attachment;
    private final Predicate<Level> isStrikeLevel;
    private final String logTag;

    /** @param attachmentId registered once; changing it orphans return records saved by earlier versions */
    public StrikeReturn(String attachmentId, String logTag, Predicate<Level> isStrikeLevel) {
        this.attachment = AttachmentRegistry.create(DestinyGuardians.id(attachmentId), b -> b.persistent(Codec.STRING).copyOnDeath());
        this.logTag = Objects.requireNonNull(logTag);
        this.isStrikeLevel = Objects.requireNonNull(isStrikeLevel);
    }
    public boolean pending(ServerPlayer p) { return p.getAttached(attachment) != null; }
    /** Keeps the first record: re-entering from inside the strike must not overwrite the true origin. */
    public void save(ServerPlayer p) {
        if (pending(p)) return;
        p.setAttached(attachment, String.join("|", p.level().dimension().identifier().toString(),
                Double.toString(p.getX()), Double.toString(p.getY()), Double.toString(p.getZ()),
                Float.toString(p.getYRot()), Float.toString(p.getXRot()), p.gameMode.getGameModeForPlayer().getName()));
    }
    /** True when nothing was pending or the player is home again; false leaves the record for a later retry. */
    public boolean restore(ServerPlayer p, java.util.function.Consumer<ServerPlayer> cleanup) {
        String saved = p.getAttached(attachment);
        if (saved == null) return true;
        if (p.hasDisconnected()) return false;
        cleanup.accept(p);
        try {
            String[] a = saved.split("\\|", -1);
            ServerLevel target = p.level().getServer().getLevel(ResourceKey.create(Registries.DIMENSION, Identifier.parse(a[0])));
            if (target == null || isStrikeLevel.test(target)) target = p.level().getServer().overworld();
            Vec3 at = new Vec3(Double.parseDouble(a[1]), Double.parseDouble(a[2]), Double.parseDouble(a[3]));
            if (target == p.level().getServer().overworld() && !target.dimension().identifier().toString().equals(a[0]))
                at = Vec3.atBottomCenterOf(target.getRespawnData().pos());
            if (!Double.isFinite(at.x) || !Double.isFinite(at.y) || !Double.isFinite(at.z)) return false;
            if (!p.teleportTo(target, at.x, at.y, at.z, Set.of(), Float.parseFloat(a[4]), Float.parseFloat(a[5]), true)) return false;
            p.setGameMode(GameType.byName(a[6], GameType.SURVIVAL));
            p.removeAttached(attachment);
            return true;
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("[{}] return failed for {}", logTag, p.getUUID(), e);
            return false;
        }
    }
}
