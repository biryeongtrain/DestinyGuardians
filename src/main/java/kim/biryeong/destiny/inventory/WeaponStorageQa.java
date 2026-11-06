package kim.biryeong.destiny.inventory;

import com.google.gson.Gson;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import java.util.*;

/** Opt-in isolated QA fixture. Selection sends the real server packet handler, not a direct slot write. */
public final class WeaponStorageQa {
    private WeaponStorageQa() { }
    public static void init() {
        if (!Boolean.getBoolean("destiny.qa.systemWeapons")) return;
        CommandRegistrationCallback.EVENT.register((d, registry, env) -> d.register(Commands.literal("destiny")
                .then(Commands.literal("systemweapons").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.literal("status").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                            var p = EntityArgument.getPlayer(c, "player");
                            c.getSource().sendSuccess(() -> Component.literal(new Gson().toJson(status(p))), false); return 1;
                        })))
                        .then(Commands.literal("migrate").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                            WeaponStorage.migrate(EntityArgument.getPlayer(c, "player")); return 1;
                        })))
                        .then(Commands.literal("select").then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("slot", IntegerArgumentType.integer(1, 9)).executes(c -> {
                                    var p = EntityArgument.getPlayer(c, "player");
                                    p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(IntegerArgumentType.getInteger(c, "slot") - 1));
                                    c.getSource().sendSuccess(() -> Component.literal(new Gson().toJson(status(p))), false); return 1;
                                }))))
                        .then(Commands.literal("equip").then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("token", IntegerArgumentType.integer(WeaponStorage.FIRST_TOKEN)).executes(c -> {
                                    var p = EntityArgument.getPlayer(c, "player"); int token = IntegerArgumentType.getInteger(c, "token");
                                    String error = WeaponEquipmentService.equip(p, token, WeaponStorage.get(p, token));
                                    if (error != null) { c.getSource().sendFailure(Component.literal(error)); return 0; }
                                    c.getSource().sendSuccess(() -> Component.literal(new Gson().toJson(status(p))), false); return 1;
                                })))))));
    }
    public static Map<String, Object> status(ServerPlayer p) {
        var inventory = new ArrayList<Map<String, Object>>();
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            var stack = p.getInventory().getItem(i); var entry = WeaponItems.entry(stack);
            if (entry.isPresent()) inventory.add(Map.of("slot", i, "id", entry.get().id(), "rounds", WeaponItems.magazine(stack, WeaponProfile.forEntry(entry.get())).rounds()));
        }
        var stored = new ArrayList<Map<String, Object>>();
        for (var row : WeaponStorage.entries(p)) {
            var entry = WeaponItems.entry(row.stack());
            var fields = new LinkedHashMap<String, Object>();
            fields.put("token", row.token()); fields.put("id", entry.map(WeaponCatalog.Entry::id).orElse("unknown"));
            fields.put("count", row.stack().getCount());
            entry.ifPresent(e -> { var ammo = WeaponItems.magazine(row.stack(), WeaponProfile.forEntry(e)); fields.put("rounds", ammo.rounds()); fields.put("reserve", ammo.reserve()); });
            fields.put("components", net.minecraft.world.item.ItemStack.CODEC.encodeStart(
                    p.registryAccess().createSerializationContext(com.mojang.serialization.JsonOps.INSTANCE), row.stack()).getOrThrow());
            stored.add(fields);
        }
        return Map.of("player", p.getUUID().toString(), "selected", p.getInventory().getSelectedSlot(), "guiOpen", WeaponHotbarGuard.guiOpen(p),
                "inventoryWeapons", inventory, "storedWeapons", stored, "reloading", WeaponRuntime.reloading(p));
    }
}
