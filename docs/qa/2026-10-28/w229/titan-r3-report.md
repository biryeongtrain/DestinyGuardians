# Titan W229 R3 — frozen / ready

Delta: `/private/tmp/destiny-w229/titan-r3-owned-delta.tar.gz` (GameTest1파일만). main/shared/product files는 수정하지 않았다. master의 최종 방벽 canonical/scale 수정은 archive에 포함되지 않는다. 이전 R2 delta를 다시 덮어쓰지 말고 R3만 통합한다.

- Aggregate SHA-256: `0e49305d64171132f4320ad9bf202ca5e54cc0df479a7eb1d6649872c09f1190`
- Archive SHA-256: `92302ff99f035e29ab265783392369f6cba15b6a8a1ec58c726a7409ebd87201`
- Manifest: `/private/tmp/destiny-w229/titan-r3-delta.json`
- Baseline: `/private/tmp/destiny-w229/titan-r3-baseline.json` (현재 integrated R2 main3파일). frozen 시 reviewed3파일 main drift=0.

## root cause

중앙 R2 XML은20/23pass, Titan은9/10pass이며 `allThreeRoaming...`가testTick38에서 실패했다. 읽은 증거: main `docs/qa/2026-10-28/w229/server-w229-r2-report.xml` 및 `.log`. R2에는 camera rotation timeout 로그가 없다.

fixture `floor.snbt`의 크기는16×8×12다. MC26.3 GameTestInfo는 구조 배치 후 TestInstanceBlockEntity.encaseStructure를 호출한다. processStructureBoundary는 skyAccess가false면 천장을 포함하고 encase callback은 BARRIER 블록으로 채운다. 이 경로의 javap 근거는 `/private/tmp/destiny-w229/titan-r3-ceiling-evidence.txt`에 기록했다.

R2 control은 일반 Void grenade를 pitch=-90으로 발사하고 super29틱 windup이 끝날 때까지 flight로 남는다고 가정했다. 실제 grenade 초기Y속도1.2/틱, gravity.04/drag.99는 낮은 fixture 천장에 먼저 충돌한다. 따라서 일반 flight는 정상적으로 field로 전환되어 tick38에 두 flight가 있을 수 없다. 소유 context를 바꿔서 취소되거나 flight상한 때문에 super가 거절된 근거는 없다: loadout은 시작 전에만1회 변경, Context 동일 identity, 최대8 대비 시작1flight, super 준비29틱/입력30틱/release37틱으로 순서는 맞는다. 로그에는 개별 flight position/count가 없어 실제 충돌tick을 실측했다고 주장하지 않는다.

## 작은 수정

해당 행동 GameTest만 `skyAccess=true`로 지정해 의도한 상향 비행 control에 천장을 두지 않는다. 벽/실제 충돌 코드/수명/발사속도/피해는 변경하지 않는다. tick38에2개 공존, session종료 후1개 ordinary 보존, Context cleanup 후0개, natural expiry의 super-only cancel 기대를 그대로 유지한다. 준비 완료30틱에도 ordinary flight1개+grenade fields0+실제 active session을 추가 확인하고 실패에game/server/test 시계와flight/field/session 상태를 기록한다. 자연 만료 직전 상향 flight도 같은 open-sky fixture에서 검사한다. 숫자만 검증하는 테스트 추가 없음.

## 검증 / 미검증

변경된 GameTest1소스만 Java25 javac exit0 (read-only integrated main/gametest cached classes 및 MC/Fabric dependency). `/private/tmp/destiny-w229/titan-r3-check/result.txt`. 별도 broad build/test 없음. 중앙 Gradle/실제 GameTest rerun/native는 master 대기이며 통과를 주장하지 않는다. TitanSuper/TitanAbilities product 수정 없음. archive1파일 범위와 content hash 검증.

## 변경파일 baseline → R3

- `src/gametest/java/kim/biryeong/destiny/test/TitanW229GameTests.java`
  - baseline main: `103fce3732a597902351ea95a1d6d85fc9fd162d2eeb396962df3986f03488c4`
  - R3: `27abcbe4687458f0f8bf414ac47375ea98509d62f49607dc06968b04f2b7f3d9`

검토만 한 TitanAbilities baseline: `08648db947fd9d329c2af5d4fff45fe7bc3568b24be56cc48c799cc4d2ed73d9`
검토만 한 TitanSuper baseline: `239e7d800e4ca4400e1e161e7e2305b895bdc4f0a3f16de0af27caaec2864636`
보존한 main TitanClassAbility 해시: `b3d292a10da25adfb0ada26f16c60471def36a5cc7812d172469daaebb0aae95`
