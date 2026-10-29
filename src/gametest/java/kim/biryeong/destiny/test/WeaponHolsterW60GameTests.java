package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.*;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

/** Real stack/selection/paid reload/HUD paths. Embedded players are NOT native client evidence. */
public final class WeaponHolsterW60GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 6), 0, 0);
        p.setAttached(WeaponLoadout.ENABLED, true);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        return p;
    }
    private static ItemStack item(String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow(); var stack = WeaponItems.create(e);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve));
        return stack;
    }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow())); }
    private static ItemStack rocket(GameTestHelper h, ServerPlayer p, int reserve) {
        var stack = item("bad_omens", 0, reserve);
        check(h, WeaponPerks.select(stack), "Bad Omens has a verified official ALH socket");
        p.getInventory().setItem(2, stack);
        p.getInventory().setItem(0, item("austringer", 7, 0));
        p.getInventory().setSelectedSlot(2);
        WeaponRuntime.tickPlayer(p);
        return stack;
    }
    private static void select(ServerPlayer p, int slot) { p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot)); }
    private static ItemDisplayHud hud(ServerPlayer p, String suffix) { return (ItemDisplayHud)DisplayHud.getHud(p, AmmoHud.PREFIX + suffix); }
    private static void digits(GameTestHelper h, ServerPlayer p, String suffix, int count) {
        var text = Integer.toString(count);
        for (int i = 0; i < text.length(); i++) check(h, hud(p, suffix + "_" + i).getItem().get(DataComponents.ITEM_MODEL)
                .toString().endsWith("/ammo_digit_" + text.charAt(i)), "Authoritative HUD " + suffix + "=" + count);
        check(h, hud(p, suffix + "_" + text.length()) == null, "No stale trailing digit");
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void nativeStowTransfersFiniteReserveExactlyAtDeadlineAndReturnShowsRealMagazine(GameTestHelper h) {
        var p = player(h); var gun = rocket(h, p, 3); long total = ammo(gun).total();
        select(p, 0); CombatHud.update(p); digits(h, p, "stowed_0_total", 3);
        h.runAfterDelay(WeaponPerks.stowedTicks() - 1, () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0 && ammo(gun).reserve() == 3, "No early paid refill");
        });
        h.runAfterDelay(WeaponPerks.stowedTicks(), () -> {
            WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(p); CombatHud.update(p);
            check(h, ammo(gun).rounds() == 1 && ammo(gun).reserve() == 2 && ammo(gun).total() == total, "One actual reload, no ammo minted");
            digits(h, p, "stowed_0_total", 3);
            check(h, hud(p, "reload") == null && !WeaponRuntime.reloading(p), "No fake held reload timer");
            select(p, 2); CombatHud.update(p); digits(h, p, "rounds", 1); digits(h, p, "reserve", 2);
            check(h, p.getMainHandItem() == gun && WeaponHandling.blocked(p) && !WeaponRuntime.beginUse(p), "Same stack; auto-load does not bypass draw");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 210, environment = "destiny-test:w90_isolated")
    public void sameTickDrawRestowCancelsOldWindowAndRestartsTheFullDelay(GameTestHelper h) {
        var p = player(h); var gun = rocket(h, p, 3); select(p, 0);
        h.runAfterDelay(60, () -> { select(p, 2); select(p, 0); });
        h.runAfterDelay(71, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0, "Same-tick native draw was not lost to polling"); });
        h.runAfterDelay(129, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0, "New stow also cannot finish early"); });
        h.runAfterDelay(130, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 1 && ammo(gun).reserve() == 2, "Only new deadline pays"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void keepingWeaponHeldNeverAutoLoadsAndHudQueriesNeverStartTimers(GameTestHelper h) {
        var p = player(h); var gun = rocket(h, p, 3); var before = gun.copy();
        h.startSequence().thenExecuteFor(80, () -> { CombatHud.update(p); AmmoHud.current(p); WeaponRuntime.tickPlayer(p); })
            .thenExecute(() -> {
                check(h, ItemStack.matches(before, gun) && ammo(gun).rounds() == 0, "Held/HUD reads cannot refill");
                select(p, 0); CombatHud.update(p); check(h, ammo(gun).rounds() == 0, "Held time is not stow credit");
            }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void noSelectedTraitMeansNoAutomaticReloadAndCopiesDoNotGetDefaultPerks(GameTestHelper h) {
        var p = player(h); var gun = item("bad_omens", 0, 3); p.getInventory().setItem(2, gun);
        p.getInventory().setItem(0, item("austringer", 4, 0)); p.getInventory().setSelectedSlot(0);
        check(h, WeaponPerks.selected(gun).isEmpty(), "New stack does not fabricate its allowed roll"); WeaponRuntime.tickPlayer(p);
        h.runAfterDelay(80, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0 && ammo(gun).reserve() == 3, "Pool membership alone grants no effect"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void bagOffhandWrongSlotAndStandaloneWeaponsAreNotStowedEquipment(GameTestHelper h) {
        var p = player(h); var bag = rocket(h, p, 3); p.getInventory().setItem(2, ItemStack.EMPTY);
        p.getInventory().setItem(8, bag); var off = bag.copy(); p.setItemInHand(InteractionHand.OFF_HAND, off);
        var wrong = bag.copy(); p.getInventory().setItem(1, wrong); select(p, 0); WeaponRuntime.tickPlayer(p);
        var standalone = player(h); var standaloneGun = rocket(h, standalone, 3); WeaponLoadout.standalone(standalone); select(standalone, 0);
        h.runAfterDelay(80, () -> {
            WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(standalone);
            check(h, ammo(bag).rounds() == 0 && ammo(off).rounds() == 0 && ammo(wrong).rounds() == 0 && ammo(standaloneGun).rounds() == 0,
                    "Only canonical enabled equipment is eligible, not inventory storage"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 170, environment = "destiny-test:w90_isolated")
    public void identicalReplacementCannotInheritTheOldActualStackTimer(GameTestHelper h) {
        var p = player(h); var old = rocket(h, p, 3); select(p, 0); var replacement = old.copy();
        h.runAfterDelay(60, () -> { p.getInventory().setItem(2, replacement); WeaponRuntime.tickPlayer(p); });
        h.runAfterDelay(71, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(old).rounds() == 0 && ammo(replacement).rounds() == 0, "Component equality is not same weapon identity"); });
        h.runAfterDelay(130, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(replacement).rounds() == 1 && ammo(old).rounds() == 0, "Only replacement's own complete window pays"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 170, environment = "destiny-test:w90_isolated")
    public void ownerCleanupCannotRestoreOfflineProgressAndCannotCancelAnotherOwner(GameTestHelper h) {
        var p = player(h); var gun = rocket(h, p, 3); select(p, 0);
        var other = player(h); var otherGun = rocket(h, other, 3); select(other, 0);
        h.runAfterDelay(60, () -> WeaponRuntime.cleanup(p));
        h.runAfterDelay(70, () -> {
            WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(other);
            check(h, ammo(gun).rounds() == 0 && ammo(otherGun).rounds() == 1, "Cleanup drops only the owner's timers");
        });
        h.runAfterDelay(140, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 1, "Fresh observation requires another full window"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void clearedOrCorruptPerksAreInertAndPreviewCannotCarryCombatTraits(GameTestHelper h) {
        var p = player(h); var gun = rocket(h, p, 3); select(p, 0); WeaponPerks.clear(gun);
        var invalid = gun.copy(); var tag = invalid.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString(WeaponPerks.HASH_KEY, Long.toString(WeaponPerks.HASH)); tag.putInt(WeaponPerks.SOCKET_KEY, 3);
        invalid.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponPerks.selected(invalid).isEmpty(), "String hash must not silently coerce");
        tag.putLong(WeaponPerks.HASH_KEY, WeaponPerks.HASH); tag.putDouble(WeaponPerks.SOCKET_KEY, 3);
        invalid.set(DataComponents.CUSTOM_DATA, CustomData.of(tag)); check(h, WeaponPerks.selected(invalid).isEmpty(), "Fractional socket cannot coerce");
        tag.putInt(WeaponPerks.SOCKET_KEY, 63); invalid.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponPerks.selected(invalid).isEmpty(), "Valid hash in an unsupported socket is inert");
        var preview = WeaponModels.create(WeaponCatalog.find("bad_omens").orElseThrow());
        check(h, !WeaponPerks.select(preview) && WeaponPerks.available(preview).isEmpty(), "Preview is not an owned combat item");
        h.runAfterDelay(80, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0, "Removed perk cannot finish its old timer"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void nonOpCommandSelectsOnlyAllowedTraitWithoutMintingOrResettingFireState(GameTestHelper h) throws Exception {
        var p = player(h); var gun = item("bad_omens", 1, 3); p.getInventory().setItem(2, gun); p.getInventory().setSelectedSlot(2);
        var before = gun.copy(); var dispatcher = h.getLevel().getServer().getCommands().getDispatcher(); var source = p.createCommandSourceStack();
        check(h, dispatcher.execute("destiny perk select auto_loading_holster", source) == 1 && WeaponPerks.selected(gun).isPresent(), "Ordinary player selects permitted socket");
        check(h, p.getMainHandItem() == gun && ammo(gun).rounds() == 1 && ammo(gun).reserve() == 3, "No new item or ammo");
        check(h, before.get(DataComponents.ITEM_MODEL).equals(gun.get(DataComponents.ITEM_MODEL)) && before.get(DataComponents.LORE).equals(gun.get(DataComponents.LORE)), "Model and user/generated lore unchanged");
        check(h, dispatcher.execute("destiny perk select rampage", source) == 0, "Unknown/unimplemented traits rejected; W61 now implements Kill Clip");
        check(h, dispatcher.execute("destiny perk status", source) == 1 && dispatcher.execute("destiny perk list", source) == 1, "Non-OP can inspect");
        check(h, WeaponRuntime.beginUse(p), "Actual rocket fired"); WeaponRuntime.cancelUseForSkill(p);
        check(h, dispatcher.execute("destiny perk clear", source) == 1 && dispatcher.execute("destiny perk select auto_loading_holster", source) == 1, "Edits allowed without gameplay reset");
        WeaponRuntime.reloadFromMarksmanDodge(p);
        check(h, !WeaponRuntime.beginUse(p) && ammo(gun).rounds() == 1, "Trait edits and paid reload cannot reset actual firing cadence");
        var unsupported = item("austringer", 7, 0); p.getInventory().setItem(2, unsupported);
        check(h, dispatcher.execute("destiny perk select auto_loading_holster", source) == 0 && WeaponPerks.selected(unsupported).isEmpty(), "No arbitrary unsupported weapon roll");
        p.setGameMode(GameType.SPECTATOR); p.getInventory().setItem(2, gun);
        check(h, dispatcher.execute("destiny perk clear", source) == 0 && WeaponPerks.selected(gun).isPresent(), "Spectator cannot modify owned traits"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void everyAllowedSocketMatchesExactOfficialSelectedWeaponAndSelectionPreservesAmmo(GameTestHelper h) {
        for (var e : WeaponCatalog.all()) {
            var gun = item(e.id(), 0, 0); var before = gun.copy(); var choices = WeaponPerks.available(gun);
            check(h, WeaponPerks.selected(gun).isEmpty(), "No default perk " + e.id());
            check(h, WeaponPerks.select(gun) == !choices.isEmpty(), "Exact allowlist " + e.id());
            if (!choices.isEmpty()) {
                var roll = WeaponPerks.selected(gun).orElseThrow();
                check(h, roll.hash() == WeaponCharacteristics.of(e).bungieHash() && roll.perkHash() == WeaponPerks.HASH,
                        "Exact selected Bungie item and trait, not another release of the same name");
                check(h, WeaponPerks.clear(gun) && ItemStack.matches(before, gun), "Selection+clear roundtrip preserves every existing component");
            } else check(h, ItemStack.matches(before, gun), "Unsupported item unchanged");
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 170, environment = "destiny-test:w90_isolated")
    public void zeroReservesNeverMintAndOneAttemptCannotRepeatWhileKeptStowed(GameTestHelper h) {
        var p = player(h); var gun = rocket(h, p, 0); select(p, 0);
        h.runAfterDelay(70, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0 && ammo(gun).total() == 0, "Empty reserve at completion means zero grant");
            WeaponItems.save(gun, new WeaponMagazine(WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()), 0, 2)); });
        h.runAfterDelay(80, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0, "Authored conservative one-attempt policy; later reserve is not an unbounded reload loop"); select(p, 2); select(p, 0); });
        h.runAfterDelay(150, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 1 && ammo(gun).reserve() == 1, "Restowing arms a new paid attempt"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void primaryAndTwoFiniteCanonicalSlotsReloadIndependentlyWhileHoldingABuildingItem(GameTestHelper h) {
        var p = player(h); var primary = item("duke_mk_44", 1, 0); var special = item("dream_breaker", 1, 2); var heavy = item("bad_omens", 0, 3);
        check(h, WeaponPerks.select(primary) && WeaponPerks.select(special) && WeaponPerks.select(heavy), "All three have their own allowed roll");
        p.getInventory().setItem(0, primary); p.getInventory().setItem(1, special); p.getInventory().setItem(2, heavy);
        p.getInventory().setItem(7, new ItemStack(Items.STONE, 12)); p.getInventory().setSelectedSlot(7);
        WeaponRuntime.tickPlayer(p); var before = p.getMainHandItem().copy();
        h.runAfterDelay(70, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, ammo(primary).rounds() == WeaponProfile.forEntry(WeaponItems.entry(primary).orElseThrow()).magazine() && ammo(primary).reserve() == 0, "Actual infinite primary reserve, not infinite magazine");
            check(h, ammo(special).rounds() == 3 && ammo(special).reserve() == 0 && ammo(special).total() == 3, "Finite partial refill uses only two actual reserve cartridges");
            check(h, ammo(heavy).rounds() == 1 && ammo(heavy).reserve() == 2, "Heavy pool paid independently");
            check(h, ItemStack.matches(before, p.getMainHandItem()) && !WeaponRuntime.reloading(p) && WeaponRuntime.activeProjectiles(p) == 0, "Building stack and input state untouched"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void stowedShotgunBulkReloadConservesSavedOverflowWithoutShellTimers(GameTestHelper h) {
        var p = player(h); var gun = item("dust_rock_blues", 0, 0);
        check(h, WeaponPerks.select(gun), "Exact shotgun socket allows ALH");
        var profile = WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
        WeaponItems.save(gun, new WeaponMagazine(profile, 0, 2, 100)); long total = ammo(gun).total();
        p.getInventory().setItem(0, gun); // Dust Rock is a Kinetic special, not an energy-slot guess.
        check(h, WeaponCharacteristics.of(WeaponItems.entry(gun).orElseThrow()).slot() == WeaponSlot.KINETIC, "Actual bucket used");
        p.getInventory().setItem(7, new ItemStack(Items.STONE)); p.getInventory().setSelectedSlot(7); WeaponRuntime.tickPlayer(p);
        h.runAfterDelay(70, () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == profile.magazine() && ammo(gun).total() == total, "Bulk perk reload conserves reserve and legacy overflow");
            check(h, !WeaponReloadPresentation.active(gun) && WeaponRuntime.activeProjectiles(p) == 0, "No shell animation or speculative shot for stowed perk"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void marksmanReloadDuringStowDoesNotPayAgainOrArmALaterShot(GameTestHelper h) {
        var p = player(h); var gun = rocket(h, p, 3); select(p, 0);
        var primary = p.getMainHandItem();
        int primarySpace = WeaponProfile.forEntry(WeaponItems.entry(primary).orElseThrow()).magazine() - ammo(primary).rounds();
        h.runAfterDelay(50, () -> {
            check(h, WeaponRuntime.reloadFromMarksmanDodge(p) == primarySpace + 1, "Existing all-equipment paid reload includes actual primary space");
            check(h, ammo(gun).rounds() == 1 && ammo(gun).reserve() == 2, "Exactly one heavy cartridge paid at dodge");
        });
        h.runAfterDelay(70, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 1 && ammo(gun).reserve() == 2, "Full magazine cannot pay twice"); });
        h.runAfterDelay(80, () -> { select(p, 2); });
        h.runAfterDelay(125, () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 1 && WeaponRuntime.activeProjectiles(p) == 0, "Waiting through draw never fabricates input");
            check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == 0, "Fresh real input still required");
            WeaponRuntime.cancelUseForSkill(p); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void spectatorAndDeathDropTimersRatherThanMutatingStowedStacks(GameTestHelper h) {
        var p = player(h); var gun = rocket(h, p, 3); select(p, 0);
        var dead = player(h); var deadGun = rocket(h, dead, 3); select(dead, 0);
        h.runAfterDelay(60, () -> { p.setGameMode(GameType.SPECTATOR); WeaponRuntime.tickPlayer(p); dead.setHealth(0); WeaponRuntime.tickPlayer(dead); });
        h.runAfterDelay(80, () -> {
            WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(dead);
            check(h, ammo(gun).rounds() == 0 && ammo(deadGun).rounds() == 0, "Ineligible owners never finish old windows");
            CombatHud.update(p); check(h, hud(p, "panel") == null, "No stale spectator ammo panel"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void goldenGunPropIsNotHolsteredEquipmentAndSuperDoesNotBackdateTheOldTimer(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> check(h,
                kr.toxicity.model.api.BetterModel.limb(kim.biryeong.destiny.fx.HunterModelAssets.MODEL_NAME).isPresent(), "Hunter limb ready"))
            .thenExecute(() -> {
                var p = player(h); Guardians.data(p).setGuardianClass(GuardianClass.HUNTER);
                Guardians.data(p).setLoadout(GuardianClass.HUNTER, kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(Element.SOLAR));
                var gun = rocket(h, p, 3); select(p, 0);
                h.runAfterDelay(60, () -> {
                    Guardians.data(p).setSuperEnergy(1);
                    check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Real Golden Gun activation");
                    WeaponRuntime.tickPlayer(p); CombatHud.update(p); digits(h, p, "rounds", 3);
                    check(h, ammo(gun).rounds() == 0 && hud(p, "reserve_0") == null, "Super uses only its real three shots, not holster ammunition");
                });
                h.runAfterDelay(80, () -> { WeaponRuntime.tickPlayer(p); AbilityService.endSuper(p); WeaponRuntime.tickPlayer(p); });
                h.runAfterDelay(149, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0, "Super cannot make an old stow deadline pay"); });
                h.runAfterDelay(150, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 1 && ammo(gun).reserve() == 2, "Fresh post-super window pays once"); h.succeed(); });
            });
    }
}
