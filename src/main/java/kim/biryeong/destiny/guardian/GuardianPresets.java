package kim.biryeong.destiny.guardian;

import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.ability.titan.TitanAbilities;
import kim.biryeong.destiny.ability.warlock.WarlockAbilities;

/** Every selectable class uses the same command, persistent loadout and ability service. */
public final class GuardianPresets {
    private GuardianPresets() { }

    public static boolean supported(Element element) {
        return element == Element.ARC || element == Element.SOLAR || element == Element.VOID;
    }

    public static Loadout preset(GuardianClass cls, Element element) {
        if (!supported(element)) throw new IllegalArgumentException("Unsupported subclass " + element);
        return switch (cls) {
            case HUNTER -> HunterAbilities.preset(element);
            case TITAN -> TitanAbilities.preset(element);
            case WARLOCK -> WarlockAbilities.preset(element);
            case NONE -> throw new IllegalArgumentException("Choose a guardian class first");
        };
    }
}
