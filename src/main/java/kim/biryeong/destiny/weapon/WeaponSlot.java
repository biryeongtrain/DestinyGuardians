package kim.biryeong.destiny.weapon;

/** Equipment bucket, NOT ammunition class. Both first slots can hold Primary or Special. */
public enum WeaponSlot {
    KINETIC(0), ENERGY(1), POWER(2);
    private final int hotbar;
    WeaponSlot(int hotbar) { this.hotbar=hotbar; }
    public int hotbar() { return hotbar; }
}
