# 악마의 소굴 3인 실행 · 이탈 후 재접속 (2026-11-04)

격리 QA 서버(`/tmp/destiny-devils-qa-20261103`)에서 Vision 클라이언트 3개(DevilsQA·DevilsQA2·DevilsQA3)를 함께 넣어 공격전을 두 번 진행했다. 처치는 `/damage` 장치로 처리했으므로 서로 다른 직업의 실제 전투나 난이도 판단은 이 기록에 포함되지 않는다.

## 1차 실행
- BL 전투에서 27/32 행위자 상태로 10분 유지했다. `tick query` 20회 결과가 `run1-tick-percentiles.txt`에 있다. P50은 약 0.9ms이고 P95는 1.3–4.0ms, P99는 최대 30.2ms다. 기획 목표인 P95 ≤ 45ms를 만족한다.
- RY→RF 전환에서 `Can't keep up` 경고가 한 번(2.1초) 나왔다. 2차 실행 때 JFR로 기록했지만 같은 정지는 재현되지 않았고, 시작 시 경고만 남았다. 전환 구간 기록의 GC 정지는 P95 91.8ms, 최대 약 109ms였다. 이 정지를 공격전 코드 때문이라고 판정하지는 않았다. 원인은 아직 찾지 못했다.
- 클라이언트 FPS가 모두 10으로 찍혔다(`run1-fps.json`). Mac 메모리 스왑이 14–15GB인 상태였으므로 성능 측정값으로 보지 않는다.
- 유지 후 DevilsQA3가 떨어졌고, 남은 두 명이 공격전을 끝까지 완료했다.

## 2차 실행
- 전 구간을 COMPLETE까지 진행했다(`run2-phases.json`, `run2-phases-sheet.jpg`). 백그라운드 클라이언트 FPS는 약 30이다.
- 이번 수정 전에는 세션이 끝난 뒤 DevilsQA3가 다시 들어오면 `Force-added player with duplicate UUID`가 기록됐다. JOIN 이벤트는 플레이어가 레벨에 등록되기 전에 호출되는데, 이때 차원을 넘는 순간이동을 하면 같은 플레이어가 두 레벨에 등록된다. 그래서 `DevilsLair` 복귀와 `GuardianDown`의 월드 아래 구조를 대기열에 넣고, 해당 연결의 엔티티가 레벨에 등록된 뒤 tick에서 처리하도록 바꿨다. 수정 후 재접속에서는 중복 경고가 나오지 않았다.

## 재접속 후 무기·HUD가 비어 보인 현상
`qa3-rejoin-after-complete.jpg`의 DevilsQA3는 손이 비어 있고 탄약 HUD도 없다. 서버에서 인벤토리를 확인하니 DevilsQA3뿐 아니라 끊김 없이 완료한 DevilsQA2도 빈 상태였다(`qa2-completed-no-loadout.jpg`). 장비를 갖춘 DevilsQA는 무기와 탄약 HUD를 유지했다(`qa1-completed-with-loadout.jpg`). 공격전은 인벤토리를 지우지 않으며 보급도 탄약만 바꾼다. 따라서 이 현상은 재접속 회귀가 아니라 QA 계정 두 개가 처음부터 장비를 받지 않은 상태 때문이다. 탄약 HUD는 장착 무기가 있을 때만 표시된다.

## 남은 검증
- 서로 다른 직업 3명의 실제 전투와 사용자 난이도 판정
- 부하가 적은 환경에서 포그라운드 FPS 측정
- 스피커로 직접 듣는 믹스 확인
