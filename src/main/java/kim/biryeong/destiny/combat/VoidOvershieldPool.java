package kim.biryeong.destiny.combat;

/** Pure conservative ownership accounting for the vanilla shared absorption scalar. */
public final class VoidOvershieldPool {
    private float owned, observed;
    public VoidOvershieldPool(float existing) { observed = Math.max(0, existing); }
    public void observe(float current) {
        current = Math.max(0, current);
        owned = ownedAt(current);
        observed = current;
    }
    public void granted(float before, float after) {
        observe(before); owned += Math.max(0, after-before); observed = Math.max(0, after);
    }
    /** Pure estimate accounts for damage since last lifecycle tick without adopting foreign gains. */
    public float ownedAt(float current) {
        return Math.min(Math.max(0,current), Math.max(0, owned - Math.max(0, observed-current)));
    }
    public float owned() { return owned; }
    public float withoutOwned(float current) { observe(current); return Math.max(0, current-owned); }
    public static float resisted(float amount, float owned) {
        if (!Float.isFinite(amount) || amount <= 0 || !Float.isFinite(owned) || owned <= 0) return amount;
        float protectedIncoming = Math.min(amount, owned / .3f);
        return amount - protectedIncoming * .7f;
    }
}
