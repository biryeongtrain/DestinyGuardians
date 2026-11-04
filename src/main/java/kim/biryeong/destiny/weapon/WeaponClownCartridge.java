package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Timed-reload authority only. Master owns ammo credit/transfer and lifecycle dispatch.
 * selected/maximumTarget are pure; target is a one-shot completion event with no item writes.
 */
public final class WeaponClownCartridge {
    private static final Map<UUID, Token> RELOADS = new HashMap<>();

    /** Opaque original reload epoch. A later accepted reload or lifecycle hook revokes it. */
    public static final class Token {
        public static final Token NONE = new Token();
        private final ServerPlayer owner;
        private final ServerLevel level;
        private final ItemStack stack;
        private final int slot;
        private final WeaponCatalog.Entry entry;
        private final WeaponPerks.Roll roll;
        private final GuardianData data;
        private final GuardianRuntime runtime;
        private final GuardianClass guardianClass;
        private final boolean loadoutEnabled;
        private final long acceptedTick;
        private boolean consumed;

        private Token() {
            owner = null; level = null; stack = null; slot = -1; entry = null; roll = null;
            data = null; runtime = null; guardianClass = null; loadoutEnabled = false; acceptedTick = -1;
            consumed = true;
        }
        private Token(ServerPlayer p, WeaponCatalog.Entry entry) {
            owner = p; level = p.level(); stack = p.getMainHandItem();
            slot = p.getInventory().getSelectedSlot(); this.entry = entry;
            roll = WeaponPerks.selected(stack, ClownCartridgeProfile.ID).orElseThrow();
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); loadoutEnabled = WeaponLoadout.enabled(p);
            acceptedTick = now(p);
        }
    }

    private WeaponClownCartridge() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Clown Cartridge is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    /** Count-one original hotbar object; loadout mode additionally requires its canonical slot. */
    private static boolean equipped(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty() || stack.getCount() != 1) return false;
        int slot = -1, identities = 0;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            if (p.getInventory().getItem(i) == stack) { identities++; slot = i; }
        }
        return identities == 1 && slot >= 0 && slot < 9 && (!WeaponLoadout.enabled(p)
            || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack));
    }
    /** Pure selected-perk/cap predicate; no token creation, RNG, attachment, or item mutation. */
    public static boolean selected(ServerPlayer p, ItemStack stack) {
        if (!ownerValid(p) || !equipped(p, stack)) return false;
        var entry = WeaponItems.entry(stack).orElse(null);
        return ClownCartridgeProfile.supports(entry)
            && WeaponPerks.selected(stack, ClownCartridgeProfile.ID)
                .filter(ClownCartridgeProfile.rolls()::contains)
                .filter(r -> r.id().equals(entry.id())).isPresent();
    }
    public static int maximumTarget(WeaponCatalog.Entry entry) { return ClownCartridgeProfile.maximumTarget(entry); }

    private static boolean valid(ServerPlayer p, Token token) {
        if (token == null || token.consumed || token.owner != p || !ownerValid(p)) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return RELOADS.get(p.getUUID()) == token && token.level == p.level()
            && token.data == data && data.guardianClass() == token.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == token.runtime && now(p) >= token.acceptedTick
            && WeaponLoadout.enabled(p) == token.loadoutEnabled
            && p.getMainHandItem() == token.stack && p.getInventory().getSelectedSlot() == token.slot
            && p.getInventory().getItem(token.slot) == token.stack && WeaponLoadout.canUse(p)
            && selected(p, token.stack)
            && WeaponItems.entry(token.stack).filter(token.entry::equals).isPresent()
            && WeaponPerks.selected(token.stack, ClownCartridgeProfile.ID).filter(token.roll::equals).isPresent();
    }

    /** Call ONLY after cycle.startReload succeeds. No RNG is drawn on acceptance.
     * Repeated acceptance replaces the epoch, never awards another roll on an older callback.
     */
    public static Token acceptedReload(ServerPlayer p) {
        if (p == null) return Token.NONE;
        thread(p);
        cleanup(p);
        var stack = p.getMainHandItem();
        if (!selected(p, stack) || !WeaponLoadout.canUse(p)) return Token.NONE;
        var token = new Token(p, WeaponItems.entry(stack).orElseThrow());
        RELOADS.put(p.getUUID(), token);
        return token;
    }

    /** Call ONCE after the real timed reload's positive ammo-credit callback (inserted=true).
     * This is an event, never a query/dry-run. Invalid or duplicate callbacks draw no RNG.
     * Consumes the original epoch and returns ceil(base * (1 + sampledPercent/100)).
     * Uniform integer 10..50 is local sampling policy; DDC does not specify discreteness.
     * Caller performs reserve-funded reloadOverflow; this method never grants or saves ammo.
     */
    public static int target(ServerPlayer p, Token token) {
        if (p == null || token == null || token == Token.NONE || token.owner != p) return 0;
        thread(p);
        boolean authorized = valid(p, token);
        token.consumed = true;
        RELOADS.remove(p.getUUID(), token);
        if (!authorized) return 0;
        int percent = ClownCartridgeProfile.minimumBonusPercent()
            + p.getRandom().nextInt(ClownCartridgeProfile.maximumBonusPercent()
                - ClownCartridgeProfile.minimumBonusPercent() + 1);
        return ClownCartridgeProfile.target(token.entry, percent);
    }

    /** Mutation boundary only. Invalid observations retire authority; queries never do. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var token = RELOADS.get(p.getUUID());
        if (token != null && token.owner == p && !valid(p, token)) {
            token.consumed = true;
            RELOADS.remove(p.getUUID(), token);
        }
    }
    /** Actual stow, including same-tick away/back, invalidates the pending timed reload. */
    public static void stowing(ServerPlayer p, ItemStack stack) { changed(p, stack); }
    /** Cancel/edit/stack replacement boundary; an edit-away-and-back cannot revive a token. */
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var token = RELOADS.get(p.getUUID());
        if (token != null && token.owner == p && token.stack == stack) cleanup(p);
    }
    public static void edited(ItemStack stack) {
        var iterator = RELOADS.values().iterator();
        while (iterator.hasNext()) {
            var token = iterator.next();
            if (token.stack == stack) { token.consumed = true; iterator.remove(); }
        }
    }
    /** Death/disconnect/world/class/Super/loadout change and explicit reload cancellation. */
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var token = RELOADS.get(p.getUUID());
        if (token != null && token.owner == p) {
            token.consumed = true;
            RELOADS.remove(p.getUUID(), token);
        }
    }
    public static void clear() {
        RELOADS.values().forEach(token -> token.consumed = true);
        RELOADS.clear();
    }
}
