package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Timed counters belong to actual owned stacks, including in-flight precision hits after stow. */
public final class WeaponPrecisionReturn {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Counter {
        final PrecisionReturnProfile.Perk perk;
        final PrecisionReturnCycle cycle;
        Counter(PrecisionReturnProfile.Perk p) { perk = p; cycle = new PrecisionReturnCycle(p.hits(), p.windowTicks()); }
    }
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final List<Counter> counters;
        Session(ServerPlayer p) {
            owner = p; level = p.level(); stack = p.getMainHandItem();
            counters = PrecisionReturnProfile.perks().stream()
                    .filter(perk -> WeaponPerks.selected(stack, perk.id()).isPresent()).map(Counter::new).toList();
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Session session;
        private boolean credited;
        private Token(Session s) { session = s; }
    }
    private WeaponPrecisionReturn() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (s.owner != p || s.level != p.level() || !ownerValid(p)) return false;
        boolean owns = false;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == s.stack) { owns = true; break; }
        if (!owns) return false;
        return PrecisionReturnProfile.perks().stream().allMatch(perk ->
                WeaponPerks.selected(s.stack, perk.id()).isPresent()
                        == s.counters.stream().anyMatch(c -> c.perk.id().equals(perk.id())));
    }
    public static void update(ServerPlayer p) {
        if (!ownerValid(p)) { cleanup(p); return; }
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> !valid(p, s));
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static Token capture(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || AbilityService.inSuper(p)
                || PrecisionReturnProfile.perks().stream().noneMatch(perk -> WeaponPerks.selected(p.getMainHandItem(), perk.id()).isPresent()))
            return Token.NONE;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        return new Token(sessions.computeIfAbsent(p.getMainHandItem(), ignored -> new Session(p)));
    }
    /** Only the production damage transaction calls this after real positive precision HP/absorption loss. */
    public static void confirmed(ServerPlayer p, Token token, boolean precision) {
        var s = token.session;
        if (!precision || s == null || token.credited) return;
        token.credited = true; // An emission cannot award twice, even if callbacks or pellets repeat.
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null || sessions.get(s.stack) != s || !valid(p, s)) return;
        var entry = WeaponItems.entry(s.stack).orElseThrow();
        var ammo = WeaponItems.magazine(s.stack, WeaponProfile.forEntry(entry));
        int returned = 0;
        for (var counter : s.counters)
            if (counter.cycle.hit(now(p))) returned += ammo.generateLoaded(counter.perk.returnRounds());
        if (returned > 0) {
            WeaponItems.save(s.stack, ammo);
            p.getInventory().setChanged();
            p.containerMenu.broadcastChanges();
        }
    }
    /** Diagnostic/read-only progress, not an invented original-game HUD countdown. */
    public static int progress(ServerPlayer p, String id) {
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(p.getMainHandItem());
        if (s == null || !valid(p, s) || !WeaponLoadout.canUse(p) || AbilityService.inSuper(p)) return 0;
        return s.counters.stream().filter(c -> c.perk.id().equals(id)).findFirst()
                .map(c -> c.cycle.progress(now(p))).orElse(0);
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) { sessions.remove(stack); if (sessions.isEmpty()) SESSIONS.remove(p.getUUID()); }
    }
    public static void cleanup(ServerPlayer p) {
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions != null) { sessions.values().removeIf(s -> s.owner == p); if (sessions.isEmpty()) SESSIONS.remove(p.getUUID()); }
    }
    public static void clear() { SESSIONS.clear(); }
}
