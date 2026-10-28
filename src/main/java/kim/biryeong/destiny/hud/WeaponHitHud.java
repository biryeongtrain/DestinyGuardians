package kim.biryeong.destiny.hud;

import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Owner-only confirmed weapon feedback. Server-thread only, like CombatHud.
 * Master calls confirm AFTER actual positive HP+absorption loss in WeaponRuntime.apply;
 * CombatHud calls update/remove. No event hooks, damage-number coupling or gameplay mutation.
 */
public final class WeaponHitHud {
    public static final String PREFIX = "destiny:hit_confirmation_w223_";
    public static final String GLYPH_ID = PREFIX + "glyph";
    public static final int MAX_NODES = 1;
    public static final int HIT_COLOR = 0xF1F3F5;
    public static final int KILL_COLOR = 0xE85C50;
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();

    private static final class Session {
        final ServerPlayer owner;
        final MinecraftServer server;
        final WeaponHitState.Binding binding;
        WeaponHitState state = WeaponHitState.idle();
        long lastTick;
        ItemDisplayHud hud;
        WeaponHitState.Cue shown = WeaponHitState.Cue.NONE;

        Session(ServerPlayer owner, long now) {
            this.owner = owner;
            server = owner.level().getServer();
            binding = new WeaponHitState.Binding(owner, owner.connection, owner.level(), owner.level().getServer());
            lastTick = now;
        }

        boolean matches(ServerPlayer player) {
            return binding.matches(player, player.connection, player.level(), player.level().getServer());
        }
    }

    private WeaponHitHud() { }

    /** Caller supplies exclusive observed damage, never requested damage or split floating numbers. */
    public static void confirm(ServerPlayer owner, float observedPositiveDamage, boolean killed) {
        if (!Float.isFinite(observedPositiveDamage) || observedPositiveDamage <= 0 || !eligible(owner)) return;
        long now = owner.level().getServer().getTickCount();
        Session session = current(owner, now);
        if (session == null) {
            session = new Session(owner, now);
            SESSIONS.put(owner.getUUID(), session);
        }
        session.state = session.state.confirm(now, observedPositiveDamage, killed);
        render(session, session.state.cueAt(now));
    }

    /** Rendering does not re-confirm damage. Expiry/rollback drops the entire bounded session. */
    public static void update(ServerPlayer owner) {
        // A delayed old player's update must not evict the current player's UUID-keyed session.
        if (!canonical(owner)) return;
        if (!eligible(owner)) { remove(owner); return; }
        long now = owner.level().getServer().getTickCount();
        Session session = current(owner, now);
        if (session == null) return;
        WeaponHitState.Cue cue = session.state.cueAt(now);
        if (cue == WeaponHitState.Cue.NONE) retire(session);
        else render(session, cue);
    }

    private static boolean canonical(ServerPlayer owner) {
        if (owner == null) return false;
        var server = owner.level().getServer();
        return server != null && server.isSameThread() && server.getPlayerList().getPlayer(owner.getUUID()) == owner;
    }

    private static boolean eligible(ServerPlayer owner) {
        return canonical(owner) && owner.connection != null && owner.isAlive() && !owner.isRemoved()
                && !owner.hasDisconnected() && !owner.isSpectator();
    }

    private static Session current(ServerPlayer owner, long now) {
        Session session = SESSIONS.get(owner.getUUID());
        // Only reached for the canonical live owner. A real replacement starts a clean session.
        if (session != null && (!session.matches(owner) || now < session.lastTick)) {
            retire(session);
            return null;
        }
        if (session != null) session.lastTick = now;
        return session;
    }

    private static void render(Session session, WeaponHitState.Cue cue) {
        ServerPlayer owner = session.owner;
        DisplayHud registered = DisplayHud.getHud(owner, GLYPH_ID);
        if (registered != session.hud) {
            // Do not overwrite an unknown/newer registry object, even if its id was reused.
            if (registered != null) return;
            session.hud = null;
            session.shown = WeaponHitState.Cue.NONE;
        }
        if (session.hud != null && session.shown == cue) return;
        boolean kill = cue == WeaponHitState.Cue.KILL;
        ItemDisplayHud hud = session.hud == null ? new ItemDisplayHud() : session.hud;
        hud.updateWhenDataChanged(false);
        ItemStack stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/hud/"
                + (kill ? "kill_confirmation_w223" : "hit_confirmation_w223")));
        stack.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(List.of(), List.of(), List.of(), List.of(kill ? KILL_COLOR : HIT_COLOR)));
        hud.setItem(stack);
        hud.setItemTransform(ItemDisplayContext.NONE);
        hud.setScale(64, 64, 1);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(960, 540, 8);
        hud.setViewRange(1000);
        hud.setAboveHand(true);
        if (session.hud == null && !hud.spawn(owner, GLYPH_ID)) return;
        session.hud = hud;
        session.shown = cue;
        hud.updateWhenDataChanged(true);
        hud.update();
    }

    /** Idempotent exact-owner cleanup, including after level change/disconnect. Must be called
     * synchronously by CombatHud lifecycle, not queued against a future incarnation of the player.
     */
    public static void remove(ServerPlayer owner) {
        if (owner == null) return;
        Session session = SESSIONS.get(owner.getUUID());
        // Allow exact-object cleanup after a level/connection change, but never UUID-only cleanup.
        if (session != null && session.owner == owner) retire(session);
    }

    /** Master registers once with ServerLifecycleEvents.SERVER_STOPPING. Server-scoped so a late
     * old-server callback cannot clear a new server's sessions in the same JVM.
     */
    public static void clearAll(MinecraftServer server) {
        for (Session session : List.copyOf(SESSIONS.values()))
            if (session.server == server) retire(session);
    }

    private static void retire(Session session) {
        if (!SESSIONS.remove(session.owner.getUUID(), session)) return;
        // Registry is UUID-keyed. Never remove a newer session's node by id alone.
        if (session.hud != null && DisplayHud.getHud(session.owner, GLYPH_ID) == session.hud)
            DisplayHud.removeHud(session.owner, GLYPH_ID);
    }
}
