package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.minigamelib.mixin.ChunkSenderAccessor;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundClearTitlesPacket;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ChunkPos;

import java.util.ArrayList;
import java.util.List;

/**
 * Owner-private black curtain: waits until the client has actually loaded the destination (the vanilla
 * "loading terrain" screen otherwise eats the hold), holds full black, then fades the world in through five
 * stepped grades (post_effect guardian_rises/fade_1..5; 26.3 post chains take no server-driven uniforms).
 * The whole curtain is cinematic (vanilla + combat HUD + first-person weapon hidden); an optional title card
 * shows over the black and an optional line on the action bar as the picture returns. Messages deferred with
 * {@link RisingPresentation#afterArrival} are sent once, when the curtain ends (or is closed).
 */
final class Curtain extends RisingPresentation.Scene {
    static final Identifier[] STEPS = {
            RisingPresentation.FADE,
            id("fade_1"), id("fade_2"), id("fade_3"), id("fade_4"), id("fade_5")};
    /** Longest wait for the client to finish loading before the hold starts anyway. */
    static final int LOAD_TIMEOUT = 200, SETTLE = 6;

    private final int hold, fade;
    private final String line;
    private final Component title, subtitle;
    final List<Component> after = new ArrayList<>();
    private RisingPresentation.Lock lock;
    private int step = -1, holdStart = -1, loadedFor;
    private boolean titled;

    Curtain(ServerPlayer player, int hold, int fade, String line, Component title, Component subtitle) {
        super(player, null);
        this.hold = Math.max(0, hold);
        this.fade = Math.max(STEPS.length, fade);
        this.line = line;
        this.title = title;
        this.subtitle = subtitle;
    }

    Curtain(ServerPlayer player, int hold, int fade, String line) { this(player, hold, fade, line, null, null); }

    private static Identifier id(String name) { return kim.biryeong.destiny.DestinyGuardians.id("guardian_rises/" + name); }

    @Override void begin() {
        lock = RisingPresentation.lock(player);
        lock.hideHud(true);
        show(0);
    }

    /** Client loaded: own chunk sent, every chunk batch acknowledged, loaded flag set, a few calm ticks. */
    private boolean clientReady() {
        var c = player.connection;
        if (!c.hasClientLoaded()) { loadedFor = 0; return false; }
        var sender = c.chunkSender;
        long own = ChunkPos.containing(BlockPos.containing(player.position())).pack();
        if (sender.isPending(own) || ((ChunkSenderAccessor) sender).minigamelib$unacknowledged() > 0) { loadedFor = 0; return false; }
        return ++loadedFor >= SETTLE;
    }

    @Override void update(int t, int now) {
        if (holdStart < 0) {
            // The first ticks after a dimension change have not queued any chunks yet: never trust them.
            if ((t < 4 || !clientReady()) && t < LOAD_TIMEOUT) return;
            holdStart = t;
        }
        int h = t - holdStart;
        if (h == 0 && title != null) {
            titled = true;
            player.connection.send(new ClientboundSetTitlesAnimationPacket(8, hold + fade / 2, 14));
            if (subtitle != null) player.connection.send(new ClientboundSetSubtitleTextPacket(subtitle));
            player.connection.send(new ClientboundSetTitleTextPacket(title));
        }
        if (h == hold && line != null) RisingAudio.voice(player, line);
        if (h >= hold) {
            int s = Math.min(STEPS.length, 1 + (h - hold) * STEPS.length / fade);
            if (s >= STEPS.length) { completeAndClose(); return; }
            show(s);
        }
    }

    private void show(int s) {
        if (s == step || player.hasDisconnected()) return;
        // Add the next grade before dropping the previous one: never a frame of unfiltered world.
        player.addPostEffect(STEPS[s]);
        if (step >= 0) player.removePostEffect(STEPS[step]);
        step = s;
    }

    @Override void restore() {
        if (!player.hasDisconnected()) {
            for (var id : STEPS) {
                if (id.equals(RisingPresentation.FADE) && RisingPresentation.wantsBlack(player, this)) continue;
                player.removePostEffect(id);
            }
            if (titled && !finished) player.connection.send(new ClientboundClearTitlesPacket(true));
            for (var m : after) player.sendSystemMessage(m);
        }
        after.clear();
        if (lock != null) { RisingPresentation.unlock(lock); lock = null; }
        RisingPresentation.holdHud(player, 6);
    }
}
