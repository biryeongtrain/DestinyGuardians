package kim.biryeong.destiny.sound;

import kim.biryeong.destiny.weapon.SwordProfile;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/** Named archive actions. Source match is documented in W56, not inferred from weapon appearance.
 * Timing is authored at real server contact/release; no sample-accurate Destiny sync claim. */
public final class SwordSounds {
    public static final String CASTER_RELEASE="weapon.sword.caster.release";
    public static final String CASTER_IMPACT="weapon.sword.caster.impact";
    private SwordSounds() { }

    public static String attackKey(WeaponCatalog.Entry entry,boolean heavy,boolean empty,boolean grounded) {
        var shape=SwordProfile.of(entry).shape(); // Reject non-swords, including accidental gun callers.
        if(!heavy) {
            String exact="weapon."+entry.id()+"."+(empty?"empty_light":"light");
            if(DestinySounds.has(exact))return exact;
            if(empty)return DestinySounds.weaponKey(entry,"fire"); // Never label charged samples as empty variants.
            return mapped("weapon.sword.light",entry);
        }
        if(shape==SwordProfile.Shape.CASTER)return mapped(CASTER_RELEASE,entry);
        String exact="weapon."+entry.id()+".heavy";
        if(!grounded&&DestinySounds.has(exact+"_air"))return exact+"_air";
        if(DestinySounds.has(exact))return exact;
        // Half Truths is an adaptive-frame proxy for Abide, never a lightweight dash recording.
        return shape==SwordProfile.Shape.UPPERCUT?mapped("weapon.sword.uppercut",entry):DestinySounds.weaponKey(entry,"fire");
    }

    private static String mapped(String key,WeaponCatalog.Entry entry) {
        return DestinySounds.has(key)?key:DestinySounds.weaponKey(entry,"fire");
    }

    public static String guardKey(WeaponCatalog.Entry entry) {
        SwordProfile.of(entry);
        String exact="weapon."+entry.id()+".guard";
        return DestinySounds.has(exact)?exact:"weapon.sword.guard";
    }

    public static void contact(ServerPlayer owner,WeaponCatalog.Entry entry,boolean heavy,boolean empty,boolean grounded) {
        DestinySounds.at(owner.level(),owner.getEyePosition(),attackKey(entry,heavy,empty,grounded),.8f);
    }

    public static void guard(ServerPlayer owner,WeaponCatalog.Entry entry) {
        DestinySounds.at(owner.level(),owner.getEyePosition(),guardKey(entry),.65f);
    }

    public static void casterImpact(ServerLevel level,Vec3 point) {
        DestinySounds.at(level,point,CASTER_IMPACT,.8f);
    }
}
