package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.protocol.game.ClientboundLevelParticlesPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** W82 paid breach grenades on the W78 48x12x32 raised deck.
 * Default TWO_HAND input retains its six-tick (approximately .3 second) release approximation;
 * explicit NATIVE grip exercises precise release through the existing vanilla use session.
 * Only real END_SERVER_TICK advances shots, arming, leases and reloads. Native trail/ring packets
 * observe geometry; no reflected clocks/Shot construction, predicted ricochet or source-physics claim.
 * Register every timed/bounds callback during initialization; executing callbacks never mutate the
 * GameTest scheduler, including indirectly when late hostile witnesses are spawned.
 */
public final class WeaponBreachW82GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String SALVO = "salvager_s_salvo";
    private static final float HP = 1000, EPS = .004f;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static void fullHp(GameTestHelper h, LivingEntity target, String message) {
        check(h, Math.abs(target.getHealth() - HP) < EPS, message + "; HP=" + target.getHealth());
    }

    private static void damaged(GameTestHelper h, LivingEntity target, String message) {
        check(h, target.getHealth() < HP - EPS && target.getHealth() > 0,
                message + "; HP=" + target.getHealth());
    }

    private static void bounded(GameTestHelper h, Entity entity) {
        var o = h.absoluteVec(Vec3.ZERO);
        var b = entity.getBoundingBox();
        check(h, b.minX > o.x && b.maxX < o.x + 48 && b.minY > o.y && b.maxY < o.y + 12
                        && b.minZ > o.z && b.maxZ < o.z + 32,
                "Whole W82 entity AABB stays inside its 48x12x32 fixture: " + entity.getUUID());
    }

    private static ServerPlayer player(GameTestHelper h, Vec3 position, boolean worldObserver) {
        var p = TestPlayers.hunter(h, Element.ARC, position, -90, 0,
                "W82_" + UUID.randomUUID().toString().substring(0, 8));
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            p.stopUsingItem();
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            if (p.level().players().contains(p)) p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(p);
        });
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setNoGravity(true);
        p.setOnGround(true);
        if (worldObserver) h.getLevel().addNewPlayer(p);
        bounded(h, p);
        h.onEachTick(() -> bounded(h, p));
        return p;
    }

    private static Husk target(Fixture f, Vec3 position) {
        var h = f.h;
        var t = h.spawn(EntityTypes.HUSK, position);
        f.targets.add(t); // Bounds/cleanup callbacks were registered during fixture initialization.
        t.setNoAi(true);
        t.setNoGravity(true);
        t.setPersistenceRequired();
        t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        t.getAttribute(Attributes.ARMOR).setBaseValue(0);
        t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        t.setHealth(HP);
        bounded(h, t);
        return t;
    }

    private static WeaponProfile profile(ItemStack gun) {
        return WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
    }

    private static WeaponMagazine ammo(ItemStack gun) {
        return WeaponItems.magazine(gun, profile(gun));
    }

    private static ItemStack equip(ServerPlayer p, WeaponModels.Grip grip, int reserve) {
        var entry = WeaponCatalog.find(SALVO).orElseThrow();
        var gun = WeaponModels.withGrip(WeaponItems.create(entry), grip).orElseThrow();
        gun.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME, Component.literal("W82_" + UUID.randomUUID()));
        WeaponItems.save(gun, new WeaponMagazine(profile(gun), 1, reserve));
        int slot = WeaponCharacteristics.of(entry).slot().hotbar();
        p.getInventory().setItem(slot, gun);
        p.getInventory().setSelectedSlot(slot);
        WeaponRuntime.tickPlayer(p); // Initial bind only, before any accepted shot.
        TestPlayers.drain(p);
        return gun;
    }

    private static void flatten(Packet<?> packet, List<Packet<?>> out) {
        if (packet instanceof BundlePacket<?> bundle) for (var child : bundle.subPackets()) flatten(child, out);
        else out.add(packet);
    }

    /** Native output observation only. Particle spacing bounds endpoint uncertainty to .35 blocks.
     * A separate world-registered observer receives Fx packets; the shooter remains embedded like W78.
     */
    private static final class Scene {
        final GameTestHelper h;
        final ServerPlayer observer;
        final int rgb = WeaponCharacteristics.of(WeaponCatalog.find(SALVO).orElseThrow()).damage().color();
        Vec3 last, lastDirection;
        boolean reversed;
        int trailPackets, ringPackets;

        Scene(GameTestHelper h) {
            this.h = h;
            observer = player(h, new Vec3(23, 4, 8), true);
            TestPlayers.drain(observer);
            h.onEachTick(this::read);
        }

        void read() {
            var packets = new ArrayList<Packet<?>>();
            for (var packet : TestPlayers.outbound(observer)) flatten(packet, packets);
            for (var packet : packets) {
                if (!(packet instanceof ClientboundLevelParticlesPacket fx)
                        || !(fx.particle() instanceof DustParticleOptions dust)) continue;
                var local = h.relativeVec(new Vec3(fx.x(), fx.y(), fx.z()));
                if (local.x <= 0 || local.x >= 48 || local.y <= 0 || local.y >= 12
                        || local.z <= 0 || local.z >= 32) continue;
                var c = dust.getColor();
                boolean arc = Math.abs(c.x() - ((rgb >> 16) & 255) / 255f) < .001
                        && Math.abs(c.y() - ((rgb >> 8) & 255) / 255f) < .001
                        && Math.abs(c.z() - (rgb & 255) / 255f) < .001;
                if (arc && Math.abs(dust.getScale() - .7f) < .001 && Math.abs(local.z - 16) < .25) {
                    if (last != null && local.distanceToSqr(last) > 1.0e-6)
                        lastDirection = local.subtract(last).normalize();
                    if (last != null && local.x < last.x - .05) reversed = true;
                    last = local;
                    trailPackets++;
                }
                // Fx.ring currently emits size 1.2 (read from its native implementation).
                if (arc && Math.abs(dust.getScale() - 1.2f) < .001) ringPackets++;
            }
        }

        Vec3 point() {
            read();
            check(h, last != null && trailPackets > 0, "Native connection received the paid grenade's actual flight trail");
            return last;
        }

        void bouncedWithoutBlast() {
            read();
            check(h, reversed && ringPackets == 0,
                    "Actual native trail reverses at the stone wall while no explosion ring is sent");
        }
    }

    private record Fixture(GameTestHelper h, ServerPlayer owner, ItemStack gun, Scene scene, List<Husk> targets) {
        void live(String message) {
            scene.read();
            check(h, WeaponRuntime.activeProjectiles(owner) == 1 && scene.ringPackets == 0, message);
            check(h, ammo(gun).rounds() == 0, "Exactly one loaded round paid for this one active projectile");
        }

        void release() {
            WeaponRuntime.releaseUse(owner, gun);
            owner.stopUsingItem();
        }
    }

    private static Fixture fixture(GameTestHelper h, WeaponModels.Grip grip, int reserve) {
        exactAdmission(h);
        for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
        // Horizontal stone wall guarantees a real world-face ricochet before arming. The enclosing
        // room keeps later floor bounces/fallbacks in bounds; no restitution or exact bounce time assumed.
        for (int y = 4; y <= 10; y++) {
            for (int z = 12; z <= 20; z++) {
                h.setBlock(2, y, z, Blocks.STONE);
                h.setBlock(25, y, z, Blocks.STONE);
            }
            for (int x = 2; x <= 25; x++) {
                h.setBlock(x, y, 12, Blocks.STONE);
                h.setBlock(x, y, 20, Blocks.STONE);
            }
        }
        for (int x = 2; x <= 25; x++) for (int z = 12; z <= 20; z++) h.setBlock(x, 10, z, Blocks.STONE);
        var owner = player(h, new Vec3(20, 4, 16), false);
        var gun = equip(owner, grip, reserve);
        WeaponAccuracy.setAirborneBonus(gun, 100);
        var entry = WeaponItems.entry(gun).orElseThrow();
        check(h, BreachGrenade.supports(entry) && WeaponCharacteristics.of(entry).bungieHash() == 2060863616L
                        && profile(gun).mode() == WeaponProfile.Mode.PROJECTILE && profile(gun).chargeTicks() == 0
                        && profile(gun).magazine() == 1 && !profile(gun).infiniteReserve(),
                "Exact paid Salvager's Salvo 2060863616 Lightweight 474269988 fixture");
        check(h, WeaponModels.twoHanded(gun) == (grip == WeaponModels.Grip.TWO_HAND), "Explicit requested input branch");
        var targets = new ArrayList<Husk>();
        TestCleanup.register(h, () -> targets.forEach(Entity::discard));
        h.onEachTick(() -> targets.forEach(t -> bounded(h, t)));
        return new Fixture(h, owner, gun, new Scene(h), targets);
    }

    /** W241 exact-impact fixture: earn ADS on real ticks, with explicit per-stack AE.
     * No RNG replacement, production tuning change, or synthetic server clock. */
    private static void exactAim(GameTestHelper h, java.util.List<ServerPlayer> owners, Runnable action) {
        for (var p : owners) {
            var gun = p.getMainHandItem();
            check(h, kim.biryeong.destiny.weapon.WeaponAccuracy.airborne(WeaponItems.entry(gun).orElseThrow(), gun) == 100, "Fixture explicitly equips AE100");
            WeaponRuntime.tickPlayer(p);
            if (!WeaponAiming.requested(p)) check(h, WeaponAiming.toggle(p), "Real ADS toggle accepted");
        }
        // GameTestInfo executes sequences after iterating its fastutil callback map.
        // The final action may register follow-up deadlines, so it must run here.
        var sequence = h.startSequence();
        for (int tick = 1; tick <= 40; tick++) {
            final int age = tick;
            sequence.thenExecuteAfter(1, () -> {
                for (var p : owners) {
                    WeaponRuntime.tickPlayer(p);
                    // Initial handling can consume ADS. A later actual click earns it after ready.
                    if (!WeaponAiming.requested(p) && age % 4 == 0) WeaponAiming.toggle(p);
                }
                if (age == 40) {
                    for (var p : owners) check(h, WeaponAiming.progress(p) == 1
                                    && WeaponAiming.coneDegrees(p) == 0,
                            "Fully earned ADS and AE100 give an exact ray before any paid shot");
                    action.run();
                }
            });
        }
    }

    private static void launch(Fixture f, boolean heartbeat) {
        check(f.h, WeaponAiming.progress(f.owner) == 1 && WeaponAiming.coneDegrees(f.owner) == 0, "Exact earned ADS launch lane");
        f.owner.setYRot(-90);
        f.owner.setYHeadRot(-90);
        f.owner.setXRot(0);
        WeaponAiming.tick(f.owner);
        var before = ammo(f.gun);
        check(f.h, WeaponRuntime.beginUse(f.owner), "Real beginUse accepts the paid breach grenade");
        if (heartbeat) check(f.h, WeaponRuntime.heartbeatUse(f.owner), "Default crossbow input owns a six-tick lease");
        else {
            f.owner.startUsingItem(InteractionHand.MAIN_HAND);
            check(f.h, f.owner.isUsingItem() && f.owner.getUseItem() == f.gun,
                    "Explicit NATIVE grip keeps the exact accepted stack's vanilla use session alive");
        }
        check(f.h, ammo(f.gun).rounds() == before.rounds() - 1 && ammo(f.gun).reserve() == before.reserve(),
                "Acceptance spends one loaded round and no reserve");
        f.live("One paid shot exists before any END tick advances it");
    }

    private static void damagePacket(GameTestHelper h, ServerPlayer owner) {
        var packets = new ArrayList<Packet<?>>();
        for (var packet : TestPlayers.outbound(owner)) flatten(packet, packets);
        boolean spawned = packets.stream().anyMatch(p -> p instanceof ClientboundAddEntityPacket add
                && add.getType() == EntityTypes.TEXT_DISPLAY);
        if (!spawned) {
            // Preserve the immediate packet assertion. Diagnose whether confirmation was rejected,
            // the native output had another shape, or the connection became ineligible; never add
            // a second cosmetic confirm or quietly defer the check to make an absent spawn pass.
            String raw = packets.stream().map(p -> p instanceof ClientboundAddEntityPacket add
                    ? p.getClass().getSimpleName() + "[id=" + add.getId() + ",type=" + add.getType() + "]"
                    : p.getClass().getSimpleName()).toList().toString();
            int active = kim.biryeong.destiny.fx.WeaponDamageNumbers.active(owner);
            String diagnostic = "W82 missing damage spawn: testTick=" + h.getTick()
                    + ",serverTick=" + h.getLevel().getServer().getTickCount() + ",owner=" + owner.getUUID()
                    + ",activeNumbers=" + active + ",alive=" + owner.isAlive() + ",removed=" + owner.isRemoved()
                    + ",spectator=" + owner.isSpectator() + ",changingDimension=" + owner.isChangingDimension()
                    + ",disconnected=" + owner.hasDisconnected() + ",accepting=" + owner.connection.isAcceptingMessages()
                    + ",sameConnectionOwner=" + (owner.connection.getPlayer() == owner)
                    + ",sameLevel=" + (owner.level() == h.getLevel()) + ",packets=" + raw;
            System.out.println(diagnostic);
            check(h, false, "Actual owner connection receives native damage-number spawn after real HP loss; " + diagnostic);
        }
    }

    private record BlastWitnesses(Husk near, Husk blocked) {}

    private static BlastWitnesses blastWitnesses(Fixture f) {
        var point = f.scene.point();
        // Observe, then put witnesses beside the CURRENT projectile; neither can intercept its X flight.
        // All x columns are shielded so line of sight cannot sneak round the ends of this local wall.
        for (int x = 3; x < 25; x++) for (int y = 4; y < 10; y++) f.h.setBlock(x, y, 15, Blocks.STONE);
        var near = target(f, new Vec3(point.x, 4, 17.5));
        var blocked = target(f, new Vec3(point.x, 4, 14));
        var origin = f.h.absoluteVec(point);
        for (var t : new Husk[]{near, blocked}) {
            check(f.h, Combat.isEnemy(f.owner, t) && f.h.getLevel().noCollision(t, t.getBoundingBox()),
                    "Hostile blast witness has a clear native entity box");
            check(f.h, origin.distanceTo(t.getBoundingBox().getCenter()) < profile(f.gun).blastRadius() - .4,
                    "Both witnesses fit inside radial range with native trail-spacing margin");
        }
        var occlusion = f.h.getLevel().clip(new ClipContext(origin, blocked.getBoundingBox().getCenter(),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, f.owner));
        check(f.h, occlusion.getType() == HitResult.Type.BLOCK, "Stone truly occludes the within-radius negative witness");
        return new BlastWitnesses(near, blocked);
    }

    private static void exploded(Fixture f, BlastWitnesses witnesses) {
        f.scene.read();
        check(f.h, WeaponRuntime.activeProjectiles(f.owner) == 0 && f.scene.ringPackets > 0,
                "Real END tick retires the paid projectile and emits native radial-blast packets");
        damaged(f.h, witnesses.near, "Nearby off-flight hostile takes radial HP damage");
        fullHp(f.h, witnesses.blocked, "Within-radius hostile behind stone stays unharmed");
        check(f.h, ammo(f.gun).rounds() == 0, "Remote detonation never spends a second round");
        damagePacket(f.h, f.owner);
    }

    @GameTest(structure = FLOOR, maxTicks = 125, environment = "destiny-test:w90_isolated")
    public void defaultTwoHandHoldBouncesAndSixTickReleaseApproximationBlastsOnlyVisibleHostile(GameTestHelper h) {
        var f = fixture(h, WeaponModels.Grip.TWO_HAND, 0);
        check(h, WeaponModels.defaultGrip(WeaponItems.entry(f.gun).orElseThrow()) == WeaponModels.Grip.TWO_HAND
                        && WeaponRuntime.HEARTBEAT_LEASE_TICKS == 6,
                "Existing default crossbow grip and six ticks (~.3s at 20Hz) remain the release approximation");
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, true);
            int lastBeat = ((BreachGrenade.ARM_TICKS + 7) / 4) * 4;
            int started = h.getLevel().getServer().getTickCount();
            for (int delay = 1; delay <= lastBeat + 5; delay++) {
                int age = delay;
                h.runAfterDelay(age, () -> {
                    f.live("Maintained/five-tick-unexpired default lease does not explode");
                    if (age <= lastBeat && age % 4 == 0)
                        check(h, WeaponRuntime.heartbeatUse(f.owner), "Real four-tick default heartbeat renews this same paid grenade");
                    if (age >= BreachGrenade.ARM_TICKS + 1) f.scene.bouncedWithoutBlast();
                    check(h, ammo(f.gun).reserve() == 0, "Heartbeats neither refill nor spend reserve");
                });
            }
            var witnesses = new BlastWitnesses[1];
            h.runAfterDelay(lastBeat + 6, () -> {
                check(h, h.getLevel().getServer().getTickCount() - started == lastBeat + 6,
                        "Six REAL server ticks elapsed since the last accepted heartbeat");
                f.live("Before this tick's END, expired lease has not yet requested the blast");
                witnesses[0] = blastWitnesses(f);
            });
            h.runAfterDelay(lastBeat + 7, () -> {
                exploded(f, witnesses[0]);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 105, environment = "destiny-test:w90_isolated")
    public void explicitNativeGripValidReleaseAfterPublicArmTicksBlastsOnNextEndTick(GameTestHelper h) {
        var f = fixture(h, WeaponModels.Grip.NATIVE, 0);
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, false);
            var witnesses = new BlastWitnesses[1];
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 2, () -> {
                f.live("Native keepalive holds an armed grenade across actual world impact");
                f.scene.bouncedWithoutBlast();
                witnesses[0] = blastWitnesses(f);
                f.release();
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 1, "Release requests detonation; END owns damage/removal");
                fullHp(h, witnesses[0].near, "No synchronous release callback damage");
            });
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 3, () -> {
                exploded(f, witnesses[0]);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void directHostileCollisionExplodesEvenWhileDefaultInputIsHeld(GameTestHelper h) {
        var f = fixture(h, WeaponModels.Grip.TWO_HAND, 0);
        var direct = target(f, new Vec3(23.6, 4.4, 16));
        var side = target(f, new Vec3(23.6, 4, 17.5));
        check(h, direct.getBoundingBox().clip(f.owner.getEyePosition(), f.owner.getEyePosition().add(5, 0, 0)).isPresent(),
                "Actual launch eye ray crosses the direct hostile before the wall");
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, true);
            fullHp(h, direct, "Accepted flight does not synchronously damage the direct hostile");
            h.runAfterDelay(4, () -> {
                f.scene.read();
                damaged(h, direct, "Direct hostile collision detonates before trigger release/arming");
                damaged(h, side, "Held direct impact also produces real off-axis radial damage");
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0 && f.scene.ringPackets > 0,
                        "Direct impact removes the projectile before the still-valid six-tick lease expires");
                check(h, ammo(f.gun).rounds() == 0 && ammo(f.gun).reserve() == 0, "Direct impact preserves the single payment");
                damagePacket(h, f.owner);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 175, environment = "destiny-test:w90_isolated")
    public void nativeEarlyReleaseIsConsumedWithoutQueuedArmBlastAndNaturalFallbackStillExplodes(GameTestHelper h) {
        var f = fixture(h, WeaponModels.Grip.NATIVE, 0);
        var witness = target(f, new Vec3(20, 4, 24));
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, false);
            // Exactly age zero, independent of any future policy change to ARM_TICKS.
            check(h, BreachGrenade.ARM_TICKS > 0, "Public arming policy has a real early-release interval");
            f.release();
            boolean[] follow = {false};
            h.onEachTick(() -> {
                f.scene.read();
                if (follow[0] && f.scene.last != null && WeaponRuntime.activeProjectiles(f.owner) == 1) {
                    var p = f.scene.point();
                    witness.setPos(h.absoluteVec(new Vec3(p.x, 4, 17.5)));
                }
            });
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 4, () -> {
                f.live("Early release stays alive AFTER arming; it was not queued for later remote detonation");
                f.scene.bouncedWithoutBlast();
                fullHp(h, witness, "Early release causes no premature HP damage");
                follow[0] = true;
            });
            h.runAfterDelay(110, () -> {
                f.scene.read();
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0 && f.scene.ringPackets > 0,
                        "Detached early-release grenade still detonates at a bounded natural fuse/range/bounce fallback");
                damaged(h, witness, "Natural fallback retains a real paid radial HP transaction");
                damagePacket(h, f.owner);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 95, environment = "destiny-test:w90_isolated")
    public void defaultLeaseExpiryBeforeArmingDoesNotQueueARemoteBlast(GameTestHelper h) {
        var f = fixture(h, WeaponModels.Grip.TWO_HAND, 0);
        check(h, BreachGrenade.ARM_TICKS > WeaponRuntime.HEARTBEAT_LEASE_TICKS,
                "Current public arming policy admits an early six-tick default-lease expiry");
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, true);
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 4, () -> {
                f.live("One unrenewed default lease expires early and does not remotely explode on later arming");
                f.scene.bouncedWithoutBlast();
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 245, environment = "destiny-test:w90_isolated")
    public void heldEmptyMagazineDefersAutomaticReloadUntilRemoteReleaseThenLoadsOnce(GameTestHelper h) {
        var f = fixture(h, WeaponModels.Grip.NATIVE, 3);
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, false);
            int releaseAt = BreachGrenade.ARM_TICKS + 3;
            for (int age = 1; age <= releaseAt; age++) h.runAfterDelay(age, () -> {
                f.live("Held remote keeps its empty automatic-reload candidate deferred");
                check(h, !WeaponRuntime.reloading(f.owner) && ammo(f.gun).reserve() == 3,
                        "Empty held grenade does not start a reload timer or consume reserve");
            });
            int reloadTicks = profile(f.gun).reloadTicks();
            h.runAfterDelay(releaseAt + 1, f::release);
            h.runAfterDelay(releaseAt + 3, () -> {
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0 && WeaponRuntime.reloading(f.owner)
                                && ammo(f.gun).rounds() == 0 && ammo(f.gun).reserve() == 3,
                        "After remote retirement, actual END progression starts reload before ammo insertion");
            });
            h.runAfterDelay(releaseAt + reloadTicks + 5, () -> {
                check(h, !WeaponRuntime.reloading(f.owner) && ammo(f.gun).rounds() == 1 && ammo(f.gun).reserve() == 2
                                && WeaponRuntime.activeProjectiles(f.owner) == 0,
                        "Deferred reload finishes once, transfers one reserve and never fires a latent replacement shot");
                h.succeed();
            });
        });
    }

    private enum Cancellation { MANUAL_RELOAD, SKILL, SWAP, REMOVE_STACK }

    private static void cancelled(GameTestHelper h, Cancellation how) {
        var f = fixture(h, WeaponModels.Grip.NATIVE, how == Cancellation.MANUAL_RELOAD ? 3 : 0);
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, false);
            var direct = new Husk[1];
            var placedFrom = new Vec3[1];
            var observedDirection = new Vec3[1];
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 2, () -> {
                f.live("Cancellation fixture really has an armed paid grenade");
                f.scene.bouncedWithoutBlast();
                switch (how) {
                    case MANUAL_RELOAD -> check(h, WeaponRuntime.reload(f.owner), "Real manual reload accepted while remote holds empty magazine");
                    case SKILL -> WeaponRuntime.cancelUseForSkill(f.owner);
                    case SWAP -> {
                        int slot = f.owner.getInventory().getSelectedSlot();
                        f.owner.getInventory().setSelectedSlot((slot + 1) % 9);
                    }
                    case REMOVE_STACK -> f.owner.getInventory().setItem(f.owner.getInventory().getSelectedSlot(), ItemStack.EMPTY);
                }
                f.owner.stopUsingItem();
            });
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 4, () -> {
                WeaponRuntime.releaseUse(f.owner, f.gun); // Stale original release cannot turn cancellation into detonation.
                f.live("Manual reload/skill/swap/removal detaches control, preserving the already-launched grenade");
            });
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 6, () -> {
                f.live("Stale armed release leaves no queued remote explosion after cancellation");
                var p = f.scene.point();
                var direction = f.scene.lastDirection;
                check(h, direction != null && direction.x < -.8,
                        "Actual native trail still advances away from the wall before placing the collision witness");
                placedFrom[0] = p;
                observedDirection[0] = direction;
                // AABB.clip is an ENTRY query, so spawning around the current ray start can
                // produce no hit even when the shot leaves that box. Place the hostile ahead
                // of the observed flight, clear of the full .35-block endpoint uncertainty.
                var ahead = p.add(direction);
                direct[0] = target(f, new Vec3(ahead.x, Math.max(4, ahead.y - .5), ahead.z));
                var from = h.absoluteVec(p);
                var to = from.add(direction.scale(2));
                var box = direct[0].getBoundingBox().inflate(.08);
                check(h, !box.contains(from) && !box.contains(from.add(direction.scale(.35)))
                                && box.clip(from, to).isPresent() && h.getLevel().noCollision(direct[0], direct[0].getBoundingBox()),
                        "Observed flight starts OUTSIDE the hostile's inflated AABB and has a clear entry ahead");
                var entry = ProjectileUtil.getEntityHitResult(h.getLevel(), f.owner, from, to,
                        new AABB(from, to).inflate(.28), entity -> entity == direct[0], .08f);
                check(h, entry != null && entry.getEntity() == direct[0],
                        "Read-only native swept-entity preflight finds this real spawned hostile, without advancing a Shot");
                var wall = h.getLevel().clip(new ClipContext(from, entry.getLocation(),
                        ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, f.owner));
                check(h, wall.getType() == HitResult.Type.MISS,
                        "World geometry does not shield the ahead-of-flight direct-collision witness");
            });
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 8, () -> {
                f.scene.read();
                damaged(h, direct[0], "Cancelled remote's launched grenade still collides and explodes naturally"
                        + "; placedFrom=" + placedFrom[0] + ",observedDirection=" + observedDirection[0] + ",latestTrail=" + f.scene.last
                        + ",active=" + WeaponRuntime.activeProjectiles(f.owner) + ",rings=" + f.scene.ringPackets);
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0 && f.scene.ringPackets > 0,
                        "Natural collision retires the detached paid projectile without needing a remote pointer");
                damagePacket(h, f.owner);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void manualReloadDetachesRemoteWithoutExplosionAndLaunchedGrenadeStillHits(GameTestHelper h) {
        cancelled(h, Cancellation.MANUAL_RELOAD);
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void skillCancellationDetachesRemoteWithoutExplosionAndLaunchedGrenadeStillHits(GameTestHelper h) {
        cancelled(h, Cancellation.SKILL);
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void swappingSelectedSlotDetachesRemoteAndStaleReleaseCannotExplodeIt(GameTestHelper h) {
        cancelled(h, Cancellation.SWAP);
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void removingExactStackReferenceDetachesRemoteAndStaleReleaseCannotExplodeIt(GameTestHelper h) {
        cancelled(h, Cancellation.REMOVE_STACK);
    }

    @GameTest(structure = FLOOR, maxTicks = 105, environment = "destiny-test:w90_isolated")
    public void copiedStackAndDifferentOwnerCannotReleaseOriginalOwnersArmedGrenade(GameTestHelper h) {
        var f = fixture(h, WeaponModels.Grip.NATIVE, 0);
        var other = player(h, new Vec3(20, 4, 24), false);
        equip(other, WeaponModels.Grip.NATIVE, 0);
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, false);
            var witnesses = new BlastWitnesses[1];
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 2, () -> {
                WeaponRuntime.releaseUse(f.owner, f.gun.copy());
                WeaponRuntime.releaseUse(other, f.gun);
            });
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 4, () -> {
                f.live("Equal-data copied stack and another owner cannot request or consume the original release");
                witnesses[0] = blastWitnesses(f);
                f.release();
            });
            h.runAfterDelay(BreachGrenade.ARM_TICKS + 5, () -> {
                exploded(f, witnesses[0]);
                h.succeed();
            });
        });
    }

    private static void exactAdmission(GameTestHelper h) {
        var selected = WeaponCatalog.find(SALVO).orElseThrow();
        check(h, BreachGrenade.WEAPON_HASH == 2060863616L && BreachGrenade.INTRINSIC_HASH == 474269988L
                        && BreachGrenade.supports(selected), "Pinned Salvager's Salvo / Lightweight intrinsic admission");
        for (var entry : WeaponCatalog.all()) check(h, BreachGrenade.supports(entry) == entry.equals(selected),
                "No frame-wide or family-wide remote admission: " + entry.id());
        for (String id : new String[]{"deafening_whisper", "dimensional_hypotrochoid", "edge_transit"}) {
            var entry = WeaponCatalog.find(id).orElseThrow();
            check(h, !BreachGrenade.supports(entry), "Existing wave/heavy GL remains outside W82: " + id);
        }
        check(h, WaveFrameProfile.of(WeaponCatalog.find("deafening_whisper").orElseThrow()).isPresent()
                        && WaveFrameProfile.of(WeaponCatalog.find("dimensional_hypotrochoid").orElseThrow()).isPresent()
                        && WaveFrameProfile.of(selected).isEmpty(), "W78 wave identities retain their own runtime path");
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void realNonGuardianDoubleOffhandSwapRetiresRemoteEvenWhenExactStackReturnsBeforeEnd(GameTestHelper h) {
        var f = fixture(h, WeaponModels.Grip.TWO_HAND, 0);
        Guardians.data(f.owner).setGuardianClass(GuardianClass.NONE);
        f.owner.setAttached(WeaponLoadout.ENABLED, false); // Ordinary standalone branch, before accepting any shot.
        f.owner.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.STONE));
        exactAim(h, java.util.List.of(f.owner), () -> {
            launch(f, true);
            int swapAt = ((BreachGrenade.ARM_TICKS + 3) / 4) * 4;
            for (int delay = 4; delay <= swapAt; delay += 4) {
                int age = delay;
                h.runAfterDelay(age, () -> {
                    f.live("Four-tick default heartbeats retain the original paid projectile before packet swap");
                    check(h, WeaponRuntime.heartbeatUse(f.owner), "Actual default heartbeat keeps an armed remote through swap tick");
                    if (age != swapAt) return;
                    f.scene.bouncedWithoutBlast();
                    int tick = h.getLevel().getServer().getTickCount();
                    f.owner.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                            ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
                    check(h, f.owner.getOffhandItem() == f.gun && f.owner.getMainHandItem().is(Items.STONE),
                            "First real non-Guardian packet moves the exact accepted stack into offhand");
                    f.owner.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                            ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
                    check(h, h.getLevel().getServer().getTickCount() == tick && f.owner.getMainHandItem() == f.gun
                                    && f.owner.getOffhandItem().is(Items.STONE),
                            "Second real packet returns the exact stack in the SAME tick before END identity polling");
                    f.live("Offhand round trip cancels remote input without deleting/exploding the launched grenade");
                });
            }
            // No heartbeat or release after the two packets. At default ARM_TICKS=10 these are T+18
            // and T+19: the latter observes the END of the old six-tick lease, not just its pre-END state.
            h.runAfterDelay(swapAt + WeaponRuntime.HEARTBEAT_LEASE_TICKS, () -> {
                f.live("Returned exact stack has no remote release at the old lease deadline");
                check(h, ammo(f.gun).reserve() == 0, "Offhand packets preserve paid ammo/reserve");
            });
            h.runAfterDelay(swapAt + WeaponRuntime.HEARTBEAT_LEASE_TICKS + 1, () -> {
                f.live("AFTER the old lease's END, detached projectile remains naturally in flight with no remote blast");
                check(h, f.owner.getMainHandItem() == f.gun && ammo(f.gun).rounds() == 0 && ammo(f.gun).reserve() == 0,
                        "Same exact returned stack retains the single original payment and no hidden replacement shot");
                h.succeed();
            });
        });
    }
}
