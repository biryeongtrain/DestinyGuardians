package kim.biryeong.destiny.weapon;

/** Item-owned ammunition; Primary has infinite reserves, never an infinite magazine; Special/Heavy remain finite. */
public final class WeaponMagazine {
    private final int capacity;
    private final boolean infinite;
    private final int reserveCapacity;
    private int loadedLimit;
    private int rounds;
    private int reserve;
    private long overflow;

    public WeaponMagazine(WeaponProfile profile, int rounds, int reserve) {
        this(profile, rounds, reserve, 0);
    }
    /** Saved nonnegative excess is conserved, not clipped away when W46 capacities shrink. */
    public WeaponMagazine(WeaponProfile profile, long rounds, long reserve, long overflow) {
        this(profile, rounds, reserve, overflow, profile.magazine());
    }
    /** Explicit persisted authorization for already-funded perk-loaded cartridges. */
    public WeaponMagazine(WeaponProfile profile, long rounds, long reserve, long overflow, int loadedLimit) {
        capacity = profile.magazine();
        this.loadedLimit = Math.max(capacity, loadedLimit);
        infinite = profile.infiniteReserve();
        reserveCapacity=profile.reserve();
        var allocation = WeaponAmmoMigration.normalize(this.loadedLimit, reserveCapacity, infinite, rounds, reserve, overflow);
        this.rounds = allocation.rounds();
        this.reserve = allocation.reserve();
        this.overflow = allocation.overflow();
    }
    public int loadedLimit() { return loadedLimit; }
    public int rounds() { return rounds; }
    public int reserve() { return reserve; }
    /** Conserved legacy ammo outside bounded HUD/reserve counts; not a free pickup grant. */
    public long overflow() { return overflow; }
    public long total() { return (long) rounds + reserve + overflow; }
    /** Ammo pickups go to reserves only. A full reserve cannot consume a brick or reload the magazine. */
    public int addReserve(int amount) {
        if(infinite||amount<=0)return 0;
        int accepted=(int)Math.min(Math.min((long)reserveCapacity-reserve,(long)amount),
                WeaponAmmoMigration.MAX_TOTAL-total());
        reserve+=accepted;
        return accepted;
    }
    public boolean consume() { if (rounds == 0) return false; rounds--; return true; }
    /** Explicit precision-trait reward, never a reload or a reserve/legacy-overflow transfer. */
    public int generateLoaded(int amount) {
        if (amount <= 0) return 0;
        int accepted = (int)Math.min(Math.min(Math.max(0L, (long)capacity - rounds), amount), WeaponAmmoMigration.MAX_TOTAL - total());
        rounds += accepted;
        return accepted;
    }
    /** Explicit generated intrinsic reward (Thorn Remnants), capped independently of reserve funding. */
    public int generateLoadedOverflow(int amount, int ceiling) {
        if (amount <= 0 || ceiling < capacity || ceiling > 1000) return 0;
        int accepted=(int)Math.min(Math.min(Math.max(0L,(long)ceiling-rounds),amount),WeaponAmmoMigration.MAX_TOTAL-total());
        rounds+=accepted;
        if(accepted>0)loadedLimit=Math.max(loadedLimit,rounds);
        return accepted;
    }
    /** Atomic paid multi-ammo attack; a denied action cannot partially spend ammunition. */
    public boolean consume(int amount) {
        if (amount <= 0 || amount > rounds) return false;
        rounds -= amount; return true;
    }
    /** Single-pool sword pickup. Never use this to silently reload an ordinary ranged magazine. */
    public int addLoaded(int amount) {
        if (infinite || reserveCapacity != 0 || amount <= 0 || overflow > 0 || reserve > 0) return 0;
        int accepted = (int)Math.min(Math.min(Math.max(0L, (long)capacity-rounds),amount),WeaponAmmoMigration.MAX_TOTAL-total());
        rounds += accepted; return accepted;
    }
    public boolean canReload() { return rounds < capacity && (infinite || reserve > 0 || overflow > 0); }
    /** W84 finite four-round intrinsic transaction: n real cartridges fund one shot.
     * Loaded cartridges first, then reserves/legacy overflow; never a generated reward.
     * Caller captures n at reload start. A pickup cannot upgrade an accepted x2 into x4.
     * Debit order/top-up are explicit local policy, not a sourced Destiny algorithm. */
    public boolean compressRounds(int count) {
        if (infinite || capacity != 4 || count < 2 || count > 4 || rounds > count || total() < count)
            return false;
        spendReserve(count - rounds);
        rounds = 1;
        return true;
    }
    /** Shotgun insert transfers exactly one shell; cancellation cannot move a later shell. */
    public int reloadOne() {
        return reloadRounds(1);
    }
    public int reload() {
        return reloadRounds(capacity);
    }
    /** One insert may carry two cartridges. Never exceeds remaining space or available finite ammo. */
    public int reloadRounds(int limit) {
        if (limit <= 0 || !canReload()) return 0;
        int space = Math.min(limit, capacity - rounds);
        int transfer = infinite ? space : (int)Math.min(space, (long)reserve + overflow);
        rounds += transfer;
        spendReserve(transfer);
        return transfer;
    }
    /** Reserve-funded perk top-up. Regular reloads/refunds still stop at base capacity.
     * Existing funded rounds never shrink when a later target is lower. */
    public int reloadOverflow(int target) {
        if (target <= rounds || target <= capacity) return 0;
        int room = target - rounds;
        int transfer = infinite ? room : (int)Math.min(room, (long)reserve + overflow);
        if (transfer <= 0) return 0;
        rounds += transfer;
        loadedLimit = Math.max(loadedLimit, rounds);
        spendReserve(transfer);
        return transfer;
    }
    private void spendReserve(int amount) {
        if (infinite) {
            // A real reload retires saved loaded excess before using infinite supply.
            overflow -= Math.min(overflow, amount);
            return;
        }
        int fromReserve = Math.min(reserve, amount);
        reserve -= fromReserve;
        overflow -= amount - fromReserve;
        // Keep the bounded reserve usable while debt exists; no automatic magazine refill.
        int promoted = (int)Math.min((long)reserveCapacity - reserve, overflow);
        reserve += promoted;
        overflow -= promoted;
    }
}
