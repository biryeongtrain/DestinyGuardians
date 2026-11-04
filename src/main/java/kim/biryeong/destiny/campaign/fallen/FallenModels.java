package kim.biryeong.destiny.campaign.fallen;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.EntityAttachment;
import eu.pb4.polymer.virtualentity.api.elements.BlockDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.data.renderer.ModelRenderer;
import kr.toxicity.model.api.mod.platform.ModAdapter;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import kr.toxicity.model.api.bone.RenderedBone;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.LightLayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import org.joml.Vector3f;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * BetterModel presentation for one Fallen (W300). Only calls into BetterModel when the requested clip changes,
 * so steady states send no animation packets. If the model or a clip is missing the mob keeps its invisible
 * server hitbox and shows a simple Polymer block-display silhouette (logged once per model).
 */
public final class FallenModels {
    public enum Action {
        IDLE, MOVE, RUN, SHOOT, MELEE, HIT, STAGGER, DEATH, SPAWN,
        FIRE, LEG_BREAK, WEAKPOINT_OPEN, RECOVER,
        TAUNT, EVADE_LEFT, EVADE_RIGHT
    }

    /** Preferred clip names per action; the first one the model provides wins. */
    static final Map<Action, List<String>> CLIPS = Map.ofEntries(
            Map.entry(Action.IDLE, List.of("idle")),
            Map.entry(Action.MOVE, List.of("walk", "fly", "idle")),
            Map.entry(Action.RUN, List.of("run", "walk", "fly", "idle")),
            Map.entry(Action.SHOOT, List.of("shoot", "fire")),
            Map.entry(Action.MELEE, List.of("melee", "shoot")),
            Map.entry(Action.HIT, List.of("hit")),
            Map.entry(Action.STAGGER, List.of("stagger", "hit")),
            Map.entry(Action.DEATH, List.of("death")),
            Map.entry(Action.SPAWN, List.of("spawn", "arrive")),
            Map.entry(Action.FIRE, List.of("fire", "shoot")),
            Map.entry(Action.LEG_BREAK, List.of("leg_break", "stagger")),
            Map.entry(Action.WEAKPOINT_OPEN, List.of("weakpoint_open", "stagger")),
            Map.entry(Action.RECOVER, List.of("recover", "idle")),
            // W300 r6 Dreg-Light handoff clips (retargeted D2 taunt / evade steps); models without them skip quietly.
            Map.entry(Action.TAUNT, List.of("taunt")),
            Map.entry(Action.EVADE_LEFT, List.of("evade_left")),
            Map.entry(Action.EVADE_RIGHT, List.of("evade_right")));

    private static final Set<Action> OPTIONAL = Set.of(Action.TAUNT, Action.EVADE_LEFT, Action.EVADE_RIGHT);
    private static final Set<String> WARNED = new HashSet<>();
    private static final int BASE_HOLD_TICKS = 5;

    private final FallenMob mob;
    private EntityTracker tracker;
    private ModelRenderer renderer;
    private ElementHolder fallback;
    private String baseClip, heldClip;
    private int lastBaseChange = -100;
    private boolean closed, dead;
    private int lightBlock = -1, lightSky = -1;
    private boolean charging, hasGlowBones;

    /**
     * Minimum block light for non-emissive bones. Light 5 keeps a dim, still-shaded silhouette in an unlit room
     * (about a third of full brightness in the vanilla lightmap) while staying clearly darker than lamps and the
     * emissive *_glow bones; in daylight the sampled sky light dominates so normal lighting is unchanged.
     * A fixed (6,15) would wrongly light enemies in dark rooms as if outdoors and flatten night/day.
     */
    static final int LIGHT_FLOOR = 5;
    static final int LIGHT_INTERVAL = 10;

    private FallenModels(FallenMob mob) { this.mob = mob; }

    /** Presentation-less handle used until the mob's first server tick attaches the real one. */
    static FallenModels detached(FallenMob mob) { return new FallenModels(mob); }

    /** Attach after the mob is in the world. Never throws. */
    static FallenModels attach(FallenMob mob, boolean visual) {
        var handle = new FallenModels(mob);
        if (!visual) return handle; // hit-region parts: no presentation
        String name = mob.archetype().model();
        try {
            handle.renderer = BetterModel.model(name).orElse(null);
            if (handle.renderer != null) {
                var modifier = TrackerModifier.builder().sightTrace(true).damageAnimation(false).damageTint(true).build();
                handle.tracker = handle.renderer.getOrCreate(kr.toxicity.model.api.mod.platform.ModEntity.of(mob), modifier); // W300: the LivingEntity adapter is rejected by the tracker path
            }
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("Fallen model {} failed to attach: {}", name, e.toString());
            handle.tracker = null;
        }
        if (handle.tracker != null) {
            handle.hasGlowBones = handle.tracker.bones().stream().anyMatch(FallenModels::glowBone);
            handle.light(true);
        }
        if (handle.tracker == null) {
            if (WARNED.add(name))
                DestinyGuardians.LOGGER.warn("Fallen model '{}' unavailable; using block-display fallback silhouettes", name);
            handle.fallback(mob);
        }
        return handle;
    }

    boolean modeled() { return tracker != null && !tracker.isClosed(); }

    private String clip(Action action) {
        if (renderer == null) return null;
        for (String c : CLIPS.get(action)) if (renderer.animation(c).isPresent()) return c;
        if (OPTIONAL.contains(action)) return null;
        if (WARNED.add(mob.archetype().model() + "#" + action))
            DestinyGuardians.LOGGER.warn("Fallen model '{}' has no clip for {}", mob.archetype().model(), action);
        return null;
    }

    /** Looping base layer (idle/walk/run/fly). Hysteresis keeps it from flickering on path jitter. */
    void base(Action action) {
        if (closed || dead || !modeled() || heldClip != null) return;
        String c = clip(action);
        if (c == null || c.equals(baseClip)) return;
        if (baseClip != null && mob.tickCount - lastBaseChange < BASE_HOLD_TICKS) return;
        var modifier = new AnimationModifier(4, 4, AnimationIterator.Type.LOOP);
        boolean ok = baseClip != null ? tracker.replace(baseClip, c, modifier) : tracker.animate(c, modifier);
        if (!ok && baseClip != null) { tracker.stopAnimation(baseClip); ok = tracker.animate(c, modifier); }
        if (ok) { baseClip = c; lastBaseChange = mob.tickCount; }
    }

    /** True when the model provides a clip for the action (optional flavour clips such as evade). */
    boolean has(Action action) { return modeled() && clip(action) != null; }

    /** One-shot overlay (shoot, melee, hit, stagger...). Returns to the base layer automatically. */
    void play(Action action) {
        if (closed || dead || !modeled()) return;
        String c = clip(action);
        if (c == null) return;
        if (action == Action.RECOVER && heldClip != null) { tracker.stopAnimation(heldClip); heldClip = null; }
        tracker.animate(c, new AnimationModifier(2, 3, AnimationIterator.Type.PLAY_ONCE));
    }

    /** Play once and hold the last frame until the next play/base change (Walker weakpoint_open). */
    void hold(Action action) {
        if (closed || dead || !modeled()) return;
        String c = clip(action);
        if (c == null) return;
        if (heldClip != null) tracker.stopAnimation(heldClip);
        if (tracker.animate(c, new AnimationModifier(2, 0, AnimationIterator.Type.HOLD_ON_LAST))) heldClip = c;
    }

    void release() {
        if (heldClip != null && modeled()) tracker.stopAnimation(heldClip);
        heldClip = null;
    }

    /** Plays the death clip and returns how long to keep the body (ticks), clamped to 20..80. */
    int death(int fallbackTicks) {
        if (dead) return fallbackTicks;
        charge(false, 0);
        dead = true;
        if (!modeled()) return fallbackTicks;
        String c = clip(Action.DEATH);
        if (c == null) return fallbackTicks;
        if (baseClip != null) tracker.stopAnimation(baseClip);
        if (heldClip != null) tracker.stopAnimation(heldClip);
        baseClip = heldClip = null;
        tracker.animate(c, new AnimationModifier(2, 0, AnimationIterator.Type.HOLD_ON_LAST));
        float seconds = renderer.animation(c).map(a -> a.length()).orElse(fallbackTicks / 20f);
        return Math.max(20, Math.min(80, Math.round(seconds * 20) + 6));
    }

    static boolean glowBone(RenderedBone bone) {
        var n = bone.name();
        return n != null && n.name() != null && n.name().endsWith("_glow");
    }

    /** Pure floor rule (unit tested): never darker than the floor, never brighter than the real light. */
    static int flooredBlockLight(int sampled) { return Math.max(Math.max(0, Math.min(15, sampled)), LIGHT_FLOOR); }

    /**
     * Brightness overrides: *_glow bones are full-bright; the rest use the light at the mob's body with a block-light
     * floor. Sampled every LIGHT_INTERVAL ticks; a packet is sent only when the floored value changes.
     */
    void light(boolean force) {
        if (closed || !modeled()) return;
        if (!force && mob.tickCount % LIGHT_INTERVAL != 0) return;
        var level = mob.level();
        BlockPos at = BlockPos.containing(mob.getX(), mob.getY() + Math.min(mob.getBbHeight() * .7, 2.5), mob.getZ());
        int block = flooredBlockLight(level.getBrightness(LightLayer.BLOCK, at));
        int sky = Math.max(0, Math.min(15, level.getBrightness(LightLayer.SKY, at)));
        if (!force && block == lightBlock && sky == lightSky) return;
        lightBlock = block; lightSky = sky;
        var body = TrackerUpdateAction.brightness(block, sky);
        var glow = TrackerUpdateAction.brightness(15, 15);
        tracker.update(TrackerUpdateAction.perBone(bone -> glowBone(bone) ? glow : body));
    }

    /**
     * Attack-charge telegraph: a short coloured outline on the emissive bones (whole model if it has none) while the
     * attacker is charging. Only called when the attacker already has line of sight, so the through-wall outline
     * never reveals a hidden enemy for longer than its own wind-up.
     */
    void charge(boolean on, int color) {
        if (closed || !modeled() || on == charging) return;
        charging = on;
        var action = on ? TrackerUpdateAction.composite(TrackerUpdateAction.glowColor(color), TrackerUpdateAction.glow(true))
                : TrackerUpdateAction.glow(false);
        if (hasGlowBones) tracker.update(action, (java.util.function.Predicate<RenderedBone>) FallenModels::glowBone);
        else tracker.update(action);
    }

    void tint() {
        if (modeled()) tracker.damageTint();
    }

    void close() {
        if (closed) return;
        closed = true;
        try {
            if (tracker != null && !tracker.isClosed()) tracker.close();
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.debug("Fallen tracker close failed: {}", e.toString());
        }
        tracker = null;
        if (fallback != null) { fallback.destroy(); fallback = null; }
    }

    // ------------------------------------------------------------------------------------------ fallback

    private void fallback(FallenMob mob) {
        var arch = mob.archetype();
        float w = arch.width(), h = arch.height();
        fallback = new ElementHolder();
        BlockState body = switch (arch.kind()) {
            case DREG -> Blocks.CONCRETE.gray().defaultBlockState();
            case VANDAL -> Blocks.DYED_TERRACOTTA.blue().defaultBlockState();
            case CAPTAIN -> Blocks.DYED_TERRACOTTA.cyan().defaultBlockState();
            case SHANK -> Blocks.CONCRETE.lightGray().defaultBlockState();
            case WALKER -> Blocks.IRON_BLOCK.defaultBlockState();
        };
        if (arch.kind() == kim.biryeong.destiny.campaign.RisingServices.FallenKind.WALKER) {
            // Hull and four legs, matching WalkerBoss.LAYOUT (anchor-local, rotated by the attachment).
            for (var e : WalkerBoss.LAYOUT.entrySet()) {
                var b = e.getValue();
                boolean weak = e.getKey() == WalkerBoss.Region.WEAKPOINT;
                var el = new BlockDisplayElement(weak ? Blocks.STAINED_GLASS.orange().defaultBlockState() : body);
                el.setScale(new Vector3f(b.width(), b.height(), b.width()));
                el.setTranslation(new Vector3f((float) -b.x() - b.width() / 2, (float) b.y(), (float) b.z() - b.width() / 2));
                if (weak) el.setBrightness(new Brightness(15, 15));
                fallback.addElement(el);
            }
        } else {
            float headH = arch.hasPrecisionHead() ? h * .25f : 0;
            var torso = new BlockDisplayElement(body);
            torso.setScale(new Vector3f(w, h - headH, w));
            torso.setTranslation(new Vector3f(-w / 2, 0, -w / 2));
            fallback.addElement(torso);
            if (headH > 0) {
                var head = new BlockDisplayElement(Blocks.STAINED_GLASS.lightBlue().defaultBlockState());
                head.setScale(new Vector3f(w * .7f, headH, w * .7f));
                head.setTranslation(new Vector3f(-w * .35f, h - headH, -w * .35f));
                head.setBrightness(new Brightness(15, 15));
                fallback.addElement(head);
            }
        }
        EntityAttachment.ofTicking(fallback, mob);
    }
}
