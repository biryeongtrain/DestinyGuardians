package kim.biryeong.destiny.inventory.gear;

import kim.biryeong.destiny.weapon.WeaponSlot;

/** The ten equipment buckets of the Destiny character screen, in screen order (left column, then right). */
public enum GearSlot {
    SUBCLASS("하위직업", null), KINETIC("기본 무기", WeaponSlot.KINETIC), ENERGY("에너지 무기", WeaponSlot.ENERGY),
    POWER("파워 무기", WeaponSlot.POWER), GHOST("고스트 의체", null),
    HELMET("헬멧", null), GAUNTLETS("건틀릿", null), CHEST("가슴 방어구", null), LEGS("다리 방어구", null),
    CLASS_ITEM("직업 아이템", null);

    private final String label;
    private final WeaponSlot weapon;
    GearSlot(String label, WeaponSlot weapon) { this.label = label; this.weapon = weapon; }
    public String label() { return label; }
    /** Weapon bucket, or null for subclass/ghost/armor. */
    public WeaponSlot weapon() { return weapon; }
    public boolean left() { return ordinal() < 5; }
    public boolean armor() { return ordinal() >= 5; }
    public static GearSlot of(WeaponSlot slot) {
        return switch (slot) { case KINETIC -> KINETIC; case ENERGY -> ENERGY; case POWER -> POWER; };
    }
}
