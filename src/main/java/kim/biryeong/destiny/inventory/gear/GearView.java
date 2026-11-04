package kim.biryeong.destiny.inventory.gear;

import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.inventory.WeaponScreenView;
import kim.biryeong.destiny.weapon.WeaponSlot;

import java.util.List;
import java.util.Map;

/** Immutable frame of the gear screen handed to {@link GearHud}; also the status/test snapshot. */
public record GearView(String playerName, GearLayout.Stage stage, GearSlot expanded, int focus, float cursorX, float cursorY,
                       float cursorYaw, float cursorPitch,
                       Map<WeaponSlot, GearItems.Bucket> buckets, GearItems.Weapon tooltip, GearItems.Weapon compare,
                       GearItems.Weapon detail, float spin, String field, List<WeaponScreenView.CharacterField> fields,
                       List<WeaponScreenView.CharacterOption> options, String message, boolean armory,
                       GuardianClass guardianClass, WeaponScreenView.CharacterView character) {
    public GearView {
        buckets = Map.copyOf(buckets); fields = List.copyOf(fields); options = List.copyOf(options);
    }
    public GearItems.Bucket bucket(WeaponSlot slot) { return buckets.get(slot); }
}
