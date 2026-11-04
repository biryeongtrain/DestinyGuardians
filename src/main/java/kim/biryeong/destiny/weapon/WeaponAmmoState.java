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
    public boolean reloading() { return reloadRemaining > 0; }
    public boolean low() { return rounds <= Math.max(1, (int)Math.ceil(capacity * .2)); }
    public float reloadProgress() { return reloading() ? 1f - reloadRemaining / (float)reloadDuration : 0; }
}
