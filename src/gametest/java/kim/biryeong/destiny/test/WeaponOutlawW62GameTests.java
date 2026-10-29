package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

/** Real paid shots, humanoid hit geometry, confirmed final blows and timed ammunition transfers.
 * Embedded server TestPlayers only: this is not native input, recoil control or rendering evidence.
 * The W61 fixture deliberately re-aims between shots; it never injects Outlaw kill credit.
 */
public final class WeaponOutlawW62GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String OUTLAW = OutlawProfile.ID;
    private static final int DURATION = 120;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static boolean near(float a, float b) { return Math.abs(a - b) < .002f; }
    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true); p.setOnGround(true);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); WeaponAiming.cleanup(p); TestPlayers.remove(p); });
        return p;
    }
    private static WeaponCatalog.Entry entry(ItemStack s) { return WeaponItems.entry(s).orElseThrow(); }
    private static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(entry(s)); }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, profile(s)); }
    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, int rounds, int reserve, boolean outlaw) {
        var e = WeaponCatalog.find(id).orElseThrow(); var s = WeaponItems.create(e);
        WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve));
        if (outlaw) check(h, WeaponPerks.select(s, OUTLAW), "Exact official Outlaw socket for " + id);
        int slot = WeaponCharacteristics.of(e).slot().hotbar();
        p.getInventory().setItem(slot, s); p.getInventory().setSelectedSlot(slot); WeaponRuntime.tickPlayer(p);
        return s;
    }
    private static ItemStack duke(GameTestHelper h, ServerPlayer p) {
        return equip(h, p, "duke_mk_44", 9, 0, true);
    }
    /** W61 re-aim fixture: reset only previous recoil/aim, never cadence, ammo or a perk session. */
    private static void reaim(ServerPlayer p) {
        WeaponAiming.cleanup(p); p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
    }
    private static double lane(GameTestHelper h, ServerPlayer p) {
        return p.getZ() - h.absoluteVec(Vec3.ZERO).z;
    }
    private static Husk target(GameTestHelper h, ServerPlayer p, double y, float health) {
        var e = h.spawn(EntityTypes.HUSK, new Vec3(8.5, y, lane(h, p)));
        e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); e.setHealth(health);
        TestCleanup.register(h, e::discard);
        var origin = h.absoluteVec(Vec3.ZERO); var box = e.getBoundingBox();
        check(h, box.minX > origin.x && box.maxX < origin.x + 16
                && box.minY > origin.y && box.maxY < origin.y + 8
                && box.minZ > origin.z && box.maxZ < origin.z + 12,
                "Entire target AABB stays inside the 16x8x12 floor fixture");
        return e;
    }
    /** Eye at relative 2.62: y=1 Husk upper quarter starts near 2.46; y=1.8 starts near 3.26. */
    private static Husk head(GameTestHelper h, ServerPlayer p, float health) {
        var e = target(h, p, 1, health); var b = e.getBoundingBox();
        check(h, p.getEyeY() >= b.maxY - b.getYsize() * .25 && p.getEyeY() < b.maxY,
                "Horizontal paid shot crosses actual upper-quarter precision geometry");
        return e;
    }
    private static Husk body(GameTestHelper h, ServerPlayer p, float health) {
        var e = target(h, p, 1.8, health); var b = e.getBoundingBox();
        check(h, p.getEyeY() > b.minY && p.getEyeY() < b.maxY - b.getYsize() * .25,
                "Horizontal paid shot crosses the body below the actual precision quarter");
        return e;
    }
    private static void shot(GameTestHelper h, ServerPlayer p, Husk target, boolean precision) {
        reaim(p); var s = p.getMainHandItem(); int before = ammo(s).rounds();
        // W241 uses a random hip/air cone. Inspect and replay one draw rather than
        // assuming the horizontal look vector is the actual paid firing ray.
        p.getRandom().setSeed(0x5DEECE66DL);
        var from = p.getEyePosition(); var ray = WeaponAiming.direction(p);
        var hit = target.getBoundingBox().inflate(.03)
                .clip(from, from.add(ray.scale(WeaponBallistics.traceRange(profile(s))))).orElseThrow();
        check(h, WeaponPrecision.critical(target, from, hit, WeaponBallistics.of(entry(s)).precision()) == precision,
                "Seeded actual ray crosses the intended precision/body region before cartridge payment");
        check(h, p.level().clip(new net.minecraft.world.level.ClipContext(from, hit,
                net.minecraft.world.level.ClipContext.Block.COLLIDER, net.minecraft.world.level.ClipContext.Fluid.NONE, p))
                .getType() == net.minecraft.world.phys.HitResult.Type.MISS,
                "Seeded precision/body witness has an unobstructed real firing corridor");
        p.getRandom().setSeed(0x5DEECE66DL);
        check(h, WeaponRuntime.beginUse(p) && ammo(s).rounds() == before - 1,
                "Accepted actual shot pays exactly one real cartridge");
        WeaponRuntime.releaseUse(p, s);
    }
    private static void deniedShot(GameTestHelper h, ServerPlayer p) {
        reaim(p); var s = p.getMainHandItem(); var before = s.copy();
        check(h, !WeaponRuntime.beginUse(p) && ItemStack.matches(before, s),
                "Original firing deadline denies the shot without spending or changing ammunition");
        WeaponRuntime.releaseUse(p, s);
    }
    private static void precisionKill(GameTestHelper h, ServerPlayer p) {
        var e = head(h, p, 1); shot(h, p, e, true);
        check(h, e.isDeadOrDying() && e.getHealth() == 0,
                "Actual low-HP humanoid precision final blow, not injected perk credit"); e.discard();
    }
    private static int fast(ItemStack s) { return OutlawProfile.reload(entry(s)).firstTicks(); }
    private static void select(ServerPlayer p, int slot) {
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));
    }

    @GameTest(structure = FLOOR, maxTicks = 140, environment = "destiny-test:w90_isolated")
    public void actualLowHpHeadshotImmediatelyStartsExactlyOneHundredTwentyTicks(GameTestHelper h) {
        var p = player(h, 6.5); var gun = duke(h, p); precisionKill(h, p); var saved = gun.copy();
        check(h, OutlawProfile.perk().durationTicks() == DURATION, "Pinned six-second contract");
        for (int i = 0; i < 8; i++) check(h, WeaponOutlaw.remaining(p) == DURATION,
                "Confirmed headshot immediately grants 120 ticks without waiting for reload");
        check(h, ItemStack.matches(saved, gun), "Repeated perk reads neither reload nor mutate the stack");
        h.runAfterDelay(119, () -> check(h, WeaponOutlaw.remaining(p) == 1 && ammo(gun).rounds() == 8,
                "Last active tick does not automatically refill primary ammunition"));
        h.runAfterDelay(120, () -> {
            check(h, WeaponOutlaw.remaining(p) == 0 && ammo(gun).rounds() == 8,
                    "Exact expiry has no implicit ammunition transfer"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void actualBodyFinalBlowNeverActivatesOutlaw(GameTestHelper h) {
        var p = player(h, 6.5); var gun = duke(h, p); var e = body(h, p, 1); shot(h, p, e, false);
        check(h, e.isDeadOrDying() && e.getHealth() == 0 && ammo(gun).rounds() == 8,
                "Body geometry still produces a real paid source-weapon final blow");
        check(h, WeaponOutlaw.remaining(p) == 0 && WeaponRuntime.reload(p), "Body kill grants no Outlaw");
        check(h, WeaponOutlaw.plan(p, entry(gun), profile(gun)).firstTicks() == profile(gun).firstReloadTicks(),
                "Reload after body kill uses the base plan"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void actualNonlethalHeadshotDealsPrecisionDamageButDoesNotActivate(GameTestHelper h) {
        var p = player(h, 3.5); var gun = duke(h, p);
        var control = player(h, 9.5); duke(h, control);
        var crit = head(h, p, 1000); var plain = body(h, control, 1000);
        shot(h, p, crit, true); shot(h, control, plain, false);
        float precisionLoss = 1000 - crit.getHealth(), bodyLoss = 1000 - plain.getHealth();
        check(h, crit.isAlive() && plain.isAlive() && bodyLoss > 0
                && near(precisionLoss, (float)(bodyLoss * WeaponBallistics.of(entry(gun)).precision()))
                && precisionLoss > bodyLoss,
                "Observed actual HP loss proves upper-quarter precision versus body geometry: " + precisionLoss + "/" + bodyLoss);
        check(h, WeaponOutlaw.remaining(p) == 0 && WeaponOutlaw.remaining(control) == 0,
                "A real critical hit without a final blow cannot arm either owner's Outlaw"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void actualAbilityFinalBlowCannotCreditTheHeldOutlawGun(GameTestHelper h) {
        var p = player(h, 6.5); var gun = duke(h, p); var e = head(h, p, 1);
        check(h, Combat.damage(p, e, 100, Element.SOLAR) && e.isDeadOrDying(), "Actual ability-attributed kill"); e.discard();
        check(h, WeaponOutlaw.remaining(p) == 0 && ammo(gun).rounds() == 9,
                "Held trait and head-height victim cannot turn ability damage into precision weapon credit");
        var tank = head(h, p, 1000); shot(h, p, tank, true);
        check(h, tank.isAlive() && tank.getHealth() < 1000 && WeaponOutlaw.remaining(p) == 0,
                "Later nonlethal weapon precision cannot borrow an ability's final blow"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void defaultUnselectedTraitStaysInertAfterAnActualHeadshotKill(GameTestHelper h) {
        var p = player(h, 6.5); var gun = equip(h, p, "duke_mk_44", 9, 0, false);
        check(h, !WeaponPerks.available(gun, OUTLAW).isEmpty() && WeaponPerks.selected(gun, OUTLAW).isEmpty(),
                "Official availability never means default selection");
        precisionKill(h, p);
        check(h, WeaponOutlaw.remaining(p) == 0 && WeaponRuntime.reload(p), "Real unselected precision kill does not activate");
        check(h, WeaponOutlaw.plan(p, entry(gun), profile(gun)).firstTicks() == 59,
                "Unselected Duke retains its actual 59-tick reload"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void actualNormalReloadFinishesAtBoostedDeadlineWhilePrimaryReserveRemainsInfinite(GameTestHelper h) {
        var p = player(h, 3.5); var gun = duke(h, p); precisionKill(h, p);
        var control = player(h, 9.5); var plain = equip(h, control, "duke_mk_44", 9, 0, false); precisionKill(h, control);
        int boosted = fast(gun), base = profile(gun).firstReloadTicks();
        check(h, boosted == 33 && base == 59 && profile(gun).infiniteReserve(), "Pinned normal-reload comparison");
        check(h, WeaponRuntime.reload(p) && WeaponRuntime.reload(control) && ammo(gun).rounds() == 8,
                "Actual reload starts without giving its missing cartridge early");
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(control); });
        h.runAfterDelay(23, () -> check(h, ammo(gun).rounds() == 8 && ammo(plain).rounds() == 8, "Before captured boosted credit neither is refilled"));
        h.runAfterDelay(24, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 9 && WeaponRuntime.reloading(p) && ammo(plain).rounds() == 8, "Boosted credit at24 retains recovery through33"); });
        h.runAfterDelay(boosted - 1, () -> {
            WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(control);
            check(h, WeaponRuntime.reloading(p) && ammo(gun).rounds() == 9 && ammo(plain).rounds() == 8,
                    "Boosted ammo is already credited but neither recovery completes before33");
        });
        h.runAfterDelay(boosted, () -> {
            WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(control);
            check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == 9 && ammo(gun).reserve() == 0
                    && WeaponRuntime.reloading(control) && ammo(plain).rounds() == 8,
                    "At tick 33 only boosted primary really fills, without inventing finite reserves");
            check(h, WeaponOutlaw.remaining(p) == DURATION - boosted, "Reload neither consumes nor refreshes Outlaw time");
        });
        h.runAfterDelay(base - 1, () -> {
            WeaponRuntime.tickPlayer(control); check(h, ammo(plain).rounds() == 9 && WeaponRuntime.reloading(control), "Base ammo is credited at42 while recovery still owns tick58");
        });
        h.runAfterDelay(base, () -> {
            WeaponRuntime.tickPlayer(control);
            check(h, !WeaponRuntime.reloading(control) && ammo(plain).rounds() == 9 && ammo(plain).reserve() == 0,
                    "Base control actually completes at 59 ticks with the same infinite-primary cost"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void outlawAlonePreservesObservedDamageAndOriginalFiringCadence(GameTestHelper h) {
        var p = player(h, 3.5); var gun = duke(h, p); precisionKill(h, p);
        var control = player(h, 9.5); equip(h, control, "duke_mk_44", 9, 0, false); precisionKill(h, control);
        int cadence = (int)Math.ceil(profile(gun).cadenceTicks());
        h.runAfterDelay(cadence - 1, () -> { deniedShot(h, p); deniedShot(h, control); });
        h.runAfterDelay(cadence, () -> {
            var boosted = body(h, p, 1000); var plain = body(h, control, 1000); shot(h, p, boosted, false); shot(h, control, plain, false);
            float loss = 1000 - plain.getHealth();
            check(h, loss > 0 && near(1000 - boosted.getHealth(), loss) && WeaponOutlaw.remaining(p) == DURATION - cadence,
                    "Both real body shots deal identical HP damage while Outlaw remains active");
            deniedShot(h, p); deniedShot(h, control);
            check(h, ammo(gun).rounds() == 7 && WeaponKillClip.remaining(p) == 0,
                    "Outlaw neither creates damage time nor permits a second cartridge in the same tick"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 260, environment = "destiny-test:w90_isolated")
    public void expiryDuringActualReloadKeepsCapturedPlanButNextReloadUsesBaseDeadline(GameTestHelper h) {
        var p = player(h, 6.5); var gun = duke(h, p); precisionKill(h, p);
        int boosted = fast(gun), base = profile(gun).firstReloadTicks();
        h.onEachTick(() -> WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(119, () -> {
            check(h, WeaponOutlaw.remaining(p) == 1 && boosted > 1 && boosted < base && WeaponRuntime.reload(p),
                    "Actual reload captures boosted timing on the final active tick");
            h.runAfterDelay(1, () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, WeaponOutlaw.remaining(p) == 0 && WeaponRuntime.reloading(p) && ammo(gun).rounds() == 8,
                        "Window expires during an actual unfinished reload");
            });
            h.runAfterDelay(boosted - 1, () -> {
                WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 9 && WeaponRuntime.reloading(p), "Captured early credit survives expiry but recovery still waits for33");
            });
            h.runAfterDelay(boosted, () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == 9 && WeaponOutlaw.remaining(p) == 0,
                        "Actual reload finishes at captured tick 33 despite expired buff");
                var tank = body(h, p, 1000); shot(h, p, tank, false);
                check(h, tank.isAlive() && tank.getHealth() < 1000 && WeaponRuntime.reload(p),
                        "A fresh paid shot starts another actual reload after expiry");
                h.runAfterDelay(boosted, () -> {
                    WeaponRuntime.tickPlayer(p); check(h, WeaponRuntime.reloading(p) && ammo(gun).rounds() == 8,
                            "New reload cannot inherit the old fast deadline");
                });
                h.runAfterDelay(base - 1, () -> {
                    WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 9 && WeaponRuntime.reloading(p), "Base credit42 does not end recovery59 early");
                });
                h.runAfterDelay(base, () -> {
                    WeaponRuntime.tickPlayer(p);
                    check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == 9 && WeaponOutlaw.remaining(p) == 0,
                            "New actual reload uses the 59-tick base plan"); h.succeed();
                });
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void nativeSameTickStowAndReturnRetiresBuffAndCancelsItsReload(GameTestHelper h) {
        var p = player(h, 6.5); var gun = duke(h, p); precisionKill(h, p);
        int slot = p.getInventory().getSelectedSlot();
        check(h, WeaponRuntime.reload(p), "Boosted reload started before stow");
        p.getInventory().setItem(7, new ItemStack(Items.STONE)); select(p, 7); select(p, slot); WeaponRuntime.tickPlayer(p);
        check(h, p.getMainHandItem() == gun && WeaponOutlaw.remaining(p) == 0
                && !WeaponRuntime.reloading(p) && ammo(gun).rounds() == 8,
                "Validated away-and-back native packets retire the session within the same server tick");
        int wait = (int)Math.max(1, WeaponHandling.remaining(p)) + fast(gun) + 1;
        h.runAfterDelay(wait, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, ammo(gun).rounds() == 8 && WeaponOutlaw.remaining(p) == 0 && !WeaponRuntime.reloading(p),
                    "Cancelled boosted deadline cannot refill or resurrect the returned actual stack"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void identicalSerializedReplacementCannotInheritBuffOrMutateOriginalStack(GameTestHelper h) {
        var p = player(h, 6.5); var original = duke(h, p); precisionKill(h, p);
        var copy = original.copy(); check(h, copy != original && ItemStack.matches(copy, original), "Identical saved components, distinct actual stack");
        p.getInventory().setItem(p.getInventory().getSelectedSlot(), copy); WeaponRuntime.tickPlayer(p);
        check(h, WeaponOutlaw.remaining(p) == 0 && WeaponPerks.selected(copy, OUTLAW).isPresent(),
                "Copied official selection and ammo cannot inherit a source-bound proc");
        int wait = (int)Math.max(1, WeaponHandling.remaining(p));
        h.runAfterDelay(wait, () -> {
            check(h, WeaponRuntime.reload(p), "Replacement may really reload after its handling delay");
            h.runAfterDelay(fast(copy), () -> {
                WeaponRuntime.tickPlayer(p); check(h, ammo(copy).rounds() == 8 && WeaponRuntime.reloading(p),
                        "Replacement cannot inherit original's boosted deadline");
            });
            h.runAfterDelay(profile(copy).firstReloadTicks(), () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, ammo(copy).rounds() == 9 && ammo(original).rounds() == 8 && WeaponOutlaw.remaining(p) == 0,
                        "Only replacement receives the actual base reload transfer"); h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void ownerCleanupDeathAndSpectatorCannotRestoreOrEraseAnotherOwnersWindow(GameTestHelper h) {
        var p = player(h, 3.5); duke(h, p); precisionKill(h, p);
        var other = player(h, 9.5); duke(h, other); precisionKill(h, other);
        check(h, WeaponOutlaw.remaining(p) == 120 && WeaponOutlaw.remaining(other) == 120, "Two independent actual precision kills");
        WeaponRuntime.cleanup(p); WeaponRuntime.tickPlayer(p);
        check(h, WeaponOutlaw.remaining(p) == 0 && WeaponOutlaw.remaining(other) == 120,
                "Owner cleanup retires only its own session; polling cannot recreate its proc");
        other.setGameMode(GameType.SPECTATOR); WeaponRuntime.tickPlayer(other);
        other.setGameMode(GameType.SURVIVAL); WeaponRuntime.tickPlayer(other);
        check(h, WeaponOutlaw.remaining(other) == 0, "Leaving spectator never restores retired precision time");
        p.setHealth(0); WeaponRuntime.tickPlayer(p);
        check(h, WeaponOutlaw.remaining(p) == 0 && !WeaponRuntime.reload(p), "Dead owner cannot recover an old buff or start a reload"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void realTraitClearAndReselectCommandsRetireBuffWithoutResettingAmmoOrCadence(GameTestHelper h) throws Exception {
        var p = player(h, 6.5); var gun = duke(h, p); precisionKill(h, p);
        var dispatcher = h.getLevel().getServer().getCommands().getDispatcher(); var source = p.createCommandSourceStack();
        var saved = gun.copy();
        check(h, dispatcher.execute("destiny perk clear", source) == 1
                && dispatcher.execute("destiny perk select outlaw", source) == 1,
                "Actual non-OP trait edit commands clear and reselect the official choice");
        check(h, p.getMainHandItem() == gun && ItemStack.matches(saved, gun) && WeaponOutlaw.remaining(p) == 0,
                "Returning identical serialized selection cannot revive its previous session or mint ammo");
        deniedShot(h, p);
        check(h, WeaponRuntime.reload(p), "Real reload remains available after edits");
        h.runAfterDelay(fast(gun), () -> {
            WeaponRuntime.tickPlayer(p); check(h, WeaponRuntime.reloading(p) && ammo(gun).rounds() == 8,
                    "Edited trait does not inherit the old accelerated plan");
        });
        h.runAfterDelay(profile(gun).firstReloadTicks(), () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 9 && WeaponOutlaw.remaining(p) == 0,
                    "After edits actual reload completes at base time"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void precisionKillThenFasterReloadActivatesCoexistingKillClipWithActualQuarterMoreDamage(GameTestHelper h) {
        var p = player(h, 3.5); var gun = duke(h, p);
        check(h, WeaponPerks.select(gun, KillClipProfile.ID)
                && WeaponPerks.selected(gun, OUTLAW).orElseThrow().socket() == 2
                && WeaponPerks.selected(gun, KillClipProfile.ID).orElseThrow().socket() == 4,
                "Duke's distinct official Outlaw 2 and Kill Clip 4 sockets coexist");
        var reverse = WeaponItems.create(entry(gun));
        check(h, WeaponPerks.select(reverse, KillClipProfile.ID) && WeaponPerks.select(reverse, OUTLAW)
                && WeaponPerks.selected(reverse, KillClipProfile.ID).isPresent(), "Reverse edit order retains separate official choices");
        var control = player(h, 9.5); equip(h, control, "duke_mk_44", 9, 0, false);
        precisionKill(h, p);
        check(h, WeaponOutlaw.remaining(p) == 120 && WeaponKillClip.remaining(p) == 0 && WeaponRuntime.reload(p),
                "Same actual precision kill immediately starts Outlaw and only arms pending Kill Clip");
        h.onEachTick(() -> WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(23, () -> check(h, ammo(gun).rounds() == 8 && WeaponKillClip.remaining(p) == 0, "Before24 no cartridge or Kill Clip"));
        h.runAfterDelay(24, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 9 && WeaponKillClip.remaining(p) == 100 && WeaponRuntime.reloading(p), "Actual early transfer starts Kill Clip while recovery continues"); });
        h.runAfterDelay(fast(gun) - 1, () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 9 && WeaponKillClip.remaining(p) == 92 && WeaponRuntime.reloading(p),
                    "Kill Clip counts down from actual credit24, not full completion33");
        });
        h.runAfterDelay(fast(gun), () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, ammo(gun).rounds() == 9 && WeaponKillClip.remaining(p) == 91 && WeaponOutlaw.remaining(p) == 87,
                    "Full recovery33 retains already-active Kill Clip and original Outlaw");
            var boosted = body(h, p, 1000); var plain = body(h, control, 1000); shot(h, p, boosted, false); shot(h, control, plain, false);
            float base = 1000 - plain.getHealth();
            check(h, base > 0 && near(1000 - boosted.getHealth(), base * 1.25f)
                    && WeaponKillClip.capture(p).multiplier() == 1.25f && WeaponOutlaw.remaining(p) == 87,
                    "Observed actual body HP loss is exactly 1.25x with both separate official traits active"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 200, environment = "destiny-test:w90_isolated")
    public void actualFiniteSlugInsertsKeepCapturedBoostAcrossExpiryAndPayEveryReserveRound(GameTestHelper h) {
        var p = player(h, 6.5); var e = WeaponCatalog.find("first_in_last_out").orElseThrow();
        var f = WeaponProfile.forEntry(e); int initial = f.magazine() - 2;
        check(h, f.shellReload() && f.roundsPerInsert() == 1 && !f.infiniteReserve() && initial >= 2,
                "Actual Outlaw pool includes finite single-slug incremental reloads");
        var gun = equip(h, p, e.id(), initial, 2, true); long total = ammo(gun).total(); precisionKill(h, p);
        int loaded = initial - 1; var boost = OutlawProfile.reload(e);
        check(h, WeaponOutlaw.remaining(p) == 120 && ammo(gun).rounds() == loaded
                && ammo(gun).reserve() == 2 && ammo(gun).total() == total - 1
                && boost.firstTicks() == 9 && boost.intervalTicks() == 9 && boost.intervalTicks() < f.reloadTicks(),
                "Real precision slug costs one finite round and earns the pinned nine-tick reload");
        h.runAfterDelay(119, () -> {
            check(h, WeaponOutlaw.remaining(p) == 1 && WeaponRuntime.reload(p), "Last active tick captures both actual insert phases");
            h.runAfterDelay(boost.firstTicks() - 1, () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, WeaponOutlaw.remaining(p) == 0 && ammo(gun).rounds() == loaded && ammo(gun).reserve() == 2,
                        "Expired buff cannot move the first finite slug before captured deadline");
            });
            h.runAfterDelay(boost.firstTicks(), () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, WeaponRuntime.reloading(p) && ammo(gun).rounds() == loaded + 1
                        && ammo(gun).reserve() == 1 && ammo(gun).total() == total - 1,
                        "First captured nine-tick phase transfers exactly one paid slug, not a whole magazine");
                WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(p);
                check(h, ammo(gun).rounds() == loaded + 1 && ammo(gun).reserve() == 1, "Duplicate same-tick processing cannot duplicate an insert");
            });
            int second = boost.firstTicks() + boost.intervalTicks();
            h.runAfterDelay(second - 1, () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, ammo(gun).rounds() == loaded + 1 && ammo(gun).reserve() == 1,
                        "Repeat phase cannot insert its paid reserve slug a tick early");
            });
            h.runAfterDelay(second, () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == loaded + 2
                        && ammo(gun).reserve() == 0 && ammo(gun).total() == total - 1
                        && ammo(gun).rounds() < f.magazine() && WeaponOutlaw.remaining(p) == 0,
                        "Repeat phase retains captured nine ticks after expiry, then stops at finite reserve exhaustion");
                check(h, !WeaponRuntime.reload(p), "Missing magazine space is insufficient without real finite reserve");
            });
            h.runAfterDelay(second + f.reloadTicks() + 1, () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, ammo(gun).rounds() == loaded + 2 && ammo(gun).reserve() == 0 && ammo(gun).total() == total - 1,
                        "No later ghost insert, free finite ammunition, or deferred full-magazine transfer"); h.succeed();
            });
        });
    }
}
