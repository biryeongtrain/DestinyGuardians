package kim.biryeong.destiny.ability;

import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.GuardianAction;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;

import java.util.Optional;

/** 능력 실행·쿨타임·궁극기 에너지 관리. */
public final class AbilityService {
    /** 아무것도 하지 않을 때 궁극기가 다 차는 시간(초). */
    public static double passiveSuperSeconds = 180.0;
    /** 처치당 궁극기 에너지. */
    public static float killSuperEnergy = 0.04f;

    public enum Result {
        OK, NOT_GUARDIAN, NO_ABILITY, COOLDOWN, NOT_READY, BUSY, FAILED
    }

    private AbilityService() {
    }

    public static void init() {
        kim.biryeong.destiny.input.InputRouter.init();
        ServerTickEvents.END_SERVER_TICK.register(AbilityService::tick);
        net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((player, from, to) -> {
            cleanup(player);
            Guardians.forget(player);
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            cleanup(handler.getPlayer());
            Guardians.forget(handler.getPlayer());
        });
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
            Statuses.creditFireDeath(entity, source);
            if (entity instanceof ServerPlayer player) {
                cleanup(player);
                Guardians.forget(player);
            }
        });
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
                (!(entity instanceof ServerPlayer player) || Guardians.runtime(player).invulnerableTicks <= 0)
                && kim.biryeong.destiny.ability.titan.TitanExpandedSupers.allowDamage(entity, source, amount));
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                cleanup(player);
                Guardians.forget(player);
            }
            kim.biryeong.destiny.hud.WeaponHitHud.clearAll(server);
            HunterVfx.clearAll();
            kim.biryeong.destiny.fx.SuperVfx.clearAll();
            kim.biryeong.destiny.fx.PostEffects.clearAll();
            SimProjectile.clearAll();
            Tasks.clearAll();
            GrenadeThrow.clearAll();
            ClassAbilityCast.clearAll();
            kim.biryeong.destiny.ability.jump.JumpAbilities.clearAll();
            Statuses.clearAll();
            kim.biryeong.destiny.ability.titan.TitanAbilities.clearAll();
            kim.biryeong.destiny.ability.warlock.WarlockAbilities.clearAll();
            kim.biryeong.destiny.fx.ClassAbilityEffects.clearAll();
            kim.biryeong.destiny.ability.hunter.HunterExpandedSupers.clearAll();
            kim.biryeong.destiny.ability.titan.TitanExpandedSupers.clearAll();
            kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers.clearAll();
        });
    }

    public static void cleanup(ServerPlayer player) {
        kim.biryeong.destiny.combat.MeleeLunge.cancel(player);
        kim.biryeong.destiny.combat.GuardianRecovery.forget(player);
        kim.biryeong.destiny.combat.SupportOvershield.cleanup(player);
        GrenadeThrow.cleanup(player);
        ClassAbilityCast.cleanup(player);
        kim.biryeong.destiny.ability.jump.JumpAbilities.cleanup(player);
        kim.biryeong.destiny.ability.hunter.HunterExpandedSupers.cleanup(player);
        kim.biryeong.destiny.ability.titan.TitanExpandedSupers.cleanup(player);
        kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers.cleanup(player);
        kim.biryeong.destiny.ability.titan.TitanAbilities.cleanup(player);
        kim.biryeong.destiny.ability.warlock.WarlockAbilities.cleanup(player);
        kim.biryeong.destiny.fx.ClassAbilityEffects.cleanup(player);
        kim.biryeong.destiny.weapon.WeaponRuntime.cancelUseForSkill(player);
        kim.biryeong.destiny.ability.hunter.HunterSkillCast.cancelPending(player);
        kim.biryeong.destiny.camera.SuperCamera.stop(player);
        endSuper(player);
        kim.biryeong.destiny.fx.PlayerAnimations.stop(player);
        CombatHud.remove(player);
        SimProjectile.discardOwned(player);
        Tasks.cancelOwned(player);
        HunterVfx.cancelOwned(player);
        kim.biryeong.destiny.fx.SuperVfx.cancelOwned(player);
        kim.biryeong.destiny.fx.PostEffects.cancel(player);
        Statuses.forget(player);
    }

    public static void tick(MinecraftServer server) {
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            tickPlayer(player);
        }
        Statuses.tick(server);
        GrenadeThrow.tick(server);
        ClassAbilityCast.tick(server);
        kim.biryeong.destiny.ability.jump.JumpAbilities.tick(server);
        SimProjectile.tickAll(server);
        Tasks.tickAll();
        kim.biryeong.destiny.ability.hunter.HunterExpandedSupers.tick(server);
        kim.biryeong.destiny.ability.titan.TitanExpandedSupers.tick(server);
        kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers.tick(server);
        kim.biryeong.destiny.ability.titan.TitanAbilities.tick(server);
        kim.biryeong.destiny.ability.warlock.WarlockAbilities.tick(server);
        HunterVfx.tick(server);
        kim.biryeong.destiny.fx.SuperVfx.tick(server);
        kim.biryeong.destiny.fx.PostEffects.tick(server);
        kim.biryeong.destiny.fx.PlayerAnimations.tick(server);
        kim.biryeong.destiny.fx.SuperVfx.tickEquipmentEnergy(server);
        kim.biryeong.destiny.camera.SuperCamera.tick(server);
    }

    public static void tickPlayer(ServerPlayer player) {
        kim.biryeong.destiny.combat.GuardianRecovery.tick(player);
        kim.biryeong.destiny.combat.SupportOvershield.tick(player);
        if (player.isDeadOrDying() || player.isSpectator()) {
            if (Guardians.runtime(player).superSession != null || kim.biryeong.destiny.fx.PlayerAnimations.isPlaying(player)) {
                cleanup(player);
            }
            CombatHud.remove(player);
            return;
        }
        GuardianData data = Guardians.data(player);
        GuardianRuntime runtime = Guardians.runtime(player);
        if (runtime.invulnerableTicks > 0) {
            runtime.invulnerableTicks--;
        }
        if (player.onGround()) {
            runtime.airJumpsUsed = 0;
        }
        if (!Guardians.isGuardian(player)) {
            MeleeSuperMovement.clear(player);
            CombatHud.update(player);
            return;
        }
        data.tickCooldowns();
        if (runtime.superSession != null) {
            if (!runtime.superSession.tick()) {
                completeSuper(player);
            }
        } else if (data.superEnergy() < 1f) {
            // Classic new-class base recharge comes from its DDC-backed super tuning.
            // Hunter retains the existing configurable recharge path. Kill/ability gains are additive.
            double rechargeTicks = passiveSuperSeconds * 20.0;
            if (data.guardianClass() == GuardianClass.TITAN || data.guardianClass() == GuardianClass.WARLOCK
                    || equipped(player, AbilitySlot.SUPER).map(a -> kim.biryeong.destiny.fx.ClassSuperModelAssets.isExpanded(a.id().getPath())).orElse(false)) {
                int tuned = equipped(player, AbilitySlot.SUPER).map(Ability::cooldownTicks).orElse(0);
                if (tuned > 0) rechargeTicks = tuned;
            }
            data.setSuperEnergy(data.superEnergy() + (float) (1.0 / rechargeTicks));
        }
        MeleeSuperMovement.tick(player);
        CombatHud.update(player);
    }

    public static Optional<Ability> equipped(ServerPlayer player, AbilitySlot slot) {
        GuardianData data = Guardians.data(player);
        return data.loadout().map(l -> l.get(slot)).flatMap(AbilityRegistry::get)
                .filter(a -> a.guardianClass() == data.guardianClass() && a.slot() == slot);
    }

    /** 입력 동작 처리. 처리했으면 true. */
    public static boolean perform(ServerPlayer player, GuardianAction action) {
        if (kim.biryeong.destiny.down.GuardianDown.active(player)) return false;
        if (!kim.biryeong.destiny.strike.devils.DevilsLair.allows(player)) return false;
        if (!kim.biryeong.destiny.crucible.CrucibleRuntime.canAct(player)) return false;
        if (!Guardians.isGuardian(player) || player.isSpectator() || player.isDeadOrDying()) {
            return false;
        }
        GuardianRuntime runtime = Guardians.runtime(player);
        return switch (action) {
            case PRIMARY -> {
                if (runtime.superSession == null) {
                    yield false;
                }
                runtime.superSession.primary();
                yield true;
            }
            case AIR_JUMP -> use(player, AbilitySlot.JUMP) == Result.OK;
            case GRENADE -> use(player, AbilitySlot.GRENADE) == Result.OK;
            case MELEE -> use(player, AbilitySlot.MELEE) == Result.OK;
            case CLASS_ABILITY -> use(player, AbilitySlot.CLASS_ABILITY) == Result.OK;
            case SUPER -> use(player, AbilitySlot.SUPER) == Result.OK;
        };
    }

    public static boolean secondarySupported(ServerPlayer player) {
        return Guardians.runtimeIfPresent(player).map(r->r.superSession).map(SuperSession::supportsSecondary).orElse(false);
    }

    /** Same activity/PvP/down/lifecycle gates as primary, with no ordinary weapon or ability side effects. */
    public static boolean secondary(ServerPlayer player) {
        if(kim.biryeong.destiny.inventory.WeaponScreen.active(player)||player.containerMenu!=player.inventoryMenu
                ||kim.biryeong.destiny.down.GuardianDown.active(player)
                ||!kim.biryeong.destiny.strike.devils.DevilsLair.allows(player)
                ||!kim.biryeong.destiny.crucible.CrucibleRuntime.canAct(player)
                ||!Guardians.isGuardian(player)||player.isSpectator()||player.isDeadOrDying()||player.hasDisconnected())return false;
        var session=Guardians.runtimeIfPresent(player).map(r->r.superSession).orElse(null);
        if(session==null||!session.supportsSecondary())return false;
        session.secondary();return true; // The opted-in session also owns rejected cooldown/recovery requests.
    }

    public static Result use(ServerPlayer player, AbilitySlot slot) {
        if (kim.biryeong.destiny.down.GuardianDown.active(player)) return Result.BUSY;
        if (!kim.biryeong.destiny.strike.devils.DevilsLair.allows(player)) return Result.BUSY;
        if (!kim.biryeong.destiny.crucible.CrucibleRuntime.canAct(player)) return Result.BUSY;
        if (player.isDeadOrDying() || player.isSpectator()) return Result.FAILED;
        if (!Guardians.isGuardian(player)) {
            return Result.NOT_GUARDIAN;
        }
        Optional<Ability> equipped = equipped(player, slot);
        if (equipped.isEmpty()) {
            return Result.NO_ABILITY;
        }
        // New Light tutorial: each ability returns at its own lesson.
        if (!kim.biryeong.destiny.tutorial.Tutorial.allows(player, slot)) return Result.BUSY;
        if (ClassAbilityCast.active(player) && slot != AbilitySlot.SUPER) return Result.BUSY;
        if (GrenadeThrow.active(player) && slot != AbilitySlot.JUMP && slot != AbilitySlot.SUPER) return Result.BUSY;
        Ability ability = equipped.get();
        GuardianData data = Guardians.data(player);
        GuardianRuntime runtime = Guardians.runtime(player);
        if (slot == AbilitySlot.JUMP && kim.biryeong.destiny.camera.SuperCamera.movementBlocked(player)) {
            return Result.BUSY;
        }
        if (runtime.superSession != null && slot != AbilitySlot.SUPER && slot != AbilitySlot.JUMP) {
            if(slot!=AbilitySlot.CLASS_ABILITY)return Result.BUSY;
            Result result=runtime.superSession.classAbility();
            if(result==Result.OK)CombatHud.update(player);
            return result; // No ordinary cooldown, reload, melee refresh, perk or cast lifecycle side effects.
        }
        if (slot == AbilitySlot.SUPER) {
            if (runtime.superSession != null) {
                return Result.BUSY;
            }
            if (data.superEnergy() < 1f) {
                return Result.NOT_READY;
            }
        } else if (data.cooldown(slot) > 0) {
            return Result.COOLDOWN;
        }
        if (slot != AbilitySlot.JUMP) kim.biryeong.destiny.weapon.WeaponRuntime.cancelUseForSkill(player);
        var wellRounded=(slot==AbilitySlot.GRENADE||slot==AbilitySlot.SUPER)
            ?kim.biryeong.destiny.weapon.WeaponWellRounded.accepted(player,slot)
            :kim.biryeong.destiny.weapon.WeaponWellRounded.Token.NONE;
        var osmosis = slot == AbilitySlot.GRENADE ? kim.biryeong.destiny.weapon.WeaponOsmosis.accepted(player)
                : kim.biryeong.destiny.weapon.WeaponOsmosis.Token.NONE;
        if (!ability.activate(player)) {
            return Result.FAILED;
        }
        if (slot == AbilitySlot.GRENADE || slot == AbilitySlot.MELEE || slot == AbilitySlot.SUPER)
            kim.biryeong.destiny.down.GuardianDown.attacked(player);
        if (slot == AbilitySlot.SUPER) {
            data.setSuperEnergy(0f);
        } else {
            data.setCooldown(slot, ability.cooldownTicks());
        }
        kim.biryeong.destiny.weapon.WeaponWellRounded.abilityUsed(player,wellRounded,slot);
        if (slot == AbilitySlot.GRENADE) kim.biryeong.destiny.weapon.WeaponOsmosis.abilityUsed(player,osmosis);
        kim.biryeong.destiny.tutorial.Tutorial.abilityUsed(player, slot);
        CombatHud.update(player);
        return Result.OK;
    }

    public static void startSuper(ServerPlayer player, SuperSession session) {
        GrenadeThrow.cleanup(player);
        ClassAbilityCast.cleanup(player);
        kim.biryeong.destiny.ability.hunter.HunterSkillCast.cancelPending(player);
        var runtime = Guardians.runtime(player);
        runtime.superSession = session;
        runtime.superResistance = new kim.biryeong.destiny.combat.SuperDamageResistance.Binding(session,
                equipped(player, AbilitySlot.SUPER).map(Ability::id).orElse(null), player.level());
    }

    public static void endSuper(ServerPlayer player) {
        completeSuper(player);
        // Explicit cancellation is not an accepted final-shot recovery.
        kim.biryeong.destiny.fx.PlayerAnimations.stop(player);
        kim.biryeong.destiny.camera.SuperCamera.stop(player);
        kim.biryeong.destiny.fx.SuperVfx.cancelOwned(player);
    }

    private static void completeSuper(ServerPlayer player) {
        kim.biryeong.destiny.combat.MeleeLunge.cancel(player);
        GuardianRuntime runtime = Guardians.runtime(player);
        SuperSession session = runtime.superSession;
        runtime.superSession = null;
        runtime.superResistance = null;
        MeleeSuperMovement.clear(player);
        if (session != null) {
            session.end();
        }
    }

    public static boolean inSuper(ServerPlayer player) {
        return Guardians.runtimeIfPresent(player).map(runtime -> runtime.superSession != null).orElse(false);
    }

    public static void onKill(ServerPlayer player, LivingEntity target, Element element) {
        GuardianData data = Guardians.data(player);
        if (Guardians.isGuardian(player) && !inSuper(player)) {
            data.setSuperEnergy(data.superEnergy() + killSuperEnergy);
        }
    }

    public static void resetCooldown(ServerPlayer player, AbilitySlot slot) {
        Guardians.data(player).setCooldown(slot, 0);
    }

    public static Identifier idOf(ServerPlayer player, AbilitySlot slot) {
        return equipped(player, slot).map(Ability::id).orElse(null);
    }
}
