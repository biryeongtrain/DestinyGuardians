package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.data.renderer.ModelRenderer;
import kr.toxicity.model.api.mod.platform.ModItemStack;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.EntityHideOption;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import kr.toxicity.model.api.util.TransformedItemStack;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;

import java.util.LinkedHashSet;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Main-thread player limb API. Call tick(server) every server tick.
 * BetterModel callbacks only flag their own run: transitions and equipment changes happen in tick.
 * Owner visibility follows GCB. The real inventory, aim and velocity are never changed.
 */
public final class PlayerAnimations {
    public static String limb = HunterModelAssets.MODEL_NAME;
    public static String fallbackLimb = "steve";
    private static final String PREFIX = "h15_";
    private static final Map<UUID, Playback> ACTIVE = new ConcurrentHashMap<>();
    // Keep optional BetterModel classes out of static initialization (even rollAnimation must work without it).
    private static final class Modifiers {
        static final AnimationModifier READY = AnimationModifier.builder()
                .start(2).end(0).priority(0).type(AnimationIterator.Type.LOOP).build();
        static final AnimationModifier ONCE = AnimationModifier.builder()
                .start(1).end(0).priority(20).type(AnimationIterator.Type.PLAY_ONCE).build();
    }

    private PlayerAnimations() { }

    private static final class Playback {
        final ServerPlayer owner;
        final MinecraftServer server;
        final ServerLevel level;
        final EntityTracker tracker;
        final String loopRequest;
        final String loopAnimation;
        Run run;
        boolean closingAfterRun;
        TransformedItemStack equipment;
        boolean bowInLeftHand;

        Playback(ServerPlayer owner, EntityTracker tracker, String loopRequest, String loopAnimation) {
            this.owner = owner;
            this.server = owner.level().getServer();
            this.level = owner.level();
            this.tracker = tracker;
            this.loopRequest = loopRequest;
            this.loopAnimation = loopAnimation;
        }
    }

    static final class Run {
        final String animation;
        final int startedAt;
        final int durationTicks;
        // Completion is per bone and may run on BetterModel's scheduler.
        final AtomicBoolean completed = new AtomicBoolean();

        Run(String animation, int startedAt, int durationTicks) {
            this.animation = animation;
            this.startedAt = startedAt;
            this.durationTicks = durationTicks;
        }

        boolean finished(int tick) {
            int elapsed = tick - startedAt;
            return (completed.get() && elapsed >= durationTicks) || elapsed >= durationTicks + 6;
        }
    }

    private record Clip(ModelRenderer renderer, String animation) { }

    public static boolean available() {
        return FabricLoader.getInstance().isModLoaded("bettermodel");
    }

    /** One-shot: returns to the active ready loop, or the vanilla player, on completion. */
    public static boolean play(ServerPlayer player, String animation) {
        return start(player, animation, false);
    }

    /** Existing super_arc / super_solar / super_void callers select the H15 ready loop. */
    public static boolean loop(ServerPlayer player, String animation) {
        return start(player, animation, true);
    }

    /** Diagonals prefer forward/back visually; Motion keeps the exact diagonal physics. */
    public static String rollAnimation(Input input) {
        int forward = (input.forward() ? 1 : 0) - (input.backward() ? 1 : 0);
        int left = (input.left() ? 1 : 0) - (input.right() ? 1 : 0);
        return PREFIX + "roll_" + (forward > 0 ? "forward" : forward < 0 ? "back"
                : left > 0 ? "left" : left < 0 ? "right" : "forward");
    }

    /**
     * Call AFTER a primary cast passes cooldown/ammo checks. Requires the matching
     * loop(player, "super_" + element id). Retriggers safely interrupt the previous attack.
     * False means no matching visual, never a gameplay veto. KINETIC is unsupported.
     */
    public static boolean superAttack(ServerPlayer player, Element element) {
        if (!available() || element == Element.KINETIC) return false;
        Playback state = ACTIVE.get(player.getUUID());
        String ready = "super_" + element.getSerializedName();
        if (state == null || state.closingAfterRun || !ready.equals(state.loopRequest)) return false;
        try {
            if (!valid(state)) return false;
            String animation = clipName(state.tracker.renderer(), ready + "_attack");
            return animation != null && oneShot(state, animation);
        } catch (RuntimeException | LinkageError e) {
            fail(player, "super attack " + element, e);
            return false;
        }
    }

    private static boolean start(ServerPlayer player, String request, boolean loop) {
        if (!available() || player.isRemoved() || !player.isAlive() || player.hasDisconnected()) return false;
        try {
            Playback previous = ACTIVE.get(player.getUUID());
            if (!loop && previous != null && !previous.closingAfterRun && previous.loopRequest != null && valid(previous)) {
                String name = clipName(previous.tracker.renderer(), request);
                return name != null && oneShot(previous, name);
            }
            Clip clip = resolve(request);
            if (clip == null) return false; // A missing clip must not destroy a working loop.
            stop(player);
            EntityTracker tracker = clip.renderer.getOrCreate(ModPlayer.of(player.connection),
                    TrackerModifier.DEFAULT, t -> t.hideOption(EntityHideOption.DEFAULT));
            Playback state = new Playback(player, tracker, loop ? logical(request) : null, loop ? clip.animation : null);
            ACTIVE.put(player.getUUID(), state);
            applyOwnerVisibility(player, tracker);
            boolean ok = loop ? tracker.animate(clip.animation, Modifiers.READY) : oneShot(state, clip.animation);
            if (!ok) discard(state);
            return ok;
        } catch (RuntimeException | LinkageError e) {
            fail(player, request, e);
            return false;
        }
    }

    private static Clip resolve(String request) {
        var names = new LinkedHashSet<String>();
        names.add(limb);
        names.add("guardian_hunter_h15");
        names.add("guardian_hunter");
        names.add(fallbackLimb);
        for (String name : names) {
            if (name == null || name.isBlank()) continue;
            ModelRenderer renderer = BetterModel.limb(name).orElse(null);
            if (renderer == null) continue;
            String animation = clipName(renderer, request);
            if (animation != null) return new Clip(renderer, animation);
        }
        return null;
    }

    private static String logical(String request) {
        return request.startsWith(PREFIX) ? request.substring(PREFIX.length()) : request;
    }

    private static String clipName(ModelRenderer renderer, String request) {
        String logical = logical(request);
        String preferred = PREFIX + (logical.equals("roll") ? "roll_forward" : logical);
        if (renderer.animation(preferred).isPresent()) return preferred;
        if (renderer.animation(logical).isPresent()) return logical;
        // Legacy/Steve has only one roll; never substitute it for a super attack.
        return logical.startsWith("roll_") && renderer.animation("roll").isPresent() ? "roll" : null;
    }

    private static boolean oneShot(Playback state, String animation) {
        Run previous = state.run;
        state.run = null; // Invalidate before stopAnimation can emit a callback.
        if (previous != null) state.tracker.stopAnimation(previous.animation);
        int ticks = Math.max(1, (int) Math.ceil(state.tracker.renderer().animation(animation)
                .orElseThrow().length() * 20) + Modifiers.ONCE.start());
        Run run = new Run(animation, state.server.getTickCount(), ticks);
        state.run = run;
        boolean ok = state.tracker.animate(animation, Modifiers.ONCE, () -> run.completed.set(true));
        if (!ok) {
            state.run = null;
            if (state.loopRequest == null) discard(state);
            else syncEquipment(state);
        }
        return ok;
    }

    /**
     * Main thread, once per server tick. Old callbacks only flag old Run objects.
     * Wait for the nominal clip length so a shorter bone cannot end the full animation.
     * Six extra ticks release missing callbacks instead of leaving a hidden player.
     */
    public static void tick(MinecraftServer server) {
        for (Playback state : ACTIVE.values()) {
            if (state.server != server || ACTIVE.get(state.owner.getUUID()) != state) continue;
            try {
                if (!valid(state)) {
                    discard(state);
                    continue;
                }
                Run run = state.run;
                if (run != null) {
                    if (run.finished(server.getTickCount())) {
                        state.run = null;
                        state.tracker.stopAnimation(run.animation);
                        if (state.loopRequest == null || state.closingAfterRun) {
                            discard(state); // Vanilla idle, skin and live inventory become visible again.
                            continue;
                        }
                    }
                }
                syncEquipment(state);
            } catch (RuntimeException | LinkageError e) {
                fail(state.owner, "tick", e);
            }
        }
    }

    private static boolean valid(Playback state) {
        return !state.tracker.isClosed() && state.owner.isAlive() && !state.owner.isRemoved()
                && !state.owner.hasDisconnected() && state.owner.level() == state.level;
    }

    public static void stop(ServerPlayer player) {
        Playback state = ACTIVE.remove(player.getUUID());
        if (state != null) close(state);
    }

    /**
     * End gameplay immediately, but allow the accepted final shot/release to finish visually.
     * Stops the ready loop now. Only the current one-shot and its equipment survive until completion.
     * No run means immediate cleanup; stop(player) always overrides this (death/logout/class change).
     */
    public static void finishSuper(ServerPlayer player) {
        Playback state = ACTIVE.get(player.getUUID());
        if (state == null) return;
        try {
            if (state.run == null || !valid(state)) {
                discard(state);
                return;
            }
            state.closingAfterRun = true;
            if (state.loopAnimation != null) state.tracker.stopAnimation(state.loopAnimation);
        } catch (RuntimeException | LinkageError e) { fail(player, "finish super", e); }
    }

    private static void discard(Playback state) {
        if (ACTIVE.remove(state.owner.getUUID(), state)) close(state);
    }

    private static void close(Playback state) {
        state.run = null;
        state.equipment = null;
        try {
            if (!state.tracker.isClosed()) state.tracker.update(TrackerUpdateAction.itemMapping());
        } catch (RuntimeException | LinkageError e) {
            DestinyGuardians.LOGGER.warn("Limb equipment restore failed: {}", e.toString());
        } finally {
            try { state.tracker.close(); }
            catch (RuntimeException | LinkageError e) {
                DestinyGuardians.LOGGER.warn("Limb close failed: {}", e.toString());
            }
        }
    }

    private static void fail(ServerPlayer player, String animation, Throwable error) {
        stop(player);
        DestinyGuardians.LOGGER.warn("Limb animation {} failed: {}", animation, error.toString());
    }

    /** Re-evaluate owner visibility after a GCB camera change. */
    public static void refreshOwnerVisibility(ServerPlayer player) {
        Playback state = ACTIVE.get(player.getUUID());
        if (state == null) return;
        try { applyOwnerVisibility(player, state.tracker); }
        catch (RuntimeException | LinkageError e) { fail(player, "visibility", e); }
    }

    public static boolean ownerSeesLimb(ServerPlayer player) {
        var runtime = Guardians.runtime(player);
        return kim.biryeong.destiny.camera.SuperCamera.active(player) || (runtime.gcbClient && runtime.gcbThirdPerson);
    }

    private static void applyOwnerVisibility(ServerPlayer player, EntityTracker tracker) {
        ModPlayer self = ModPlayer.of(player.connection);
        if (ownerSeesLimb(player)) tracker.show(self);
        else tracker.hide(self);
    }

    public static boolean isPlaying(ServerPlayer player) {
        Playback state = ACTIVE.get(player.getUUID());
        return state != null && !state.tracker.isClosed();
    }

    /** Visual hand only. EMPTY clears the override and restores live equipment mapping. */
    public static void superItem(ServerPlayer player, ItemStack item) {
        superItem(player, item, false);
    }

    /** Visual equipment only: a right-handed archer supports the bow with the left hand. */
    public static void superItem(ServerPlayer player, ItemStack item, boolean bowInLeftHand) {
        Playback state = ACTIVE.get(player.getUUID());
        if (state == null) return;
        try {
            state.equipment = item.isEmpty() ? null : TransformedItemStack.of(ModItemStack.of(item.copy()));
            state.bowInLeftHand = bowInLeftHand;
            syncEquipment(state);
        } catch (RuntimeException | LinkageError e) { fail(player, "equipment", e); }
    }

    private static void syncEquipment(Playback state) {
        if (state.equipment == null) {
            state.tracker.update(TrackerUpdateAction.itemMapping(), bone ->
                    bone.name().rawName().equals("pri_right_item") || bone.name().rawName().equals("pli_left_item"));
        } else if (state.bowInLeftHand) {
            state.tracker.update(TrackerUpdateAction.itemStack(state.equipment),
                    bone -> bone.name().rawName().equals("pli_left_item"));
            state.tracker.update(TrackerUpdateAction.itemStack(TransformedItemStack.of(ModItemStack.of(ItemStack.EMPTY))),
                    bone -> bone.name().rawName().equals("pri_right_item"));
        } else {
            state.tracker.update(TrackerUpdateAction.itemStack(state.equipment),
                    bone -> bone.name().rawName().equals("pri_right_item"));
        }
    }
}
