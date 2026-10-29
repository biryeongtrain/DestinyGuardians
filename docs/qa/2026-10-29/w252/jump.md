# W252-jump — 슬롯1 반환

2026-10-29. 작업본: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1`.
`/private/tmp/destiny-w252/manifest.json`의 W252-jump 소유 7개 파일만 편집했다.
refresh 보고서와 master ready 후 편집했다. main·SSD 원본·공유 registry/InputRouter/UI/AbilityService는 편집하지 않았다.
commit/stash/reset/clean/push, Gradle, Minecraft, Vision, CU는 실행하지 않았다.

## 통합 API와 이전 ID

- `JumpAbilities.register()`가 11개 옵션을 모두 등록한다. 기존 Hunter 2개, Titan 1개, Warlock 1개 등록을 제거한 뒤 호출한다. 중복 호출 자체에는 guard가 있다.
- `JumpAbilities.tick(MinecraftServer)`, `.cleanup(ServerPlayer)`, `.clearAll()`을 master 공통 수명주기에 연결한다.
- 기존 `HunterJump(Identifier,String,int,double)`와 `extraJumps()`, `TitanJump()` 및 `WarlockJump(Identifier)`를 유지했다.
- 기존 `TitanJump.tick(server)`와 `WarlockJump.tick()`는 같은 엔진에 위임한다. 플레이어별 `Budget.observe(serverTick,...)`와 `propel(serverTick)` 양쪽 guard로 기존 classAbilities/common hook의 호출 순서와 관계없이 한 틱에 한 번만 갱신한다. 초기 활성화도 그 틱의 추진을 이미 사용한 것으로 기록한다.
- `TitanJump.active/cleanup/clearAll`, `WarlockJump.active/cleanup`의 기존 시그니처를 유지했다. 별도 옛 ACTIVE/Lease/Context로 점프를 이중 소유하지 않는다.

| 직업 | 표시 이름 | ID (`destiny:` 접두사 생략) | 제한 |
| --- | --- | --- | --- |
| Hunter | 높은 점프 | `hunter/double_jump` | 공중 1회 |
| Hunter | 제어 점프 | `hunter/strafe_jump` | 공중 1회 |
| Hunter | 삼중 점프 | `hunter/triple_jump` | 공중 2회 |
| Hunter | 점멸 | `hunter/blink` | ARC만 |
| Titan | 높은 리프트 | `titan/high_lift` | 유한 연료 |
| Titan | 제어 리프트 | `titan/jump` | 기존 기본 ID |
| Titan | 도약 리프트 | `titan/catapult_lift` | 유한 연료 |
| Warlock | 제어 활공 | `warlock/strafe_glide` | 유한 시간·횟수 |
| Warlock | 폭발 활공 | `warlock/burst_glide` | 유한 시간·횟수 |
| Warlock | 균형 활공 | `warlock/jump` | 기존 기본 ID |
| Warlock | 점멸 | `warlock/blink` | VOID만 |

점멸의 Element를 각각 ARC/VOID로 등록하여 기존 CharacterLoadouts 선택 규칙을 사용하며, 활성화 시에도 현재 super에서 판정한 subclass를 확인한다.

## 물리와 자원

순수 계산/예산은 `JumpPhysics`, Minecraft 연결과 플레이어별 상태는 `JumpAbilities`가 소유한다. GuardianRuntime 새 필드는 없다. 기존 `airJumpsUsed`는 호환 표시용으로 갱신하지만 예산 판정은 별도 map이 담당한다.

보통 Hunter 점프/Lift/Glide와 직업 교체는 한 공중 기간의 정규화 에너지 1을 공유한다. 높은/제어 Hunter 점프는 1, 삼중 점프는 .5를 사용한다. 추진/활공은 매 적용마다 `1 / 활성화 시 확정한 duration_ticks`를 사용한다. 옵션 교체로 기간을 늘려도 사용한 에너지 비율은 유지된다. 취소·중단 기간에는 연료가 재생되지 않는다. 추진/활공의 시작·재개는 공중 합계 최대 3회이며, 시작 틱도 사용 시간에 포함한다. 특히 도약 리프트·폭발 활공의 초기 임펄스를 무제한 토글할 수 없다.

점멸은 이 공중 에너지·추진 시작 횟수와 독립된 2충전/44틱 타이머를 사용한다. 마지막 성공 사용에서 44틱이 지나면 지상/공중 모두 2충전을 회복한다. 일반 점프 연료를 소진해도 점멸은 가능하고, 점멸은 일반 점프 연료를 소모하거나 충전하지 않는다. Hunter/Warlock 점멸은 같은 플레이어 타이머를 공유하며 옵션·직업 교체나 착지가 이 타이머를 초기화하지 않는다. 거절된 입력은 마지막 성공 사용 시각을 연장하지 않는다.

일반 `cleanup()`은 활성 이동만 취소하고 연료·횟수·점멸 재충전 시각을 보존한다. 캐릭터 메뉴가 cleanup을 호출하기 때문이다. 착지에서 연료·횟수를 초기화하고, 사망·접속 종료·player 객체 교체·차원 변경에는 epoch를 제거한다. 서버 종료의 `clearAll()`은 이동 표본까지 제거한다. 기존 Titan/Warlock cleanup도 동일 경로를 사용한다.

`flying`·`noGravity`·이동 속성은 읽기만 한다. 물/용암/탑승/사다리/겉날개/기존 비행·무중력/궁극기 이동 제한에서는 활성 이동을 중단한다. 취소 시 새 속도·중력 변경을 쓰지 않는다. 실제 이동 적용에는 기존 Motion의 클라이언트 속도 패킷을 사용한다.

### 바닐라 상승 관성

서버 `getDeltaMovement()`를 실제 바닐라 관성의 대체값으로 사용하지 않는다. 공통 tick은 점프 상태가 없는 접속 플레이어도 위치를 추적한다. 순수 `MotionTracker`는 **마지막 위치 변경 이후 시간**으로 누적 변위를 나누며, 같은 서버 틱의 반복 호출은 같은 anchor를 유지한다. 이동 패킷이 없어 위치가 같은 틱은 유효한 정지 표본으로 만들지 않는다. `getKnownMovement()`의 마지막 패킷 변위와 실제 위치 변화를 대조하고, 패킷 변위 Y=0만으로 이미 관측한 상승을 지우지 않는다.

최종 읽기 검토에서 수평 위치 변경만 있어도 공통 관측 시각이 갱신되어 `freshVertical=true`가 되는 추가 경로를 확인했다. **수직 관측 시각과 마지막 Y 변경 시각을 수평 관측과 분리**했다. 수평-only 표본은 Y=0을 하강·정지 증거로 만들지 않고, 수직 표본 유효기간도 갱신하지 않는다. known 벡터의 X/Z만 바뀌어도 같은 양의 Y가 새 수직 관측으로 재분류되지 않는다. Y 누적 변위는 수평 패킷 간격이 아닌 마지막 Y 변경 이후 시간으로 나눈다. 명시적인 지상 판정은 실제 정지/다음 점프의 기준점이며, 천장 충돌은 기존 `ceilingBlocked` 경로를 사용한다.

26.3 로컬 Minecraft JAR을 `javap -c -p`로 확인했다. `ServerPlayer.getKnownMovement()`는 비탑승 시 `lastKnownClientMovement`를 반환한다. 추가 확인한 `ServerGamePacketListenerImpl`에서는 패킷의 실제 변위를 `handlePlayerKnownMovement`로 전달하고, 이동 패킷이 없는 client-tick 종료에는 ZERO를 대입한다. 따라서 이것도 항상 최신 클라이언트 물리 속도인 것은 아니다. 위치 변경 간격 1~4틱, 정규화한 수직 <=1.5 block/tick·수평 <=3 block/tick을 채택한다. 패킷 공백은 최대 2서버틱까지만 마지막 관측 관성을 보존하고, 더 긴 무응답은 바닐라 중력·감쇠로 예측하여 새 상승 근거로 쓰지 않는다. 실제 하강은 과거 상승 명령보다 우선한다. 점멸 직후 위치 anchor를 다시 잡고 차원/플레이어 객체가 바뀌면 표본을 교체한다.

워록은 `GlideCarry`에 관측한 양의 수직 운동을 저장하고 다음 vanilla gravity/drag를 보상하며 유한하게 소진한다. 패킷 공백·지연된 양의 표본이 이 관성을 매번 재충전하지 않는다. 실제 하강 표본이나 머리 위 충돌이 관측되면 상승을 끝내며, 같은 활공 중 늦게 도착한 양의 표본이 새 상승을 만들지 않는다. 낙하 중 활성화/재개는 낙하 속도만 제한한다. 추진/활공의 수평 속도 상한은 활성화 때 확정해, 이후의 coalesced 표본이 상한 자체를 1.33 등으로 올리지 못한다. 활성화 때 이미 있던 외부 수평 속도는 보존한다. 바닐라 클라이언트 실제 움직임/패킷 간격에 대한 최종 수용은 master Vision이 필요하다.

### 1차 Vision 결함과 2차 수정

master 제공 원본 `/private/tmp/destiny-w252/qa/native/warlock-jump-r1.json`의 stdout JSON 내 observations/captures를 읽었다. client tick 3381은 y=100.42/vy=.3332, 3383은 y=101.001335979/vy=.164773282였으나 활공 입력 직후 3384에서 y=101.166109261/vy=0, 3385에서 vy=-.0784, 3388에서 y=101.009335335/vy=-.078373924였다. 3395에는 수평 vz=1.336995666도 기록됐다. 원본 trajectory는 수정하지 않았다. Hunter high maxY=103.28 정상, Titan 토글/재개 정상은 master 피드백이며 여기서 새로 실행한 Vision 결과가 아니다.

첫 구현의 `sampleValid=true`인 0변위 우선 선택과, 서버 틱마다 위치 anchor 시각을 갱신한 계산이 패킷 공백·몰림에 취약했다. 새 순수 테스트는 이 관측 상승값·수평 속도를 사용해 패킷 공백/누적 변위/하강 전환을 모형화한다. client tick과 server tick이 일치한다고 가정한 실제 재생 증거는 아니다. 기존 `GlideCarry` 없는 22-test 동결판의 1차 Vision은 **워록 실패**로 기록하며, R2 native 후속 결과와 R3 대기 상태는 다음 절에 기록한다.

### R2 native 진단과 R3 상승 carry 보정 (2026-10-30)

master는 R2 중앙 42 PASS / 7 GameTest PASS를 보고했다. worker가 중앙 검사를 재실행한 결과는 아니다. 읽기 검토한 원본은 `/private/tmp/destiny-w252/qa-r2/native/warlock-rise-r2.json`, `warlock-rise-r2-server.json`, `warlock-rise-r2-trajectory.json`이다. sparse trajectory의 최고 표본 Y101.50374와 달리 원본 capture의 client tick521 및 서버 tick244217에는 **Y101.6573501814**가 있다. 관측 최고점은 최소 이 값이며 모든 클라이언트 틱의 절대 최고점을 증명하지는 않는다. 서버 tick244213의 vy=.10606800136에서 244217의 .03406799996으로 정확히 .018/tick 감소했고, 244220에는 glide=true인 채 vy=-.196이었다. 기존 감쇠가 약 6틱 뒤 carry를 소진하는 추세와 일치하므로 R2 native 상승 지속은 수용하지 않았다. 수평 cap .63 정상은 master 피드백이다. 패킷 순서가 추가 손실을 만드는지는 이 기록만으로 확정하지 않았다.

사용자 승인 R3는 **`GLIDE_ASCENT_DECAY = .006` block/tick의 틱당 감소량**을 사용한다. 기존 .018보다 완만한 **MC 튜닝**이며 원작 확정 수치가 아니다. 매 적용과 skipped server tick 모두 같은 선언 상수를 사용한다. 최초 관측 양수로 채운 `GlideCarry`가 이후 유한 상승을 주도하며, 활성화 뒤 작은/큰 양수 표본은 내부 carry를 삭감하거나 재충전하지 않는다. fresh 비양수 관측과 천장 충돌은 계속 상승을 중단하고, 한번 낙하 상태가 되면 늦은 양수 패킷으로 재상승하지 않는다. .164773282로 시작하는 순수 1중력-step 모형은 양의 유효 속도를 약 27회 적용까지 유지한 뒤 소진한다. 이는 native 재생 결과가 아니다. 기존 활성 60틱/공중 시작 3회/공유 연료 제한과 Blink 독립 2충전/44틱은 유지한다. 낙하 raw command -.12 및 바닐라 적용 후 -.196의 차이는 이번 승인 범위에서 변경하지 않았다.

R3 standalone **37/37 PASS**, 0 failed/skipped. 기존 상승 테스트를 새 감쇠에 맞게 갱신하고, 양수 표본이 작거나 커도 carry를 삭감/재충전하지 않는 검사와 skipped/regular tick의 감쇠·중복 호출·소진 경계 일관성 검사를 추가했다. 실제 하강·천장·낙하 시작·늦은 양수 재상승 금지 검사도 통과했다. 첫 실행은 신규 테스트의 raw command 음수 전환 예상이 1틱 빨라 36 PASS/1 FAIL이었으며, 유효 상승 소진(27)과 raw 음수 전환(29)을 구분하도록 assertion을 수정했다. 첫 로그는 `result-glide-r3-first-run.txt`, 최종 로그는 `/private/tmp/destiny-w252/jump-puretest/result-glide-r3.txt`에 보존한다. R3 중앙 컴파일/GameTest/native 상승·하강·천장·수평 cap은 아직 미검증이며 master가 통합 후 확인한다.

### 점멸 충돌

최대 .125 block 간격으로 이전/다음 **플레이어 전체 AABB를 연결한 swept box**를 검사한다. 끝점만 비어 있어도 중간의 얇은 벽/천장을 통과하지 않는다. 매 구간에서 월드 경계 전체 상자, build/world bounds, 적재된 청크와 `noCollision`을 확인한다. 최소 .25 block 이동도 불가능하면 실패하며 연료·충전을 사용하지 않는다. 청크를 강제로 적재하지 않는다. 순간이동은 기존 속도를 보존하고 추가 상승 임펄스를 주지 않는다.

## 원작 근거와 MC 튜닝 구분

- [사용자 지정 Destiny Data Compendium](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit): 2026-10-29 웹으로 열었다. 읽힌 개요 A1:X40 화면에는 이동 수치가 없었다. 해당 이동 탭/행과 Hunter/Lift/Glide 정확한 절대 속도·지속·활성 횟수는 확인하지 못했다. 아래 값을 DDC 확정값이라고 주장하지 않는다.
- [Bungie Update 1.1.4, 2018-03-27](https://www.bungie.net/7/en/News/article/46708): Strafe Lift 속도, Catapult 초기 수평 가속, Glide 상승 연장, Strafe 기동성·Burst 최고 속도·Balanced의 중간 성격을 설명한다. 설계 방향 근거이며 현재 절대 수치 근거는 아니다.
- [Bungie Update 6.2.0, 2022-08-23](https://www.bungie.net/7/en/News/article/51707): ARC Hunter Blink 추가, 점멸 최대 변위 5.25m/수직 오프셋 2.5m, 2충전과 마지막 사용 2.2초 후 동시 재충전을 명시한다. **당시 공식 수치**로 확인했으며 2026 최신값 전수 확인은 아니다.

MC에서 1m를 1 block으로 대응해 점멸 범위 상한 5.25, 수직 상한 2.5, 재충전 44틱을 사용했다. 2충전은 공중에서도 마지막 사용 44틱 뒤 함께 회복된다. 방향은 시선이고 입력 cadence 6틱은 별도 **MC 튜닝**이다. 일반 점프 연료와 무관하게 재충전된 점멸을 사용할 수 있고, 순간이동 후 기존 관성과 바닐라 중력은 계속 적용된다. 비행·무중력 플래그를 추가하지 않는다.

나머지는 모두 MC 초기 튜닝이다. 속도는 block/tick, 가속은 틱당 속도 변화량이다. PvE/PvP·이동 스탯별 원작 수치로 확정하지 않았다.

| 모드 | 초기 Y/낙하 회복 | 수평 steering / cap | 지속 가속 / Y 상한 | 총 활성 틱 |
| --- | --- | --- | --- | --- |
| Hunter high | 최소 .62 | .10 / .38 | 해당 없음 | 임펄스 |
| Hunter strafe | 최소 .46 | .34 / .64 | 해당 없음 | 임펄스 |
| Hunter triple | 최소 .45, 2회 | .17 / .46 | 해당 없음 | 임펄스 |
| Titan high | 현재 Y + .16 | .035 / .40 | .125 / .64 | 24 |
| Titan strafe | 현재 Y + .10 | .095 / .58 | .095 / .50 | 16 |
| Titan catapult | 최소 .50 | 시작 .18, 이후 .065 / .48 | .105 / .56 | 18 |
| Warlock strafe | 기존 상승 연장/낙하 제한 | .13 / .52 | 낙하 raw Y >= -.12 | 60 |
| Warlock burst | 동일, 시작 수평 .32 가속 | 이후 .035 / .78 | 동일 | 60 |
| Warlock balanced | 동일 | .075 / .63 | 동일 | 60 |

기존 JSON `duration_ticks/max_up_speed/acceleration/descent_speed/strength/horizontal_carry`를 유한 범위로 읽는다. 새 JSON은 추가하지 않았다. 활성화 당시 외부 임펄스가 cap보다 빠르면 그 속도를 허용 상한으로 보존하지만, 이후 추진/활공의 위치 표본이 그 상한을 더 올리지는 못한다. 입력이 없으면 카메라 방향으로 강제 이동하지 않는다. WASD와 시선을 구분한다.

## 수행 검사와 남은 검사

- 1차 반환: Java 25 javac + 캐시된 JUnit Jupiter 5.11.4/Platform 1.11.4로 **standalone pure test 19/19 PASS**, 0 skipped/failed. 최초 공중 재충전 제한이 남아 있던 버전의 결과이며 최종판 결과와 구분한다. Minecraft/Gradle 미실행.
- Blink 동결판(1차 Vision 이전): 독립 충전/공중 재충전 반영 후 같은 standalone 환경에서 **22/22 PASS**, 0 skipped/failed. 추가 3개 검사는 착지 없이 반복 재충전·마지막 성공 사용 기준 경계, 양방향 일반 연료 독립성, 일반 추진/직업 교체 중 점멸 타이머 유지다. 로그는 `/private/tmp/destiny-w252/jump-puretest/result-blink.txt`다. 이 결과만으로 위 native 워록 결함을 검출하지 못했다.
- 워록 2차 수정 동결판: 같은 standalone Java/JUnit 환경에서 **30/30 PASS**, 0 skipped/failed. 추가 8개는 패킷 공백·수평-only known Y=0·누적 변위 정규화·마지막 패킷 반영·측정 상승의 지속/소진·실제 하강 후 늦은 양의 표본·긴 무응답·천장/중복 틱·수평 상한을 검사한다. 로그는 `/private/tmp/destiny-w252/jump-puretest/result-glide-r2.txt`다. 기존 19/22 결과와 로그도 보존했다.
- 2차 읽기 검토 보정 동결판: **35/35 PASS**, 0 skipped/failed. 수평 **실제 위치** 변경 + 양의 known Y 유지, 수평 실제 위치 변경 + known Y=0의 활성화 순간, 수평 갱신으로 수직 정보 유효기간이 연장되지 않음, 수평 패킷 도중 Y 누적 변위 정규화/실제 하강, 긴 지상 대기 후 첫 점프를 추가했다. 이전 30개는 known 벡터만 수평으로 바뀌는 사례를 다뤘고 실제 수평 위치 변경 경로를 놓쳤다. 로그: `/private/tmp/destiny-w252/jump-puretest/result-glide-r2-axis.txt`. 19/22/30 결과도 보존했다.
- 소유 파일 대상 `rtk git diff --check` PASS. untracked 신규 파일까지 포함한 7개 파일의 trailing whitespace·manifest 경로·flight/gravity setter 비사용 검사 PASS.
- 1차 로그: `/private/tmp/destiny-w252/jump-puretest/result.txt`. 임시 JUnit Launcher 출력이며 제품 파일에 runner를 추가하지 않았다.
- 검사 내용: 서버 delta=0의 실제 상승 표본, stale 상승을 덮는 실제 하강, 수평-only Y=0과 실제 지상/천장 정지의 구분, Hunter 방향 제어 차이, 외부 임펄스 보존, Titan 높이/낙하 회복 차이, Warlock 상승 소진/낙하 재상승 금지, 중복 틱·입력 방지, 취소/재개·옵션/직업 교체 예산 보존, 횟수/총시간 제한, 착지 리셋, 점멸 cadence·충전 타이머, 범위·얇은 벽·천장·경계 sweep, 잘못된 tuning clamp.
- 미검증: master 중앙 컴파일/기존 회귀, native 스페이스 상승-취소-재개 타이밍, 실제 메뉴 교체, 사망/로그아웃/차원 이동 이벤트, 실제 블록·엔티티 충돌, 소리·시각·패킷 감각. pure sweep 검사는 충돌 predicate 수학을 검사하며 Minecraft 충돌 엔진 실행 증거가 아니다.

최종 반환은 manifest 소유 7파일 전체다. Blink 동결판 대비 이번 수정은 `JumpAbilities.java`, `JumpPhysics.java`, `JumpPhysicsTest.java`, 이 문서 4개다. 30-test 보정판 대비 최종 읽기 검토 후에는 Physics/Test/문서 3개만 추가 수정했다. 기존 3직업 facade와 공통 통합 API, Blink 독립 2충전/44틱 정책은 유지했다. R2 35-test 동결 SHA-256은 `/private/tmp/destiny-w252/jump-puretest/frozen-glide-r2-axis.json`에 보존한다. 최신 R3 37-test 동결 SHA-256은 `/private/tmp/destiny-w252/jump-puretest/frozen.json` 및 `frozen-glide-r3.json`이다. R2 대비 R3 변경은 Physics/Test/문서 3개이며 나머지 4개는 R2 해시와 같다. 이전 30-test 해시는 `frozen-glide-r2.json`, Blink 기준 해시는 `frozen-blink.json`에 보존한다. 이후 master R3 Vision 피드백 전까지 이 7개 파일을 더 수정하지 않는다.

master 수용 시나리오: 3직업 각 옵션 전환, ARC/VOID 외 점멸 선택 차단, 공중 메뉴 교체로 일반 점프 연료/횟수 비복구, 점멸 2회 후 착지 없이 마지막 사용 44틱에 2회 재충전, 점멸 타이머의 착지/옵션/직업 교체 보존, 일반 연료 소진 뒤에도 점멸 가능, 3회 추진 재개와 총시간 제한, 지면에서 재사용, native 바닐라 상승 중 활공/떨어진 뒤 활공 대비, 얇은 벽·낮은 천장·월드 경계에서 점멸, 죽음/로그아웃/차원이동 뒤 잔여 추진 없음. 격리 fixture의 `setDeltaMovement`만으로 native 상승 보존을 통과 처리하지 않는다.
