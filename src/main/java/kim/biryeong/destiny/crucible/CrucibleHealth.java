package kim.biryeong.destiny.crucible;

import net.minecraft.server.level.ServerPlayer;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Base (<=100 Health stat) DDC recovery: 100 health +130 shields, represented by one MC health bar.
 * Vanilla food healing is disabled only in the arena. Ability healing remains independent. */
public final class CrucibleHealth {
    private static final Map<UUID, Long> LAST_DAMAGE = new HashMap<>();
    private CrucibleHealth() {}
    public static void arrive(ServerPlayer p) { LAST_DAMAGE.put(p.getUUID(), p.level().getGameTime()); }
    public static void leave(ServerPlayer p) { LAST_DAMAGE.remove(p.getUUID()); }
    public static void damaged(ServerPlayer p, boolean healthLost) {
        if (healthLost && CrucibleRuntime.participating(p))
            LAST_DAMAGE.put(p.getUUID(), p.level().getGameTime());
    }
    public static double recoveredHp(double hp, long quietTicks) {
        if (!Double.isFinite(hp) || hp <= 0 || hp >= 230) return hp;
        if (hp < 100 && quietTicks >= 35) hp = Math.min(100, hp + 31.25 / 20);
        if (quietTicks >= 106) hp = Math.min(230, hp + 39.5 / 20);
        return hp;
    }
    public static void tick(ServerPlayer p) {
        if (!p.isAlive() || !CrucibleRuntime.canAct(p)) return;
        long last = LAST_DAMAGE.getOrDefault(p.getUUID(), p.level().getGameTime());
        double hp = p.getHealth() * 230.0 / p.getMaxHealth();
        double next = recoveredHp(hp, p.level().getGameTime() - last);
        if (next > hp) p.setHealth((float)(next * p.getMaxHealth() / 230.0));
    }
}
