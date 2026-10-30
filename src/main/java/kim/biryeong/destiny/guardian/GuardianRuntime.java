package kim.biryeong.destiny.guardian;

import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.input.GuardianAction;
import net.minecraft.world.entity.player.Input;

import java.util.EnumMap;
import java.util.Map;

/** 저장하지 않는 플레이어별 실행 상태. 접속 중에만 유지된다. */
public final class GuardianRuntime {
    /** Server tick of the last melee-super forward step (MeleeSuperMovement). */
    public int meleeSuperStepAt = Integer.MIN_VALUE / 2;
    public Input lastInput = Input.EMPTY;
    public int lastShiftPressTick = Integer.MIN_VALUE / 2;
    public int airJumpsUsed;
    public int invulnerableTicks;
    public SuperSession superSession;
    public kim.biryeong.destiny.combat.SuperDamageResistance.Binding superResistance;
    public boolean gcbClient;
    public boolean gcbThirdPerson;
    /** GCB reported a real attack-key press: it, not the vanilla punch packet, drives ADS. */
    public boolean gcbAttackKey;
    public int punchToggleTick = Integer.MIN_VALUE / 2;
    public final Map<GuardianAction, Integer> lastActionTick = new EnumMap<>(GuardianAction.class);
}
