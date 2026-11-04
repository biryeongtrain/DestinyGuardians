# 공용 길 안내(웨이포인트·브레드크럼) — 2026-11-04

## 변경
- 캠페인 W301 웨이포인트와 브레드크럼을 `activity/presentation` 공용 코드로 승격했다.
  - `GuideRoute`: 걷는 경로 점 목록(점프 플래그), 가장 가까운 점·구간 계산.
  - `GuideTrail`: 소유자 전용 바닥 파티클 경로와 경로 없을 때 직선 대체.
  - `ObjectiveWaypoint`: 벽 투과 마름모+거리, 화면 크기 고정. 플레이어별 인스턴스, 정적 전역 맵 없음.
  - `ObjectiveGuide`: 이동(TRAVEL)/전투(COMBAT) 모드, 25초 진행 없음 시 길 잃음 판정, 숨김 처리.
- 캠페인(`RisingObjectives`, `RisingRoutes`)은 공용 클래스를 사용한다. 기존 동작 값은 유지했다.
- 악마의 소굴 어댑터 `DevilsGuide`: 단계별 목표 마커와 구역별 마커 체인 경로.
  - RY 접근전 → RY.C2 (전투, 길 잃었을 때만), RY/RF/BL 정리 → 출구, RF 장치 → RF.G, BL 전투 → 출구(길 잃었을 때만).
  - 다운·시네마틱·배치 중·부활 대기 중에는 숨기고, 이탈/접속 끊김/세션 종료에서 정리한다.

## 검증
- 단위: `ObjectiveGuideTest`(3), `ObjectiveWaypointTest`(1), `RisingRoutesTest`(7), `DevilsGuideTest`(2) 통과, `jar` 빌드 통과.
- 실화면(격리 서버, 1인 DevilsQA, 백그라운드 Vision): RY 접근전에서 25초 정지 후 마커 `44m`가 벽 너머로 표시됨 (`guide-lost-marker.png`), 바닥 하늘색 브레드크럼 확인 (`guide-trail-sheet.png`). 서버 로그 ERROR/Exception 0건.
- 미검증: 정리 단계 TRAVEL 모드 실화면(전투 완료 필요), RF 장치·BL 경로의 실제 지형 일치, 3인 동시 표시.
- 마커 체인 경로는 직선 연결이라 벽을 통과할 수 있다. 필요하면 구역별 routes 데이터를 작성해 교체한다.

## 브리핑 포즈 무기 (추가)
- 브리핑 포즈를 시작할 때 원래 들고 있던 무기 모델을 몸 리그 손 본(`pri_right_item`)에 시각 전용으로 붙인다(`PlayerAnimations.superItem`). 실제 슬롯은 계속 비워 두므로 1인칭 무기와 바닐라 손 아이템은 나타나지 않는다.
- 실화면: 1인 브리핑에서 착지 후 오른손에 흰 소총 모델 확인 (`briefing-weapon-in-hand.png`). 3인 동시 확인과 근접 무기·활 파지 각도는 미검증.
