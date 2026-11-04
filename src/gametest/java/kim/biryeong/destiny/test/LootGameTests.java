package kim.biryeong.destiny.test;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.inventory.gear.GearAcquisition;
import kim.biryeong.destiny.loot.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Shared loot: official trait coverage, rolls, starter gear, engrams, storage overflow and personal drops. */
public final class LootGameTests {
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }

    private static ServerPlayer player(GameTestHelper h, String name) {
        for (int x = 0; x < 8; x++) for (int z = 0; z < 8; z++) h.setBlock(x, 0, z, Blocks.STONE);
        var p = TestPlayers.hunter(h, Element.ARC, new Vec3(2.5, 1, 2.5), 0, 0, name);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        p.getInventory().clearContent();
        p.setAttached(Loot.PROFILE, LootProfile.EMPTY);
        return p;
    }

    /** Every trait in every legendary weapon's official columns (manifest snapshot) is selectable there. */
    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void everyOfficialTraitIsImplemented(GameTestHelper h) {
        var in = LootGameTests.class.getResourceAsStream("/destiny/trait-pools.json");
        check(h, in != null, "trait pool snapshot present");
        var root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
        var missing = new ArrayList<String>();
        int checked = 0;
        for (var weapon : root.getAsJsonObject("weapons").entrySet()) {
            var stack = WeaponItems.create(WeaponCatalog.find(weapon.getKey()).orElseThrow());
            var offered = new HashSet<String>();
            for (String id : WeaponPerks.ids()) for (var r : WeaponPerks.available(stack, id)) offered.add(r.socket() + ":" + r.perkHash());
            for (var socket : weapon.getValue().getAsJsonObject().entrySet())
                for (var trait : socket.getValue().getAsJsonObject().entrySet()) {
                    checked++;
                    if (!offered.contains(socket.getKey() + ":" + trait.getKey()))
                        missing.add(weapon.getKey() + "#" + socket.getKey() + " " + trait.getValue().getAsString());
                }
        }
        check(h, checked > 300, "pool snapshot too small: " + checked);
        check(h, missing.isEmpty(), "unimplemented official traits: " + missing);
        h.succeed();
    }

    /** A rolled legendary has exactly one implemented trait in each of its trait columns. */
    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void rolledWeaponsGetOneTraitPerColumn(GameTestHelper h) {
        var random = net.minecraft.util.RandomSource.create(11);
        for (var e : LootRoller.pool(new LootTables.WeaponFilter(false, null, null, null, null, null))) {
            var stack = LootRoller.create(e, random);
            var columns = new HashSet<Integer>(); var chosen = new HashSet<Integer>();
            for (String id : WeaponPerks.ids()) {
                for (var r : WeaponPerks.available(stack, id)) columns.add(r.socket());
                WeaponPerks.selected(stack, id).ifPresent(r -> chosen.add(r.socket()));
            }
            check(h, columns.equals(chosen), e.id() + " columns " + columns + " rolled " + chosen);
        }
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void starterGearEngramsAndOverflow(GameTestHelper h) {
        var p = player(h, "LootStarter");
        check(h, Loot.grantStarter(p), "starter granted once");
        check(h, !Loot.grantStarter(p), "starter not granted twice");
        var held = new ArrayList<String>();
        for (var slot : WeaponSlot.values())
            WeaponItems.entry(p.getInventory().getItem(slot.hotbar())).ifPresent(e -> held.add(slot + "=" + e.id()));
        check(h, held.contains("KINETIC=gnawing_hunger") && held.contains("ENERGY=mindbender_s_ambition_adept")
                && held.contains("POWER=edge_transit"), "starter loadout equipped: " + held);
        check(h, WeaponSkins.of(p.getInventory().getItem(WeaponSlot.KINETIC.hotbar())).isPresent(), "Khvostov skin kept");

        check(h, Loot.collect(p, LootRoller.Reward.engram("legendary"), "test"), "engram kept");
        check(h, Loot.profile(p).engrams().equals(List.of("legendary")), "engram inventory");
        check(h, Loot.decode(p, 0) == null && Loot.profile(p).engrams().isEmpty(), "decode moves engram to storage");
        int stored = 0;
        for (int i = 3; i < 36; i++) if (WeaponItems.entry(p.getInventory().getItem(i)).isPresent()) stored++;
        check(h, stored == 1, "decoded weapon stored: " + stored);

        // Fill the power bucket: further power weapons become engrams instead of being lost.
        var rocket = WeaponCatalog.find("edge_transit").orElseThrow();
        int added = 0;
        for (int i = 0; i < 12; i++) if (GearAcquisition.store(p, LootRoller.create(rocket, p.getRandom())) == null) added++;
        int before = Loot.profile(p).engrams().size();
        check(h, Loot.collect(p, LootRoller.Reward.weapon(LootRoller.create(rocket, p.getRandom())), "test"), "overflow kept");
        check(h, Loot.profile(p).engrams().size() == before + 1, "overflow weapon became an engram");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void personalDropIsCollectedByWalkingOverIt(GameTestHelper h) {
        var p = player(h, "LootDrop");
        Loot.drop(p, p.position().add(.4, 0, 0), LootRoller.Reward.engram("legendary"));
        h.succeedWhen(() -> check(h, Loot.profile(p).engrams().equals(List.of("legendary")), "drop picked up"));
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void activityCompletionGrantsRewardAndChest(GameTestHelper h) {
        var p = player(h, "LootStrike");
        Loot.activityComplete("devils_lair", List.of(p), "악마의 소굴");
        int weapons = 0;
        for (int i = 3; i < 36; i++) if (WeaponItems.entry(p.getInventory().getItem(i)).isPresent()) weapons++;
        check(h, weapons == 1, "completion weapon granted: " + weapons);
        int finalWeapons = weapons;
        // Closing the activity delivers the unopened chest.
        Loot.activityClosed(List.of(p));
        int after = 0;
        for (int i = 3; i < 36; i++) if (WeaponItems.entry(p.getInventory().getItem(i)).isPresent()) after++;
        check(h, after + Loot.profile(p).engrams().size() == finalWeapons + 1, "unopened chest delivered on close");
        h.succeed();
    }
}
