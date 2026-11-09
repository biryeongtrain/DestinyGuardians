package kim.biryeong.destiny.test;

import kim.biryeong.destiny.activity.strike.StrikeInstances;
import kim.biryeong.destiny.inventory.WeaponScreenText;
import kim.biryeong.destiny.inventory.WeaponStorage;
import kim.biryeong.destiny.inventory.gear.GearAcquisition;
import kim.biryeong.destiny.inventory.gear.GearLayout;
import kim.biryeong.destiny.loot.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSystemChatPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import xyz.nucleoid.fantasy.util.VoidChunkGenerator;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/** Real strike instance worlds and outbound chat packets, without a graphical client. */
public final class ExoticAcquisitionNoticeGameTests {
    private static void check(GameTestHelper h, boolean value, String why) { h.assertTrue(value, Component.literal(why)); }
    private static List<String> notices(ServerPlayer p) {
        return TestPlayers.outbound(p).stream().filter(ClientboundSystemChatPacket.class::isInstance)
                .map(ClientboundSystemChatPacket.class::cast).filter(c -> !c.overlay())
                .map(c -> c.content().getString()).filter(s -> s.endsWith(" 획득했습니다.")).toList();
    }
    private static ItemStack weapon(ServerPlayer p, String id) { return LootRoller.create(WeaponCatalog.find(id).orElseThrow(), p.getRandom()); }

    private static final class Fixture implements AutoCloseable {
        final StrikeInstances instances;
        final List<ServerPlayer> players = new ArrayList<>();
        StrikeInstances.Instance first, second;
        ServerPlayer owner, mate, outsider;
        boolean closed;
        Fixture(GameTestHelper h) {
            var server = h.getLevel().getServer();
            instances = new StrikeInstances(server, "exotic_notice_qa", 2, 1, 3, () -> new VoidChunkGenerator(server));
            TestCleanup.register(h, this::close);
            owner = create(h, "LootOwner"); mate = create(h, "SameInstance"); outsider = create(h, "OtherInstance");
            first = instances.prepare(List.of(owner.getUUID(), mate.getUUID())).orElseThrow(); instances.ready(first);
            second = instances.prepare(List.of(outsider.getUUID())).orElseThrow(); instances.ready(second);
            check(h, first.level() != second.level() && first.level().dimensionType().equals(second.level().dimensionType()),
                    "Distinct real instances with the same dimension type");
            move(h, owner, first.level(), 2); move(h, mate, first.level(), 100); move(h, outsider, second.level(), 2);
            drain();
        }
        private ServerPlayer create(GameTestHelper h, String name) {
            var p = TestPlayers.create(h, new Vec3(2, 1, 2), 0, 0, name);
            players.add(p); p.setNoGravity(true); h.getLevel().addNewPlayer(p); return p;
        }
        void drain() { players.forEach(TestPlayers::drain); }
        void silent(GameTestHelper h) { for (var p : players) check(h, notices(p).isEmpty(), "No exotic notice for " + p.getGameProfile().name()); }
        void expect(GameTestHelper h, String message) {
            check(h, notices(owner).equals(List.of(message)), "Acquirer gets exactly one correctly named notice");
            check(h, notices(mate).equals(List.of(message)), "Distant same-instance user gets exactly one notice");
            check(h, notices(outsider).isEmpty(), "Other same-type instance is excluded");
        }
        @Override public void close() {
            if (closed) return; closed = true;
            for (var p : players) {
                p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED); TestPlayers.remove(p);
            }
            if (second != null) instances.close(second);
            if (first != null) instances.close(first);
        }
    }
    private static void move(GameTestHelper h, ServerPlayer p, ServerLevel level, int x) {
        check(h, p.teleportTo(level, x + .5, 80, 2.5, Set.of(), 0, 0, true), "Player enters owned instance world");
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100)
    public void exoticEngramWeaponAndDecodeNotifyOnlyCurrentInstanceOnce(GameTestHelper h) {
        try (var f = new Fixture(h)) {
            check(h, Loot.collect(f.owner, LootRoller.Reward.engram("exotic"), "QA"), "Exotic engram acquired");
            f.expect(h, "LootOwner 님이 경이 엔그램을 획득했습니다.");
            check(h, Loot.collect(f.owner, LootRoller.Reward.weapon(weapon(f.owner, "ace_of_spades")), "QA"), "Exotic weapon acquired");
            f.expect(h, "LootOwner 님이 스페이드 에이스를 획득했습니다.");
            check(h, GearAcquisition.store(f.owner, weapon(f.owner, "ace_of_spades")) == null, "Direct grant uses common acquisition path");
            f.expect(h, "LootOwner 님이 스페이드 에이스를 획득했습니다.");
            check(h, Loot.decode(f.owner, 0) == null, "Owned exotic engram decoded");
            var entries = WeaponStorage.entries(f.owner);
            var result = WeaponItems.entry(entries.getLast().stack()).orElseThrow();
            String name = WeaponScreenText.weapon(result.id(), result.name());
            var own = notices(f.owner);
            check(h, own.size() == 1 && own.getFirst().startsWith("LootOwner 님이 " + name), "Decode names the actual rolled exotic weapon");
            check(h, notices(f.mate).equals(own) && notices(f.outsider).isEmpty(), "Decode shares only with the same instance");
            var full = LootProfile.EMPTY;
            for (int i = 0; i < LootProfile.ENGRAM_CAP; i++) full = full.plus("legendary");
            f.owner.setAttached(Loot.PROFILE, full);
            check(h, Loot.collect(f.owner, LootRoller.Reward.engram("exotic"), "auto decode"), "Full engram inventory decodes incoming exotic");
            own = notices(f.owner);
            check(h, own.size() == 1 && !own.getFirst().contains("경이 엔그램"), "Only the actually retained weapon is announced");
            check(h, notices(f.mate).equals(own) && notices(f.outsider).isEmpty(), "Auto decode stays within the instance");
            h.succeed();
        }
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100)
    public void nonExoticFailedDuplicateAndStorageExchangeNeverAnnounce(GameTestHelper h) {
        try (var f = new Fixture(h)) {
            for (String tier : List.of("common", "uncommon", "rare", "legendary"))
                check(h, Loot.collect(f.owner, LootRoller.Reward.engram(tier), "QA"), "Non-exotic acquired");
            var legendary = weapon(f.owner, "edge_transit");
            check(h, GearAcquisition.store(f.owner, legendary) == null, "Legendary acquired"); f.silent(h);
            check(h, GearAcquisition.store(f.owner, legendary) != null, "Already-owned object rejected"); f.silent(h);
            for (int i = 0; i < GearLayout.STORAGE_COUNT; i++)
                check(h, WeaponStorage.store(f.owner, weapon(f.owner, "ace_of_spades")) == null, "Fill kinetic storage without acquiring new loot");
            check(h, !Loot.collect(f.owner, LootRoller.Reward.weapon(weapon(f.owner, "ace_of_spades")), "full"), "Failed exotic cannot be retained");
            f.silent(h);
            var full = LootProfile.EMPTY;
            for (int i = 0; i < LootProfile.ENGRAM_CAP; i++) full = full.plus("legendary");
            f.owner.setAttached(Loot.PROFILE, full);
            check(h, Loot.storeEngram(f.owner, "exotic") != null && Loot.decode(f.owner, -1) != null, "Failed engram receipt and decode"); f.silent(h);
            var stored = WeaponStorage.entries(f.owner).getLast();
            check(h, WeaponStorage.exchange(f.owner, stored.token(), stored.stack(), ItemStack.EMPTY), "Existing ownership exchanged without acquiring an item");
            f.silent(h); h.succeed();
        }
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100)
    public void movingBetweenInstancesImmediatelyChangesAudienceDespiteOldRoster(GameTestHelper h) {
        try (var f = new Fixture(h)) {
            move(h, f.mate, f.second.level(), 100); f.drain();
            check(h, f.first.members().contains(f.mate.getUUID()), "Old activity roster still contains departed fixture member");
            check(h, Loot.collect(f.owner, LootRoller.Reward.engram("exotic"), "QA"), "First world acquisition");
            check(h, notices(f.owner).equals(List.of("LootOwner 님이 경이 엔그램을 획득했습니다.")), "Acquirer hears first-world notice");
            check(h, notices(f.mate).isEmpty() && notices(f.outsider).isEmpty(), "Moved member no longer hears old world");
            check(h, GearAcquisition.store(f.mate, weapon(f.mate, "ace_of_spades")) == null, "Second world acquisition");
            String message = "SameInstance 님이 스페이드 에이스를 획득했습니다.";
            check(h, notices(f.mate).equals(List.of(message)) && notices(f.outsider).equals(List.of(message)), "Current second-world audience hears new owner");
            check(h, notices(f.owner).isEmpty(), "First world remains isolated"); h.succeed();
        }
    }
}
