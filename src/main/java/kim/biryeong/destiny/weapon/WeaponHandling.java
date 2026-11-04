package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Separate from firing/reload State: skill cancellation cannot reset switch deadlines or cadence.
 * Tracks actual stacks, never ammo copies, speculative shots, tasks, or a fabricated HUD timer. */
public final class WeaponHandling {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final WeaponSwapCycle cycle = new WeaponSwapCycle();
        ItemStack stack;
        WeaponCatalog.Entry outgoing;
        Session(ServerPlayer owner, ItemStack stack) {
            this.owner = owner; this.level = owner.level(); this.stack = stack;
            cycle.select(stack, now(owner), 0, 0);
        }
    }
    private WeaponHandling() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p);
    }
    private static int duration(ServerPlayer p, ItemStack stack, boolean ready) {
        int ticks = WeaponItems.entry(stack).map(WeaponHandlingProfile::of).filter(WeaponHandlingProfile::supported)
                .map(profile -> WeaponQuickdraw.handlingTicks(p,stack,ready,WeaponFirmlyPlanted.handlingTicks(p,stack,ready,WeaponElementalCapacitor.handlingTicks(p,stack,ready,WeaponSurplus.handlingTicks(p,stack,ready,WeaponThreatDetector.handlingTicks(p,stack,ready,WeaponStatsForAll.handlingTicks(p,stack,ready,WeaponFrenzy.handlingTicks(p,stack,ready,WeaponAdrenalineJunkie.handlingTicks(p,stack,ready,WeaponPerpetualMotion.handlingTicks(p,stack,ready,
                        ready ? profile.readyTicks() : profile.stowTicks())))))))))).orElse(0);
        ticks = PerkBatchA.handlingTicks(p,stack,ready,ticks); // W320 batch A
        return WeaponSlickdraw.handlingTicks(p,stack,ready,WeaponSteadyHands.handlingTicks(p,stack,ready,WeaponRecoveryHandling.handlingTicks(p,stack,ready,WeaponBackupPlan.handlingTicks(p,stack,ready,WeaponWellRounded.handlingTicks(p,stack,ready,WeaponPugilist.handlingTicks(p,stack,ready,WeaponEnsemble.handlingTicks(p,stack,ready,ticks)))))));
    }
    /** Observe inventory replacement/commands, including swaps to non-weapons, before inputs or ticks. */
    public static void update(ServerPlayer p) {
        if (!eligible(p)) { WeaponSwapPresentation.cleanup(p); WeaponEnsemble.cleanup(p); return; }
        WeaponEnsemble.update(p);
        select(p, p.getMainHandItem());
        var view = presentation(p);
        if (view.isPresent()) {
            var v = view.get();
            WeaponSwapPresentation.update(p, p.getMainHandItem(), v.outgoing(), v.phase(), v.progress());
        } else WeaponSwapPresentation.cleanup(p);
    }
    /** Called only at vanilla's validated selection mutation, while the outgoing stack is still held. */
    public static void selecting(ServerPlayer p, int slot) {
        if (!eligible(p) || slot < 0 || slot >= 9 || slot == p.getInventory().getSelectedSlot()) return;
        WeaponThreatDetector.update(p);
        update(p);
        select(p, p.getInventory().getItem(slot));
    }
    private static void select(ServerPlayer p, ItemStack desired) {
        Session s = SESSIONS.get(p.getUUID());
        if (s == null || s.owner != p || s.level != p.level()) {
            SESSIONS.put(p.getUUID(), new Session(p, desired)); return;
        }
        if (s.stack == desired) return;
        WeaponSwapPresentation.cleanup(p);
        boolean combatChange = WeaponItems.entry(s.stack).isPresent() || WeaponItems.entry(desired).isPresent();
        if (s.cycle.phase(now(p)) != WeaponSwapCycle.Phase.STOW)
            s.outgoing = WeaponItems.entry(s.stack).orElse(null);
        int stow = duration(p, s.stack, false);
        PerkBatchA.stowing(p, s.stack); // W320 batch A: after the outgoing stow duration
        WeaponAssassinsBlade.stowing(p,s.stack); WeaponUnrelenting.stowing(p,s.stack); WeaponWhirlwindBlade.stowing(p,s.stack); WeaponEnGarde.stowing(p,s.stack); WeaponOpeningShot.stowing(p,s.stack); WeaponBoxBreathing.stowing(p,s.stack); WeaponHeadseeker.stowing(p,s.stack); WeaponSteadyHands.stowing(p,s.stack); WeaponDynamicSway.released(p,s.stack);
        WeaponKillingTally.stowing(p,s.stack); WeaponSympatheticArsenal.stowing(p,s.stack);
        WeaponAdagio.stowing(p,s.stack); WeaponClownCartridge.stowing(p,s.stack);
        WeaponBackupPlan.stowing(p,s.stack);
        WeaponCornered.stowing(p,s.stack);
        WeaponEnsemble.stowing(p,s.stack);
        WeaponEnsemble.selecting(p,desired);
        PerkBatchB.selecting(p,s.stack,desired); // W321 batch B
        WeaponWellRounded.selecting(p,desired);
        WeaponBackupPlan.selecting(p,desired);
        // Capture outgoing Quickdraw first. A real incoming identity change then owns its own window.
        WeaponQuickdraw.selected(p, desired);
        WeaponRecoveryHandling.selecting(p, desired);
        WeaponSteadyHands.selecting(p, desired);
        int ready = duration(p, desired, true);
        s.cycle.select(desired, now(p), stow, ready);
        s.stack = desired;
        if (combatChange) WeaponRuntime.cancelUseForSkill(p);
    }
    /** Pure query. Timers never hide the real current ammo row or block ordinary building items. */
    public static boolean blocked(ServerPlayer p) { return remaining(p) > 0; }
    public record Readiness(long remainingTicks, WeaponSwapCycle.Phase phase) {}
    /** Read the actual current binding without observing/advancing a replacement.
     * Empty is deliberately not READY: fixtures may query between an inventory
     * mutation and the first server tick that establishes its Handling clock.
     * A cosmetic swap can be absent while this gameplay deadline still applies.
     */
    public static Optional<Readiness> readiness(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (!eligible(p) || s == null || s.owner != p || s.level != p.level()
                || s.stack != p.getMainHandItem() || WeaponItems.entry(s.stack).isEmpty())
            return Optional.empty();
        long tick = now(p);
        return Optional.of(new Readiness(s.cycle.remaining(tick), s.cycle.phase(tick)));
    }
    public static long remaining(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        return eligible(p) && s != null && s.owner == p && s.level == p.level()
                && s.stack == p.getMainHandItem() && WeaponItems.entry(s.stack).isPresent()
                ? s.cycle.remaining(now(p)) : 0;
    }
    public record Presentation(WeaponCatalog.Entry outgoing, WeaponSwapCycle.Phase phase, float progress) {}
    /** Observation of the existing Handling transaction, not an alternate switch controller. */
    public static Optional<Presentation> presentation(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (!eligible(p) || s == null || s.owner != p || s.level != p.level()
                || s.stack != p.getMainHandItem() || s.cycle.phase(now(p)) == WeaponSwapCycle.Phase.NONE)
            return Optional.empty();
        var incoming = WeaponItems.entry(s.stack).orElse(null);
        if (!WeaponSwapPresentation.supports(s.outgoing, incoming)) return Optional.empty();
        return Optional.of(new Presentation(s.outgoing, s.cycle.phase(now(p)), s.cycle.progress(now(p))));
    }
    public static void cleanup(ServerPlayer p) {
        WeaponSwapPresentation.cleanup(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { WeaponSwapPresentation.clearAll(); SESSIONS.clear(); }
}
