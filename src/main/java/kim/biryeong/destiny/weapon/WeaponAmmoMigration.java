package kim.biryeong.destiny.weapon;

/**
 * Pure W47 allocation of saved ammo after capacity changes. Finite total is
 * rounds + reserve + overflow; excess loaded ammo fills reserve space first,
 * then explicit overflow. No read of this projection writes or grants ammo.
 *
 * Valid legacy nonnegative int pairs are lossless, including two MAX_VALUEs.
 * Negative counts are corrupt and treated as zero. The entire representable
 * total is capped at Long.MAX_VALUE using saturating addition: corrupt/future
 * long inputs beyond that ceiling deliberately lose only the unrepresentable
 * excess, never wrap negative. No extra BigInteger/array debt can bypass it.
 * Primary ignores obsolete finite-reserve/sentinel values, always reserve=0;
 * only its actual loaded excess and already explicit overflow are retained.
 */
public final class WeaponAmmoMigration {
    public static final long MAX_TOTAL = Long.MAX_VALUE;
    private WeaponAmmoMigration() {}

    public record Allocation(int rounds, int reserve, long overflow) {
        public Allocation {
            if (rounds < 0 || reserve < 0 || overflow < 0
                    || overflow > MAX_TOTAL - rounds - reserve)
                throw new IllegalArgumentException("Invalid ammunition allocation");
        }
        public long total() { return (long) rounds + reserve + overflow; }
    }

    public static Allocation normalize(int capacity, int reserveCapacity, boolean infinite,
                                       long rounds, long reserve, long overflow) {
        if (capacity < 1 || reserveCapacity < 0)
            throw new IllegalArgumentException("Invalid ammunition capacities");
        rounds = Math.max(0, rounds);
        reserve = infinite ? 0 : Math.max(0, reserve);
        overflow = Math.max(0, overflow);
        long total = add(add(rounds, reserve), overflow);
        int loaded = (int) Math.min(rounds, capacity);
        long remaining = total - loaded;
        int stored = infinite ? 0 : (int) Math.min(remaining, reserveCapacity);
        return new Allocation(loaded, stored, remaining - stored);
    }

    private static long add(long a, long b) {
        return b > MAX_TOTAL - a ? MAX_TOTAL : a + b;
    }
}
