package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.weapon.WeaponAce;
import kim.biryeong.destiny.weapon.WeaponAiming;
import kim.biryeong.destiny.weapon.WeaponExotics;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.minecraft.server.level.ServerPlayer;

import java.util.ArrayList;
import java.util.List;

/** Memento Mori shot-count pips, as described in Bungie's Season 21 weapon preview:
 * https://www.bungie.net/7/en/News/Article/season_21_weapon_preview
 * Placement is an authored approximation, not pixel-exact original artwork.
 * Server-thread presentation only: no grants, timers or mutable player caches.
 */
public final class AceReticleCounter {
    public static final String PREFIX = "destiny:ace_counter_w158_";
    public static final int MAX_NODES = 6;
    public static final int EARNED_COLOR = 0xF1F3F5;
    public static final int EMPTY_COLOR = 0x50545A;

    /** Immutable screen-space pip; coordinates use the shared 1920 x 1080 HUD canvas. */
    public record Pip(String id, float x, float y, float width, float height, int color) { }

    private AceReticleCounter() { }

    /** Six fixed slots whenever Mori is active; zero (including negative input) hides all slots.
     * Only brightness changes as earned rounds are spent, so the counter never shifts the sight.
     */
    public static List<Pip> layout(int rounds) {
        int earned = Math.clamp(rounds, 0, MAX_NODES);
        if (earned == 0) return List.of();
        List<Pip> pips = new ArrayList<>(MAX_NODES);
        for (int i = 0; i < MAX_NODES; i++) {
            pips.add(new Pip(PREFIX + "pip_" + i, 945 + i * 6, 578, 3, 7,
                    i < earned ? EARNED_COLOR : EMPTY_COLOR));
        }
        return List.copyOf(pips);
    }

    /** Reads authoritative remaining shots only after lifecycle, presentation and loadout guards. */
    public static void update(ServerPlayer player) {
        if (!player.isAlive() || player.isRemoved() || player.hasDisconnected() || player.isSpectator()
                || AbilityService.inSuper(player) || WeaponRuntime.reloading(player)
                || WeaponAiming.scoped(player) || !WeaponLoadout.canUse(player)
                || WeaponItems.entry(player.getMainHandItem()).filter(WeaponExotics::ace).isEmpty()) {
            remove(player);
            return;
        }
        List<Pip> pips = layout(WeaponAce.rounds(player));
        if (pips.isEmpty()) {
            remove(player);
            return;
        }
        // Retire obsolete nodes from this owner only, keeping the live set bounded to six.
        List<String> ids = pips.stream().map(Pip::id).toList();
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet())) {
            if (id.startsWith(PREFIX) && !ids.contains(id)) DisplayHud.removeHud(player, id);
        }
        for (Pip pip : pips) {
            CombatHud.sprite(player, pip.id(), "solid", pip.x(), pip.y(), pip.width(), pip.height(),
                    6, pip.color(), DisplayHud.HudAlignment.CENTER);
            DisplayHud.getHud(player, pip.id()).setAboveHand(true);
        }
    }

    /** Idempotent and prefix-local, including stale nodes; preserves the existing Mori HUD row. */
    public static void remove(ServerPlayer player) {
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet())) {
            if (id.startsWith(PREFIX)) DisplayHud.removeHud(player, id);
        }
    }
}
