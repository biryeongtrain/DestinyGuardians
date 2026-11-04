package kim.biryeong.destiny.combat;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Shared Stasis "Frozen" status (W322). The project had no Stasis verbs: local policy is an
 * immobilising slowness plus target loss for combatants; Guardians are only heavily slowed.
 * Frozen state is remembered until expiry even after death so final-blow perks can observe it.
 */
public final class StasisStatus {
    private record Frozen(ServerLevel level, long until) {}
    private static final Map<UUID, Frozen> FROZEN = new HashMap<>();
    private StasisStatus() {}

    public static void freeze(LivingEntity target, int ticks) {
        if (target == null || ticks <= 0 || !target.isAlive() || !(target.level() instanceof ServerLevel level)) return;
        long until = level.getGameTime() + ticks;
        FROZEN.merge(target.getUUID(), new Frozen(level, until), (a, b) -> a.level == b.level && a.until > b.until ? a : b);
        target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, target instanceof Player ? 3 : 9, false, false));
        if (!(target instanceof Player)) target.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, ticks, 4, false, false));
        if (target instanceof Mob mob) mob.setTarget(null);
    }
    /** Pure query; true while frozen, including a corpse observed in the killing tick. */
    public static boolean frozen(Entity target) {
        if (target == null) return false;
        var f = FROZEN.get(target.getUUID());
        return f != null && f.level == target.level() && f.until > f.level.getGameTime();
    }
    public static void tick(MinecraftServer server) {
        var it = FROZEN.entrySet().iterator();
        while (it.hasNext()) {
            var e = it.next(); var f = e.getValue();
            if (f.level.getServer() != server) continue;
            if (f.until <= f.level.getGameTime()) { it.remove(); continue; }
            if (f.level.getEntity(e.getKey()) instanceof Mob mob && mob.isAlive()) mob.setTarget(null);
        }
    }
    public static void forget(Entity entity) { if (entity != null) FROZEN.remove(entity.getUUID()); }
    public static void clear() { FROZEN.clear(); }
}
