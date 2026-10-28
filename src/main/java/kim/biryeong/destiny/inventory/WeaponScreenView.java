package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.weapon.WeaponSlot;
import java.util.List;
import java.util.Map;

/** Read-only UI projection. Index -1 is a catalog preview; no items live in the HUD. */
public record WeaponScreenView(String playerName, WeaponSlot selectedSlot, List<Card> equipped,
        List<Card> choices, Card inspected, int page, int pages, int focus,
        float cursorX, float cursorY, String message, boolean testArmory, String perkGroup,
        List<PerkOption> perks, String selectedDamage, String selectedUtility,
        String stage, List<FamilyOption> families, String selectedFamily) {
    public WeaponScreenView {
        equipped = List.copyOf(equipped);
        choices = List.copyOf(choices);
        perks = List.copyOf(perks);
        families = List.copyOf(families);
        perkGroup = perkGroup == null ? "" : perkGroup;
        selectedDamage = selectedDamage == null ? "" : selectedDamage;
        selectedUtility = selectedUtility == null ? "" : selectedUtility;
        stage = stage == null || stage.isBlank() ? "LOADOUT" : stage;
        selectedFamily = selectedFamily == null ? "" : selectedFamily;
    }

    /** Existing callers enter the loadout without creating or equipping a draft. */
    public WeaponScreenView(String playerName, WeaponSlot selectedSlot, List<Card> equipped,
            List<Card> choices, Card inspected, int page, int pages, int focus,
            float cursorX, float cursorY, String message) {
        this(playerName, selectedSlot, equipped, choices, inspected, page, pages, focus,
                cursorX, cursorY, message, false, "", List.of(), "", "", "LOADOUT", List.of(), "");
    }

    public WeaponScreenView(String playerName, WeaponSlot selectedSlot, List<Card> equipped,
            List<Card> choices, Card inspected, int page, int pages, int focus,
            float cursorX, float cursorY, String message, boolean testArmory, String perkGroup,
            List<PerkOption> perks, String selectedDamage, String selectedUtility) {
        this(playerName, selectedSlot, equipped, choices, inspected, page, pages, focus,
                cursorX, cursorY, message, testArmory, perkGroup, perks, selectedDamage, selectedUtility,
                "LOADOUT", List.of(), "");
    }

    public boolean perkMode() { return "PERKS".equals(stage); }

    /** The wizard edits only its detached draft; other stages retain the prior equipped lookup. */
    public Card perkTarget() {
        if (perkMode()) return inspected;
        return equipped.stream().filter(card -> card.slot() == selectedSlot && card.inventoryIndex() >= 0)
                .findFirst().orElse(null);
    }

    /** Perks, like choices, are the controller's current page of at most nine entries. */
    public record PerkOption(String id, String name, String description,
            boolean selected, boolean enabled, String reason) { }

    /** Like choices/perks, families contains only the controller's current page. */
    public record FamilyOption(String id, String name, int count) { }

    public record Card(int inventoryIndex, String id, String name, String family, String frame,
            WeaponSlot slot, String damage, String ammo, boolean exotic, Map<String, Integer> stats,
            int rounds, int capacity, boolean equipped) {
        public Card { stats = Map.copyOf(stats); }
    }
}
