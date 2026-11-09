package kim.biryeong.destiny.weapon;

import java.util.ArrayDeque;

/** DDC base rows 115,116,143,165. Uncertain windows are explicit local policies:
 * Heal Clip 5.3? s ->106 ticks; Headstone ? burst interval ->100 ticks, five successful spawns.
 * Tick boundaries are exclusive; no wall clock and no query-side activation. */
public final class PerkExpansionSupportCycle {
    private long healUntil = Long.MIN_VALUE, looseUntil = Long.MIN_VALUE, headstoneUntil;
    private final ArrayDeque<Long> crystals = new ArrayDeque<>();
    private final OsmosisCycle conversion = new OsmosisCycle();
    public void killed(long now) { healUntil = now + 106; }
    public boolean reload(long now) {
        boolean active = now >= 0 && now < healUntil;
        healUntil = Long.MIN_VALUE;
        return active;
    }
    public void debuffed(long now) { looseUntil = now + 180; }
    public int healRemaining(long now) { return remaining(healUntil, now); }
    public int looseRemaining(long now) { return remaining(looseUntil, now); }
    public boolean converted() { return conversion.active(); }
    private static int remaining(long until, long now) {
        return now < 0 || until <= now ? 0 : (int)Math.min(Integer.MAX_VALUE, until-now);
    }
    public boolean loose(long now) { return now >= 0 && now < looseUntil; }
    public boolean canCrystal(long now) { return now >= headstoneUntil; }
    public void crystalSpawned(long now) {
        while (!crystals.isEmpty() && now - crystals.peekFirst() >= 100) crystals.removeFirst();
        crystals.addLast(now);
        if (crystals.size() >= 5) { headstoneUntil = now + 100; crystals.clear(); }
    }
    public OsmosisCycle.Token accepted(WeaponCharacteristics.Damage element) { return conversion.accepted(element); }
    public int classUsed(OsmosisCycle.Token token, WeaponMagazine ammo, int capacity) {
        return conversion.abilityUsed(token, ammo, capacity);
    }
    public WeaponCharacteristics.Damage damage(WeaponCharacteristics.Damage base) { return conversion.damage(base); }
    public void stow() { conversion.clear(); }
}
