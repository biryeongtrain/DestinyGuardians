package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.minecraft.server.level.ServerPlayer;

/** The required pack hides vanilla's large cross/attack indicator so it cannot obscure scope sights.
 * A small replacement dot keeps ordinary tools, empty hands and supers aimable. Actual weapons
 * own their own reticle; never stack a second dot inside a hollow scope ring/chevron.
 */
public final class FallbackAimHud {
    public static final String ID = "destiny:aim_fallback_w45";

    private FallbackAimHud() {}

    public static void update(ServerPlayer player) {
        if (!player.isAlive() || player.isRemoved() || player.hasDisconnected() || player.isSpectator()
                || WeaponRuntime.reloading(player)
                || (!kim.biryeong.destiny.ability.AbilityService.inSuper(player)
                    && kim.biryeong.destiny.weapon.WeaponLoadout.canUse(player)
                    && kim.biryeong.destiny.weapon.WeaponItems.entry(player.getMainHandItem())
                        .filter(e -> kim.biryeong.destiny.weapon.WeaponAimPresentation.physicalSight(e,
                                kim.biryeong.destiny.weapon.WeaponAiming.progress(player))).isPresent())
                || DisplayHud.getHud(player, WeaponReticleHud.CENTER_ID) != null
                || DisplayHud.getHud(player, WeaponScopeHud.CENTER_ID) != null
                || DisplayHud.getHud(player, AmmoHud.PREFIX + "glaive_reticle") != null) {
            remove(player);
            return;
        }
        CombatHud.sprite(player, ID, "reticle_w44_dot", 960, 540, 4, 4, 6, 0xF1F3F5,
                DisplayHud.HudAlignment.CENTER);
        DisplayHud.getHud(player, ID).setAboveHand(true);
    }

    public static void remove(ServerPlayer player) {
        DisplayHud.removeHud(player, ID);
    }
}
