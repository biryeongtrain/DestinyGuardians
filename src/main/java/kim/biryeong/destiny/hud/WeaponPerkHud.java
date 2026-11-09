package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.weapon.WeaponAce;
import kim.biryeong.destiny.weapon.WeaponAiming;
import kim.biryeong.destiny.weapon.WeaponArcherTempo;
import kim.biryeong.destiny.weapon.WeaponFeedingFrenzy;
import kim.biryeong.destiny.weapon.WeaponIzanagi;
import kim.biryeong.destiny.weapon.WeaponKillClip;
import kim.biryeong.destiny.weapon.WeaponOneForAll;
import kim.biryeong.destiny.weapon.WeaponOutlaw;
import kim.biryeong.destiny.weapon.WeaponRampage;
import kim.biryeong.destiny.weapon.WeaponSurrounded;
import kim.biryeong.destiny.weapon.WeaponSwashbuckler;
import kim.biryeong.destiny.weapon.WeaponMultikillClip;
import kim.biryeong.destiny.weapon.WeaponRapidHit;
import kim.biryeong.destiny.weapon.WeaponPerpetualMotion;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.minecraft.server.level.ServerPlayer;
import java.util.List;

/** Original pack-backed, bounded Destiny-inspired weapon-buff feed; observes actual runtime state. */
public final class WeaponPerkHud {
    public static final String PREFIX = WeaponPerkRows.PREFIX;
    private WeaponPerkHud() {}

    public static void update(ServerPlayer player) {
        var state = new WeaponPerkRows.Snapshot(
                WeaponKillClip.remaining(player), WeaponOutlaw.remaining(player),
                WeaponRampage.stacks(player), WeaponRampage.remaining(player),
                WeaponArcherTempo.remaining(player), WeaponAce.rounds(player), WeaponIzanagi.charge(player),
                WeaponAiming.noDistractions(player), WeaponFeedingFrenzy.stacks(player),
                WeaponFeedingFrenzy.remaining(player), WeaponOneForAll.remaining(player),
                WeaponSurrounded.active(player), WeaponSwashbuckler.stacks(player),
                WeaponSwashbuckler.remaining(player), WeaponMultikillClip.stacks(player),
                WeaponMultikillClip.remaining(player), WeaponRapidHit.stacks(player),
                WeaponRapidHit.remaining(player), WeaponPerpetualMotion.stacks(player), kim.biryeong.destiny.weapon.WeaponTapTheTrigger.remaining(player),
                kim.biryeong.destiny.weapon.WeaponFrenzy.remaining(player),
                kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.stacks(player),
                kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.remaining(player),
                kim.biryeong.destiny.weapon.WeaponFocusedFury.remaining(player),
                kim.biryeong.destiny.weapon.WeaponStatsForAll.remaining(player),
                kim.biryeong.destiny.weapon.WeaponHeatingUp.stacks(player),
                kim.biryeong.destiny.weapon.WeaponHeatingUp.remaining(player),
                kim.biryeong.destiny.weapon.WeaponThreatDetector.stacks(player),
                kim.biryeong.destiny.weapon.WeaponSurplus.stacks(player),
                kim.biryeong.destiny.weapon.WeaponKillingTally.stacks(player),
                kim.biryeong.destiny.weapon.WeaponWhirlwindBlade.stacks(player),
                kim.biryeong.destiny.weapon.WeaponWhirlwindBlade.remaining(player),
                kim.biryeong.destiny.weapon.WeaponEnGarde.remaining(player),
                // Aggregate observer deliberately survives ordinary source stow.
                kim.biryeong.destiny.weapon.WeaponAssassinsBlade.remaining(player),
                kim.biryeong.destiny.weapon.WeaponDynamicSway.stacks(player),
                kim.biryeong.destiny.weapon.WeaponBoxBreathing.ready(player),
                kim.biryeong.destiny.weapon.WeaponPulseMonitor.active(player),
                kim.biryeong.destiny.weapon.WeaponUnrelenting.active(player),
                kim.biryeong.destiny.weapon.WeaponHeadseeker.remaining(player),
                // Aggregate runtime observer includes active sources in stowed slots.
                kim.biryeong.destiny.weapon.WeaponSteadyHands.remaining(player));
        var extra = new java.util.ArrayList<WeaponPerkRows.Extra>();
        for (var b : kim.biryeong.destiny.weapon.PerkExpansionStats.buffs(player)) extra.add(new WeaponPerkRows.Extra(b.id(),b.stacks(),b.remainingTicks()));
        for (var b : kim.biryeong.destiny.weapon.PerkExpansionCombat.buffs(player)) extra.add(new WeaponPerkRows.Extra(b.id(),b.stacks(),b.remainingTicks()));
        for (var b : kim.biryeong.destiny.weapon.PerkExpansionSupport.buffs(player)) extra.add(new WeaponPerkRows.Extra(b.id(),b.stacks(),b.remainingTicks()));
        var rows = WeaponPerkRows.merge(WeaponPerkRows.project(state), extra);
        // Reconcile with the real registry, not a per-player cache. Remove hidden/deactivated rows first.
        for (String id : WeaponPerkRows.nodesToRemove(rows, List.copyOf(DisplayHud.getHuds(player).keySet())))
            DisplayHud.removeHud(player, id);
        for (var row : rows) render(player, row);
    }

    private static void render(ServerPlayer player, WeaponPerkRows.Row row) {
        var kind = row.kind();
        var layout = kind.layout;
        String key = PREFIX + kind.key;
        float y = row.y();
        var left = DisplayHud.HudAlignment.LEFT;
        int markerColor = kind == WeaponPerkRows.Kind.MEMENTO_MORI || kind == WeaponPerkRows.Kind.HONED_EDGE
                ? 0xF8D278 : 0x8DE2AF;
        CombatHud.sprite(player, key+"marker", "perk_buff_w61", 104, y, 18, 18, 2, markerColor, left);
        boolean compact = layout == WeaponPerkRows.Layout.TIMER;
        CombatHud.sprite(player, key+"label", row.label(), compact ? 168 : 184, y,
                compact ? 94 : 118, 24, 2, 0xF1F3F5, left);
        if (layout.counted()) {
            CombatHud.sprite(player, key+"x", "perk_stack_x_w83", 257, y, 10, 20, 2, 0xF1F3F5, left);
            int count = row.displayCount();
            if ((layout == WeaponPerkRows.Layout.DECIMAL_COUNT
                    || layout == WeaponPerkRows.Layout.DECIMAL_COUNT_TIMER) && count >= 10) {
                CombatHud.sprite(player, key+"count_tens", "ammo_digit_"+count/10, 268, y, 8, 20, 2, 0xF1F3F5, left);
                CombatHud.sprite(player, key+"count", "ammo_digit_"+count%10, 278, y, 8, 20, 2, 0xF1F3F5, left);
            } else {
                // Also reconcile locally: a previously rendered ten must never leave its tens sprite.
                DisplayHud.removeHud(player, key+"count_tens");
                CombatHud.sprite(player, key+"count", "ammo_digit_"+count, 271, y, 10, 20, 2, 0xF1F3F5, left);
            }
        }
        if (layout.timed()) {
            int seconds = row.seconds();
            float start = compact ? 232 : 292;
            CombatHud.sprite(player, key+"minutes", "ammo_digit_0", start, y, 10, 20, 2, 0xF1F3F5, left);
            CombatHud.sprite(player, key+"colon", "perk_colon_w61", start+9, y, 4, 20, 2, 0xF1F3F5, left);
            CombatHud.sprite(player, key+"tens", "ammo_digit_"+seconds/10, start+18, y, 10, 20, 2, 0xF1F3F5, left);
            CombatHud.sprite(player, key+"ones", "ammo_digit_"+seconds%10, start+30, y, 10, 20, 2, 0xF1F3F5, left);
        }
    }

    public static void remove(ServerPlayer player) {
        for (String id : WeaponPerkRows.nodesToRemove(List.of(), List.copyOf(DisplayHud.getHuds(player).keySet())))
            DisplayHud.removeHud(player, id);
    }
}
