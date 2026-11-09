package kim.biryeong.destiny.test;

import kim.biryeong.destiny.inventory.WeaponStorage;
import kim.biryeong.destiny.inventory.gear.GearAcquisition;
import kim.biryeong.destiny.inventory.gear.GearLayout;
import kim.biryeong.destiny.loot.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/** Actual success/failure paths and owner connection packets; not speaker-listening acceptance. */
public final class AcquisitionSoundGameTests {
    private static void check(GameTestHelper h, boolean value, String why) { h.assertTrue(value, Component.literal(why)); }
    private static ServerPlayer player(GameTestHelper h, String name) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 2), 0, 0, name);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        return p;
    }
    private static List<ClientboundSoundPacket> sounds(ServerPlayer p) {
        return TestPlayers.outbound(p).stream().filter(ClientboundSoundPacket.class::isInstance)
                .map(ClientboundSoundPacket.class::cast).toList();
    }
    private static void cue(GameTestHelper h, ServerPlayer p, String tier) {
        var sounds = sounds(p);
        check(h, sounds.size() == 1, "Exactly one acquisition cue, with no legacy pickup/decode overlay: " + sounds.size());
        var sound = sounds.getFirst();
        check(h, sound.getSound().value().location().toString().equals("destiny:loot.acquire." + tier), "Correct supplied recording for " + tier);
        check(h, sound.getSource() == SoundSource.PLAYERS && sound.getPitch() == 1f && sound.getVolume() == 1f,
                "Owner players category, original pitch and unity volume");
    }
    private static ItemStack weapon(ServerPlayer p, WeaponRarity tier) {
        if (tier == WeaponRarity.LEGENDARY || tier == WeaponRarity.EXOTIC)
            return LootRoller.create(WeaponCatalog.find(tier == WeaponRarity.EXOTIC ? "ace_of_spades" : "edge_transit").orElseThrow(), p.getRandom());
        var skin = WeaponSkins.ofRarity(tier).getFirst();
        return LootRoller.create(WeaponCatalog.find(skin.base()).orElseThrow(), skin.id(), p.getRandom());
    }
    private static String soundTier(WeaponRarity tier) {
        return switch (tier) { case COMMON, UNCOMMON, RARE -> "basic"; case LEGENDARY -> "legendary"; case EXOTIC -> "exotic"; };
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void engramsUseEachRarityOnceAndRemainOwnerOnly(GameTestHelper h) {
        var p = player(h, "AudioEngrams"); var other = player(h, "AudioObserver");
        TestPlayers.drain(p); TestPlayers.drain(other);
        for (var tier : WeaponRarity.values()) {
            check(h, Loot.collect(p, LootRoller.Reward.engram(tier.id()), "test"), "Engram acquired: " + tier);
            cue(h, p, soundTier(tier));
        }
        check(h, Loot.storeEngram(p, "prime") == null, "Prime/postmaster acquisition succeeds");
        cue(h, p, "legendary");
        check(h, sounds(other).isEmpty(), "Another owner receives no acquisition packets");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void itemAndDecodeSuccessUseEffectiveSkinTierWithoutDoublePlayback(GameTestHelper h) {
        var p = player(h, "AudioWeapons"); TestPlayers.drain(p);
        for (var tier : WeaponRarity.values()) {
            var item = weapon(p, tier);
            check(h, WeaponRarity.of(item) == tier, "Fixture has effective tier " + tier);
            check(h, Loot.collect(p, LootRoller.Reward.weapon(item), "test"), "Weapon acquisition succeeds");
            cue(h, p, soundTier(tier));
        }
        check(h, GearAcquisition.store(p, weapon(p, WeaponRarity.EXOTIC)) == null, "Direct vendor/admin/gift acquisition succeeds");
        cue(h, p, "exotic");
        p.setAttached(Loot.PROFILE, LootProfile.EMPTY.plus("legendary"));
        check(h, Loot.decode(p, 0) == null, "Decode succeeds"); cue(h, p, "legendary");
        check(h, Loot.decode(p, 0) != null && sounds(p).isEmpty(), "Failed decode stays silent");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void fullStorageOnlySoundsForKeptFallbackAndStarterIsNotRepeated(GameTestHelper h) {
        var p = player(h, "AudioOverflow");
        var legendary = WeaponCatalog.find("edge_transit").orElseThrow();
        for (int i = 0; i < GearLayout.STORAGE_COUNT; i++)
            check(h, WeaponStorage.store(p, LootRoller.create(legendary, p.getRandom())) == null, "Fill power storage silently");
        TestPlayers.drain(p);
        check(h, Loot.collect(p, LootRoller.Reward.weapon(weapon(p, WeaponRarity.LEGENDARY)), "overflow"), "Full weapon bucket retains engram");
        cue(h, p, "legendary");
        p.setAttached(Loot.PROFILE, LootProfile.EMPTY);
        for (int i = 0; i < LootProfile.ENGRAM_CAP; i++) p.setAttached(Loot.PROFILE, Loot.profile(p).plus("legendary"));
        check(h, !Loot.collect(p, LootRoller.Reward.weapon(weapon(p, WeaponRarity.LEGENDARY)), "full"), "No weapon or engram capacity");
        check(h, sounds(p).isEmpty(), "Failed acquisition stays silent");
        check(h, Loot.storeEngram(p, "exotic") != null && sounds(p).isEmpty(), "Failed mailed engram stays silent");
        var starter = player(h, "AudioStarter"); TestPlayers.drain(starter);
        check(h, Loot.grantStarter(starter), "Starter acquired");
        var cues = sounds(starter);
        check(h, cues.size() == 3 && cues.stream().filter(s -> s.getSound().value().location().getPath().equals("loot.acquire.basic")).count() == 2
                && cues.stream().filter(s -> s.getSound().value().location().getPath().equals("loot.acquire.legendary")).count() == 1,
                "Two common campaign weapons and one legendary each use their recording");
        check(h, !Loot.grantStarter(starter) && sounds(starter).isEmpty(), "Repeated starter grant stays silent");
        h.succeed();
    }
}
