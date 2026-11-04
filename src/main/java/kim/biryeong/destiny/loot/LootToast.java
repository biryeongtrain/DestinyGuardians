package kim.biryeong.destiny.loot;

import kim.biryeong.destiny.inventory.HudPainter;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import java.util.*;

/**
 * Destiny item-acquired notices: a stack of cards at the left edge (icon, rarity band, name, source line). Each card
 * lives {@link #LIFE} ticks; at most {@link #MAX} are shown. Own HUD prefix, so it coexists with combat/gear HUDs.
 */
/* Card layers stay below HudPainter text (depth 130). */
public final class LootToast {
    public static final String PREFIX = "destiny:loot_toast_";
    static final int LIFE = 120, MAX = 4;
    public record Card(String icon, String weapon, String name, String line, int band, int until) { }
    private static final Map<UUID, Deque<Card>> CARDS = new HashMap<>();
    private static final Map<UUID, Boolean> HIDDEN = new HashMap<>();

    private LootToast() { }

    public static void show(ServerPlayer p, String icon, String weapon, String name, String line, int band) {
        var q = CARDS.computeIfAbsent(p.getUUID(), k -> new ArrayDeque<>());
        q.addFirst(new Card(icon, weapon, name, line, band, p.level().getServer().getTickCount() + LIFE));
        while (q.size() > MAX) q.removeLast();
        render(p);
    }

    static void tick(MinecraftServer server) {
        int now = server.getTickCount();
        for (var it = CARDS.entrySet().iterator(); it.hasNext(); ) {
            var e = it.next();
            var p = server.getPlayerList().getPlayer(e.getKey());
            if (p == null) { HIDDEN.remove(e.getKey()); it.remove(); continue; }
            boolean gear = kim.biryeong.destiny.inventory.gear.GearScreen.active(p);
            if (gear != Boolean.TRUE.equals(HIDDEN.put(e.getKey(), gear))) render(p);
            if (e.getValue().removeIf(c -> c.until() <= now)) {
                render(p);
                if (e.getValue().isEmpty()) it.remove();
            }
        }
    }

    static void forget(ServerPlayer p) { CARDS.remove(p.getUUID()); HIDDEN.remove(p.getUUID()); }

    private static void render(ServerPlayer p) {
        var painter = new HudPainter(p, PREFIX);
        // The gear screen shows the change itself; cards wait underneath and reappear when it closes.
        var q = kim.biryeong.destiny.inventory.gear.GearScreen.active(p) ? new ArrayDeque<Card>() : CARDS.getOrDefault(p.getUUID(), new ArrayDeque<>());
        float y = 700;
        int i = 0;
        for (var c : q) {
            String k = "c" + i++;
            painter.rect(k + "_bg", 250, y, 380, 76, 120, 0x0E1318);
            painter.rect(k + "_band", 250, y - 32, 380, 12, 121, c.band());
            if (c.icon() != null) painter.icon(k + "_icon", c.icon(), 98, y + 4, 60, 124, 0xFFFFFF);
            else if (c.weapon() != null) painter.weapon(k + "_icon", c.weapon(), 98, y + 4, 60, 124);
            painter.textLeft(k + "_name", c.name(), 138, y - 12, 22, 0xF2F2EE, 280, 255);
            painter.textLeft(k + "_line", c.line(), 138, y + 16, 18, 0x9AA3AA, 280, 255);
            y -= 92;
        }
        painter.finish();
    }
}
