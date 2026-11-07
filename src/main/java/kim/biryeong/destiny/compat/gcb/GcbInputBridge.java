package kim.biryeong.destiny.compat.gcb;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.input.ClientControls;
import kim.biryeong.gcbserver.player.GCBPlayer;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.gcbserver.events.PlayerCameraTypeChangedEvent;
import kim.biryeong.gcbserver.events.PlayerKeyStateChangedEvent;
import kim.biryeong.gcbserver.player.CameraType;
import kim.biryeong.gcbserver.player.Key;
import net.minecraft.server.level.ServerPlayer;

/**
 * GCB-mod 클라이언트의 키·시점 이벤트 연결 (docs/design/12).
 * Z 수류탄, C 근접, V 직업 능력. F 궁극기는 InputRouter의 손 교환 패킷으로 처리한다.
 */
public final class GcbInputBridge {
    private GcbInputBridge() {
    }

    public static void init() {
        ClientControls.setDetector(player -> {
            GCBPlayer gcb = (GCBPlayer) player;
            return new ClientControls.Capability(gcb.gcb$hasMod(), gcb.gcb$getModVersion());
        });
        PlayerKeyStateChangedEvent.EVENT.register(GcbInputBridge::onKey);
        PlayerCameraTypeChangedEvent.EVENT.register(GcbInputBridge::onCamera);
    }

    public static GuardianAction actionFor(Key key) {
        return switch (key) {
            case KEY_Z -> GuardianAction.GRENADE;
            case KEY_C -> GuardianAction.MELEE;
            case KEY_V -> GuardianAction.CLASS_ABILITY;
            case KEY_ATTACK -> GuardianAction.PRIMARY;
            default -> null;
        };
    }

    static void onKey(ServerPlayer player, boolean pushed, Key key) {
        ClientControls.gcb(player);
        if (key == Key.KEY_ATTACK || key == Key.KEY_USE)
            kim.biryeong.destiny.weapon.GcbWeaponInput.key(player, key == Key.KEY_ATTACK, pushed);
        if(pushed&&key==Key.KEY_USE&&InputRouter.onUseItem(player,net.minecraft.world.InteractionHand.MAIN_HAND)
                !=net.minecraft.world.InteractionResult.PASS)return;
        if (pushed && key == Key.KEY_0) {
            kim.biryeong.destiny.inventory.WeaponScreen.toggle(player); return;
        }
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) return;
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
        ClientControls.gcb(player);
        runtime.gcbThirdPerson = !type.isFirstPerson();
        PlayerAnimations.refreshOwnerVisibility(player);
    }
}
