# W229 Warlock R3 — bounded fixture correction

**frozen / 통합 가능 / 변경1개: WarlockW229GameTests.java.** 제품 Java/JSON/shared/main 변경 없음. GameTest 수10개 유지. 중앙 실행/Gradle/native/CU 없음.

- delta: `/private/tmp/destiny-w229/warlock-r3-delta.json`
- snapshot: `/private/tmp/destiny-w229/warlock-r3-delta/files/`
- patch: `/private/tmp/destiny-w229/warlock-r3.patch`
- baseline: R2 통합 main19개 해시가 worker와 일치한 상태에서 시작. `warlock-r3-baseline.json`, `warlock-r3-main-baseline.sha256` 및 delta.baseline_main_files에 전체 보존. 생성 직전 main19/19 기준 일치.
- main HEAD `f5e304c02f44de0c7c7e88e4a63658708484eb10`
- baseline test SHA256 `54b31772f9b5138e115238fa6304614b94e4b234d9447eb213570e283487e7c1`
- R3 test SHA256 `479e9f46e1d033a3f8170823b8dcc28ea96ab8be0d0c49c233a4574fcda411ea`
- changed manifest SHA256 `0d4c02cdb3c213fade5a5afce0ed873965f5680d8cf3ddc7d3deb13a1fb11da1`

## R2 실패 geometry 분석

근거: main `docs/qa/2026-10-28/w229/server-w229-r2-report.xml` 및 `server-w229-r2.log` 읽기 전용. 중앙20/23pass, Warlock8/10pass(2fail). Nova post-cast field/LOS/expiry/subclass 정리 기존 테스트도 통과했다.

### Grenade

실제 FieldSnapshot 원점 `(9381312.899999976,8.305607156821385,-5075450.5)`. 벽 collider X `[9381315,9381316]`, Y `[7,11]`. blocked 중심 `(9381316,7.975000023841858,-5075450.5)`. 원점→몸 중심 선은 벽보다 낮거나 위로 빠지지 않고 X벽을 통과하므로 BLOCK이어야 한다. 원점은 벽에서2.10block 앞이며 crossing origin 증거가 없다.

Husk feet X=9381316은 벽 먼 면 경계와 같다. 폭0.6의 bbox minX≈9381315.7으로 벽에0.3block 겹친다. R2 visible HP94는6피해이고 FieldSnapshot 총 actualDamage6/pulses2/lastTargets1과 일치한다. blocked HP97의3피해는 이 field 집계에 없다. 벽 몸체 overlap이 확정 fixture 결함이며25tick에3HP 손실은 vanilla in-wall1HP 주기와 일치한다. damage source 로그가 없으므로 질식 원인 자체를 실행 trace로 확정했다고 주장하지 않는다.

R3 front5.5→5.75, blocked8→8.5. 벽 X7..8은 유지. blocked bbox min8.2로0.2block clearance. front를0.25 옮겨 실제 field origin도 약X5.15로 옮기므로 blocked가 radius3.5 안에 남는다(독립 비행 근사거리3.36593). 실행 테스트는 근사값 대신 실제 FieldSnapshot.origin→blocked center 거리<radius, front MISS/blocked BLOCK, body noCollision을 assert한다. field 피해는 visible<100/blocked==100 그대로다.

### Daybreak

R2 caster eye `(9381402.5,8.620000004768372,-5075450.5)`, look `(0.9951187372207642,-0.09868500381708145,~0)`. 중력0/drag.99는 직선 방향을 보존한다. 벽 X `[9381408,9381409]` 진입점 Y≈8.07458, incoming face offset-.06을 포함한 원점 X≈9381407.94. 이는 native impact snapshot이 아니라 발사 ray/제품 offset으로 계산한 접촉점이다. blocked centerX9381409까지 ray는 벽을 가로지른다. front의12HP 손실은 sword damage12와 같지만 blocked6HP는 동일 sword 피해량이 아니며60tick의 in-wall1HP 주기와 일치한다.

blocked feetX9381409는 벽 먼 면 경계. bbox min9381408.7로0.3block 겹친다. R3 blocked9→9.5로 바꿔 bbox min9.2의0.2block clearance를 확보한다. 새 independent wall-hit ray의 near-side 원점(relative `[7.94,2.1132143,6.5]`)에서 blocked 몸 중심까지 약1.56611 <radius2.5. front도 반경 안이다. 제품 impactPoint를 호출하지 않고 native collider ray의 face/location에서 near-side contact를 산출하여 양 대상 반경 포함과 front MISS/blocked BLOCK을 assert한다. 원래 emitted==1/front<100/blocked==100 기대를 유지한다. 실패 메시지에 near-side contact/ray/distance와 bodyClear를 추가했다.

## 검증과 잔여

JavacTask.parse1개 통과(타입 해석/bytecode 생성 아님), whitespace/newline, test10개 유지 확인. noCollision 전제 및 실제 필드 원점 LOS 추가로 fixture/피해를 구분한다. 다른 damage 경로를 무력화하거나 expected damage를 낮추지 않았다. 테스트 좌표 수정의 실제 수락 및 제품 no-wall-damage 최종 결론은 master 중앙 R3 재실행 대기다. native는 master 소유이며 아직 실행하지 않았다.
