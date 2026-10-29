package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.core.BlockPos;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import net.minecraft.world.phys.Vec3;

/** W67 server/EmbeddedChannel tests. Progress is earned only by paid production damage.
 * The frozen pool has no projectile or burst weapon; those branches are not claimed here.
 * All drivers are installed during initial setup and all mobs fit wholly inside the existing floor.
 */
public final class WeaponPrecisionReturnW67GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String TT = "triple_tap", FTTC = "fourth_times_the_charm";
    private static final String SCOUT = "distant_relation", DUAL = "aishas_embrace";
    private static final String HC = "seventh_seraph_officer_revolver", MG = "retrofit_escapade";
    private static final String SNIPER = "beloved", DUKE = "duke_mk_44";
    private static final float HEALTH = 1000;
    // Independent literal socket/item/plug-set oracle, not profile-versus-profile comparison.
    private static final Set<WeaponPerks.Roll> TT_ROWS = Set.of(
            new WeaponPerks.Roll(DUAL, 2638190703L, 3, 3400784728L, 7997267L),
            new WeaponPerks.Roll("ammit_ar2", 2119346509L, 3, 3400784728L, 1723759242L),
            new WeaponPerks.Roll("austringer", 3055790362L, 3, 3400784728L, 2750499928L),
            new WeaponPerks.Roll(SCOUT, 2034817450L, 3, 3400784728L, 1131958073L),
            new WeaponPerks.Roll(DUKE, 2112909414L, 2, 3400784728L, 3744182842L));
    private static final Set<WeaponPerks.Roll> FTTC_ROWS = Set.of(
            new WeaponPerks.Roll(DUAL, 2638190703L, 4, 1354429876L, 4211351701L),
            new WeaponPerks.Roll(SNIPER, 3107853529L, 3, 1354429876L, 1196545279L),
            new WeaponPerks.Roll(MG, 3103325054L, 3, 1354429876L, 3756086698L),
            new WeaponPerks.Roll(HC, 3037520408L, 3, 1354429876L, 903350103L));

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static WeaponCatalog.Entry entry(ItemStack s) { return WeaponItems.entry(s).orElseThrow(); }
    private static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(entry(s)); }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, profile(s)); }
    private static int cadence(ItemStack s) { return (int)Math.ceil(profile(s).cadenceTicks()); }
    private static int slot(ItemStack s) { return WeaponCharacteristics.of(entry(s)).slot().hotbar(); }
    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true); p.setOnGround(true);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); CombatHud.remove(p);
            p.setServerLevel(h.getLevel()); TestPlayers.remove(p); });
        return p;
    }
    private static ItemStack item(String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow(); var s = WeaponItems.create(e);
        WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve)); return s;
    }
    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, String perk, int rounds, int reserve) {
        var s = item(id, rounds, reserve);
        if (perk != null) check(h, WeaponPerks.select(s, perk), "Official selection: " + id + "/" + perk);
        p.getInventory().setItem(slot(s), s); p.getInventory().setSelectedSlot(slot(s));
        WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); return s;
    }
    private static void drive(GameTestHelper h, ServerPlayer... players) {
        h.onEachTick(() -> { for (var p : players) { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); } });
    }
    private static void select(ServerPlayer p, int slot) {
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot)); WeaponRuntime.tickPlayer(p);
    }
    private static void reaim(ServerPlayer p) {
        WeaponAiming.cleanup(p); p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
    }
    private static Husk target(GameTestHelper h, ServerPlayer p, boolean precision, float health) {
        double z = p.getZ() - h.absoluteVec(Vec3.ZERO).z;
        var e = h.spawn(EntityTypes.HUSK, new Vec3(8.5, precision ? 1 : 1.8, z));
        e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HEALTH);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); e.setHealth(health);
        TestCleanup.register(h, e::discard);
        var o = h.absoluteVec(Vec3.ZERO); var b = e.getBoundingBox();
        check(h, b.minX > o.x && b.maxX < o.x + 16 && b.minY > o.y && b.maxY < o.y + 8
                        && b.minZ > o.z && b.maxZ < o.z + 12, "Whole mob AABB strictly inside 16x8x12 floor");
        check(h, precision ? p.getEyeY() >= b.maxY - b.getYsize() * .25 && p.getEyeY() < b.maxY
                        : p.getEyeY() > b.minY && p.getEyeY() < b.maxY - b.getYsize() * .25,
                "Horizontal ray intersects actual requested precision/body region");
        return e;
    }
    private static void fire(GameTestHelper h, ServerPlayer p, int generated) {
        reaim(p); var s = p.getMainHandItem(); var before = ammo(s);
        // Fix the dispersion draw; retain the real cone, collision, damage and ammo path.
        p.getRandom().setSeed(0x5DEECE66DL);
        check(h, profile(s).mode() == WeaponProfile.Mode.HITSCAN && profile(s).burst() == 1
                        && profile(s).chargeTicks() == 0, "Fixture uses an actual uncharged single-bolt pool weapon");
        check(h, WeaponRuntime.beginUse(p), "Real trigger accepted after existing cadence");
        WeaponRuntime.releaseUse(p, s); var after = ammo(s);
        check(h, after.rounds() == before.rounds() - 1 + generated && after.reserve() == before.reserve()
                        && after.overflow() == before.overflow(),
                "Exactly one paid round plus " + generated + " earned rounds; reserve/overflow unchanged for " + entry(s).id());
    }
    private static void hit(GameTestHelper h, ServerPlayer p, boolean precision, int generated) {
        var e = target(h, p, precision, HEALTH); fire(h, p, generated);
        check(h, e.isAlive() && e.getHealth() < HEALTH, "Actual positive nonlethal HP loss"); e.discard();
    }
    private static void progress(GameTestHelper h, ServerPlayer p, String perk, int expected) {
        int actual = WeaponPrecisionReturn.progress(p, perk);
        check(h, actual == expected, perk + " progress expected " + expected + ", actual " + actual);
    }
    private static int command(GameTestHelper h, ServerPlayer p, String text) {
        try { return h.getLevel().getServer().getCommands().getDispatcher().execute(text, p.createCommandSourceStack()); }
        catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) { throw new AssertionError(text, e); }
    }
    private static ItemDisplayHud node(ServerPlayer p, String suffix) {
        return (ItemDisplayHud)DisplayHud.getHud(p, AmmoHud.PREFIX + suffix);
    }
    private static void digits(GameTestHelper h, ServerPlayer p, String field, int expected) {
        String text = Integer.toString(expected);
        for (int i = 0; i < text.length(); i++) {
            var n = node(p, field + "_" + i);
            check(h, n != null && Identifier.fromNamespaceAndPath("destiny", "gui/hud/ammo_digit_" + text.charAt(i))
                    .equals(n.getItem().get(DataComponents.ITEM_MODEL)), "Live HUD " + field + " digit " + i);
        }
        check(h, node(p, field + "_" + text.length()) == null, "No stale trailing " + field + " digit");
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void exactBaseSocketsAndAll63OwnedCommandsNeverMintAmmo(GameTestHelper h) {
        WeaponModelGameTests.assertCatalogExpansion(h);
        check(h, WeaponCatalog.all().size() == 65 && PrecisionReturnProfile.perks().size() == 2, "Original63 plus Ace and Izanagi, two traits");
        var p = player(h, 6.5);
        for (String perk : List.of(TT, FTTC)) {
            var rows = perk.equals(TT) ? TT_ROWS : FTTC_ROWS;
            var pinned = PrecisionReturnProfile.find(perk).orElseThrow(); boolean triple = perk.equals(TT);
            check(h, pinned.hash() == (triple ? 3400784728L : 1354429876L) && pinned.hits() == (triple ? 3 : 4)
                            && pinned.returnRounds() == (triple ? 1 : 2) && pinned.windowTicks() == 40
                            && pinned.weapons().size() == rows.size() && Set.copyOf(pinned.weapons()).equals(rows),
                    "Independent literal base hashes, exact official sockets and pairwise 40-tick timing");
            Set<String> pool = rows.stream().map(WeaponPerks.Roll::id).collect(Collectors.toSet());
            for (var e : WeaponCatalog.all()) {
                p.getInventory().clearContent(); var s = equip(h, p, e.id(), null, 0, 0); var saved = s.copy();
                check(h, WeaponPerks.selected(s, perk).isEmpty(), "No default precision trait: " + e.id());
                check(h, command(h, p, "destiny perk list") == 1 && command(h, p, "destiny perk status") == 1,
                        "Real owned-stack list/status for " + e.id());
                check(h, command(h, p, "destiny perk select " + perk) == (pool.contains(e.id()) ? 1 : 0),
                        "All-65 command allowlist for " + e.id() + "/" + perk);
                if (pool.contains(e.id())) {
                    check(h, rows.contains(WeaponPerks.selected(s, perk).orElseThrow())
                                    && command(h, p, "destiny perk select " + perk) == 1, "Pinned row and idempotent select");
                    check(h, command(h, p, "destiny perk clear") == 1, "Actual command clears selected trait");
                }
                progress(h, p, perk, 0);
                check(h, ItemStack.matches(saved, s) && ammo(s).total() == 0 && WeaponRuntime.activeProjectiles(p) == 0,
                        "Command round trip cannot mint ammo, enrich inventory or emit: " + e.id());
            }
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void tripleTapScoutAndHandCannonReturnOnlyOnEveryThirdPaidPrecision(GameTestHelper h) {
        var scout = player(h, 3); var hand = player(h, 9);
        var a = equip(h, scout, SCOUT, TT, 8, 0); var b = equip(h, hand, DUKE, TT, 8, 0); drive(h, scout, hand);
        int c = Math.max(cadence(a), cadence(b)); check(h, c < 40, "Actual cadence fits precision window");
        for (int n = 1; n <= 6; n++) {
            final int count = n;
            Runnable step = () -> {
                for (var p : List.of(scout, hand)) {
                    hit(h, p, true, count % 3 == 0 ? 1 : 0); progress(h, p, TT, count % 3);
                    check(h, ammo(p.getMainHandItem()).rounds() == 8 - count + count / 3
                                    && !WeaponRuntime.reloading(p) && WeaponKillClip.remaining(p) == 0,
                            "Real third/sixth return never invokes reload or Kill Clip");
                }
                if (count == 6) h.succeed();
            };
            if (n == 1) step.run(); else h.runAfterDelay((long)(n - 1) * c, step);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void fourthTimesSniperRevolverAndFiniteMachineGunReturnAtFourthNotThird(GameTestHelper h) {
        var sniper = player(h, 2.5); var revolver = player(h, 6); var machine = player(h, 9.5);
        var a = equip(h, sniper, SNIPER, FTTC, 4, 0);
        var b = equip(h, revolver, HC, FTTC, 4, 0); var d = equip(h, machine, MG, FTTC, 4, 0);
        check(h, !profile(a).infiniteReserve() && !profile(d).infiniteReserve(), "Actual zero-reserve special/heavy fixtures");
        drive(h, sniper, revolver, machine); int c = Math.max(cadence(a), Math.max(cadence(b), cadence(d)));
        check(h, c < 40, "Actual sniper cadence fits window");
        for (int n = 1; n <= 4; n++) {
            final int count = n; Runnable step = () -> {
                for (var p : List.of(sniper, revolver, machine)) {
                    hit(h, p, true, count == 4 ? 2 : 0); progress(h, p, FTTC, count % 4);
                    check(h, ammo(p.getMainHandItem()).rounds() == 4 - count + (count == 4 ? 2 : 0)
                                    && !WeaponRuntime.reloading(p), "Fourth paid shot returns two with no reload");
                }
                if (count == 4) h.succeed();
            };
            if (n == 1) step.run(); else h.runAfterDelay((long)(n - 1) * c, step);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 170, environment = "destiny-test:w90_isolated")
    public void pairwiseThirtyNineSurvivesAndExactlyFortyExpiresForBothTraits(GameTestHelper h) {
        var tt39 = player(h, 2); var tt40 = player(h, 4.5); var f39 = player(h, 7); var f40 = player(h, 10);
        equip(h, tt39, SCOUT, TT, 8, 0); equip(h, tt40, SCOUT, TT, 8, 0);
        equip(h, f39, MG, FTTC, 8, 0); equip(h, f40, MG, FTTC, 8, 0); drive(h, tt39, tt40, f39, f40);
        for (var p : List.of(tt39, tt40, f39, f40)) hit(h, p, true, 0);
        for (int n = 2; n <= 4; n++) {
            final int count = n;
            h.runAfterDelay((long)(n - 1) * 39, () -> {
                if (count <= 3) { progress(h, tt39, TT, count - 1); hit(h, tt39, true, count == 3 ? 1 : 0); progress(h, tt39, TT, count % 3); }
                progress(h, f39, FTTC, count - 1); hit(h, f39, true, count == 4 ? 2 : 0); progress(h, f39, FTTC, count % 4);
            });
            h.runAfterDelay((long)(n - 1) * 40, () -> {
                if (count <= 3) { progress(h, tt40, TT, 0); hit(h, tt40, true, 0); progress(h, tt40, TT, 1); }
                progress(h, f40, FTTC, 0); hit(h, f40, true, 0); progress(h, f40, FTTC, 1);
                if (count == 4) {
                    check(h, ammo(tt39.getMainHandItem()).rounds() == 6 && ammo(tt40.getMainHandItem()).rounds() == 5
                                    && ammo(f39.getMainHandItem()).rounds() == 6 && ammo(f40.getMainHandItem()).rounds() == 4,
                            "78/117-tick total sequences qualify only through consecutive 39-tick gaps"); h.succeed();
                }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void sameOwnedStackKeepsProgressThroughStowButItsClockContinues(GameTestHelper h) {
        var keep = player(h, 3); var expire = player(h, 9);
        var a = equip(h, keep, DUAL, TT, 8, 0); var b = equip(h, expire, DUAL, TT, 8, 0); drive(h, keep, expire);
        hit(h, keep, true, 0); hit(h, expire, true, 0);
        for (var p : List.of(keep, expire)) { p.getInventory().setItem(7, new ItemStack(Items.STONE)); select(p, 7); progress(h, p, TT, 0); }
        h.runAfterDelay(2, () -> select(keep, slot(a)));
        h.runAfterDelay(20, () -> { check(h, keep.getMainHandItem() == a && !WeaponHandling.blocked(keep), "Same owned stack ready after real switch");
            progress(h, keep, TT, 1); hit(h, keep, true, 0); progress(h, keep, TT, 2); });
        h.runAfterDelay(30, () -> { hit(h, keep, true, 1); progress(h, keep, TT, 0); });
        h.runAfterDelay(41, () -> select(expire, slot(b)));
        h.runAfterDelay(60, () -> {
            check(h, expire.getMainHandItem() == b && ammo(b).rounds() == 7, "Stowing never reloads or swaps the actual weapon");
            progress(h, expire, TT, 0); hit(h, expire, true, 0); progress(h, expire, TT, 1);
            check(h, ammo(a).rounds() == 6 && ammo(b).rounds() == 6, "Preserved short stow versus expired long stow"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void copyNewOwnerEditsDeathRemovalAndCleanupCannotInheritEarnedHits(GameTestHelper h) {
        var keep = player(h, 9); equip(h, keep, SCOUT, TT, 8, 0); hit(h, keep, true, 0);
        for (String reason : List.of("copy", "new_owner", "edit", "death", "removal", "cleanup", "spectator", "dimension")) {
            var p = player(h, 3); var original = equip(h, p, SCOUT, TT, 8, 0); hit(h, p, true, 0); progress(h, p, TT, 1);
            var saved = original.copy(); ServerPlayer recipient = p;
            switch (reason) {
                case "copy" -> { p.getInventory().setItem(slot(original), original.copy()); WeaponRuntime.tickPlayer(p); }
                case "new_owner" -> {
                    recipient = player(h, 3); p.getInventory().setItem(slot(original), ItemStack.EMPTY); WeaponRuntime.tickPlayer(p);
                    recipient.getInventory().setItem(slot(original), original); recipient.getInventory().setSelectedSlot(slot(original)); WeaponRuntime.tickPlayer(recipient);
                }
                case "edit" -> check(h, command(h, p, "destiny perk clear") == 1 && command(h, p, "destiny perk select " + TT) == 1,
                        "Actual command invalidates even if selected serialized hash returns to the same value");
                case "death" -> { p.setHealth(0); WeaponRuntime.tickPlayer(p); p.setHealth(20); }
                case "removal" -> { p.getInventory().setItem(slot(original), ItemStack.EMPTY); WeaponRuntime.tickPlayer(p);
                    p.getInventory().setItem(slot(original), original); WeaponRuntime.tickPlayer(p); }
                case "cleanup" -> { WeaponRuntime.cleanup(p); WeaponRuntime.tickPlayer(p); }
                case "spectator" -> { p.setGameMode(GameType.SPECTATOR); WeaponRuntime.tickPlayer(p); p.setGameMode(GameType.SURVIVAL); }
                case "dimension" -> {
                    var other = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                            .filter(l -> l != h.getLevel()).findFirst().orElseThrow();
                    p.setServerLevel(other); WeaponRuntime.tickPlayer(p); p.setServerLevel(h.getLevel());
                }
                default -> throw new AssertionError(reason);
            }
            var receiver = recipient; var gun = receiver.getMainHandItem(); progress(h, receiver, TT, 0);
            check(h, ItemStack.matches(saved, original) && ItemStack.matches(saved, gun), reason + " preserves serialized weapon/ammo");
            // Installed now, never inside a delayed callback. Let genuine handling/cadence elapse.
            drive(h, receiver);
            h.runAfterDelay(20, () -> { hit(h, receiver, true, 0); progress(h, receiver, TT, 1); });
            h.runAfterDelay(30, () -> { hit(h, receiver, true, 0); progress(h, receiver, TT, 2);
                check(h, ammo(gun).rounds() == 5, reason + " cannot borrow old hit to return on the second fresh shot"); });
        }
        drive(h, keep);
        h.runAfterDelay(20, () -> progress(h, keep, TT, 1));
        h.runAfterDelay(31, h::succeed);
    }

    @GameTest(structure = FLOOR, maxTicks = 140, environment = "destiny-test:w90_isolated")
    public void bodyAbilityImmuneMissBlockedAndUnselectedNeverEarnOrResetPrecision(GameTestHelper h) {
        var p = player(h, 3); var s = equip(h, p, DUAL, TT, 12, 0);
        var plain = player(h, 9); var unselected = equip(h, plain, DUAL, null, 8, 0); drive(h, p, plain);
        int c = cadence(s); check(h, 5 * c < 40, "Negative controls fit between qualifying hits");
        hit(h, p, true, 0); progress(h, p, TT, 1);
        h.runAfterDelay(c, () -> { hit(h, p, false, 0); progress(h, p, TT, 1);
            var e = target(h, p, true, HEALTH); Combat.damage(p, e, 7, Element.SOLAR);
            check(h, e.getHealth() < HEALTH, "Real ability-attributed positive HP loss"); e.discard(); progress(h, p, TT, 1);
            WeaponRuntime.cancelUseForSkill(p); progress(h, p, TT, 1); });
        h.runAfterDelay(2L * c, () -> {
            var e = target(h, p, true, HEALTH); e.setPermanentlyInvulnerable(true); fire(h, p, 0);
            check(h, e.getHealth() == HEALTH, "Actually immune precision target takes no HP loss"); e.discard(); progress(h, p, TT, 1);
        });
        h.runAfterDelay(3L * c, () -> { fire(h, p, 0); progress(h, p, TT, 1); });
        h.runAfterDelay(4L * c, () -> {
            var e = target(h, p, true, HEALTH); var wall = new BlockPos(5, 2, 3);
            // The lane lies on z=3, a block seam: occlude both sides of the real dispersed ray.
            h.setBlock(wall, Blocks.STONE); h.setBlock(wall.offset(0, 0, -1), Blocks.STONE);
            fire(h, p, 0);
            check(h, e.getHealth() == HEALTH, "Real solid wall blocks otherwise valid precision ray");
            h.setBlock(wall, Blocks.AIR); h.setBlock(wall.offset(0, 0, -1), Blocks.AIR); e.discard(); progress(h, p, TT, 1);
        });
        h.runAfterDelay(5L * c, () -> { hit(h, p, true, 0); progress(h, p, TT, 2); });
        h.runAfterDelay(6L * c, () -> { hit(h, p, true, 1); progress(h, p, TT, 0);
            check(h, ammo(s).rounds() == 6, "Seven paid shots and precisely one generated round"); });
        for (int n = 0; n < 3; n++) h.runAfterDelay((long)n * c + 1, () -> { hit(h, plain, true, 0); progress(h, plain, TT, 0); });
        h.runAfterDelay(6L * c + 1, () -> { check(h, ammo(unselected).rounds() == 5, "Three actual unselected headshots never return ammo"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 190, environment = "destiny-test:w90_isolated")
    public void generatedRoundIsNotReloadAndRealReloadOrSkillDoesNotResetOrPauseClock(GameTestHelper h) {
        var p = player(h, 6.5); var s = equip(h, p, DUKE, TT, 8, 0);
        check(h, WeaponPerks.select(s, KillClipProfile.ID) && WeaponPerks.selected(s, TT).isPresent(), "Real independent Duke TT2/KC4 sockets");
        drive(h, p); int c = cadence(s); var e = target(h, p, true, 1); fire(h, p, 0);
        check(h, e.isDeadOrDying(), "Actual weapon kill arms Kill Clip pending reload"); e.discard();
        h.runAfterDelay(c, () -> { hit(h, p, true, 0); progress(h, p, TT, 2); });
        h.runAfterDelay(2L * c, () -> {
            hit(h, p, true, 1); progress(h, p, TT, 0);
            check(h, WeaponKillClip.remaining(p) == 0 && !WeaponRuntime.reloading(p), "Earned return cannot masquerade as a reload/KC event");
        });
        h.runAfterDelay(3L * c, () -> {
            hit(h, p, true, 0); progress(h, p, TT, 1); WeaponRuntime.cancelUseForSkill(p); progress(h, p, TT, 1);
            check(h, WeaponRuntime.reload(p), "Actual normal reload starts after paid fourth shot"); progress(h, p, TT, 1);
        });
        h.runAfterDelay(3L * c + 1, () -> progress(h, p, TT, 1));
        h.runAfterDelay(3L * c + 39, () -> progress(h, p, TT, 1));
        h.runAfterDelay(3L * c + 40, () -> progress(h, p, TT, 0));
        h.runAfterDelay(3L * c + profile(s).reloadTicks() + 1, () -> {
            check(h, !WeaponRuntime.reloading(p) && ammo(s).rounds() == profile(s).magazine(), "Only real reload fills magazine at actual deadline");
            progress(h, p, TT, 0); hit(h, p, true, 0); progress(h, p, TT, 1); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void finiteZeroReserveMachineGunHudTracksEarnedReturnThenSixPaidShotsReachDry(GameTestHelper h) {
        var p = player(h, 6.5); var s = equip(h, p, MG, FTTC, 4, 0); drive(h, p); int c = cadence(s);
        CombatHud.update(p); digits(h, p, "rounds", 4); digits(h, p, "reserve", 0);
        var glyph = node(p, "rounds_0"); int entity = glyph.getEntityId();
        for (int n = 1; n <= 6; n++) {
            final int count = n; Runnable step = () -> {
                hit(h, p, true, count == 4 ? 2 : 0); progress(h, p, FTTC, count % 4);
                int expected = 4 - count + (count >= 4 ? 2 : 0); var saved = s.copy();
                CombatHud.update(p); digits(h, p, "rounds", expected); digits(h, p, "reserve", 0);
                check(h, node(p, "rounds_0") == glyph && glyph.getEntityId() == entity && node(p, "infinity") == null,
                        "Same actual display entity follows finite ammo, including 1-to-2 return and dry zero");
                for (int i = 0; i < 12; i++) {
                    var state = AmmoHud.current(p).orElseThrow(); var runtime = WeaponRuntime.ammunition(p).orElseThrow();
                    check(h, state.rounds() == expected && state.reserve() == 0 && !state.infiniteReserve()
                                    && runtime.equals(state) && !state.reloading(), "Read-only actual ammo projections");
                    progress(h, p, FTTC, count % 4); CombatHud.update(p);
                }
                check(h, ItemStack.matches(saved, s) && ammo(s).overflow() == 0 && WeaponKillClip.remaining(p) == 0,
                        "HUD/progress reads neither generate a second return nor spend reserve/overflow");
            };
            if (n == 1) step.run(); else h.runAfterDelay((long)(n - 1) * c, step);
        }
        h.runAfterDelay(6L * c, () -> {
            var saved = s.copy(); reaim(p);
            check(h, !WeaponRuntime.beginUse(p) && !WeaponRuntime.reload(p) && !WeaponRuntime.reloading(p)
                            && ItemStack.matches(saved, s) && ammo(s).total() == 0,
                    "Six genuinely paid shots exhaust four initial plus two earned rounds; dry input cannot mint or reload");
            WeaponRuntime.releaseUse(p, s); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 150, environment = "destiny-test:w90_isolated")
    public void aishaDistinctSocketsTrackIndependentGroupsAndTwelfthHitReturnsThree(GameTestHelper h) {
        var p = player(h, 6.5); var s = equip(h, p, DUAL, TT, 12, 0);
        check(h, WeaponPerks.select(s, FTTC) && WeaponPerks.selected(s, TT).orElseThrow().socket() == 3
                        && WeaponPerks.selected(s, FTTC).orElseThrow().socket() == 4, "Actual TT3 plus FTTC4 sockets coexist");
        drive(h, p); int c = cadence(s);
        for (int n = 1; n <= 12; n++) {
            final int count = n; Runnable step = () -> {
                int generated = (count % 3 == 0 ? 1 : 0) + (count % 4 == 0 ? 2 : 0);
                hit(h, p, true, generated); progress(h, p, TT, count % 3); progress(h, p, FTTC, count % 4);
                check(h, ammo(s).rounds() == 12 - count + count / 3 + 2 * (count / 4)
                                && ammo(s).reserve() == 0 && !WeaponRuntime.reloading(p) && WeaponKillClip.remaining(p) == 0,
                        "Independent exact paid-shot arithmetic at hit " + count);
                if (count == 12) { check(h, ammo(s).rounds() == 10, "Twelfth real emission returns exactly three, once per selected trait"); h.succeed(); }
            };
            if (n == 1) step.run(); else h.runAfterDelay((long)(n - 1) * c, step);
        }
    }
}
