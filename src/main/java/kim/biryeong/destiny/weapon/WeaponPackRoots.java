package kim.biryeong.destiny.weapon;

import net.minecraft.resources.Identifier;
import java.util.HashSet;
import java.util.Set;

/** Exact current cosmetic routes, derived from the same selectors as Polymer's model getter. */
public final class WeaponPackRoots {
    private WeaponPackRoots() {}

    public static Set<Identifier> active() {
        var roots = new HashSet<Identifier>();
        for (var entry : WeaponCatalog.all()) {
            roots.add(Identifier.parse(entry.item_model()));
            if (WeaponReloadPresentation.supports(entry)) roots.add(WeaponReloadPresentation.model(entry));
            if (WeaponInsertPresentation.supports(entry)) roots.add(WeaponInsertPresentation.model(entry));
            if (WeaponScopes.supports(entry)) roots.add(WeaponScopes.model(entry));
            if (WeaponExotics.izanagi(entry)) roots.add(WeaponIzanagiPresentation.packModel());
            if (WeaponBowPresentation.supports(entry)) roots.add(WeaponBowPresentation.model(entry));
            if (WeaponAimPresentation.supports(entry)) {
                String prefix = WeaponAimPresentation.modelPrefix(entry) + entry.id();
                roots.add(Identifier.fromNamespaceAndPath("destiny", prefix));
                if (WeaponBowPresentation.supports(entry))
                    roots.add(Identifier.fromNamespaceAndPath("destiny", prefix + "_bow"));
            }
            for (var incoming : WeaponCatalog.all())
                if (WeaponSwapPresentation.supports(entry, incoming))
                    roots.add(WeaponSwapPresentation.packModel(entry, incoming));
        }
        return Set.copyOf(roots);
    }
}
