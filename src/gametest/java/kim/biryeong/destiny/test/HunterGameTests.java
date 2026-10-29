package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.input.InputRouter;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.phys.Vec3;

/** 헌터 기능 GameTest (docs/design/13). 플레이어는 (2,1,6)에서 +x(동쪽)를 본다. */
public final class HunterGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Vec3 PLAYER_POS = new Vec3(2.5, 1, 6.5);
    private static final Input JUMP = new Input(false, false, false, false, true, false, false);
    private static final Input SHIFT = new Input(false, false, false, false, false, true, false);

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static Husk husk(GameTestHelper h, double x, double z) {
        Husk husk = h.spawn(EntityTypes.HUSK, new Vec3(x, 1, z));
        husk.setNoAi(true);
        husk.setPersistenceRequired();
        return husk;
    }

    private static ServerPlayer hunter(GameTestHelper h, Element element, float pitch) {
        return TestPlayers.hunter(h, element, PLAYER_POS, -90f, pitch);
    }

    // ---------- 이동 ----------

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void airJumpOnlyOnceAndResetsOnGround(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        try {
            GuardianRuntime rt = Guardians.runtime(p);
            p.setOnGround(true);
            InputRouter.onPlayerInput(p, Input.EMPTY, JUMP);
            check(h, rt.airJumpsUsed == 0, "Ground jump must not use an air jump");

            p.setOnGround(false);
            p.setDeltaMovement(0, -0.2, 0);
            InputRouter.onPlayerInput(p, Input.EMPTY, JUMP);
            check(h, rt.airJumpsUsed == 1 && Math.abs(p.getDeltaMovement().y - 0.62) < 1e-6, "Air jump should set vy=0.62 (registered HUNTER_HIGH), got " + p.getDeltaMovement());

            p.setDeltaMovement(0, -0.1, 0);
            InputRouter.onPlayerInput(p, Input.EMPTY, JUMP);
            check(h, rt.airJumpsUsed == 1 && p.getDeltaMovement().y < 0, "Double jump must allow only one air jump");

            InputRouter.onPlayerInput(p, JUMP, JUMP);
            check(h, rt.airJumpsUsed == 1, "Held jump is not a new press");

            p.setOnGround(true);
            AbilityService.tickPlayer(p);
            check(h, rt.airJumpsUsed == 0, "Landing resets air jumps");
            h.succeed();
        } finally {
            TestPlayers.remove(p);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void tripleJumpAllowsTwoAirJumps(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        GuardianData data = Guardians.data(p);
        data.setLoadout(GuardianClass.HUNTER, data.loadout(GuardianClass.HUNTER).with(AbilitySlot.JUMP, HunterAbilities.TRIPLE_JUMP));
        // JumpPhysics.Budget admits at most one press per server tick. Three input
        // edges in one synchronous callback exercise debounce, not the airborne budget.
        var accepted = new java.util.concurrent.atomic.AtomicInteger();
        for (int attempt = 1; attempt <= 3; attempt++) {
            final int expected = Math.min(attempt, 2);
            h.runAfterDelay(attempt, () -> {
                p.setOnGround(false);
                p.setDeltaMovement(0, -0.3, 0);
                InputRouter.onPlayerInput(p, Input.EMPTY, JUMP);
                if (p.getDeltaMovement().y > 0) accepted.incrementAndGet();
                check(h, accepted.get() == expected && Guardians.runtime(p).airJumpsUsed == expected,
                        "Triple jump admits the first two distinct ticks and rejects the third");
                InputRouter.onPlayerInput(p, JUMP, Input.EMPTY);
            });
        }
        h.runAfterDelay(4, h::succeed);
    }

    // ---------- 회피 ----------

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void doubleShiftDodgesWithIframesAndGamblerRefreshesMelee(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        Husk husk = husk(h, 6.5, 6.5);
        try {
            GuardianData data = Guardians.data(p);
            data.setCooldown(AbilitySlot.MELEE, 300);
            InputRouter.onPlayerInput(p, Input.EMPTY, SHIFT);
            check(h, data.cooldown(AbilitySlot.CLASS_ABILITY) == 0, "A single shift press must not dodge");
            InputRouter.onPlayerInput(p, SHIFT, Input.EMPTY);
            InputRouter.onPlayerInput(p, Input.EMPTY, SHIFT);
            check(h, data.cooldown(AbilitySlot.CLASS_ABILITY) == 220, "Gambler's dodge cooldown 11s=220t, got " + data.cooldown(AbilitySlot.CLASS_ABILITY));
            check(h, Guardians.runtime(p).invulnerableTicks == 6, "Dodge gives 6 invulnerable ticks");
            check(h, data.cooldown(AbilitySlot.MELEE) == 0, "Gambler's dodge near an enemy refreshes melee");
            Vec3 v = p.getDeltaMovement();
            check(h, Math.hypot(v.x, v.z) > 1.0, "Dodge should launch horizontally, got " + v);

            float health = p.getHealth();
            p.hurtServer(p.level(), p.damageSources().generic(), 5);
            check(h, p.getHealth() == health, "Damage during dodge i-frames must be ignored");
            for (int i = 0; i < 6; i++) {
                AbilityService.tickPlayer(p);
            }
            p.damageCooldownTime = 0;
            p.hurtServer(p.level(), p.damageSources().generic(), 5);
            check(h, p.getHealth() < health, "Damage applies after i-frames");

            InputRouter.onPlayerInput(p, Input.EMPTY, SHIFT);
            check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.COOLDOWN, "Dodge on cooldown");
            h.succeed();
        } finally {
            TestPlayers.remove(p);
            husk.discard();
        }
    }

    // ---------- 수류탄 ----------

    private void grenadeTest(GameTestHelper h, Element element, Keyword keyword) {
        ServerPlayer p = hunter(h, element, 15);
        Husk husk = husk(h, 6.5, 6.5);
        float start = husk.getHealth();
        double originalX = husk.getX();
        boolean cancelled = InputRouter.onPlayerAction(p, ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND);
        check(h, cancelled, "F (swap hands) must be cancelled for guardians");
        check(h, Guardians.data(p).cooldown(AbilitySlot.GRENADE) > 0, "Grenade should go on cooldown");
        h.succeedWhen(() -> {
            check(h, husk.getHealth() < start, "Grenade did not damage the husk yet");
            if (element == Element.VOID) {
                check(h, start - husk.getHealth() > 3.01f, "Vortex must deal more than one damage pulse");
                check(h, husk.getX() < originalX - 0.05 || husk.getDeltaMovement().x < -0.01, "Vortex must pull toward the anchor (NoAI fixture may retain velocity without traveling), x=" + husk.getX() + " vx=" + husk.getDeltaMovement().x);
            }
            if (keyword != null) {
                check(h, Statuses.has(husk, keyword), "Husk should have " + keyword);
            }
            TestPlayers.remove(p);
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void arcFlashbangBlinds(GameTestHelper h) {
        grenadeTest(h, Element.ARC, Keyword.BLINDED);
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void solarIncendiaryScorches(GameTestHelper h) {
        grenadeTest(h, Element.SOLAR, Keyword.SCORCHED);
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void voidVortexDamagesOverTime(GameTestHelper h) {
        grenadeTest(h, Element.VOID, null);
    }

    // ---------- 근접 ----------

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void arcCombinationBlowWithShiftPunch(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        Husk husk = husk(h, 4.5, 6.5);
        husk.setHealth(5f);
        p.setHealth(12f);
        float start = husk.getHealth();
        p.setShiftKeyDown(true);
        InputRouter.onPunch(p);
        check(h, Guardians.data(p).cooldown(AbilitySlot.MELEE) > 0, "Shift + punch should use melee");
        h.succeedWhen(() -> {
            check(h, husk.getHealth() < start, "Combination blow did not hit");
            check(h, !husk.isAlive() && Statuses.has(p, Keyword.AMPLIFIED), "Melee kill must amplify the hunter");
            check(h, p.getHealth() >= 16f, "Melee kill must heal the hunter");
            TestPlayers.remove(p);
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void solarKnifeScorches(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.SOLAR, 5);
        Husk husk = husk(h, 8.5, 6.5);
        float start = husk.getHealth();
        check(h, AbilityService.use(p, AbilitySlot.MELEE) == AbilityService.Result.OK, "Knife throw");
        h.succeedWhen(() -> {
            check(h, husk.getHealth() < start && Statuses.has(husk, Keyword.SCORCHED), "Knife should damage + scorch");
            TestPlayers.remove(p);
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void voidSmokeSuppresses(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.VOID, 20);
        Husk husk = husk(h, 5.5, 6.5);
        check(h, AbilityService.use(p, AbilitySlot.MELEE) == AbilityService.Result.OK, "Smoke bomb");
        h.succeedWhen(() -> {
            check(h, Statuses.has(husk, Keyword.SUPPRESSED), "Smoke should suppress the husk");
            TestPlayers.remove(p);
        });
    }

    // ---------- 궁극기 ----------

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void superNeedsFullEnergyAndArcStaffStrikes(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        Husk husk = husk(h, 5.5, 6.5);
        try {
            p.setShiftKeyDown(true);
            InputRouter.onPlayerAction(p, ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND);
            check(h, !AbilityService.inSuper(p), "Super must not start without energy");
            Guardians.data(p).setSuperEnergy(1f);
            InputRouter.dispatch(p, GuardianAction.SUPER);
            check(h, AbilityService.inSuper(p) && Guardians.data(p).superEnergy() == 0f, "Shift+F with full energy starts super");
            float start = husk.getHealth();
            p.setShiftKeyDown(false);
            InputRouter.onPunch(p);
            check(h, husk.getHealth() == start, "Deploy/wind-up is not a hit");
            for (int i = 0; i < kim.biryeong.destiny.fx.SuperAttackTiming.ARC_DEPLOY
                    + kim.biryeong.destiny.fx.SuperAttackTiming.ARC_CONTACT; i++) AbilityService.tickPlayer(p);
            check(h, husk.getHealth() < start, "Arc staff contact should hit the husk in front");
            check(h, Guardians.data(p).cooldown(AbilitySlot.MELEE) == 0, "Punch during super is not a melee ability");
            for (int i = 0; i < 400; i++) {
                AbilityService.tickPlayer(p);
            }
            check(h, !AbilityService.inSuper(p), "Arc staff ends after 400 ticks");
            h.succeed();
        } finally {
            TestPlayers.remove(p);
            husk.discard();
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void goldenGunThreeShots(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.SOLAR, 0);
        Husk husk = husk(h, 10.5, 6.5);
        try {
            Guardians.data(p).setSuperEnergy(1f);
            check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Golden gun starts");
            for (int i = 0; i < kim.biryeong.destiny.fx.SuperAttackTiming.SOLAR_DEPLOY; i++) AbilityService.tickPlayer(p);
            InputRouter.dispatch(p, GuardianAction.PRIMARY);
            check(h, husk.isAlive(), "Gun wind-up is not a hit");
            for (int i = 0; i < kim.biryeong.destiny.fx.SuperAttackTiming.SOLAR_CONTACT; i++) AbilityService.tickPlayer(p);
            check(h, !husk.isAlive() || husk.isDeadOrDying(), "Golden gun shot should kill a husk");
            for (int shot = 0; shot < 2; shot++) {
                for (int i = 0; i < 8; i++) {
                    AbilityService.tickPlayer(p);
                }
                AbilityService.perform(p, GuardianAction.PRIMARY);
            }
            for (int i = 0; i < 12; i++) AbilityService.tickPlayer(p);
            check(h, !AbilityService.inSuper(p), "Golden gun ends after third contact and dissolve");
            h.succeed();
        } finally {
            TestPlayers.remove(p);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void shadowshotTetherWeakens(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.VOID, 10);
        Husk husk = husk(h, 9.5, 6.5);
        Guardians.data(p).setSuperEnergy(1f);
        check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Shadowshot starts");
        h.succeedWhen(() -> {
            // Embedded fixture is not in PlayerList: advance its pending H19 bow draw once per test tick.
            AbilityService.tickPlayer(p);
            check(h, Statuses.has(husk, Keyword.WEAKENED) && Statuses.has(husk, Keyword.SUPPRESSED), "Tether should weaken + suppress");
            check(h, Math.abs(Statuses.modifyIncoming(husk, 10f) - 13f) < 1e-4, "Weakened takes x1.3 damage");
            TestPlayers.remove(p);
        });
    }

    // ---------- 에너지·HUD·데이터 ----------

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void superEnergyChargesAndHudShows(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        try {
            GuardianData data = Guardians.data(p);
            data.setSuperEnergy(0f);
            AbilityService.tickPlayer(p);
            check(h, data.superEnergy() > 0f, "Super energy charges passively");
            data.setSuperEnergy(0.5f);
            AbilityService.onKill(p, null, Element.ARC);
            check(h, Math.abs(data.superEnergy() - 0.54f) < 1e-4, "Kill grants super energy");
            data.setCooldown(AbilitySlot.GRENADE, 100);
            CombatHud.update(p);
            String text = CombatHud.lastText(p);
            check(h, text != null && text.contains("수류탄 5s") && text.contains("궁극기"), "HUD text: " + text);
            h.succeed();
        } finally {
            TestPlayers.remove(p);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void tuningJsonLoadedFromDatapack(GameTestHelper h) {
        check(h, AbilityRegistry.tuning(HunterAbilities.GOLDEN_GUN).params().containsKey("damage"),
                "data/destiny/destiny_ability/hunter/golden_gun.json should be loaded");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void nonGuardianIgnoresInput(GameTestHelper h) {
        ServerPlayer p = TestPlayers.create(h, PLAYER_POS, -90, 0);
        try {
            check(h, !InputRouter.onPlayerAction(p, ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND),
                    "Vanilla F must work for non-guardians");
            h.succeed();
        } finally {
            TestPlayers.remove(p);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void projectilesCleanUp(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        var projectile = SimProjectile.launch(p, p.getEyePosition(), Vec3.ZERO, 0, 2,
                new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.STICK), 0.5f, 0xFFFFFF, hit -> { });
        check(h, SimProjectile.activeCount(p) == 1, "Test projectile must exist");
        h.succeedWhen(() -> {
            check(h, projectile.isDone() && SimProjectile.activeCount(p) == 0, "Expired projectile and holder must be disposed");
            TestPlayers.remove(p);
        });
    }
    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void guardianDataCodecRoundTripsAndClassSwitchKeepsLoadouts(GameTestHelper h) {
        GuardianData data = new GuardianData();
        data.setGuardianClass(GuardianClass.HUNTER);
        data.setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(Element.VOID));
        data.setCooldown(AbilitySlot.GRENADE, 347);
        data.setSuperEnergy(0.63f);
        var encoded = GuardianData.CODEC.encodeStart(com.mojang.serialization.JsonOps.INSTANCE, data).getOrThrow();
        GuardianData restored = GuardianData.CODEC.parse(com.mojang.serialization.JsonOps.INSTANCE, encoded).getOrThrow();
        check(h, restored.guardianClass() == GuardianClass.HUNTER, "Class persists");
        check(h, restored.cooldown(AbilitySlot.GRENADE) == 347, "Cooldown persists");
        check(h, Math.abs(restored.superEnergy() - 0.63f) < 0.0001, "Super energy persists");
        check(h, restored.loadout().orElseThrow().get(AbilitySlot.SUPER).equals(HunterAbilities.SHADOWSHOT), "Loadout persists");
        restored.setGuardianClass(GuardianClass.NONE);
        restored.setGuardianClass(GuardianClass.HUNTER);
        check(h, restored.loadout().orElseThrow().get(AbilitySlot.SUPER).equals(HunterAbilities.SHADOWSHOT), "Switching away preserves hunter loadout");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void guardianAttachmentSurvivesDeathRespawnEvent(GameTestHelper h) {
        ServerPlayer old = hunter(h, Element.SOLAR, 0);
        ServerPlayer respawned = TestPlayers.create(h, PLAYER_POS, -90, 0);
        try {
            Guardians.data(old).setCooldown(AbilitySlot.MELEE, 123);
            Guardians.data(old).setSuperEnergy(0.42f);
            respawned.restoreFrom(old, false);
            // Fabric transfers attachments after respawn, not in vanilla restoreFrom.
            net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents.AFTER_RESPAWN.invoker()
                    .afterRespawn(old, respawned, false);
            GuardianData data = Guardians.data(respawned);
            check(h, data.guardianClass() == GuardianClass.HUNTER, "Hunter attachment copies on death");
            check(h, data.cooldown(AbilitySlot.MELEE) == 123, "Death keeps cooldown");
            check(h, Math.abs(data.superEnergy() - 0.42f) < 0.0001, "Death keeps super energy");
            check(h, data.loadout().orElseThrow().get(AbilitySlot.SUPER).equals(HunterAbilities.GOLDEN_GUN), "Death keeps subclass");
            h.succeed();
        } finally {
            TestPlayers.remove(old);
            TestPlayers.remove(respawned);
        }
    }

}
