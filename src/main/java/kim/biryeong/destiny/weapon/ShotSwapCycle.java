package kim.biryeong.destiny.weapon;

/** Shot Swap: kills bank stacks (no timer). Ready uses a positive bank, a real stow consumes one. */
public final class ShotSwapCycle {
    private int stacks;
    public void killed(int perKill, int max) { stacks = Math.min(max, stacks + perKill); }
    public int stacks() { return stacks; }
    /** @return true if a stack was consumed by this stow transaction. */
    public boolean stowed() {
        if (stacks <= 0) return false;
        stacks--;
        return true;
    }
}
