# W257 reload/탄약/퍽 GameTest 인계

slot5의 소유 GameTest 15개만 수정했다. 135개 `@GameTest`를 모두 유지했고 disabled/manual 전환, 허용 오차 확대, 피해 배율/탄약 기대값 완화는 하지 않았다. main과 제품 코드, 공통 TestPlayers는 이 작업에서 수정하지 않았다. 중앙 빌드/Java 컴파일/서버/GameTest 실행은 하지 않았다.

## 수정과 현행 계약 근거

| 파일 | 수정 및 유지한 검증 | main 근거 |
|---|---|---|
| WeaponAutoFireW48GameTests, WeaponEmptyReloadW49GameTests | 기본 무기 trigger 정책 fixture에 `WeaponAccessibility.setEnabled(false)`를 명시. 기존 native/two-hand 두 grip, semi-auto 1회 지불, burst, 재장전 후 fresh input 검증 유지. | `weapon/WeaponAccessibility.java:19`, `weapon/WeaponRuntime.java:222`: 기본 ON인 접근성 full-auto를 base profile과 합성한다. |
| WeaponReloadW47GameTests | 최종 wire 기대값을 `WeaponFirstPersonHands.model(reloadRoute)`로 합성. 실재 장전 소유권, 복제/preview 음성 대조군과 유한 탄약 3발 이동 유지. | `weapon/WeaponCombatItem.java:60`, `weapon/WeaponFirstPersonHands.java:47`: 승인된 경로를 마지막에 hand wrapper로 감싼다. |
| HandCannonReloadW64GameTests | Duke w215, Beloved w208 등 현재 53개 authored route를 독립 literal 표로 고정. catalog 전체의 지원/비지원 경계와 packaged item graph 존재까지 검증. 기존 불변/cleanup/탄약 테스트 유지. | `weapon/WeaponReloadPresentation.java:54`, 각 `assets/destiny/items/weapon_reload_*/...json`, `destiny/weapons/w201-first-person-hands.json`. |
| ReloadCreditW65GameTests, AutoRifleReloadW69GameTests, RecluseReloadW100GameTests | 외부 hand wrapper와 60 intervals/61 poses에 wire/CMD 기대값 정합. Ammit w207, Recluse w208, Duke w215, Beloved w208 명시. 지급/회복 경계 및 원본 모델 불변 assertion 유지. W65 earned-kill fixture에 동일한 분산 seed 사용. | `weapon/WeaponReloadPresentation.java:25`, `:54`; `destiny/weapons/w46-timing.json`, `w65-reload-credit.json`. |
| WeaponInsertW71GameTests | Long Arm w222, 61 samples, 현재 body bank의 initial60/loop00/loop60 양손 endpoint 연속성. 지원 경계를 Long Arm+shotgun 5개(6/65, 비지원59)와 개별 literal route로 검증. Shift ADS를 실제 toggle로 교체. preview/copy wire도 hand wrapper로 비교. | `weapon/WeaponInsertPresentation.java:35`, `:53`, `weapon/WeaponAiming.java:75`; `weapon/WeaponReloadPolicy.java:22`의 initial20/repeat13/2발과 return6, 총98틱은 변경하지 않았다. |
| WeaponKillClipW61GameTests, WeaponRampageW66GameTests, WeaponPrecisionReturnW67GameTests, WeaponAceW83GameTests, WeaponIzanagiW84GameTests | 실제 emission 직전 RNG seed를 고정해 피해/precision fixture의 조준을 재현 가능하게 한다. spread/cone/HP/ammo/perk/cadence 제품 경로는 그대로 실행한다. Ace/Izanagi는 preflight ray를 한 번만 얻고 같은 seed로 실사격하여 서로 다른 난수 ray를 비교하던 문제를 제거했다. W67 wall은 z=3 블록 이음매의 양쪽을 막고 원복한다. 배율/허용 오차/보상/만료 경계는 유지. | `weapon/WeaponAiming.java:211`, `weapon/ShotDispersion.java`, `weapon/WeaponRuntime.java:183`, `:853`: 실제 탄축에 stochastic dispersion을 샘플링한다. `sound/DestinySounds.java`는 player RNG가 아닌 level RNG를 사용한다. |
| PerksW226GameTests | Gutshot은 좌클릭 ADS toggle 및 재현 가능한 분산 seed를 사용하고 ADS body/hip/precision 피해 검증 유지. Cornered는 시작 시 비활성을 추가 확인하고 원본 T+14 경계에서 heartbeat/continue/tick을 먼저 실행한 후 정확히 1발 지불을 검증. | `weapon/WeaponAiming.java:75`; `weapon/WeaponRuntime.java:306` 및 `:390`의 charge acceptance snapshot, `weapon/WeaponCycle.java:30`의 tick-duration 경계. Dream Breaker 원본 667ms→14틱 유지. |
| DemolitionistW103GameTests | W252 throw의 T+6 방출/T+20 회복을 명시 검증. T+5 무지급, T+6 실 projectile+유한 탄약 이동, 실제 회복 뒤 T+21 발사, T+65 ICD 거절/T+66 정확한 1발 이동을 검증한다. 초기 T+8 full-magazine release 관찰은 유지. 재사용 token 거절과 독립 owner 검증 유지. | `ability/GrenadeThrow.java:15`, `ability/AbilityService.java:111`→`:115` 실행 순서; `weapon/WeaponDemolitionist.java:121`의 release 기준 owner ICD. |

위 Java 경로는 모두 `/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/` 기준이며, 리소스는 `/Users/qf/IdeaProjects/DestinyGuardians/src/main/resources/` 기준이다.

## 원본 타이밍 보존

- W65 full/credit: Duke 59/42, Austringer 53/38, Seventh Seraph 52/37, Fixed Odds 106/69, Hammerhead 91/60, Retrofit 90/59. 원본 JSON과 ceil(fraction)으로 정적 교차 확인했다.
- Ammit41, Beloved62, Long Arm20/13/2발 및 return6은 변경하지 않았다.
- 61포즈는 출력 selector 해상도이며 gameplay 시전/장전 시간을 바꾸지 않았다.

## 검증 및 후속 게이트

- 모든 소유 main 파일 및 보존 main-baseline의 SHA-256이 최초 ownership manifest와 일치한다.
- baseline→slot patch의 `git apply --check`가 main에서 성공했다. 실제 apply는 하지 않았다.
- 53 reload 경로와 6 insert 경로의 packaged item graph 및 hand mapping 존재를 확인했다.
- Long Arm current body/shell 732개 pose 리소스의 존재와 양 grip의 body endpoint transform equality를 확인했다.
- 135개 GameTest 유지, Java delimiter와 trailing whitespace 정적 검사 통과. 이는 Java typecheck 또는 GameTest 통과를 뜻하지 않는다.
- Cornered 실패를 callback 순서 문제로 단정하지 않는다. 경계에서 실제 입력 처리를 먼저 하도록 fixture 의존성을 제거했으며, master의 실행에서 T+14 실패가 남으면 accepted-charge/handling 상태를 확인해야 한다. 현재 근거로 제품 수정은 요청하지 않는다.
- 고정 seed는 precision/피해/탄약 계약 fixture에 한정한다. native 조작이나 분산 통계의 검증을 주장하지 않는다.
- 테스트명 한 개 변경: `HandCannonReloadW64GameTests.onlyDukeAndLegacyBelovedSupportReloadWrappers` → `authoredReloadRoutesCoverExactCurrentCatalogBoundary`. 나머지 이름과 테스트 수는 유지했다.
- 공통 TestPlayers 수정 요청은 없다.

## 산출물

- `reload-gametest.patch`: main-baseline 대비 전체 15파일 patch.
- `patches/`: 파일별 독립 patch 15개.
- `result-manifest.json`: baseline/current 파일 SHA-256, patch SHA-256, 소유 slot 경로, 테스트 수.
- `changed-files.txt`: 상대 경로 변경파일 목록.
- `static-validation.json`: 수행/미수행 검증 구분.
- 최초 `manifest.json`, `main-baseline/`, `slot-before/`는 보존했다.
