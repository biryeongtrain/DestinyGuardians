package kim.biryeong.destiny.compat.gcb;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.gcbserver.events.PlayerCameraTypeChangedEvent;
import kim.biryeong.gcbserver.events.PlayerKeyStateChangedEvent;
import kim.biryeong.gcbserver.player.CameraType;
import kim.biryeong.gcbserver.player.Key;
import net.minecraft.server.level.ServerPlayer;

/**
 * GCB-mod 클라이언트의 키·시점 이벤트 연결 (docs/design/12).
 * Z 수류탄, V 근접, C 직업 능력, X 궁극기, 좌클릭(누름) 궁극기 기본 공격.
 */
public final class GcbInputBridge {
    private GcbInputBridge() {
    }

    public static void init() {
        PlayerKeyStateChangedEvent.EVENT.register(GcbInputBridge::onKey);
        PlayerCameraTypeChangedEvent.EVENT.register(GcbInputBridge::onCamera);
    }

    public static GuardianAction actionFor(Key key) {
        return switch (key) {
            case KEY_Z -> GuardianAction.GRENADE;
            case KEY_V -> GuardianAction.MELEE;
            case KEY_C -> GuardianAction.CLASS_ABILITY;
            case KEY_X -> GuardianAction.SUPER;
            case KEY_ATTACK -> GuardianAction.PRIMARY;
            default -> null;
        };
    }

    static void onKey(ServerPlayer player, boolean pushed, Key key) {
        Guardians.runtime(player).gcbClient = true;
        if (!pushed || !Guardians.isGuardian(player)) {
            return;
        }
        GuardianAction action = actionFor(key);
        if (action == null || (action == GuardianAction.PRIMARY && !AbilityService.inSuper(player))) {
            return;
        }
        InputRouter.dispatch(player, action);
    }

    static void onCamera(ServerPlayer player, CameraType type) {
        GuardianRuntime runtime = Guardians.runtime(player);
        runtime.gcbClient = true;
        runtime.gcbThirdPerson = !type.isFirstPerson();
        PlayerAnimations.refreshOwnerVisibility(player);
    }
}
