package kim.biryeong.destiny.inventory;

import com.mojang.math.Transformation;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.minigamelib.displayhud.DisplayHudManager;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.armor.PlayerArmor;
import kr.toxicity.model.api.mod.platform.ModItemStack;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.profile.ModelProfile;
import kr.toxicity.model.api.skin.SkinData;
import kr.toxicity.model.api.util.TransformedItemStack;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.EnumMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

/**
 * The player's own skinned body drawn as a screen-fixed DisplayHud figure (gear screen, vault, vendors).
 * <p>
 * The limbs are BetterModel's per-player skin items (DynamicUV geometry tinted with the player's real skin pixels,
 * no per-user pack), posed on BetterModel's steve rig and projected orthographically onto the HUD canvas. Depth is
 * flattened so the figure stays inside its own HUD layer instead of cutting through panels in front of it.
 */
public final class PlayerFigure {
    /** steve.bbmodel bones: pivot in model pixels (feet at the origin), parent, and the skin item drawn on it. */
    public enum Limb {
        HIP(null, 0, 11.25f, 0, s -> s.hip(PlayerArmor.EMPTY)),
        WAIST(HIP, 0, 15, 0, s -> s.waist(PlayerArmor.EMPTY)),
        CHEST(WAIST, 0, 18.75f, 0, s -> s.chest(PlayerArmor.EMPTY)),
        HEAD(CHEST, 0, 22.5f, 0, s -> s.head(PlayerArmor.EMPTY)),
        RIGHT_ARM(CHEST, 5, 22, 0, s -> s.rightArm(PlayerArmor.EMPTY)),
        RIGHT_FOREARM(RIGHT_ARM, 5, 16.5f, 0, SkinData::rightForeArm),
        LEFT_ARM(CHEST, -5, 22, 0, s -> s.leftArm(PlayerArmor.EMPTY)),
        LEFT_FOREARM(LEFT_ARM, -5, 16.5f, 0, SkinData::leftForeArm),
        RIGHT_LEG(null, 1.875f, 11.25f, 0, s -> s.rightLeg(PlayerArmor.EMPTY)),
        RIGHT_FORELEG(RIGHT_LEG, 1.875f, 5.625f, 0, s -> s.rightForeLeg(PlayerArmor.EMPTY)),
        LEFT_LEG(null, -1.875f, 11.25f, 0, s -> s.leftLeg(PlayerArmor.EMPTY)),
        LEFT_FORELEG(LEFT_LEG, -1.875f, 5.625f, 0, s -> s.leftForeLeg(PlayerArmor.EMPTY));

        final Limb parent;
        final Vector3f pivot;
        final Function<SkinData, TransformedItemStack> item;
        Limb(Limb parent, float x, float y, float z, Function<SkinData, TransformedItemStack> item) {
            // BetterModel mirrors Blockbench X: steve's +X "right" bones sit on the entity's right (-X) side.
            this.parent = parent; this.pivot = new Vector3f(-x, y, z).div(16); this.item = item;
        }
    }

    /** Per-bone Euler rotation in degrees (X, Y, Z; applied Z, then Y, then X like Blockbench). */
    public record Pose(Map<Limb, Vector3f> rotations) {
        public Pose { rotations = Map.copyOf(rotations); }
        public Vector3f of(Limb limb) { return rotations.getOrDefault(limb, new Vector3f()); }
        /** A relaxed, slightly open stance for character screens. */
        public static final Pose STANDING = pose(Map.of(
                Limb.HEAD, new Vector3f(3, 8, 0),
                Limb.RIGHT_ARM, new Vector3f(-6, 0, 3),
                Limb.RIGHT_FOREARM, new Vector3f(-30, 0, 0),
                Limb.LEFT_ARM, new Vector3f(-4, 0, -5),
                Limb.LEFT_FOREARM, new Vector3f(-10, 0, 0),
                Limb.RIGHT_LEG, new Vector3f(2, 6, 2),
                Limb.LEFT_LEG, new Vector3f(-4, -8, -3),
                Limb.LEFT_FORELEG, new Vector3f(6, 0, 0)));
        private static Pose pose(Map<Limb, Vector3f> map) { return new Pose(new EnumMap<>(map)); }

        /** Inhale (1) or exhale (0) of the idle breath: the chest lifts, head settles, arms ease out. */
        public Pose breath(int phase) {
            if (phase == 0) return this;
            var map = new EnumMap<Limb, Vector3f>(Limb.class);
            for (var limb : Limb.values()) map.put(limb, new Vector3f(of(limb)));
            map.get(Limb.CHEST).add(-0.8f, 0, 0);
            map.get(Limb.HEAD).add(2.2f, 0, 0);
            map.get(Limb.RIGHT_ARM).add(0, 0, 1.4f);
            map.get(Limb.LEFT_ARM).add(0, 0, -1.8f);
            map.get(Limb.LEFT_FOREARM).add(-2.5f, 0, 0);
            return new Pose(map);
        }
    }

    /** Ticks per half breath; the full idle breath takes twice this. */
    public static final int BREATH = 30;
    /** Model height in blocks (steve top of head); the figure is scaled so this spans {@code height} canvas pixels. */
    static final float MODEL_HEIGHT = 30 / 16f;
    /**
     * Held weapon on steve's right-item bone, in the weapon's FIXED display space: barrel forward with a slight
     * downward tip, grip up into the fist. Tuned on the live screen (side and three-quarter views) with Ace of
     * Spades, Duke Mk. 44 and Halfdan-D and a forearm at -30.
     */
    static final Vector3f GRIP_TURN = new Vector3f(40, -90, 0);
    /** Block units in the turned weapon space: moves the model forward so its grip, not its centre, sits in the hand. */
    static final Vector3f GRIP_OFFSET = new Vector3f(0.3f, 0.07f, 0);
    /** Depth kept per block of model depth, as a fraction of the on-screen scale. */
    static final float DEPTH_FLATTEN = .04f;

    private record Cached(Object profile, CompletableFuture<SkinData> future) { }
    private static final Map<UUID, Cached> SKINS = new ConcurrentHashMap<>();

    private PlayerFigure() { }

    /** The completed skin, or BetterModel's fallback while the player's own skin loads. */
    static SkinData skin(ServerPlayer player) {
        var skins = BetterModel.platform().skinManager();
        var cached = SKINS.get(player.getUUID());
        if (cached == null || !cached.profile.equals(player.getGameProfile())) {
            CompletableFuture<SkinData> future;
            try {
                var profile = ModelProfile.of(ModPlayer.of(player.connection));
                future = skins.complete(profile.asUncompleted()).thenApply(s -> (SkinData) s)
                        .completeOnTimeout(null, 30, java.util.concurrent.TimeUnit.SECONDS)
                        .exceptionally(error -> { DestinyGuardians.LOGGER.warn("Player figure skin failed for {}", player.getUUID(), error); return null; });
            } catch (RuntimeException | LinkageError e) {
                DestinyGuardians.LOGGER.warn("Player figure skin unavailable for {}", player.getUUID(), e);
                future = CompletableFuture.completedFuture(null);
            }
            cached = new Cached(player.getGameProfile(), future);
            SKINS.put(player.getUUID(), cached);
        }
        var done = cached.future.getNow(null);
        return done != null ? done : skins.fallback();
    }

    public static void forget(UUID player) { SKINS.remove(player); }

    /**
     * Draws the figure standing with its feet at canvas ({@code x}, {@code footY}), {@code height} canvas pixels tall,
     * turned {@code yaw} degrees from facing the viewer, centred on HUD layer {@code depth}.
     */
    public static void draw(HudPainter painter, ServerPlayer player, String key, float x, float footY, float height,
                            float depth, float yaw, Pose pose, ItemStack held, String heldKey) {
        SkinData skin;
        try { skin = skin(player); }
        catch (RuntimeException | LinkageError e) { return; }
        if (skin == null) return;
        // Idle breath: a two-key loop blended by the client, so the server sends one pose every BREATH ticks.
        int phase = (player.level().getServer().getTickCount() / BREATH) % 2;
        pose = pose.breath(phase);
        float k = height / MODEL_HEIGHT * DisplayHudManager.unitX; // display units per block
        var root = new Matrix4f()
                .translate(anchor(x, footY, depth))
                .scale(k, k, k * DEPTH_FLATTEN)
                .rotateY((float) Math.toRadians(180 + yaw));
        Map<Limb, Matrix4f> bones = new EnumMap<>(Limb.class);
        String skinKey = Integer.toHexString(System.identityHashCode(skin));
        for (var limb : Limb.values()) {
            var parent = limb.parent == null ? root : bones.get(limb.parent);
            var origin = limb.parent == null ? new Vector3f() : limb.parent.pivot;
            var r = pose.of(limb); // Blockbench angles; mirrored X flips the Y and Z turns
            var m = new Matrix4f(parent).translate(new Vector3f(limb.pivot).sub(origin))
                    .rotate(new Quaternionf().rotationZYX((float) Math.toRadians(-r.z), (float) Math.toRadians(-r.y), (float) Math.toRadians(r.x)));
            bones.put(limb, m);
            TransformedItemStack item;
            try { item = limb.item.apply(skin); }
            catch (RuntimeException | LinkageError e) { continue; }
            if (item == null || item.isAir()) continue;
            var placed = new Matrix4f(m).translate(item.position()).translate(item.offset()).scale(item.scale());
            ItemStack stack = ((ModItemStack) item.itemStack()).source();
            painter.model(key + "_" + limb.name().toLowerCase(java.util.Locale.ROOT), stack, skinKey,
                    ItemDisplayContext.FIXED, new Transformation(placed), BREATH);
        }
        if (held != null && !held.isEmpty()) {
            // steve's pri_right_item bone position: (5.625, 10.875, 0) px on the right forearm.
            var hand = new Matrix4f(bones.get(Limb.RIGHT_FOREARM))
                    .translate(new Vector3f(-5.625f, 10.875f, 0).div(16).sub(Limb.RIGHT_FOREARM.pivot));
            // FIXED context: every weapon model shares the same fixed display turn (Y 90, centred), unlike the
            // third-person transforms that differ between one-hand, two-hand and legacy models.
            hand.rotateXYZ((float) Math.toRadians(GRIP_TURN.x), (float) Math.toRadians(GRIP_TURN.y), (float) Math.toRadians(GRIP_TURN.z))
                    .translate(GRIP_OFFSET);
            painter.model(key + "_held", held, heldKey, ItemDisplayContext.FIXED, new Transformation(hand), BREATH);
        }
    }

    /** DisplayHud CENTER-aligned translation of canvas point ({@code x}, {@code y}) on layer {@code depth}. */
    static Vector3f anchor(float x, float y, float depth) {
        float ux = DisplayHudManager.unitX, uy = DisplayHudManager.unitY;
        int gap = DisplayHudManager.alignmentGap;
        return new Vector3f((DisplayHudManager.screenX / 2 - x) * ux,
                (float) (-1.5 * gap - 0.178 + (DisplayHudManager.screenY / 2 - y) * uy - gap * 2L),
                -depth * 100);
    }
}
