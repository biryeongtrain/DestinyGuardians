# W229 Warlock 구현

기준: ready baseline219937, master 통지 main HEAD `f5e304c`. 지정 슬롯 `w221-seventh_seraph_officer_revolver`의 batch.json owned_paths 19개만 작성했다. 공유 main/AbilityService/Combat/HUD/registry/command/PlayerAnimations/Camera/sounds 및 모델·사운드 자산은 master 소유다.

## 단계와 검증 상태

1. refresh 이전: main 읽기 전용 API 검토. 어떤 슬롯 수정/빌드도 하지 않음.
2. refresh 허용 뒤: Warlock Java 6개, 행동 GameTests 1개, tuning JSON 11개, 이 문서를 구현.
3. worker 정적 검증: JavaCompiler의 **parse만** 수행하여 Java7개 문법 확인. 타입/API 해석과 bytecode 생성은 하지 않았다. JSON11개 파싱/계약 ID/소유 경로 확인. 독립적인 전투·회복 실행 검증으로 간주하지 않는다.
4. R1 중앙 W22923개 중11개 실패라는 master 통지 및 server-w229.log/xml을 읽었다. Warlock10개 중6개 실패(Rift3/grenade/Storm/Daybreak),4개 통과다. R2 수정 뒤 재실행은 아직 없다. worker는 Gradle, 게임, 서버, Vision, Computer Use를 실행하지 않았다. parse 성공을 실행 통과로 보고하지 않는다.
5. 원본 Warlock blend 발견/61pose retarget은 master 통지로만 확인했다. worker는 blend/pose를 직접 검수하지 않았고, 전달된 timing-manifest의 Warlock clip 길이/kinematic 후보만 읽었다. Hunter pose로 대체하지 않았고 추측한 모션을 리핑 애니메이션으로 주장하지 않는다.

## 등록과 기본 장착

`WarlockAbilities.register()`는 `destiny:warlock/{jump,class_ability,arc_grenade,solar_grenade,void_grenade,arc_melee,solar_melee,void_melee,arc_super,solar_super,void_super}`의 11개 능력을 등록한다. `preset(Element)`는 Arc/Solar/Void마다 점프·직업·수류탄·근접·궁극기 5슬롯을 반환한다. 기존 Hunter 능력은 수정하지 않는다.

- 점프: Glide.
- 직업: Healing Rift.
- Arc: Storm Grenade / Chain Lightning / Stormtrance.
- Solar: Solar Grenade / Incinerator Snap / Daybreak.
- Void: Vortex Grenade / Pocket Singularity / Nova Bomb.

공유 initializer/command/기본 장착 및 lifecycle 연결은 master가 담당한다고 확인했다. master는 `AbilityService.equipped`의 class+slot 검증, AdrenalineJunkie의 HUNTER 제한 해제를 구현했다고 통지했다. 이 worker 슬롯의 해당 공유 파일은 변경하지 않았다.

## 움직임과 Healing Rift

Glide는 자체 runtime에서 최대60틱의 하강 제한을 제공한다. 공중 첫 입력으로 시작, 다시 누르면 즉시 취소한다. 취소/만료 뒤에는 접지 전 재시작할 수 없고, 기존 `GuardianRuntime.airJumpsUsed`가 소진된 비행 중 예산을 유지한다. 원래 상승 속도를 새로 부여하지 않으며, 하강 속도가 설정 floor보다 빠를 때만 `Motion.setVelocity`로 제한한다. `flying`, `mayfly`, `noGravity`, walk/fly speed는 변경하지 않는다. 기존 비행·물·탑승·사다리·elytra 상태에서는 시작/지속하지 않는다. 적용 중 fall distance만 초기화한다. 플레이어의 기존 중력 설정을 복구한다는 이름으로 덮어쓰지 않는다.

Rift는 onGround와 실제 발밑 collider의 UP 지지면을 확인한 뒤 수락한다. 거절은 `activate=false`로 전달되어 cooldown을 소비하지 않는다. 월드 블록을 놓거나 제거하지 않는다. 생성 당시 차원과 월드 위치가 고정되며 owner가 걸어 나가도 남는다. owner의 사망/로그아웃/직업·장착·차원 변경은 lifecycle 정리 조건이다.

회복 대상은 살아 있는 비관전자 `Player`뿐이다. 자기 자신, 같은 팀, 양쪽 모두 팀 미지정인 PvE 협동 Player를 동료로 본다. 명시적으로 다른 팀은 회복하지 않는다. 수평 원형 반경과 발 위치의 높이 차이를 확인하고, 고정 Rift 원점+0.3block에서 대상 눈까지 collider LOS가 있어야 회복한다. owner가 움직인 위치를 LOS 원점으로 사용하지 않는다. AABB 모서리/벽 뒤/층 위/반경 밖/PvE Mob은 회복하지 않는다. 회복 potion을 추가하지 않고 `heal`만 호출하며 owner는 pulse마다 한 번만 처리한다.

## 피해와 지속 동작

모든 공격은 `Combat.isEnemy` + 동맹/길들인 동물 제외를 먼저 확인하고 Player/ArmorStand를 공격 대상으로 고르지 않는다. 근접 직선/연쇄 및 폭발·장판 피해는 collider LOS를 추가 검사한다. 범위 공격은 pulse당 최대32개의 적을 선택한다. 체인에는 별도 UUID 방문 집합과 최대 hop 수가 있다. 적 탐색의 AABB만으로 벽 너머 피해를 주지 않는다.

- 수류탄은 `SimProjectile.launch`로 실제 서버 충돌을 처리한다. 충돌 후 고정 Field가 생성되고 유한 pulse로 피해를 준다. Storm은 번개 particle 연결, Solar는 지속 태양 장판, Vortex는 유효 적에게만 약한 끌림을 추가한다. 벽 충돌 위치는 incoming face 방향으로0.06block 띄워 blast가 벽 안/반대편에서 시작하지 않게 한다.
- 수류탄 수락 시 AdrenalineJunkie/Demolitionist 토큰을 캡처한다. 실제 launch 뒤 Demolitionist release를 한 번 전달하고 장판 피해는 grenadeDamage 경계를 사용한다. 별도의 수치퍽 전수 테스트를 신설하지 않는다.
- Chain Lightning은 조준한 첫 적과 각 hop의 LOS/범위를 확인하고 같은 적을 다시 때리지 않는다. Incinerator Snap은 서로 벌어진 실제5개의 spark projectile이며 한 번의 snap에서 한 적에게 powered contact를 중복 지급하지 않는다. 살아남은 적에게30틱 내3회, 각1HP의 자체 burn pulse를 준다. 이는 공유 `Statuses.SCORCHED`/바닐라 화염 상태를 변경하지 않는 **임시 MC burn**이다. 원작의 scorch stack/ignition 동등성을 주장하지 않는다. burn은 원래 contact 원점에서6block 이내/LOS 및 owner epoch가 유효해야 한다.
- Pocket Singularity는 실제 projectile 직접 접촉 피해 뒤 bounded 바깥쪽/위쪽 넉백을 준다. powered 접촉은 `MeleeWeaponTraits.accepted` 스냅샷을 `poweredDamage`에 전달한다. 자체 burn은 generic ABILITY 피해이며 powered melee reward를 반복 발동하지 않는다.

## 궁극기와 원본 contact 연결

모든 궁극기는 `ClassAbilityEffects.beginSuper(player, element, abilityPath)`가 성공한 뒤 `AbilityService.startSuper`한다. helper가 제공하는 3P camera/source start/idle/prop만 사용한다. `SuperSession.tick()`은 공유 AbilityService가 정확히 한 번 진행하며 `WarlockAbilities.tick()`에서 중복 진행하지 않는다. 매 session tick helper.superTick, 공격 준비 helper.attack, 실제 발사 시 helper.sound(super.fire), 종료 helper.endSuper를 사용한다. end는 반복 안전하다. 모든 실제 궁극기 피해는 `AmmoGeneration.SUPER`다.

- Nova Bomb: manifest에 별도 start/idle/end 없이 전체 cast인 `_attack`26틱만 있다. 첫 session tick에 helper.attack를 **한 번** 호출한다. 잠정 release14틱 + 실제 ONCE start blend1틱 뒤 자동 단일 발사하며 `primary()`는 추가 발사/준비 재시작을 하지 않는다. 별도8틱 시작 대기는 제거했다. 벽/적 충돌 또는 projectile 수명 종료에서 단일 폭발. 빠른 충돌이어도 전체26+1틱 cast recovery 이전에 session을 끊지 않는다. 최장 release 준비+비행+2틱으로 종료가 제한된다. R2는 Vortex 변형을 선택하여 충돌 후 별도 고정 필드를 생성한다. DDC Void127행의 생성 지연0.43초는20TPS 반올림으로9틱, 필드10초는200틱으로 적용한다. 시전 session/카메라 종료 뒤에도 Lease가 유효한 동안 남고, 각 pulse에 적 탐색·LOS·SUPER 피해를 적용한다. 필드 수는 owner당1개로 제한한다. 필드 지속을 roaming super 시간으로 사용하지 않는다. Cataclysm 추적체/원작 끌림·피해량 동등성은 구현하지 않았다.
- Stormtrance: 채널 창 초기값은 **0**이다. cast25+1틱 동안 공격 입력을 무시하며 입력 없이 자동 공격하지 않는다. primary가 유한12틱 채널 창을 열거나 갱신한다. helper.attack 뒤 잠정contact5+1틱에서 제한된 chain을 실행한다. 연타로 pending contact/원본 action을 재시작하지 않으며 재공격 간격은 max(attack_interval_ticks, 원본attack10+blend1틱) 이상이다. DDC 기본320틱 session이며 채널 창 뒤에는 추가 공격을 예약하지 않는다.
- Daybreak: cast32+1틱 뒤 primary로 검 공격을 수락한다. helper.attack 뒤 잠정contact8+1틱에서 실제 sword projectile을 발사한다. pending/recovery 중 연타는 무시하며 원본attack21+blend1틱보다 빨리 새 animation을 시작하지 않는다. 동시에 최대3개 비행 검, 유한 projectile 수명, DDC 기본480틱 session이다. 벽 충돌 후 near-side/LOS splash만 처리한다.

입력 잠금은 기존 공개 `SuperCamera.blockMovement`를 호출하여 cast/attack clip+blend 동안 적용한다. Camera 파일은 수정하지 않았다. 기존 API는 세션 소유 입력 gate로 이동/점프 입력만 막고 gravity/기존 impulse를 보존한다. 공유 AbilityService의 movementBlocked JUMP BUSY 경로도 그대로 사용한다. own super가 끝날 때 해당 block을 해제한 뒤 helper.endSuper를 호출한다.

읽은 manifest: `/private/tmp/destiny-w229-animation/timing-manifest.json`, SHA256 `12a6a8d83cf8daf71264eeee5eff6f987faf16f0b8551bc3157ece559bbbf83b`. `productProvisional.status=kinematic_visual_candidate_unconfirmed`; unknown `S80808C1A/S80808C12`를 damage event로 해석하지 않았다. Arc action80A8A8A8의 nearest candidate5틱(원래5.333틱), Solar80A8A960의8틱, Nova80A8AD80의14틱을 잠정 제품 release/contact로 채택했다. 각 JSON은 blend를 제외한 clip tick을 저장하며 코드가 실제 `SwordTiming.START_TICKS`를 더한다. 이는 master가 설명한 ONCE start blend와 동기화한 **미확정 후보**이며 decoded contact/Vision 수락은 아니다. helper.attack는 visual/animation only이고 `super.fire` sound는 실제 contact/projectile release에서 한 번만 호출한다.

## 수명과 정리의 소유권

`Lease`는 owner object/차원/GuardianData attachment identity/runtime identity/클래스/전체 Loadout 값과 취소 상태를 캡처한다. class/subclass/장착 epoch가 바뀐 뒤 오래된 projectile callback, field, burn은 추가 피해를 주지 않는다. 자기 능력 state 외 다른 potion/inventory/물리 flag/task를 정리하지 않는다.

`WarlockAbilities.tick(MinecraftServer)`는 유효하지 않은 owner state를 정리하고 Glide/Rift/Field/burn을 한 번 진행한다. `cleanup(ServerPlayer)`는 해당 owner의 모든 자체 state와 own super session만 정리하고 `clearAll()`은 자체 owner들을 반복 정리한다. 새 session을 취소하면서 다른 클래스의 session을 덮어쓰지 않는다.

R2에서 Lease의 identity set에 각 Warlock projectile을 기록한다. 클래스 cleanup은 해당 instance의 공개 `SimProjectile.cancel()`만 호출한다. 자연 super 종료는 session.flights만 취소한다. 취소는 callback 없이 holder destroy+ACTIVE.remove를 하는 master API에 의존하며, main에 해당 public 메서드가 존재함을 읽기 확인했다. 같은 owner의 ordinary emission 및 다른 owner는 보존한다. global pool/Tasks/Statuses clear를 호출하지 않는다. 자연 Daybreak 종료/클래스 cleanup 테스트는 unrelated ordinary flight를 함께 만들고 실제 잔여 sword/grenade만 없어지는지 확인한다. Nova post-impact Vortex는 session 종료와 별도 수명이지만 class/subclass/death/logout/dimension/server stop Lease cleanup에 포함한다.

## Rift 표시 모델 R2

master/아트 worker가 제공하는 `destiny:class_ability/warlock/class_ability` item만 optional ItemDisplayElement로 표시한다. 읽은 후보는 `/private/tmp/destiny-w229-props/vfx-class-ability-delta/`의 모델·item·텍스처 및 scripts/build.py다. ground field 지름16px, 중심[8,8,8], ground plane Y8.018, outer white ring radius7.82px 기준의 **새로 저작한 임시 FX**다. 리핑 원본 Rift FX라고 주장하지 않는다. 지름16px·anchor8을 class_ability.json에 기록하고 horizontal scale=`radius*32/diameterPixels`로 effect radius4block과 field 반경을 맞췄다. 높이 scale1은 독립 유지한다. origin은 실제 지지면+0.04block이며 아트 ground의0.018px offset을 보존한다. flow geometry/texture는 정적이며 원작 동적 flow 재현을 주장하지 않는다.

각 Rift가 holder 하나/display 하나를 소유한다. FIXED/NONE, full brightness, 원점 ChunkAttachment로 owner 이동에 따라 움직이지 않는다. duration 만료/epoch cleanup은 idempotent destroy한다. item 모델 또는 canonical metadata가 없으면 display를 생성하지 않고 기존 particle ring을 유지한다. fallback fire-charge를 Rift로 띄우지 않는다. 아트 자산과 ClassAbilityAssets의 class_ability 인식은 master 통합 범위이며 이 worker는 수정하지 않는다. 최종 모델 크기 변경 시 JSON canonical metadata 재조정이 필요하다. 실제 지면 z-fighting/observer/경사면/렌더 수락은 Vision2 미검증이다.

## 임시 MC 환산 수치

R2에서 아래 시간값만 새 DDC 근거표 `/private/tmp/destiny-w229-sources/ddc-class-values.md`(2026-10-28 조회)를 반영했다. 초→틱은20TPS·가장 가까운 정수(Math.round), Chunk Scalar는 시간에 곱하지 않는다. Base Cooldown을 특정 스탯의 실효 cooldown으로 재명명하지 않는다. HP/회복·피해·거리·속도·pulse·공격 소모·그 외 시간은 Minecraft PvE 임시 튜닝이며 원작 동등성을 주장하지 않는다.

| DDC 근거 | 기본 초 | 적용 tick |
|---|---|---|
| Class Abilities43 Healing Rift | CD118.7 / 지속15 | CD2374 / 지속300 |
| Arc126 Stormtrance | CD556 / 기본지속16 | CD11120 / 지속320 |
| Solar137 Daybreak | CD556 / 기본지속24 | CD11120 / 지속480 |
| Void127 Nova Bomb: Vortex | CD500 / 특이점10 / 생성지연0.43 | CD10000 / 별도필드200 / 지연9 |
| Void51 기본 Vortex Grenade | CD219.5 / 기본필드4 | CD4390 / 필드80 |

Remnants+1초/charged4.3+2.3초/스탯 실효 cooldown은 적용하지 않았다. Daybreak projectile6.5% 추가 에너지 소모/Storm 미기재 공격 소모는 이번 시간 대조로 구현했다고 주장하지 않는다. 원본 링크·행·조건은 위 근거표에 있다. 단위:20tick=1초, 거리block, 속도block/tick, HP2=하트1.

| 능력 | 기본값 | 런타임 상한/제약 |
|---|---|---|
| Glide | cooldown0초,60tick,-0.12block/tick 하강 | duration1~100tick, descent0.06~0.5, 접지 전 한 예산 |
| Rift | cooldown118.7초,300tick,반경4,높이1.5,pulse10tick,2HP | duration<=400, radius<=6,height<=2,pulse>=5,heal<=6HP |
| Storm grenade | cooldown40초,60tick,반경3.5,pulse15tick,3HP | duration<=200,radius<=5,pulse>=5,damage<=15HP |
| Solar grenade | cooldown40초,80tick,반경3.5,pulse10tick,2HP | 동일 |
| Vortex grenade | cooldown219.5초,80tick,반경3.5,pulse10tick,2HP | 동일, 매 pulse pull0.08block/tick 가산 |
| 공통 grenade flight | throw_speed1.1,위로0.12,gravity0.045,최대60tick | throw_speed0.4~2, owner당 flight+field최대4 |
| Chain Lightning | cooldown22초,6HP,첫사거리5,hop4,최대3대상 | damage<=30HP,range<=8,hop<=6,targets<=5 |
| Snap | cooldown22초,6HP,5spark,속도0.7,수명7tick | 동일 적 direct1회,각spark옆벌림0.17, burn30tick/10tick당1HP |
| Singularity | cooldown22초,6HP,속도1.1,수명35tick | knockback정규화0.5+위0.15 가산 |
| Stormtrance |CD556초,320tick,cast25+blend1,contact5+blend1,attack10+blend1,간격11tick,5HP,range10,hop4,targets3 | duration<=600,cast/attack<=80+blend,contact<=40+blend,interval>=5,range<=16,hop<=6,targets<=5 |
| Daybreak |CD556초,480tick,cast32+blend1,contact8+blend1,attack21+blend1,간격22tick,12HP,속도1.8,수명60tick,반경2.5 |flight<=3,life<=80,speed<=3,radius<=4,damage<=60HP |
| Nova Bomb: Vortex |CD500초,첫tick 전체attack26+blend1 시작,release14+blend1,속도0.9,수명60tick,반경4,24HP |contact<=40+blend,life<=80,speed<=2,radius<=6,damage<=100HP,단발; post-field지연9/지속200/pulse10/2HP,지속<=400 |

JSON의 cooldown_seconds와 params는 기존 AbilityTuning loader를 사용한다. 해당 DDC 시간의 Java fallback도 JSON과 일치시키고 Daybreak duration 상한을600으로 올려480이400으로 잘리지 않게 했다. 그 외 Java fallback은 임시값이다. 행동에 필요한 duration/range/damage/count/speed는 finite 값과 상한으로 제한한다. projectile 공통 drag0.99는 기존 SimProjectile 동작이다.

## 행동 GameTests 10개와 남은 검증

`WarlockW229GameTests`는 `destiny-test:w90_isolated`를 사용하고 TestPlayers/TestCleanup fixture로 실패/timeout에서도 정리한다. fake caster는 PlayerList에 없으므로 기존 Hunter HUD 테스트 방식대로 자기 super만 AbilityService.tickPlayer로 펌프한다. 등록된 동료 fixture는 월드에서 제거하고 packet channel도 정리한다. 다른 테스트의 global pool을 clear하지 않는다.

1. initializer의 실제11개 등록/세 속성5슬롯.
2. 공중/가짜 onGround Rift 거절 시 cooldown 미소비와 지지 블록 보존.
3. 동료 Player만 회복, Mob/벽 뒤/범위 밖/위층 제외, owner 이동 뒤 Rift 고정, 모델 존재 시 표시1개/동일반경과 만료 정리.
4. Glide 실제 velocity 제한, 재입력 취소, 예산 재활성화 차단, 접지 갱신과 만료/flag 보존.
5. 수류탄 실제 flight→field→만료 및 cooldown 중복/벽 뒤 피해 차단.
6. 세 powered melee의 실제 적중/5spark/특이점 넉백/벽 뒤 피해 차단과 수명 종료.
7. Nova 자동 준비/클릭 중복 방지/벽 폭발/실제 SUPER ammo contribution/단발 자연 종료, 이후 late arrival의 Vortex 실제 피해·LOS·별도 만료·subclass epoch 정리.
8. Stormtrance 입력 전 발사 없음/준비 이동·점프 lock/실제3타깃 cap/각 hop LOS/입력 뒤 유한 채널.
9. Daybreak 애니 준비 뒤 실제 projectile/연타 중복 금지/벽 충돌 splash, natural end가 잔여 sword만 취소하고 same-owner ordinary flight 보존.
10. 직업·서브클래스·차원·사망 epoch 정리, 실제 projectile owner격리 cleanup 및 다른 owner/효과/인벤토리/물리 flag 보존.

R2 미실행: 중앙 타입 컴파일 및10 GameTests 재실행, 실제 quit/서버정지 lifecycle, helper 실제 source animation/contact/카메라·장비·post effect 정리, 동시 다수 플레이어, 유리/펜스·모서리·경사면 LOS, 네이티브 입력, 모델·사운드·Vision. 사용자 단순 수치퍽 예외를 준수하여 숫자별 테스트는 추가하지 않았다. master 최종 수락 전 완료 QA/검증 통과로 표기하지 않는다.

## R1 중앙 실패 원인과 R2 대응

- Rift3건은 tick0 CLASS_ABILITY 거절. 기존 SuperCameraGameTests가 기록한 것처럼 런타임 floor fixture의 relativeY0이 AIR/아래 barrier인 환경이며 제품은 실제 UP support를 요구한다. fixture가 명시적으로 stone 지지면을 만들도록 했다. unsupported/onGround spoof 거절과 cooldown 미소비 기대는 유지했다.
- Storm tick65 / Daybreak tick60은 fake player가 rotation packet을 보내지 않아40틱 카메라 watchdog이 안전 해제한 로그를 확인했다. TestPlayers는 PlayerList 밖이므로 각 fake session만 tickPlayer로 펌프하며 실제 Rot packet heartbeat를 추가하고 rotations 증가/카메라 유지를 assert한다. watchdog을 끄거나 global world/projectile을 이중 tick하지 않는다. 실제 body aim과 MISS/BLOCK collider 전제도 확인한다.
- Grenade tick25는 R1의 결합 assertion만으로 damage0/through-wall 중 어느 분기가 실패했는지 확정할 수 없다. body center 조준과 native LOS 전제를 명시하고 front 실제피해와 blocked 무피해를 분리했다. testTick/serverTick/gameTime/feet/eye/look/support/rotation/target hp·position·ray, FieldSnapshot의 origin/age/pulses/lastTargets/actualDamage를 실패 메시지에 추가했다. 중앙 재실행 전 제품 결함 해결로 단정하지 않는다.
- 수치만 확인하는 새 테스트는 만들지 않았다. 기존10개 행동 테스트에 모델·수명·소유권 회귀를 포함했다. Daybreak 자연종료 검사는 fake session만 빠르게 진행하며 일반 projectile은 진행하지 않아 종료 시 instance 취소를 관측한다.

## R1 native 읽기 전용 검수

읽은 근거는 `/private/tmp/destiny-w229-native/frames/warlock-*`, `oracles/warlock*`, contact-starts-r1.jpg다. 실제 게임 입력/서버 실행/청취는 수행하지 않았다. Solar attack sample05는3P 검 공격과 화염 impact, Arc attack sample05는3P 전기 공격/impact, Nova start sample05→09는 cast의 구형 orb→보라색 폭발→1P 복귀를 관찰했다. 세 cleaned PNG는1P 복귀/남은 class rig가 보이지 않음을 확인했다. 장비·모든 virtual holder/피해를 PNG만으로 수치 검증한 것은 아니다.

Arc oracle start/attack camera/inSuper=true, presentation1, rotations49/126; emitted0은 projectile 없는 chain의 실패 증거가 아니다. Solar attack emitted1/impacts1/rotations127. Nova oracle은 완료 후 camera/inSuper=false/presentation0이라 초기화된 카운터0만으로 단발 release 수를 증명하지 않는다. 자동 cast/release/폭발은 PNG sequence 및 master 실행 보고 범위로 기록한다. Rift는 particle ring과 class cooldown771, jump 최종 oracle은 grounded/glide=false라60틱 bounded 하강을 수치 증명하지 않는다.

master 정정: native melee6종 CD0이며 simultaneous sneak+attack packet 순서상 수락되지 않았다. melee=true는 시퀀스 전송 기록뿐이므로 **실제 native melee 수락/피해 통과로 보고하지 않는다**. R2는 sneak2tick 선행+새 target2.5m 시나리오로 master가 교정 예정이며 제품 입력 코드는 변경하지 않았다. 서버 행동 GameTest melee와 native 입력을 구분한다.

R1 Nova PNG는 예전 ender-pearl형 orb다. master가 통합한38cube 임시 orb와 이번 새 Rift 모델은 Vision2 대상이며 아직 검수하지 않았다. 신규 모델/정적 FX를 원본 리핑 FX라고 주장하지 않는다. 소리는 청취하지 않았으며 release 시 sound 호출 연결만 코드로 확인했다.
