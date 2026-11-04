# 특탄·궁극기 드렉 처치 기준 (기획 §6)

기획 §6에는 특탄을 정상 유효거리에서 중심 명중하거나 직접 타격형 궁극기를 정상 명중하면 일반 드렉 1기를 확실히 처치해야 한다는 기준이 있다. 이를 실제 발사 경로로 검사하는 GameTest 두 개를 `DevilsWalkerGameTests`에 추가했다.

- `specialShotgunCentreHitKillsOrdinaryDreg`: 공격전 대여 샷건 `mindbender_s_ambition_adept`을 사용한다. 5블록 거리에서 드렉 중심을 조준해 `WeaponRuntime.beginUse/releaseUse` 한 번으로 발사하면 드렉(HP 20)이 사망한다.
- `directSuperShotKillsOrdinaryDreg`: 솔라 헌터 황금총을 `AbilityService.use(SUPER)`로 활성화하고 PRIMARY 발사 한 번을 쏘면 7블록 거리의 드렉이 사망한다.

두 테스트의 드렉은 `DevilsActors`로 생성한 실제 공격전 행위자다. 감독기가 배정한 슬롯과 계획 HP를 쓰고, 참가자 소유권 검사와 `allowedDamage`를 그대로 통과한다. 피해를 직접 주입하거나 드렉 HP를 낮추지 않았다. `PveDamageBalance`의 특탄 2.5배·궁극기 3배 외에 공격전 전용 배율은 없다.

실행: 필터 `destiny-test:devils_walker_game_tests*`로 `runGameTest`를 실행했고 18/18이 통과했다(`gametest.xml`).

검사 범위: 산탄 일부만 맞은 경우, 사거리를 벗어난 경우, 지속형 궁극기의 단일 tick, 다른 직업의 직접 타격 궁극기는 이 검사에 포함되지 않는다. 실제 3인 전투 판정은 사용자가 따로 진행한다.
