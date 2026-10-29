package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.*;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** Actual accepted ability/item/reserve/earned-brick/HUD paths, not native-input/rendering proof. */
public final class MarksmanDodgeW57GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }
    private static ServerPlayer player(GameTestHelper h, Element element) {
        var p = TestPlayers.hunter(h, element, new Vec3(2.5, 1, 6.5), -90, 0);
        p.setOnGround(true);
        TestCleanup.register(h, () -> { AmmoEconomy.cleanup(p); WeaponRuntime.cleanup(p); AbilityService.cleanup(p); TestPlayers.remove(p); });
        return p;
    }
    private static ItemStack item(String id, int rounds, int reserve) {
        var entry = WeaponCatalog.find(id).orElseThrow(); var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, reserve));
        return stack;
    }
    private static WeaponProfile profile(ItemStack stack) { return WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()); }
    private static WeaponMagazine ammo(ItemStack stack) { return WeaponItems.magazine(stack, profile(stack)); }
    private static ItemStack equip(ServerPlayer p, String id, int rounds, int reserve) {
        var stack = item(id, rounds, reserve);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.getInventory().setItem(WeaponCharacteristics.of(WeaponItems.entry(stack).orElseThrow()).slot().hotbar(), stack);
        return stack;
    }
    private static void dodge(GameTestHelper h, ServerPlayer p) {
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.OK, "Real equipped class ability accepted");
    }
    private static void reset(ServerPlayer p) { AbilityService.resetCooldown(p, AbilitySlot.CLASS_ABILITY); }
    private static void brick(GameTestHelper h, ServerPlayer p, WeaponAmmoType type) {
        var meter = AmmoEconomy.meters(p);
        p.setAttached(AmmoEconomy.METERS, new AmmoMeters(type == WeaponAmmoType.SPECIAL ? AmmoMeters.FULL : meter.special(),
                type == WeaponAmmoType.HEAVY ? AmmoMeters.FULL : meter.heavy()));
        var target = h.spawn(EntityTypes.HUSK, new Vec3(5.5, 1, 6.5)); target.setNoAi(true); target.setPersistenceRequired();
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        TestCleanup.register(h, target::discard);
        Combat.damage(h.getLevel(), p, target, 100, Element.KINETIC, AmmoGeneration.ABILITY);
        check(h, target.isDeadOrDying(), "A real confirmed defeat materialized the personal brick");
    }
    private static ItemDisplayHud hud(ServerPlayer p, String suffix) {
        return (ItemDisplayHud)DisplayHud.getHud(p, AmmoHud.PREFIX + suffix);
    }
    private static void digits(GameTestHelper h, ServerPlayer p, String field, int value) {
        var text = Integer.toString(value);
        for (int i = 0; i < text.length(); i++) {
            var node = hud(p, field + "_" + i);
            check(h, node != null && node.getItem().get(DataComponents.ITEM_MODEL).toString()
                    .equals("destiny:gui/hud/ammo_digit_" + text.charAt(i)), "Actual HUD glyph " + field + "=" + value);
        }
        check(h, hud(p, field + "_" + text.length()) == null, "No stale trailing HUD digit");
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void acceptedDodgeImmediatelyReloadsAllThreeRealSlotsAndUpdatesHeldAndStowedHud(GameTestHelper h) {
        var p = player(h, Element.SOLAR);
        var primary = equip(p, "austringer", 1, 0);
        var special = equip(p, "beloved", 1, 12);
        var heavy = equip(p, "bad_omens", 0, 3);
        p.getInventory().setSelectedSlot(1);
        int specialTotal = (int)ammo(special).total(), heavyTotal = (int)ammo(heavy).total();
        dodge(h, p);
        for (var s : new ItemStack[]{primary, special, heavy}) check(h, ammo(s).rounds() == profile(s).magazine(), "Filled actual equipped magazine");
        check(h, ammo(special).total() == specialTotal && ammo(heavy).total() == heavyTotal, "Finite ammo conserved");
        check(h, p.getInventory().getItem(0) == primary && p.getMainHandItem() == special && p.getInventory().getItem(2) == heavy,
                "No replaced or shadow equipment; selected slot unchanged");
        check(h, Guardians.data(p).cooldown(AbilitySlot.CLASS_ABILITY) == 160, "Existing authored dodge cooldown unchanged");
        digits(h, p, "rounds", ammo(special).rounds()); digits(h, p, "reserve", ammo(special).reserve());
        digits(h, p, "stowed_1_total", (int)ammo(heavy).total());
        check(h, hud(p, "stowed_0_infinity") != null && hud(p, "reload") == null, "Primary infinity and no invented reload timer");
        check(h, Guardians.runtime(p).invulnerableTicks == 6 && Math.hypot(p.getDeltaMovement().x, p.getDeltaMovement().z) > 1,
                "Existing immediate roll physics and six authored invulnerable ticks preserved");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void allCatalogWeaponsUsePaidInstantTransfersAndSwordNeverGetsReloadOrEnergy(GameTestHelper h) {
        var p = player(h, Element.SOLAR); WeaponLoadout.standalone(p);
        for (var entry : WeaponCatalog.all()) {
            var shape = WeaponProfile.forEntry(entry); var stack = item(entry.id(), 0, shape.infiniteReserve() ? 0 : 3);
            if (entry.family().equals("sword")) SwordItems.save(stack, 23456, 9);
            p.setItemInHand(InteractionHand.MAIN_HAND, stack); var before = ammo(stack); var expected = new WeaponMagazine(shape, before.rounds(), before.reserve(), before.overflow());
            if (!entry.family().equals("sword")) expected.reload();
            reset(p); dodge(h, p);
            check(h, ammo(stack).rounds() == expected.rounds() && ammo(stack).reserve() == expected.reserve()
                    && ammo(stack).overflow() == expected.overflow(), "Exact transfer for " + entry.id());
            if (entry.family().equals("sword")) check(h, SwordItems.energy(stack) == 23456, "Dodge cannot recharge sword energy");
            check(h, !AmmoHud.current(p).orElseThrow().reloading() && WeaponRuntime.activeProjectiles(p) == 0, "No invented timer or shot " + entry.id());
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void canonicalSlotsOnlyExcludeBagOffhandPreviewAndWrongSlotEvenWhenHoldingBuildingItem(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var primary = equip(p, "austringer", 0, 0);
        var special = equip(p, "beloved", 0, 8);
        var wrongSlot = item("austringer", 0, 0); p.getInventory().setItem(2, wrongSlot);
        var bag = item("beloved", 0, 8); p.getInventory().setItem(8, bag);
        var offhand = item("bad_omens", 0, 3); p.setItemInHand(InteractionHand.OFF_HAND, offhand);
        var preview = WeaponModels.create(WeaponCatalog.find("beloved").orElseThrow()); p.getInventory().setItem(9, preview); var previewBefore = preview.copy();
        p.getInventory().setSelectedSlot(1); check(h, WeaponRuntime.reload(p), "Existing bound reload before a held nonweapon");
        p.getInventory().setItem(7, new ItemStack(Items.STONE)); p.getInventory().setSelectedSlot(7);
        dodge(h, p);
        check(h, ammo(primary).rounds() == profile(primary).magazine() && ammo(special).rounds() == profile(special).magazine(),
                "All actual equipped slots reload even while a nonweapon is held");
        check(h, ammo(bag).rounds() == 0 && ammo(offhand).rounds() == 0 && ammo(wrongSlot).rounds() == 0, "No backpack/offhand/wrong-slot grant");
        check(h, ItemStack.matches(preview, previewBefore) && p.getMainHandItem().is(Items.STONE), "Preview and live hand unchanged");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void existingTimedReloadAndModelAreCancelledWithoutLaterExtraTransfer(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var stack = equip(p, "beloved", 0, 16); p.getInventory().setSelectedSlot(1);
        check(h, WeaponRuntime.reload(p) && WeaponReloadPresentation.active(stack), "Actual normal reload and model active");
        int oldDelay = profile(stack).reloadTicks(); dodge(h, p);
        check(h, !WeaponReloadPresentation.active(stack) && !WeaponRuntime.ammunition(p).orElseThrow().reloading(), "Instant reload retired both timer and model");
        check(h, WeaponRuntime.beginUse(p), "Real post-dodge shot leaves reloadable magazine space"); var expected = ammo(stack);
        h.startSequence().thenExecuteFor(oldDelay + 3, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, ammo(stack).rounds() == expected.rounds() && ammo(stack).reserve() == expected.reserve(), "Old completion cannot pay or transfer again");
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void partiallyInsertedShotgunIsFilledOnceAndOldNextInsertCannotRefillAPostDodgeShot(GameTestHelper h) {
        var p = player(h, Element.SOLAR); WeaponLoadout.standalone(p);
        var entry = WeaponCatalog.family("shotgun").getFirst(); var shape = WeaponProfile.forEntry(entry);
        var stack = item(entry.id(), 0, shape.reserve()); p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        check(h, shape.shellReload() && WeaponRuntime.reload(p), "Actual progressive shell reload started");
        h.startSequence().thenExecuteAfter(shape.firstReloadTicks() + 1, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, ammo(stack).rounds() == shape.roundsPerInsert() && WeaponRuntime.ammunition(p).orElseThrow().reloading(),
                    "First real insert paid, next shell still pending");
            long total = ammo(stack).total(); dodge(h, p);
            check(h, ammo(stack).rounds() == shape.magazine() && ammo(stack).total() == total
                    && !WeaponRuntime.ammunition(p).orElseThrow().reloading(), "Dodge bulk transfer paid exactly remaining space");
            check(h, WeaponRuntime.beginUse(p), "A real shell is fired after dodge");
        }).thenExecuteFor(shape.reloadTicks() + 3, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, ammo(stack).rounds() == shape.magazine() - 1, "Cancelled next insert cannot silently refill the new shot");
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void pendingBurstIsRetiredButSharedFiringCadenceCannotBeResetByDodge(GameTestHelper h) {
        var p = player(h, Element.SOLAR); WeaponLoadout.standalone(p);
        var entry = WeaponCatalog.family("pulse_rifle").getFirst(); var stack = item(entry.id(), 10, 0); p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        check(h, WeaponRuntime.beginUse(p) && ammo(stack).rounds() == 9, "Real first bolt paid once");
        dodge(h, p); int loaded = ammo(stack).rounds();
        check(h, !WeaponRuntime.beginUse(p) && ammo(stack).rounds() == loaded, "Dodge does not erase just-fired cadence");
        int delay = (int)Math.ceil(profile(stack).cadenceTicks()) + 2;
        h.startSequence().thenExecuteFor(delay, () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(stack).rounds() == loaded, "Cancelled burst/hold cannot synthesize later bullets without new input");
        }).thenExecute(() -> check(h, WeaponRuntime.beginUse(p) && ammo(stack).rounds() == loaded - 1, "New trigger works after preserved real deadline"))
                .thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void drawnBowIsLetDownWithoutReleaseShotThenRestoredToLoadedIdle(GameTestHelper h) {
        var p = player(h, Element.SOLAR); WeaponLoadout.standalone(p);
        var stack = item("biting_winds", 1, 0); p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        p.gameMode.useItem(p, h.getLevel(), stack, InteractionHand.MAIN_HAND);
        check(h, p.isUsingItem() && WeaponBowPresentation.active(stack), "Actual native bow consumption/draw active");
        h.startSequence().thenExecuteAfter(profile(stack).chargeTicks() + 2, () -> {
            dodge(h, p);
            check(h, !p.isUsingItem() && WeaponRuntime.activeProjectiles(p) == 0 && ammo(stack).rounds() == 1, "Dodge letdown cannot release a shot");
            var cmd = stack.get(DataComponents.CUSTOM_MODEL_DATA);
            check(h, WeaponBowPresentation.active(stack) && cmd.getFloat(WeaponBowPresentation.SELECTOR_INDEX).intValue() == WeaponBowPresentation.LOADED,
                    "Loaded idle selector restored, not armed draw or nock");
        }).thenExecuteFor(8, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(stack).rounds() == 1 && WeaponRuntime.activeProjectiles(p) == 0, "No latent old arrow"); })
                .thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void realPersonalBrickIsCollectedAtFifteenButNotOutsideAndNeverForAnotherOwner(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var other = player(h, Element.SOLAR);
        var stack = equip(p, "beloved", 0, 0); equip(other, "beloved", 0, 0); p.getInventory().setSelectedSlot(1);
        brick(h, p, WeaponAmmoType.SPECIAL); var pos = AmmoEconomy.brickPositions(p).getFirst();
        other.setPos(pos); dodge(h, other);
        check(h, AmmoEconomy.bricks(p) == 1 && ammo(other.getInventory().getItem(1)).total() == 0, "Other owner cannot inherit or collect the personal brick");
        p.setPos(pos.add(-15.01, 0, 0)); dodge(h, p);
        check(h, AmmoEconomy.bricks(p) == 1 && ammo(stack).total() == 0, "Outside 15 body units does not collect");
        p.setPos(pos.add(-15, 0, 0)); reset(p); dodge(h, p);
        check(h, AmmoEconomy.bricks(p) == 0 && ammo(stack).rounds() > 0, "Inclusive exact 15 body sphere collects and reloads earned ammo");
        long total = ammo(stack).total(); reset(p); dodge(h, p);
        check(h, ammo(stack).total() == total && AmmoEconomy.bricks(p) == 0, "Same consumed brick cannot be paid twice");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void refillFirstMakesReserveRoomBeforeSinglePickupAndNoSpaceRetainsNextBrick(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var entry = WeaponCatalog.find("beloved").orElseThrow(); var shape = WeaponProfile.forEntry(entry);
        var stack = equip(p, "beloved", 0, shape.reserve()); p.getInventory().setSelectedSlot(1);
        brick(h, p, WeaponAmmoType.SPECIAL); long before = ammo(stack).total(); dodge(h, p);
        check(h, AmmoEconomy.bricks(p) == 0 && ammo(stack).rounds() == shape.magazine() && ammo(stack).total() > before,
                "Existing reserve reload frees room, so a useful earned pickup is not ignored");
        WeaponItems.save(stack, new WeaponMagazine(shape, shape.magazine(), shape.reserve()));
        brick(h, p, WeaponAmmoType.SPECIAL); reset(p); dodge(h, p);
        check(h, AmmoEconomy.bricks(p) == 1 && ammo(stack).rounds() == shape.magazine() && ammo(stack).reserve() == shape.reserve(),
                "Truly full magazine/reserve leaves the earned brick on the ground");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void ordinaryBodyPickupKeepsLineOfSightWhileDodgeUsesDocumentedAuthoredSphere(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var stack = equip(p, "beloved", 0, 0); p.getInventory().setSelectedSlot(1);
        brick(h, p, WeaponAmmoType.SPECIAL); var pos = AmmoEconomy.brickPositions(p).getFirst();
        // Brick sits near x=5.15, body at x=3.8: within ordinary range but behind x=4.
        p.setPos(h.absoluteVec(new Vec3(3.8, 1, 6.5))); h.setBlock(4, 1, 6, Blocks.STONE); h.setBlock(4, 2, 6, Blocks.STONE);
        AmmoEconomy.tickPlayer(p); check(h, AmmoEconomy.bricks(p) == 1, "Existing normal pickup still cannot cross solid wall");
        check(h, p.position().distanceTo(pos) < 15, "Dedicated sphere fixture in range"); dodge(h, p);
        check(h, AmmoEconomy.bricks(p) == 0 && ammo(stack).rounds() > 0, "Authored Marksman body sphere ignores LOS, not a D2 through-wall certification");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void doubleSpecialPickupKeepsExistingSplitThenReloadsBothAndSwordEnergyIsUntouched(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var a = equip(p, "bite_of_the_fox", 0, 0); var b = equip(p, "nezarec_s_whisper", 0, 0);
        var sword = equip(p, "crown_splitter", 5, 0); SwordItems.save(sword, 12345, 7); GlaiveItems.saveEnergy(b, 27150);
        p.getInventory().setSelectedSlot(0); brick(h, p, WeaponAmmoType.SPECIAL); dodge(h, p);
        check(h, ammo(a).rounds() == 1 && ammo(b).rounds() == 2 && ammo(a).reserve() == 0 && ammo(b).reserve() == 0,
                "Existing archetype split grant becomes actual loaded rounds, never full-rate twice");
        check(h, ammo(sword).rounds() == 5 && SwordItems.energy(sword) == 12345 && GlaiveItems.energy(b) == 27150,
                "No reload or energy creation on sword, no glaive energy reset");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void finiteShortageAndSavedOverflowAreConservedInsteadOfGrantingFullFreeMagazines(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var special = equip(p, "beloved", 0, 2); var heavy = equip(p, "bad_omens", 0, 0);
        p.getInventory().setSelectedSlot(1); dodge(h, p);
        check(h, ammo(special).rounds() == 2 && ammo(special).reserve() == 0 && ammo(heavy).rounds() == 0, "Finite shortage pays only available ammo");
        var shape = profile(special); WeaponItems.save(special, new WeaponMagazine(shape, 0, shape.reserve(), 123)); long total = ammo(special).total();
        reset(p); dodge(h, p);
        check(h, ammo(special).rounds() == shape.magazine() && ammo(special).total() == total && ammo(special).overflow() > 0,
                "Legacy overflow debt conserved and usable, never duplicated or clipped by instant reload");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void gamblerOnlyRefreshesMeleeAndDoesNotReloadOrMagnetizeBricks(GameTestHelper h) {
        var p = player(h, Element.ARC); var stack = equip(p, "beloved", 0, 8); p.getInventory().setSelectedSlot(1);
        brick(h, p, WeaponAmmoType.SPECIAL); Guardians.data(p).setCooldown(AbilitySlot.MELEE, 300); dodge(h, p);
        check(h, ammo(stack).rounds() == 0 && ammo(stack).reserve() == 8 && AmmoEconomy.bricks(p) == 1, "Gambler does not acquire Marksman effects");
        // Existing ordinary test separately proves melee refresh near a live enemy.
        check(h, HunterAbilities.GAMBLERS_DODGE.equals(AbilityService.idOf(p, AbilitySlot.CLASS_ABILITY)), "Variant remains Gambler");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void cooldownDeadSpectatorAndSuperRejectionsNeverTransferAmmoOrConsumeBricks(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var stack = equip(p, "beloved", 0, 8); p.getInventory().setSelectedSlot(1);
        brick(h, p, WeaponAmmoType.SPECIAL); Guardians.data(p).setCooldown(AbilitySlot.CLASS_ABILITY, 20);
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.COOLDOWN, "Cooldown denial");
        reset(p); p.setGameMode(GameType.SPECTATOR);
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.FAILED, "Spectator denial");
        p.setGameMode(GameType.SURVIVAL); p.setHealth(0);
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.FAILED, "Death denial");
        p.setHealth(20); Guardians.data(p).setSuperEnergy(1);
        check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Real Solar super active");
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.BUSY, "Super denial");
        check(h, ammo(stack).rounds() == 0 && ammo(stack).reserve() == 8 && AmmoEconomy.bricks(p) == 1, "Denied input never reached reload or collection");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void swordRigHandoffKeepsNewHunterRollInsteadOfCancellingItDuringInstantReload(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var primary = equip(p, "austringer", 0, 0);
        var sword = equip(p, "crown_splitter", 5, 0); SwordItems.save(sword, 34567, 4); p.getInventory().setSelectedSlot(2);
        h.startSequence().thenWaitUntil(() -> check(h, kr.toxicity.model.api.BetterModel.limb(
                kim.biryeong.destiny.fx.SwordStanceAssets.MODEL_NAME).isPresent(), "Real sword rig loaded"))
                .thenExecute(() -> {
                    WeaponRuntime.tickPlayer(p);
                    check(h, kim.biryeong.destiny.fx.PlayerAnimations.swordPlaying(p)
                            && kim.biryeong.destiny.camera.SuperCamera.swordActive(p), "Existing sword loop/camera active");
                    int energy = SwordItems.energy(sword); dodge(h, p);
                    check(h, kim.biryeong.destiny.fx.PlayerAnimations.isPlaying(p)
                            && kim.biryeong.destiny.fx.PlayerAnimations.foreignToSword(p)
                            && !kim.biryeong.destiny.fx.PlayerAnimations.swordPlaying(p)
                            && !kim.biryeong.destiny.camera.SuperCamera.swordActive(p), "Reload cleanup cannot cancel the new Hunter roll or retain old sword camera");
                    check(h, SwordItems.energy(sword) == energy && ammo(sword).rounds() == 5
                            && ammo(primary).rounds() == profile(primary).magazine(), "Sword state preserved, other equipped gun reloaded");
                }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void sameTickDuplicateClassInputCannotReloadOrCollectAgainAfterARealShot(GameTestHelper h) {
        var p = player(h, Element.SOLAR); var stack = equip(p, "austringer", 0, 0); p.getInventory().setSelectedSlot(0);
        dodge(h, p); check(h, WeaponRuntime.beginUse(p), "Fresh real trigger after an unfired dodge"); int rounds = ammo(stack).rounds();
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.COOLDOWN && ammo(stack).rounds() == rounds,
                "Duplicate class input cannot bypass cooldown and refill the paid shot");
        h.succeed();
    }
}
