package kim.biryeong.destiny.weapon;

/** Shot Swap (W320): final blows bank 2 stacks (max 6); with a stack, ready/stow get +100 Handling and
 * x0.7 duration; each real stow consumes one stack. */
final class WeaponShotSwap {
    private WeaponShotSwap() {}
    static void killed(PerkBatchA.Slot slot) {
        if (slot.has(ShotSwapProfile.ID)) slot.swap.killed(ShotSwapProfile.stacksPerKill(), ShotSwapProfile.maxStacks());
    }
    private static boolean charged(PerkBatchA.Slot slot) { return slot.has(ShotSwapProfile.ID) && slot.swap.stacks() > 0; }
    static int handlingBonus(PerkBatchA.Slot slot) { return charged(slot) ? ShotSwapProfile.handlingBonus() : 0; }
    static double durationScalar(PerkBatchA.Slot slot) { return charged(slot) ? ShotSwapProfile.durationScalar() : 1; }
}
