# W229 Titan 구현

상태: R2 frozen/통합 가능. R1 중앙23개 중 Titan5/10 실패 원인 수정 및 개별 flight cancel/방벽 모델/DDC 기본시간 반영. master 재통합/실행 검증 대기. 기준선 ready219937, HEAD f5e304c02f44de0c7c7e88e4a63658708484eb10. worker가 main·공유 파일을 수정하지 않았다.

## 범위와 구현 단계

1. 계약·배치·main API를 읽고 준비 보고. refresh 전 worktree 수정/빌드 없음.
2. refresh 승인 후 11개 Titan 능력, Arc/Solar/Void의 5슬롯 preset, 소유 tick/cleanup/clearAll 구현.
3. 실체적 원거리 방호, LOS, grenade/강화근접 퍽 귀속, SUPER 피해 귀속과 세션 lifecycle 구현.
4. 원본 timing manifest를 읽고 Solar/Void 액션 길이와 잠정 release 동기화. 파일 frozen 후 master 통합 가능 통보.
5. 실제 GameTests/중앙 compile/Vision·청취 검증은 master 대기. 아래 독립 javac 검사는 런타임 통과가 아니다.

등록 ID는 `destiny:titan/{jump,class_ability,arc_grenade,solar_grenade,void_grenade,arc_melee,solar_melee,void_melee,arc_super,solar_super,void_super}` 11개다. 기본 장착은 공통 jump/class_ability + 각 속성 grenade/melee/super. Hunter는 수정하지 않았다.

| 구현 파일 | 실제 동작 |
|---|---|
| TitanAbilities | register/preset/tick/cleanup/clearAll, owner·level·Loadout 객체 identity 검증, 소유 flight 추적, LOS와 유효 수치 clamp |
| TitanJump | 1회 공중 리프트, 유한 상승 보조, 착지 시 기존 airJumpsUsed reset 경로 사용. flying/mayfly/noGravity·인벤토리 변경 없음 |
| TitanClassAbility | 가상 ItemDisplay(모델 존재 시)/BlockDisplay fallback 1개 + 방향성 원거리 방호/HP. 실제 월드블록 배치·삭제·교체 없음 |
| TitanGrenade | Arc 충돌 후 유한 pulse, Solar 충돌 후 부착·fuse·1회 폭발, Void 유한 피해장+대상 억제(타깃 해제·감속·약화) |
| TitanMelee | Arc 전방 원뿔 powered strike, Solar 망치/Void 방패 SimProjectile 실제 충돌. 임의 회수·도탄 기능을 주장하지 않음 |
| TitanSuper | Arc 이동 타격/공중 slam, Solar roaming hammer throws, Void roaming shield throws. source 길이 보존 cadence, 유한 공격 수·지속시간 |

## 수치 출처와 단위

R2는 최신 DDC 근거표의 아래 명시된 기본 지속시간/CD만 초→20TPS 틱으로 직접 연결했다. 초기 사용자 요구의 방벽12초는 최신 DDC 적용 지시로20초가 됐다. 나머지 HP/피해/거리/속도/공격 소모/상태 효과는 **Minecraft 잠정 환산 기본값**이다. 숫자 단위는 cooldown_seconds=초, *_ticks=20TPS 틱, damage/health=MC health points(하트의 절반), 거리=블록, speed/acceleration=블록/틱 및 블록/틱²다. param은 finite/clamp로 제한한다.

| JSON | cooldown_seconds | params |
|---|---|---|
| jump | 0 | duration_ticks=16, max_up_speed=0.5, acceleration=0.095 |
| class_ability | 101.3 | duration_ticks=400, health=80, width=3, height=2.4 |
| arc_grenade | 40 | throw_speed=1.1, duration_ticks=80, pulse_ticks=20, damage=5, radius=3.5 |
| solar_grenade | 40 | throw_speed=1.1, fuse_ticks=20, damage=16, radius=3.5 |
| void_grenade | 175.6 | throw_speed=1.1, duration_ticks=80, pulse_ticks=20, damage=5, radius=3.5 |
| arc_melee | 22 | damage=14, reach=4 |
| solar_melee | 131.7 | damage=12, speed=1.8 |
| void_melee | 22 | damage=12, speed=1.8 |
| arc_super | 556 | duration_ticks=500, deploy_ticks=6, attack_interval_ticks=12, max_attacks=16, damage=24, radius=3.5, attack_contact_ticks=4 |
| solar_super | 556 | duration_ticks=420, deploy_ticks=26, attack_interval_ticks=32, max_attacks=16, damage=24, radius=3, projectile_speed=1.7, attack_contact_ticks=6 |
| void_super | 556 | duration_ticks=340, deploy_ticks=28, attack_interval_ticks=27, max_attacks=16, damage=24, radius=3, projectile_speed=1.7, attack_contact_ticks=6 |

DDC 근거: `/private/tmp/destiny-w229-sources/ddc-class-values.md`, SHA-256 `22782fa561aefe2b394d3f8d76489cde03a97bc6ece5ff765def8ccbc1c10aeb`. 조회2026-10-28 11:47:58–11:48:54 UTC, 원본 HTTP200 표시값 전사. 초→틱은20TPS, cooldown은 기존 Ability.cooldownTicks 반올림 경로, 아래 모든 값은 정확한 정수 틱으로 표현 가능하다. Chunk Scalar는 에너지 회수 배율이며 CD/지속시간에 곱하지 않았다. 아래 표만 이번 R2의 직접 DDC 연결 범위다.

| 원작 기본 조건/행 | CD초 → 틱 | 기본 지속초 → 틱 |
|---|---|---|
| [Towering Barricade class r26](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=527596209&range=B26:N26) | 101.3 → 2026 | 20 → 400 |
| [Hammer of Sol no-Aspect solar r105](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1186062409&range=B105:N105) | 556 → 11120 | 21 → 420 |
| [Fists of Havoc arc r98](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=618967225&range=B98:N98) | 556 → 11120 | 25 → 500 |
| [Sentinel Shield void r96](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B96:N96) | 556 → 11120 | 17 → 340 |
| [Throwing Hammer solar r99](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1186062409&range=B99:N99) | 131.7 → 2634 | 비행 수명/회수/자동 폭발은 별도, 미연결 |
| [Suppressor Grenade void r45](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B45:N45) | 175.6 → 3512 | suppression PvE10/PvP5초를 비행/필드 수명으로 대입하지 않음 |

중요한 적용 경계: SUPER의556초는 JSON/Ability CD 메타데이터로 연결했으나 **실제 충전은 공유 AbilityService.passiveSuperSeconds=180 및 kill energy 경로**다. shared service는 SUPER에서 cooldownTicks를 사용하지 않아 현재556초 실효 충전을 구현했다고 주장하지 않는다. master의 공유 범위 검토가 필요하다. 기본 지속시간은 실제 Session.until에 연결되어 적용된다. 원작의 공격/방어 추가 energy drain·Sunspot/Aspect 연장·스탯 실효 CD는 구현하지 않았다. HP80은 원작500 Construct HP의 직접 치환이 아니다. 근거표의 다른 능력/조건까지 모두 적용·검증했다고 주장하지 않는다.

고정 안전/기하값: 소유 SimProjectile 동시 최대8, 일반 grenade/melee/super projectile 수명60/40/40틱, grenade gravity .04, Solar melee .025, Solar super .018, 기타 투척0; grenade 초기 상방 .1. 방벽 caster 앞1.35블록/두께.12, 바닥지지 검사 .15~-.4, native 검색32×16×32, native projectile HP 비용10. 원거리 피해 HP 비용은 ALLOW_DAMAGE에 전달된 amount다. Arc 근접 전방 dot≥.55, super grounded 전방 dot>.25; Arc super 돌진 .65/+Y .1, 공중 slam 수평.45/Y-.9, 착지 대기최대20틱. 이 값도 원작 확정값이 아니다. 추가로 모든 직접/범위 피해는 PvE enemy + ally/tame 제외 + LOS를 검사한다.

## 방벽의 방호와 표시

- 설치 전에 alive/non-spectator/grounded·물/용암/수면/탑승/비행 상태와 바닥 지지·직사각형 공간 충돌·caster에서의 LOS를 검사한다. 실패 activate=false → cooldown 소비 없음.
- Polymer ChunkAttachment에 표시1개를 붙인다. `ClassAbilityEffects.item("titan/class_ability")`의 ITEM_MODEL이 정확히 `destiny:class_ability/titan/class_ability`이면 ItemDisplayElement/FIXED/NONE을 사용하고, 모델이 없으면 청색유리 BlockDisplay로 fallback한다. 기본 아이템의 ITEM_MODEL 존재만으로 custom 모델이라고 판단하지 않는다.
- art worker 산출물 `/private/tmp/destiny-w229-props/vfx-class-ability-delta/assets/destiny/models/class_ability/titan/class_ability.json`을 읽어 canonical bounds `[0,0,7.68]..[16,16,8.32]`, anchor `[8,8,8]`, fixed identity를 확인했다. 16unit/block 기준1×1×.04를 `(width,height,.12/.04)`로 배율 적용한다. authored+Z가 고정 normal을 향하도록 rotationTo 및 ItemDisplayRenderer Y=PI 보정을 사용한다. 중심/normal/폭/높이는 방호 판정과 같고 소유자의 이후 이동/회전은 평면을 바꾸지 않는다. 모델/팩은 master가 별도로 통합한다.
- 이 모델은 source mesh/UV가 없는 자체 제작 에너지 primitive VFX이며 리핑 방벽 모델이 아니다. 두꺼운 외곽과 중앙면 모두 동일 canonical 경계다. 회전/모델 표시의 실제 PNG 수락은 master 미검증 항목이다.
- 기본400틱=20초(DDC), HP80(MC 잠정). 재시전은 사전 검사 성공 후 이전 holder를 파괴하고 정확히1개로 교체한다. 만료/0HP/취소/죽음/클래스·Loadout 재선택/차원/로그아웃/서버 종료 cleanup에서 holder.destroy와 방호 map 제거를 함께 수행한다.
- native projectile은 이전→현재, 현재→예상 다음 위치의 평면 교차를 검사한다. front→back이고 폭·높이 안인 경우만 제거한다. 바닐라 블록 충돌이 먼저 있으면 방벽까지 관통했다고 처리하지 않는다. 적대 Mob 또는 owner 없는 native projectile을 처리하며 player 발사체/아군/길들인 Mob 발사체는 제외한다.
- ALLOW_DAMAGE는 IS_PROJECTILE/IS_EXPLOSION 또는 직접 Projectile source만 처리한다. sourcePosition과 피해자 중심 사이의 front→back 평면 교차를 검사한다. 빠른 native projectile이 이미 피해자에 닿았으면 실제 velocity로 입사 선분을 복원한다. 책임 entity는 적대 Mob 또는 owner 없는 projectile이어야 한다. 근접 공격/후면/옆/높이 밖/방향 없는 환경피해/BYPASSES_SHIELD/다른차원은 통과한다.
- HP가 남았으면 마지막 초과 피해도 그1회를 전부 막고 HP0 즉시 파괴한다. Fabric boolean 이벤트만으로 잔여 피해를 부분 전달한다고 주장하지 않는다. 피해 재적용/재귀 없음.
- 표시 자체는 collision entity가 아니다. 플레이어·몹 이동을 벽처럼 막지 않으며 가상 SimProjectile/hitscan 전체의 교차를 가로채는 공유 API도 없다. 이 배치의 방호 범위는 native projectile + 적격 ranged DamageSource이다. shared HUD/registry/Combat/Camera/sounds 파일은 master 소유다.

## 전투·퍽·소유 정리

grenade는 수락 시 AdrenalineJunkie/Demolitionist token을 캡처하고 실제 발사 성공 시 Demolitionist.grenadeReleased를1회 호출한다. grenadeDamage는 각 실제 피해에 원래 token을 전달한다. melee는 accepted snapshot을 실제 powered contact에만 사용한다. super 피해는 Combat.damage의 AmmoGeneration.SUPER 경로다. generic playerAttack source만으로 grenade/melee/super 귀속을 추정하지 않는다.

SimProjectile는 실제 world clip 뒤 entity 충돌을 처리한다. Titan은 확장 충돌 상자가 얇은 벽 뒤 target을 잡을 수 있는 경우까지 추가 LOS로 거절한다. 범위 폭발은 wall hit normal 쪽으로 .08 offset 후 대상마다 LOS를 검사한다. 지연 callback은 원래 owner/level/Loadout identity와 취소 토큰이 살아있을 때만 작동한다.

Void 억제는 기존 Statuses 전역 소유권을 덮어쓰지 않는다. 자체 필드가 Mob 타깃을 해제하고, 기존 동종 효과가 없을 때만 weakness/slowness를 설치한다. cleanup은 자신이 설치한 instance·amplifier·남은 만료시간과 일치할 때만 제거한다. 더 강하거나 더 길게 갱신된 효과와 기존/다른 종류 효과는 보존한다. 기존 Keyword.SUPPRESSED map 등록/원작 능력 사용 봉쇄를 주장하지 않는다. 억제의 Minecraft 구현은 명시된 Mob 타깃·이동·공격 디버프다.

R2는 master가 추가하는 public SimProjectile.cancel() 인스턴스 API를 사용한다(impact callback 없이 idempotent destroy/ACTIVE 제거). Context.launchFlight는 실제 handle을 반환하고, Session은 자신이 발사한 handle만 별도로 기록한다. 궁극기 시작 시 일반 flight 존재를 이유로 거절하던 R1 임시 제약을 제거했다. 궁극기 종료/자연 만료는 Session.flights만 cancel하고, 전체 Context.cleanup도 자신이 수락한 shots만 cancel한다. 같은 Context의 이전 일반 grenade/melee flight·기존 grenade fields·제3기능 flight·타 소유자 flight는 세션 종료로 지우지 않는다. service의 super 중 일반 능력 입력 잠금은 기존대로 유지한다. master 공유 API 통합 전에는 R2를 실행할 수 없으며 worker가 공유 SimProjectile 파일을 수정하지 않았다.

cleanup/clearAll은 idempotent. 클래스 이동·죽음·로그아웃·dimension·서버 종료는 master가 한 번 wiring하며 worker가 중복 tick listener를 등록하지 않는다. register의 ALLOW_DAMAGE event init만 자기 영역에서1회 등록한다.

## 원본 timing과 잠정 contact

읽은 manifest: `/private/tmp/destiny-w229-animation/timing-manifest.json` SHA-256 `12a6a8d83cf8daf71264eeee5eff6f987faf16f0b8551bc3157ece559bbbf83b`.
`PlayerAnimations.play`의 `.start(SwordTiming.START_TICKS)`와 `SwordTiming.START_TICKS=1`을 main에서 확인했다. source cast/attack full length에는 이1틱을 더한다. `SuperCamera.blockMovement` 기존 API로 시작 준비 동안 입력만 잠그며 물리 플래그·중력·인벤토리를 바꾸지 않는다. 공유 Camera 파일 변경 없음.

| Super | source cast ceil | 준비/공격 잠금 | attack full ceil | 최소 다음 공격 | release |
|---|---|---|---|---|---|
| Solar | 26틱 | 27틱 | 32틱 | 33틱 | candidate6+blend1=7틱 |
| Void | 28틱 | 29틱 | 27틱 | 28틱 | candidate6+blend1=7틱 |
| Arc Fists | 원본 미식별 | MC 잠정6틱 | 원본 없음 | MC 잠정12틱 | MC 잠정4틱 후 strike/하강, 공중 slam은 실제 착지 때 |

Solar/Void contact는 source wrist kinematics의 **미확정 제품 후보**다. manifest의 contact=null은 decoded damage event가 없음을 뜻한다. Solar hammer spawn audio frame15=.5초=10틱은 mesh visibility/contact 확정 근거가 아니므로 gameplay release를10틱으로 단정하지 않았다. 선택한 release6틱과 별도 cosmetic spawn10틱에는 모두 start blend가 붙는다. 소유 worker는 prop 숨김/재장착/원본 리타게팅을 수정하지 않았다. master visual helper 범위다.

primary는 visual/animation-only ClassAbilityEffects.attack을1회 호출하고 release를 예약한다. 준비·현재 pending·원본 전체 action interval 동안 반복 입력은 새 action으로 덮지 않는다. 실제 release 시 aim/origin을 샘플링하고 payload 성공 때 super.fire를1회 호출한다(Arc는 실제 strike/slam contact). ClassAbilityEffects.superTick은 매 게임 틱 호출하며 동일 틱 중복 호출은 막는다. 종료 시 아직 예약된 release/slam도 취소한다.

Solar/Void start/attack은 전달된 manifest의 source-backed motion이다. idle은 source terminal pose를 취한 explicit hold이므로 원작 idle animation이라고 주장하지 않는다. Fists를 Thundercrash로 대체하지 않았으며 Fists/end 원본이 없는 모션은 리핑 애니메이션으로 주장하지 않는다. 원본 검수·모델·소리·최종 Vision 타이밍 수락은 master 담당이다.

## 검증

작성한 `TitanW229GameTests`는10개 behavior test이며 `destiny-test:w90_isolated`/floor/TestPlayers/TestCleanup를 사용한다.

1. 11능력과3속성 preset/class/slot/element.
2. 실제 lift 속도, 중복 제한, 수명·착지 reset, 기존 physics flags/inventory 보존.
3. 방벽 공중·사용자 블록 충돌 거절/쿨타임 무소비/블록 보존.
4. 실제 hurtServer 앞면 원거리 차단, HP 소비·0HP 제거, 근접/후면/환경 통과, owner 없는 arrow source.
5. native arrow 앞뒤 sweep, 재시전1개, 제품 시계 기준설정 수명-1틱 생존/수명틱 expiry(기본399/400).
6. 실제 Arc grenade 반복 피해와 벽 차폐·player 제외·owner 귀속·유한 field 종료.
7. Solar fuse 지연1회 폭발, Void 실제 weakness/damage와 unrelated effect 보존 cleanup.
8. Arc powered cone/LOS, Solar/Void 실제 thrown melee 충돌.
9. 세 super energy/prepare/pending contact/반복 입력/실제 피해·귀속. 실제 일반 grenade flight가 Context에 있어도 시전 가능하며 두 flight 공존 후 session 취소가 일반 flight를 보존. 자연 만료 직전 일반/궁극기 flight가 실제 공존하고340틱 만료는 궁극기 flight만 cancel함을 확인.
10. 재선택/죽음/차원/클래스 해제/반복 cleanup과 다른 owner 방벽 보존.

embedded fixture는 PlayerList에 없어 AbilityService.tickPlayer를 명시 호출한다. 그러나 공유 SuperCamera.tick은 자체 ACTIVE map을 순회하므로 fake owner도 watchdog 대상이다. R2 fixture는 매 tick 실제 connection.handleMovePlayer(Rot) 경로를 통과시키고 rotations 카운터가 정확히1 증가했는지 확인한다. watchdog을 끄거나 우회하지 않는다. per-owner Titan runtime도 유효 소유 레코드에서 tick한다. GameTest fixture/targets를 terminal TestCleanup로 정리한다. 공유 테스트 manifest 등록은 master 담당.

worker 수행: JSON 파싱/파일 범위 검사, API javap, 독립 javac(Java25, 구현6+GameTests1) 타입 검사. R2 최종 검사는 캐시된 main/gametest 클래스·26.3 MC/Fabric/Polymer 및 read-only main의 실제 ClassAbilityEffects.java/SimProjectile.java 소스를 함께 javac하여 exit0. `/private/tmp/destiny-w229/titan-compile-check/actual-api-result.txt` 및 `actual-api-sources.json`에 결과와 입력 해시를 남긴다. 출력은 /private/tmp에만 썼다. 초기 signature stub 검사보다 강화했지만 mixin·중앙 Gradle·실제 GameTest 통과를 대신하지 않는다.

미수행: 실제 GameTests 실행/중앙 Gradle/서버/client/Vision/CU/청취. 수치퍽 개별 테스트 예외 유지. 새 행동 검증만10개이며 수치별 테스트를 양산하지 않았다.

## master 수락 항목

공유 ClassAbilityEffects.attack이 visual/animation-only인지 확인하고 super.fire 중복 호출을 제거한다. TitanAbilities lifecycle 및 registry/preset/테스트 entrypoint를 통합한다(사용자 통지상 main wiring 완료). 실제 helper 기준 compile·10 GameTests 후 native 입력과 실제 PNG로 방벽 앞뒤/HP/20초/취소, 3속성 장착, grenade·melee LOS, source start/attack/release/종료를 취합한다. 실패는 worker 소유 delta로 재요청한다. 본 worker는 commit/push/reset/stash/clean/워크트리 삭제를 수행하지 않는다.


## R2 중앙 실패 root cause와 수정 (2026-10-28)

입력 증거: main `docs/qa/2026-10-28/w229/server-w229.log` 및 `server-w229-report.xml`. 중앙23개 중 Titan은10개 중5개 실패였다. **재실행 통과를 아직 주장하지 않는다.**

### 방벽4개: fixture의 실제 지지 누락

모든 실패가 tick0 `Accepted CLASS_ABILITY`이며 긍정 배치 이전에 멈췄다. floor.snbt의 상대 y=0 stone을 실행 fixture도 그대로 제공한다고 가정하고 fake player의 onGround만 true로 설정한 것이 오류다. 기존 `SuperCameraGameTests.nativeDropDamagesDespiteSpoofedGroundPackets`에도 "running26.3 fixture exposed air there and a barrier one block below"라고 기록돼 있어 landing pad를 명시적으로 설치한다. Titan의 support ray는 feet+.15 → feet-.4 범위여서 한 블록 아래 보호 바닥을 ground로 인정하면 안 된다.

R2 fixture는 배치 전 자기 테스트 상대 y=0에 stone pad를 설치하고 block state를 확인한다. 부정 대조는 pad가 있어도 airborne이면 실패, onGround=true여도 wall 지지 위치의 실제 바닥을 제거하면 실패/cooldown0, 지지 복구 후 사용자 diamond obstruction이면 실패/블록 보존이다. 정상 배치는 표시 생성·실제 방향 피해·화살·수명 검증까지 계속 진행한다. 제품의 support/clearance 검사를 완화하거나 블록 쓰기를 추가하지 않았다.

master 제공 native R1 증거도 별도로 검수했다. `/private/tmp/destiny-w229-native/frames/titan-class-after.png`는 투명 방벽 표시가 있고, `oracles/titan-class.json`은 body=(.5,65,.5), ground=true, barricade=true, class cooldown670t를 기록한다. 이는 실지면의 시전/표시 수락 근거이며 HP·방향 방호·12초 만료 검증을 대신하지 않는다.

### 궁극기1개: 실제 Rot heartbeat 없는 fake camera가 중도 종료

`allThreeRoamingSupers...`는 tick336 비행 대조군 부재로 실패했다. 로그에 같은 Titan fixture의 `Super camera rotation timed out ... safe release`가2회 있다. R1 주석은 fake가 PlayerList에 없으므로 camera watchdog도 자동 호출되지 않는다고 잘못 가정했다. 실제 AbilityService.tick은 SuperCamera.tick을 호출하고, 이 함수는 PlayerList가 아닌 자체 ACTIVE 세션을 순회한다. 회전 packet 없는40틱 후 안전 해제가 정상적으로 궁극기를 끝냈다. 따라서 마지막230틱 공격 전에 세션이 사라져 비행 대조군도 생기지 않았다.

R2는 `connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(...))`를 매 tick 주입해 제품 mixin→SuperCamera.move→lastRotation 갱신 경로를 그대로 사용한다. rotations 증가를 assert하여 단순 setYRot/setXRot으로 대체하지 않는다. watchdog timeout 값/제품 취소 정책은 바꾸지 않았다.

기존 h.runAfterDelay의 test-relative clock과 제품의 level.getGameTime 기준을 분리했다. R2의 수명/contact 관측 callback은 product game-clock deadline에 예약하고, 도착 game tick이 정확한지 assert하며 failure에 test/game/server 시계와 delta를 포함한다. DDC Sentinel 기본17초에 맞춰 자연 만료 직전339틱에는 동일 세션이 살아 있고,340틱에는 끝나며 자신이 발사한 flight만 취소됐는지 확인한다. 단순히 관측 시점을 늦추거나 기대를0으로 약화하지 않았다.

### 추가 사용자 지시 반영

R2는 public instance cancel API를 사용한 정밀 소유 취소로 일반 flight 중 super 거절 임시 제한을 없앴다. 테스트에는 실제 grenade flight와 super flight 공존/개별 취소, long-lived ordinary control을 둔 자연 만료 보존을 포함했다.

native R1 근접6종의 same-tick sneak+attack은 서버cd0이므로 수락 성공으로 세지 않는다. master의 sneak2tick→attack1tick 및 cooldown 재확인이 필요하다. worker는 제품 입력 코드를 수정하지 않았다. 손 파지/하체 이동 모션/원본 리타게팅은 master 및 art worker 소유다.

R2 DDC 적용 후 watch limit: 방벽 행동 테스트 maxTicks260→430, 복합 궁극기 테스트450→600. 제품 설정에서 실제 수명을 읽어 마지막-1/만료틱을 검증한다. 복합 시나리오는 일반 flight 공존38 + 세 공격16/40/42 + Void 자연 만료340 = 약476틱이므로 기존450틱 한도를 넘는다. global tunings/공유 JSON override 없이 기본 DDC 수명을 사용한다. Arc500/Solar420은 공격 검증 후 명시 종료하여 전체 수명 대기를 더하지 않는다. 숫자만 assert하는 신규 테스트는 추가하지 않았다.
