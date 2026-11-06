package kim.biryeong.destiny.inventory.gear;

import com.mojang.brigadier.arguments.StringArgumentType;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;


/**
 * The single path that puts a new weapon into a Guardian's possession (rewards, vendors and admin grants all
 * call {@link #give}). The weapon goes to persistent player storage with its perks rolled once; perks stay
 * bound to that stack. A bucket holds at most {@link GearLayout#STORAGE_COUNT} stored weapons.
 */
public final class GearAcquisition {
    private GearAcquisition() { }

    public static void init() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) ->
                dispatcher.register(Commands.literal("destiny").then(Commands.literal("gear")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.literal("give").then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("id", StringArgumentType.word()).executes(c -> {
                                    var p = EntityArgument.getPlayer(c, "player");
                                    String id = StringArgumentType.getString(c, "id");
                                    var entry = WeaponCatalog.find(id);
                                    var skin = WeaponSkins.find(id);   // W325/W302 skin ids give the skinned weapon
                                    if (entry.isEmpty() && skin.isPresent()) entry = WeaponCatalog.find(skin.get().base());
                                    if (entry.isEmpty()) { c.getSource().sendFailure(Component.literal("무기 id를 찾을 수 없습니다.")); return 0; }
                                    String error = store(p, kim.biryeong.destiny.loot.LootRoller.create(entry.get(),
                                            skin.map(WeaponSkins.Skin::id).orElse(null), p.getRandom()));
                                    if (error != null) { c.getSource().sendFailure(Component.literal(error)); return 0; }
                                    c.getSource().sendSuccess(() -> Component.literal("지급: " + id), false);
                                    return 1;
                                }))))
                        .then(Commands.literal("equip").then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("id", StringArgumentType.word()).executes(c -> {
                                    // QA: replace the loadout slot's weapon with a fresh one (catalog or skin id) and hold it.
                                    var p = EntityArgument.getPlayer(c, "player");
                                    String id = StringArgumentType.getString(c, "id");
                                    var skin = WeaponSkins.find(id);
                                    // Legendary IDs have their own catalog identity even when they also expose skin assets.
                                    var entry = WeaponCatalog.find(id);
                                    if (entry.isEmpty() && skin.isPresent()) entry = WeaponCatalog.find(skin.get().base());
                                    if (entry.isEmpty()) { c.getSource().sendFailure(Component.literal("무기 id를 찾을 수 없습니다.")); return 0; }
                                    var stack = kim.biryeong.destiny.loot.LootRoller.create(entry.get(), skin.map(WeaponSkins.Skin::id).orElse(null), p.getRandom());
                                    var slot = WeaponLoadout.slot(p, stack, entry.get());
                                    p.getInventory().setItem(slot.hotbar(), stack);
                                    p.getInventory().setChanged();
                                    p.setAttached(WeaponLoadout.ENABLED, true);
                                    WeaponLoadout.select(p, slot);
                                    WeaponHandling.update(p);
                                    c.getSource().sendSuccess(() -> Component.literal("장착: " + id), false);
                                    return 1;
                                }))))
                        .then(Commands.literal("status").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                            var p = EntityArgument.getPlayer(c, "player");
                            String text = GearScreen.snapshot(p).map(GearScreen::describe).orElse("GearScreen closed");
                            c.getSource().sendSuccess(() -> Component.literal(text), false);
                            return 1;
                        }))))));
    }

    /** Null on success; otherwise why the weapon could not be stored. Never displaces an existing item. */
    public static String give(ServerPlayer p, WeaponCatalog.Entry entry, net.minecraft.util.RandomSource random) {
        return store(p, kim.biryeong.destiny.loot.LootRoller.create(entry, random));
    }

    /** Put an already-built weapon stack (perks rolled) into storage. Null on success; never displaces items. */
    public static String store(ServerPlayer p, ItemStack stack) {
        return kim.biryeong.destiny.inventory.WeaponStorage.store(p, stack);
    }
}
