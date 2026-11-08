package kim.biryeong.destiny.weapon;

/** Immutable read-only projection of authoritative item ammunition; no prediction or refill. */
public record WeaponAmmoState(String family, int rounds, int reserve, int capacity,
                              int reloadRemaining, int reloadDuration, boolean superWeapon, boolean infiniteReserve) {
    public WeaponAmmoState(String family,int rounds,int reserve,int capacity,int remaining,int duration,boolean superWeapon) {
        this(family,rounds,reserve,capacity,remaining,duration,superWeapon,false);
    }
    public WeaponAmmoState {
        if (infiniteReserve && (reserve != 0 || superWeapon)) throw new IllegalArgumentException("Infinite reserve must not fake finite rounds");
        if (family == null || rounds < 0 || reserve < 0 || capacity < 1 || rounds > capacity
                || reloadRemaining < 0 || reloadDuration < 1 || reloadRemaining > reloadDuration)
            throw new IllegalArgumentException("Invalid ammunition snapshot");
    }
    /**
     * HUD projection of a stowed weapon. Perk-loaded cartridges (Overflow, Clown Cartridge, Ambitious Assassin) legitimately
     * hold more than the base magazine, so the reported capacity covers the loaded limit and the rounds actually present;
     * rejecting them threw from the server tick whenever such a weapon was holstered.
     */
    public static WeaponAmmoState stowed(String family, WeaponMagazine ammo, int baseCapacity, int reloadTicks, boolean infiniteReserve) {
        int capacity = Math.max(Math.max(baseCapacity, ammo.loadedLimit()), ammo.rounds());
        return new WeaponAmmoState(family, ammo.rounds(), ammo.reserve(), capacity, 0, reloadTicks, false, infiniteReserve);
    }
    public boolean reloading() { return reloadRemaining > 0; }
    public boolean low() { return rounds <= Math.max(1, (int)Math.ceil(capacity * .2)); }
    public float reloadProgress() { return reloading() ? 1f - reloadRemaining / (float)reloadDuration : 0; }
}
