# W258 JUnit sidecar — 테스트 변경 없음

## 결론

네 실패는 W251 canonical 형상/UV 변경 후 파생 자산과 provenance가 함께 갱신되지 않은 상태를 검출한다. 현행 계약에 근거해 안전하게 통과시킬 테스트 수정은 없다. 테스트 4개를 main baseline 그대로 유지했고 빈 followup.patch/changed-files.txt를 반환한다. 실패 삭제·disabled·manual 전환·expected 숫자/해시 교체는 하지 않았다.

## 실패별 근거

| 테스트 / 실패 지점 | 현재 원본과 생성물 | 판정 |
|---|---|---|
| ReloadW168AustringerTest:37, exactSourceElementsAndUvPartitionWithoutDuplication | W123 현재 full 170, W168 body114+moving12=126. 현재 활성 W208도 두 파트 elements/textures가 W168과 exact 동일 | 현재 원본과 exact disjoint partition 계약 불일치. 126을170으로 바꾸어도 실제 조립체가 부족하며, 옛32..43 인덱스는 새 원본에서 cylinder가 아니다. |
| InsertW179MindbenderTest:45, canonicalBodyAndUvsExactAndConnectedHiddenShellBudget | 현재 canonical189, W179 body104+shell12. 현재 활성 W221 body/shell은 W179 elements/textures와 exact 동일 | canonical body exact-copy 계약 불일치. body189 expected로 교체하거나 elements 비교를 제거하면 결함을 가린다. |
| WeaponSurfaceW115Test:283, everyExistingAimGripInspectAndReloadPoseResolvesToExactlyOneReplacedGeometry | W151 source pin 두 개 불일치. Blast Furnace 현재178 대 sight99=옛97+2; Hammerhead 현재245 대 sight165=옛163+2 | W151 현재 W123 + 두 sight pin 계약 불일치. 해시만 바꿔도 다음 element/order 비교 실패. |
| WeaponSilhouetteW112AssetTest:86, currentSourceInputsAndAllOutputBytesMatchManifestHashes | inputs_sha256 중 surface migration manifest 불일치. HUD 개별 원본5종도 불일치: Austringer126→170, Blast97→178, Recluse66→143, Mindbender104→189, Hammerhead163→245 | current default migration geometry에서 생성한다는 HUD 계약 불일치. manifest pin 하나만 갱신해도 개별 source hash/element 비교가 실패. |

## 현행 계약과 경로 근거

- scripts/generate_reload_w168_austringer.py:147–157은 source SHA, 126원소, cylinder 이름/indices, fixed frame을 검사한 뒤 원본 elements를 무손실 분할한다. :176–184에는 partition 근거와 geometry/UV 보존이 명시돼 있다. 현재170 geometry를 옛 인덱스로 분할하면 안 된다.
- scripts/generate_insert_w179_mindbender_s_ambition_adept.py:257–271은 source/migration pin과104원소를 확인하고 body를 deep copy한다. shell UV도 같은 source에서 유래한다(:124–156).
- WeaponReloadPresentation.java:68은 Austringer를 W208로, WeaponInsertPresentation.java:42는 Mindbender를 W221로 연결한다. 그 item JSON의 model/parent를 읽기 전용으로 추적해 각각 old114+12 / old104+12 geometry가 남아 있음을 확인했다. 숨김 shell0은 정상 별도 경로다.
- WeaponAimPresentation.java:30–41은 Blast/Hammerhead를 W151 sight로 연결한다. art/weapons/w151/pulse-sights.json은 현재 W123 원본 해시와 요소를 선언하지만 두 무기의 원본 해시와 실제 body가 맞지 않는다.
- scripts/build_weapon_hud_w112.py:82–112는 default emitted W123 migration을 원본으로 선택하고 stale pin에 fail하도록 명시한다. :281–299는 source hash, current-source profile과 input pin을 출력한다. AmmoHud.java:39,126은 이 W112 sprite들을 사용한다.
- WeaponSurfaceW123Assets.java:18–99,118–161은 명시적80 target만 migration한다. 위 W168/W179/W208/W221/W151 baked body는 target에 없다. ProfileArmAssets의 gunOnly와 WeaponPackOptimizer는 selector/동일 모델 공유를 처리하며 원본170/189 geometry로 재생성하지 않는다.
- docs/qa/2026-10-29/w251/README.md:21–23에 다섯 원본의 형상 증가와12개 교체모델, targeted9 tests가 기록돼 있다. 이후 W257 full-gate.json은2225 tests 중 동일4개 실패를 기록한다.

## 권장 후속 작업

master가 별도 자산 소유권을 배정해 canonical 변경을 장전/삽탄/ADS/HUD 생성 체인까지 전파해야 한다. Austringer는 현재 semantic cylinder/fixed-frame 분할을 재검토하고 새 부품의 움직임 소속을 명시해야 한다. Mindbender는 현재 body exact copy와 shell donor UV를 점검해야 한다. W151은 현재 source와 두 sight pin을 재조립하고 W112는 default migration을 따라 생성물과 provenance를 함께 재생성해야 한다. historical W168/W179 자산을 보존할 계획이라면 검증 가능한 immutable source fixture 및 현재 active-bank 별도 exactness 검증 계약을 먼저 확정해야 하며, 이전 기대값만 남기기 위해 현재-source 비교를 제거하지 않는다.

이 보고서는 디스크 원본/생성물/코드에 대한 정적 근거다. 생성팩 또는 화면에서 나타나는 시각적 결과를 확인했다고 주장하지 않는다. failure-evidence.json의 active_routes fallback 수치는 migration 전 원본 JSON의 수치이며 default pack은 W123 converter의170/189/178/245로 교체한다.

## 보존과 검증

main-baseline/와 slot-before/에 네 파일 원본 보존. baseline-manifest.json에 입력 SHA256, result-manifest.json에 종료 시 main/slot 재확인 SHA256. 네 파일 모두 baseline과 exact 동일. main 쓰기, 제품/자산 수정, Gradle, Java/JUnit 실행, 서버/client/runtime 조작 없음. Python으로 JSON/해시/참조 관계만 읽기 검증했다. 중앙 JUnit 통과 결과는 없으며 네 실패 해결을 주장하지 않는다.
