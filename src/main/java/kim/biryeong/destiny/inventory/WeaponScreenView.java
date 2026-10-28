package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.weapon.WeaponSlot;
import java.util.List;
import java.util.Map;

/** Read-only UI projection. Inventory indices address owned stacks; no items live in the HUD. */
public record WeaponScreenView(String playerName, WeaponSlot selectedSlot, List<Card> equipped,
        List<Card> choices, Card inspected, int page, int pages, int focus,
        float cursorX, float cursorY, String message) {
    public WeaponScreenView { equipped = List.copyOf(equipped); choices = List.copyOf(choices); }
    public record Card(int inventoryIndex, String id, String name, String family, String frame,
            WeaponSlot slot, String damage, String ammo, boolean exotic, Map<String, Integer> stats,
            int rounds, int capacity, boolean equipped) {
        public Card { stats = Map.copyOf(stats); }
    }
}
