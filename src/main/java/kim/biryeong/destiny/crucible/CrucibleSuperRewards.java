package kim.biryeong.destiny.crucible;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;

/** W273 local Minecraft tuning, NOT an official Destiny/DDC gain curve.
 * Each 20 points of actual health/absorption loss grants 1%; a killing hit adds 1.5%.
 * Combat owns this synchronous transaction; no tick task, death-listener payout or life ledger.
 */
public final class CrucibleSuperRewards {
    public static final float ENERGY_PER_HP = .01f / 20f;
    public static final float KILL_ENERGY = .015f;
    private static final ThreadLocal<Hit> ACTIVE = new ThreadLocal<>();

    private CrucibleSuperRewards() { }

    public static Hit begin(ServerPlayer owner, LivingEntity target, AmmoGeneration attribution) {
        var hit = new Hit(owner, target, ACTIVE.get(), attribution);
        ACTIVE.set(hit);
        return hit;
    }

    private static float remaining(LivingEntity target) {
        // Negative lethal health must not turn overkill into earned damage.
        return Math.max(0, target.getHealth()) + Math.max(0, target.getAbsorptionAmount());
    }

    public static final class Hit {
        private final ServerPlayer owner;
        private final LivingEntity target;
        private final Hit previous;
        private final float before;
        private final boolean aliveBefore;
        private final boolean eligible;
        private float childDelta;
        private boolean childKilled;
        private boolean finished;

        private Hit(ServerPlayer owner, LivingEntity target, Hit previous, AmmoGeneration attribution) {
            this.owner = owner;
            this.target = target;
            this.previous = previous;
            before = remaining(target);
            aliveBefore = target.isAlive() && !target.isDeadOrDying();
            // Capture before hurtServer: its death callback makes canFight false on a valid lethal hit.
            eligible = target instanceof ServerPlayer victim && owner != victim && aliveBefore
                    && owner.isAlive() && !owner.isRemoved() && !owner.hasDisconnected()
                    && !owner.isSpectator() && !victim.isSpectator() && !victim.hasDisconnected()
                    && Guardians.isGuardian(owner) && !AbilityService.inSuper(owner)
                    && attribution.kind() != AmmoGeneration.Kind.SUPER
                    && CrucibleRuntime.canFight(owner, victim);
        }

        /** Finish exactly once, including on exceptions. Nested same-victim changes
         * are subtracted from their parent, so one loss/death can never pay twice. */
        public void finish(boolean completed) {
            if (finished) return;
            if (ACTIVE.get() != this) throw new IllegalStateException("Out-of-order combat reward transaction");
            finished = true;
            if (previous == null) ACTIVE.remove(); else ACTIVE.set(previous);
            float inclusive = before - remaining(target);
            boolean died = aliveBefore && (!target.isAlive() || target.isDeadOrDying());
            for (Hit parent = previous; parent != null; parent = parent.previous) {
                if (parent.target != target) continue;
                parent.childDelta += inclusive;
                parent.childKilled |= died;
                break;
            }
            float loss = Math.max(0, Math.min(before, inclusive - childDelta));
            if (!completed || !eligible || !Float.isFinite(loss) || loss <= 0
                    || !owner.isAlive() || owner.isRemoved() || owner.hasDisconnected()
                    || AbilityService.inSuper(owner)) return;
            float gain = loss * ENERGY_PER_HP + (died && !childKilled ? KILL_ENERGY : 0);
            var data = Guardians.data(owner);
            data.setSuperEnergy(Math.min(1f, data.superEnergy() + gain));
        }
    }
}
