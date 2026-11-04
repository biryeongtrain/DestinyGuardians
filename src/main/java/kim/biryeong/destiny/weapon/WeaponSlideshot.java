package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;

/** Slideshot (W320): a detected slide refills 15% of the held magazine and grants +20 Range /
 * +20 Stability for 2.5s or until the first paid emission; 0.3s cooldown; stow removes it. */
final class WeaponSlideshot {
    private WeaponSlideshot() {}
    static void slide(ServerPlayer p, PerkBatchA.Slot slot, long tick) {
        if (!slot.has(SlideshotProfile.ID)) return;
        if (slot.slideshot.slide(tick, SlideshotProfile.durationTicks(), SlideshotProfile.cooldownTicks()))
            WeaponSlideways.refill(p, slot, SlideshotProfile.refillFraction());
    }
    static void shot(PerkBatchA.Slot slot) { if (slot.has(SlideshotProfile.ID)) slot.slideshot.shot(); }
    static int rangeBonus(PerkBatchA.Slot slot, long tick) {
        return slot.has(SlideshotProfile.ID) && slot.slideshot.active(tick) ? SlideshotProfile.rangeBonus() : 0;
    }
    static int stabilityBonus(PerkBatchA.Slot slot, long tick) {
        return slot.has(SlideshotProfile.ID) && slot.slideshot.active(tick) ? SlideshotProfile.stabilityBonus() : 0;
    }
}
