package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.data.renderer.ModelRenderer;
import kr.toxicity.model.api.mod.platform.ModItemStack;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.EntityHideOption;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.ModelRotation;
import kr.toxicity.model.api.tracker.TrackerModifier;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import kr.toxicity.model.api.util.TransformedItemStack;
import kr.toxicity.model.api.bone.BoneTags;
import kr.toxicity.model.api.util.function.BonePredicate;
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
                .start(kim.biryeong.destiny.weapon.SwordTiming.START_TICKS).end(0).priority(20).type(AnimationIterator.Type.PLAY_ONCE).build();
    }

    private PlayerAnimations() { }

    private static final class Playback {
        final ServerPlayer owner;
        final MinecraftServer server;
        final ServerLevel level;
        final EntityTracker tracker;
        final String loopRequest;
        String loopAnimation;
        net.minecraft.world.phys.Vec3 previousPosition;
        int classMovingUntil;
        Run run;
        boolean closingAfterRun, meleeCast;
        boolean introOwned; // Survives run=null on completion, failure and explicit stop.
        IntroSelfCarrier introSelfCarrier;
        final LimbEquipment equipment;
        ItemStack swordStack;
        SwordHandPackets.Protection handProtection;

        Playback(ServerPlayer owner, EntityTracker tracker, String loopRequest, String loopAnimation, LimbEquipment equipment) {
            this.equipment = equipment;
            this.owner = owner;
            this.server = owner.level().getServer();
            this.level = owner.level();
            this.tracker = tracker;
            this.loopRequest = loopRequest;
            this.loopAnimation = loopAnimation;
            this.previousPosition = owner.position();
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
    /** Crucible entrances are authored in place by HunterModelAssets.inPlaceIntro. */
    public static boolean playIntroInPlace(ServerPlayer player, String clip) {
        return clip != null && clip.startsWith("h15_intro_") && start(player, clip, false);
    }

    public static boolean play(ServerPlayer player, String animation) {
        return start(player, animation, false);
    }

    /** Keep the accepted melee purpose even when a legacy rig resolves a throw fallback. */
    public static boolean playMelee(ServerPlayer player, String animation) {
        if (!start(player, animation, false)) return false;
        Playback state = ACTIVE.get(player.getUUID());
        if (state != null && state.owner == player) state.meleeCast = true;
        return true;
    }

    /** Existing super_arc / super_solar / super_void callers select the H15 ready loop. */
    public static boolean loop(ServerPlayer player, String animation) {
        return start(player, animation, true);
    }

    /** Weapon cosmetics never replace a dodge/grenade/super or use an unsupported fallback clip. */
    public static boolean swordAttack(ServerPlayer player,String animation) {
        if(!kim.biryeong.destiny.weapon.SwordItems.isSword(player.getMainHandItem())
                ||player.isSpectator()||!kim.biryeong.destiny.weapon.WeaponLoadout.canUse(player)
                ||kim.biryeong.destiny.ability.AbilityService.inSuper(player)||foreignToSword(player)
                ||player.getCamera()!=player||kim.biryeong.minigamelib.cinematic.CameraViews.get(player)!=null)return false;
        return start(player,animation,false,true);
    }

    /** Persistent stance underlay. Accepted attacks stay on this exact tracker
     * and keep its monotonic server clock; a stance request cannot cut a swing. */
    public static boolean swordPose(ServerPlayer player,SwordStance stance) {
        if(!kim.biryeong.destiny.weapon.SwordItems.isSword(player.getMainHandItem())
                ||player.isSpectator()||!kim.biryeong.destiny.weapon.WeaponLoadout.canUse(player)
                ||kim.biryeong.destiny.ability.AbilityService.inSuper(player)||foreignToSword(player)
                ||player.getCamera()!=player||kim.biryeong.minigamelib.cinematic.CameraViews.get(player)!=null)return false;
        return start(player,stance.clip(),true,true);
    }

    public static boolean foreignToSword(ServerPlayer player) {
        Playback s=ACTIVE.get(player.getUUID());
        return s!=null&&!s.tracker.isClosed()&&s.swordStack==null;
    }

    public static boolean swordPlaying(ServerPlayer player) {
        Playback s=ACTIVE.get(player.getUUID());
        return s!=null&&!s.tracker.isClosed()&&s.swordStack!=null;
    }

    /** Main-thread packet projection: only the exact live pose binding owns the
     * invisible logical carrier. Model bones continue reading the real item. */
    public static boolean ownsSwordHand(ServerPlayer player, ItemStack stack) {
        Playback state = ACTIVE.get(player.getUUID());
        return state != null && state.owner == player && state.swordStack == stack && valid(state);
    }

    /** Preserve a nonempty owner carrier while the grenade HUD draws its own skin arm.
     * BM's empty-slot disguise would otherwise make vanilla render an additional fist. */
    public static boolean ownsGrenadeHand(ServerPlayer player, ItemStack stack) {
        Playback state = ACTIVE.get(player.getUUID());
        return state != null && state.owner == player && state.handProtection != null
                && state.swordStack == null && "grenade".equals(logical(activeClip(player)))
                && stack == player.getMainHandItem() && !stack.isEmpty() && valid(state);
    }

    public static boolean meleePlaying(ServerPlayer player) {
        Playback state = ACTIVE.get(player.getUUID());
        return state != null && state.owner == player && state.meleeCast && valid(state);
    }

    public static boolean swordAttacking(ServerPlayer player) {
        Playback s=ACTIVE.get(player.getUUID());
        return s!=null&&!s.tracker.isClosed()&&s.swordStack!=null&&s.run!=null;
    }

    /** Active underlay, not necessarily the displayed priority-20 attack. */
    public static String swordPose(ServerPlayer player) {
        Playback s=ACTIVE.get(player.getUUID());
        return s!=null&&!s.tracker.isClosed()&&s.swordStack!=null?s.loopAnimation:null;
    }

    public static void stopSword(ServerPlayer player) {
        Playback s=ACTIVE.get(player.getUUID());
        if(s!=null&&s.swordStack!=null)discard(s);
    }

    /** Cancel only the owned attack; a valid stance underlay may remain.
     * Foreign/lifecycle-invalid bindings still receive full cleanup. */
    public static void cancelSwordAttack(ServerPlayer player) {
        Playback s=ACTIVE.get(player.getUUID());
        if(s==null||s.swordStack==null)return;
        if(s.loopRequest==null||!valid(s)) {discard(s);return;}
        Run run=s.run;
        s.run=null;
        if(run!=null)s.tracker.stopAnimation(run.animation);
    }

    /** Diagonals prefer forward/back visually; Motion keeps the exact diagonal physics. */
    public static String rollAnimation(Input input) {
        int forward = (input.forward() ? 1 : 0) - (input.backward() ? 1 : 0);
        int left = (input.left() ? 1 : 0) - (input.right() ? 1 : 0);
        return PREFIX + "roll_" + (forward > 0 ? "forward" : forward < 0 ? "back"
                : left > 0 ? "left" : left < 0 ? "right" : "forward");
    }

    /** W259 keeps the two dodge silhouettes distinct and the legacy roll API stable. */
    public static String dodgeAnimation(Input input, boolean marksman) {
        String roll = rollAnimation(input);
        return marksman ? roll.replace(PREFIX + "roll_", PREFIX + "dodge_marksman_") : roll;
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
        return start(player,request,loop,false);
    }

    private static boolean start(ServerPlayer player,String request,boolean loop,boolean sword) {
        if (!available() || player.isRemoved() || !player.isAlive() || player.hasDisconnected()) return false;
        SwordHandPackets.Protection handProtection = null;
        boolean adopted = false;
        try {
            Playback previous = ACTIVE.get(player.getUUID());
            if(sword&&previous!=null&&previous.swordStack==player.getMainHandItem()&&valid(previous)) {
                String name=clipName(previous.tracker.renderer(),request);
                if(name==null)return false;
                return loop ? (previous.run!=null || updateLoop(previous,name)) : oneShot(previous,name);
            }
            if (!sword && !loop && previous != null && previous.swordStack==null
                    && !previous.closingAfterRun && previous.loopRequest != null && valid(previous)) {
                String name = clipName(previous.tracker.renderer(), request);
                return name != null && oneShot(previous, name);
            }
            Clip clip;
            if(sword) {
                var renderer=BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).orElse(null);
                var name=renderer==null?null:clipName(renderer,request);
                clip=name==null?null:new Clip(renderer,name);
            } else clip = resolve(request);
            if (clip == null) return false; // A missing clip must not destroy a working loop.
            stop(player);
            if (sword || logical(request).startsWith("class_") || ("grenade".equals(logical(request))
                    && kim.biryeong.destiny.ability.GrenadeThrow.active(player)))
                handProtection = SwordHandPackets.begin(player);
            LimbEquipment equipment = new LimbEquipment();
            AtomicBoolean created = new AtomicBoolean();
            EntityTracker tracker = clip.renderer.getOrCreate(ModPlayer.of(player.connection),
                    TrackerModifier.DEFAULT, t -> {
                        t.hideOption(EntityHideOption.DEFAULT);
                        equipment.bind(t);
                        created.set(true);
                    });
            // getOrCreate skips its initializer for an existing same-model tracker.
            // Do not claim a foreign clock or install an unbound visual state.
            if (!created.get()) return false;
            ((ServerAnimationClock) (Object) tracker).destiny$claimServerClock();
            Playback state = new Playback(player, tracker, loop ? logical(request) : null, loop ? clip.animation : null, equipment);
            state.introOwned = clip.animation.startsWith("h15_intro_");
            if (state.introOwned) {
                // Freeze the authored stage facing instead of BM's movement-smoothed body yaw.
                float stageYaw = player.getYRot();
                tracker.rotation(() -> new ModelRotation(0, stageYaw));
                float correction = IntroFacing.correctionRadians(clip.animation);
                // BM cancels a parent's GLOBAL modifier for each child: repeat the same
                // correction through the subtree. Root translation/entry path stays untouched.
                tracker.getPipeline().addGlobalRotModifier(
                        BonePredicate.from(b -> b.name().rawName().equals("player_root")).children(true),
                        q -> q.rotationY(correction));
            }
            if(sword) {
                state.swordStack=player.getMainHandItem();
                tracker.rotation(() -> new ModelRotation(0,player.getYRot()));
            }
            if (logical(request).startsWith("roll_") || logical(request).startsWith("dodge_marksman_")) {
                // Directional source poses are relative to the accepted aim, not the
                // body's movement-facing yaw. Do not rotate the player's real view.
                float dodgeYaw = player.getYRot();
                tracker.rotation(() -> new ModelRotation(0, dodgeYaw));
            }
            if ("super_void".equals(state.loopRequest) || "super_solar".equals(state.loopRequest)
                    || request.startsWith("w229_") || request.startsWith("w230_")) {
                // Aim supers face the authoritative view, not BM's independently smoothed
                // body yaw. This only rotates the visual tracker; camera/body input is untouched.
                tracker.rotation(() -> new ModelRotation(0, player.getYRot()));
                // BM cancels parent's GLOBAL modifier on each child. Use the same quaternion
                // throughout the upper-body subtree, replacing built-in head pitch while aiming.
                tracker.getPipeline().addGlobalRotModifier(BonePredicate.tag(BoneTags.PLAYER_CHEST).withChildren(),
                        q -> q.rotationX((float) Math.toRadians(player.getXRot())));
            }
            state.handProtection = handProtection;
            ACTIVE.put(player.getUUID(), state);
            adopted = true;
            applyOwnerVisibility(player, tracker);
            if (handProtection != null) SwordHandPackets.syncCurrent(player);
            boolean ok = loop ? tracker.animate(clip.animation, Modifiers.READY) : oneShot(state, clip.animation);
            if (ok && loop) ((ServerAnimationClock) (Object) tracker).destiny$primeAnimation();
            if (!ok) discard(state);
            return ok;
        } catch (RuntimeException | LinkageError e) {
            fail(player, request, e);
            return false;
        } finally {
            if (!adopted && handProtection != null) {
                SwordHandPackets.syncCurrent(player);
                SwordHandPackets.end(handProtection);
            }
        }
    }

    private static Clip resolve(String request) {
        if (request.startsWith("w229_") || request.startsWith("w230_")) {
            ModelRenderer renderer = BetterModel.limb(ClassSuperModelAssets.MODEL_NAME).orElse(null);
            String animation = renderer == null ? null : clipName(renderer, request);
            return animation == null ? null : new Clip(renderer, animation);
        }
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
        // Only a missing imported marksman clip may use the legacy roll fallback.
        if (logical.startsWith("dodge_marksman_"))
            return clipName(renderer, "roll_" + logical.substring("dodge_marksman_".length()));
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
        if (ok) ((ServerAnimationClock) (Object) state.tracker).destiny$primeAnimation();
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
                if (state.run != null && state.run.animation.startsWith("h15_intro_"))
                    kim.biryeong.minigamelib.cinematic.CameraViews.sending(() ->
                            ((ServerAnimationClock) (Object) state.tracker).destiny$advanceServerTick());
                else ((ServerAnimationClock) (Object) state.tracker).destiny$advanceServerTick();
                var position = state.owner.position();
                double moved = position.subtract(state.previousPosition).horizontalDistanceSqr();
                state.previousPosition = position;
                Run run = state.run;
                if (run != null) {
                    boolean arcDeployDone = run.animation.equals(PREFIX + "super_arc_start")
                            && server.getTickCount() - run.startedAt >= run.durationTicks;
                    if (arcDeployDone || run.finished(server.getTickCount())) {
                        state.run = null;
                        state.tracker.stopAnimation(run.animation);
                        if (state.loopRequest == null || state.closingAfterRun) {
                            discard(state); // Vanilla idle, skin and live inventory become visible again.
                            continue;
                        }
                    }
                }
                if (state.run == null && !state.closingAfterRun && "super_arc".equals(state.loopRequest)) {
                    updateArcLocomotion(state, moved > .000225 && state.owner.onGround());
                }
                if (state.run == null && !state.closingAfterRun && state.loopRequest != null
                        && (state.loopRequest.startsWith("w229_") || state.loopRequest.startsWith("w230_"))) {
                    if (moved > .000225) state.classMovingUntil = server.getTickCount() + 3;
                    updateClassLocomotion(state, server.getTickCount() < state.classMovingUntil);
                }
                if (state.run == null && state.swordStack!=null && state.loopRequest!=null) {
                    var pose=SwordStance.select(kim.biryeong.destiny.weapon.WeaponRuntime.swordStatus(state.owner)
                            .map(kim.biryeong.destiny.weapon.WeaponRuntime.SwordStatus::guarding).orElse(false),
                            state.owner.onGround(),moved);
                    String name=clipName(state.tracker.renderer(),pose.clip());
                    if(name!=null)updateLoop(state,name);
                }
                syncEquipment(state);
            } catch (RuntimeException | LinkageError e) {
                fail(state.owner, "tick", e);
            }
        }
    }

    /** Actual collision-resolved displacement drives gait, not held keys against a wall. */
    private static void updateArcLocomotion(Playback state, boolean moving) {
        String name = clipName(state.tracker.renderer(), moving ? "super_arc_move" : "super_arc");
        if(name!=null)updateLoop(state,name);
    }

    /** Class upper-body ready/hold plus source-backed or explicitly authored lower-body gait.
     * Collision-resolved movement drives selection. Cast/attack one-shots always finish first. */
    private static void updateClassLocomotion(Playback state, boolean moving) {
        String base = state.loopRequest.endsWith("_idle")
                ? state.loopRequest.substring(0, state.loopRequest.length() - 5) : state.loopRequest;
        String request = !state.owner.onGround() ? base + "_air" : moving ? base + "_move" : state.loopRequest;
        String name = clipName(state.tracker.renderer(), request);
        if (name == null) name = clipName(state.tracker.renderer(), moving ? base + "_move" : state.loopRequest);
        if (name == null) name = clipName(state.tracker.renderer(), state.loopRequest);
        if (name != null) updateLoop(state, name);
    }

    private static boolean updateLoop(Playback state,String name) {
        if(name.equals(state.loopAnimation))return true;
        if(!state.tracker.animate(name,Modifiers.READY))return false;
        if (state.loopAnimation != null) state.tracker.stopAnimation(state.loopAnimation);
        state.loopAnimation = name;
        ((ServerAnimationClock) (Object) state.tracker).destiny$primeAnimation();
        return true;
    }

    private static boolean valid(Playback state) {
        return !state.tracker.isClosed() && state.owner.isAlive() && !state.owner.isSpectator() && !state.owner.isRemoved()
                && !state.owner.hasDisconnected() && state.owner.level() == state.level
                && (state.swordStack==null || (state.owner.getMainHandItem()==state.swordStack
                    && !kim.biryeong.destiny.ability.AbilityService.inSuper(state.owner)
                    && kim.biryeong.destiny.weapon.WeaponLoadout.canUse(state.owner)
                    && state.owner.getCamera()==state.owner
                    && kim.biryeong.minigamelib.cinematic.CameraViews.get(state.owner)==null));
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
        if (state.introOwned) CameraViews.sending(() -> closeNow(state));
        else closeNow(state);
    }

    private static void closeNow(Playback state) {
        state.run = null;
        state.equipment.clear();
        try {
            if (!state.tracker.isClosed()) state.tracker.update(TrackerUpdateAction.itemMapping());
        } catch (RuntimeException | LinkageError e) {
            DestinyGuardians.LOGGER.warn("Limb equipment restore failed: {}", e.toString());
        } finally {
            state.tracker.bones().forEach(EquipmentDisplaySamples::forget);
            try { state.tracker.close(); }
            catch (RuntimeException | LinkageError e) {
                DestinyGuardians.LOGGER.warn("Limb close failed: {}", e.toString());
            } finally {
                closeIntroSelfCarrier(state);
                if (state.handProtection != null) {
                    try { SwordHandPackets.syncCurrent(state.owner); }
                    finally { SwordHandPackets.end(state.handProtection); }
                }
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
        return kim.biryeong.destiny.camera.SuperCamera.active(player)
                || kim.biryeong.destiny.crucible.CrucibleRuntime.viewingIntro(player)
                || (runtime.gcbClient && runtime.gcbThirdPerson);
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

    /** Submit the existing intro pose to one viewer; never replay or advance its clock.
     * A successful return means submitted, not acknowledged by the native client.
     */
    public static boolean syncIntroViewer(ServerPlayer owner, ServerPlayer viewer, String expectedClip) {
        Playback state = ACTIVE.get(owner.getUUID());
        if (expectedClip == null || !expectedClip.startsWith("h15_intro_") || state == null
                || state.owner != owner || !state.introOwned || state.run == null
                || !expectedClip.equals(state.run.animation)) return false;
        if (!state.server.isSameThread()) throw new IllegalStateException("Intro audience requires server thread");
        if (!valid(state) || viewer.hasDisconnected() || viewer.isRemoved() || !viewer.isAlive()
                || viewer.level() != state.level || state.server.getPlayerList().getPlayer(viewer.getUUID()) != viewer
                || !kim.biryeong.destiny.crucible.CrucibleRuntime.viewingIntro(viewer)) return false;
        var tracker = state.tracker;
        var registry = tracker.registry();
        // Registry.spawn includes every tracker. Do not resend a foreign model.
        if (registry.trackers().stream().anyMatch(t -> t != tracker && !t.isClosed())) return false;
        boolean[] submitted = {false};
        CameraViews.sending(() -> {
            tracker.getPipeline().viewFilter(candidate -> {
                var player = state.server.getPlayerList().getPlayer(candidate.uuid());
                return (player != null && player.level() == state.level
                        && kim.biryeong.destiny.crucible.CrucibleRuntime.viewingIntro(player))
                        || !tracker.modifier().sightTrace()
                        || kr.toxicity.model.api.util.EntityUtil.canSee(candidate.eyeLocation(), tracker.location());
            });
            if (viewer == owner) {
                if (state.introSelfCarrier == null)
                    state.introSelfCarrier = new IntroSelfCarrier(owner, tracker);
                // Installation is ordered on Netty, never block the server thread.
                // CrucibleIntro retries this pair next tick without restarting the cast.
                if (!state.introSelfCarrier.ready()) return;
                state.introSelfCarrier.spawn();
            }
            var target = ModPlayer.of(viewer.connection);
            tracker.show(target);
            // Fake camera respawn/cuts can erase the client model while BM still
            // reports isSpawned=true. A full resend also registers new viewers.
            if (!registry.spawn(target)) return;
            var channel = tracker.getPipeline().channel(viewer.getUUID());
            if (channel == null) return;
            // BM's spawn-success callback runs on Netty, outside this ThreadLocal
            // scope. Submit the vanilla-body disguise synchronously as well.
            BetterModel.nms().hide(channel, registry);
            submitted[0] = tracker.isSpawned(target);
        });
        return submitted[0];
    }

    /** Detach this viewer from only the still-owned intro; a foreign replacement survives. */
    public static void removeIntroViewer(ServerPlayer owner, ServerPlayer viewer, String expectedClip) {
        Playback state = ACTIVE.get(owner.getUUID());
        if (expectedClip == null || !expectedClip.startsWith("h15_intro_") || state == null
                || state.owner != owner || !state.introOwned || state.run == null
                || !expectedClip.equals(state.run.animation) || state.tracker.isClosed()) return;
        if (!state.server.isSameThread()) throw new IllegalStateException("Intro audience requires server thread");
        var connected = state.server.getPlayerList().getPlayer(viewer.getUUID());
        if (connected != null && connected != viewer) return; // Old disconnect after reconnect.
        CameraViews.sending(() -> {
            var target = ModPlayer.of(viewer.connection);
            var registry = state.tracker.registry();
            try {
                if (registry.trackers().stream().noneMatch(t -> t != state.tracker && !t.isClosed()))
                    registry.remove(target);
                else state.tracker.remove(target);
            } finally {
                if (viewer == owner) closeIntroSelfCarrier(state);
            }
        });
    }

    private static void closeIntroSelfCarrier(Playback state) {
        IntroSelfCarrier carrier = state.introSelfCarrier;
        state.introSelfCarrier = null;
        if (carrier != null) {
            try { carrier.close(); }
            catch (RuntimeException | LinkageError e) {
                DestinyGuardians.LOGGER.warn("Intro self carrier close failed: {}", e.toString());
            }
        }
    }

    /** Read-only effective clip for server QA; does not create or advance a tracker. */
    public static String activeClip(ServerPlayer player) {
        Playback s = ACTIVE.get(player.getUUID());
        return s == null || s.owner != player || s.tracker.isClosed() ? "none"
                : s.run != null ? s.run.animation : s.loopAnimation == null ? "none" : s.loopAnimation;
    }

    /** QA telemetry from the actual BetterModel clock, not a separate gameplay counter. */
    public static long serverFrames(ServerPlayer player) {
        Playback state = ACTIVE.get(player.getUUID());
        return state == null ? 0 : ((ServerAnimationClock) (Object) state.tracker).destiny$serverFrames();
    }

    /** World socket on the equipped prop, using the SAME transform sent to the vanilla display.
     * Raw coordinates are Java model units. H24 staff and H22 bow hand contexts are pinned here.
     * Null means no live equipped pose: callers must skip cosmetics rather than guess near the face.
     */
    public static net.minecraft.world.phys.Vec3 equipmentPoint(ServerPlayer player, boolean bow,
                                                               double rawX, double rawY, double rawZ) {
        if (!Double.isFinite(rawX) || !Double.isFinite(rawY) || !Double.isFinite(rawZ)) return null;
        Playback state = ACTIVE.get(player.getUUID());
        if (state == null || state.tracker.isClosed() || !valid(state)) return null;
        var equipment = state.equipment.selection();
        if (equipment.item() == null || bow != equipment.bowInLeftHand()) return null;
        var bone = state.tracker.bone(b -> b.name().rawName().equals(bow ? "pli_left_item" : "pri_right_item"));
        var sample = bone == null ? null : EquipmentDisplaySamples.sample(bone);
        if (sample == null) return null;
        var local = new org.joml.Vector3f((float)(rawX-8)/16, (float)(rawY-8)/16, (float)(rawZ-8)/16);
        if (bow) local.rotateY(-(float)Math.PI/2); // left-handed ItemTransform mirrors authored +90.
        local.add(0, .125f, 0).rotateY((float)Math.PI); // native hand translation then submitInner Ry180.
        local.mul(sample.scale()).rotate(sample.rotation()).add(sample.position());
        local.rotateY(-(float)Math.toRadians(state.tracker.getPipeline().getRotation().y()));
        // BM sends SetPassengers: limb displays ride the player, not tracker.location().
        // Vanilla clamps all these non-registered model riders to the first passenger anchor.
        // ItemDisplay has zero VEHICLE attachment; do not add BM off-world spawn sentinel.
        var seat = player.getPassengerRidingPosition(player);
        return seat.add(local.x, local.y, local.z);
    }

    /** Visual hand only. EMPTY clears the override and restores live equipment mapping. */
    public static void superItem(ServerPlayer player, ItemStack item) {
        superItem(player, item, false);
    }

    /** Explicit bare hands on the visual rig; EMPTY via superItem instead restores live equipment. */
    public static void superEmptyHands(ServerPlayer player) {
        Playback state = ACTIVE.get(player.getUUID());
        if (state == null) return;
        try {
            state.equipment.set(TransformedItemStack.empty(), true);
            syncEquipment(state);
        } catch (RuntimeException | LinkageError e) { fail(player, "empty super hands", e); }
    }

    /** Two virtual props on the skin rig; does not write the player's real inventory. */
    public static void superItems(ServerPlayer player, ItemStack main, ItemStack off) {
        Playback state = ACTIVE.get(player.getUUID());
        if (state == null) return;
        try {
            state.equipment.dual(TransformedItemStack.of(ModItemStack.of(main.copy())),
                    TransformedItemStack.of(ModItemStack.of(off.copy())));
            syncEquipment(state);
        } catch (RuntimeException | LinkageError e) { fail(player, "dual super hands", e); }
    }

    /** Visual equipment only: a right-handed archer supports the bow with the left hand. */
    public static void superItem(ServerPlayer player, ItemStack item, boolean bowInLeftHand) {
        Playback state = ACTIVE.get(player.getUUID());
        if (state == null) return;
        try {
            state.equipment.set(item.isEmpty() ? null : TransformedItemStack.of(ModItemStack.of(item.copy())), bowInLeftHand);
            syncEquipment(state);
        } catch (RuntimeException | LinkageError e) { fail(player, "equipment", e); }
    }

    private static void syncEquipment(Playback state) {
        // Mapping refreshes respect the lifetime policy at the actual native commit.
        // Both hands refresh: switching away from a left-hand bow restores live offhand.
        state.tracker.update(TrackerUpdateAction.itemMapping(), bone ->
                bone.name().rawName().equals("pri_right_item") || bone.name().rawName().equals("pli_left_item"));
    }
}
