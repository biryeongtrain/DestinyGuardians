package kim.biryeong.destiny.weapon;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemLore;
import java.util.List;
import java.util.ArrayList;
import java.util.Optional;

/** Explicit opt-in to combat; saved W30/W32 preview markers alone never grant damage. */
public final class WeaponItems {
    public static final String LIVE = "destiny_weapon_live";
    public static final String ROUNDS = "destiny_weapon_rounds";
    public static final String RESERVE = "destiny_weapon_reserve";
    /** W47 nonnegative long: ammo conserved outside bounded magazine/reserve capacities. */
    public static final String OVERFLOW = "destiny_weapon_overflow";
    public static final String LOADED_LIMIT = "destiny_weapon_loaded_capacity";
    private WeaponItems() {}
    public static Optional<WeaponCatalog.Entry> entry(ItemStack stack) {
        if (!stack.is(WeaponCombatItem.INSTANCE)) return Optional.empty();
        var data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null) return Optional.empty();
        return entry(stack, WeaponReadCache.read(data));
    }
    /** Revalidate the current carrier/model even when a caller already holds the component projection. */
    static Optional<WeaponCatalog.Entry> entry(ItemStack stack, WeaponReadCache.Snapshot read) {
        return stack.is(WeaponCombatItem.INSTANCE) && read.live()
                ? read.entry(stack.get(DataComponents.ITEM_MODEL)) : Optional.empty();
    }
    public static ItemStack create(WeaponCatalog.Entry entry) {
        var stack = WeaponModels.create(entry).transmuteCopy(WeaponCombatItem.INSTANCE);
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putBoolean(LIVE, true);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        stack.set(DataComponents.ITEM_NAME, Component.literal("[전투] " + WeaponExotics.displayName(entry)).withStyle(ChatFormatting.GOLD));
        var profile = WeaponProfile.forEntry(entry);
        var magazine = new WeaponMagazine(profile, profile.magazine(), profile.reserve());
        stack.set(DataComponents.LORE, combatLore(stack, magazine));
        save(stack, magazine);
        if (SwordItems.isSword(stack)) SwordItems.save(stack,SwordCycle.CAPACITY,0);
        return stack;
    }
    public static WeaponMagazine magazine(ItemStack stack, WeaponProfile p) {
        var data = stack.get(DataComponents.CUSTOM_DATA);
        // Missing/corrupt ammunition never refills a saved item.
        p = WeaponComponents.profile(stack, p); // W326 magazine components
        if (data == null) return new WeaponMagazine(p, 0, 0);
        var read = WeaponReadCache.read(data);
        // Pure projection only. HUD/get/inspect must not migrate or save the real item.
        var ammo = new WeaponMagazine(p, read.rounds(), read.reserve(), read.overflow(), loadedLimit(stack, p, read));
        // A sword has a single ammo pool, no magazine/reload. Pure local projection
        // folds legacy reserve/overflow into usable capacity without minting ammo.
        if (SwordItems.isSword(stack)) ammo.reload();
        return ammo;
    }
    /** Only an exact implemented selected roll may retain a saved over-base magazine.
     * A trait edit projects unauthorized excess into reserve/legacy debt without losing ammo. */
    private static int loadedLimit(ItemStack stack, WeaponProfile p, WeaponReadCache.Snapshot read) {
        int base = p.magazine(), maximum = base;
        if (WeaponPerks.selected(stack, "ambitious_assassin").isPresent())
            maximum = (int)Math.min(Integer.MAX_VALUE, ((long)base * 250 + 99) / 100);
        if (WeaponPerks.selected(stack, "clown_cartridge").isPresent())
            maximum = Math.max(maximum, (int)Math.min(Integer.MAX_VALUE, ((long)base * 150 + 99) / 100));
        if (WeaponPerks.selected(stack, "overflow").isPresent()
                || WeaponPerks.selected(stack, "reconstruction").isPresent())
            maximum = Math.max(maximum, (int)Math.min(Integer.MAX_VALUE, (long)base * 2));
        if (WeaponItems.entry(stack).filter(e -> e.id().equals("thorn") && ExoticWeaponsW350.supports(e)).isPresent())
            maximum = Math.max(maximum, 40);
        return (int)Math.clamp(read.loadedLimit(), base, maximum);
    }
    /** Mutation boundary only: write the projected state once, never merge legacy counts again. */
    public static void save(ItemStack stack, WeaponMagazine magazine) {
        var data = stack.get(DataComponents.CUSTOM_DATA);
        var tag = data == null ? new CompoundTag() : data.copyTag();
        tag.putInt(ROUNDS, magazine.rounds());
        tag.putInt(LOADED_LIMIT, magazine.loadedLimit());
        tag.putInt(RESERVE, magazine.reserve());
        if (magazine.overflow() > 0) tag.putLong(OVERFLOW, magazine.overflow());
        else tag.remove(OVERFLOW);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        // Only update our recognized generated ammo line. User lore/other components survive.
        var lore = stack.get(DataComponents.LORE);
        if (lore != null && lore.lines().size() > 1
                && lore.lines().getFirst().getString().equals("W33 PvE 전투 무기 · 서버 판정")
                && (lore.lines().get(1).getString().startsWith("검 탄약 ")
                || lore.lines().get(1).getString().startsWith("탄창 ")
                && lore.lines().get(1).getString().contains(" / 예비 "))) {
            var lines = new ArrayList<>(lore.lines());
            lines.set(1, ammoLine(stack, magazine));
            stack.set(DataComponents.LORE, new ItemLore(lines));
        }
    }
    private static Component ammoLine(ItemStack stack, WeaponMagazine magazine) {
        if (SwordItems.isSword(stack)) return Component.literal("검 탄약 " + magazine.rounds());
        return Component.literal("탄창 " + magazine.rounds() + " / 예비 " +
                (entry(stack).map(WeaponProfile::forEntry).map(WeaponProfile::infiniteReserve).orElse(false) ? "∞" : magazine.reserve()));
    }
    private static ItemLore combatLore(ItemStack stack, WeaponMagazine magazine) {
        var lines = new ArrayList<>(List.of(
                Component.literal("W33 PvE 전투 무기 · 서버 판정").withStyle(ChatFormatting.GOLD),
                ammoLine(stack, magazine),
                Component.literal(SwordItems.isSword(stack)?"좌클릭 약공격 / 우클릭 강공격 / 웅크리기 가드 / 검은 재장전 없음"
                        :GlaiveItems.isGlaive(stack)?"우클릭 발사 / 웅크리기 방패·방패사격 / Q 재장전"
                        :entry(stack).filter(WeaponExotics::izanagi).isPresent()?"우클릭 발사 / 좌클릭 ADS 토글 / Q 재장전 / Shift+Q 연마된 칼날"
                        :"우클릭 발사·유지 / 좌클릭 ADS 토글 / Q 재장전"),
                Component.literal(entry(stack).map(e->e.family().equals("bow")).orElse(false)
                        ?"활: 유지해 당김 · 놓아 발사 · Q: 시위 풀기 · 발사 후 자동 재노킹"
                        :entry(stack).filter(WeaponExotics::izanagi).isPresent()
                        ?"No Distractions: 1초간 사격 없이 ADS · 조준 중 플린치 35% 감소"
                        :"활: 당긴 뒤 놓기 / 융합: 충전 완료 시 발사"),
                Component.literal("검·글레이브: 좌클릭 근접 / 궁극기·스킬 입력 우선")));
        entry(stack).ifPresent(e -> lines.addAll(ExoticDescriptionsW350.lore(e)));
        return new ItemLore(lines);
    }
}
