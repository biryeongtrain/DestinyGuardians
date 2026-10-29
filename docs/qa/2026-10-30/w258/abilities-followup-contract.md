# followup03 반환 — 중앙 재실행 대기

소유 5파일 수정, 기존 3개 실패 + 추가 Titan/Warlock 5개 실패 대응. **실행 통과는 아직 미확인**. H20 3개는 아래 근거를 반환하며 소스와 strict assertion을 보존했다. readiness 4개 및 timeout은 변경하지 않았다. main/제품/공통 TestPlayers/자산 변경 없음.

- `existing-followup.patch`: 통합된 followup01+02의 현재 main/slot 기준. Dragonfly, Payload, Tracking 3파일.
- `extra2.patch`: 추가 소유 manifest의 seed 기준. Titan/Warlock 2파일.
- `return-manifest.json`: 파일별 baseline/returned SHA256와 patch SHA256. `returned/`에 반환본, `returned-baseline/`에 변경 전 사본.

## 수정 근거

1. Dragonfly equal-token: InventoryAceMixin.setItem → WeaponRuntime.inventoryStowing → WeaponAiming.inventoryStowing가 outgoing stack의 ADS/fire 표시를 정리한다. 먼저 EMPTY로 실제 stow 후 복사하여, **동등한 serialization + 다른 object identity**를 모두 검증한다. perk/원본 미소유/피해/탄약 불변 assertions 유지.
2. Payload cap: 130개의 동일 좌표 Husk를 ADS 40틱 대기 전에 생성하면 cramming 환경 피해를 받을 수 있다. 발사 직전에 생성하고 pre-shot HP1000·wall 비충돌을 검증한다. 130개 전부의 정렬 거리, 피해0, cap 비소모 및 exposed 피해 assertions 유지. HP 재설정이나 gamerule 변경 없음.
3. Tracking hip control: W241 hip random axis는 정상이다. world Z=0 대신 **처음 관측한 실제 속도벡터 불변 + 위치 차이가 그 속도와 일치**함을 매틱 검증한다. target=null, tracking=false, 속력 및 3도 turn bound도 유지. 벡터 오차제곱 각각 1e-14 / 1e-12; 후자는 수백만 블록 world 좌표 뺄셈 오차용이다.
4. Titan/Warlock roster: 각 registrar 10개 + expanded super 3개 + JumpAbilities Titan3/Warlock4 = 16/17. 실패 개수만 복사하지 않고 전체 ID 집합을 명시한다. 기존 class/slot/element preset 검증 유지.
5. Titan lift: JumpAbilities.airborne은 !isNoGravity 필수. 이 테스트에만 false 적용하고, 기존 noGravity 상태에서는 거절·속도불변을 먼저 검사한다. JumpAbilities.momentum은 getKnownMovement를 읽으므로 fake player에 .05 상승 관측을 주고 strafe .10 impulse 결과 .15를 엄격 확인한다. 낙하 즉시 반전은 catapult 계약이며 strafe 계약이 아니다(JumpPhysics.liftStart). 유한수명/flags/인벤토리 유지, landing budget 관측과 재시전은 실제 별도틱(T20 ground, T22 jump).
6. Warlock grenade: GrenadeThrow.RELEASE_TICKS=6, DURATION_TICKS=20. 승인 직후 prop+pending/flight0, T5 flight/field0, T7 실제 flight+field합1 검증. pending 재입력은 AbilityService의 cooldown보다 앞선 BUSY 분기. T25 실제 impact/LOS/피해 및 T150 종료 검증 유지.
7. Warlock lifecycle: 두 실제 grenade를 위로 조준하여 release 후 T7의 owner별 flight2/1 확인, 그 뒤 cleanup/other-owner/ordinary-flight 격리 검사. 이후 epoch 검증은 같은 상대 간격으로 T8/10/12/14/16에 사전 등록. 카운트 완화 없음.
8. 추가 두 클래스의 기존 nested callback 등록 지점도 부모를 sequence로 옮겨 fastutil callback-map 순회 중 구조변경을 피했다. 엔진 수정 없음.

## H20 — 지금 반환하는 정확한 근거, 미해결 3건

`h20-source-evidence.json`에 입력 파일 경로·SHA256·재계산 값을 저장했다. 이것은 정적 FK 비교이며 native 통과 증거가 아니다.

- W197/W199의 Arc attack/deploy clip JSON은 동일하다. 현재 설치 W255_r2 모델의 25ms 회전 샘플과 W199를 비교한 최대 차이는 attack 1.99e-13°, deploy 2.42e-13°다. **현재 원본과 다른 stale clip이라는 근거 없음.**
- 공격 .05→.10초 staff world +Y 회전: H26 82.398149666°, W197/W199/설치본 13.655651051°. 기존 H26 고정 구간 >60° 기대는 현행 source-retarget 계약에 맞지 않는다. native 실패값 15.99949를 새 expected로 쓰지 않았다. 새 native source-motion oracle은 basis/보간 경로 확인 후 정해야 한다.
- staff support: W199/설치본 attack의 25ms FK 키에서 local(0,6,0) support 오차 최대 1.08264e-8 blocks. native 로그는 .0500878 blocks. W197 문서도 support constraint를 유지한다. 따라서 .025를 늘리거나 검사를 없애는 수정은 부적절하다. 중간 보간/손 좌표 변환/첫 전환의 어느 경로가 어긋나는지는 아직 확정하지 않았다. **제품/native 변환 결함 가능성 보고**이며 제품 수정 없음.
- deploy endpoint: H20은 clock.destiny$advanceServerTick만 같은 실제 tick0에서 반복한다. PlayerAnimations.tick:363–399는 server.getTickCount 기반 run.durationTicks 경과 후 stopAnimation·ready loop 복귀를 수행한다. 현재 fixture는 이 lifecycle을 실행하지 않는다. source endpoint는 ready 정렬 계약을 유지하므로 .001 허용치를 늘릴 근거가 없다. 실제 서버틱 기반 검증으로 옮겨 확인할 필요가 있다.
- 원본 계약: docs/qa/2026-10-27/w197/hunter.md (source 80A8A922/80A8A937, .50/.35초 retiming 및 .10 contact, DE9D6BEA hand 기반 staff orientation, support/neutral endpoint). 전체 H20 소스는 변경하지 않았다.

## 검증

Java tree-sitter 파싱, 기존 public GameTest method 목록 보존, 두 delta의 git apply --check --whitespace=error, 여섯 snapshot 파일 main baseline 일치 확인. 중앙 build/runtime은 지시대로 실행하지 않았다. no commit/reset/stash/push.
