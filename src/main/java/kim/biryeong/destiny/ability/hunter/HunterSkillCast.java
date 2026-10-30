package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import java.util.Map;
import java.util.Objects;
import java.util.WeakHashMap;

/** Main-thread cast snapshot. No repeating global scheduler or player-retaining registry. */
public final class HunterSkillCast {
    // Opaque values MUST NOT refer to the weak player key. A newer ordinary cast owns the hand.
    private static final Map<ServerPlayer, Object> VISUAL_OWNER = new WeakHashMap<>();

    private final ServerPlayer player;
    private final ServerLevel level;
    private final GuardianRuntime runtime;
    private final GuardianClass guardianClass;
    private final AbilitySlot slot;
    private final Identifier equipped;
    private final SuperSession superSession;
    private final int acceptedTick;
    private final Object visualToken = new Object();
    private boolean modeled;

    /**
     * Parent hook: call before starting a super, and from AbilityService.cleanup.
     * Only revokes windups; existing projectiles/fields keep their own lifecycle checks.
     * This does not stop animations or clear someone else's visual equipment.
     */
    public static void cancelPending(ServerPlayer player) {
        VISUAL_OWNER.remove(player);
    }

    private HunterSkillCast(ServerPlayer player, AbilitySlot slot) {
        this.player = player;
        this.level = player.level();
        this.runtime = Guardians.runtime(player);
        this.guardianClass = Guardians.data(player).guardianClass();
        this.slot = slot;
        this.equipped = equipped();
        this.superSession = runtime.superSession;
        this.acceptedTick = level.getServer().getTickCount();
    }

    static HunterSkillCast snapshot(ServerPlayer player, AbilitySlot slot) {
        HunterSkillCast cast = new HunterSkillCast(player, slot);
        return cast.valid() ? cast : null;
    }

    static HunterSkillCast begin(ServerPlayer player, AbilitySlot slot, String animation, ItemStack hand) {
        HunterSkillCast cast = new HunterSkillCast(player, slot);
        if (!cast.valid()) return null;
        VISUAL_OWNER.put(player, cast.visualToken);
        cast.modeled = HunterAbilityVisuals.play(player, animation);
        if (cast.modeled && (slot == AbilitySlot.MELEE || slot == AbilitySlot.CLASS_ABILITY)) {
            if (hand.isEmpty()) PlayerAnimations.superEmptyHands(player);
            else PlayerAnimations.superItems(player, hand, ItemStack.EMPTY);
            if (slot == AbilitySlot.MELEE) player.swing(net.minecraft.world.InteractionHand.MAIN_HAND,
                    new net.minecraft.world.item.component.SwingAnimation(net.minecraft.world.item.SwingAnimationType.WHACK, 6), true);
        } else if (cast.modeled) PlayerAnimations.superItem(player, hand);
        return cast;
    }

    ServerLevel level() { return level; }
    boolean modeled() { return modeled; }

    private Identifier equipped() {
        return Guardians.data(player).loadout().map(l -> l.get(slot)).orElse(null);
    }

    /** Use for projectile impacts/cloud pulses too; a later ordinary cast does not erase a grenade. */
    boolean valid() {
        return player.isAlive() && !player.isRemoved() && !player.hasDisconnected() && !player.isSpectator()
                && player.level() == level && Guardians.runtime(player) == runtime
                && Guardians.data(player).guardianClass() == guardianClass
                && Objects.equals(equipped, equipped());
    }

    private boolean windupValid() {
        return valid() && VISUAL_OWNER.get(player) == visualToken && runtime.superSession == superSession;
    }

    void at(int delay, Runnable action) { schedule(delay, false, action); }
    void contact(int delay, Runnable action) { schedule(delay, true, action); }

    private void schedule(int delay, boolean releaseHand, Runnable action) {
        HunterSkillTiming timing = new HunterSkillTiming(acceptedTick, delay);
        Tasks.run(player, level, ignoredAge -> {
            if (timing.poll(level.getServer().getTickCount(), windupValid())) {
                // The prop leaves at contact; keep both rig hands bare through recovery.
                // EMPTY via superItem would restore the live gun before the clip finished.
                if (releaseHand && modeled) {
                    if (slot == AbilitySlot.MELEE || slot == AbilitySlot.CLASS_ABILITY) PlayerAnimations.superEmptyHands(player);
                    else PlayerAnimations.superItem(player, ItemStack.EMPTY);
                }
                if (releaseHand) VISUAL_OWNER.remove(player, visualToken);
                action.run();
            }
            return !timing.finished();
        });
    }
}
