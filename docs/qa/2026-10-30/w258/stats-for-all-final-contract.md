# W258 StatsForAll 단일 파일 반환

- 새 소유 파일: `src/gametest/java/kim/biryeong/destiny/test/StatsForAllW176GameTests.java` 하나만 편집. 기존 20개는 재편집하지 않음.
- main 기준 SHA256: `fb6352076cca3ee111d6ce5adc93bc5ed03856ae78e9da09f6ec54177df7e722`
- 결과 SHA256: `6971b7147b6c8ae4ea9aa482a468cc056567c8d9121929d25844278596de1932`
- `baseline/`, `slot-before/`, `result/`와 `repair.patch`, `manifest.json` 제공. main 현재 hash는 기준본과 동일.
- fourth-run.log:1051 및1413에서 tick36의 실제 장거리 피해 비교 실패를 확인. 로그에는 두 실제 피해값이 없어 miss/precision 중 어느 경우였는지는 확정하지 않음.

## 원인과 계약

기존 Fixture.fire는 매번 ADS/bloom을 초기화하여 hip-fire로 발사하지만 RNG는 고정하지 않았다. W241 이후 장거리 두 발은 서로 다른 stochastic ray라서 몸통 명중 비교 조건이 성립하지 않을 수 있다. ADS를 켜면 falloff 배율까지 달라지므로 기존 hip-fire 계약을 유지한다.

현재 Ammit base Range 61, 기본 falloff 18.375..40.0, Stats for All의 +10 Range 후1.05 곡선 20.60625..42.0. 기존 x2.5 플레이어와 x30 표적의 명목 충돌거리는 약27.17로 두 곡선의 경사 구간에 있다. 따라서 표적 거리나 기존 `improved > baseline + .01`을 변경할 이유가 없다.

- Fixture.fire는 `0x5DEECE66DL` seed로 실제 산포를 유지하며 명중을 재현한다.
- 해당 장거리 테스트만 같은 seed의 ray를 preflight하여 실제 몸통·막힘 없는 corridor·hip-fire 상태를 확인한다. 후속 유료 방출은 같은 seed를 재생한다.
- 실제 baseline/강화 HP 손실을 각각 원래/+10 Range→1.05 곡선의 body damage와 .001 이내로 비교한다. 두 충돌거리도 동일해야 한다. 기존 비교조건을 강화했으며 완화하지 않았다.
- 두 근거리 유료 타격과 마지막 장거리 발사를 gap/2gap/3gap에 미리 등록했다. 원래12/24/36틱 및200틱 발동 계약 유지. positive token 주입/무료 탄약 없음.
- 기존 10개 GameTest 이름·annotation·timeout 보존. 새 테스트, disabled/manual 전환 없음.

## 확인 범위

기준본에 git apply --check 통과. Java tree-sitter 문법 파싱 통과, 기존 테스트 식별자·annotation 동일, main hash drift 없음. 빌드·Gradle·런타임·Vision/CU 미실행. 실제 실행 통과 여부는 master 중앙 재실행 필요. 기존20개 통과는 사용자가 전달한 fourth-full 결과이며 이 worker가 새로 실행한 결과가 아니다.
