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
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/** W66 server/EmbeddedChannel integration fixtures: all credit comes from paid, real final blows.
 * Uses the existing 16x8x12 floor. No injected kill tokens, clock rewrites, native-client claims,
 * or registration here. Drivers are installed at setup, never inside a scheduler callback.
 */
public final class WeaponRampageW66GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String DUKE = "duke_mk_44";
    private static final String GL = "edge_transit";
    private static final String RAMPAGE = RampageProfile.ID;
    private static final String KC = KillClipProfile.ID;
    private static final String OUTLAW = OutlawProfile.ID;
    private static final int DECAY = 90;
    private static final float HEALTH = 1000;
    private static final Set<String> POOL = Set.of(DUKE, "austringer", "gnawing_hunger", "bygones",
            "chattering_bone", "blast_furnace", "claws_of_the_wolf", "dead_man_walking_xx7463",
            "brass_attacks", "beloved", "dust_rock_blues", "parcel_of_stardust_fell_to_earth",
            "dream_breaker", "line_in_the_sand", "stormchaser", "deafening_whisper", GL,
            "canis_major", "fixed_odds", "hammerhead", "retrofit_escapade");

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static boolean near(float a, float b) { return Math.abs(a - b) < .003f; }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static WeaponCatalog.Entry entry(ItemStack s) { return WeaponItems.entry(s).orElseThrow(); }
    private static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(entry(s)); }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, profile(s)); }
    private static int cadence(ItemStack s) { return (int) Math.ceil(profile(s).cadenceTicks()); }
    private static int slot(ItemStack s) { return WeaponCharacteristics.of(entry(s)).slot().hotbar(); }
    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            p.setServerLevel(h.getLevel());
            TestPlayers.remove(p);
        });
        return p;
    }
    private static ItemStack item(String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow();
        var gun = WeaponItems.create(e);
        WeaponItems.save(gun, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve));
        return gun;
    }
    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, boolean selected) {
        var e = WeaponCatalog.find(id).orElseThrow();
        var f = WeaponProfile.forEntry(e);
        var gun = item(id, f.magazine(), f.infiniteReserve() ? 0 : 3);
        if (selected) check(h, WeaponPerks.select(gun, RAMPAGE), "Official Rampage selection: " + id);
        p.getInventory().setItem(slot(gun), gun);
        p.getInventory().setSelectedSlot(slot(gun));
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
        return gun;
    }
    private static void drive(GameTestHelper h, ServerPlayer... players) {
        h.onEachTick(() -> {
            for (var p : players) {
                WeaponRuntime.tickPlayer(p);
                TestPlayers.drain(p);
            }
        });
    }
    private static void select(ServerPlayer p, int index) {
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(index));
        WeaponRuntime.tickPlayer(p);
    }
    private static void reaim(ServerPlayer p) {
        WeaponAiming.cleanup(p);
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0);
        WeaponAiming.tick(p);
    }
    private static void shot(GameTestHelper h, ServerPlayer p) {
        // Every comparison starts from this explicit ray, including every projectile emission.
        // Fix the dispersion draw; retain the real cone, collision, damage and ammo path.
        p.getRandom().setSeed(0x5DEECE66DL);
        reaim(p);
        var gun = p.getMainHandItem();
        int rounds = ammo(gun).rounds();
        int reserve = ammo(gun).reserve();
        check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == rounds - 1
                        && ammo(gun).reserve() == reserve,
                "Accepted production shot spends exactly one loaded round, never free reserve");
        WeaponRuntime.releaseUse(p, gun);
    }
    private static double lane(GameTestHelper h, ServerPlayer p) {
        return p.getZ() - h.absoluteVec(Vec3.ZERO).z;
    }
    private static Husk target(GameTestHelper h, double x, double y, double z, float health) {
        var e = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z));
        e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HEALTH);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        e.setHealth(health);
        TestCleanup.register(h, e::discard);
        var o = h.absoluteVec(Vec3.ZERO); var b = e.getBoundingBox();
        check(h, b.minX > o.x && b.maxX < o.x + 16 && b.minY > o.y && b.maxY < o.y + 8
                        && b.minZ > o.z && b.maxZ < o.z + 12,
                "Whole enemy AABB must remain strictly inside the existing 16x8x12 fixture");
        return e;
    }
    private static Husk target(GameTestHelper h, ServerPlayer p, double x, boolean precision, float health) {
        var e = target(h, x, precision ? 1 : 1.8, lane(h, p), health);
        var b = e.getBoundingBox();
        check(h, precision ? p.getEyeY() >= b.maxY - b.getYsize() * .25 && p.getEyeY() < b.maxY
                        : p.getEyeY() > b.minY && p.getEyeY() < b.maxY - b.getYsize() * .25,
                "Horizontal firing ray crosses the requested precision/body geometry");
        return e;
    }
    private static void kill(GameTestHelper h, ServerPlayer p, boolean precision) {
        var e = target(h, p, 8.5, precision, 1);
        shot(h, p);
        check(h, e.isDeadOrDying() && e.getHealth() == 0, "Real paid hitscan final blow");
        e.discard();
    }
    private static float damage(GameTestHelper h, ServerPlayer p) {
        var e = target(h, p, 8.5, false, HEALTH);
        shot(h, p);
        float loss = HEALTH - e.getHealth();
        check(h, loss > 0 && e.isAlive(), "Comparison measures actual nonlethal body HP loss");
        e.discard();
        return loss;
    }
    private static void state(GameTestHelper h, ServerPlayer p, int stacks, int left) {
        check(h, WeaponRampage.stacks(p) == stacks && WeaponRampage.remaining(p) == left,
                "Expected Rampage x" + stacks + " / next decay " + left + ", got x"
                        + WeaponRampage.stacks(p) + " / " + WeaponRampage.remaining(p));
        float multiplier = switch (stacks) { case 1 -> 1.1f; case 2 -> 1.21f; case 3 -> 1.331f; default -> 1; };
        check(h, near(WeaponRampage.capture(p).multiplier(), multiplier), "Emission captures current actual stack multiplier");
    }
    private static int command(GameTestHelper h, ServerPlayer p, String text) {
        try {
            return h.getLevel().getServer().getCommands().getDispatcher().execute(text, p.createCommandSourceStack());
        } catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) {
            throw new AssertionError("Registered player command: " + text, e);
        }
    }
    private static ItemDisplayHud node(ServerPlayer p, String suffix) {
        return (ItemDisplayHud) DisplayHud.getHud(p, WeaponPerkHud.PREFIX + suffix);
    }
    private static long nodes(ServerPlayer p) {
        return DisplayHud.getHuds(p).keySet().stream().filter(k -> k.startsWith(WeaponPerkHud.PREFIX)).count();
    }
    private static void model(GameTestHelper h, ServerPlayer p, String suffix, String path) {
        var n = node(p, suffix);
        check(h, n != null && Identifier.fromNamespaceAndPath("destiny", "gui/hud/" + path)
                        .equals(n.getItem().get(DataComponents.ITEM_MODEL)), "Actual HUD model " + suffix + " = " + path);
    }
    private static void hud(GameTestHelper h, ServerPlayer p) {
        CombatHud.update(p);
        int count = WeaponRampage.stacks(p), left = WeaponRampage.remaining(p);
        boolean kc = WeaponKillClip.remaining(p) > 0, outlaw = WeaponOutlaw.remaining(p) > 0;
        check(h, nodes(p) == 6L * ((count > 0 ? 1 : 0) + (kc ? 1 : 0) + (outlaw ? 1 : 0)),
                "Exactly six live nodes per actual active perk, without stale rows");
        for (String suffix : List.of("marker", "label", "minutes", "colon", "tens", "ones"))
            check(h, (node(p, "rampage_" + suffix) != null) == (count > 0), "Rampage row lifetime: " + suffix);
        if (count > 0) {
            model(h, p, "rampage_label", "perk_rampage_w66_x" + count);
            model(h, p, "rampage_minutes", "ammo_digit_0");
            model(h, p, "rampage_colon", "perk_colon_w61");
            int seconds = (left + 19) / 20;
            model(h, p, "rampage_tens", "ammo_digit_" + seconds / 10);
            model(h, p, "rampage_ones", "ammo_digit_" + seconds % 10);
            check(h, node(p, "rampage_label").getLocation().y() == 778 - 32 * (kc ? 1 : 0),
                    "W155 damage-priority Rampage follows KC, before reload utility Outlaw");
        }
        if (kc) model(h, p, "label", "perk_kill_clip_w61");
        if (outlaw) model(h, p, "outlaw_label", "perk_outlaw_w62");
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void exactTwentyOneBaseSocketsAndOwnedCommandsNeverMintAmmo(GameTestHelper h) {
        check(h, RampageProfile.HASH == 3425386926L && RampageProfile.perk().hash() == 3425386926L
                        && RampageProfile.perk().decayTicks() == DECAY && RampageProfile.rolls().size() == 21
                        && RampageProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(Collectors.toSet()).equals(POOL),
                "Exact release base-hash pool: no enhanced 288411554 or broad family fallback");
        for (var e : WeaponCatalog.all()) {
            var gun = item(e.id(), 0, 0); var saved = gun.copy();
            check(h, WeaponPerks.selected(gun, RAMPAGE).isEmpty(), "New weapons have no default Rampage");
            check(h, WeaponPerks.select(gun, RAMPAGE) == POOL.contains(e.id()), "Exact allowlist: " + e.id());
            if (POOL.contains(e.id())) {
                var r = WeaponPerks.selected(gun, RAMPAGE).orElseThrow();
                check(h, r.socket() == (e.id().equals("bygones") ? 3 : 4)
                                && r.hash() == WeaponCharacteristics.of(e).bungieHash()
                                && r.perkHash() == 3425386926L && r.plugSetHash() > 0,
                        "Pinned official zero-based socket, item and base perk hash: " + e.id());
                var tag = gun.get(DataComponents.CUSTOM_DATA).copyTag();
                var slots = new CompoundTag(); slots.putLong(Integer.toString(r.socket()), 288411554L);
                tag.put(WeaponPerks.SLOTS_KEY, slots); gun.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
                check(h, WeaponPerks.selected(gun, RAMPAGE).isEmpty(), "Enhanced saved hash is inert: " + e.id());
                check(h, WeaponPerks.clear(gun), "Clear actual saved selection");
            }
            check(h, ItemStack.matches(saved, gun), "Trait edits preserve every non-trait component, including empty ammo");
        }
        var p = player(h, 6.5); var gun = equip(h, p, DUKE, false);
        WeaponItems.save(gun, new WeaponMagazine(profile(gun), 0, 0)); var saved = gun.copy();
        check(h, command(h, p, "destiny perk list") == 1 && command(h, p, "destiny perk select rampage") == 1
                        && command(h, p, "destiny perk select rampage") == 1 && command(h, p, "destiny perk status") == 1,
                "Real non-OP owned-stack list/select/idempotent-select/status commands");
        state(h, p, 0, 0);
        check(h, ammo(gun).rounds() == 0 && ammo(gun).reserve() == 0 && WeaponRuntime.activeProjectiles(p) == 0,
                "Selection/status commands grant neither ammunition, a stack, nor an emitted shot");
        check(h, command(h, p, "destiny perk clear") == 1 && p.getMainHandItem() == gun && ItemStack.matches(saved, gun),
                "Command round trip preserves original stack and empty ammunition");
        var preview = WeaponModels.create(WeaponCatalog.find(DUKE).orElseThrow());
        p.getInventory().setItem(0, preview);
        check(h, !WeaponPerks.select(preview, RAMPAGE) && command(h, p, "destiny perk select rampage") == 0,
                "Preview carriers cannot acquire combat Rampage");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void officialSocketConflictsReplaceOnlyThatSocketInEitherEditOrder(GameTestHelper h) {
        for (String id : new String[]{DUKE, "gnawing_hunger", "bygones", "blast_furnace",
                "claws_of_the_wolf", "dead_man_walking_xx7463", "canis_major"}) {
            for (boolean reverse : new boolean[]{false, true}) {
                var gun = item(id, 1, 2); var saved = gun.copy();
                String first = reverse ? RAMPAGE : KC, last = reverse ? KC : RAMPAGE;
                check(h, WeaponPerks.select(gun, first) && WeaponPerks.select(gun, last)
                                && WeaponPerks.selected(gun, first).isEmpty() && WeaponPerks.selected(gun, last).isPresent(),
                        "KC/Rampage same official socket is exclusive: " + id);
                check(h, WeaponPerks.clear(gun) && ItemStack.matches(saved, gun), "Conflicts never alter paid ammo");
            }
        }
        for (String id : new String[]{DUKE, "austringer", "blast_furnace", "chattering_bone"}) {
            for (boolean reverse : new boolean[]{false, true}) {
                var gun = item(id, 1, 2);
                check(h, WeaponPerks.select(gun, reverse ? RAMPAGE : OUTLAW)
                                && WeaponPerks.select(gun, reverse ? OUTLAW : RAMPAGE)
                                && WeaponPerks.selected(gun, OUTLAW).orElseThrow().socket()
                                != WeaponPerks.selected(gun, RAMPAGE).orElseThrow().socket(),
                        "Distinct official Outlaw/Rampage sockets coexist: " + id);
            }
        }
        for (boolean reverse : new boolean[]{false, true}) {
            var gun = item("chattering_bone", 1, 0);
            check(h, WeaponPerks.select(gun, reverse ? RAMPAGE : KC) && WeaponPerks.select(gun, reverse ? KC : RAMPAGE)
                            && WeaponPerks.selected(gun, KC).orElseThrow().socket() == 3
                            && WeaponPerks.selected(gun, RAMPAGE).orElseThrow().socket() == 4,
                    "Chattering Bone KC3/Rampage4 both remain selected");
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 220, environment = "destiny-test:w90_isolated")
    public void paidDukeKillsScaleRealBodyDamageAtEveryStackAndFourthKillRefreshesTheCap(GameTestHelper h) {
        var p = player(h, 6.5); var gun = equip(h, p, DUKE, true); drive(h, p);
        float baseline = damage(h, p); state(h, p, 0, 0); int c = cadence(gun);
        for (int stage = 1; stage <= 3; stage++) {
            final int n = stage;
            h.runAfterDelay((2L * n - 1) * c, () -> { kill(h, p, false); state(h, p, n, DECAY); });
            h.runAfterDelay(2L * n * c, () -> {
                float expected = switch (n) { case 1 -> 1.1f; case 2 -> 1.21f; default -> 1.331f; };
                check(h, near(damage(h, p), baseline * expected), "Observed HP loss at Rampage x" + n + " = " + expected);
                state(h, p, n, DECAY - c);
            });
        }
        h.runAfterDelay(7L * c, () -> {
            state(h, p, 3, DECAY - 2 * c); kill(h, p, false); state(h, p, 3, DECAY);
            check(h, ammo(gun).rounds() == profile(gun).magazine() - 8 && ammo(gun).reserve() == 0,
                    "Baseline, three comparisons and four kills paid eight real rounds");
        });
        h.runAfterDelay(7L * c + DECAY - 1, () -> state(h, p, 3, 1));
        h.runAfterDelay(7L * c + DECAY, () -> { state(h, p, 2, DECAY); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 360, environment = "destiny-test:w90_isolated")
    public void ninetyTickStageBoundariesCatchUpAfterSkippedPollingWithoutQueryRefresh(GameTestHelper h) {
        var p = player(h, 3); var gun = equip(h, p, DUKE, true);
        var skipped = player(h, 9); var other = equip(h, skipped, DUKE, true);
        int c = Math.max(cadence(gun), cadence(other));
        // Deliberately no per-test runtime driver: neither reads nor update counts advance the clock.
        kill(h, p, false); kill(h, skipped, false);
        h.runAfterDelay(c, () -> { kill(h, p, false); kill(h, skipped, false); });
        h.runAfterDelay(2L * c, () -> {
            kill(h, p, false); kill(h, skipped, false); state(h, p, 3, DECAY);
            var saved = gun.copy();
            for (int n = 0; n < 20; n++) { WeaponRampage.update(p); state(h, p, 3, DECAY); }
            check(h, ItemStack.matches(saved, gun), "Repeated same-tick reads/updates cannot refresh or mutate ammo");
            skipped.getInventory().setItem(7, new ItemStack(Items.STONE)); select(skipped, 7);
        });
        for (int stage = 0; stage < 3; stage++) {
            final int n = stage;
            h.runAfterDelay(2L * c + (n + 1L) * DECAY - 1, () -> state(h, p, 3 - n, 1));
            h.runAfterDelay(2L * c + (n + 1L) * DECAY, () -> {
                WeaponRampage.update(p); state(h, p, 2 - n, n == 2 ? 0 : DECAY);
            });
        }
        h.runAfterDelay(2L * c + 3L * DECAY + 7, () -> {
            select(skipped, slot(other)); WeaponRampage.update(skipped);
            state(h, skipped, 0, 0); state(h, p, 0, 0);
            check(h, ammo(gun).rounds() == 6 && ammo(other).rounds() == 6,
                    "Skipped polling/stowed expiry does not spend or replenish the three paid rounds");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 35, environment = "destiny-test:w90_isolated")
    public void abilityMeleeNonlethalAndUnselectedFinalBlowsCannotEarnRampage(GameTestHelper h) {
        var p = player(h, 3); var gun = equip(h, p, DUKE, true);
        var ability = target(h, p, 8.5, false, 1);
        check(h, Combat.damage(p, ability, 100, Element.SOLAR) && ability.isDeadOrDying(), "Real ability-attributed final blow");
        ability.discard(); state(h, p, 0, 0);
        var melee = target(h, p, 3.5, false, 1);
        check(h, melee.hurtServer(p.level(), p.damageSources().playerAttack(p), 100) && melee.isDeadOrDying(),
                "Actual ordinary melee damage source final blow");
        melee.discard(); state(h, p, 0, 0);
        damage(h, p); state(h, p, 0, 0);
        check(h, ammo(gun).rounds() == 8, "Abilities and melee do not secretly emit or spend a weapon shot");
        var unselected = player(h, 9); equip(h, unselected, DUKE, false);
        kill(h, unselected, true); state(h, unselected, 0, 0);
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void sameTickReturnAndStowedClockBelongOnlyToTheActualStillOwnedStack(GameTestHelper h) {
        var p = player(h, 3); var gun = equip(h, p, DUKE, true);
        var other = player(h, 9); var own = equip(h, other, DUKE, true);
        kill(h, p, false); kill(h, other, false);
        p.getInventory().setItem(7, new ItemStack(Items.STONE));
        select(p, 7); state(h, p, 0, 0); select(p, 0); state(h, p, 1, DECAY);
        var copy = gun.copy();
        check(h, copy != gun && ItemStack.matches(copy, gun), "Component-identical copy is a different actual stack");
        p.getInventory().setItem(9, gun); p.getInventory().setItem(0, copy);
        WeaponRampage.update(p); state(h, p, 0, 0);
        p.getInventory().setItem(0, gun); p.getInventory().setItem(9, copy);
        WeaponRampage.update(p); state(h, p, 1, DECAY);
        select(p, 7);
        h.runAfterDelay(37, () -> {
            select(p, 0); check(h, p.getMainHandItem() == gun, "Return holds the original actual stack");
            state(h, p, 1, DECAY - 37); state(h, other, 1, DECAY - 37);
            var copiedForOther = gun.copy();
            other.getInventory().setItem(9, own); other.getInventory().setItem(0, copiedForOther);
            WeaponRampage.update(other); state(h, other, 0, 0);
            other.getInventory().setItem(0, own); other.getInventory().setItem(9, copiedForOther);
            state(h, other, 1, DECAY - 37);
            p.getInventory().setItem(0, ItemStack.EMPTY); WeaponRampage.update(p);
            other.getInventory().setItem(10, own); other.getInventory().setItem(0, gun);
            WeaponRampage.update(other); state(h, other, 0, 0);
            other.getInventory().setItem(0, own); other.getInventory().setItem(10, ItemStack.EMPTY);
            p.getInventory().setItem(0, gun); WeaponRampage.update(p);
            state(h, p, 0, 0); state(h, other, 1, DECAY - 37);
            check(h, ammo(gun).rounds() == 8 && ammo(own).rounds() == 8,
                    "Copies and actual ownership transfer never inherit buffs or refill ammunition");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void realGrenadeBlastKeepsEmissionSnapshotAndCreditsOnlyItsStillOwnedStowedSource(GameTestHelper h) {
        var p = player(h, 2); var source = equip(h, p, GL, true);
        var dropped = player(h, 6); var lost = equip(h, dropped, GL, true);
        var control = player(h, 10); equip(h, control, GL, false);
        drive(h, p, dropped, control);
        check(h, profile(source).mode() == WeaponProfile.Mode.PROJECTILE && profile(source).blastRadius() > 0,
                "Fixture uses implemented generic weapon-projectile GL blast, not an explosive payload perk");
        var first = target(h, p, 5.5, false, 1); shot(h, p);
        check(h, first.isAlive() && WeaponRuntime.activeProjectiles(p) == 1, "Emission does not pre-credit an in-flight grenade");
        h.runAfterDelay(3, () -> {
            check(h, first.isDeadOrDying(), "Actual GL collision earns first source stack"); first.discard();
            check(h, WeaponRampage.stacks(p) == 1, "Real generic grenade blast is eligible weapon damage");
        });
        record Impact(Husk victim, Husk tank, Husk lostVictim, Husk plainVictim, Husk plainTank, ItemStack current) {}
        var impact = new Impact[1];
        h.runAfterDelay(cadence(source) + 3L, () -> {
            var victim = target(h, p, 12.5, false, 1);
            // Outward splash probes keep both comparison AABBs outside the middle lane's blast.
            var tank = target(h, 12.5, 1.8, lane(h, p) - .9, HEALTH);
            var lostVictim = target(h, dropped, 12.5, false, 1);
            var plainVictim = target(h, control, 12.5, false, 1);
            var plainTank = target(h, 12.5, 1.8, lane(h, control) + .9, HEALTH);
            shot(h, p); shot(h, dropped); shot(h, control);
            check(h, tank.getHealth() == HEALTH && plainTank.getHealth() == HEALTH, "Blast HP is unchanged at emission");
            var current = item(DUKE, 8, 0); check(h, WeaponPerks.select(current, RAMPAGE), "Current Duke also selects Rampage");
            p.getInventory().setItem(0, current); select(p, 0); state(h, p, 0, 0);
            var replacement = lost.copy(); dropped.getInventory().setItem(slot(lost), replacement);
            WeaponRampage.update(dropped);
            check(h, WeaponRuntime.activeProjectiles(p) == 1 && WeaponRuntime.activeProjectiles(dropped) == 1,
                    "Stow and source removal preserve already emitted weapon projectiles");
            impact[0] = new Impact(victim, tank, lostVictim, plainVictim, plainTank, current);
        });
        h.runAfterDelay(cadence(source) + 3L + 8, () -> {
                var f = impact[0];
                var victim = f.victim(); var tank = f.tank(); var lostVictim = f.lostVictim();
                var plainVictim = f.plainVictim(); var plainTank = f.plainTank(); var current = f.current();
                float base = HEALTH - plainTank.getHealth();
                check(h, victim.isDeadOrDying() && lostVictim.isDeadOrDying() && plainVictim.isDeadOrDying()
                                && base > 0 && near(HEALTH - tank.getHealth(), base * 1.1f),
                        "Actual splash retains x1 emission damage even though its final blow earns source x2");
                state(h, p, 0, 0); state(h, dropped, 0, 0); state(h, control, 0, 0);
                select(p, slot(source));
                check(h, p.getMainHandItem() == source && WeaponRampage.stacks(p) == 2
                                && WeaponRampage.remaining(p) > 0 && WeaponRampage.remaining(p) <= DECAY,
                        "Projectile final blow credits original still-owned selected stack while stowed, never current Duke");
                check(h, ammo(source).rounds() == profile(source).magazine() - 2 && ammo(source).reserve() == 3
                                && ammo(current).rounds() == 8 && ammo(lost).rounds() == profile(lost).magazine() - 1,
                        "Every GL round is paid and neither current gun nor removed source is reloaded by credit");
                check(h, WeaponRuntime.activeProjectiles(p) == 0 && WeaponRuntime.activeProjectiles(dropped) == 0,
                        "Both actual impacts retire their projectiles");
                h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 140, environment = "destiny-test:w90_isolated")
    public void grenadeEmittedOnLastActiveTickStillDealsSnapshotBlastAfterExpiry(GameTestHelper h) {
        var p = player(h, 3); var gun = equip(h, p, GL, true);
        var control = player(h, 9); equip(h, control, GL, false); drive(h, p, control);
        var first = target(h, p, 5.5, false, 1); shot(h, p);
        record Impact(Husk buffed, Husk plain) {}
        var impact = new Impact[1];
        long[] fireAt = {-1};
        h.runAfterDelay(3, () -> {
            check(h, first.isDeadOrDying() && WeaponRampage.stacks(p) == 1, "Actual projectile kill primes source");
            first.discard(); int remaining = WeaponRampage.remaining(p);
            fireAt[0] = now(p) + remaining - 1L;
        });
        // The actual kill determines expiry. Register the observer before callback iteration;
        // it reads that real deadline without adding callbacks or changing the gameplay clock.
        h.onEachTick(() -> {
            if (fireAt[0] < 0) return;
            long elapsed = now(p) - fireAt[0];
            if (elapsed == 0) {
                state(h, p, 1, 1);
                var buffed = target(h, p, 12.5, false, HEALTH);
                var plain = target(h, control, 12.5, false, HEALTH);
                shot(h, p); shot(h, control);
                check(h, buffed.getHealth() == HEALTH && WeaponRuntime.activeProjectiles(p) == 1,
                        "Last-tick emission has not impacted or fabricated a final blow");
                impact[0] = new Impact(buffed, plain);
            } else if (elapsed == 8) {
                    var buffed = impact[0].buffed(); var plain = impact[0].plain();
                    float base = HEALTH - plain.getHealth();
                    check(h, base > 0 && near(HEALTH - buffed.getHealth(), base * 1.1f),
                            "Post-expiry generic GL impact retains the emission-time x1 snapshot");
                    state(h, p, 0, 0);
                    check(h, ammo(gun).rounds() == profile(gun).magazine() - 2 && ammo(gun).reserve() == 3,
                            "Waiting for expiry neither refunds nor auto-fills paid finite GL ammunition");
                    h.succeed();
            }
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void cleanupDeathSpectatorDimensionRemovalAndRealTraitEditsInvalidateSessions(GameTestHelper h) {
        var keeper = player(h, 9); equip(h, keeper, DUKE, true); kill(h, keeper, false);
        for (String reason : List.of("cleanup", "death", "spectator", "dimension", "removal", "changed")) {
            var p = player(h, 3); var gun = equip(h, p, DUKE, true); kill(h, p, false); state(h, p, 1, DECAY);
            var saved = gun.copy();
            switch (reason) {
                case "cleanup" -> { WeaponRuntime.cleanup(p); WeaponRuntime.tickPlayer(p); }
                case "death" -> { p.setHealth(0); WeaponRampage.update(p); p.setHealth(20); }
                case "spectator" -> { p.setGameMode(GameType.SPECTATOR); WeaponRampage.update(p); p.setGameMode(GameType.SURVIVAL); }
                case "dimension" -> {
                    var otherLevel = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                            .filter(l -> l != h.getLevel()).findFirst().orElseThrow();
                    // Embedded player is unregistered: exercise level validation, not a claimed teleport event.
                    p.setServerLevel(otherLevel); WeaponRampage.update(p); p.setServerLevel(h.getLevel());
                }
                case "removal" -> { p.getInventory().setItem(0, ItemStack.EMPTY); WeaponRampage.update(p); p.getInventory().setItem(0, gun); }
                case "changed" -> check(h, command(h, p, "destiny perk clear") == 1
                                && command(h, p, "destiny perk select rampage") == 1,
                        "Actual command edits call changed even when serialized trait selection returns to the same value");
                default -> throw new AssertionError(reason);
            }
            WeaponRampage.update(p); state(h, p, 0, 0); state(h, keeper, 1, DECAY);
            check(h, ItemStack.matches(saved, gun), reason + " invalidation preserves paid ammo and serialized item identity");
            if (reason.equals("changed")) {
                check(h, !WeaponRuntime.beginUse(p), "Trait edits cannot reset the just-spent Duke firing cadence");
                WeaponRuntime.releaseUse(p, gun);
                check(h, ItemStack.matches(saved, gun), "Denied same-tick shot after edit spends no extra ammo");
            }
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 340, environment = "destiny-test:w90_isolated")
    public void liveHudUsesActualStackStageAndNextDecayAlongsideRealOutlawAndKillClip(GameTestHelper h) {
        var p = player(h, 3); var gun = equip(h, p, DUKE, true);
        check(h, WeaponPerks.select(gun, OUTLAW), "Duke selects independent Outlaw socket");
        var chatter = player(h, 9); var pulse = equip(h, chatter, "chattering_bone", true);
        check(h, WeaponPerks.select(pulse, KC), "Chattering Bone retains Rampage4 with KC3");
        drive(h, p, chatter); hud(h, p); hud(h, chatter);
        check(h, nodes(p) == 0 && nodes(chatter) == 0, "Selection alone creates no buff feed nodes");
        kill(h, p, true); kill(h, chatter, false);
        check(h, WeaponRuntime.reloadFromMarksmanDodge(chatter) == 1 && WeaponKillClip.remaining(chatter) == 100,
                "Actual paid source kill plus transferred cartridge activates coexisting KC");
        state(h, p, 1, DECAY); hud(h, p); hud(h, chatter);
        check(h, WeaponOutlaw.remaining(p) == 120 && nodes(p) == 12 && nodes(chatter) == 12,
                "Actual precision kill gives Outlaw/Rampage, actual reload gives KC/Rampage");
        var label = node(p, "rampage_label"); int entity = label.getEntityId();
        var saved = gun.copy();
        for (int i = 0; i < 20; i++) hud(h, p);
        check(h, ItemStack.matches(saved, gun) && node(p, "rampage_label") == label,
                "Repeated HUD reads preserve the actual gun, countdown and cached display entity");
        var ops = h.getLevel().registryAccess().createSerializationContext(NbtOps.INSTANCE);
        // Server-safe codec for live label ItemStacks. Client-only ItemModels codecs belong in asset unit tests.
        for (int n = 1; n <= 3; n++) {
            var icon = label.getItem().copy();
            icon.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/hud/perk_rampage_w66_x" + n));
            var decoded = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, icon).getOrThrow()).getOrThrow();
            check(h, ItemStack.matches(icon, decoded), "Real registry ItemStack codec preserves Rampage x" + n + " HUD model");
        }
        int c = cadence(gun);
        h.runAfterDelay(c, () -> {
            kill(h, p, true); state(h, p, 2, DECAY); hud(h, p);
            check(h, node(p, "rampage_label") == label && label.getEntityId() == entity,
                    "Actual x1-to-x2 updates label without replacing the display entity");
        });
        h.runAfterDelay(2L * c, () -> { kill(h, p, true); state(h, p, 3, DECAY); hud(h, p); });
        h.runAfterDelay(DECAY - 1, () -> { state(h, chatter, 1, 1); hud(h, chatter); });
        h.runAfterDelay(DECAY, () -> {
            state(h, chatter, 0, 0); hud(h, chatter);
            check(h, nodes(chatter) == 6 && node(chatter, "label").getLocation().y() == 778,
                    "Rampage expiry removes its six nodes while actual KC keeps its own row");
        });
        h.runAfterDelay(100, () -> { hud(h, chatter); check(h, nodes(chatter) == 0, "KC expires independently at 100"); });
        h.runAfterDelay(2L * c + DECAY - 1, () -> { state(h, p, 3, 1); hud(h, p); });
        h.runAfterDelay(2L * c + DECAY, () -> { state(h, p, 2, DECAY); hud(h, p); });
        h.runAfterDelay(2L * c + 120, () -> {
            hud(h, p);
            check(h, WeaponOutlaw.remaining(p) == 0 && nodes(p) == 6
                            && node(p, "rampage_label") == label && label.getLocation().y() == 778,
                    "Outlaw expiry compacts surviving Rampage row without respawning its cached label");
        });
        h.runAfterDelay(2L * c + 2L * DECAY, () -> { state(h, p, 1, DECAY); hud(h, p); });
        h.runAfterDelay(2L * c + 3L * DECAY, () -> {
            state(h, p, 0, 0); hud(h, p); hud(h, chatter);
            check(h, nodes(p) == 0 && nodes(chatter) == 0, "No stale x0 label or 0:00 row after final decay");
            CombatHud.remove(p); CombatHud.remove(chatter); h.succeed();
        });
    }
}
