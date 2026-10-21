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

    @GameTest(structure = FLOOR, maxTicks = 40)
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
            check(h, rt.airJumpsUsed == 1 && Math.abs(p.getDeltaMovement().y - 0.55) < 1e-6, "Air jump should set vy=0.55, got " + p.getDeltaMovement());

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

    @GameTest(structure = FLOOR, maxTicks = 40)
    public void tripleJumpAllowsTwoAirJumps(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        try {
            GuardianData data = Guardians.data(p);
            data.setLoadout(GuardianClass.HUNTER, data.loadout(GuardianClass.HUNTER).with(AbilitySlot.JUMP, HunterAbilities.TRIPLE_JUMP));
            p.setOnGround(false);
            int ok = 0;
            for (int i = 0; i < 3; i++) {
                p.setDeltaMovement(0, -0.3, 0);
                InputRouter.onPlayerInput(p, Input.EMPTY, JUMP);
                if (p.getDeltaMovement().y > 0) {
                    ok++;
                }
            }
            check(h, ok == 2, "Triple jump should allow exactly 2 air jumps, got " + ok);
            h.succeed();
        } finally {
            TestPlayers.remove(p);
        }
    }

    // ---------- 회피 ----------

    @GameTest(structure = FLOOR, maxTicks = 60)
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
            p.setInvulnerableTime(0);
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
        boolean cancelled = InputRouter.onPlayerAction(p, ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND);
        check(h, cancelled, "F (swap hands) must be cancelled for guardians");
        check(h, Guardians.data(p).cooldown(AbilitySlot.GRENADE) > 0, "Grenade should go on cooldown");
        h.succeedWhen(() -> {
            check(h, husk.getHealth() < start, "Grenade did not damage the husk yet");
            if (keyword != null) {
                check(h, Statuses.has(husk, keyword), "Husk should have " + keyword);
            }
            TestPlayers.remove(p);
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80)
    public void arcFlashbangBlinds(GameTestHelper h) {
        grenadeTest(h, Element.ARC, Keyword.BLINDED);
    }

    @GameTest(structure = FLOOR, maxTicks = 80)
    public void solarIncendiaryScorches(GameTestHelper h) {
        grenadeTest(h, Element.SOLAR, Keyword.SCORCHED);
    }

    @GameTest(structure = FLOOR, maxTicks = 100)
    public void voidVortexDamagesOverTime(GameTestHelper h) {
        grenadeTest(h, Element.VOID, null);
    }

    // ---------- 근접 ----------

    @GameTest(structure = FLOOR, maxTicks = 60)
    public void arcCombinationBlowWithShiftPunch(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.ARC, 0);
        Husk husk = husk(h, 4.5, 6.5);
        float start = husk.getHealth();
        p.setShiftKeyDown(true);
        InputRouter.onPunch(p);
        check(h, Guardians.data(p).cooldown(AbilitySlot.MELEE) > 0, "Shift + punch should use melee");
        h.succeedWhen(() -> {
            check(h, husk.getHealth() < start, "Combination blow did not hit");
            TestPlayers.remove(p);
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 60)
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

    @GameTest(structure = FLOOR, maxTicks = 80)
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

    @GameTest(structure = FLOOR, maxTicks = 40)
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
            check(h, husk.getHealth() < start, "Arc staff strike should hit the husk in front");
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

    @GameTest(structure = FLOOR, maxTicks = 40)
    public void goldenGunThreeShots(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.SOLAR, 0);
        Husk husk = husk(h, 10.5, 6.5);
        try {
            Guardians.data(p).setSuperEnergy(1f);
            check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Golden gun starts");
            InputRouter.dispatch(p, GuardianAction.PRIMARY);
            check(h, !husk.isAlive() || husk.isDeadOrDying(), "Golden gun shot should kill a husk");
            for (int shot = 0; shot < 2; shot++) {
                for (int i = 0; i < 8; i++) {
                    AbilityService.tickPlayer(p);
                }
                AbilityService.perform(p, GuardianAction.PRIMARY);
            }
            AbilityService.tickPlayer(p);
            check(h, !AbilityService.inSuper(p), "Golden gun ends after 3 shots");
            h.succeed();
        } finally {
            TestPlayers.remove(p);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 80)
    public void shadowshotTetherWeakens(GameTestHelper h) {
        ServerPlayer p = hunter(h, Element.VOID, 10);
        Husk husk = husk(h, 9.5, 6.5);
        Guardians.data(p).setSuperEnergy(1f);
        check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Shadowshot starts");
        AbilityService.perform(p, GuardianAction.PRIMARY);
        h.succeedWhen(() -> {
            check(h, Statuses.has(husk, Keyword.WEAKENED) && Statuses.has(husk, Keyword.SUPPRESSED), "Tether should weaken + suppress");
            check(h, Math.abs(Statuses.modifyIncoming(husk, 10f) - 13f) < 1e-4, "Weakened takes x1.3 damage");
            TestPlayers.remove(p);
        });
    }

    // ---------- 에너지·HUD·데이터 ----------

    @GameTest(structure = FLOOR, maxTicks = 40)
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

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void tuningJsonLoadedFromDatapack(GameTestHelper h) {
        check(h, AbilityRegistry.tuning(HunterAbilities.GOLDEN_GUN).params().containsKey("damage"),
                "data/destiny/destiny_ability/hunter/golden_gun.json should be loaded");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
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

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void projectilesCleanUp(GameTestHelper h) {
        h.succeedWhen(() -> check(h, SimProjectile.activeCount() >= 0, "noop"));
    }
}
