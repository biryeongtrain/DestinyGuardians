package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.server.level.ServerPlayer;

/** Local selected trait decision; never writes the player's accessibility preference. */
public final class WeaponFullAuto {
    private WeaponFullAuto(){}
    private static WeaponCatalog.Entry held(ServerPlayer p){
        if(p==null||!p.isAlive()||p.isRemoved()||p.isSpectator()||p.hasDisconnected()
                ||!WeaponLoadout.canUse(p)||Guardians.runtimeIfPresent(p).map(r->r.superSession!=null).orElse(false))return null;
        var stack=p.getMainHandItem();
        if(stack.getCount()!=1)return null;
        var e=WeaponItems.entry(stack).orElse(null);
        var roll=WeaponPerks.selected(stack,FullAutoProfile.ID).orElse(null);
        return FullAutoProfile.supports(e)&&roll!=null&&FullAutoProfile.rolls().contains(roll)?e:null;
    }
    public static boolean selected(ServerPlayer p){return held(p)!=null;}
    public static int stabilityBonus(ServerPlayer p){return FullAutoProfile.stabilityBonus(held(p));}
    public static WeaponProfile firingProfile(ServerPlayer p,WeaponCatalog.Entry e,WeaponProfile base){
        return e!=null&&e.equals(held(p))?FullAutoProfile.firingProfile(e,base):base;
    }
}
