package kim.biryeong.destiny.inventory;

import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.RecipeBookType;
import net.minecraft.world.item.crafting.RecipeBookCategories;
import net.minecraft.world.item.crafting.display.RecipeDisplayEntry;
import net.minecraft.world.item.crafting.display.RecipeDisplayId;
import java.util.*;

/** Client-only highlighted recipes reveal the otherwise client-local inventory key.
 * Based on InventoryRedirection. Synthetic display IDs never unlock real server recipes.
 * Server thread only; one generation can toggle once, even if several tabs report seen.
 */
public final class InventoryMenuRedirect {
    private static final int BASE = 0x3f000000;
    private static final int LIMIT = 0x40000000;
    private static int next = BASE;
    private record Armed(ServerPlayer owner, Object connection, List<RecipeDisplayId> ids) { }
    private static final Map<UUID, Armed> ARMED = new HashMap<>();
    private static final Map<UUID, ServerPlayer> NATIVE_OPEN = new HashMap<>();
    public static boolean nativeOpen(ServerPlayer player) { return NATIVE_OPEN.get(player.getUUID()) == player; }
    private InventoryMenuRedirect() { }

    public static void init() {
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) ->
                server.execute(() -> { NATIVE_OPEN.remove(handler.getPlayer().getUUID()); arm(handler.getPlayer()); }));
        ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> { NATIVE_OPEN.remove(oldPlayer.getUUID()); arm(newPlayer); });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            NATIVE_OPEN.remove(handler.getPlayer().getUUID(), handler.getPlayer());
            var a = ARMED.get(handler.getPlayer().getUUID());
            if (a != null && a.owner == handler.getPlayer()) ARMED.remove(handler.getPlayer().getUUID());
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
            ARMED.entrySet().removeIf(e -> e.getValue().owner.level().getServer() == server);
            NATIVE_OPEN.entrySet().removeIf(e -> e.getValue().level().getServer() == server);
        });
    }

    /** Keep page-one beacons after vanilla unlock/remove/datapack recipe synchronization. */
    public static void refreshIfArmed(ServerPlayer player) {
        var a = ARMED.get(player.getUUID());
        if (a != null && a.owner == player && a.connection == player.connection) arm(player);
    }

    /** Restore the real client recipe book before a crafting table/furnace/etc opens.
     * The managed inventory book contains only four beacons to guarantee page-one visibility.
     */
    public static void externalMenu(ServerPlayer player) {
        NATIVE_OPEN.remove(player.getUUID(), player);
        var a = ARMED.get(player.getUUID());
        if (a == null || a.owner != player || a.connection != player.connection) return;
        ARMED.remove(player.getUUID());
        player.getRecipeBook().sendInitialRecipeBook(player);
    }

    /** Re-arm after native inventory closes, including a rejected menu-open attempt. */
    public static void closed(ServerPlayer player) {
        NATIVE_OPEN.remove(player.getUUID(), player);
        if (player.containerMenu == player.inventoryMenu) { WeaponStorage.migrate(player); WeaponHotbarGuard.restoreCombatSlot(player); arm(player); }
    }

    /** True only for our reserved beacon, so ordinary seen recipes retain vanilla behavior. */
    public static boolean seen(ServerPlayer player, RecipeDisplayId id) {
        if (id.index() < BASE || id.index() >= LIMIT) return false;
        var a = ARMED.get(player.getUUID());
        if (a == null || a.owner != player || a.connection != player.connection || !a.ids.contains(id)
                || player.containerMenu != player.inventoryMenu) return true;
        // Retire first: queued duplicates cannot toggle the menu a second time.
        ARMED.remove(player.getUUID());
        player.connection.send(new ClientboundRecipeBookRemovePacket(a.ids));
        if (WeaponScreen.toggle(player)) {
            player.connection.send(new ClientboundContainerClosePacket(player.inventoryMenu.containerId));
            arm(player);
        } else {
            // The native inventory remains usable when a midair/super guard rejects our HUD.
            NATIVE_OPEN.put(player.getUUID(), player);
            player.getRecipeBook().sendInitialRecipeBook(player);
        }
        return true;
    }

    private static void arm(ServerPlayer player) {
        if (player.hasDisconnected() || player.isRemoved()) return;
        var previous = ARMED.remove(player.getUUID());
        if (previous != null && previous.owner == player && previous.connection == player.connection)
            player.connection.send(new ClientboundRecipeBookRemovePacket(previous.ids));
        var source = new ArrayList<RecipeDisplayEntry>();
        player.level().getServer().getRecipeManager().listDisplaysForRecipe(
                ResourceKey.create(Registries.RECIPE, Identifier.withDefaultNamespace("crafting_table")), source::add);
        if (source.isEmpty()) return; // A datapack may remove this recipe; /메뉴 remains available.
        var categories = List.of(RecipeBookCategories.CRAFTING_BUILDING_BLOCKS,
                RecipeBookCategories.CRAFTING_REDSTONE, RecipeBookCategories.CRAFTING_EQUIPMENT,
                RecipeBookCategories.CRAFTING_MISC);
        var ids = new ArrayList<RecipeDisplayId>();
        var entries = new ArrayList<ClientboundRecipeBookAddPacket.Entry>();
        for (var category : categories) {
            if (next >= LIMIT) next = BASE;
            var id = new RecipeDisplayId(next++); ids.add(id);
            var display = source.getFirst();
            entries.add(new ClientboundRecipeBookAddPacket.Entry(new RecipeDisplayEntry(id, display.display(),
                    OptionalInt.empty(), category, display.craftingRequirements()), false, true));
        }
        ARMED.put(player.getUUID(), new Armed(player, player.connection, List.copyOf(ids)));
        var settings = player.getRecipeBook().getBookSettings().copy();
        settings.setOpen(RecipeBookType.CRAFTING, true);
        settings.setFiltering(RecipeBookType.CRAFTING, false);
        player.connection.send(new ClientboundRecipeBookSettingsPacket(settings));
        // A client-local shadow, not server unlock mutation. Appending to a full
        // recipe book can put all beacons outside the first page and miss E entirely.
        player.connection.send(new ClientboundRecipeBookAddPacket(entries, true));
    }
}
