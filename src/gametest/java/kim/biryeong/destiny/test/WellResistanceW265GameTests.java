package kim.biryeong.destiny.test;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.ability.warlock.WarlockAbilities;
import kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.GuardianDamageSource;
import kim.biryeong.destiny.combat.SuperDamageResistance;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponItems;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.UUID;
import java.util.function.BiConsumer;

/** Real W230 Well cast/lifecycle plus the incoming modifier; no exhaustive health-loss matrix. */
public final class WellResistanceW265GameTests {
    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated",
            maxTicks = 80, skyAccess = true, manualOnly = true)
    public void wellResistanceOutlivesCastAndTracksMembershipAndCapturedAmmo(GameTestHelper h) {
        BiConsumer<Boolean, String> check = (ok, why) -> h.assertTrue(ok, Component.literal(why));
        for (int x = 0; x < 16; x++) for (int z = 0; z < 14; z++) h.setBlock(x, 0, z, Blocks.STONE);
        ServerPlayer[] players = new ServerPlayer[4];
        for (int i = 0; i < players.length; i++) {
            ServerPlayer p = TestPlayers.create(h, new Vec3(2.5 + i, 1, 6.5), -90, 0,
                    "W265" + UUID.randomUUID().toString().substring(0, 8));
            players[i] = p;
            TestCleanup.register(h, () -> { WarlockExpandedSupers.cleanup(p); TestPlayers.remove(p); });
            p.setNoGravity(true); p.setOnGround(true);
        }
        ServerPlayer owner = players[0], ally = players[1], enemy = players[2], attacker = players[3];
        var board = h.getLevel().getScoreboard();
        var team = board.addPlayerTeam("w265" + UUID.randomUUID().toString().substring(0, 8));
        TestCleanup.register(h, () -> board.removePlayerTeam(team));
        board.addPlayerToTeam(owner.getScoreboardName(), team);
        board.addPlayerToTeam(ally.getScoreboardName(), team);
        // Minimal W230 fixture: actual equipped cast, native rotation heartbeat, independent field tick.
        for (ServerPlayer p : new ServerPlayer[]{owner, ally}) {
            Guardians.data(p).setGuardianClass(GuardianClass.WARLOCK);
            Guardians.data(p).setLoadout(GuardianClass.WARLOCK, WarlockAbilities.preset(Element.SOLAR)
                    .with(AbilitySlot.SUPER, WarlockExpandedSupers.WELL_OF_RADIANCE));
            Guardians.runtime(p);
            Guardians.data(p).setSuperEnergy(1);
            check.accept(AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK,
                    "Actual equipped Well cast accepted");
        }
        h.onEachTick(() -> {
            for (ServerPlayer p : players) {
                TestPlayers.drain(p);
                if (AbilityService.inSuper(p)) {
                    int rotations = SuperCamera.rotations(p);
                    p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(
                            p.getYRot(), p.getXRot(), false, false));
                    check.accept(SuperCamera.active(p) && SuperCamera.rotations(p) == rotations + 1,
                            "W230 native rotation heartbeat retains cast camera");
                    AbilityService.tickPlayer(p);
                }
            }
            WarlockExpandedSupers.tick(h.getLevel().getServer());
        });
        h.runAfterDelay(48, () -> {
            for (ServerPlayer p : new ServerPlayer[]{owner, ally}) {
                check.accept(!AbilityService.inSuper(p) && !SuperCamera.active(p)
                                && Guardians.runtime(p).superSession == null,
                        "Cast session and camera have ended");
                check.accept(WarlockExpandedSupers.status(p).contains("well=true")
                                && WarlockExpandedSupers.inWell(p),
                        "Each independently cast field survives its session");
            }
            check.accept(!WarlockExpandedSupers.inWell(enemy), "Enemy inside both fields is excluded");
            var type = h.getLevel().registryAccess().lookupOrThrow(Registries.DAMAGE_TYPE).getOrThrow(
                    ResourceKey.create(Registries.DAMAGE_TYPE, DestinyGuardians.id("crucible")));
            var primaryEntry = WeaponCatalog.find("ace_of_spades").orElseThrow();
            var specialEntry = WeaponCatalog.find("beloved").orElseThrow();
            attacker.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(primaryEntry));
            var primary = new GuardianDamageSource(type, attacker, AmmoGeneration.weapon(primaryEntry));
            attacker.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(specialEntry));
            var special = new GuardianDamageSource(type, attacker, AmmoGeneration.weapon(specialEntry));
            check.accept(primary.kind() == AmmoGeneration.Kind.PRIMARY
                            && special.kind() == AmmoGeneration.Kind.SPECIAL,
                    "Paid source attribution captures distinct primary/special kinds");
            // At impact each source is checked while its attacker holds the opposite ammunition kind.
            check.accept(Math.abs(SuperDamageResistance.modifyIncoming(owner, primary, 10) - 6) < .001f
                            && Math.abs(SuperDamageResistance.modifyIncoming(ally, primary, 10) - 6) < .001f,
                    "Primary retains 40% reduction after special swap; overlapping Wells apply only once");
            attacker.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(primaryEntry));
            check.accept(special.kind() == AmmoGeneration.Kind.SPECIAL
                            && Math.abs(SuperDamageResistance.modifyIncoming(ally, special, 10) - 5) < .001f,
                    "Special retains 50% reduction after primary swap");
            check.accept(SuperDamageResistance.modifyIncoming(enemy, primary, 10) == 10
                            && SuperDamageResistance.modifyIncoming(enemy, special, 10) == 10,
                    "Neither captured PvP source protects an enemy in the field");
            var mob = EntityTypes.HUSK.create(h.getLevel(), net.minecraft.world.entity.EntitySpawnReason.COMMAND);
            check.accept(mob != null, "Control mob created");
            mob.setPos(h.absoluteVec(new Vec3(12.5, 1, 6.5)));
            check.accept(h.getLevel().addFreshEntity(mob), "Control mob added to actual world");
            TestCleanup.register(h, mob::discard);
            mob.setNoAi(true); mob.setNoGravity(true);
            var pve = mob.damageSources().mobAttack(mob);
            check.accept(Math.abs(SuperDamageResistance.modifyIncoming(owner, pve, 10) - 8) < .001f,
                    "Live Well applies 20% ordinary PvE reduction");
            mob.entityTags().add("destiny_boss");
            check.accept(Math.abs(SuperDamageResistance.modifyIncoming(owner, pve, 10) - 9) < .001f,
                    "Boss-tagged attacker receives the 10% boss branch");

            WarlockExpandedSupers.cleanup(ally);
            check.accept(WarlockExpandedSupers.inWell(ally)
                            && Math.abs(SuperDamageResistance.modifyIncoming(ally, primary, 10) - 6) < .001f,
                    "Removing one overlapping Well leaves exactly the owner's protection");
            ally.setPos(h.absoluteVec(new Vec3(7.49, 1, 6.5)));
            check.accept(WarlockExpandedSupers.inWell(ally), "Default radius 5 includes distance 4.99");
            ally.setPos(h.absoluteVec(new Vec3(7.51, 1, 6.5)));
            check.accept(!WarlockExpandedSupers.inWell(ally)
                            && SuperDamageResistance.modifyIncoming(ally, primary, 10) == 10,
                    "Crossing default radius 5 revokes resistance immediately without a field tick");
            ally.setPos(h.absoluteVec(new Vec3(3.5, 1, 6.5)));
            check.accept(WarlockExpandedSupers.inWell(ally)
                            && Math.abs(SuperDamageResistance.modifyIncoming(ally, primary, 10) - 6) < .001f,
                    "Re-entry restores membership before cleanup");
            WarlockExpandedSupers.cleanup(owner);
            for (ServerPlayer p : new ServerPlayer[]{owner, ally}) {
                check.accept(!WarlockExpandedSupers.inWell(p)
                                && SuperDamageResistance.modifyIncoming(p, primary, 10) == 10
                                && SuperDamageResistance.modifyIncoming(p, special, 10) == 10,
                        "Final owner cleanup revokes owner and ally resistance synchronously");
            }
            h.succeed();
        });
    }
}
