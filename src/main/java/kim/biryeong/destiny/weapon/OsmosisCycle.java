package kim.biryeong.destiny.weapon;

/** Tick-free stow episode. Acceptance alone does nothing; only successful ability use applies.
 * Full/no-reserve use still spends the episode's sole refill. Subsequent uses may change element.
 * No timer, manual-reload proc, generated ammo, damage scalar or query-side mutation. */
public final class OsmosisCycle {
    private Object epoch = new Object();
    private WeaponCharacteristics.Damage element;
    private boolean refillSpent;

    public static final class Token {
        private final OsmosisCycle owner;
        private final Object epoch;
        private final WeaponCharacteristics.Damage element;
        private boolean consumed;
        private Token(OsmosisCycle owner, WeaponCharacteristics.Damage element) {
            this.owner = owner; this.epoch = owner.epoch; this.element = element;
        }
    }
    public Token accepted(WeaponCharacteristics.Damage grenadeElement) {
        if (grenadeElement == null || grenadeElement == WeaponCharacteristics.Damage.KINETIC) return null;
        return new Token(this, grenadeElement);
    }
    /** Caller validated the original held source and a successful, paid grenade activate. */
    public int abilityUsed(Token token, WeaponMagazine magazine, int capacity) {
        if (token == null || token.consumed || token.owner != this || token.epoch != epoch) return 0;
        token.consumed = true;
        if (magazine == null || capacity <= 0) return 0;
        element = token.element;
        if (refillSpent) return 0;
        refillSpent = true;
        return magazine.reloadRounds(OsmosisProfile.refillRounds(capacity));
    }
    public boolean active() { return element != null; }
    public WeaponCharacteristics.Damage damage(WeaponCharacteristics.Damage canonical) {
        return element == null ? canonical : element;
    }
    /** Stow/edit/replacement revokes both pending accepted tokens and the active conversion. */
    public void clear() { epoch = new Object(); element = null; refillSpent = false; }
}
