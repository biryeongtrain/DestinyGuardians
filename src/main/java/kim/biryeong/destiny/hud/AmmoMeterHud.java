package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.minecraft.server.level.ServerPlayer;
import java.util.List;
import static kim.biryeong.destiny.hud.CombatHud.*;
import static kim.biryeong.minigamelib.displayhud.DisplayHud.HudAlignment.LEFT;

/** Two bounded personal ammo-generation meters. Reading progress never earns or spends it. */
public final class AmmoMeterHud {
    public static final String PREFIX="destiny:hud_meter_";
    private AmmoMeterHud() {}
    public static void update(ServerPlayer p) {
        if(!p.isAlive()||p.isRemoved()||p.isSpectator()||!WeaponLoadout.enabled(p)||AbilityService.inSuper(p)) {remove(p);return;}
        var progress=AmmoEconomy.meters(p);
        int row=0;
        for(var type:List.of(WeaponAmmoType.SPECIAL,WeaponAmmoType.HEAVY)) {
            String id=PREFIX+type.name().toLowerCase(java.util.Locale.ROOT);
            if(!AmmoEconomy.hasType(p,type)){removeType(p,id);row++;continue;}
            float x=82+row++*96;
            sprite(p,id+"_icon","ammo_meter_w42",x-10,1008,11,14,2,type.color(),LEFT);
            bar(p,id+"_track",x,1008,72,4,1,0x414954,LEFT);
            float fraction=(float)Math.floor(progress.fraction(type)*16)/16;
            bar(p,id+"_fill",x,1008,72*fraction,3,2,progress.owed(type)?0xEDF3F5:type.color(),LEFT);
        }
    }
    private static void removeType(ServerPlayer p,String id) {for(String s:List.of("_icon","_track","_fill"))DisplayHud.removeHud(p,id+s);}
    public static void remove(ServerPlayer p) {
        for(var id:List.copyOf(DisplayHud.getHuds(p).keySet()))if(id.startsWith(PREFIX))DisplayHud.removeHud(p,id);
    }
}
