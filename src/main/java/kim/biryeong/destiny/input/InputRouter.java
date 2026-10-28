package kim.biryeong.destiny.input;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Input;

/**
 * 바닐라 입력 → {@link GuardianAction}. GCB 키 입력도 {@link #dispatch} 로 들어온다 (docs/design/12).
 *
 * <ul>
 *   <li>공중에서 점프 → AIR_JUMP</li>
 *   <li>웅크리기 두 번 (간격 {@link #DOUBLE_TAP_TICKS}틱 이내) → CLASS_ABILITY</li>
 *   <li>F → GRENADE, 웅크리기 + F → SUPER (바닐라 손 바꾸기는 취소)</li>
 *   <li>웅크리기 + 좌클릭 → MELEE, 궁극기 중 좌클릭 → PRIMARY</li>
 * </ul>
 */
public final class InputRouter {
    public static final int DOUBLE_TAP_TICKS = 7;

    private InputRouter() {
    }

    /** 같은 동작이 같은 틱에 두 경로로 들어오면 한 번만 처리한다. */
    public static boolean dispatch(ServerPlayer player, GuardianAction action) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) return false;
        if (action == GuardianAction.AIR_JUMP) {
            // 점프는 바닐라 입력에서만 온다. 같은 틱 중복이 생기지 않는다.
            return AbilityService.perform(player, action);
        }
        // GCB 키와 바닐라 키가 같은 틱에 같은 동작을 보내면 한 번만 처리한다.
        // 실패한 시도(쿨다운·에너지 부족)는 기록하지 않아 같은 틱의 다른 경로가 다시 시도할 수 있다.
        GuardianRuntime runtime = Guardians.runtime(player);
        int tick = player.level().getServer().getTickCount();
        Integer last = runtime.lastActionTick.get(action);
        if (last != null && last == tick) {
            return true;
        }
        boolean ok = AbilityService.perform(player, action);
        if (ok) {
            runtime.lastActionTick.put(action, tick);
        }
        return ok;
    }

    public static void onPlayerInput(ServerPlayer player, Input previous, Input next) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) return;
        if (!Guardians.isGuardian(player)) {
            return;
        }
        GuardianRuntime runtime = Guardians.runtime(player);
        runtime.lastInput = next;
        if (next.jump() && !previous.jump() && canAirJump(player)) {
            dispatch(player, GuardianAction.AIR_JUMP);
        }
        if (next.shift() && !previous.shift()) {
            int tick = player.level().getServer().getTickCount();
            if (tick - runtime.lastShiftPressTick <= DOUBLE_TAP_TICKS) {
                runtime.lastShiftPressTick = Integer.MIN_VALUE / 2;
                dispatch(player, GuardianAction.CLASS_ABILITY);
            } else {
                runtime.lastShiftPressTick = tick;
            }
        }
    }

    /** @return true 면 바닐라 처리를 취소한다. */
    public static boolean onPlayerAction(ServerPlayer player, ServerboundPlayerActionPacket.Action action) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) return true;
        if (action == ServerboundPlayerActionPacket.Action.DROP_ITEM && player.isShiftKeyDown()) {
            kim.biryeong.destiny.inventory.WeaponScreen.open(player);
            return true;
        }
        if (!Guardians.isGuardian(player)) {
            return false;
        }
        if (action == ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND) {
            dispatch(player, player.isShiftKeyDown() ? GuardianAction.SUPER : GuardianAction.GRENADE);
            return true;
        }
        if (action == ServerboundPlayerActionPacket.Action.START_DESTROY_BLOCK && AbilityService.inSuper(player)) {
            return true;
        }
        return false;
    }

    public static void onPunch(ServerPlayer player) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) return;
        if (!Guardians.isGuardian(player)) {
            return;
        }
        if (AbilityService.inSuper(player)) {
            dispatch(player, GuardianAction.PRIMARY);
        } else if (player.isShiftKeyDown()) {
            dispatch(player, GuardianAction.MELEE);
        }
    }

    public static boolean canAirJump(ServerPlayer player) {
        return !player.onGround()
                && !player.getAbilities().flying
                && !player.isInWater()
                && !player.isPassenger()
                && !player.onClimbable()
                && !player.isFallFlying();
    }
}
