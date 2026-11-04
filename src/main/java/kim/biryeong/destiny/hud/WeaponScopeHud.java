package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.weapon.WeaponAiming;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponExotics;
import kim.biryeong.destiny.weapon.WeaponIzanagi;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.minecraft.server.level.ServerPlayer;

import java.util.List;

/** Reference-informed original scope artwork, driven only by actual server ADS.
 * Vanilla servers cannot read F5: graphics follow ADS in every perspective, while the
 * context-aware held-item wrapper hides the gun in first person only. No camera is forced.
 * This sidecar never ticks/saves a magazine or changes zoom, recoil, damage or identity.
 */
public final class WeaponScopeHud {
    public static final String PREFIX = "destiny:scope_w45_";
    public static final String FRAME_ID = PREFIX + "frame";
    public static final String CENTER_ID = PREFIX + "center";
    public static final int MAX_NODES = 2;

    private WeaponScopeHud() {}

    public static void update(ServerPlayer player, boolean reloading) {
        if (reloading || !player.isAlive() || player.isRemoved() || player.hasDisconnected()
                || player.isSpectator() || !WeaponAiming.scoped(player)) {
            remove(player);
            return;
        }
        var entry = WeaponItems.entry(player.getMainHandItem()).orElseThrow();
        boolean sniper = entry.family().equals("sniper_rifle");
        boolean izanagi = WeaponExotics.izanagi(entry);
        String artwork = (izanagi ? "scope_w162_" : "scope_w45_") + entry.id();
        // W84 remains the sole authority for funded charge; a cosmetic selector grants nothing.
        int tint = izanagi && WeaponIzanagi.charge(player.getMainHandItem()) >= 2 ? 0xFFAA8C : 0xFFFFFF;
        // A wide black extension preserves a circular aperture up through 32:9 without stretching it.
        // Normal depth keeps the existing vitals/ammunition/abilities above the sniper mask.
        if (sniper) {
            CombatHud.sprite(player, FRAME_ID, artwork + "_frame", 960, 540,
                    3840, 3840, 0, tint, DisplayHud.HudAlignment.CENTER);
        } else {
            // LFR optics stay real 3D held models with an open aperture, never a flat HUD receiver.
            DisplayHud.removeHud(player, FRAME_ID);
        }
        CombatHud.sprite(player, CENTER_ID, artwork + "_reticle", 960, 540,
                80, 80, 6, tint, DisplayHud.HudAlignment.CENTER);
        DisplayHud.getHud(player, CENTER_ID).setAboveHand(true);
    }

    public static void remove(ServerPlayer player) {
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet())) {
            if (id.startsWith(PREFIX)) DisplayHud.removeHud(player, id);
        }
    }
}
