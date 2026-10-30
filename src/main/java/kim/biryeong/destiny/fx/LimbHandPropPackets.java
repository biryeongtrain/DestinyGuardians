package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.data.DisplayEntityData;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelOutboundHandlerAdapter;
import io.netty.channel.ChannelPromise;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kr.toxicity.model.api.bone.RenderedBone;
import kr.toxicity.model.api.mod.platform.ModItemStack;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.util.TransformedItemStack;
import kr.toxicity.model.impl.fabric.entity.ModelDisplayEntityImpl;
import kr.toxicity.model.impl.fabric.entity.PlayerChannelHandlerImpl;
import kr.toxicity.model.impl.fabric.network.BetterModelBundlePacket;
import kr.toxicity.model.impl.fabric.network.PacketsKt;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.Connection;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBundlePacket;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.HashSet;
import java.util.Set;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Supplier;

/** Scoped to one owned limb tracker. Native bones/stacks, armor and skin never change.
 * Main thread resolves teams/assets; Netty only copies matching hand ITEM metadata.
 * Install before BM in pipeline order (after BM in outbound order), so dirty/full/spawn
 * bundles all use the same projection instead of racing a corrective color packet.
 */
final class LimbHandPropPackets implements AutoCloseable {
    private static final AtomicLong NEXT = new AtomicLong();
    record Rule(Identifier original, Identifier enemy) { }
    private final String name = "destiny_limb_props_" + NEXT.incrementAndGet();
    private final ServerPlayer owner;
    private final EntityTracker tracker;
    private final Supplier<LimbEquipment.Selection> selection;
    private final RenderedBone left;
    private final RenderedBone right;
    // Connection identity prevents a reconnect or old close from touching another session.
    private final Map<ServerGamePacketListenerImpl, Audience> audience = new IdentityHashMap<>();
    private boolean closed;

    private static final class Audience {
        final Channel channel;
        final Projection projection = new Projection();
        Map<Integer, Rule> rules = Map.of();
        boolean enemy;
        boolean repaired;
        final Set<Integer> refreshIds = new HashSet<>();
        Audience(ServerGamePacketListenerImpl connection) {
            channel = PacketsKt.getChannel(PacketsKt.getConnection(connection));
        }
    }

    LimbHandPropPackets(ServerPlayer owner, EntityTracker tracker, Supplier<LimbEquipment.Selection> selection) {
        this.owner = owner;
        this.tracker = tracker;
        this.selection = selection;
        // bone(String) matches the tag-stripped name (left_item/right_item), not rawName.
        // Use the same exact raw names as LimbEquipment.bind so projection targets its displays.
        left = tracker.bone(bone -> bone.name().rawName().equals("pli_left_item"));
        right = tracker.bone(bone -> bone.name().rawName().equals("pri_right_item"));
    }

    /** Called before an equipment commit, or on the owned server clock before bundlers flush. */
    synchronized void publish(boolean repair) {
        if (closed || !owner.level().getServer().isSameThread()) return;
        var current = selection.get();
        Map<Integer, Rule> rules = new HashMap<>();
        addRule(rules, left, current.offItem() != null ? current.offItem()
                : current.bowInLeftHand() ? current.item() : null);
        addRule(rules, right, current.bowInLeftHand() ? null : current.item());
        Map<Integer, Rule> published = Map.copyOf(rules);
        var present = new IdentityHashMap<ServerGamePacketListenerImpl, Boolean>();
        for (ServerPlayer viewer : owner.level().players()) {
            if (viewer.connection == null || viewer.hasDisconnected()) continue;
            var connection = viewer.connection;
            present.put(connection, Boolean.TRUE);
            boolean enemy = CrucibleRuntime.enemies(owner, viewer);
            Audience state = audience.get(connection);
            // Ordinary equipment and viewers never sent a hostile prop need no handler/repair.
            if (state == null && (!enemy || rules.isEmpty())) continue;
            if (state == null) {
                state = new Audience(connection);
                audience.put(connection, state);
            }
            Audience target = state;
            boolean changed = !state.rules.equals(published) || state.enemy != enemy;
            Map<Integer, Rule> previous = state.rules;
            if (changed) {
                state.refreshIds.addAll(previous.keySet());
                state.refreshIds.addAll(published.keySet());
                state.rules = published;
                state.enemy = enemy;
                state.repaired = false;
                ordered(state, () -> {
                    target.projection.rules = enemy ? published : Map.of();
                    if (target.channel.pipeline().context(target.projection) == null) {
                        var anchor = target.channel.pipeline().context(PlayerChannelHandlerImpl.class);
                        if (anchor == null) anchor = target.channel.pipeline().context(Connection.class);
                        if (anchor != null) target.channel.pipeline().addBefore(anchor.name(), name, target.projection);
                    }
                });
            }
            if (repair && !state.repaired && tracker.isSpawned(viewer.getUUID())) {
                // Relationship flips need a refresh even if native item data is not dirty.
                // Read current native equipment after mapping; never resurrect a saved prop.
                refresh(connection, left, state.refreshIds);
                refresh(connection, right, state.refreshIds);
                state.refreshIds.clear();
                state.repaired = true;
                if (!enemy || published.isEmpty()) {
                    detach(state);
                    audience.remove(connection);
                }
            }
        }
        var iterator = audience.entrySet().iterator();
        while (iterator.hasNext()) {
            var entry = iterator.next();
            if (!present.containsKey(entry.getKey())) { detach(entry.getValue()); iterator.remove(); }
        }
    }

    private static void addRule(Map<Integer, Rule> rules, RenderedBone bone, TransformedItemStack transformed) {
        if (bone == null || bone.getDisplay() == null || transformed == null || transformed.isAir()
                || !(transformed.itemStack() instanceof ModItemStack mod)) return;
        Rule rule = rule(mod.source());
        if (rule != null) rules.put(bone.getDisplay().id(), rule);
    }

    static Rule rule(ItemStack original) {
        ItemStack enemy = AbilityVisualVariants.item(original, true);
        if (enemy == original) return null; // No packaged enemy asset: keep native original, no invented tint.
        return new Rule(original.get(DataComponents.ITEM_MODEL), enemy.get(DataComponents.ITEM_MODEL));
    }

    private static void refresh(ServerGamePacketListenerImpl connection, RenderedBone bone,
                                Set<Integer> refreshIds) {
        if (bone == null || !(bone.getDisplay() instanceof ModelDisplayEntityImpl display)) return;
        if (!refreshIds.contains(display.id())) return;
        ItemStack nativeItem = display.getDisplay().getEntityData().get(DisplayEntityData.Item.ITEM).copy();
        connection.send(new ClientboundSetEntityDataPacket(display.id(), List.of(
                SynchedEntityData.DataValue.create(DisplayEntityData.Item.ITEM, nativeItem))));
    }

    private static void ordered(Audience audience, Runnable action) {
        var loop = audience.channel.eventLoop();
        if (loop.inEventLoop()) action.run(); else loop.execute(action);
    }

    private static void detach(Audience state) {
        ordered(state, () -> {
            state.projection.rules = Map.of();
            if (state.channel.pipeline().context(state.projection) != null)
                state.channel.pipeline().remove(state.projection);
        });
    }

    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        audience.values().forEach(LimbHandPropPackets::detach);
        audience.clear();
    }

    private static final class Projection extends ChannelOutboundHandlerAdapter {
        // Confined to this connection's event loop. No player/world lookups here.
        Map<Integer, Rule> rules = Map.of();
        @Override public void write(ChannelHandlerContext context, Object message, ChannelPromise promise) throws Exception {
            context.write(!rules.isEmpty() && message instanceof Packet<?> packet
                    ? project(packet, rules, DisplayEntityData.Item.ITEM) : message, promise);
        }
    }

    /** Copies only matching ITEM entries of the two selected prop displays, including nested BM bundles. */
    static Packet<?> project(Packet<?> incoming, Map<Integer, Rule> rules, EntityDataAccessor<ItemStack> itemAccessor) {
        if (rules.isEmpty()) return incoming;
        if (incoming instanceof ClientboundSetEntityDataPacket data) {
            Rule rule = rules.get(data.id());
            if (rule == null) return incoming;
            List<SynchedEntityData.DataValue<?>> values = new ArrayList<>(data.packedItems().size());
            boolean changed = false;
            for (var value : data.packedItems()) {
                if (value.id() == itemAccessor.id() && value.value() instanceof ItemStack item
                        && rule.original().equals(item.get(DataComponents.ITEM_MODEL))) {
                    ItemStack copy = item.copy();
                    copy.set(DataComponents.ITEM_MODEL, rule.enemy());
                    values.add(SynchedEntityData.DataValue.create(itemAccessor, copy));
                    changed = true;
                } else values.add(value);
            }
            return changed ? new ClientboundSetEntityDataPacket(data.id(), values) : incoming;
        }
        if (incoming instanceof ClientboundBundlePacket bundle) {
            var packets = new ArrayList<Packet<? super ClientGamePacketListener>>();
            boolean changed = false;
            for (var packet : bundle.subPackets()) {
                Packet<?> projected = project(packet, rules, itemAccessor);
                changed |= projected != packet;
                @SuppressWarnings("unchecked") var cast = (Packet<? super ClientGamePacketListener>) projected;
                packets.add(cast);
            }
            if (!changed) return incoming;
            var copy = new ClientboundBundlePacket(packets);
            if ((Object) bundle instanceof BetterModelBundlePacket original
                    && (Object) copy instanceof BetterModelBundlePacket marked)
                marked.bettermodel$setBetterModelPacket(original.bettermodel$isBetterModelPacket());
            return copy;
        }
        return incoming;
    }
}
