package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * 전투 HUD (docs/design/08 3장): 왼쪽 아래 능력 쿨타임, 아래 가운데 궁극기 게이지.
 * 표시 문자열이 바뀔 때만 갱신한다.
 */
public final class CombatHud {
    public static final String ABILITIES_ID = "destiny:hud_abilities";
    public static final String SUPER_ID = "destiny:hud_super";
    private static final Map<UUID, String> LAST = new HashMap<>();

    public static float abilitiesX = 80f;
    public static float abilitiesY = 955f;
    public static float superX = 960f;
    public static float superY = 860f;

    private CombatHud() {
    }

    public static void update(ServerPlayer player) {
        if (!Guardians.isGuardian(player)) {
            remove(player);
            return;
        }
        Component abilities = abilitiesLine(player);
        Component superLine = superLine(player);
        String key = abilities.getString() + "|" + superLine.getString();
        if (key.equals(LAST.get(player.getUUID())) && DisplayHud.getHud(player, ABILITIES_ID) != null) {
            return;
        }
        LAST.put(player.getUUID(), key);
        text(player, ABILITIES_ID, abilities, abilitiesX, abilitiesY, Display.TextDisplay.Align.LEFT, DisplayHud.HudAlignment.LEFT);
        text(player, SUPER_ID, superLine, superX, superY, Display.TextDisplay.Align.CENTER, DisplayHud.HudAlignment.CENTER);
    }

    public static void remove(ServerPlayer player) {
        LAST.remove(player.getUUID());
        DisplayHud.removeHud(player, ABILITIES_ID);
        DisplayHud.removeHud(player, SUPER_ID);
    }

    /** 현재 HUD 문자열 (테스트·디버그용). */
    public static String lastText(ServerPlayer player) {
        return LAST.get(player.getUUID());
    }

    static Component abilitiesLine(ServerPlayer player) {
        GuardianData data = Guardians.data(player);
        MutableComponent line = Component.empty();
        slot(line, player, data, AbilitySlot.GRENADE, "수류탄");
        line.append("   ");
        slot(line, player, data, AbilitySlot.MELEE, "근접");
        line.append("   ");
        slot(line, player, data, AbilitySlot.CLASS_ABILITY, "직업");
        return line;
    }

    private static void slot(MutableComponent line, ServerPlayer player, GuardianData data, AbilitySlot slot, String label) {
        Ability ability = AbilityService.equipped(player, slot).orElse(null);
        int color = ability == null ? 0x8A94A3 : ability.element().color();
        int cd = data.cooldown(slot);
        String state = cd > 0 ? (cd + 19) / 20 + "s" : "●";
        line.append(Component.literal(label + " ").withStyle(Style.EMPTY.withColor(TextColor.fromRgb(0xE6EAF0))));
        line.append(Component.literal(state).withStyle(Style.EMPTY.withColor(TextColor.fromRgb(cd > 0 ? 0x8A94A3 : color))));
    }

    static Component superLine(ServerPlayer player) {
        GuardianData data = Guardians.data(player);
        GuardianRuntime runtime = Guardians.runtime(player);
        Element element = AbilityService.equipped(player, AbilitySlot.SUPER).map(Ability::element).orElse(Element.KINETIC);
        float value = runtime.superSession != null ? runtime.superSession.remaining() : data.superEnergy();
        int filled = Math.round(value * 20);
        MutableComponent line = Component.literal(runtime.superSession != null ? "궁극기 발동 중 " : data.superEnergy() >= 1f ? "궁극기 준비 " : "궁극기 ")
                .withStyle(Style.EMPTY.withColor(TextColor.fromRgb(data.superEnergy() >= 1f || runtime.superSession != null ? 0xF2C14E : 0xE6EAF0)));
        line.append(Component.literal("|".repeat(filled)).withStyle(Style.EMPTY.withColor(TextColor.fromRgb(element.color()))));
        line.append(Component.literal("|".repeat(20 - filled)).withStyle(Style.EMPTY.withColor(TextColor.fromRgb(0x3A4250))));
        line.append(Component.literal(" " + Math.round(value * 100) + "%").withStyle(Style.EMPTY.withColor(TextColor.fromRgb(0xE6EAF0))));
        return line;
    }

    private static void text(ServerPlayer player, String id, Component content, float x, float y,
                             Display.TextDisplay.Align align, DisplayHud.HudAlignment hudAlign) {
        DisplayHud existing = DisplayHud.getHud(player, id);
        if (existing instanceof TextDisplayHud hud) {
            hud.setText(content);
            return;
        }
        TextDisplayHud hud = new TextDisplayHud();
        hud.setLineWidth(300);
        hud.setTextAlignment(align);
        hud.setShadowToggle(true);
        hud.setBackgroundColor(0);
        hud.setText(content);
        hud.setScale(220, 220, 1);
        hud.setViewRange(1000);
        hud.setAlignment(hudAlign);
        hud.setLocation(x, y, 0);
        hud.spawn(player, id);
    }
}
