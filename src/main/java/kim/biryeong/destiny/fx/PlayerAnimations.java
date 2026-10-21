package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.guardian.Guardians;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.EntityHideOption;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.server.level.ServerPlayer;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * BetterModel limb 로 몸 전체 동작을 재생한다 (docs/design/04).
 * 본인에게는 1인칭이면 숨기고, GCB 로 3인칭임을 알면 보여준다 (docs/design/12 6장).
 */
public final class PlayerAnimations {
    public static String limb = "guardian_hunter";
    public static String fallbackLimb = "steve";
    private static final Map<UUID, EntityTracker> ACTIVE = new HashMap<>();

    private PlayerAnimations() {
    }

    public static boolean available() {
        return FabricLoader.getInstance().isModLoaded("bettermodel");
    }

    /** @return 재생을 시작했으면 true */
    public static boolean play(ServerPlayer player, String animation) {
        if (!available()) {
            return false;
        }
        try {
            return playInternal(player, animation);
        } catch (RuntimeException | LinkageError e) {
            kim.biryeong.destiny.DestinyGuardians.LOGGER.warn("Limb animation {} failed: {}", animation, e.toString());
            return false;
        }
    }

    private static boolean playInternal(ServerPlayer player, String animation) {
        var renderer = BetterModel.limb(limb)
                .filter(r -> r.animation(animation).isPresent())
                .or(() -> BetterModel.limb(fallbackLimb).filter(r -> r.animation(animation).isPresent()))
                .orElse(null);
        if (renderer == null) {
            return false;
        }
        stop(player);
        ModPlayer self = ModPlayer.of(player.connection);
        EntityTracker tracker = renderer.getOrCreate(self, TrackerModifier.DEFAULT, t -> t.hideOption(EntityHideOption.DEFAULT));
        ACTIVE.put(player.getUUID(), tracker);
        applyOwnerVisibility(player, tracker);
        boolean ok = tracker.animate(animation, AnimationModifier.DEFAULT_WITH_PLAY_ONCE, () -> {
            tracker.close();
            ACTIVE.remove(player.getUUID(), tracker);
        });
        if (!ok) {
            tracker.close();
            ACTIVE.remove(player.getUUID());
        }
        return ok;
    }

    public static void stop(ServerPlayer player) {
        EntityTracker old = ACTIVE.remove(player.getUUID());
        if (old != null) {
            old.close();
        }
    }

    /** 시점이 바뀌었을 때 (GCB) 다시 판단한다. */
    public static void refreshOwnerVisibility(ServerPlayer player) {
        EntityTracker tracker = ACTIVE.get(player.getUUID());
        if (tracker != null) {
            applyOwnerVisibility(player, tracker);
        }
    }

    public static boolean ownerSeesLimb(ServerPlayer player) {
        var runtime = Guardians.runtime(player);
        return runtime.gcbClient && runtime.gcbThirdPerson;
    }

    private static void applyOwnerVisibility(ServerPlayer player, EntityTracker tracker) {
        ModPlayer self = ModPlayer.of(player.connection);
        if (ownerSeesLimb(player)) {
            tracker.show(self);
        } else {
            tracker.hide(self);
        }
    }

    public static boolean isPlaying(ServerPlayer player) {
        return ACTIVE.containsKey(player.getUUID());
    }
}
