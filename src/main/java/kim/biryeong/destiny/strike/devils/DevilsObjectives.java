package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.campaign.presentation.ObjectiveTracker;
import net.minecraft.server.level.ServerPlayer;

/** Read-only projection of the shared encounter. The session owns the player's tracker lease. */
public final class DevilsObjectives {
    private DevilsObjectives() { }

    public static ObjectiveTracker.View view(DevilsDirector.Snapshot state, boolean atDevice, boolean hidden) {
        String objective = switch (state.phase()) {
            case READY -> "화력팀을 기다리세요";
            case BRIEFING, RY_APPROACH -> "정제소로 향하는 길을 확보하세요";
            case RY_CLEAR -> "화력팀과 함께 정제소로 이동하세요";
            case RF_ENTRY -> "정제소의 적을 처치하세요";
            case RF_DEVICE -> state.deviceReady() ? "고스트로 보안 장치를 조사하세요" : "고스트의 분석을 기다리세요";
            case RF_HACK -> "고스트가 보안 장치를 해킹하는 중입니다";
            case RF_DEFENSE1, RF_DEFENSE2, RF_DEFENSE3 -> "고스트를 보호하고 적을 처치하세요";
            case RF_INTERMISSION1, RF_INTERMISSION2 -> "다음 공격에 대비하세요";
            case RF_CLEAR -> "화력팀과 함께 폭파장으로 이동하세요";
            case BL_BATTLE -> "타락자 워커와 브리그를 파괴하세요";
            case BL_CLEAR -> "화력팀과 함께 악마의 소굴로 진입하세요";
            case SP_GUARD -> "세픽스 프라임의 호위 병력을 처치하세요";
            case SP_INTRO -> "세픽스 프라임이 깨어납니다";
            case SP_DAMAGE1, SP_DAMAGE2, SP_DAMAGE3 -> "세픽스 프라임을 파괴하세요";
            case SP_SHIELD1, SP_SHIELD2 -> "보호막을 유지하는 서비터를 파괴하세요";
            case SP_RECOVER1, SP_RECOVER2 -> "세픽스 프라임의 보호막이 무너지고 있습니다";
            case COMPLETE -> "세픽스 프라임을 파괴했습니다";
            case CLOSED -> "공격전 종료";
        };
        int count = 0, goal = 0;
        if (switch (state.phase()) {
            case RF_DEFENSE1, RF_DEFENSE2, RF_DEFENSE3, RF_INTERMISSION1, RF_INTERMISSION2 -> true;
            default -> false;
        }) {
            objective = "고스트 보호 · 방어 진행";
            count = state.defenseDefeated(); goal = 88;
        } else if (state.phase() == DevilsDirector.Phase.RF_ENTRY) {
            count = state.defeated(); goal = 24;
        } else if (state.phase().shieldPhase()) {
            int phase = state.phase() == DevilsDirector.Phase.SP_SHIELD1 ? 1 : 2;
            String prefix = "SP-servitor-" + phase + "-";
            count = (int) state.slots().stream().filter(s -> s.slot().id().startsWith(prefix)
                    && s.state() == DevilsDirector.SlotState.DEFEATED).count();
            goal = 3;
        } else if (state.phase() == DevilsDirector.Phase.BL_BATTLE) {
            count = (int) state.slots().stream().filter(s -> !s.slot().ordinary()
                    && s.state() == DevilsDirector.SlotState.DEFEATED).count();
            goal = 3;
        } else if (state.phase() == DevilsDirector.Phase.COMPLETE) { count = 1; goal = 1; }
        boolean interact = atDevice && state.phase() == DevilsDirector.Phase.RF_DEVICE && state.deviceReady();
        return new ObjectiveTracker.View("악마의 소굴", state.phase().name(), objective, count, goal,
                interact ? "웅크리기" : null, interact ? "고스트 배치" : null,
                null, null, hidden || state.phase() == DevilsDirector.Phase.CLOSED);
    }

    /** Remaining times come from the session clock; the HUD never advances encounter state. */
    public static ObjectiveTracker.View countdown(ObjectiveTracker.View view, DevilsDirector.Phase phase,
                                                   int gatherSeconds, int returnSeconds, boolean voicePlaying) {
        String objective = view.objective();
        boolean gathering = phase == DevilsDirector.Phase.RY_CLEAR || phase == DevilsDirector.Phase.RF_CLEAR
                || phase == DevilsDirector.Phase.BL_CLEAR;
        if (gathering && gatherSeconds >= 0) {
            objective = gatherSeconds > 0 ? "화력팀 합류까지 " + gatherSeconds + "초" : "안전한 합류 지점을 준비하는 중입니다";
        } else if (phase == DevilsDirector.Phase.COMPLETE && returnSeconds >= 0) {
            objective = returnSeconds > 0 ? "공격전 완료 · 귀환까지 " + returnSeconds + "초"
                    : voicePlaying ? "보고 종료 후 귀환합니다" : "귀환 준비 중입니다";
        }
        return new ObjectiveTracker.View(view.mission(), view.step(), objective, view.count(), view.goal(),
                view.key(), view.action(), view.toastTitle(), view.toastSub(), view.hidden());
    }

    public static void render(ServerPlayer player, DevilsDirector.Snapshot state, boolean atDevice, boolean hidden) {
        ObjectiveTracker.render(player, view(state, atDevice, hidden));
    }
    public static void render(ServerPlayer player, DevilsDirector.Snapshot state, boolean atDevice, boolean hidden,
                              boolean atSupply, boolean supplyAvailable) {
        render(player, state, atDevice, hidden, atSupply, supplyAvailable, -1, -1, false);
    }
    public static void render(ServerPlayer player, DevilsDirector.Snapshot state, boolean atDevice, boolean hidden,
                              boolean atSupply, boolean supplyAvailable, int gatherSeconds, int returnSeconds,
                              boolean voicePlaying) {
        var v = countdown(view(state, atDevice, hidden), state.phase(), gatherSeconds, returnSeconds, voicePlaying);
        if (atSupply) v = new ObjectiveTracker.View(v.mission(), v.step(), v.objective(), v.count(), v.goal(),
                supplyAvailable ? "웅크리기" : "보급", supplyAvailable ? "특수·중화기 탄약 보급" : "이 구역 보급 사용 완료",
                v.toastTitle(), v.toastSub(), v.hidden());
        ObjectiveTracker.render(player, v);
    }
    public static void remove(ServerPlayer player) { ObjectiveTracker.remove(player); }
}
