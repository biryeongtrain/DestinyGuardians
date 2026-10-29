package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.Map;

/** Actual paid shots, confirmed kills and reload transfers with Embedded TestPlayers.
 * Automated server coverage only; no native-client/input/rendering proof.
 * Pending-kill stow reset and first-shell consumption are conservative authored policies.
 */
public final class WeaponKillClipW61GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String KC = KillClipProfile.ID;
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }
    private static boolean near(float a, float b) { return Math.abs(a - b) < .002f; }
    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true); p.setOnGround(true);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        return p;
    }
    private static ItemStack item(String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow(); var s = WeaponItems.create(e);
        WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve)); return s;
    }
    private static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow()); }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, profile(s)); }
    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, int rounds, int reserve, boolean perk) {
        var s = item(id, rounds, reserve);
        if (perk) check(h, WeaponPerks.select(s, KC), "Exact official KC socket for " + id);
        int slot = WeaponCharacteristics.of(WeaponItems.entry(s).orElseThrow()).slot().hotbar();
        p.getInventory().setItem(slot, s); p.getInventory().setSelectedSlot(slot); WeaponRuntime.tickPlayer(p); return s;
    }
    private static ItemStack duke(GameTestHelper h, ServerPlayer p) { return equip(h, p, "duke_mk_44", 9, 0, true); }
    private static Husk target(GameTestHelper h, double x, double z, float health) {
        check(h, x > .3 && x < 15.7 && z > .3 && z < 11.7, "Entire target AABB must stay inside 16x8x12 floor fixture, not boundary blocks");
        var e = h.spawn(EntityTypes.HUSK, new Vec3(x, 1.8, z));
        e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); e.setHealth(health);
        TestCleanup.register(h, e::discard); return e;
    }
    private static double lane(GameTestHelper h, ServerPlayer p) { return p.getZ() - h.absoluteVec(Vec3.ZERO).z; }
    private static void shot(GameTestHelper h, ServerPlayer p) {
        var s = p.getMainHandItem(); int before = ammo(s).rounds();
        // Fix the dispersion draw; retain the real cone, collision, damage and ammo path.
        p.getRandom().setSeed(0x5DEECE66DL);
        check(h, WeaponRuntime.beginUse(p) && ammo(s).rounds() == before - 1, "Accepted shot paid exactly one real cartridge");
        WeaponRuntime.releaseUse(p, s);
    }
    private static void kill(GameTestHelper h, ServerPlayer p) {
        var e = target(h, 5.5, lane(h, p), 1); shot(h, p);
        check(h, e.isDeadOrDying() && e.getHealth() == 0, "Actual source-weapon final blow, not injected perk credit"); e.discard();
    }
    private static void select(ServerPlayer p, int slot) { p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot)); }
    /** Comparable blast falloff requires the same firing ray: simulate re-aim after prior real recoil.
     * This fixture touches only aim, not Kill Clip, ammunition, cadence or the emitted damage. */
    private static void reaim(ServerPlayer p) {
        WeaponAiming.cleanup(p); p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
    }
    private static void data(ItemStack s, CompoundTag tag) { s.set(DataComponents.CUSTOM_DATA, CustomData.of(tag)); }
    private static void legacy(ItemStack s, long hash, int socket) {
        var tag = s.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putLong(WeaponPerks.HASH_KEY, hash); tag.putInt(WeaponPerks.SOCKET_KEY, socket); data(s, tag);
    }
    /** Real projectile kill + real finite-reserve reload; wait out the original rocket cadence. */
    private static void primedRocket(GameTestHelper h, ServerPlayer p) {
        var gun = equip(h, p, "bad_omens", 1, 3, true);
        var victim = target(h, 5.5, lane(h, p), 1); shot(h, p);
        check(h, WeaponRuntime.activeProjectiles(p) == 1 && victim.isAlive() && WeaponKillClip.remaining(p) == 0,
                "Emission alone is neither a kill nor activation");
        h.runAfterDelay(3, () -> {
            check(h, victim.isDeadOrDying(), "Source rocket actually killed on collision"); victim.discard();
            check(h, WeaponRuntime.reloadFromMarksmanDodge(p) == 1 && ammo(gun).rounds() == 1 && ammo(gun).reserve() == 2,
                    "One reserve rocket actually transferred");
            check(h, WeaponKillClip.remaining(p) == 100, "Confirmed kill followed by real reload activates");
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void exactThirteenOfficialWeaponsAndSocketsAreSelectableWithoutDefaultRolls(GameTestHelper h) {
        var expected = Map.ofEntries(Map.entry("duke_mk_44", 4), Map.entry("gnawing_hunger", 4),
                Map.entry("bygones", 3), Map.entry("chattering_bone", 3), Map.entry("blast_furnace", 4),
                Map.entry("claws_of_the_wolf", 4), Map.entry("antiope_d", 3), Map.entry("lonesome", 4),
                Map.entry("dead_man_walking_xx7463", 4), Map.entry("apostate", 4), Map.entry("dust_rock_blues", 3),
                Map.entry("canis_major", 4), Map.entry("bad_omens", 4));
        check(h, KillClipProfile.rolls().size() == 13 && KillClipProfile.perk().multiplier() == 1.25f
                && KillClipProfile.perk().killWindowTicks() == 72 && KillClipProfile.perk().durationTicks() == 100,
                "Pinned W61 pool and explicit timing/damage contract");
        for (var e : WeaponCatalog.all()) {
            var s = item(e.id(), 0, 0); var before = s.copy();
            check(h, WeaponPerks.selected(s, KC).isEmpty(), "No default KC " + e.id());
            check(h, WeaponPerks.select(s, KC) == expected.containsKey(e.id()), "Exact release allowlist " + e.id());
            if (expected.containsKey(e.id())) {
                var r = WeaponPerks.selected(s, KC).orElseThrow();
                check(h, r.socket() == expected.get(e.id()) && r.hash() == WeaponCharacteristics.of(e).bungieHash()
                        && r.perkHash() == 1015611457L && r.plugSetHash() > 0, "Exact item, trait and socket " + e.id());
                if (e.id().equals("antiope_d")) check(h, r.plugSetHash() == 669, "Antiope fixed socket pool is supported");
                check(h, WeaponPerks.clear(s), "Selection clears");
            }
            check(h, ItemStack.matches(before, s), "Selection/clear preserves ammo, model, lore and all other components " + e.id());
        }
        var preview = WeaponModels.create(WeaponCatalog.find("bad_omens").orElseThrow());
        check(h, !WeaponPerks.select(preview, KC) && WeaponPerks.available(preview, KC).isEmpty(), "Preview cannot carry combat traits"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void sameSocketIsExclusiveAndDifferentOfficialSocketsCoexistInEitherEditOrder(GameTestHelper h) {
        var same = item("duke_mk_44", 4, 0);
        check(h, WeaponPerks.select(same) && WeaponPerks.select(same, KC), "Both official choices selectable");
        check(h, WeaponPerks.selected(same).isEmpty() && WeaponPerks.selected(same, KC).orElseThrow().socket() == 4,
                "KC replaces ALH in Duke socket 4");
        check(h, WeaponPerks.select(same) && WeaponPerks.selected(same, KC).isEmpty(), "Reverse edit replaces KC in same socket");
        for (String id : new String[]{"gnawing_hunger", "dust_rock_blues", "bad_omens"}) {
            for (boolean reverse : new boolean[]{false, true}) {
                var s = item(id, 1, 2); var before = s.copy();
                check(h, reverse ? WeaponPerks.select(s, KC) && WeaponPerks.select(s)
                        : WeaponPerks.select(s) && WeaponPerks.select(s, KC), "Both edit orders " + id);
                check(h, WeaponPerks.selected(s).orElseThrow().socket() != WeaponPerks.selected(s, KC).orElseThrow().socket(),
                        "Different official sockets remain selected " + id);
                check(h, WeaponPerks.clear(s) && ItemStack.matches(before, s), "Edits never mint ammo or replace the stack");
            }
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void legacyReadsArePureAndRealEditsMigrateOnlyRecognizedSelections(GameTestHelper h) {
        var s = item("bad_omens", 0, 3); legacy(s, WeaponPerks.HASH, 3); var before = s.copy();
        check(h, WeaponPerks.selected(s).isPresent() && WeaponPerks.selected(s, KC).isEmpty()
                && ItemStack.matches(before, s), "Legacy ALH is recognized without read migration");
        check(h, WeaponPerks.select(s, KC) && WeaponPerks.selected(s).isPresent() && WeaponPerks.selected(s, KC).isPresent(),
                "Real KC edit migrates legacy ALH and retains its separate socket");
        var tag = s.get(DataComponents.CUSTOM_DATA).copyTag();
        check(h, !tag.contains(WeaponPerks.HASH_KEY) && !tag.contains(WeaponPerks.SOCKET_KEY)
                && tag.get(WeaponPerks.SLOTS_KEY) instanceof CompoundTag, "Migration removes old pair only on edit");
        var kc = item("bad_omens", 0, 3); legacy(kc, KillClipProfile.HASH, 4); var saved = kc.copy();
        check(h, WeaponPerks.selected(kc, KC).isPresent() && ItemStack.matches(saved, kc), "Legacy KC read is also pure");
        check(h, WeaponPerks.select(kc) && WeaponPerks.selected(kc, KC).isPresent(), "Reverse migration retains legacy KC");
        var invalid = item("bad_omens", 0, 3); legacy(invalid, KillClipProfile.HASH, 63);
        check(h, WeaponPerks.select(invalid) && WeaponPerks.selected(invalid, KC).isEmpty(), "Unsupported old socket is not migrated"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void corruptHashesTypesAndModernSocketOverridesCannotResurrectLegacyTraits(GameTestHelper h) {
        var s = item("bad_omens", 1, 3); legacy(s, KillClipProfile.HASH, 4);
        var tag = s.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString(WeaponPerks.HASH_KEY, Long.toString(KillClipProfile.HASH)); data(s, tag);
        check(h, WeaponPerks.selected(s, KC).isEmpty(), "String hash is not a long");
        tag.putLong(WeaponPerks.HASH_KEY, KillClipProfile.HASH); tag.putDouble(WeaponPerks.SOCKET_KEY, 4); data(s, tag);
        check(h, WeaponPerks.selected(s, KC).isEmpty(), "Double socket is not an int");
        legacy(s, KillClipProfile.HASH, 4); tag = s.get(DataComponents.CUSTOM_DATA).copyTag();
        var slots = new CompoundTag(); slots.putLong("4", WeaponPerks.HASH); tag.put(WeaponPerks.SLOTS_KEY, slots); data(s, tag);
        check(h, WeaponPerks.selected(s, KC).isEmpty() && WeaponPerks.selected(s).isEmpty(), "Modern wrong hash masks old KC and cannot fake ALH in wrong socket");
        slots.putString("4", Long.toString(KillClipProfile.HASH)); tag.put(WeaponPerks.SLOTS_KEY, slots); data(s, tag);
        check(h, WeaponPerks.selected(s, KC).isEmpty(), "Malformed modern value cannot fall back to valid old pair");
        tag.putString(WeaponPerks.SLOTS_KEY, "corrupt"); data(s, tag); var before = s.copy();
        check(h, WeaponPerks.selected(s, KC).isEmpty() && ItemStack.matches(before, s), "Malformed container is inert and reads remain pure"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 210, environment = "destiny-test:w90_isolated")
    public void sourceKillThenCompletedManualReloadAddsExactlyTwentyFivePercentUntilExpiry(GameTestHelper h) {
        var p = player(h, 6.5); var gun = duke(h, p); kill(h, p);
        check(h, WeaponKillClip.remaining(p) == 0, "Kill alone never activates");
        int cadence = (int)Math.ceil(profile(gun).cadenceTicks()); int reload = profile(gun).firstReloadTicks();
        // Register the driver at test setup, not while the scheduler iterates a delayed callback.
        h.onEachTick(() -> WeaponRuntime.tickPlayer(p));
        float[] baseline = {0};
        int[] rounds = {0};
        int credit = 42;
        h.runAfterDelay(cadence, () -> {
            var victim = target(h, 8.5, 6.5, 1000); shot(h, p); baseline[0] = 1000 - victim.getHealth();
            check(h, baseline[0] > 0 && WeaponKillClip.remaining(p) == 0, "Actual pre-reload shot is unbuffed"); victim.discard();
            rounds[0] = ammo(gun).rounds(); check(h, WeaponRuntime.reload(p), "Actual timed reload accepted");
            check(h, ammo(gun).rounds() == rounds[0] && WeaponKillClip.remaining(p) == 0, "Starting reload transfers nothing and grants no buff");
        });
        h.runAfterDelay(cadence + credit - 1, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds()==rounds[0] && WeaponKillClip.remaining(p)==0, "No transfer or Kill Clip before credit42"); });
        h.runAfterDelay(cadence + credit, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds()==profile(gun).magazine() && WeaponKillClip.remaining(p)==100 && WeaponRuntime.reloading(p), "Actual credit42 activates once during recovery"); });
        h.runAfterDelay(cadence + reload - 1, () -> { WeaponRuntime.tickPlayer(p);
            check(h, WeaponRuntime.reloading(p) && ammo(gun).rounds() == profile(gun).magazine() && WeaponKillClip.remaining(p) == 100-(reload-1-credit), "Recovery retains credited ammo and correctly aging Kill Clip"); });
        h.runAfterDelay(cadence + reload, () -> {
            WeaponRuntime.tickPlayer(p); check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == profile(gun).magazine()
                    && WeaponKillClip.remaining(p) == 100-(reload-credit), "Full recovery does not restart the earlier credit-triggered buff");
            var buffed = target(h, 8.5, 6.5, 1000); shot(h, p);
            check(h, near(1000 - buffed.getHealth(), baseline[0] * 1.25f), "Actual observed body HP loss is exactly 25% larger"); buffed.discard();
        });
        h.runAfterDelay(cadence + credit + 99, () -> check(h, WeaponKillClip.remaining(p) == 1, "Last active tick measured from actual ammo credit"));
        h.runAfterDelay(cadence + credit + 100, () -> { var expired = target(h, 8.5, 6.5, 1000); shot(h, p);
            check(h, WeaponKillClip.remaining(p) == 0 && near(1000 - expired.getHealth(), baseline[0]), "Exact expiry returns actual damage to baseline"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void abilityKillNonlethalShotAndUnselectedWeaponNeverEarnKillClip(GameTestHelper h) {
        var p = player(h, 3.5); var gun = duke(h, p); var abilityVictim = target(h, 8.5, 3.5, 1);
        check(h, Combat.damage(p, abilityVictim, 100, Element.SOLAR) && abilityVictim.isDeadOrDying(), "Real ability-attributed final blow"); abilityVictim.discard();
        var tank = target(h, 8.5, 3.5, 1000); shot(h, p);
        check(h, tank.isAlive() && tank.getHealth() < 1000, "Weapon damage is real but nonlethal");
        check(h, WeaponRuntime.reloadFromMarksmanDodge(p) == 1 && WeaponKillClip.remaining(p) == 0, "Neither ability final blow nor nonlethal weapon hit arms KC");
        check(h, WeaponRuntime.reloadFromMarksmanDodge(p) == 0 && ammo(gun).rounds() == 9, "Full magazine is not another completed reload");
        var other = player(h, 11.5); equip(h, other, "duke_mk_44", 9, 0, false); kill(h, other);
        check(h, WeaponRuntime.reloadFromMarksmanDodge(other) == 1 && WeaponKillClip.remaining(other) == 0, "Allowed but unselected trait is inert"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void actualMarksmanAbilityCancelsPendingTimerAndActivatesOnlyAfterPaidReload(GameTestHelper h) {
        var p = player(h, 6.5); var gun = duke(h, p); kill(h, p);
        check(h, WeaponRuntime.reload(p) && WeaponKillClip.remaining(p) == 0, "Timed reload started without early activation");
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.OK, "Actual equipped Marksman Dodge accepted");
        check(h, ammo(gun).rounds() == 9 && !WeaponRuntime.reloading(p) && WeaponKillClip.remaining(p) == 100,
                "Ability actually moved the missing round and activated KC");
        int deadline = profile(gun).firstReloadTicks();
        h.runAfterDelay(deadline, () -> { WeaponRuntime.tickPlayer(p);
            check(h, ammo(gun).rounds() == 9 && WeaponRuntime.activeProjectiles(p) == 0
                    && WeaponKillClip.remaining(p) == 100 - deadline, "Cancelled old timer cannot refresh buff, duplicate reload or synthesize a shot"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void firstRealShotgunShellConsumesKillAndLaterShellsNeedAFreshKillToRefresh(GameTestHelper h) {
        var p = player(h, 6.5); var gun = equip(h, p, "dust_rock_blues", 1, 4, true); kill(h, p);
        check(h, WeaponRuntime.reload(p), "Actual incremental reload started"); int first = profile(gun).firstReloadTicks(); int interval = profile(gun).reloadTicks();
        h.runAfterDelay(first - 1, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 0 && WeaponKillClip.remaining(p) == 0, "No first shell or early buff"); });
        h.runAfterDelay(first, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 1 && ammo(gun).reserve() == 3
                && WeaponRuntime.reloading(p) && WeaponKillClip.remaining(p) == 100, "Authored first paid shell activates, not whole-magazine estimate"); });
        h.runAfterDelay(first + interval, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 2 && ammo(gun).reserve() == 2
                && WeaponKillClip.remaining(p) == 100 - interval, "Second real shell does not reuse consumed kill"); });
        h.runAfterDelay(first + 2 * interval, () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 3 && ammo(gun).reserve() == 1
                    && WeaponKillClip.remaining(p) == 100 - 2 * interval, "Third shell also cannot refresh");
            kill(h, p); check(h, WeaponRuntime.reload(p), "Fresh real kill followed by another actual reload");
        });
        h.runAfterDelay(2 * first + 2 * interval, () -> { WeaponRuntime.tickPlayer(p); check(h, ammo(gun).rounds() == 3 && ammo(gun).reserve() == 0
                && WeaponKillClip.remaining(p) == 100, "Fresh kill plus paid insert refreshes active buff"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void expiredPendingKillCannotActivateFromALaterActualReload(GameTestHelper h) {
        var p = player(h, 6.5); duke(h, p); kill(h, p);
        h.runAfterDelay(73, () -> {
            check(h, WeaponRuntime.reloadFromMarksmanDodge(p) == 1 && WeaponKillClip.remaining(p) == 0,
                    "Real reload after inclusive 72-tick pending window is too late"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void nativeSameTickStowAndReturnDropsBothPendingKillAndActiveBuff(GameTestHelper h) {
        var pending = player(h, 3.5); var a = duke(h, pending); kill(h, pending);
        var active = player(h, 11.5); var b = duke(h, active); kill(h, active);
        check(h, WeaponRuntime.reloadFromMarksmanDodge(active) == 1 && WeaponKillClip.remaining(active) == 100, "Second owner has an actual buff");
        for (var p : new ServerPlayer[]{pending, active}) {
            p.getInventory().setItem(7, new ItemStack(Items.STONE)); select(p, 7); select(p, 0); WeaponRuntime.tickPlayer(p);
            check(h, WeaponKillClip.remaining(p) == 0, "Away-and-back within one tick is observed through real slot packets");
        }
        check(h, pending.getMainHandItem() == a && active.getMainHandItem() == b, "Returned to original actual stacks");
        check(h, WeaponRuntime.reloadFromMarksmanDodge(pending) == 1 && WeaponKillClip.remaining(pending) == 0,
                "Authored pending-kill stow policy prevents delayed activation after return"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void identicalStackCopiesInheritNeitherPendingKillNorActiveDamageTime(GameTestHelper h) {
        var pending = player(h, 3.5); var a = duke(h, pending); kill(h, pending);
        var active = player(h, 11.5); var b = duke(h, active); kill(h, active); WeaponRuntime.reloadFromMarksmanDodge(active);
        var copyA = a.copy(); var copyB = b.copy();
        check(h, ItemStack.matches(a, copyA) && ItemStack.matches(b, copyB), "Component-identical replacements");
        pending.getInventory().setItem(0, copyA); active.getInventory().setItem(0, copyB);
        WeaponRuntime.tickPlayer(pending); WeaponRuntime.tickPlayer(active);
        check(h, WeaponKillClip.remaining(active) == 0 && WeaponRuntime.reloadFromMarksmanDodge(pending) == 1
                && WeaponKillClip.remaining(pending) == 0, "Session belongs to actual stack identity, never serialized perk/ammo equality");
        check(h, ammo(a).rounds() == 8 && ammo(copyA).rounds() == 9, "Replacement reload cannot mutate original stack"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void cleanupDeathAndSpectatorInvalidateOnlyTheirOwnersSession(GameTestHelper h) {
        var p = player(h, 3.5); duke(h, p); kill(h, p); WeaponRuntime.reloadFromMarksmanDodge(p);
        var other = player(h, 11.5); duke(h, other); kill(h, other); WeaponRuntime.reloadFromMarksmanDodge(other);
        WeaponRuntime.cleanup(p); WeaponRuntime.tickPlayer(p);
        check(h, WeaponKillClip.remaining(p) == 0 && WeaponKillClip.remaining(other) == 100, "Owner cleanup cannot erase another owner's buff or restore its own");
        other.setGameMode(GameType.SPECTATOR); WeaponRuntime.tickPlayer(other); other.setGameMode(GameType.SURVIVAL); WeaponRuntime.tickPlayer(other);
        check(h, WeaponKillClip.remaining(other) == 0, "Leaving spectator cannot recover old damage time");
        p.setHealth(0); WeaponRuntime.tickPlayer(p);
        check(h, WeaponKillClip.remaining(p) == 0 && WeaponRuntime.reloadFromMarksmanDodge(p) == 0, "Dead owner cannot reload into a session"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void emittedRocketKeepsBuffAfterStowButItsFinalBlowCannotCreditCurrentGun(GameTestHelper h) {
        var p = player(h, 3.5);
        record Impact(ItemStack source, ItemStack current, ServerPlayer control,
                      Husk victim, Husk tank, Husk plainVictim, Husk plainTank) {}
        var impact = new Impact[1];
        primedRocket(h, p);
        h.runAfterDelay(3 + 48, () -> {
            var source = p.getMainHandItem(); var current = item("duke_mk_44", 8, 0); WeaponPerks.select(current, KC); p.getInventory().setItem(0, current);
            var control = player(h, 9.5); equip(h, control, "bad_omens", 1, 3, false);
            var victim = target(h, 12.5, 3.5, 1); var tank = target(h, 12.5, 4.4, 1000);
            var plainVictim = target(h, 12.5, 9.5, 1); var plainTank = target(h, 12.5, 10.4, 1000);
            reaim(p); reaim(control); shot(h, p); shot(h, control); select(p, 0); WeaponRuntime.tickPlayer(p);
            check(h, WeaponKillClip.remaining(p) == 0 && WeaponRuntime.activeProjectiles(p) == 1, "Stow removes held buff without deleting emitted rocket");
            impact[0] = new Impact(source, current, control, victim, tank, plainVictim, plainTank);
        });
        h.runAfterDelay(3 + 48 + 6, () -> {
                var f = impact[0];
                var source = f.source(); var current = f.current(); var control = f.control();
                var victim = f.victim(); var tank = f.tank();
                var plainVictim = f.plainVictim(); var plainTank = f.plainTank();
                float base = 1000 - plainTank.getHealth();
                check(h, victim.isDeadOrDying() && plainVictim.isDeadOrDying() && base > 0
                        && near(1000 - tank.getHealth(), base * 1.25f), "Real splash HP retains emission-time 25% snapshot after stow: base="+base+", buffed="+(1000-tank.getHealth())
                                +", victims="+victim.getHealth()+"/"+plainVictim.getHealth()+", controlShots="+WeaponRuntime.activeProjectiles(control)
                                +", control="+control.position()+", tank="+plainTank.position()+", victim="+plainVictim.position()+", aim="+control.getYRot()+"/"+control.getXRot());
                check(h, WeaponRuntime.reloadFromMarksmanDodge(p) > 0 && ammo(current).rounds() == 9
                        && WeaponKillClip.remaining(p) == 0, "Actual reload of current KC gun cannot use another weapon's in-flight final blow");
                select(p, 2); WeaponRuntime.tickPlayer(p);
                check(h, p.getMainHandItem() == source && WeaponKillClip.remaining(p) == 0, "Returning source cannot revive retired session"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 150, environment = "destiny-test:w90_isolated")
    public void rocketEmittedOnLastBuffTickStillDealsSnapshotDamageAfterExpiry(GameTestHelper h) {
        var p = player(h, 3.5);
        record Impact(Husk buffed, Husk plain) {}
        var impact = new Impact[1];
        primedRocket(h, p);
        // The actual reserve transfer at tick3 above starts the pinned 100-tick buff.
        int lastActive = 3 + KillClipProfile.perk().durationTicks() - 1;
        h.runAfterDelay(lastActive, () -> {
            var control = player(h, 9.5); equip(h, control, "bad_omens", 1, 3, false);
            var buffed = target(h, 12.5, 3.5, 1000); var plain = target(h, 12.5, 9.5, 1000);
            check(h, WeaponKillClip.remaining(p) == 1, "Emitting on exact final active tick"); reaim(p); reaim(control); shot(h, p); shot(h, control);
            check(h, buffed.getHealth() == 1000 && WeaponRuntime.activeProjectiles(p) == 1, "Damage has not arrived at emission");
            impact[0] = new Impact(buffed, plain);
        });
        h.runAfterDelay(lastActive + 6, () -> {
                var buffed = impact[0].buffed(); var plain = impact[0].plain();
                float baseline = 1000 - plain.getHealth();
                check(h, WeaponKillClip.remaining(p) == 0 && baseline > 0 && near(1000 - buffed.getHealth(), baseline * 1.25f),
                        "Actual post-expiry impact retains 25% snapshot: remaining="+WeaponKillClip.remaining(p)+", base="+baseline+", buffed="+(1000-buffed.getHealth()));
                check(h, WeaponKillClip.capture(p).multiplier() == 1, "A newly emitted shot would have no expired bonus"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void actualHolsterFillAfterSourceKillCannotActivateOrRestoreStowedKillClip(GameTestHelper h) {
        var p = player(h, 6.5); var rocket = equip(h, p, "bad_omens", 1, 3, true); WeaponPerks.select(rocket);
        var victim = target(h, 5.5, 6.5, 1); shot(h, p);
        h.runAfterDelay(3, () -> {
            check(h, victim.isDeadOrDying(), "Actual KC source final blow"); victim.discard();
            p.getInventory().setItem(7, new ItemStack(Items.STONE)); select(p, 7); WeaponRuntime.tickPlayer(p);
        });
        h.runAfterDelay(3 + 70, () -> { WeaponRuntime.tickPlayer(p);
                check(h, ammo(rocket).rounds() == 1 && ammo(rocket).reserve() == 2, "Coexisting ALH actually paid finite reserve while stowed");
                select(p, 2); WeaponRuntime.tickPlayer(p);
                check(h, WeaponKillClip.remaining(p) == 0 && WeaponKillClip.capture(p).multiplier() == 1
                        && WeaponRuntime.activeProjectiles(p) == 0, "Holster fill cannot activate KC, resurrect pending kill, or fabricate a shot"); h.succeed();
        });
    }
}
