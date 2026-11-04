package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.server.level.ServerPlayer;

/** Pure current-source numeric queries. No attachments, sessions, procs or lifecycle mutations. */
public final class WeaponImpulseAmplifier {
    private WeaponImpulseAmplifier() {}

    private static WeaponCatalog.Entry held(ServerPlayer player) {
        if (player == null || !player.isAlive() || player.isRemoved() || player.isSpectator()
                || player.hasDisconnected()
                || Guardians.runtimeIfPresent(player).map(r -> r.superSession != null).orElse(false)
                || !WeaponLoadout.canUse(player)) return null;
        var stack = player.getMainHandItem();
        int slot = player.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9 || player.getInventory().getItem(slot) != stack || stack.getCount() != 1)
            return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, ImpulseAmplifierProfile.ID).orElse(null);
        return ImpulseAmplifierProfile.supports(entry) && roll != null && entry.id().equals(roll.id())
            && ImpulseAmplifierProfile.rolls().contains(roll) ? entry : null;
    }

    public static boolean selected(ServerPlayer player) { return held(player) != null; }

    /** MASTER: outermost wrapper, after other trait plans and immediately before startReload.
     * Re-evaluate the raw curve with total colegal bonuses; do not scale already rounded ticks.
     * Existing accepted reloads are unchanged. SFA/TD/other reload traits have no distinct pair
     * in these exact pools. Only Code Duello and Nezarec's Whisper can pair with base Frenzy.
     */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer player, WeaponCatalog.Entry entry,
                                                WeaponReloadPolicy.Plan base) {
        var actual = held(player);
        if (actual == null || !actual.equals(entry) || base == null || base.incremental()
                || WeaponRuntime.reloadOwnedBy(player, player.getMainHandItem())) return base;
        int bonus = ImpulseAmplifierProfile.reloadBonus();
        if (WeaponPerks.selected(player.getMainHandItem(), FrenzyProfile.ID)
                .filter(r -> ImpulseAmplifierProfile.compatible(entry, FrenzyProfile.ID, r)).isPresent()
                && WeaponFrenzy.ownedRemaining(player, player.getMainHandItem()) > 0)
            bonus += FrenzyProfile.reloadBonus();
        return ImpulseAmplifierProfile.reloadPlan(entry, bonus, ImpulseAmplifierProfile.durationMultiplier(entry), base);
    }

    /** MASTER: sample exactly once at accepted paid projectile launch, alongside Rangefinder's
     * distinct-socket sample. Freeze in the Shot's initial velocity, never re-query in flight.
     * Rocket 1.10 is sourced. GL/glaive omission is unknown: preserve launchSpeed until resolved.
     * Invalid/foreign sources and nonpositive/nonfinite input are passed through unchanged.
     */
    public static double projectileSpeed(ServerPlayer player, WeaponCatalog.Entry entry, double launchSpeed) {
        if (!Double.isFinite(launchSpeed) || launchSpeed <= 0) return launchSpeed;
        var actual = held(player);
        if (actual == null || !actual.equals(entry)) return launchSpeed;
        var scalar = ImpulseAmplifierProfile.projectileSpeedScalar(entry);
        if (scalar.isEmpty()) return launchSpeed;
        double speed = launchSpeed * scalar.getAsDouble();
        return Double.isFinite(speed) ? speed : launchSpeed;
    }
}
