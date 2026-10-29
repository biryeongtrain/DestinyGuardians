# W258 run2 ADS 후속 패치

기존 소유 20개 중 실패한 5파일의 patch는 현재 승인된 scheduling/movement followup 및 Bowfix를 기준으로 한다. W113은 `/private/tmp/destiny-w258/ads-extra/manifest.json`의 별도 seed SHA256을 기준으로 `extra-w113/followup.patch`에 분리했다. 두 manifest에 파일별 이전/수정 SHA256 및 patch SHA256이 있다.

## 5개 실패의 원인과 유지한 계약

1. **W44 실제 ADS 피해량**: embedded player fixture는 grounded 상태를 설정하지 않았다. slot `WeaponAccuracy.airborne`와 `ShotDispersion.coneDegrees`에서 완전 ADS도 AE 공중 항을 제거하지 않는다. grounded 상태와 실제 cone=0을 발사 전에 검증한다. 또한 slot `WeaponRuntime` 873/1050행은 hitscan에서 `.03f` margin을 사용하는데 기존 기대 거리는 uninflated 발 위치였다. 독립적인 inflated AABB 하단 교차점으로 body-hit 거리와 HP를 계산한다. authored range scalar가 start/end만 변화시키는지, hip보다 큰 실제 ADS 피해인지, 탄약 1발만 지불하는지 검증하며 기존 HP 오차 `.002`를 유지한다. 실패 메시지에 expected/actual/distance/contact/direction을 추가했다.
2. **W70 nock 0.051 vs 0.05**: `WeaponReloadPresentation.update`는 저장된 float1이 60구간 샘플과 같으면 새 binding에 `.001` cache offset을 붙인다. 이 fixture는 bow float2 padding으로 float1=0을 저장하므로 그 사전조건을 먼저 검증한다. 발사 후 실제 nock acquisition에서 정확히 `.001`, 이후 매 샘플에서 `floor(progress*60)/60 + .001`, 종료 후 -1을 검증한다. 실제 결과에서 offset을 역산하거나 허용 오차를 넓히지 않았다.
3. **W75 sneaking-speed dirty**: 테스트가 첫 관측에서 lazy AttributeInstance를 만들면 그 조회 자체가 sync dirty를 만든다. setup 때 sneak 인스턴스와 modifiers/base/value를 먼저 확보하고 초기 dirty를 비운다. 이후 모든 ADS tick에서 sneak dirty 없음, modifier/base/value 불변을 계속 검증한다. speed dirty/정지 샘플 객체 재사용/즉시 release 검증은 유지했다.
4. **W85 paid-shot 전제**: helper에 남은 `isShiftKeyDown` 두 곳을 실제 `requested`, `aimInput`, progress=1 검증으로 바꿨다. 실제 지불, reserve 보존, 20틱 No Distractions 획득/재시작/해제 경계는 변경하지 않았다.
5. **W92 funded Izanagi wire**: W162의 `WeaponIzanagiPresentation.scopedIdle` 및 CombatItem 우선순위에 따라 charged IDLE+scope는 W45 scope 경로를 사용한다. stale W91 3D ADS 기대 대신 실제 scope intent/정확한 ADS 소유자/scopedIdle 및 `destiny:weapon_scope_w45/izanagis_burden`을 검증한다. 61틱 unscoped funded-idle W91 대조군, charge2/탄약/float6 보존, float3와 incremental/full native packet 및 원본 canonical/round-trip 검증을 유지했다.

## 추가 W113 두 실패

기존 exact pair 경로/Handling phase/deadline/소유권 getter 검증은 그대로다. outgoing swap 경로와 복원/foreign-copy fallback에만 이미 통합된 `WeaponGripGameTests.projected`를 사용해 authored W201 손 모델 투영을 반영했다. 원본 불변·탄약 비용·양쪽 carrier 검증은 그대로 유지했다.

## 검증 및 경계

- 기존 139개 + W113 2개 GameTest 이름/개수 유지; 삭제/disabled/manual 전환 없음.
- 정적 Java syntax 21/21 통과. 소유 파일 직접 중첩 scheduler 호출 0개 유지.
- 두 patch 모두 보존 integrated-before 대상 `git apply --check` 통과. 실제 apply 실행 없음.
- 나머지 기존 소유 15파일은 승인된 결과 SHA256과 동일하다.
- main 접근/수정, 제품 수정, 공통 TestPlayers 수정, build/QA/game runtime 실행 없음. 로그와 slot 파일만 확인했다.
- 중앙 compile/native reporter 재실행 결과는 아직 없으며 통과를 주장하지 않는다.
