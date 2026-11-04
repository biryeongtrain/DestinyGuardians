package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.minecraft.server.level.ServerPlayer;
import java.util.List;
import java.util.Optional;
import static kim.biryeong.destiny.hud.CombatHud.*;
import static kim.biryeong.minigamelib.displayhud.DisplayHud.HudAlignment.LEFT;

/** Destiny-inspired selected-weapon panel: silhouette, large magazine, small reserve.
 * Uses bounded, cached glyph quads and actual server state. No invented secondary weapons.
 */
public final class AmmoHud {
    public static final String PREFIX = "destiny:hud_ammo_";
    private AmmoHud() {}

    public static Optional<WeaponAmmoState> current(ServerPlayer player) {
        if (!player.isAlive() || player.isRemoved() || player.isSpectator()) return Optional.empty();
        if (AbilityService.inSuper(player)) {
            var session = Guardians.runtime(player).superSession;
            var shots = session.ammunition();
            return shots.isPresent() ? Optional.of(new WeaponAmmoState("hand_cannon", shots.getAsInt(), 0,
                    session.ammunitionCapacity(), 0, 1, true)) : Optional.empty();
        }
        return WeaponRuntime.ammunition(player);
    }

    public static void update(ServerPlayer player) {
        var value = current(player);
        if (value.isEmpty()) { remove(player); return; }
        var state = value.get();
        int tint = state.rounds() == 0 ? 0xF16B5B : state.superWeapon() ? 0xF4D36A
                : state.low() ? 0xF2BE75 : 0xF1F3F5;
        sprite(player, PREFIX + "panel", "ammo_panel", 424, 948, 280, 56, 1, 0xFFFFFF, LEFT);
        String silhouette = state.superWeapon() ? "ammo_golden_gun_w122"
                : kim.biryeong.destiny.weapon.WeaponSkins.hudIcon(player.getMainHandItem(), WeaponItems.entry(player.getMainHandItem()).orElseThrow());
        sprite(player, PREFIX + "weapon", silhouette, 336, 948, 80, 32, 2,
                state.superWeapon() ? 0xF4D36A : 0xC7CDD4, LEFT);
        number(player, "rounds", state.rounds(), 476, 948, 28, 43, 78, tint);
        if (!state.superWeapon()) {
            if (state.family().equals("sword")) {
                DisplayHud.removeHud(player, PREFIX+"divider");
                DisplayHud.removeHud(player, PREFIX+"infinity");
                clearNumber(player,"reserve");
            } else {
            bar(player, PREFIX + "divider", 492, 948, 1, 32, 2, 0x899199, LEFT);
            if (state.infiniteReserve()) {
                clearNumber(player, "reserve");
                sprite(player, PREFIX+"infinity", "ammo_infinity", 534, 947, 22, 15, 3, 0xD1D6DC, LEFT);
            } else {
                DisplayHud.removeHud(player, PREFIX+"infinity");
                number(player, "reserve", state.reserve(), 550, 947, 13, 21, 48,
                        state.reserve() == 0 ? 0xA0A6AF : 0xD1D6DC);
            }
            }
            var entry=WeaponItems.entry(player.getMainHandItem()).orElseThrow();
            var meta=WeaponCharacteristics.of(entry);
            var damage=WeaponOsmosis.damage(player,player.getMainHandItem(),entry);
            sprite(player, PREFIX+"damage", "ammo_damage_"+damage.name().toLowerCase(java.util.Locale.ROOT),
                    390, 948, 14, 14, 3, damage.color(), LEFT);
            bar(player,PREFIX+"ammo_type",286,948,2,46,2,meta.ammo().color(),LEFT);
        } else {
            DisplayHud.removeHud(player, PREFIX + "divider");
            clearNumber(player, "reserve");
            DisplayHud.removeHud(player, PREFIX+"infinity");
            DisplayHud.removeHud(player, PREFIX+"damage");
            DisplayHud.removeHud(player, PREFIX+"ammo_type");
        }
        updateStowed(player,state.superWeapon());
        updateGlaive(player);
        var sword=WeaponRuntime.swordStatus(player);
        if (sword.isPresent()&&!Guardians.isGuardian(player)) {
            bar(player,PREFIX+"sword_track",286,984,276,3,2,0x515863,LEFT);
            bar(player,PREFIX+"sword_energy",286,984,276*sword.get().energy(),3,3,
                    sword.get().guarding()?0x95ECF8:0xF1F3F5,LEFT);
        } else {
            DisplayHud.removeHud(player,PREFIX+"sword_track");
            DisplayHud.removeHud(player,PREFIX+"sword_energy");
        }
        if (state.reloading()) {
            bar(player, PREFIX + "reload_track", 286, 980, 276, 3, 2, 0x515863, LEFT);
            // Eight discrete steps cap per-tick metadata without pretending rounds arrive early.
            float progress = (float)Math.floor(state.reloadProgress() * 8) / 8;
            bar(player, PREFIX + "reload", 286, 980, 276 * progress, 3, 3, 0xF4D36A, LEFT);
        } else {
            DisplayHud.removeHud(player, PREFIX + "reload_track");
            DisplayHud.removeHud(player, PREFIX + "reload");
        }
    }

    private static void updateGlaive(ServerPlayer player) {
        var value=WeaponRuntime.glaiveStatus(player);
        if(value.isEmpty()) {
            for(String id:List.copyOf(DisplayHud.getHuds(player).keySet()))
                if(id.startsWith(PREFIX+"glaive_"))DisplayHud.removeHud(player,id);
            return;
        }
        var g=value.get();int fill=(int)Math.floor(g.energy()*16);
        sprite(player,PREFIX+"glaive_reticle","glaive_reticle_w41",960,540,58,58,2,0xCBDDE2,
                DisplayHud.HudAlignment.CENTER);
        for(int i=0;i<16;i++) {
            double angle=Math.toRadians(35+i*110.0/15);
            float x=960+(float)Math.cos(angle)*35,y=540+(float)Math.sin(angle)*35;
            sprite(player,PREFIX+"glaive_energy_"+i,"solid",x,y,3,5,3,
                    i<fill?(g.guarding()?0x95ECF8:0xE1EBEE):0x444D58,DisplayHud.HudAlignment.CENTER);
        }
    }

    private static void updateStowed(ServerPlayer p,boolean superWeapon) {
        var others=superWeapon||!WeaponLoadout.enabled(p)?java.util.List.<WeaponLoadout.Equipped>of()
                :WeaponLoadout.equipped(p).stream().filter(e->e.stack()!=p.getMainHandItem()).toList();
        for(int i=0;i<2;i++) {
            String row="stowed_"+i+"_";
            if(i>=others.size()) {
                for(String id:List.copyOf(DisplayHud.getHuds(p).keySet()))
                    if(id.startsWith(PREFIX+row))DisplayHud.removeHud(p,id);
                continue;
            }
            var equipped=others.get(i);var meta=equipped.characteristics();var ammo=equipped.ammunition();
            float y=1005+i*33;
            sprite(p,PREFIX+row+"panel","ammo_stowed_panel",409,y,250,28,1,0xC5CBD1,LEFT);
            // Same 2.5:1 canvas as selected80x32; do not flatten the actual weapon outline.
            sprite(p,PREFIX+row+"weapon",kim.biryeong.destiny.weapon.WeaponSkins.hudIcon(equipped.stack(),equipped.weapon()),329,y,50,20,2,0xA9B0B9,LEFT);
            sprite(p,PREFIX+row+"damage","ammo_damage_"+meta.damage().name().toLowerCase(java.util.Locale.ROOT),
                    385,y,11,11,2,meta.damage().color(),LEFT);
            bar(p,PREFIX+row+"type",400,y,5,9,2,meta.ammo().color(),LEFT);
            if(ammo.infiniteReserve()) {
                clearNumber(p,row+"total");
                sprite(p,PREFIX+row+"infinity","ammo_infinity",513,y,17,12,2,0xC7CDD4,LEFT);
            } else {
                DisplayHud.removeHud(p,PREFIX+row+"infinity");
                number(p,row+"total",ammo.rounds()+ammo.reserve(),522,y,12,20,95,
                        ammo.rounds()+ammo.reserve()==0?0xC16D67:0xC7CDD4);
            }
        }
    }

    private static void number(ServerPlayer p, String id, int count, float right, float y,
                               float width, float height, float available, int color) {
        String text = Integer.toString(count);
        float advance = Math.min(width, available / text.length());
        for (int i = 0; i < 10; i++) {
            String key = PREFIX + id + "_" + i;
            if (i >= text.length()) DisplayHud.removeHud(p, key);
            else sprite(p, key, "ammo_digit_" + text.charAt(i), right - (text.length() - i - .5f) * advance,
                    y, advance, height, 3, color, LEFT);
        }
    }
    private static void clearNumber(ServerPlayer p, String id) {
        for (int i = 0; i < 10; i++) DisplayHud.removeHud(p, PREFIX + id + "_" + i);
    }
    public static void remove(ServerPlayer p) {
        for (String id : List.copyOf(DisplayHud.getHuds(p).keySet()))
            if (id.startsWith(PREFIX)) DisplayHud.removeHud(p, id);
    }
}
