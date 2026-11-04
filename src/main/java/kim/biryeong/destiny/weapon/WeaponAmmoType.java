package kim.biryeong.destiny.weapon;

public enum WeaponAmmoType {
    PRIMARY(0xF1F3F5), SPECIAL(0x7FE39C), HEAVY(0xB58CF0);
    private final int color;
    WeaponAmmoType(int color) { this.color=color; }
    public int color() { return color; }
}
