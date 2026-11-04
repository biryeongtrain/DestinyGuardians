package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import java.util.*;

/** Killing Wind (W320): held-weapon final blows grant +20 Range, +50 Mobility, +40 Handling and
 * x1.05 falloff for 5s (+5s per kill, max 8s); stowing removes it. LOCAL POLICY: no Mobility stat,
 * so +50 maps to +20% movement speed (WeaponPerkMovement's 100 Mobility = x1.4 walking). */
final class WeaponKillingWind {
    static final Identifier ID = DestinyGuardians.id("killing_wind_mobility_w320");
    private static final Map<UUID, Owned> OWNED = new HashMap<>();
    private record Owned(ServerPlayer owner, AttributeInstance speed, AttributeModifier modifier) {
        void release() { if (speed.getModifier(ID) == modifier) speed.removeModifier(ID); }
    }
    private WeaponKillingWind() {}
    static void killed(PerkBatchA.Slot slot, long tick) {
        if (slot.has(KillingWindProfile.ID))
            slot.wind.killed(tick, KillingWindProfile.durationTicks(), KillingWindProfile.extendTicks(), KillingWindProfile.maxTicks());
    }
    private static boolean active(PerkBatchA.Slot slot, long tick) { return slot != null && slot.has(KillingWindProfile.ID) && slot.wind.active(tick); }
    static int rangeBonus(PerkBatchA.Slot slot, long tick) { return active(slot, tick) ? KillingWindProfile.rangeBonus() : 0; }
    static int handlingBonus(PerkBatchA.Slot slot, long tick) { return active(slot, tick) ? KillingWindProfile.handlingBonus() : 0; }
    static double falloffScalar(PerkBatchA.Slot slot, long tick) { return active(slot, tick) ? KillingWindProfile.falloffScalar() : 1; }
    static double speedMultiplier() { return KillingWindProfile.mobilityBonus() / 100.0 * .4; }
    /** Owned transient movement modifier exactly while the held buff is live; yields to foreign owners. */
    static void movement(ServerPlayer p, PerkBatchA.Slot held) {
        if (!active(held, PerkBatchA.now(p))) { release(p); return; }
        var current = OWNED.get(p.getUUID());
        var speed = p.getAttribute(Attributes.MOVEMENT_SPEED);
        if (current != null && current.owner == p && current.speed == speed && speed != null
            && speed.getModifier(ID) == current.modifier) return;
        release(p);
        if (speed == null || speed.hasModifier(ID)) return;
        var modifier = new AttributeModifier(ID, speedMultiplier(), AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        speed.addTransientModifier(modifier);
        OWNED.put(p.getUUID(), new Owned(p, speed, modifier));
    }
    static void release(ServerPlayer p) {
        var o = OWNED.get(p.getUUID());
        if (o != null && o.owner == p) { o.release(); OWNED.remove(p.getUUID()); }
    }
    static void clear() { for (var o : OWNED.values()) o.release(); OWNED.clear(); }
}
