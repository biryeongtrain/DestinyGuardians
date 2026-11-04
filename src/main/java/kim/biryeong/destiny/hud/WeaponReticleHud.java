package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponChargeState;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.destiny.weapon.WeaponBowWindow;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.minecraft.server.level.ServerPlayer;

import java.util.List;

/** Original, pack-backed family reticles. Cosmetic bloom is supplied by the authoritative weapon runtime.
 * The two base quads use stable identities; the aim point never wanders. Active fusion/linear
 * charge feedback or physical-optic rocket tracking adds at most four solid ticks
 * using the same post-effect pass (the two families are mutually exclusive).
 * All methods run on the server thread, like CombatHud. Glaive HUD ownership stays with W41.
 */
public final class WeaponReticleHud {
    public static final String PREFIX = "destiny:reticle_w44_";
    public static final String FRAME_ID = PREFIX + "frame";
    public static final String CENTER_ID = PREFIX + "center";
    public static final int MAX_NODES = 2;
    public static final int MAX_CHARGE_NODES = 4;
    public static final int MAX_TRACKING_NODES = 4;
    public static final String TRACKING_TOP_ID = PREFIX + "tracking_top";
    public static final int MAX_TOTAL_NODES = MAX_NODES + MAX_CHARGE_NODES;
    public static final int TRACKING_ACQUIRING = 0xF6D66B;
    public static final int TRACKING_LOCKED = 0xE85C50;
    private static final int WHITE = 0xF1F3F5;
    private static final List<String> CHARGE_IDS = List.of(PREFIX + "charge_top", PREFIX + "charge_right",
            PREFIX + "charge_bottom", PREFIX + "charge_left");
    private static final List<String> TRACKING_IDS = List.of(TRACKING_TOP_ID, PREFIX + "tracking_right",
            PREFIX + "tracking_bottom", PREFIX + "tracking_left");
    private static final int CHARGE_STEPS = 16;

    private record Style(String image, float hipWidth, float hipHeight,
                         float adsWidth, float adsHeight, float bloomPixels) { }

    private WeaponReticleHud() { }

    /** Inputs are normalized to finite [0,1]; invalid values safely fall back to a rested hip reticle.
     * Reload hides the gun reticle without inventing a reload timer or changing any weapon state.
     * No weapon, magazine, ADS, recoil or loadout state is mutated here.
     */
    public static void update(ServerPlayer player, float aimProgress, float bloom, boolean reloading) {
        if (!player.isAlive() || player.isRemoved() || player.hasDisconnected() || player.isSpectator()) {
            remove(player);
            return;
        }
        // Golden Gun owns finite shots independently of the underlying inventory
        // gun's scope/reload/bloom. Other supers keep the existing fallback dot.
        if (AbilityService.inSuper(player)) {
            var superAmmo = AmmoHud.current(player).filter(kim.biryeong.destiny.weapon.WeaponAmmoState::superWeapon);
            if (superAmmo.isPresent()) superWeaponReticle(player, superAmmo.get().rounds());
            else remove(player);
            return;
        }
        if (reloading || kim.biryeong.destiny.weapon.WeaponAiming.scoped(player)
                || !WeaponLoadout.canUse(player)) {
            remove(player);
            return;
        }
        var entry = WeaponItems.entry(player.getMainHandItem());
        boolean physicalSight = entry.filter(e ->
                kim.biryeong.destiny.weapon.WeaponAimPresentation.physicalSight(e, aimProgress)).isPresent();
        Style style = entry.map(WeaponReticleHud::style).orElse(null);
        if (style == null) {
            remove(player);
            return;
        }
        float aim = normalized(aimProgress);
        float expansion = normalized(bloom) * style.bloomPixels();
        float width = halfPixel(style.hipWidth() + (style.adsWidth() - style.hipWidth()) * aim + expansion);
        float height = halfPixel(style.hipHeight() + (style.adsHeight() - style.hipHeight()) * aim + expansion);
        String family = entry.orElseThrow().family();
        // Query only after ordinary eligibility and only for the two authoritative charge families.
        WeaponChargeState charge = family.equals("fusion_rifle") || family.equals("linear_fusion_rifle")
                ? WeaponRuntime.chargeState(player) : WeaponChargeState.idle();
        float chargeProgress = (float) Math.floor(charge.progress() * CHARGE_STEPS) / CHARGE_STEPS;
        if (charge.phase() == WeaponChargeState.Phase.CHARGING) {
            float scale = 1 - .25f * chargeProgress;
            width = halfPixel(width * scale); height = halfPixel(height * scale);
        }
        int color = WHITE;
        if (entry.orElseThrow().family().equals("bow")) {
            var draw = WeaponRuntime.bowDrawState(player);
            // Authored readable feedback, not a claim of pixel-exact original reticle art.
            // Late warning does not pretend an unimplemented accuracy/damage penalty exists.
            if (draw.phase() == WeaponBowWindow.Phase.DRAWING || draw.phase() == WeaponBowWindow.Phase.PERFECT) {
                float scale = 1 - .35f * draw.progress();
                width = halfPixel(width * scale); height = halfPixel(height * scale);
            }
            color = switch (draw.phase()) {
                case PERFECT -> 0xF6D66B;
                case LATE -> 0xD6A36F;
                default -> WHITE;
            };
        }
        var tracking = entry.orElseThrow().family().equals("rocket_launcher")
                ? kim.biryeong.destiny.weapon.WeaponTracking.status(player) : null;
        if(tracking != null) {
            // Local legible lock feedback, not claimed to be pixel-exact Destiny artwork.
            color=switch(tracking.phase()) {
                case ACQUIRING -> TRACKING_ACQUIRING;
                case LOCKED -> TRACKING_LOCKED;
                default -> WHITE;
            };
        }
        String image=style.image().startsWith("w105_shotgun_")?"reticle_"+style.image():"reticle_w44_"+style.image();
        if (!physicalSight) {
            CombatHud.sprite(player, FRAME_ID, image, 960, 540,
                    width, height, 5, color, DisplayHud.HudAlignment.CENTER);
            CombatHud.sprite(player, CENTER_ID, "reticle_w44_dot", 960, 540,
                    4, 4, 6, WHITE, DisplayHud.HudAlignment.CENTER);
            DisplayHud.getHud(player, FRAME_ID).setAboveHand(true);
            DisplayHud.getHud(player, CENTER_ID).setAboveHand(true);
        } else {
            // A real optic replaces the hip ring/dot, not the authoritative
            // fusion charge / remaining-bolt feedback surrounding that optic.
            DisplayHud.removeHud(player, FRAME_ID);
            DisplayHud.removeHud(player, CENTER_ID);
        }
        boolean chargeActive = charge.phase() != WeaponChargeState.Phase.IDLE;
        if (chargeActive) chargeTicks(player, charge, chargeProgress, width, height);
        // A physical rocket optic must not erase earned tracking feedback along
        // with the hip ring. Four thin ticks surround (never cover) the real sight.
        // Fusion charge and rocket tracking are disjoint families: at most six nodes.
        boolean trackingActive = physicalSight && tracking != null
                && tracking.phase() != kim.biryeong.destiny.weapon.WeaponTracking.Phase.IDLE;
        if (trackingActive) trackingTicks(player, tracking.ticks(), color);
        // Remove obsolete W44 parts after a swap/reconnect without touching ammo, super or glaive HUDs.
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet())) {
            if (id.startsWith(PREFIX) && !id.equals(FRAME_ID) && !id.equals(CENTER_ID)
                    && !(chargeActive && CHARGE_IDS.contains(id))
                    && !(trackingActive && TRACKING_IDS.contains(id)))
                DisplayHud.removeHud(player, id);
        }
    }

    private static void trackingTicks(ServerPlayer player, int ticks, int color) {
        float length = halfPixel(2 + 6 * Math.clamp(ticks / 20f, 0, 1));
        for (int i = 0; i < MAX_TRACKING_NODES; i++) {
            float x = 960 + (i == 1 ? 32 : i == 3 ? -32 : 0);
            float y = 540 + (i == 2 ? 32 : i == 0 ? -32 : 0);
            String id = TRACKING_IDS.get(i);
            CombatHud.sprite(player, id, "solid", x, y, i % 2 == 0 ? length : 2,
                    i % 2 == 0 ? 2 : length, 6, color, DisplayHud.HudAlignment.CENTER);
            DisplayHud.getHud(player, id).setAboveHand(true);
        }
    }

    /** Reuses the bounded hand-cannon ring as authored Solar aim feedback, not
     * a claim of an extracted/pixel-exact Destiny reticle. No simulated recoil,
     * charge, shot ownership or extra node set: the shared centre never moves.
     */
    private static void superWeaponReticle(ServerPlayer player, int rounds) {
        CombatHud.sprite(player, FRAME_ID, "reticle_w44_hand_cannon", 960, 540,
                40, 40, 5, rounds > 0 ? 0xF4D36A : 0xF16B5B, DisplayHud.HudAlignment.CENTER);
        CombatHud.sprite(player, CENTER_ID, "reticle_w44_dot", 960, 540,
                4, 4, 6, WHITE, DisplayHud.HudAlignment.CENTER);
        DisplayHud.getHud(player, FRAME_ID).setAboveHand(true);
        DisplayHud.getHud(player, CENTER_ID).setAboveHand(true);
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet())) {
            if (id.startsWith(PREFIX) && !id.equals(FRAME_ID) && !id.equals(CENTER_ID))
                DisplayHud.removeHud(player, id);
        }
    }

    /** Authored Destiny-inspired feedback, not pixel-exact canonical art. No ready/auto-fire timer.
     * Four solid ticks travel inward during charge; burst tick length shows remaining/total bolts.
     * Sixteen charge steps and half-pixel geometry bound metadata without a per-player cache.
     */
    private static void chargeTicks(ServerPlayer player, WeaponChargeState charge, float progress,
                                    float frameWidth, float frameHeight) {
        boolean charging = charge.phase() == WeaponChargeState.Phase.CHARGING;
        float gap = charging ? 10 - 6 * progress : 4;
        float xRadius = halfPixel(frameWidth / 2 + gap);
        float yRadius = halfPixel(frameHeight / 2 + gap);
        float length = halfPixel(charging ? 2 + 6 * progress
                : 8f * (charge.totalBolts() - charge.emittedBolts()) / charge.totalBolts());
        int color = charging ? 0xF6D66B : WHITE;
        for (int i = 0; i < MAX_CHARGE_NODES; i++) {
            boolean horizontal = i % 2 == 0;
            float x = 960 + (i == 1 ? xRadius : i == 3 ? -xRadius : 0);
            float y = 540 + (i == 2 ? yRadius : i == 0 ? -yRadius : 0);
            String id = CHARGE_IDS.get(i);
            CombatHud.sprite(player, id, "solid", x, y, horizontal ? length : 2,
                    horizontal ? 2 : length, 6, color, DisplayHud.HudAlignment.CENTER);
            DisplayHud.getHud(player, id).setAboveHand(true);
        }
    }

    /** Idempotent prefix-local cleanup; the caller also invokes this on disconnect. */
    public static void remove(ServerPlayer player) {
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet())) {
            if (id.startsWith(PREFIX)) DisplayHud.removeHud(player, id);
        }
    }

    private static float normalized(float value) {
        return Float.isFinite(value) ? Math.clamp(value, 0f, 1f) : 0f;
    }

    private static float halfPixel(float value) { return Math.round(value * 2) / 2f; }

    private static Style circle(String image, float hip, float ads, float bloom) {
        return new Style(image, hip, hip, ads, ads, bloom);
    }

    private static Style style(WeaponCatalog.Entry entry) {
        return switch (entry.family()) {
            case "hand_cannon" -> circle("hand_cannon", 40, 30, 10);
            case "sidearm" -> circle("sidearm", 34, 26, 8);
            case "auto_rifle" -> circle("auto_rifle", 44, 30, 10);
            case "pulse_rifle" -> circle("pulse_rifle", 42, 28, 8);
            case "submachine_gun" -> circle("submachine_gun", 46, 32, 12);
            case "machine_gun" -> circle("machine_gun", 50, 34, 10);
            case "scout_rifle" -> circle("scout_rifle", 36, 24, 6);
            case "sniper_rifle" -> new Style("sniper_rifle", 46, 40, 24, 18, 4);
            case "linear_fusion_rifle" -> new Style("linear_fusion_rifle", 42, 36, 24, 20, 4);
            case "shotgun" -> shotgun(entry);
            case "fusion_rifle" -> new Style("fusion_rifle", 52, 42, 36, 30, 10);
            case "trace_rifle" -> circle("trace_rifle", 32, 24, 6);
            case "bow" -> circle("bow", 44, 28, 6);
            case "grenade_launcher" -> new Style("grenade_launcher", 50, 54, 40, 44, 6);
            case "heavy_grenade_launcher" -> new Style("heavy_grenade_launcher", 56, 58, 44, 48, 8);
            case "rocket_launcher" -> circle("rocket_launcher", 62, 46, 6);
            // Melee swords and the independently owned glaive sight never get a gun reticle.
            default -> null;
        };
    }

    private static Style shotgun(WeaponCatalog.Entry entry) {
        var shape=kim.biryeong.destiny.weapon.ShotgunPatternProfile.shape(entry);
        if(shape.isEmpty())return circle("shotgun",78,64,12);
        return switch(shape.get()) {
            case SLUG -> circle("shotgun_slug",34,26,6);
            case CONE -> circle("w105_shotgun_aggressive",78,64,12);
            case VERTICAL_OVAL -> circle("w105_shotgun_precision",78,64,12);
            case DIAMOND -> circle("w105_shotgun_lightweight",78,64,12);
            case SQUARE -> circle("w105_shotgun_rapid_fire",78,64,12);
        };
    }
}
