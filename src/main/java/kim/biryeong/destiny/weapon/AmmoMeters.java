package kim.biryeong.destiny.weapon;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/** Immutable player-owned progress, including owed bricks. No timers, random drops or HUD mutations. */
public record AmmoMeters(int special, int heavy) {
    public static final int FULL=100_000, MAX=FULL*32;
    public static final AmmoMeters EMPTY=new AmmoMeters(0,0);
    public static final Codec<AmmoMeters> CODEC=RecordCodecBuilder.create(i->i.group(
            Codec.INT.optionalFieldOf("special",0).forGetter(AmmoMeters::special),
            Codec.INT.optionalFieldOf("heavy",0).forGetter(AmmoMeters::heavy)).apply(i,AmmoMeters::new));
    public AmmoMeters { special=Math.clamp(special,0,MAX);heavy=Math.clamp(heavy,0,MAX); }
    public int points(WeaponAmmoType type) {return switch(type){case SPECIAL->special;case HEAVY->heavy;default->0;};}
    public float fraction(WeaponAmmoType type) {return Math.min(1,points(type)/(float)FULL);}
    public boolean owed(WeaponAmmoType type){return points(type)>=FULL;}
    public AmmoMeters add(int s,int h) {return new AmmoMeters((int)Math.min(MAX,(long)special+Math.max(0,s)),
            (int)Math.min(MAX,(long)heavy+Math.max(0,h)));}
    public AmmoMeters spend(WeaponAmmoType type) {
        if(!owed(type))return this;
        return new AmmoMeters(special-(type==WeaponAmmoType.SPECIAL?FULL:0),heavy-(type==WeaponAmmoType.HEAVY?FULL:0));
    }
}
