package kim.biryeong.destiny.economy;

import net.minecraft.nbt.CompoundTag;

/**
 * An item held by the economy (vault, postmaster, auction listing). The stack is kept as its encoded NBT so a
 * payload that cannot be decoded (a removed item, a codec change) is never dropped: it stays in the ledger and is
 * shown as damaged. The descriptive fields are a snapshot taken when the item entered the economy, used for
 * browsing and search without decoding.
 *
 * @param uid      ledger-unique id; every move keeps it, so a client click on a stale view can be matched exactly
 * @param weaponId catalog id (or skin id) for icons/search, empty for non-weapons
 * @param name     display name at deposit time
 * @param rarity   {@link kim.biryeong.destiny.weapon.WeaponRarity#id()} or empty
 * @param slot     KINETIC / ENERGY / POWER for weapons, empty otherwise
 */
public record ItemPayload(long uid, CompoundTag stack, String weaponId, String name, String rarity, String slot) {
    public ItemPayload {
        if (stack == null) throw new IllegalArgumentException("stack");
        stack = stack.copy();
        weaponId = weaponId == null ? "" : weaponId;
        name = name == null || name.isBlank() ? "알 수 없는 아이템" : name;
        rarity = rarity == null ? "" : rarity;
        slot = slot == null ? "" : slot;
    }

    @Override public CompoundTag stack() { return stack.copy(); }
    public boolean weapon() { return !weaponId.isEmpty(); }

    public CompoundTag write() {
        var t = new CompoundTag();
        t.putLong("uid", uid); t.put("stack", stack.copy());
        t.putString("weapon", weaponId); t.putString("name", name); t.putString("rarity", rarity); t.putString("slot", slot);
        return t;
    }

    public static ItemPayload read(CompoundTag t) {
        return new ItemPayload(t.getLongOr("uid", 0), t.getCompoundOrEmpty("stack"), t.getStringOr("weapon", ""),
                t.getStringOr("name", ""), t.getStringOr("rarity", ""), t.getStringOr("slot", ""));
    }
}
