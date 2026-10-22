package kim.biryeong.destiny.ability;

import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianData;
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
                !(entity instanceof ServerPlayer player) || Guardians.runtime(player).invulnerableTicks <= 0);
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                cleanup(player);
                Guardians.forget(player);
            }
            HunterVfx.clearAll();
            kim.biryeong.destiny.fx.SuperVfx.clearAll();
            kim.biryeong.destiny.fx.PostEffects.clearAll();
            SimProjectile.clearAll();
            Tasks.clearAll();
            Statuses.clearAll();
        });
    }

    public static void cleanup(ServerPlayer player) {
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
        SimProjectile.tickAll(server);
        Tasks.tickAll();
        HunterVfx.tick(server);
        kim.biryeong.destiny.fx.SuperVfx.tick(server);
        kim.biryeong.destiny.fx.PostEffects.tick(server);
        kim.biryeong.destiny.fx.PlayerAnimations.tick(server);
        kim.biryeong.destiny.camera.SuperCamera.tick(server);
    }

    public static void tickPlayer(ServerPlayer player) {
        if (player.isDeadOrDying() || player.isSpectator()) {
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
            CombatHud.update(player);
            return;
        }
        data.tickCooldowns();
        if (runtime.superSession != null) {
            if (!runtime.superSession.tick()) {
                endSuper(player);
            }
        } else if (data.superEnergy() < 1f) {
            data.setSuperEnergy(data.superEnergy() + (float) (1.0 / (passiveSuperSeconds * 20.0)));
        }
        CombatHud.update(player);
    }

    public static Optional<Ability> equipped(ServerPlayer player, AbilitySlot slot) {
        return Guardians.data(player).loadout().map(l -> l.get(slot)).flatMap(AbilityRegistry::get);
    }

    /** 입력 동작 처리. 처리했으면 true. */
    public static boolean perform(ServerPlayer player, GuardianAction action) {
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

    public static Result use(ServerPlayer player, AbilitySlot slot) {
        if (player.isDeadOrDying() || player.isSpectator()) return Result.FAILED;
        if (!Guardians.isGuardian(player)) {
            return Result.NOT_GUARDIAN;
        }
        Optional<Ability> equipped = equipped(player, slot);
        if (equipped.isEmpty()) {
            return Result.NO_ABILITY;
        }
        Ability ability = equipped.get();
        GuardianData data = Guardians.data(player);
        GuardianRuntime runtime = Guardians.runtime(player);
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
        if (!ability.activate(player)) {
            return Result.FAILED;
        }
        if (slot == AbilitySlot.SUPER) {
            data.setSuperEnergy(0f);
        } else {
            data.setCooldown(slot, ability.cooldownTicks());
        }
        CombatHud.update(player);
        return Result.OK;
    }

    public static void startSuper(ServerPlayer player, SuperSession session) {
        Guardians.runtime(player).superSession = session;
    }

    public static void endSuper(ServerPlayer player) {
        GuardianRuntime runtime = Guardians.runtime(player);
        SuperSession session = runtime.superSession;
        runtime.superSession = null;
        if (session != null) {
            session.end();
        }
    }

    public static boolean inSuper(ServerPlayer player) {
        return Guardians.runtime(player).superSession != null;
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
