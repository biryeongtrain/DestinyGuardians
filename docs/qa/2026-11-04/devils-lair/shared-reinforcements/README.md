# 공용 증원 코드 추출 — 2026-11-04

사용자 지시: 잠깐 보이는 무적 스키프의 미술 정밀 검증보다 증원 시스템을 우선한다.
다른 공격전/시스템에서 쓸 가능성이 있는 기능은 공용 코드로 작성한다.

## 변경

- `activity/reinforcement/ReinforcementQueue`: 중복 팩 방지, FIFO, 활동의 cap predicate,
  실제 첫 투입에 따른 다음 팩 간격 보정, 선택/전체 취소, 세대 초기화.
- `SpawnAttemptBudget`: 틱당 작업 상한과 round-robin. 두 막힌 지점의 1틱 재시도가
  뒤의 안전한 지점까지 무한 대기시키던 문제를 공통 경로에서 방지한다.
- `SpawnWarnings`: 선택 지점/충돌 예약, 전체 경고 시간, generation 조회와 pruning.
- DevilsDirector/DevilsSpawnTelegraphs가 이 구현을 실제 사용한다.
  최대 몹/팩, 보스 단계, 1~3인 입장·3인 고정 난이도는 기존 활동 어댑터에 남겼다.
- AGENTS.md에 향후 공용 코드 우선 지시를 기록했다.

## 검증

- targeted.log 및 6개 JUnit XML: 35 tests, 0 failures/errors.
- actor.log 및 actor-report.xml: 실제 Fabric GameTest 14 tests, 0 failures/errors.
  실제 월드 삽입 후에만 연출에 알리고, 연출 예외가 성공한 투입을 취소하지 않는 경로 포함.
- 이전 순회 구현에서 starvation 회귀가 실패한 증거는 ../reinforcement-fairness/before.log.
- 전체 회귀/실제 Gradle JAR 결과는 regression.json 및 full.log에 별도 기록한다.

이번 변경은 서버 측 공통화다. Vision 클라이언트는 실행하지 않았다.
수송선 모델의 strike 연결/도착·퇴장 화면 검증과 전체 실제 플레이 수락은 아직 남아 있다.
서버 테스트 통과를 수송선 화면·오디오 청취·3인 난이도 수락으로 해석하지 않는다.

전체 회귀: 2,578개 실행, 기존과 동일한 16건 실패, 신규 실패 0건. `test`는 실패 상태이며
`--continue`로 실제 Gradle `jar` 태스크는 성공했다. JAR 내부 공통 클래스 6개를 확인했다.
