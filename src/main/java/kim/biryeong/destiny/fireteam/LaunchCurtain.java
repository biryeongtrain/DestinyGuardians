package kim.biryeong.destiny.fireteam;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.minigamelib.mixin.ChunkSenderAccessor;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * One player's launch curtain: steps the world to black (post_effect fireteam/fade_5 … fade_1 → black), holds it
 * while the activity prepares, then fades back in once the client has loaded wherever it now stands. The ids are the
 * finder's own copies, so an activity's own curtain (same shader, different id) can overlap without either removing
 * the other's layer. Movement and jumping are frozen while dark.
 */
final class LaunchCurtain {
    static final Identifier BLACK = DestinyGuardians.id("fireteam/black");
    /** Brightest grade first; index STEPS.length is full black. */
    private static final Identifier[] STEPS = {
            DestinyGuardians.id("fireteam/fade_5"), DestinyGuardians.id("fireteam/fade_4"), DestinyGuardians.id("fireteam/fade_3"),
            DestinyGuardians.id("fireteam/fade_2"), DestinyGuardians.id("fireteam/fade_1"), BLACK};
    private static final Identifier FREEZE = DestinyGuardians.id("fireteam_launch");
    static final int SETTLE = 6;

    final ServerPlayer player;
    private int shown = -1, readyFor;
    private boolean released;

    LaunchCurtain(ServerPlayer player) { this.player = player; }

    /** Darkness level 0 (clear) .. 1 (black). Adds the next grade before removing the previous: never a bright frame. */
    void level(float darkness) {
        if (released || player.hasDisconnected()) return;
        int step = darkness <= 0 ? -1 : Math.min(STEPS.length - 1, (int) Math.ceil(darkness * STEPS.length) - 1);
        if (step == shown) return;
        if (step >= 0) player.addPostEffect(STEPS[step]);
        if (shown >= 0) player.removePostEffect(STEPS[shown]);
        shown = step;
    }
    boolean black() { return shown == STEPS.length - 1; }

    void freeze() {
        for (var type : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH)) {
            var attr = player.getAttribute(type);
            if (attr != null && !attr.hasModifier(FREEZE))
                attr.addTransientModifier(new AttributeModifier(FREEZE, -1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
        }
        player.setDeltaMovement(new Vec3(0, Math.min(0, player.getDeltaMovement().y), 0));
    }
    void unfreeze() {
        for (var type : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH)) {
            var attr = player.getAttribute(type);
            if (attr != null) attr.removeModifier(FREEZE);
        }
    }

    /** Client has its own chunk, every chunk batch acknowledged and the loaded flag, for a few calm ticks. */
    boolean clientReady() {
        if (player.hasDisconnected()) return false;
        var c = player.connection;
        if (!c.hasClientLoaded()) { readyFor = 0; return false; }
        var sender = c.chunkSender;
        long own = ChunkPos.containing(BlockPos.containing(player.position())).pack();
        if (sender.isPending(own) || ((ChunkSenderAccessor) sender).minigamelib$unacknowledged() > 0) { readyFor = 0; return false; }
        return ++readyFor >= SETTLE;
    }

    /** Removes every grade and the freeze. Idempotent. */
    void release() {
        if (released) return;
        released = true;
        if (!player.hasDisconnected()) for (var id : STEPS) player.removePostEffect(id);
        unfreeze();
    }
    boolean released() { return released; }
}
