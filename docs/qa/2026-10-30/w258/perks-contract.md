# W258 perks 반환

지정 20개 Java 경로만 수정. 기존 GameTest 148개 이름·annotation·timeout·구조체·환경 모두 유지. 새 테스트 없음. main 및 공통 TestPlayers 수정 없음.

## 반환 파일

- repair.patch: 주어진 current-main 기준 SHA256 → 최종 수정본 unified patch (HEAD 대비 아님).
- manifest.json: 경로별 기준/결과/main 현재 SHA256, 원래 테스트명·annotation, 한국어 이유.
- baseline/ 및 result/: 각 20개 기준본/결과본.
- product-bugs.md: assertion을 유지한 제품 결함 증거.
- owned-run2-failures.json: 전달받은 run2에서 이 범위의 실패만 추출.

## 검사와 미검증

- 보존된 기준본에 git apply --check 통과.
- 기준본 20개 SHA256 일치 확인 후 보존. 최종 Java tree-sitter 문법 파싱 20/20 통과. 타입/링크/컴파일 통과를 뜻하지 않음.
- 기존 테스트 이름과 annotation 전수 동일, disabled/manual 전환 없음. 기존 배율·탄약 credit·만료·소유권 조건 유지.
- runAfterDelay는 전부 상대 deadline을 보존하는 startSequence().thenIdle().thenExecute()로 변경. 26.3 GameTestSequence 바이트코드 정적 확인: 생성 시 parent.getTick() 저장, thenIdle(int) 지원. 실제 게임 실행 없음.
- 정밀 명중은 동일 near-axis seed를 preflight/유료 방출에 사용. 충전·지연 bolt는 실제 tick 전 재조준/seed를 공급하며 paid token은 주입하지 않음.
- 빌드/Gradle/GameTest 실행/Vision/CU/commit/reset/stash/clean/push 및 child agent 모두 미실행. 중앙 run3에서 컴파일·실행 필요.
- 시작 readiness의 독립 master 작업은 변경하지 않음. W203의 기존 BetterModel readiness gate 유지.

## 파일별 계약 근거

- `SubsistenceW167GameTests.java`: 실제 유료 발사를 고정 난수로 재현. 비가디언 런타임 미생성 assertion은 제품 결함 증거로 유지.
- `RapidHitW169GameTests.java`: 정밀/몸통 preflight와 발사에 같은 seed 재사용. 화살은 실제 release 시 seed 설정. x5, 40틱, 장전 snapshot 보존.
- `PerpetualMotionW170GameTests.java`: 좌클릭 ADS 입력으로 교체. 이동40/200틱·정지유예·재장전 수치 유지.
- `TapTheTriggerW171GameTests.java`: 기존 bloom ring 대신 W241 hip+bloom/독립 air cone 및 동일 seed의 disk ray를 정확 비교. 12틱, .9, recoil .5 유지.
- `FocusedFuryW174GameTests.java`: 실제 precision/body preflight와 발사 seed 일치. 6발/220틱/1.25 배율 및 Triple Tap 탄약 보존.
- `FrenzyW172GameTests.java`: 좌클릭 ADS 및 비교 로켓 동일 발사 seed. 240틱 활성화, 144틱 유지, 1.15 및 reload credit 유지.
- `ThreatDetectorW178GameTests.java`: 좌클릭 ADS 입출력 및 실제 명중 seed. 15m 구체, tier2, .81 ready/stow 및 ADS 단일 ceil 유지.
- `HeatingUpW177GameTests.java`: 유료 처치 seed 고정. .75 growth와 .75 cone을 W241 수식에서 별도로 검증, 110틱과 x2 보존.
- `SurplusW183GameTests.java`: 좌클릭 ADS·고정 명중 seed. 충전개수/실제 cooldown/장전 snapshot 및 paid damage 유지.
- `VorpalW181GameTests.java`: 실제 충전 heartbeat 및 tick 전 재조준/seed. boss 1.2/1.15/1.1과 교체 후 발사원 소유권 검증 유지.
- `HighImpactReservesW182GameTests.java`: 지연 fusion/pulse bolt를 매 tick 동일 aim/seed로 비교. 원래 탄약선결제량·공유 token·수정 후 배율 assertion 그대로.
- `ElementalCapacitorW184GameTests.java`: 좌클릭 ADS 및 정밀/몸통 유료 발사 seed. 실제 SUPER element, raw stat 합성과 소켓 권한 유지.
- `QuickdrawW185GameTests.java`: Shift packet 대신 생산 좌클릭 라우터. handling 중 클릭 소비/동일틱 debounce 검증. 20틱·기존 swap/ADS/reload 수치 보존.
- `FirmlyPlantedW189GameTests.java`: 실제 crouch 검증은 그대로. ADS만 좌클릭으로 교체. .83 growth/.6 cone/.2 yaw를 W241 cone+sample로 정확 비교.
- `PerksW191GameTests.java`: 기본 full-auto ON 확인 후 명시 OFF로 opt-out하여 퍽 자체 연사를 검증. 퍽이 preference를 변경하지 않는 assertion 유지.
- `PerksW192GameTests.java`: 수류탄 활성 중 중복 입력 BUSY 계약 반영. 퍽 stack/소유권 보존. LFR 실제 방출 전 재조준/seed, .7 charge/.8 damage 유지.
- `PerksW194GameTests.java`: W241 두 nextDouble 뒤 Mulligan nextInt(100)=15가 되는 seed0 사용. 무적 geometry contact는 near-axis seed. ADS 좌클릭/기존 sword 지연 보존.
- `PerksW203GameTests.java`: 수류탄20틱 복구 중 무기 HUD 숨김/BUSY, 복구 후 기존 SOLAR/VOID 아이콘과 COOLDOWN 검증. 1회 refill·stow reset·foreign modifier 보존.
- `PerksW195GameTests.java`: Opening Shot/Box Breathing 실제 발사 seed. 좌클릭 해제 후 debounce3틱을 기다려 재진입, 원래 다음 발사 deadline 및 소비된 buff 비상속 검증 유지. sword guard Shift 유지.
- `PerkReadyHudW200GameTests.java`: 좌클릭 ADS 실제 release는 ready cycle 폐기. 순수 HUD 조회 무변경 검증 유지하고, debounce3틱 후 새32틱 ADS로만 다시 ready되는지 검증.

## 남은 제품 결함

Subsistence의 ordinaryLiveWeaponOwnerDoesNotNeedAnAbilityRuntime는 런타임 미생성 assertion을 그대로 유지했다. WeaponFireMotion.visible의 Guardians.runtime(p) 생성 부작용을 master가 검토해야 한다. 테스트를 느슨하게 만들어 통과시키지 않았다.
