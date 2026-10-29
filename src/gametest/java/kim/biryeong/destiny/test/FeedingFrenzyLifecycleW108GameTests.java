package kim.biryeong.destiny.test;

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
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Additional W108 local lifecycle contracts, not sourced Destiny stow/reload rules.
 * Every positive proc comes from a paid production final blow; killed() calls only challenge
 * invalid/retired tokens. Existing W108 geometry and TestCleanup own all fixture resources.
 * Global WeaponRuntime/Tasks own ticking; no test advances gameplay clocks or projectiles.
 */
public final class FeedingFrenzyLifecycleW108GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String ENV = "destiny-test:w90_isolated";
    private static final String FF = "feeding_frenzy";
    private static final int CAPACITY = 41;
    private static final int DURATION = 70;
    private static final int BASE = 43;
    private static final int ONE_STACK = 40;
    private static final int BUILDING_SLOT = 7;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static WeaponCatalog.Entry entry(ItemStack gun) { return WeaponItems.entry(gun).orElseThrow(); }
    private static WeaponProfile profile(ItemStack gun) { return WeaponProfile.forEntry(entry(gun)); }
    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun, profile(gun)); }
    private static int slot(ItemStack gun) { return WeaponCharacteristics.of(entry(gun)).slot().hotbar(); }
    private static void state(GameTestHelper h, ServerPlayer p, int count, int left) {
        check(h, WeaponFeedingFrenzy.stacks(p) == count && WeaponFeedingFrenzy.remaining(p) == left,
                "Expected local x" + count + "/" + left + ", got x" + WeaponFeedingFrenzy.stacks(p)
                        + "/" + WeaponFeedingFrenzy.remaining(p));
    }
    private static void plan(GameTestHelper h, ServerPlayer p, ItemStack gun, int ticks) {
        check(h, p.getMainHandItem() == gun, "Reload query belongs to exact held source");
        var actual = WeaponFeedingFrenzy.plan(p, entry(gun), profile(gun));
        check(h, actual.firstTicks() == ticks && actual.intervalTicks() == ticks && !actual.incremental(),
                "Independent Recluse whole-magazine plan " + ticks + ", got " + actual);
    }
    private static void ammunition(GameTestHelper h, ItemStack gun, int rounds) {
        var actual = ammo(gun);
        check(h, actual.rounds() == rounds && actual.reserve() == 0 && actual.overflow() == 0,
                "Only paid shots change source ammunition; expected " + rounds + "/0/0");
    }
    private static void hud(GameTestHelper h, ServerPlayer p, int count, int seconds) {
        CombatHud.update(p);
        String prefix = WeaponPerkHud.PREFIX + "feeding_frenzy_";
        long nodes = DisplayHud.getHuds(p).keySet().stream().filter(k -> k.startsWith(prefix)).count();
        check(h, nodes == (count == 0 ? 0 : 8), "Hidden/expired local buff has no row; active row has eight nodes");
        if (count == 0) return;
        for (var glyph : List.of(new String[]{"label", "perk_feeding_frenzy_w108"},
                new String[]{"count", "ammo_digit_" + count},
                new String[]{"tens", "ammo_digit_" + seconds / 10},
                new String[]{"ones", "ammo_digit_" + seconds % 10})) {
            var node = DisplayHud.getHud(p, prefix + glyph[0]);
            check(h, node instanceof ItemDisplayHud item
                            && Identifier.parse("destiny:gui/hud/" + glyph[1]).equals(item.getItem().get(DataComponents.ITEM_MODEL)),
                    "Actual server HUD glyph " + glyph[0] + " = " + glyph[1]);
        }
    }
    private static void select(GameTestHelper h, ServerPlayer p, int index) {
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(index));
        WeaponRuntime.tickPlayer(p);
        check(h, p.getInventory().getSelectedSlot() == index, "Validated native hotbar selection applied");
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
        void bounded(Entity entity) {
            var o = h.absoluteVec(Vec3.ZERO); var b = entity.getBoundingBox();
            check(h, b.minX > o.x && b.maxX < o.x + 16 && b.minY > o.y && b.maxY < o.y + 8
                            && b.minZ > o.z && b.maxZ < o.z + 12,
                    "Whole fixture AABB inside existing committed 16x8x12 floor");
        }
        ServerPlayer player(double z) {
            var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0,
                    "W108L_" + UUID.randomUUID().toString().substring(0, 8));
            players.add(p);
            p.setAttached(WeaponLoadout.ENABLED, true); p.setNoGravity(true); p.setOnGround(true);
            bounded(p); return p;
        }
        ItemStack item() {
            var e = WeaponCatalog.find("the_recluse").orElseThrow(); var gun = WeaponItems.create(e);
            check(h, WeaponPerks.selected(gun, FF).isEmpty() && WeaponPerks.select(gun, FF),
                    "Explicitly select exact Recluse Feeding Frenzy source socket");
            check(h, profile(gun).magazine() == CAPACITY && profile(gun).firstReloadTicks() == BASE,
                    "Independent 41-round/43-tick Recluse fixture oracle");
            WeaponItems.save(gun, new WeaponMagazine(profile(gun), CAPACITY, 0)); return gun;
        }
        ItemStack equip(ServerPlayer p) {
            var gun = item(); p.getInventory().setItem(slot(gun), gun);
            p.getInventory().setSelectedSlot(slot(gun)); WeaponRuntime.tickPlayer(p); return gun;
        }
        void kill(ServerPlayer p, boolean head) {
            var gun = p.getMainHandItem(); var before = ammo(gun);
            var victim = h.spawn(EntityTypes.HUSK,
                    new Vec3(8.5, head ? 1 : 1.8, p.getZ() - h.absoluteVec(Vec3.ZERO).z));
            targets.add(victim); victim.setNoAi(true); victim.setNoGravity(true); victim.setPersistenceRequired();
            victim.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            victim.getAttribute(Attributes.ARMOR).setBaseValue(0);
            victim.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); victim.setHealth(1);
            bounded(victim);
            var b = victim.getBoundingBox(); double eye = p.getEyeY();
            check(h, head ? eye >= b.maxY - b.getYsize() * .25 && eye < b.maxY
                            : eye > b.minY && eye < b.maxY - b.getYsize() * .25,
                    "Existing W108 horizontal paid ray crosses real head/body geometry");
            WeaponAiming.cleanup(p); p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
            check(h, profile(gun).chargeTicks() == 0 && WeaponRuntime.beginUse(p), "Actual immediate trigger accepted");
            WeaponRuntime.releaseUse(p, gun);
            check(h, victim.isDeadOrDying() && victim.getHealth() == 0, "Actual production final blow, no injected positive credit");
            check(h, ammo(gun).rounds() == before.rounds() - 1 && ammo(gun).reserve() == before.reserve()
                            && ammo(gun).overflow() == before.overflow(), "Actual emission pays exactly one cartridge");
            victim.discard();
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = ENV)
    public void localStowHidesEarnedBuffAndReturnKeepsOriginalDeadlineThroughExpiry(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(6); var gun = f.equip(p);
        f.kill(p, false); state(h, p, 1, DURATION); plan(h, p, gun, ONE_STACK); hud(h, p, 1, 4);
        check(h, p.getInventory().getItem(BUILDING_SLOT).isEmpty(), "Empty building slot is not another trait source");
        select(h, p, BUILDING_SLOT); state(h, p, 0, 0); hud(h, p, 0, 0);
        check(h, p.getInventory().getItem(slot(gun)) == gun, "Stow retains exact source possession");
        h.runAfterDelay(20, () -> {
            select(h, p, slot(gun)); state(h, p, 1, 50); plan(h, p, gun, ONE_STACK); hud(h, p, 1, 3);
            for (int i = 0; i < 8; i++) {
                WeaponRuntime.tickPlayer(p); state(h, p, 1, 50); plan(h, p, gun, ONE_STACK); hud(h, p, 1, 3);
            }
            ammunition(h, gun, 40);
        });
        h.runAfterDelay(35, () -> {
            select(h, p, BUILDING_SLOT); state(h, p, 0, 0); hud(h, p, 0, 0);
        });
        h.runAfterDelay(69, () -> {
            select(h, p, slot(gun)); state(h, p, 1, 1); plan(h, p, gun, ONE_STACK); hud(h, p, 1, 1);
            select(h, p, BUILDING_SLOT); state(h, p, 0, 0); hud(h, p, 0, 0);
        });
        h.runAfterDelay(70, () -> {
            select(h, p, slot(gun)); state(h, p, 0, 0); plan(h, p, gun, BASE); hud(h, p, 0, 0);
            ammunition(h, gun, 40);
            check(h, !WeaponRuntime.reloading(p), "Stow/return/expiry never starts a reload");
        });
        h.runAfterDelay(71, () -> {
            select(h, p, BUILDING_SLOT); select(h, p, slot(gun));
            state(h, p, 0, 0); hud(h, p, 0, 0); ammunition(h, gun, 40); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = ENV)
    public void observedPossessionLossRetiresTokenEvenWhenExactSourceReturnsAndEarnsAgain(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(6); var gun = f.equip(p);
        f.kill(p, true); state(h, p, 1, DURATION); hud(h, p, 1, 4);
        var retired = WeaponFeedingFrenzy.capture(p);
        p.getInventory().setItem(slot(gun), ItemStack.EMPTY); WeaponRuntime.tickPlayer(p);
        WeaponFeedingFrenzy.killed(p, retired); state(h, p, 0, 0); hud(h, p, 0, 0);
        p.getInventory().setItem(slot(gun), gun); WeaponRuntime.tickPlayer(p);
        check(h, p.getMainHandItem() == gun, "Return the same actual source, not a component copy");
        WeaponFeedingFrenzy.killed(p, retired); state(h, p, 0, 0); plan(h, p, gun, BASE); hud(h, p, 0, 0);
        ammunition(h, gun, 40);
        int wait = (int) WeaponHandling.remaining(p) + 2;
        h.runAfterDelay(wait, () -> {
            f.kill(p, false); state(h, p, 1, DURATION); plan(h, p, gun, ONE_STACK); hud(h, p, 1, 4);
            ammunition(h, gun, 39);
            h.runAfterDelay(1, () -> {
                // A new live session now exists for the very same stack: rejection cannot be
                // explained by an absent map, an empty hand, or an ineligible owner.
                WeaponFeedingFrenzy.killed(p, retired); state(h, p, 1, 69);
                plan(h, p, gun, ONE_STACK); hud(h, p, 1, 4); ammunition(h, gun, 39); h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = ENV)
    public void exactSourceTransferCannotRewardEitherOwnerFromFormerOwnersLateToken(GameTestHelper h) {
        var f = new Fixture(h); var donor = f.player(3); var source = f.equip(donor);
        var control = f.player(6); var controlGun = f.equip(control); var recipient = f.player(9);
        f.kill(donor, false); f.kill(control, true);
        state(h, donor, 1, DURATION); state(h, control, 1, DURATION); hud(h, donor, 1, 4);
        var retired = WeaponFeedingFrenzy.capture(donor); var replacement = f.item();
        donor.getInventory().setItem(slot(source), replacement); WeaponRuntime.tickPlayer(donor);
        recipient.getInventory().setItem(slot(source), source);
        recipient.getInventory().setSelectedSlot(slot(source)); WeaponRuntime.tickPlayer(recipient);
        check(h, recipient.getMainHandItem() == source && donor.getMainHandItem() == replacement
                        && source != replacement, "Only recipient possesses exact transferred source; former owner holds selected replacement");
        // Bind a fresh recipient session before challenging the old token, so rejection is
        // tested even when its map already contains this exact source identity.
        WeaponFeedingFrenzy.capture(recipient);
        WeaponFeedingFrenzy.killed(donor, retired); WeaponFeedingFrenzy.killed(recipient, retired);
        state(h, donor, 0, 0); state(h, recipient, 0, 0); state(h, control, 1, DURATION);
        plan(h, donor, replacement, BASE); plan(h, recipient, source, BASE);
        hud(h, donor, 0, 0); hud(h, recipient, 0, 0); hud(h, control, 1, 4);
        ammunition(h, source, 40); ammunition(h, replacement, 41);
        int wait = (int) Math.max(WeaponHandling.remaining(donor), WeaponHandling.remaining(recipient)) + 2;
        check(h, wait + 1 < DURATION, "Real readiness wait leaves unrelated earned control buff alive");
        h.runAfterDelay(wait, () -> {
            f.kill(donor, true); f.kill(recipient, false);
            state(h, donor, 1, DURATION); state(h, recipient, 1, DURATION);
            state(h, control, 1, DURATION - wait);
            h.runAfterDelay(1, () -> {
                WeaponFeedingFrenzy.killed(donor, retired); WeaponFeedingFrenzy.killed(recipient, retired);
                state(h, donor, 1, 69); state(h, recipient, 1, 69); state(h, control, 1, DURATION - wait - 1);
                plan(h, donor, replacement, ONE_STACK); plan(h, recipient, source, ONE_STACK);
                hud(h, donor, 1, 4); hud(h, recipient, 1, 4);
                ammunition(h, source, 39); ammunition(h, replacement, 40); ammunition(h, controlGun, 40);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = ENV)
    public void deadAndSpectatorEligibilityRetireEarnedSessionsWithoutTouchingControl(GameTestHelper h) {
        var f = new Fixture(h); var dead = f.player(3); var deadGun = f.equip(dead);
        var control = f.player(6); var controlGun = f.equip(control);
        var spectator = f.player(9); var spectatorGun = f.equip(spectator);
        for (var p : List.of(dead, control, spectator)) {
            f.kill(p, false); state(h, p, 1, DURATION); hud(h, p, 1, 4);
        }
        var deadToken = WeaponFeedingFrenzy.capture(dead); var spectatorToken = WeaponFeedingFrenzy.capture(spectator);
        // Exercise tickPlayer's dead-owner guard without producing drops or claiming native
        // respawn/AFTER_DEATH coverage. Health restoration below is only a validity probe.
        dead.setHealth(0); spectator.setGameMode(GameType.SPECTATOR);
        check(h, dead.isDeadOrDying() && spectator.isSpectator(), "Both real eligibility predicates are false");
        WeaponRuntime.tickPlayer(dead); WeaponRuntime.tickPlayer(spectator);
        WeaponFeedingFrenzy.killed(dead, deadToken); WeaponFeedingFrenzy.killed(spectator, spectatorToken);
        state(h, dead, 0, 0); state(h, spectator, 0, 0); hud(h, dead, 0, 0); hud(h, spectator, 0, 0);
        dead.setHealth(dead.getMaxHealth()); spectator.setGameMode(GameType.SURVIVAL);
        WeaponRuntime.tickPlayer(dead); WeaponRuntime.tickPlayer(spectator);
        check(h, dead.isAlive() && !spectator.isSpectator() && dead.getMainHandItem() == deadGun
                        && spectator.getMainHandItem() == spectatorGun, "Re-eligible owners retain their exact source stacks");
        WeaponFeedingFrenzy.killed(dead, deadToken); WeaponFeedingFrenzy.killed(spectator, spectatorToken);
        state(h, dead, 0, 0); state(h, spectator, 0, 0); state(h, control, 1, DURATION);
        plan(h, dead, deadGun, BASE); plan(h, spectator, spectatorGun, BASE);
        hud(h, dead, 0, 0); hud(h, spectator, 0, 0); hud(h, control, 1, 4);
        int wait = (int) Math.max(WeaponHandling.remaining(dead), WeaponHandling.remaining(spectator)) + 2;
        check(h, wait + 1 < DURATION, "Eligibility recovery does not outwait the control buff");
        h.runAfterDelay(wait, () -> {
            f.kill(dead, true); f.kill(spectator, true);
            state(h, dead, 1, DURATION); state(h, spectator, 1, DURATION);
            h.runAfterDelay(1, () -> {
                WeaponFeedingFrenzy.killed(dead, deadToken); WeaponFeedingFrenzy.killed(spectator, spectatorToken);
                state(h, dead, 1, 69); state(h, spectator, 1, 69); state(h, control, 1, DURATION - wait - 1);
                plan(h, dead, deadGun, ONE_STACK); plan(h, spectator, spectatorGun, ONE_STACK);
                hud(h, dead, 1, 4); hud(h, spectator, 1, 4);
                ammunition(h, deadGun, 39); ammunition(h, spectatorGun, 39); ammunition(h, controlGun, 40);
                h.succeed();
            });
        });
    }
}
