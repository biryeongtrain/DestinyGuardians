package kim.biryeong.destiny.activity.presentation;

import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import java.util.*;
import java.util.function.Predicate;

/** Per-session presentation; adapters supply authoritative restriction/wipe facts and eligible viewers. */
public final class ActivityFailurePresentation implements AutoCloseable {
    public static final int ENTRY_TICKS = 100;
    private static final BitSet CHANNELS = new BitSet(64);
    private final UUID activity;
    private final ActivityFailureState state;
    private final Map<UUID, View> viewers = new HashMap<>();
    private final int channel;
    private final Identifier entrySound, wipeSound;
    private boolean closed;
    private static final class View {
        final ServerPlayer player;
        final ActivityFailureHud hud;
        long enteredAt = -1;
        ActivityFailureState.Wipe heardWipe;
        View(ServerPlayer player, UUID activity) { this.player = player; hud = new ActivityFailureHud(player, activity); }
    }
    public ActivityFailurePresentation(UUID activity) {
        this.activity = activity; state = new ActivityFailureState(activity);
        int free = CHANNELS.nextClearBit(0); channel = free < 64 ? free : -1;
        if (channel >= 0) CHANNELS.set(channel);
        entrySound = event("restricted_entry"); wipeSound = event("team_wipe");
    }
    private Identifier event(String name) {
        return Identifier.fromNamespaceAndPath("destiny_activity_failure", name + (channel < 0 ? "" : "_" + channel));
    }
    public ActivityFailureState state() { return state; }
    public void scope(long generation, String zone, boolean restricted) {
        boolean changed = state.generation() != generation || !state.zone().equals(zone) || state.restricted() != restricted;
        if (state.scope(generation, zone, restricted) && changed) clearViewers();
    }
    public boolean beginWipe(long generation) { return !closed && state.beginWipe(generation); }
    public boolean tick(long generation, boolean audienceReady) { return !closed && state.tick(generation, audienceReady); }
    public void render(Collection<ServerPlayer> audience, Predicate<ServerPlayer> hidden, long now, int wipeRemaining) {
        if (closed) return;
        Set<ServerPlayer> current = Collections.newSetFromMap(new IdentityHashMap<>()); current.addAll(audience);
        for (var view : List.copyOf(viewers.values()))
            if (!current.contains(view.player) || view.player.hasDisconnected()) remove(view.player);
        if (!state.restricted() && !state.wiping()) { clearViewers(); return; }
        for (var p : audience) {
            if (p.hasDisconnected()) continue;
            var view = viewers.get(p.getUUID());
            if (view != null && view.player != p) { remove(view.player); view = null; }
            if (view == null) { view = new View(p, activity); viewers.put(p.getUUID(), view); }
            if (!state.wiping() && (hidden.test(p) || kim.biryeong.destiny.inventory.WeaponScreen.active(p))) {
                // Shared screen state covers Gear, Finder and the legacy armory; visibility never re-arms audio.
                view.hud.clear(); continue;
            }
            if (state.wiping()) {
                if (!Objects.equals(view.heardWipe, state.wipe())) { play(p, wipeSound); view.heardWipe = state.wipe(); }
            } else if (view.enteredAt < 0) { play(p, entrySound); view.enteredAt = now; }
            view.hud.render(!state.wiping() && now - view.enteredAt < ENTRY_TICKS, state.wiping(),
                    state.wipeAge(), state.remainingSeconds(), wipeRemaining);
        }
    }
    /** Exact connection only: a delayed old disconnect cannot remove a replacement connection's HUD. */
    public void remove(ServerPlayer player) {
        var view = viewers.get(player.getUUID());
        if (view == null || view.player != player || !viewers.remove(player.getUUID(), view)) return;
        view.hud.clear();
        if (channel >= 0 && !player.hasDisconnected()) {
            player.connection.send(new ClientboundStopSoundPacket(entrySound, SoundSource.PLAYERS));
            player.connection.send(new ClientboundStopSoundPacket(wipeSound, SoundSource.PLAYERS));
        }
    }
    private void clearViewers() { for (var view : List.copyOf(viewers.values())) remove(view.player); }
    private static void play(ServerPlayer player, Identifier sound) {
        var at = player.getEyePosition();
        player.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createVariableRangeEvent(sound)),
                SoundSource.PLAYERS, at.x, at.y, at.z, 1, 1, player.getRandom().nextLong()));
    }
    @Override public void close() {
        if (closed) return;
        closed = true; state.close(); clearViewers(); if (channel >= 0) CHANNELS.clear(channel);
    }
}
