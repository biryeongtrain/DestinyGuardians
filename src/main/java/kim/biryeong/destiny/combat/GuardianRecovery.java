package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.down.GuardianDown;
import net.minecraft.server.level.ServerPlayer;

import java.util.HashMap;
import java.util.Map;

/** PvE base Health stat: 70 health + 130 shields represented by one Minecraft health bar.
 * DDC Game Mechanics rows 106-114 (2026-10-30 snapshot): 1.75s / 21.89 HP/s,
 * shield prose 5.3s / 39.5 HP/s. The table conflicts (4.9s / 2.9s); use prose for
 * shields, consistently with CrucibleHealth. This does not add PvE damage resistance.
 * Only health damage interrupts recovery; overshield-only hits and firing do not.
 */
public final class GuardianRecovery {
    private static final Map<ServerPlayer, Long> LAST_DAMAGE = new HashMap<>();

    private GuardianRecovery() { }

    public static void forget(ServerPlayer player) { LAST_DAMAGE.remove(player); }

    public static void damaged(ServerPlayer player, boolean healthLost) {
        if (healthLost) LAST_DAMAGE.put(player, (long) player.level().getServer().getTickCount());
    }

    public static double recoveredHp(double hp, long quietTicks) {
        if (!Double.isFinite(hp) || hp <= 0 || hp >= 200) return hp;
        if (hp < 70 && quietTicks >= 35) hp = Math.min(70, hp + 21.89 / 20);
        if (quietTicks >= 106) hp = Math.min(200, hp + 39.5 / 20);
        return hp;
    }

    public static void tick(ServerPlayer player) {
        // Crucible owns its separate 230 HP pool and recovery tick. Never heal twice.
        if (CrucibleRuntime.participating(player) || !player.isAlive() || player.isSpectator()
                || GuardianDown.active(player)) {
            forget(player);
            return;
        }
        long now = player.level().getServer().getTickCount();
        long last = LAST_DAMAGE.computeIfAbsent(player, ignored -> now);
        float max = player.getMaxHealth();
        if (!Float.isFinite(max) || max <= 0) return;
        double hp = player.getHealth() * 200.0 / max;
        double next = recoveredHp(hp, now - last);
        if (next > hp) player.setHealth((float) (next * max / 200.0));
    }
}
