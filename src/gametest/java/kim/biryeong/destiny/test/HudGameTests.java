package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.ClientControls;
import kim.biryeong.gcbserver.player.GCBPlayer;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;

public final class HudGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Map<String, String> VANILLA_KEYS = Map.of(
            "destiny:hud_abilities_key", "F",
            "destiny:hud_abilities_1_key", "Shift+",
            "destiny:hud_abilities_1_key_2", "좌클릭",
            "destiny:hud_abilities_2_key", "Shift+",
            "destiny:hud_abilities_2_key_2", "Shift",
            "destiny:hud_super_key", "Shift+F");

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static TextDisplayHud key(GameTestHelper h, ServerPlayer p, String id, String text) {
        var hud = DisplayHud.getHud(p, id);
        check(h, hud instanceof TextDisplayHud, "Key row is a TextDisplayHud: " + id);
        var label = (TextDisplayHud) hud;
        check(h, text.equals(label.getText()), "Key row has expected text " + text + ": " + id);
        return label;
    }

    private static Map<String, Integer> vanillaKeys(GameTestHelper h, ServerPlayer p) {
        Map<String, Integer> entities = new HashMap<>();
        VANILLA_KEYS.forEach((id, text) -> entities.put(id, key(h, p, id, text).getEntityId()));
        long nonKeyNodes = DisplayHud.getHuds(p).keySet().stream()
                .filter(id -> !VANILLA_KEYS.containsKey(id)).count();
        check(h, nonKeyNodes <= 20, "Non-key combat HUD retains the original 20-node budget");
        check(h, DisplayHud.getHuds(p).size() <= 26, "Combat HUD allows six explicit vanilla key rows, at most 26 nodes total");
        return entities;
    }

    private static void remove(ServerPlayer p) {
        try { TestPlayers.remove(p); }
        finally { ClientControls.forget(p); }
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void healthBarUsesRealHealthAbsorptionAndCriticalTint(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.ARC, new Vec3(2, 1, 2), 0, 0);
        try {
            p.setHealth(p.getMaxHealth() / 2);
            p.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_ABSORPTION).setBaseValue(20);
            p.setAbsorptionAmount(6);
            CombatHud.update(p);
            var keyEntities = vanillaKeys(h, p);
            var health = (ItemDisplayHud) DisplayHud.getHud(p, CombatHud.HEALTH_ID);
            check(h, Math.abs(health.getScale().x - 212) < 0.1, "Half health fills exactly half the 424px track");
            check(h, DisplayHud.getHud(p, CombatHud.ABSORPTION_ID) != null, "Actual absorption gets a separate thin bar");
            check(h, Math.abs(health.getScale().y - 7) < 0.1, "Health fill uses the thicker 7px size");
            int entityId = health.getEntityId();
            p.setHealth(p.getMaxHealth() / 5);
            p.setAbsorptionAmount(0);
            CombatHud.update(p);
            health = (ItemDisplayHud) DisplayHud.getHud(p, CombatHud.HEALTH_ID);
            check(h, health.getEntityId() == entityId, "Health updates reuse the same HUD entity");
            check(h, health.getItem().get(DataComponents.CUSTOM_MODEL_DATA).getColor(0) == 0xE75A4E,
                    "Critical health uses red tint");
            check(h, DisplayHud.getHud(p, CombatHud.ABSORPTION_ID) == null, "No fabricated absorption at zero");
            check(h, vanillaKeys(h, p).equals(keyEntities), "Repeated updates reuse every vanilla key entity");
            h.succeed();
        } finally { remove(p); }
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void nonGuardianStillHasVitalsBecauseHeartPackIsGlobal(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2, 1, 2), 0, 0);
        try {
            CombatHud.update(p);
            vanillaKeys(h, p);
            check(h, DisplayHud.getHud(p, CombatHud.ABILITIES_ID) != null, "Guardian has abilities");
            Guardians.data(p).setGuardianClass(GuardianClass.NONE);
            AbilityService.tickPlayer(p);
            check(h, DisplayHud.getHud(p, CombatHud.HEALTH_ID) != null, "Non-guardian health remains visible");
            check(h, DisplayHud.getHud(p, CombatHud.ABILITIES_ID) == null, "Non-guardian ability cluster removed");
            for (String id : VANILLA_KEYS.keySet()) {
                check(h, DisplayHud.getHud(p, id) == null, "Class NONE removes key row: " + id);
            }
            CombatHud.remove(p);
            check(h, DisplayHud.getHuds(p).isEmpty(), "Lifecycle removal clears every HUD node");
            h.succeed();
        } finally { remove(p); }
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void abilityChargeAndEquippedGlyphFollowActualLoadout(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2, 1, 2), 0, 0);
        try {
            int duration = AbilityService.equipped(p, AbilitySlot.GRENADE).orElseThrow().cooldownTicks();
            Guardians.data(p).setCooldown(AbilitySlot.GRENADE, duration / 2);
            CombatHud.update(p);
            var keyEntities = vanillaKeys(h, p);
            check(h, Math.abs(CombatHud.charge(p, AbilitySlot.GRENADE) - 0.5f) < 0.001, "Half cooldown is half charge");
            var tile = (ItemDisplayHud) DisplayHud.getHud(p, CombatHud.ABILITIES_ID);
            check(h, Math.abs(tile.getScale().x - 53) < 0.1 && Math.abs(tile.getScale().y - 53) < 0.1,
                    "Ability tiles are enlarged to 53px");
            var diamond = (ItemDisplayHud) DisplayHud.getHud(p, "destiny:hud_super_diamond");
            check(h, Math.abs(diamond.getScale().x - 80) < 0.1, "Super diamond is enlarged to 80px");
            var gauge = (ItemDisplayHud) DisplayHud.getHud(p, CombatHud.ABILITIES_ID + "_charge");
            check(h, Math.abs(gauge.getScale().x - 24) < 0.1, "Actual charge drives the icon underline");
            var icon = (ItemDisplayHud) DisplayHud.getHud(p, CombatHud.ABILITIES_ID + "_icon");
            check(h, icon.getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/flame"), "Solar uses flame glyph");
            Guardians.data(p).setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(Element.VOID));
            CombatHud.update(p);
            icon = (ItemDisplayHud) DisplayHud.getHud(p, CombatHud.ABILITIES_ID + "_icon");
            check(h, icon.getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/vortex"), "Loadout change changes glyph");
            check(h, vanillaKeys(h, p).equals(keyEntities), "Loadout change reuses every vanilla key entity");
            var client = (GCBPlayer) p;
            client.gcb$markHasMod();
            client.gcb$setModVersion("4.0.0");
            CombatHud.update(p);
            check(h, ClientControls.gcb(p), "Handshake selects GCB key guides");
            var gcbKeys = Map.of("destiny:hud_abilities_key", "Z", "destiny:hud_abilities_1_key", "C",
                    "destiny:hud_abilities_2_key", "V", "destiny:hud_super_key", "F");
            gcbKeys.forEach((id, text) -> check(h,
                    key(h, p, id, text).getEntityId() == keyEntities.get(id),
                    "GCB label change reuses the key entity: " + id));
            for (String id : VANILLA_KEYS.keySet()) {
                if (!gcbKeys.containsKey(id)) {
                    check(h, DisplayHud.getHud(p, id) == null, "GCB removes fallback second line: " + id);
                }
            }
            h.succeed();
        } finally { remove(p); }
    }
}
