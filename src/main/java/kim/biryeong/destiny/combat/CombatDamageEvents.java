package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

/** Read-only actual-loss observation. The dispatcher owns no activity statistics or encounter state. */
public final class CombatDamageEvents {
    public record Applied(ServerPlayer source, LivingEntity recipient, AmmoGeneration attribution, double damage, boolean killed) { }
    private static final List<Consumer<Applied>> LISTENERS = new CopyOnWriteArrayList<>();
    private CombatDamageEvents() { }
    public static AutoCloseable subscribe(Consumer<Applied> listener) {
        LISTENERS.add(listener);
        return () -> LISTENERS.remove(listener);
    }
    static void applied(ServerPlayer source, LivingEntity recipient, AmmoGeneration attribution, double damage, boolean killed) {
        if (!Double.isFinite(damage) || damage <= 0) return;
        var event = new Applied(source, recipient, attribution, damage, killed);
        for (var listener : LISTENERS) {
            try { listener.accept(event); }
            catch (RuntimeException failure) {
                // A failed observer is detached once; damage, attribution and rewards still complete normally.
                LISTENERS.remove(listener);
                DestinyGuardians.LOGGER.error("Combat observation detached after failure", failure);
            }
        }
    }
}
