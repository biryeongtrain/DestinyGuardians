package kim.biryeong.destiny.weapon;

/** Immutable damage attribution captured at emission, not whatever happens to be held at impact.
 * Gain curves are explicitly Minecraft tuning; official item stat values are not decoded gain curves.
 */
public record AmmoGeneration(Kind kind,int stat) {
    public enum Kind { PRIMARY, SPECIAL, HEAVY, ABILITY, SUPER, GLAIVE_MELEE }
    public static final AmmoGeneration ABILITY=new AmmoGeneration(Kind.ABILITY,0);
    public static final AmmoGeneration GLAIVE_MELEE=new AmmoGeneration(Kind.GLAIVE_MELEE,0);
    public static final AmmoGeneration SUPER=new AmmoGeneration(Kind.SUPER,0);
    public AmmoGeneration {java.util.Objects.requireNonNull(kind);stat=Math.clamp(stat,0,100);}
    public static AmmoGeneration weapon(WeaponCatalog.Entry e) {
        var m=WeaponCharacteristics.of(e);
        return new AmmoGeneration(Kind.valueOf(m.ammo().name()),e.family().equals("sword")?0:
                m.stats().getOrDefault("1931675084",0));
    }
    public AmmoMeters gains(boolean assist) {
        int s,h;
        switch(kind) {
            case PRIMARY -> {s=4000+60*stat;h=1600+24*stat;}
            case SPECIAL -> {s=1500+25*stat;h=2000+30*stat;}
            case HEAVY -> {s=3000+30*stat;h=700+10*stat;}
            case SUPER -> {s=1500;h=750;}
            default -> {s=2000;h=1000;}
        }
        return new AmmoMeters(assist?s/2:s,assist?h/2:h);
    }
    /** Base brick payout. Curated Minecraft defaults, not all current Destiny archetype curves. */
    public static int perBrick(WeaponCatalog.Entry e) {
        return switch(e.family()) {
            case "sniper_rifle","fusion_rifle","shotgun","grenade_launcher"->e.frame().equals("rapid_fire")?4:3;
            case "glaive"->4;
            case "trace_rifle"->40;
            case "linear_fusion_rifle"->e.frame().equals("precision")?5:3;
            case "rocket_launcher"->1;
            case "heavy_grenade_launcher"->3;
            case "machine_gun"->25;
            case "sword"->8;
            default->0;
        };
    }
    /** Double-Special divides a per-weapon grant; the minimum is one round, never a full grant twice. */
    public static int split(int full,int equippedCount) {
        if(full<=0||equippedCount<=0)return 0;
        return Math.max(1,full/equippedCount);
    }
}
