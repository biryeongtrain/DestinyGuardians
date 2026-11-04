package kim.biryeong.destiny.campaign.fallen;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * D2 Fallen combat VFX, ported as short-lived Polymer item-display sprites (W300 r5). Each sprite is the first
 * surface of a D2 particle texture from the Rising-Guardian-Fallen-AV extract (see
 * {@code destiny/guardian_rises/fallen_vfx.json} and docs/design/guardian-rises/fallen-vfx.md); colour comes from
 * the item model's custom_model_data tint. D2 shader stages (scroll, erosion, HDR) are not reproduced: sprites
 * pop in, interpolate their scale to a peak, then shrink away and are destroyed.
 *
 * <p>Budget: effects are built separately for each player within {@link #RANGE} blocks, so every sprite is sized
 * for that viewer: its apparent size is capped at {@link Sprite#maxDeg} degrees of view (r5b). Never sent to a
 * player whose eye is inside the effect's near-clip radius, nor (for impacts) to the player who was hit; at most {@link #PLAYER_CAP} live sprites per player and
 * {@link #GLOBAL_CAP} overall. Over budget an effect is dropped for that viewer (the vanilla particles that
 * FallenWeapons still emits remain as the fallback read). Sounds are untouched. Self-registers its server tick on
 * first use, so callers only add one-line hooks.
 */
public final class FallenVfx {
    private FallenVfx() {}

    static final double RANGE = 48;
    static final int GLOBAL_CAP = 192, PLAYER_CAP = 72;
    static final int SMOKE = 0x5E6068, WHITE = 0xFFFFFF, EMP = 0x8FD8FF;
    /** Impact/flash stars: at most ~4 degrees on screen (Vision r5: near hits covered a quarter of the view). */
    static final float STAR_DEG = 4f, BEAM_DEG = 1.2f;
    /** r5b: stars drawn 40% smaller and 40% dimmer than r5. */
    static final float STAR_SCALE = .6f, STAR_DIM = .6f;
    /** r5b: contrail width (blocks) at spawn / end, and lifetime in ticks. */
    static final float TRAIL_W0 = .1f, TRAIL_W1 = .02f;
    static final int TRAIL_LIFE = 2;

    /** Sprite ids; names match fallen_vfx.json and assets/destiny/items/guardian_rises/vfx/&lt;name&gt;.json. */
    enum Sprite {
        GLOW(false, 8), ENERGY_RING(false, 10), FLASH_STAR(false, STAR_DEG), FLASH_JET(false, 8), BURST_STAR(false, STAR_DEG),
        SHRAP_ROUND(false, 12), SHRAP_LONG(false, 14), CANNON_JET(false, 14), FIRE_PUFFS(false, 24), SMOKE(false, 30),
        EMP_ARCS(false, 30), CONTRAIL(true, BEAM_DEG), BOLT_CORE(true, BEAM_DEG);
        final boolean beam;
        /** Largest apparent size (degrees of the viewer's field of view) this sprite may reach; beams: width. */
        final float maxDeg;
        Sprite(boolean beam, float maxDeg) { this.beam = beam; this.maxDeg = maxDeg; }
        String id() { return name().toLowerCase(java.util.Locale.ROOT); }
    }

    private static final List<Fx> LIVE = new ArrayList<>();
    private static final Map<UUID, Integer> LOAD = new HashMap<>();
    private static int liveSprites;
    private static boolean hooked;

    // ================================================================================== effects (public API)

    /** Weapon discharge at the muzzle; the archetype is read from the shooter (Dreg/Vandal/Captain/Shank/Walker). */
    public static void muzzle(ServerLevel level, LivingEntity shooter, Vec3 at, Vec3 dir, int color, FallenWeapons.Style style) {
        FallenKind kind = shooter instanceof FallenMob m ? m.fallenKind() : null;
        emit(level, at, at, 0, null, fx -> {
            switch (style) {
                case SHELL -> { // Walker cannon: 80A5A2D7 flash_long + ring, then a smoke puff
                    fx.jet(Sprite.CANNON_JET, color, dir, 3.4f, 1.7f, 1, 6);
                    fx.quad(Sprite.ENERGY_RING, color, .8f, 2.6f, 2, 6, 0);
                    fx.quad(Sprite.GLOW, color, 3f, 3.4f, 1, 4, 0);
                    fx.quad(Sprite.SMOKE, SMOKE, 1.2f, 3f, 6, 22, 0).drift(dir.scale(.8).add(0, 1.2, 0));
                }
                case ORB -> { // Captain shock blast
                    fx.quad(Sprite.ENERGY_RING, color, .5f, 1.8f, 2, 5, 0);
                    fx.star(Sprite.FLASH_STAR, WHITE, .4f, 1.1f, 1, 3, 0);
                    fx.quad(Sprite.GLOW, color, 1.8f, 2f, 1, 3, 0);
                }
                case ARC -> {
                    if (kind == FallenKind.DREG) { // shock pistol 80CEA1DB: energy burst + light flash
                        fx.quad(Sprite.ENERGY_RING, color, .25f, .95f, 1, 3, 0);
                        fx.quad(Sprite.GLOW, color, 1f, 1.1f, 1, 3, 0);
                    } else if (kind == FallenKind.WALKER) { // anti-personnel guns
                        fx.star(Sprite.FLASH_STAR, color, .5f, 1.3f, 1, 3, 0);
                        fx.jet(Sprite.FLASH_JET, color, dir, 1.7f, .7f, 1, 3);
                        fx.quad(Sprite.GLOW, color, 1.4f, 1.5f, 1, 3, 0);
                    } else { // Vandal wire rifle 80CEA54B (flash_round + flash_long); Shank arc burst
                        float s = kind == FallenKind.SHANK ? .8f : 1f;
                        fx.star(Sprite.FLASH_STAR, color, .3f * s, .85f * s, 1, 3, 0);
                        fx.jet(Sprite.FLASH_JET, color, dir, 1.2f * s, .5f * s, 1, 3);
                        fx.quad(Sprite.GLOW, color, .9f * s, 1f * s, 1, 3, 0);
                    }
                }
            }
        });
    }

    /**
     * Bolt flight for one tick of travel (from → to): a thin contrail (80CEA182) for arc bolts, plasma/fire for
     * orbs/shells. The contrail starts slightly behind {@code from} so consecutive 2-tick segments overlap (r5b:
     * continuous line instead of separate blobs).
     */
    public static void tracer(ServerLevel level, Vec3 from, Vec3 to, int color, FallenWeapons.Style style) {
        Vec3 d = to.subtract(from);
        double len = d.length();
        if (len < 1e-3) return;
        switch (style) {
            case ARC -> {
                Vec3 a = from.subtract(d.scale(.25 / len));
                emit(level, a, to, 1.2, null, fx -> fx.beam(Sprite.CONTRAIL, color, d, (float) (len + .25), TRAIL_W0, TRAIL_W1, TRAIL_LIFE));
            }
            case ORB -> emit(level, to, to, 1.6, null, fx -> fx.quad(Sprite.GLOW, color, 1.3f, .4f, 0, 3, 0));
            case SHELL -> emit(level, to, to, 1.6, null,
                    fx -> fx.quad(Sprite.FIRE_PUFFS, color, .9f, .3f, 0, 5, level.getRandom().nextFloat() * 6.28f));
        }
    }

    /**
     * Bolt hit: the D2 impact sequences carry sounds only, so the wire-rifle burst (80CEA681) + glow is reused. A hit
     * on a player is not drawn for that player (it would sit on their own camera); others see it.
     */
    public static void impact(ServerLevel level, Vec3 at, int color, boolean onPlayer) {
        emit(level, at, at, onPlayer ? 1.8 : .8, onPlayer ? at : null, fx -> {
            fx.star(Sprite.BURST_STAR, color, .25f, .95f, 1, 4, level.getRandom().nextFloat() * 6.28f);
            fx.quad(Sprite.GLOW, color, .9f, .2f, 0, 3, 0);
        });
    }

    /** Splash detonation (Captain orb, Walker shell): flash, fireball (80A5A26D/80A6DB1C), smoke, shrapnel. */
    public static void explosion(ServerLevel level, Vec3 at, double radius, int color, boolean big) {
        float r = (float) Math.max(.6, radius);
        emit(level, at.add(0, .3, 0), at.add(0, .3, 0), Math.min(2.4, r * .8), null, fx -> {
            var rnd = level.getRandom();
            fx.quad(Sprite.GLOW, color, r * 1.8f, r * 2f, 1, 4, 0);
            fx.star(Sprite.BURST_STAR, big ? WHITE : color, r * .5f, r * 1.6f, 2, 5, rnd.nextFloat() * 6.28f);
            for (int i = 0, n = big ? 3 : 2; i < n; i++)
                fx.quad(Sprite.FIRE_PUFFS, color, r * .4f, r * (1.1f + rnd.nextFloat() * .4f), 3, 10 + i * 2, rnd.nextFloat() * 6.28f)
                        .offset(new Vec3((rnd.nextFloat() - .5) * r * .5, rnd.nextFloat() * r * .3, (rnd.nextFloat() - .5) * r * .5));
            for (int i = 0, n = big ? 2 : 1; i < n; i++)
                fx.quad(Sprite.SMOKE, SMOKE, r * .7f, r * 2f, 10, 26 + i * 4, rnd.nextFloat() * 6.28f)
                        .drift(new Vec3((rnd.nextFloat() - .5) * r * .4, r * .9, (rnd.nextFloat() - .5) * r * .4));
            if (big) for (int i = 0; i < 3; i++) {
                double a = rnd.nextDouble() * Math.PI * 2;
                fx.jet(Sprite.SHRAP_LONG, color, new Vec3(Math.cos(a), .9 + rnd.nextDouble(), Math.sin(a)), r * 1.3f, r * .55f, 2, 6);
            }
        });
    }

    /** Shank self-destruct burst on death (shrapnel launcher flash_round 80A6DAED + fireball). */
    public static void shankBurst(ServerLevel level, Vec3 at) {
        emit(level, at, at, 1.2, null, fx -> {
            var rnd = level.getRandom();
            fx.quad(Sprite.SHRAP_ROUND, FallenArchetypes.FALLEN_ARC, .3f, 1.6f, 2, 6, rnd.nextFloat() * 6.28f);
            fx.quad(Sprite.GLOW, FallenArchetypes.FALLEN_ARC, 1.8f, 2.2f, 1, 4, 0);
            fx.quad(Sprite.FIRE_PUFFS, 0xFFB060, .4f, 1.3f, 3, 9, rnd.nextFloat() * 6.28f);
            fx.quad(Sprite.SMOKE, SMOKE, .6f, 1.6f, 8, 20, rnd.nextFloat() * 6.28f).drift(new Vec3(0, .8, 0));
        });
    }

    /** Walker leg armour broken: big fireball, smoke column and shrapnel jets. */
    public static void legBreak(ServerLevel level, Vec3 at) {
        explosion(level, at, 2.2, FallenArchetypes.WALKER_ORANGE, true);
    }

    /** Walker destroyed: the largest detonation. */
    public static void walkerDeath(ServerLevel level, Vec3 at) {
        explosion(level, at, 4.2, FallenArchetypes.WALKER_ORANGE, true);
        emp(level, at);
    }

    /**
     * D2 Walker EMP (sequence 80A5AC46: lightning sheets + flash). The W300 Walker has no EMP attack, so this marks
     * the STAGGER discharge: arcs gather for 5 ticks, then burst outwards with a light flash.
     */
    public static void emp(ServerLevel level, Vec3 at) {
        emit(level, at, at, 2.5, null, fx -> {
            var rnd = level.getRandom();
            fx.quad(Sprite.EMP_ARCS, EMP, 1.2f, 2.4f, 5, 7, rnd.nextFloat() * 6.28f);
            fx.quad(Sprite.EMP_ARCS, EMP, .6f, 5.5f, 7, 12, rnd.nextFloat() * 6.28f).delay(5);
            fx.quad(Sprite.ENERGY_RING, EMP, 1f, 6f, 5, 9, 0).delay(5);
            fx.quad(Sprite.GLOW, EMP, 4f, 5f, 2, 6, 0).delay(5);
        });
    }

    /** Walker weakpoint opening (80A5AFDB bright flash). */
    public static void weakpointExpose(ServerLevel level, Vec3 at) {
        emit(level, at, at, 1.5, null, fx -> {
            fx.quad(Sprite.GLOW, 0xFFC14D, 3f, 3.6f, 2, 8, 0);
            fx.quad(Sprite.ENERGY_RING, 0xFFD27A, .6f, 2.8f, 3, 8, 0);
            fx.star(Sprite.FLASH_STAR, WHITE, .6f, 1.8f, 2, 5, 0);
        });
    }

    /** Exposed weakpoint heartbeat glow (every few ticks while EXPOSED). */
    public static void weakpointPulse(ServerLevel level, Vec3 at) {
        emit(level, at, at, 1.5, null, fx -> fx.quad(Sprite.GLOW, 0xFFC14D, 1.6f, 2.1f, 2, 5, 0));
    }

    /** Captain/Vandal arc shield collapses: ring pops outwards (80A5A2D7 ring texture). */
    public static void shieldPop(ServerLevel level, Vec3 center, double height) {
        float h = (float) Math.max(1, height);
        emit(level, center, center, 1.5, null, fx -> {
            fx.quad(Sprite.ENERGY_RING, FallenArchetypes.FALLEN_ARC, h * .8f, h * 1.9f, 3, 7, 0);
            fx.quad(Sprite.EMP_ARCS, FallenArchetypes.FALLEN_ARC, h * .9f, h * 1.4f, 2, 5, level.getRandom().nextFloat() * 6.28f);
            fx.quad(Sprite.GLOW, FallenArchetypes.FALLEN_ARC, h * 1.4f, h * 1.6f, 1, 4, 0);
        });
    }

    /** Arc shield re-forms around the mob. */
    public static void shieldUp(ServerLevel level, Vec3 center, double height) {
        float h = (float) Math.max(1, height);
        emit(level, center, center, 1.5, null, fx -> fx.quad(Sprite.ENERGY_RING, FallenArchetypes.FALLEN_ARC, h * 1.8f, h * 1.1f, 4, 8, 0));
    }

    /** Vandal blink: a collapsing glow where it left, an expanding ring where it arrives. */
    public static void blink(ServerLevel level, Vec3 from, Vec3 to) {
        Vec3 a = from.add(0, 1.1, 0), b = to.add(0, 1.1, 0);
        emit(level, a, a, 1.5, null, fx -> {
            fx.quad(Sprite.GLOW, 0xE6F7FF, 2.2f, .2f, 0, 6, 0);
            fx.quad(Sprite.ENERGY_RING, 0xE6F7FF, 1.6f, .3f, 0, 6, 0);
        });
        emit(level, b, b, 1.5, null, fx -> {
            fx.quad(Sprite.ENERGY_RING, 0xE6F7FF, .3f, 1.8f, 3, 7, 0);
            fx.quad(Sprite.GLOW, 0xE6F7FF, 1.8f, 2f, 1, 5, 0);
        });
    }

    // ================================================================================== per-viewer emission

    @FunctionalInterface interface Build { void into(Fx fx); }

    /**
     * Builds the effect once per eligible viewer (so sizes can be capped for that viewer's distance). Viewers:
     * within RANGE of a, under PLAYER_CAP, eye outside the near-clip radius of segment a-b, and, when
     * {@code hitAt} is set, not the player whose (slightly inflated) box contains it.
     */
    static void emit(ServerLevel level, Vec3 a, Vec3 b, double nearClip, Vec3 hitAt, Build build) {
        if (liveSprites >= GLOBAL_CAP) return;
        double near2 = nearClip * nearClip, range2 = RANGE * RANGE;
        for (ServerPlayer p : level.players()) {
            if (p.hasDisconnected() || p.distanceToSqr(a) > range2) continue;
            if (LOAD.getOrDefault(p.getUUID(), 0) >= PLAYER_CAP) continue;
            if (hitAt != null && p.getBoundingBox().inflate(.4).contains(hitAt)) continue;
            double d2 = segmentDistanceSq(p.getEyePosition(), a, b);
            if (near2 > 0 && d2 < near2) continue;
            if (liveSprites >= GLOBAL_CAP) return;
            var fx = new Fx(level, a, p, Math.sqrt(d2));
            build.into(fx);
            fx.start();
        }
    }

    /** Largest size (blocks) that subtends {@code degrees} at {@code distance} blocks (pure; tested). */
    static float maxSize(double distance, float degrees) {
        return (float) (2 * Math.max(.05, distance) * Math.tan(Math.toRadians(degrees) / 2));
    }

    /** Factor (≤ 1) that brings a sprite of {@code size} blocks under its angular cap at {@code distance}. */
    static float capFactor(Sprite sprite, float size, double distance) {
        float max = maxSize(distance, sprite.maxDeg);
        return size <= max || size <= 0 ? 1f : max / size;
    }

    static int dim(int rgb, float k) {
        int r = (int) (((rgb >> 16) & 255) * k), g = (int) (((rgb >> 8) & 255) * k), b = (int) ((rgb & 255) * k);
        return (r << 16) | (g << 8) | b;
    }

    // ================================================================================== lifecycle

    static void tick(MinecraftServer server) {
        if (LIVE.isEmpty()) return;
        int now = server.getTickCount();
        Iterator<Fx> it = LIVE.iterator();
        while (it.hasNext()) {
            Fx fx = it.next();
            if (fx.level.getServer() != server) continue;
            if (now <= fx.born) continue; // spawn packets go out this tick; animate from the next
            if (fx.advance()) { fx.close(); it.remove(); }
        }
    }

    public static void clearAll() {
        for (Fx fx : LIVE) fx.close();
        LIVE.clear();
        LOAD.clear();
        liveSprites = 0;
    }

    static int liveSprites() { return liveSprites; }

    private static void hook() {
        if (hooked) return;
        hooked = true;
        ServerTickEvents.END_SERVER_TICK.register(FallenVfx::tick);
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> clearAll());
    }

    /** Squared distance from p to segment ab (pure; tested). */
    static double segmentDistanceSq(Vec3 p, Vec3 a, Vec3 b) {
        Vec3 ab = b.subtract(a);
        double l2 = ab.lengthSqr();
        double t = l2 < 1e-9 ? 0 : Math.max(0, Math.min(1, p.subtract(a).dot(ab) / l2));
        return p.distanceToSqr(a.add(ab.scale(t)));
    }

    /** Rotation taking model +X onto dir (display-space jet axis), with a roll about dir. */
    static Quaternionf axisX(Vec3 dir, float roll) {
        Vector3f d = new Vector3f((float) dir.x, (float) dir.y, (float) dir.z);
        if (d.lengthSquared() < 1e-8f) d.set(1, 0, 0);
        return new Quaternionf().rotationTo(new Vector3f(1, 0, 0), d.normalize()).rotateX(roll);
    }

    private static final Map<Long, ItemStack> STACKS = new HashMap<>();

    static ItemStack stack(Sprite sprite, int color) {
        long key = ((long) sprite.ordinal() << 32) | (color & 0xFFFFFFL);
        return STACKS.computeIfAbsent(key, k -> {
            var s = new ItemStack(Items.PAPER);
            s.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "guardian_rises/vfx/" + sprite.id()));
            s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(color & 0xFFFFFF)));
            return s;
        }).copy();
    }

    // ================================================================================== effect instance

    private static final class Part {
        final ItemDisplayElement e;
        final Vector3f base; // unit scale vector (x,y,z multipliers)
        final float s0, peak;
        final int peakAt, life;
        Vector3f t0 = new Vector3f(), t1;
        int delay;
        boolean added;
        Part(ItemDisplayElement e, Vector3f base, float s0, float peak, int peakAt, int life) {
            this.e = e; this.base = base; this.s0 = s0; this.peak = peak; this.peakAt = peakAt; this.life = life;
        }
        Part drift(Vec3 v) { t1 = new Vector3f(t0).add((float) v.x, (float) v.y, (float) v.z); return this; }
        Part offset(Vec3 v) { t0.add((float) v.x, (float) v.y, (float) v.z); if (t1 != null) t1.add((float) v.x, (float) v.y, (float) v.z); e.setTranslation(new Vector3f(t0)); return this; }
        Part delay(int ticks) { delay = ticks; return this; }
    }

    private static final class Fx {
        final ServerLevel level;
        final Vec3 at;
        final ServerPlayer viewer;
        /** Distance from the viewer's eye to the effect (blocks); drives the angular size cap. */
        final double distance;
        final ElementHolder holder = new ElementHolder();
        final List<Part> parts = new ArrayList<>();
        final int born;
        int age, counted;

        Fx(ServerLevel level, Vec3 at, ServerPlayer viewer, double distance) {
            this.level = level; this.at = at; this.viewer = viewer; this.distance = distance;
            this.born = level.getServer().getTickCount();
        }

        private ItemDisplayElement element(Sprite sprite, int color) {
            var e = new ItemDisplayElement(stack(sprite, color));
            e.setItemDisplayContext(ItemDisplayContext.FIXED);
            e.setBrightness(new Brightness(15, 15));
            e.setShadowRadius(0);
            e.setViewRange(1f);
            return e;
        }

        /** Impact/flash star: 40% smaller and dimmer than a plain quad, capped at STAR_DEG. */
        Part star(Sprite sprite, int color, float s0, float peak, int peakAt, int life, float roll) {
            return quad(sprite, dim(color, STAR_DIM), s0 * STAR_SCALE, peak * STAR_SCALE, peakAt, life, roll);
        }

        /** Camera-facing sprite; size in blocks, grows s0 → peak by peakAt, then shrinks to nothing at life. */
        Part quad(Sprite sprite, int color, float s0, float peak, int peakAt, int life, float roll) {
            float k = capFactor(sprite, Math.max(s0, peak), distance);
            s0 *= k; peak *= k;
            var e = element(sprite, color);
            e.setBillboardMode(Display.BillboardConstraints.CENTER);
            if (roll != 0) e.setRightRotation(new Quaternionf().rotationZ(roll));
            return add(e, new Vector3f(1, 1, 1), s0, peak, peakAt, life);
        }

        /** Directional flame: two crossed planes whose model +X runs along dir from the origin. */
        void jet(Sprite sprite, int color, Vec3 dir, float length, float width, int peakAt, int life) {
            Vec3 d = dir.lengthSqr() < 1e-8 ? new Vec3(1, 0, 0) : dir.normalize();
            float k = capFactor(sprite, Math.max(length, width), distance);
            length *= k; width *= k;
            float roll = level.getRandom().nextFloat() * 6.28f;
            for (int i = 0; i < 2; i++) {
                var e = element(sprite, color);
                e.setLeftRotation(axisX(d, roll + i * (float) (Math.PI / 2)));
                var p = add(e, new Vector3f(length, width, width), .45f, 1f, peakAt, life);
                p.t0.set((float) d.x * length * .5f, (float) d.y * length * .5f, (float) d.z * length * .5f);
                e.setTranslation(new Vector3f(p.t0));
            }
        }

        /** Beam (two crossed planes along model +Z) spanning the segment, width w0 → w1. */
        void beam(Sprite sprite, int color, Vec3 d, float length, float w0, float w1, int life) {
            float k = capFactor(sprite, Math.max(w0, w1), distance);
            w0 *= k; w1 *= k;
            var e = element(sprite, color);
            Vector3f dir = new Vector3f((float) d.x, (float) d.y, (float) d.z).normalize();
            e.setLeftRotation(new Quaternionf().rotationTo(new Vector3f(0, 0, 1), dir));
            var p = add(e, new Vector3f(w0, w0, length), 1f, 1f, 0, life);
            p.t0.set(dir).mul(length * .5f);
            e.setTranslation(new Vector3f(p.t0));
            // shrink across the width only: encode the end width as the peak multiplier on x/y
            p.base.set(1, 1, 1);
            beamEnds.put(p, new float[]{w0, w1, length});
        }

        private final Map<Part, float[]> beamEnds = new HashMap<>();

        private Part add(ItemDisplayElement e, Vector3f base, float s0, float peak, int peakAt, int life) {
            var p = new Part(e, base, s0, peak, peakAt, Math.max(1, life));
            e.setScale(new Vector3f(base).mul(s0));
            parts.add(p);
            return p;
        }

        void start() {
            if (parts.isEmpty()) return;
            hook();
            for (Part p : parts) if (p.delay == 0) { holder.addElement(p.e); p.added = true; }
            counted = parts.size();
            liveSprites += counted;
            LOAD.merge(viewer.getUUID(), counted, Integer::sum);
            new ManualAttachment(holder, level, () -> at);
            holder.startWatching(viewer);
            LIVE.add(this);
        }

        /** @return true when finished. */
        boolean advance() {
            age++;
            boolean any = false;
            for (Part p : parts) {
                int t = age - p.delay;
                if (t < 0) { any = true; continue; }
                if (!p.added) { // delayed part: spawn now, animate from the next tick
                    holder.addElement(p.e); p.added = true; any = true; continue;
                }
                if (p.delay > 0) t--;
                if (t >= p.life) { if (p.e.getHolder() == holder) holder.removeElement(p.e); continue; }
                any = true;
                float[] beam = beamEnds.get(p);
                if (t == 1 && beam != null) {
                    p.e.setInterpolationDuration(p.life - 1);
                    p.e.setScale(new Vector3f(beam[1], beam[1], beam[2]));
                    p.e.startInterpolation();
                } else if (t == 1 && beam == null) {
                    int d = p.peakAt > 0 ? p.peakAt : p.life - 1;
                    p.e.setInterpolationDuration(Math.max(1, d));
                    p.e.setScale(new Vector3f(p.base).mul(p.peak));
                    if (p.t1 != null) p.e.setTranslation(lerp(p.t0, p.t1, d / (float) p.life));
                    p.e.startInterpolation();
                } else if (beam == null && p.peakAt > 0 && t == p.peakAt + 1 && p.life - t > 0) {
                    p.e.setInterpolationDuration(p.life - t);
                    p.e.setScale(new Vector3f(p.base).mul(p.peak * .08f));
                    if (p.t1 != null) p.e.setTranslation(new Vector3f(p.t1));
                    p.e.startInterpolation();
                }
            }
            holder.tick();
            return !any;
        }

        private static Vector3f lerp(Vector3f a, Vector3f b, float k) {
            return new Vector3f(a).lerp(b, Math.max(0, Math.min(1, k)));
        }

        void close() {
            liveSprites = Math.max(0, liveSprites - counted);
            LOAD.computeIfPresent(viewer.getUUID(), (k, n) -> n - counted <= 0 ? null : n - counted);
            holder.destroy();
        }
    }
}
