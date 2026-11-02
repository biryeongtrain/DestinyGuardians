package kim.biryeong.destiny.test;

import kim.biryeong.destiny.campaign.RisingLoadout;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.fallen.RisingFallen;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.tutorial.TutorialLoan;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundAttackPacket;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

public final class RisingBugsGameTests {
    private static void check(GameTestHelper h, boolean ok, String text) { h.assertTrue(ok, Component.literal(text)); }

    @GameTest(structure="destiny-test:floor", maxTicks=170, environment="destiny-test:w90_isolated")
    public void hungerHealingAndFractionalRecovery(GameTestHelper h) throws Exception {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        p.setHealth(5);
        var food = p.getFoodData();
        food.setFoodLevel(1); food.setSaturation(0);
        for (int i=0;i<200;i++) { food.addExhaustion(40); food.tick(p); }
        check(h, food.getFoodLevel()==20 && food.getSaturationLevel()==5, "Exhaustion cannot consume food");
        check(h, p.getHealth()==5, "Saturated food cannot naturally heal");
        // Activate the independent peaceful path, otherwise this assertion would be vacuous.
        var peaceful = net.minecraft.server.level.ServerPlayer.class.getDeclaredMethod("tickRegeneration");
        peaceful.setAccessible(true);
        var server = h.getLevel().getServer();
        var difficulty = h.getLevel().getDifficulty();
        check(h, h.getLevel().getGameRules().get(net.minecraft.world.level.gamerules.GameRules.NATURAL_HEALTH_REGENERATION),
                "Fixture enables vanilla natural regeneration");
        try {
            server.setDifficulty(net.minecraft.world.Difficulty.PEACEFUL, true);
            check(h, h.getLevel().getDifficulty()==net.minecraft.world.Difficulty.PEACEFUL, "Peaceful fixture is active");
            for (int i=0;i<80;i++) { p.tickCount=i; peaceful.invoke(p); }
        } finally { server.setDifficulty(difficulty, true); }
        check(h, p.getHealth()==5, "Peaceful regeneration cannot heal");
        p.heal(0.25f);
        check(h, p.getHealth()==5.25f, "Explicit ability healing remains fractional");
        p.setHealth(5);
        kim.biryeong.destiny.combat.GuardianRecovery.tick(p);
        h.runAfterDelay(34, () -> {
            kim.biryeong.destiny.combat.GuardianRecovery.tick(p);
            check(h, p.getHealth()==5, "No regeneration before health delay");
        });
        h.runAfterDelay(35, () -> {
            kim.biryeong.destiny.combat.GuardianRecovery.tick(p);
            check(h, Math.abs(p.getHealth()-5.10945f)<0.00001, "Server heals a fractional amount each tick");
            kim.biryeong.destiny.hud.CombatHud.update(p);
            var hud = kim.biryeong.minigamelib.displayhud.DisplayHud.getHud(p, kim.biryeong.destiny.hud.CombatHud.HEALTH_ID);
            p.heal(0.10945f);
            kim.biryeong.destiny.hud.CombatHud.update(p);
            check(h, Math.abs(hud.getScale().x - 424*p.getHealth()/p.getMaxHealth())<0.0001, "HUD retains fractional width");
            check(h, hud.getDisplay().getTransformationInterpolationDuration()==2, "Recovery transform interpolates");
            p.setInvulnerableTime(0);
            p.hurtServer(h.getLevel(), p.damageSources().generic(), 1);
            float after = p.getHealth();
            check(h, after < 5, "Real health damage applied");
            h.runAfterDelay(34, () -> {
                kim.biryeong.destiny.combat.GuardianRecovery.tick(p);
                check(h, p.getHealth()==after, "Real damage hook restarts delay");
            });
            h.runAfterDelay(35, () -> {
                kim.biryeong.destiny.combat.GuardianRecovery.tick(p);
                check(h, p.getHealth()>after && p.getHealth()<after+1, "Fractional recovery resumes");
                p.setGameMode(net.minecraft.world.level.GameType.SPECTATOR);
                float before = p.getHealth();
                kim.biryeong.destiny.combat.GuardianRecovery.tick(p);
                check(h, p.getHealth()==before, "Spectators cannot recover");
                h.succeed();
            });
        });
    }

    @GameTest(structure="destiny-test:floor", maxTicks=150, environment="destiny-test:w90_isolated")
    public void missionLoansEquipFireMigrateAndRestore(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        TestCleanup.register(h, () -> { TutorialLoan.restore(p); WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        p.getInventory().setItem(0, new ItemStack(Items.DIAMOND, 3));
        RisingLoadout.grantRifle(p);
        var rifle = p.getMainHandItem();
        check(h, p.getInventory().getSelectedSlot() == 0 && WeaponLoadout.canUse(p), "Khvostov loan uses kinetic equipment slot");
        RisingLoadout.grantShotgun(p);
        var shotgun = p.getMainHandItem();
        check(h, p.getInventory().getSelectedSlot() == 1 && WeaponLoadout.canUse(p), "Shotgun selected and usable");
        check(h, WeaponLoadout.equipped(p).size() == 2, "Both loan weapons are equipped");
        // Reproduce an old save with the two loans in the pre-fix swapped slots.
        p.getInventory().setItem(0, shotgun); p.getInventory().setItem(1, rifle);
        RisingLoadout.grantRifle(p); RisingLoadout.grantShotgun(p);
        check(h, p.getInventory().getItem(0) == rifle && p.getInventory().getItem(1) == shotgun, "Migration moves original references");
        var profile = WeaponProfile.forEntry(WeaponItems.entry(shotgun).orElseThrow());
        int before = WeaponItems.magazine(shotgun, profile).rounds();
        h.runAfterDelay(45, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, WeaponRuntime.beginUse(p), "Shotgun fires through real runtime");
            check(h, WeaponItems.magazine(shotgun, profile).rounds() == before - 1, "Shot consumes exactly one shell");
            WeaponRuntime.cancelUseForSkill(p);
            RisingLoadout.grantShotgun(p);
            check(h, p.getMainHandItem() == shotgun && WeaponItems.magazine(shotgun, profile).rounds() == before - 1, "Repeated grant cannot refill or duplicate");
            check(h, WeaponLoadout.select(p, WeaponSlot.KINETIC), "Rifle remains selectable");
            TutorialLoan.restore(p); TutorialLoan.restore(p);
            check(h, p.getInventory().getItem(0).is(Items.DIAMOND) && p.getInventory().getItem(0).getCount() == 3, "Original gear restored once");
            check(h, !TutorialLoan.active(p), "Loan escrow closed");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor", maxTicks=40, environment="destiny-test:w90_isolated")
    public void thirdPersonSelfAttackNeverDisconnects(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        TestCleanup.register(h, () -> { p.discard(); TestPlayers.remove(p); });
        h.getLevel().addNewPlayer(p);
        check(h, h.getLevel().getEntity(p.getId()) == p, "Real server self target exists");
        var state = Guardians.runtime(p);
        state.gcbClient = true; state.gcbThirdPerson = true;
        for (int i = 0; i < 5; i++) p.connection.handleAttack(new ServerboundAttackPacket(p.getId()));
        check(h, p.connection.isAcceptingMessages(), "Own rear-camera body hit remains connected");
        state.gcbThirdPerson = false;
        p.connection.handleAttack(new ServerboundAttackPacket(p.getId()));
        check(h, !p.connection.isAcceptingMessages(), "Ordinary invalid self attacks retain vanilla validation");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=40, environment="destiny-test:w90_isolated")
    public void captainBlinkRejectsWallsRoofsAndOccupiedDestinations(GameTestHelper h) throws Exception {
        // Materialize support: the 26.3 fixture does not reliably place floor.snbt's y=0.
        for (int x=0;x<10;x++) for (int z=0;z<8;z++) {
            h.setBlock(x,0,z,Blocks.STONE);
            for (int y=1;y<6;y++) h.setBlock(x,y,z,Blocks.AIR);
        }
        var from = h.absoluteVec(new Vec3(2.5, 1, 2.5));
        var mob = RisingFallen.instance().spawn(h.getLevel(), RisingServices.FallenKind.CAPTAIN, from, 0, null, null);
        TestCleanup.register(h, mob::discard);
        mob.setOnGround(true);
        var brainField = mob.getClass().getDeclaredField("brain"); brainField.setAccessible(true);
        var brain = brainField.get(mob);
        var method = brain.getClass().getDeclaredMethod("safeBlink", net.minecraft.server.level.ServerLevel.class, Vec3.class, Vec3.class);
        method.setAccessible(true);
        var spot = h.absoluteVec(new Vec3(6.5, 1, 2.5));
        check(h, (boolean)method.invoke(brain, h.getLevel(), from, spot), "Open connected floor remains a valid blink");
        for (int y=1;y<5;y++) for (int z=0;z<8;z++) h.setBlock(4,y,z,Blocks.STONE);
        check(h, !(boolean)method.invoke(brain, h.getLevel(), from, spot), "Cannot cross arena wall even if destination floor is safe");
        check(h, !(boolean)method.invoke(brain, h.getLevel(), from, from.add(0,2,0)), "Cannot climb onto roof");
        check(h, !(boolean)method.invoke(brain, h.getLevel(), from, from.add(40,0,0)), "Cannot leave home leash");
        h.succeed();
    }
}
