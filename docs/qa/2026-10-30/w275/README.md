# W275 시련의 장 초반 연출·UI (데스티니 점령전 스타일)

## 변경 요약
- `CrucibleUi` (DisplayHud): 레터박스 → 타이틀 카드(시련의 장/점령/맵/지역) → 아군·적 로스터 → VS → 5초 카운트다운 → "시작".
- 진행 중: 상단 중앙 점수 바(150점 한도)·타이머 플레이트·A/B/C 거점 다이아몬드(점령 진행도 채움)·목표 배너·이벤트 토스트(점령/상실/파워 플레이)·일시정지/부활 배너·결과 카드.
- 스프라이트는 `scripts/hud/build_crucible_hud_w275.py`로 생성한 흰색/알파 텍스처를 custom_model_data 색으로 런타임 틴트(아군 청록/적 적색).
- PostEffect: `crucible/intro`(차가운 시네마틱 보정·비네트), 카운트다운 숫자마다 `tick_pulse`, 시작 시 `start_flash`.
- 버그 수정: 시련의 장 입장/퇴장 시 다른 시청자 클라이언트의 가상 팀(`dgV…`)이 남아 있는 채로 서버가 `dg_control_*` 팀 REMOVE를 브로드캐스트 → 클라이언트가 `Cannot remove from team` 로 접속이 끊김. 팀 변경 전에 `CrucibleTeamVisuals.invalidate()`를 호출해 해결(CrucibleRuntime·CrucibleRecovery).
- 텍스트 LEFT/RIGHT 정렬: 라이브러리의 스페이서 보정이 맞지 않아 폭을 추정해 중앙 정렬로 변환(`estimateWidth`).

## 검증 (Vision 실화면, GCB 4.2 클라이언트 + 2인 매치 fixture)
| 단계 | 증거 |
|---|---|
| 로스터 | ![](intro_roster.png) |
| 카운트다운 | ![](intro_countdown.png) |
| 진행 HUD | ![](playing_hud.png) |
- 수정 전: 입장 즉시 클라이언트 disconnect(로그 `Cannot remove from team 'dg_control_alpha'`). 수정 후 재현 없음.
- `*Crucible*` 단위 테스트 통과(`CrucibleUiTimelineTest` 추가).

## 남은 작업 / 알려진 한계
- 카운트다운 배너 크기는 촬영 이후 조정(`505/260`)했으며 재촬영하지 않았다.
- 결과 화면·점령 토스트·시작 플래시의 실화면 캡처는 아직 없다.
- 인트로 액터/카메라 연출(맵 팬)은 이번 범위에서 변경하지 않았다.
