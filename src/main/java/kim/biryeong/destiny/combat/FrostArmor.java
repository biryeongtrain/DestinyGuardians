package kim.biryeong.destiny.combat;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Shared Stasis Frost Armor buff (W322; first used by Rimestealer).
 * DDC Weapon Perks gives no Frost Armor numbers: explicit local policy from
 * W322 mechanics.frostArmor (5% damage resistance per stack, 5 stacks, 10 s refreshed on gain).
 * Owner-identity scoped: a replacement player object never inherits or clears another's armor.
 */
public final class FrostArmor {
    /** Pure stack state. */
    public static final class Stacks {
        private int stacks; private long until = Long.MIN_VALUE;
        public void grant(long now, int amount, int max, int ticks) {
            if (amount <= 0 || max <= 0 || ticks <= 0) return;
            stacks = Math.min(max, (active(now) ? stacks : 0) + amount);
            until = now + ticks;
        }
        public boolean active(long now) { return stacks > 0 && now < until; }
        public int stacks(long now) { return active(now) ? stacks : 0; }
        public float resist(long now, float amount, double perStack) {
            int n = stacks(now);
            if (n <= 0 || !Float.isFinite(amount) || amount <= 0) return amount;
            return (float) (amount * Math.max(0, 1 - perStack * n));
        }
    }
    private record Armor(ServerPlayer owner, Stacks stacks) {}
    private static final Map<UUID, Armor> ARMOR = new HashMap<>();
    private FrostArmor() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static kim.biryeong.destiny.weapon.PerkBatchCProfile.FrostArmorRule rule() {
        return kim.biryeong.destiny.weapon.PerkBatchCProfile.frostArmor();
    }

    public static void grant(ServerPlayer p, int amount) {
        if (p == null || amount <= 0 || !p.isAlive() || p.isRemoved()) return;
        var a = ARMOR.get(p.getUUID());
        if (a == null || a.owner != p) { a = new Armor(p, new Stacks()); ARMOR.put(p.getUUID(), a); }
        a.stacks.grant(now(p), amount, rule().maxStacks(), rule().ticks());
    }
    public static int stacks(ServerPlayer p) {
        var a = p == null ? null : ARMOR.get(p.getUUID());
        return a == null || a.owner != p ? 0 : a.stacks.stacks(now(p));
    }
    /** Incoming damage hook (LivingEntityMixin, before vanilla armor). */
    public static float modifyIncoming(ServerPlayer p, float amount) {
        var a = p == null ? null : ARMOR.get(p.getUUID());
        return a == null || a.owner != p ? amount : a.stacks.resist(now(p), amount, rule().resistancePerStack());
    }
    public static void tick(MinecraftServer server) {
        ARMOR.values().removeIf(a -> a.owner.level().getServer() == server
                && (a.owner.isRemoved() || !a.stacks.active(now(a.owner))));
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var a = ARMOR.get(p.getUUID());
        if (a != null && a.owner == p) ARMOR.remove(p.getUUID());
    }
    public static void clear() { ARMOR.clear(); }
}
