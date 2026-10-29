package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;

import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** Paid production combat and real-clock reload/HUD integration, using W62/W66/W103 fixtures.
 * No positive killed-token injection, reflection, rewritten clocks/profiles, or native-input claims.
 * Whole-window refresh/expiry, reload non-consumption/snapshot and Dragonfly secondary credit
 * are explicit local integration contracts; the pinned source does not establish these policies.
 * Global WeaponRuntime/Tasks events own ticking. These embedded players are not added to the
 * server player list; no second driver advances projectiles or increments a gameplay clock.
 */
public final class FeedingFrenzyW108GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String ENV = "destiny-test:w90_isolated";
    private static final String FF = "feeding_frenzy";
    private static final String PRIMARY = "the_recluse";
    private static final int DURATION = 70;
    private static final int BASE = 43;
    private static final int CAPACITY = 41;
    private static final int[] FAST = {0, 40, 28, 25, 23, 22};
    private static final Set<String> IDS = Set.of("seventh_seraph_officer_revolver", "steelfeather_repeater",
            "cold_denial", "blast_furnace", "the_recluse", "brass_attacks", "hollow_words", "null_composure",
            "coriolis_force", "retraced_path", "fixed_odds", "hammerhead", "retrofit_escapade");
    private static final Set<WeaponPerks.Roll> EXACT_ROLLS = Set.of(
            roll("seventh_seraph_officer_revolver", 3037520408L, 4, 3527094473L),
            roll("steelfeather_repeater", 1251729046L, 3, 473189353L),
            roll("cold_denial", 1216130969L, 3, 330841869L),
            roll("blast_furnace", 3843477312L, 3, 1976101165L),
            roll("the_recluse", 3354242550L, 3, 242L),
            roll("brass_attacks", 2121785039L, 3, 100135553L),
            roll("hollow_words", 607191995L, 3, 637298592L),
            roll("null_composure", 1644680957L, 3, 272L),
            roll("coriolis_force", 3512349612L, 3, 2568674372L),
            roll("retraced_path", 548958835L, 3, 2945646047L),
            roll("fixed_odds", 2194955522L, 3, 4227334000L),
            roll("hammerhead", 603242241L, 3, 2515290473L),
            roll("retrofit_escapade", 3103325054L, 3, 3756086698L));

    private static WeaponPerks.Roll roll(String id, long hash, int socket, long pool) {
        return new WeaponPerks.Roll(id, hash, socket, 2779035018L, pool);
    }

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static WeaponCatalog.Entry entry(ItemStack gun) { return WeaponItems.entry(gun).orElseThrow(); }
    private static WeaponProfile profile(ItemStack gun) { return WeaponProfile.forEntry(entry(gun)); }
    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun, profile(gun)); }
    private static int slot(ItemStack gun) { return WeaponCharacteristics.of(entry(gun)).slot().hotbar(); }
    private static void state(GameTestHelper h, ServerPlayer p, int count, int left) {
        check(h, WeaponFeedingFrenzy.stacks(p) == count && WeaponFeedingFrenzy.remaining(p) == left,
                "Actual Feeding Frenzy x" + count + " with " + left + " ticks, got x"
                        + WeaponFeedingFrenzy.stacks(p) + "/" + WeaponFeedingFrenzy.remaining(p));
    }
    private static void plan(GameTestHelper h, ServerPlayer p, ItemStack gun, int ticks) {
        var actual = WeaponFeedingFrenzy.plan(p, entry(gun), profile(gun));
        check(h, actual.firstTicks() == ticks && actual.intervalTicks() == ticks && !actual.incremental(),
                "Independent whole-magazine expected plan " + ticks + ", got " + actual);
    }

    private static final class Fixture {
        final GameTestHelper h;
        final List<ServerPlayer> players = new ArrayList<>();
        final List<Husk> targets = new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h = h;
            TestCleanup.register(h, () -> {
                for (var target : targets) target.discard();
                for (var p : players) {
                    p.stopUsingItem(); WeaponRuntime.cleanup(p); WeaponFeedingFrenzy.cleanup(p);
                    WeaponAiming.cleanup(p); CombatHud.remove(p); TestPlayers.remove(p);
                }
            });
            h.onEachTick(() -> { for (var p : players) TestPlayers.drain(p); });
        }
        ServerPlayer player(double z) {
            var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0,
                    "W108_" + UUID.randomUUID().toString().substring(0, 8));
            p.setAttached(WeaponLoadout.ENABLED, true); p.setNoGravity(true); p.setOnGround(true);
            players.add(p); bounded(p); return p;
        }
        void bounded(net.minecraft.world.entity.Entity entity) {
            var o = h.absoluteVec(Vec3.ZERO); var b = entity.getBoundingBox();
            check(h, b.minX > o.x && b.maxX < o.x + 16 && b.minY > o.y && b.maxY < o.y + 8
                            && b.minZ > o.z && b.maxZ < o.z + 12,
                    "Whole entity AABB inside existing committed 16x8x12 floor");
        }
        ItemStack item(String id, boolean selected, int rounds, int reserve) {
            var e = WeaponCatalog.find(id).orElseThrow(); var gun = WeaponItems.create(e);
            check(h, WeaponPerks.selected(gun, FF).isEmpty(), "Fresh stack never auto-selects Feeding Frenzy");
            if (selected) check(h, WeaponPerks.select(gun, FF), "Select exact official source socket: " + id);
            WeaponItems.save(gun, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve)); return gun;
        }
        ItemStack equip(ServerPlayer p, String id, boolean selected, int rounds, int reserve) {
            var gun = item(id, selected, rounds, reserve);
            p.getInventory().setItem(slot(gun), gun); p.getInventory().setSelectedSlot(slot(gun));
            WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); return gun;
        }
        ItemStack recluse(ServerPlayer p) { return equip(p, PRIMARY, true, CAPACITY, 0); }
        Husk target(double x, double y, double z, float hp) {
            var t = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z)); targets.add(t);
            t.setNoAi(true); t.setNoGravity(true); t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); t.setHealth(hp);
            bounded(t); return t;
        }
        Husk target(ServerPlayer p, boolean head, float hp) {
            var t = target(8.5, head ? 1 : 1.8, p.getZ() - h.absoluteVec(Vec3.ZERO).z, hp);
            var b = t.getBoundingBox(); double eye = p.getEyeY();
            check(h, head ? eye >= b.maxY - b.getYsize() * .25 && eye < b.maxY
                            : eye > b.minY && eye < b.maxY - b.getYsize() * .25,
                    "Horizontal paid ray crosses real " + (head ? "precision quarter" : "body geometry"));
            return t;
        }
        void aim(ServerPlayer p) {
            WeaponAiming.cleanup(p); p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
        }
        void fire(ServerPlayer p) {
            aim(p); var gun = p.getMainHandItem(); var before = ammo(gun);
            check(h, profile(gun).chargeTicks() == 0 && WeaponRuntime.beginUse(p), "Real immediate trigger accepted");
            WeaponRuntime.releaseUse(p, gun);
            check(h, ammo(gun).rounds() == before.rounds() - 1 && ammo(gun).reserve() == before.reserve()
                            && ammo(gun).overflow() == before.overflow(),
                    "First actual emission pays one cartridge without reserve/overflow reward");
        }
        void kill(ServerPlayer p, boolean head) {
            var victim = target(p, head, 1); fire(p);
            check(h, victim.isDeadOrDying() && victim.getHealth() == 0, "Paid production final blow, no injected kill credit");
            victim.discard();
        }
        void chain(ServerPlayer p, int count, Runnable done) { chain(p, 1, count, done); }
        private void chain(ServerPlayer p, int next, int count, Runnable done) {
            kill(p, next % 2 == 0); state(h, p, next, DURATION);
            plan(h, p, p.getMainHandItem(), FAST[next]);
            if (next == count) done.run();
            else h.runAfterDelay(2, () -> chain(p, next + 1, count, done));
        }
    }

    private static ItemDisplayHud node(ServerPlayer p, String suffix) {
        var n = DisplayHud.getHud(p, WeaponPerkHud.PREFIX + "feeding_frenzy_" + suffix);
        return n instanceof ItemDisplayHud item ? item : null;
    }
    private static long nodes(ServerPlayer p) {
        return DisplayHud.getHuds(p).keySet().stream().filter(k -> k.startsWith(WeaponPerkHud.PREFIX + "feeding_frenzy_")).count();
    }
    private static void model(GameTestHelper h, ServerPlayer p, String suffix, String path) {
        var n = node(p, suffix);
        check(h, n != null && Identifier.parse("destiny:gui/hud/" + path).equals(n.getItem().get(DataComponents.ITEM_MODEL)),
                "Actual server HUD model " + suffix + " = " + path);
    }
    private static void hud(GameTestHelper h, ServerPlayer p, int stacks, int seconds) {
        CombatHud.update(p);
        check(h, nodes(p) == (stacks == 0 ? 0 : 8), "Exactly eight graph nodes per live Feeding Frenzy row");
        if (stacks == 0) return;
        model(h, p, "marker", "perk_buff_w61");
        model(h, p, "label", "perk_feeding_frenzy_w108");
        model(h, p, "x", "perk_stack_x_w83"); model(h, p, "count", "ammo_digit_" + stacks);
        model(h, p, "minutes", "ammo_digit_0"); model(h, p, "colon", "perk_colon_w61");
        model(h, p, "tens", "ammo_digit_" + seconds / 10); model(h, p, "ones", "ammo_digit_" + seconds % 10);
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = ENV)
    public void exactThirteenSourceSocketsNeverAutoSelectOrExpandToAnotherWeapon(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(6);
        check(h, FeedingFrenzyProfile.ID.equals(FF) && FeedingFrenzyProfile.HASH == 2779035018L
                        && FeedingFrenzyProfile.durationTicks() == DURATION && FeedingFrenzyProfile.rolls().size() == 13,
                "Independent pinned base identity, 3.5 seconds and thirteen exact source sockets");
        check(h, Set.copyOf(FeedingFrenzyProfile.rolls()).equals(EXACT_ROLLS), "Independent exact item/socket/base-perk/plug-set identities for all thirteen rows");
        int selected = 0;
        for (var e : WeaponCatalog.all()) {
            var gun = WeaponItems.create(e); var saved = gun.copy();
            check(h, WeaponPerks.selected(gun, FF).isEmpty() && ItemStack.matches(saved, gun), "Fresh official entry has no default trait: " + e.id());
            long total = ammo(gun).total(); boolean expected = IDS.contains(e.id());
            check(h, WeaponPerks.select(gun, FF) == expected && WeaponPerks.selected(gun, FF).isPresent() == expected
                            && ammo(gun).total() == total, "Exact optional pool membership without free ammo: " + e.id());
            if (expected) {
                selected++;
                check(h, EXACT_ROLLS.contains(WeaponPerks.selected(gun, FF).orElseThrow()), "Selection serializes the exact official socket/hash tuple");
                check(h, profile(gun).mode() != WeaponProfile.Mode.PROJECTILE && !profile(gun).shellReload(),
                        "This exact source pool has no supported projectile or incremental reload");
            }
        }
        check(h, selected == 13, "No enhanced hash, newer copy, family-wide or exotic expansion");
        var gun = f.recluse(p); var roll = WeaponPerks.selected(gun, FF).orElseThrow();
        check(h, roll.hash() == 3354242550L && roll.socket() == 3 && roll.plugSetHash() == 242L && roll.perkHash() == 2779035018L,
                "The Recluse exact fixed curated option is explicitly selected, never automatically equipped");
        for (int i = 1; i <= 5; i++) {
            var reload = FeedingFrenzyProfile.reload(entry(gun), i);
            check(h, reload.firstTicks() == FAST[i] && reload.intervalTicks() == FAST[i], "Independent Recluse x" + i + " timing oracle");
        }
        state(h, p, 0, 0); plan(h, p, gun, BASE); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 175, environment = ENV)
    public void paidBodyAndHeadKillsReachFiveThenLocalWholeWindowRefreshAndExpiry(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(6); var gun = f.recluse(p);
        f.chain(p, 5, () -> {
            check(h, ammo(gun).rounds() == 36, "Five actual final blows spend five cartridges without reloading");
            h.runAfterDelay(69, () -> {
                state(h, p, 5, 1); f.kill(p, true); state(h, p, 5, DURATION);
                check(h, ammo(gun).rounds() == 35, "Sixth real kill refreshes local cap without a sixth stack or free cartridge");
                h.runAfterDelay(1, () -> state(h, p, 5, 69));
                h.runAfterDelay(69, () -> state(h, p, 5, 1));
                h.runAfterDelay(70, () -> {
                    state(h, p, 0, 0); plan(h, p, gun, BASE);
                    check(h, ammo(gun).rounds() == 35, "Local whole-window expiry never reloads the weapon");
                    f.kill(p, false); state(h, p, 1, DURATION); h.succeed();
                });
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = ENV)
    public void nonlethalAbilityUnselectedAndEmptyInputsCannotBorrowHeldTraitCredit(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(3); var gun = f.recluse(p);
        var tank = f.target(p, true, 1000); f.fire(p);
        check(h, tank.isAlive() && tank.getHealth() < 1000 && ammo(gun).rounds() == 40, "Real paid nonlethal precision damage");
        state(h, p, 0, 0); tank.discard();
        var victim = f.target(p, false, 1);
        check(h, Combat.damage(p, victim, 100, Element.SOLAR) && victim.isDeadOrDying(), "Actual ability-attributed final blow with selected gun held");
        state(h, p, 0, 0); check(h, ammo(gun).rounds() == 40, "Ability kill neither pays nor rewards weapon cartridges"); victim.discard();
        var plain = f.player(6); f.equip(plain, PRIMARY, false, CAPACITY, 0); f.kill(plain, true); state(h, plain, 0, 0);
        var empty = f.player(9); var dry = f.equip(empty, "retraced_path", true, 0, 0);
        var witness = f.target(empty, false, 1); var saved = dry.copy();
        check(h, !WeaponRuntime.beginUse(empty) && witness.isAlive() && ItemStack.matches(saved, dry), "Denied finite empty trigger has no emission or damage");
        state(h, empty, 0, 0); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = ENV)
    public void actualFiveStackReloadCompletesAtTwentyTwoWhileUnselectedControlWaitsFortyThree(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(3); var gun = f.recluse(p);
        var control = f.player(9); var plain = f.equip(control, PRIMARY, false, CAPACITY, 0); f.kill(control, false);
        f.chain(p, 5, () -> {
            check(h, profile(gun).magazine() == CAPACITY && profile(gun).firstReloadTicks() == BASE
                            && ReloadCreditProfile.find(entry(gun)).isEmpty(), "Pinned 41-round/43-tick whole magazine has no independent early credit");
            check(h, WeaponRuntime.reload(p) && WeaponRuntime.reload(control), "Both actual reloads start on the same server tick");
            h.runAfterDelay(21, () -> {
                WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(control);
                check(h, ammo(gun).rounds() == 36 && ammo(plain).rounds() == 40 && WeaponRuntime.reloading(p), "No pre-deadline ammunition at T+21");
            });
            h.runAfterDelay(22, () -> {
                WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(control);
                check(h, ammo(gun).rounds() == CAPACITY && ammo(gun).reserve() == 0 && !WeaponRuntime.reloading(p)
                                && ammo(plain).rounds() == 40 && WeaponRuntime.reloading(control), "Actual selected x5 completes exactly at22, control remains pending");
                state(h, p, 5, 48); // Explicit local reload-non-consumption policy.
            });
            h.runAfterDelay(42, () -> { WeaponRuntime.tickPlayer(control); check(h, ammo(plain).rounds() == 40 && WeaponRuntime.reloading(control), "Base deadline is not42"); });
            h.runAfterDelay(43, () -> {
                WeaponRuntime.tickPlayer(control);
                check(h, ammo(plain).rounds() == CAPACITY && ammo(plain).reserve() == 0 && !WeaponRuntime.reloading(control), "Same primary actually completes base43 with infinite reserve semantics"); h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = ENV)
    public void localReloadStartSnapshotSurvivesExpiryButNextActualReloadUsesBase(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(6); var gun = f.recluse(p); f.kill(p, false);
        h.runAfterDelay(69, () -> {
            state(h, p, 1, 1); plan(h, p, gun, 40);
            check(h, WeaponRuntime.reload(p), "Actual reload captures x1 forty ticks on the final active tick");
            h.runAfterDelay(1, () -> { state(h, p, 0, 0); check(h, WeaponRuntime.reloading(p) && ammo(gun).rounds() == 40, "Expiry cannot finish or stretch an in-flight snapshot"); });
            h.runAfterDelay(39, () -> { WeaponRuntime.tickPlayer(p); check(h, WeaponRuntime.reloading(p) && ammo(gun).rounds() == 40, "Captured deadline has no early ammo at39"); });
            h.runAfterDelay(40, () -> {
                WeaponRuntime.tickPlayer(p); state(h, p, 0, 0);
                check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == CAPACITY, "Snapshot completes at40 despite lifetime expiry");
                var tank = f.target(p, false, 1000); f.fire(p);
                check(h, tank.isAlive() && tank.getHealth() < 1000 && WeaponRuntime.reload(p), "New paid nonlethal shot starts a new actual reload");
                plan(h, p, gun, BASE);
                h.runAfterDelay(40, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 40 && WeaponRuntime.reloading(p), "New reload cannot inherit expired forty-tick plan"); });
                h.runAfterDelay(43, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == CAPACITY && !WeaponRuntime.reloading(p), "New actual reload completes at base43"); h.succeed(); });
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = ENV)
    public void naturalLastPaidRoundsReachZeroBeforeInfiniteAndFiniteActualAmmoTransfers(GameTestHelper h) {
        var f = new Fixture(h); var primary = f.player(3); var special = f.player(6); var dry = f.player(9);
        var a = f.equip(primary, PRIMARY, true, 1, 0);
        var b = f.equip(special, "retraced_path", true, 1, 2);
        var c = f.equip(dry, "retraced_path", true, 1, 0);
        f.kill(primary, false); f.kill(special, false); f.kill(dry, false);
        for (var p : List.of(primary, special, dry)) state(h, p, 1, DURATION);
        check(h, ammo(a).rounds() == 0 && ammo(b).rounds() == 0 && ammo(b).reserve() == 2 && ammo(c).total() == 0,
                "Natural 1->0 funded final blows never grant ammunition at activation");
        // Consume the production pending-empty flag on the real emission tick; no synthetic reload request.
        WeaponRuntime.tickPlayer(primary); WeaponRuntime.tickPlayer(special); WeaponRuntime.tickPlayer(dry);
        check(h, WeaponRuntime.reloading(primary) && WeaponRuntime.reloading(special) && !WeaponRuntime.reloading(dry), "Only genuine supply admits automatic empty-mag reload");
        h.runAfterDelay(38, () -> check(h, ammo(a).rounds() == 0 && ammo(b).rounds() == 0 && ammo(b).reserve() == 2, "No primary or finite trace transfer before captured39/40"));
        h.runAfterDelay(39, () -> {
            WeaponRuntime.tickPlayer(special);
            check(h, ammo(b).rounds() == 2 && ammo(b).reserve() == 0 && ammo(b).total() == 2 && !WeaponRuntime.reloading(special), "Trace x1 actual39 transfers only two real reserves");
            check(h, ammo(a).rounds() == 0 && WeaponRuntime.reloading(primary), "Primary x1 still waits for40");
        });
        h.runAfterDelay(40, () -> {
            WeaponRuntime.tickPlayer(primary); WeaponRuntime.tickPlayer(dry);
            check(h, ammo(a).rounds() == CAPACITY && ammo(a).reserve() == 0 && !WeaponRuntime.reloading(primary), "Infinite primary fills only at actual40");
            check(h, ammo(c).total() == 0 && !WeaponRuntime.reloading(dry), "Zero-supply finite source stays dry, no reward/retry mint");
            check(h, WeaponKillClip.remaining(primary) == 0 && WeaponKillClip.remaining(special) == 0, "Feeding Frenzy does not invent an unselected damage perk"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = ENV)
    public void identicalReplacementAndDifferentSelectedSourceRejectOldCapturedTokens(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(3); var gun = f.recluse(p); f.kill(p, false);
        var stale = WeaponFeedingFrenzy.capture(p); var saved = gun.copy(); var replacement = gun.copy();
        check(h, replacement != gun && ItemStack.matches(replacement, gun), "Equal serialized components are distinct actual source identities");
        p.getInventory().setItem(slot(gun), replacement); WeaponRuntime.tickPlayer(p);
        state(h, p, 0, 0); WeaponFeedingFrenzy.killed(p, stale); state(h, p, 0, 0);
        check(h, ItemStack.matches(gun, saved), "Rejected old-token path cannot mutate removed original");
        var other = f.player(9); var original = f.recluse(other); f.kill(other, true);
        var old = WeaponFeedingFrenzy.capture(other);
        var next = f.item("retraced_path", true, 3, 2);
        other.getInventory().setItem(slot(original), next); WeaponRuntime.tickPlayer(other);
        WeaponFeedingFrenzy.killed(other, old); state(h, other, 0, 0);
        int wait = (int)Math.ceil(Math.max(WeaponHandling.remaining(p), WeaponHandling.remaining(other))) + 2;
        h.runAfterDelay(wait, () -> {
            f.kill(p, false); f.kill(other, false); state(h, p, 1, DURATION); state(h, other, 1, DURATION);
            check(h, ammo(replacement).rounds() == 39 && ammo(next).rounds() == 2 && ammo(next).reserve() == 2,
                    "Only new real paid final blows arm replacement/different source, no redirected ammo");
            var retired = WeaponFeedingFrenzy.capture(p); WeaponFeedingFrenzy.changed(p, replacement);
            WeaponFeedingFrenzy.killed(p, retired); state(h, p, 0, 0); state(h, other, 1, DURATION);
            var cleaned = WeaponFeedingFrenzy.capture(other); WeaponFeedingFrenzy.cleanup(other);
            WeaponFeedingFrenzy.killed(other, cleaned); state(h, other, 0, 0); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = ENV)
    public void actualSelectedChargedFusionFinalBlowCreditsOnceAfterPaidEmission(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(6); var gun = f.equip(p, "null_composure", true, 2, 0);
        var victim = f.target(p, false, 1); var base = profile(gun);
        check(h, base.mode() == WeaponProfile.Mode.HITSCAN && base.chargeTicks() == 11
                        && base.burst() == 9 && base.sharedBurstAmmo(), "Exact selected Null Composure uses eleven-tick charge and nine paid shared-ammo bolts, not projectile mode");
        f.aim(p); check(h, WeaponRuntime.heartbeatUse(p), "Actual two-handed charge input accepted");
        check(h, victim.isAlive() && ammo(gun).rounds() == 2, "Charge acceptance has no kill or cartridge debit"); state(h, p, 0, 0);
        for (int tick = 1; tick <= 10; tick++) {
            int elapsed = tick;
            h.runAfterDelay(tick, () -> {
                if (elapsed % 4 == 0) check(h, WeaponRuntime.heartbeatUse(p), "Renew real charge lease before expiry");
                WeaponRuntime.tickPlayer(p);
                check(h, victim.isAlive() && ammo(gun).rounds() == 2, "No early charged final blow at T+" + elapsed);
            });
        }
        h.runAfterDelay(12, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, victim.isDeadOrDying() && victim.getHealth() == 0 && ammo(gun).rounds() == 1, "Actual charged emission killed and paid exactly one shared unit");
            check(h, WeaponFeedingFrenzy.stacks(p) == 1 && WeaponFeedingFrenzy.remaining(p) > 0, "Observed ranged final blow arms selected source once");
            WeaponRuntime.releaseUse(p, gun);
        });
        h.runAfterDelay(24, () -> {
            check(h, WeaponFeedingFrenzy.stacks(p) == 1 && ammo(gun).rounds() == 1 && ammo(gun).reserve() == 0
                            && WeaponRuntime.activeProjectiles(p) == 0, "Remaining real bolts cannot re-credit one corpse, refund cartridge or invent projectile coverage"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = ENV)
    public void actualHudLabelCountAndTimerUsePureQueriesAndDisappearAtLocalExpiry(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(6); var gun = f.recluse(p); hud(h, p, 0, 0);
        f.kill(p, false); hud(h, p, 1, 4); state(h, p, 1, DURATION);
        var label = node(p, "label"); var nativeItem = label.getItemDisplay().getItemStack(); int entityId = label.getEntityId();
        var saved = gun.copy();
        for (int i = 0; i < 30; i++) { state(h, p, 1, DURATION); plan(h, p, gun, 40); hud(h, p, 1, 4); }
        check(h, ItemStack.matches(saved, gun) && label.getItemDisplay().getItemStack() == nativeItem
                        && label.getEntityId() == entityId && !WeaponRuntime.reloading(p), "Repeated plan/gameplay/HUD reads preserve ammo, deadline and cached native display item");
        h.runAfterDelay(2, () -> {
            f.kill(p, true); state(h, p, 2, DURATION); hud(h, p, 2, 4);
            check(h, node(p, "label") == label && label.getEntityId() == entityId, "Stack count changes without respawning the label graph");
            h.runAfterDelay(10, () -> { state(h, p, 2, 60); hud(h, p, 2, 3); });
            h.runAfterDelay(69, () -> { state(h, p, 2, 1); hud(h, p, 2, 1); });
            h.runAfterDelay(70, () -> { state(h, p, 0, 0); hud(h, p, 0, 0); check(h, ammo(gun).rounds() == 39, "HUD expiry never transfers ammo"); h.succeed(); });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 35, environment = ENV)
    public void actualSameSocketReplacementAndClearReselectRetireCreditAndHudImmediately(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(3); var gun = f.recluse(p); f.kill(p, false); hud(h, p, 1, 4);
        var stale = WeaponFeedingFrenzy.capture(p); var before = ammo(gun);
        check(h, WeaponPerks.select(gun, FF), "Selecting already-selected trait is a no-op"); state(h, p, 1, DURATION);
        check(h, WeaponPerks.clear(gun) && WeaponPerks.select(gun, FF), "Real same-tick clear/reselect, with no intervening update");
        WeaponFeedingFrenzy.killed(p, stale); state(h, p, 0, 0); hud(h, p, 0, 0);
        check(h, ammo(gun).rounds() == before.rounds() && ammo(gun).reserve() == before.reserve(), "Real edits revoke old token and graph without changing ammo");
        var other = f.player(9); var blast = f.equip(other, "blast_furnace", true, 27, 0); f.kill(other, false);
        var ff = WeaponPerks.selected(blast, FF).orElseThrow(); var old = WeaponFeedingFrenzy.capture(other);
        check(h, ff.socket() == 3 && WeaponPerks.available(blast, OutlawProfile.ID).getFirst().socket() == 3,
                "Only proven Outlaw overlap is the same exact Blast Furnace socket3");
        check(h, WeaponPerks.select(blast, OutlawProfile.ID) && WeaponPerks.selected(blast, FF).isEmpty(), "Successful same-socket selection replaces Feeding Frenzy");
        WeaponFeedingFrenzy.killed(other, old); state(h, other, 0, 0); hud(h, other, 0, 0);
        check(h, WeaponPerks.select(blast, FF) && WeaponPerks.selected(blast, OutlawProfile.ID).isEmpty(), "Reverse real edit restores selection without the retired proc");
        state(h, other, 0, 0); WeaponFeedingFrenzy.cleanup(other); state(h, other, 0, 0); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = ENV)
    public void localDragonflySecondaryFinalBlowCreditsBrassSourceTwiceButBodyOnlyOnce(GameTestHelper h) {
        var f = new Fixture(h); var precise = f.player(3); var body = f.player(9);
        var a = f.equip(precise, "brass_attacks", true, 24, 0); var b = f.equip(body, "brass_attacks", true, 24, 0);
        for (var gun : List.of(a, b)) {
            check(h, WeaponPerks.select(gun, DragonflyProfile.ID), "Actual independent Brass Attacks Dragonfly socket selected");
            check(h, WeaponPerks.selected(gun, FF).orElseThrow().socket() == 3
                            && WeaponPerks.selected(gun, DragonflyProfile.ID).orElseThrow().socket() == 4,
                    "Exact source-backed independent sockets3/4 coexist");
        }
        var primary = f.target(precise, true, 1); var splash = f.target(8.5, 1, 4.5, 1);
        var safe = f.target(13.1, 1, 3, 1); // 4.6 blocks from the corpse center, beyond 4.5 radius.
        var nonrecursive = f.target(8.5, 1, 6, 1000);
        var bodyVictim = f.target(body, false, 1); var bodyWitness = f.target(8.5, 1.8, 10.5, 1);
        f.fire(precise); f.fire(body);
        check(h, primary.isDeadOrDying() && splash.isDeadOrDying() && bodyVictim.isDeadOrDying()
                        && bodyWitness.isAlive() && safe.isAlive(), "Actual precision primary plus lethal off-axis blast; body final blow and outside-radius witnesses do not explode");
        check(h, Math.abs(nonrecursive.getHealth() - (1000 - 10f / 3)) < .003f,
                "Local 10HP falloff at distance3 is applied once; lethal secondary neither recursively explodes nor gains a Feeding Frenzy damage multiplier");
        state(h, precise, 2, DURATION); state(h, body, 1, DURATION);
        // No .killed positive injection: all earned credit above came from production damage.
        var old = WeaponFeedingFrenzy.capture(precise);
        var next = f.item(PRIMARY, true, CAPACITY, 0);
        precise.getInventory().setItem(slot(a), next); WeaponRuntime.tickPlayer(precise);
        WeaponFeedingFrenzy.killed(precise, old); state(h, precise, 0, 0);
        check(h, ammo(next).rounds() == CAPACITY && WeaponPerks.selected(next, DragonflyProfile.ID).isEmpty(), "Old Brass token cannot credit or spend on another selected weapon");
        h.runAfterDelay(8, () -> {
            check(h, WeaponFeedingFrenzy.stacks(body) == 1 && bodyWitness.isAlive() && safe.isAlive(), "Queued body burst cannot turn its corpse into secondary credit");
            check(h, ammo(b).rounds() == 22 && ammo(b).reserve() == 0, "Both real non-shared burst rounds are funded; no blast refunds"); h.succeed();
        });
    }
}
