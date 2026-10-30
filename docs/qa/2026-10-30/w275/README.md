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

## 2차 보강 (카메라·타이틀·결과 실화면)
- 인트로 카메라: 높은 크레인 샷에서 대치 구도로 하강 → 양 팀 푸시인 → 와이드 풀백(`safe()`로 충돌 시 정지 샷 대체).
- 타이틀 카드 구간을 8~176틱으로 늘려 팀 명단 전에 충분히 노출(`intro_sequence_contact_sheet.png` 4번째 컷).
- 카운트다운 배너 크기 보정 후 재촬영, 시작 플래시(PostEffect) 컷 확인(11번째 컷), 결과 "승리 0:0" 카드 확인(`results_contact_sheet.png`).

## 한계
- 타이틀 카드 글자가 작고 채팅창과 겹친다(채팅 숨김 상태로 재촬영 필요). 점령 토스트는 실제 점령 없이는 캡처하지 못했다.

## 3차 보강
- 타이틀 카드 글자 확대(점령 120px), 카메라 주시점을 낮춰 아바타가 하단 로스터 HUD 위쪽에 놓이도록 조정. `intro_sequence_v3.png`에서 확인.
- 점령 토스트는 여전히 실화면 미확인.

## 4차: 점령 토스트
- QA 전용 `/crucible toast <cue>`(OP)로 토스트를 실화면 확인: `toast_capture.png`(A 거점 점령, 아군 청록), `toast_enemy_power_play.png`(적 파워 플레이, 적 적색).
- 캡처 당시 목표 배너·일시정지 배너와 겹쳐서, 토스트가 떠 있는 동안 목표 배너를 숨기도록 수정(재촬영 안 함). 일시정지 배너 겹침은 상대 없는 QA 상황에서만 발생.
