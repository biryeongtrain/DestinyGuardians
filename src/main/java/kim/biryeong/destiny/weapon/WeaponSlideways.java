package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.hud.AmmoHud;
import net.minecraft.server.level.ServerPlayer;

/** Slideways (W320): a detected slide refills 15% of the held magazine from reserve and grants
 * +15 Stability / +30 Handling for 3s behind a 0.5s cooldown; stowing removes the buff. */
final class WeaponSlideways {
    private WeaponSlideways() {}
    static void slide(ServerPlayer p, PerkBatchA.Slot slot, long tick) {
        if (!slot.has(SlidewaysProfile.ID)) return;
        if (slot.slideways.slide(tick, SlidewaysProfile.durationTicks(), SlidewaysProfile.cooldownTicks()))
            refill(p, slot, SlidewaysProfile.refillFraction());
    }
    static int refill(ServerPlayer p, PerkBatchA.Slot slot, double fraction) {
        var profile = WeaponProfile.forEntry(slot.entry);
        var ammo = WeaponItems.magazine(slot.stack, profile);
        int moved = ammo.reloadRounds(SlideBuffCycle.refillRounds(profile.magazine(), fraction));
        if (moved > 0) {
            WeaponItems.save(slot.stack, ammo);
            p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); AmmoHud.update(p);
        }
        return moved;
    }
    static int stabilityBonus(PerkBatchA.Slot slot, long tick) {
        return slot.has(SlidewaysProfile.ID) && slot.slideways.active(tick) ? SlidewaysProfile.stabilityBonus() : 0;
    }
    static int handlingBonus(PerkBatchA.Slot slot, long tick) {
        return slot.has(SlidewaysProfile.ID) && slot.slideways.active(tick) ? SlidewaysProfile.handlingBonus() : 0;
    }
}
