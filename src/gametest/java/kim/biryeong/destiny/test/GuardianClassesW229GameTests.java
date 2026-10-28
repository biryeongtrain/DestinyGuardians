package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.guardian.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/** Shared command/persistence boundaries, rather than testing every provisional number. */
public final class GuardianClassesW229GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean b, String message) { h.assertTrue(b, Component.literal(message)); }
    private static int command(ServerPlayer p, String command) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        return p.level().getServer().getCommands().getDispatcher().execute(command, p.createCommandSourceStack());
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w229CommandsSelectThreeClassesAndPreserveTheirLoadouts(GameTestHelper h) throws Exception {
        var p = TestPlayers.create(h, new Vec3(2, 1, 2), 0, 0);
        try {
            ItemStack item = new ItemStack(Items.DIAMOND);
            p.getInventory().setItem(0, item);
            check(h, command(p, "guardian class titan") == 1, "Titan is selectable");
            check(h, command(p, "guardian subclass solar") == 1, "Titan Solar preset");
            var titan = Guardians.data(p).loadout(GuardianClass.TITAN);
            check(h, command(p, "guardian class warlock") == 1, "Warlock is selectable");
            check(h, command(p, "guardian subclass void") == 1, "Warlock Void preset");
            var warlock = Guardians.data(p).loadout(GuardianClass.WARLOCK);
            check(h, command(p, "guardian class hunter") == 1, "Hunter remains selectable");
            check(h, command(p, "guardian subclass arc") == 1, "Hunter Arc remains equipped");
            check(h, command(p, "guardian class titan") == 1 && Guardians.data(p).loadout().orElseThrow().equals(titan),
                    "Returning to Titan preserves its selected Solar loadout");
            check(h, Guardians.data(p).loadout(GuardianClass.WARLOCK).equals(warlock), "Warlock loadout is independent");
            check(h, p.getInventory().getItem(0) == item, "Class selection never replaces an inventory item");
            check(h, command(p, "guardian subclass kinetic") == 0 && Guardians.data(p).loadout().orElseThrow().equals(titan),
                    "Unsupported element is rejected before changes");
            var restored = GuardianData.CODEC.parse(com.mojang.serialization.JsonOps.INSTANCE,
                    GuardianData.CODEC.encodeStart(com.mojang.serialization.JsonOps.INSTANCE, Guardians.data(p)).getOrThrow()).getOrThrow();
            check(h, restored.loadout(GuardianClass.TITAN).equals(titan)
                    && restored.loadout(GuardianClass.WARLOCK).equals(warlock), "All class presets persist through the actual codec");
            h.succeed();
        } finally { TestPlayers.remove(p); }
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w229AllNinePresetsResolveToTheCorrectClassAndSlot(GameTestHelper h) {
        for (var cls : List.of(GuardianClass.HUNTER, GuardianClass.TITAN, GuardianClass.WARLOCK))
            for (var element : List.of(Element.ARC, Element.SOLAR, Element.VOID)) {
                var preset = GuardianPresets.preset(cls, element);
                for (var slot : AbilitySlot.values()) {
                    var ability = AbilityRegistry.get(preset.get(slot)).orElseThrow();
                    check(h, ability.guardianClass() == cls && ability.slot() == slot,
                            cls + "/" + element + "/" + slot + " must resolve to its own implementation");
                }
            }
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w229InvalidPersistedAbilityCannotCrossClassOrSlotBoundary(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 2), 0, 0);
        try {
            var data = Guardians.data(p);
            data.setGuardianClass(GuardianClass.TITAN);
            data.setLoadout(GuardianClass.TITAN, HunterAbilities.preset(Element.ARC));
            check(h, AbilityService.use(p, AbilitySlot.GRENADE) == AbilityService.Result.NO_ABILITY,
                    "A persisted Hunter grenade is not castable by a Titan");
            var preset = GuardianPresets.preset(GuardianClass.TITAN, Element.ARC);
            data.setLoadout(GuardianClass.TITAN, preset.with(AbilitySlot.GRENADE, preset.get(AbilitySlot.MELEE)));
            check(h, AbilityService.use(p, AbilitySlot.GRENADE) == AbilityService.Result.NO_ABILITY,
                    "Wrong-slot data cannot cast a melee under grenade hooks");
            check(h, data.cooldown(AbilitySlot.GRENADE) == 0, "Rejected data does not consume a cooldown");
            h.succeed();
        } finally { TestPlayers.remove(p); }
    }
}
