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
 *   <li>GCB 사용자는 Z/C/V 및 손 교환 F만 능력 키로 사용한다.</li>
 *   <li>아래 웅크리기 조합과 수류탄 F는 GCB 미설치자에게만 적용한다.</li>
 *   <li>웅크리기 두 번 (간격 {@link #DOUBLE_TAP_TICKS}틱 이내) → CLASS_ABILITY</li>
 *   <li>F → GRENADE, 웅크리기 + F → SUPER (바닐라 손 바꾸기는 취소)</li>
 *   <li>총기 좌클릭 → ADS 토글 (Shift는 웅크리기 유지)</li>
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
        if (!ClientControls.gcb(player) && next.shift() && !previous.shift()) {
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
        if ((action == ServerboundPlayerActionPacket.Action.DROP_ITEM
                || action == ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS)
                && kim.biryeong.destiny.weapon.WeaponItems.entry(player.getMainHandItem()).isPresent()) {
            // Holding Ctrl to sprint changes Q into DROP_ALL_ITEMS on vanilla clients.
            // While actually sprinting it is ordinary reload, never the removed Ctrl+Q special action.
            boolean dropAll = action == ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS;
            if (dropAll && !player.isSprinting()) return true;
            if (!dropAll && player.isShiftKeyDown()
                    && kim.biryeong.destiny.weapon.WeaponItems.entry(player.getMainHandItem())
                        .filter(kim.biryeong.destiny.weapon.WeaponExotics::izanagi).isPresent()) {
                kim.biryeong.destiny.weapon.WeaponRuntime.reloadHoned(player);
            } else {
                kim.biryeong.destiny.weapon.WeaponRuntime.reload(player);
            }
            return true; // 모든 실전 무기의 Q 계열 입력은 장전 성공·거절과 무관하게 버리기를 취소한다.
        }
        if (action == ServerboundPlayerActionPacket.Action.START_DESTROY_BLOCK
                && kim.biryeong.destiny.weapon.WeaponItems.entry(player.getMainHandItem()).isPresent()) return true;
        if (!Guardians.isGuardian(player)) {
            if(action==ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND) {
                kim.biryeong.destiny.weapon.WeaponQuickdraw.changed(player,player.getMainHandItem());
                kim.biryeong.destiny.weapon.WeaponAiming.inventoryStowing(player,player.getMainHandItem());
                // Unlike Guardian F, this packet really stows the main hand. Observe it BEFORE
                // vanilla swaps, including away/back in one tick that identity polling misses.
                kim.biryeong.destiny.weapon.WeaponArcherTempo.cleanup(player);
                kim.biryeong.destiny.weapon.WeaponAce.stowing(player);
                if(kim.biryeong.destiny.weapon.SwordItems.isSword(player.getMainHandItem())
                        ||kim.biryeong.destiny.weapon.WeaponItems.entry(player.getMainHandItem())
                            .filter(e->e.family().equals("bow")||kim.biryeong.destiny.weapon.BreachGrenade.supports(e)
                                    ||kim.biryeong.destiny.weapon.WeaponExotics.izanagi(e)).isPresent())
                    kim.biryeong.destiny.weapon.WeaponRuntime.cancelUseForSkill(player);
            }
            return false;
        }
        if (action == ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND) {
            // GCB reports Z/C/V directly; F uses vanilla swap-offhand transport.
            // A GCB client must not also activate the old Shift+F fallback.
            if (ClientControls.gcb(player)) {
                if (!player.isShiftKeyDown()) dispatch(player, GuardianAction.SUPER);
            } else {
                dispatch(player, player.isShiftKeyDown() ? GuardianAction.SUPER : GuardianAction.GRENADE);
            }
            return true;
        }
        if (action == ServerboundPlayerActionPacket.Action.START_DESTROY_BLOCK && AbilityService.inSuper(player)) {
            return true;
        }
        return false;
    }

    public static void onPunch(ServerPlayer player) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) return;
        // Only non-GCB players use the crouch/punch melee chord. GCB players may
        // still toggle ordinary gun ADS while crouching; their melee ability is C.
        boolean vanillaMelee = player.isShiftKeyDown() && Guardians.isGuardian(player) && !ClientControls.gcb(player);
        // Vanilla clients drop left clicks for 10 ticks after a click into empty air (missTime),
        // so GCB players toggle ADS from the real attack-key event instead (gcbAttack below).
        boolean gcbKeyDriven = ClientControls.gcb(player) && Guardians.runtime(player).gcbAttackKey;
        if (!AbilityService.inSuper(player) && !vanillaMelee && !gcbKeyDriven
                && kim.biryeong.destiny.weapon.WeaponAiming.toggle(player)) {
            Guardians.runtime(player).punchToggleTick = player.level().getServer().getTickCount();
            return;
        }
        if (gcbKeyDriven && !AbilityService.inSuper(player) && !vanillaMelee
                && kim.biryeong.destiny.weapon.WeaponAiming.handles(player)) return;
        if (kim.biryeong.destiny.weapon.WeaponRuntime.onPunch(player)) return;
        if (!Guardians.isGuardian(player)) {
            return;
        }
        if (AbilityService.inSuper(player)) {
            dispatch(player, GuardianAction.PRIMARY);
        } else if (vanillaMelee) {
            dispatch(player, GuardianAction.MELEE);
        }
    }

    /** GCB attack-key press. Not subject to the client's missTime click suppression. */
    public static void gcbAttack(ServerPlayer player) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player) || AbilityService.inSuper(player)) return;
        var runtime = Guardians.runtime(player);
        boolean first = !runtime.gcbAttackKey;
        runtime.gcbAttackKey = true;
        // The very first press may already have toggled through the punch packet this/last tick.
        if (first && player.level().getServer().getTickCount() - runtime.punchToggleTick <= 1) return;
        boolean vanillaMelee = player.isShiftKeyDown() && Guardians.isGuardian(player) && !ClientControls.gcb(player);
        if (!vanillaMelee) kim.biryeong.destiny.weapon.WeaponAiming.toggleKey(player);
    }

    public static boolean canAirJump(ServerPlayer player) {
        return !player.onGround()
                && !player.getAbilities().flying
                && !player.isInWater()
                && !player.isInLava()
                && !player.isNoGravity()
                && !player.isPassenger()
                && !player.onClimbable()
                && !player.isFallFlying();
    }
}
