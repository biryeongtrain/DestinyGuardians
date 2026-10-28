# W230 헌터 확장 궁극기

## 구현 범위와 조작

기존 헌터에 새 SUPER ID 네 개를 등록한다. 기존 속성별 기본 프리셋은 보존하며, 로드아웃에서 해당 ID를 SUPER 슬롯에 장착해야 한다. 발동은 기존 웅크리기+손 교체, 후속 기본 공격은 좌클릭이다. 모든 신규 궁극기는 서버 후방 3인칭을 사용한다. 실제 인벤토리는 건드리지 않고 공유 ClassAbilityEffects의 가상 장비·스킨 리그를 사용한다.

| ID | 발동과 후속 조작 | 서버 동작 |
|---|---|---|
| `hunter/blade_barrage` | 발동만으로 전체 시전, 좌클릭 불필요 | 7개씩 두 차례, 합계14개의 충돌 칼. 착탄 후10틱 뒤 폭발. 시전 카메라와 투사체·지연 폭발 수명을 분리한다. 클릭 연타는 조기 발사·3차 투척을 만들지 않는다. |
| `hunter/spectral_blades` | 발동 후 이동, 좌클릭 교대 베기, 웅크리기+좌클릭 강공격 | 원본 약공격1/2 교대. 강공격은 원본 약공격3을 임시 대응한다. 접촉 지연·회복 중 입력 차단, 전방 범위·LOS 피해. 약공격은 이번 시전 소유 바닐라 은신 해제, 강공격 접촉은 재적용. |
| `hunter/gathering_storm` | 발동만으로 지팡이1개 자동 투척 | 표면·적 충돌 후 지팡이를 고정. 40틱 뒤 낙뢰, 추가24틱 뒤 160틱 동안14틱 간격 피해. 캐스트와 독립된 지팡이/필드 수명이다. 빗나가 수명이 끝난 공중 위치에는 필드를 만들지 않는다. |
| `hunter/storms_edge` | 첫 투척 자동, 남은2회는 좌클릭 | 유한 칼 투사체→안전 도착부피 검사→순간이동·회오리. 이전 투사체/회복 중 연타 차단, 총3회 상한. 안전 도착점이 없으면 이동·회오리를 생략하고 해당 투척을 소모한다. |

스펙트럼 칼날은 기존 헌터 연막탄의 바닐라 `MobEffects.INVISIBILITY` 경로를 사용한다. 준비 완료 후 실제 은신을 적용하며, 약공격 수락은 이번 시전 소유 효과를 즉시 해제하고 강공격 접촉은 재적용한다. 실제 flying/noGravity/noPhysics 플래그는 바꾸지 않는다. 발동 후 준비 종료 시 이동을 풀며, 시전/공격 중 루프 선택은 공유 애니메이션 계층이 담당한다.

은신은 기존 효과를 덮어쓰지 않는 scoped lease다. 효과가 없을 때만4틱짜리 `CloakEffect`를 설치하고 자신의 효과만2틱 이하일 때 갱신한다. `MobEffectInstance.update`는 외부 갱신도 같은 살아 있는 객체를 수정하므로 단순 reference 비교만 하지 않는다. 같은 시전의 비공개 token으로 갱신한 경우만 계속 소유하며, 다른 입력을 한 번이라도 받으면 기존 객체가 그대로여도 소유권을 포기한다. 약공격·정상 종료·사망·Loadout epoch 변경·명시 cleanup은 정확하게 소유 중인 객체만 제거한다. 타인의 선행/강화/연장/동일값 갱신과 force-replacement는 보존한다. 모든 효과를 지우거나 원래 은신 시간을 늘리는 복원은 하지 않는다.

시전 상태가 은신인 동안 실제 은신 효과가 있으면 주변24블록의 적대적 Mob 중 이 owner를 현재 target으로 가진 최대32개만 표적을 비운다. 다른 플레이어/몹을 대상으로 한 AI 선택을 바꾸지 않는다. 바깥 범위의 탐지와 재탐지는 바닐라 invisibility visibility-weight를 사용하며 완전한 전역 AI 탐지 금지로 주장하지 않는다. **바닐라 효과와 AI 상태가 적용돼도 BetterModel item_display 리그가 자동으로 투명해진다고 주장하지 않는다.** BM 쌍칼·피부의 관전자별 비가시 렌더, PvP 팀별 은신 표시·진실의 시야는 별도 검수/후속 연결 대상이다. 외부 은신이 있는 경우 약공격도 그 효과를 지우지 않으므로 실제 은신이 남을 수 있다.

## 수치 근거

조회: 2026-10-28, [Destiny Data Compendium](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4). 세부 반환본 `/private/tmp/destiny-w230-sources/ddc-values.json`의 exact_cells와 fetch SHA를 근거로 한다. 단순 초→20TPS만 적용하고 Chunk Scalar를 곱하지 않는다.

| 궁극기 | DDC 행·조건 | 적용 |
|---|---|---|
| 칼날 장전 | Solar75, 기본14칼, Knock 'Em Down 제외, 기본455초 | cooldown455초, 두 번7칼, 착탄 뒤0.5초 지연 폭발. 강화20칼 미적용. |
| 스펙트럼 칼날 | Void67, 은신 상태 기본23.5초, 드러난 상태 배수1.5 | cooldown556초, 최대470틱. 드러난 동안2틱마다 추가1틱 수명 소모. 약/강 공격당 소모는 DDC 물음표 수치를 확정하지 않고10/35틱 MC 잠정값. |
| 폭풍결집 | Arc66, 기본500초, 착탄+2초 낙뢰, +1.2초 뒤8초 필드,0.7초 간격 | cooldown500초,40/24/160/14틱. 원작10미터를4블록과 동등하다고 주장하지 않는다. |
| 폭풍의 칼날 | Arc68, 기본625초, 유지시간·투척당 에너지 DDC `?` | cooldown625초. MC 잠정 최대400틱·3회 투척. 원작 기본 유지시간 확정값이 아니다. |

모든 Minecraft 피해·반경·속도·강공격 비용은 플레이 가능한 초안용 잠정값이다. 원작 HP/미터/방어 배율과 동일 단위로 환산하지 않았다. 이 동작들을 단순 수치 테스트로 중복 검증하지 않는다. 칼/단검 유도와 원작 스코치·약화·감전 상태이상, 피해 저항·특성·힘의 보주까지 이 파일이 구현한다고 주장하지 않는다.

## 원본 모션과 타격 후보

애니메이션 리더의 실제 `.blend` 평가→61포즈 산출을 사용한다. 플레이어 궁극기3P 소스이며 무기1P 장전 소스로 취급하지 않는다. 원본 평가·출처·리타기팅 한계는 animation leader의 timing-manifest와 provenance가 근거다. worker는 Blender를 별도로 열었다고 주장하지 않는다.

Java는 `ClassSuperModelAssets.durationTicks(path,phase,fallback)+SwordTiming.START_TICKS`로 실제 클립 길이를 읽는다. 부족한 런타임 동작을 원본이라고 표시하지 않는다. `_start` 전체 길이와 투척/접촉 후보를 분리한다.

| 동작 | source tag / 구간 | 선택한 잠정 접촉시점(시작 보간 포함) |
|---|---|---|
| 칼날 장전 start | `80A8AD86`,1..60,1.9667초,40틱 | 1차 원본21프레임의 손목속도 후보15틱. 2차29틱은 제품 임시 분할점이며 원작 이벤트가 아님. |
| 폭풍결집 start | `80A8ABF2`,1..50,1.6333초,33틱 | 원본7프레임 손목속도 후보5틱. 실제 투척 순간은 R1 Vision에서 검수. |
| 스펙트럼 start | `80A8AAC4`,1..48,1.5667초,32틱 | 전체33틱 이후 이동·공격 허용. 별도 cast 피해 없음. |
| 스펙트럼 약1/약2 | `80A8AAC8` / `80A8AAC7`,각1..45 | 원본9/7프레임 후보7/5틱. |
| 스펙트럼 강공격 임시 | 약3 `80A8AAC5`,1..53 | 원본5프레임 후보4틱. **원작 강공격/uppercut 소스를 확보했다고 주장하지 않는다.** |
| 폭풍의 칼날 start | `80A8ACCE`,1..51,1.6667초,34틱 | 원본27프레임 손목속도 후보19틱. |
| 폭풍의 칼날 blink | `80A8ACF0`,1..3 | 실제 짧은2틱 클립+시작 보간1틱. source blink-entry이며 완성된 긴 회오리 원본이 아님. |

전달된 이벤트는 원작 damage/release event로 해독되지 않았다. 위 후보는 명시적으로 `kinematic_visual_candidate_unconfirmed`이며 R1/R2 실제 PNG를 통해 조정한다. 스펙트럼 idle/move/air는 animation leader가 명시한 MC authored 루프다. 폭풍의 칼날 후속 투척에는 전용 `_attack`이 없을 때 `_start`를 재사용하고 blink-entry를 뒤에 연결한다.

## 소품과 적군 변형

아트 계약: NONE context, raw16units=1block, display center `(8,8,8)`. `hunter/gathering_storm`은 손잡이 중심 지팡이, `hunter/gathering_storm_embedded`는 바닥 앵커·높이1.5블록의 독립 모델이다. 필드 모델은 scale1, 충돌점에서 아래8블록까지 지면을 찾아 배치한다. 피해/LOS 원점은 벽 가까운 충돌면 바깥을 보존하므로 지면 모델 위치로 옮겨 벽 너머 피해를 만들지 않는다. 지면을 찾지 못한 곳은 충돌 위치를 기준으로 표시한다.

기존 적군 `_enemy` 선택 규칙을 공유 helper가 제공한다. 관전자별 실제 PvP 팀 라우팅은 이 worker의 범위가 아니며 자동 구현됐다고 표시하지 않는다. spectral 칼은 임시 제작이며, 지팡이·단검·태양 칼은 원본을 참고한 재설계라는 아트 출처 구분을 보존한다. 전용 Gathering spear 이벤트 연결을 원작 Arcstrider staff 참고품으로 대체한 한계도 남긴다.

모든 사운드는 `sound(player,element,path,action)`으로 호출하여 cast 종료 후 필드도 궁극기별 key를 유지한다. 공유 sound routing/음원 선정은 master/source leader가 담당한다.

W231 중복 수정: 칼날 장전은 첫 칼 투척 순간 `blade_barrage.fire`를 시전당1회만 재생한다. 두 번째 fan에서는 반복하지 않으며 준비·종료 단계의 숫자 후보음원을 덧씌우지 않는다. 실제 투사체14개·두 차례 투척은 유지한다.

## 충돌·소유권·수명

- `Combat.isEnemy`에 더해 allied/tamed를 제외하고, 모든 범위 피해는 필드/접촉 원점의 collider LOS를 확인한다.
- lease는 플레이어 객체·connection·level·GuardianData·GuardianRuntime·Loadout 객체 epoch를 캡처한다. 같은 값의 새 Loadout도 이전 lease를 무효화한다. 직업/장착 변경, 죽음·관전·로그아웃·차원 변경과 명시 cleanup은 지연 callback을 무효화한다. 잠깐 다른 직업을 거쳐 돌아온 상태는 master의 lifecycle cleanup과 함께 처리한다.
- 시전·필드 모두 level gameTime의 절대 마감시각을 사용한다. 같은 gameTime에 여러 번 호출해도 session.tick은 한 번만 처리하고 필드 pulse/단일 폭발도 복제되지 않는다. fake player 수동 pump로 애니메이션을 수백틱 빨리 끝내지 않는다.
- 각 투사체 인스턴스만 취소한다. `discardOwned`로 같은 플레이어의 무관한 투사체까지 제거하지 않는다. explicit cleanup은 lease→session→field→knife→flight 순으로 폐기한다. 다른 플레이어 필드와 실제 인벤토리·물리 플래그는 보존한다. Spectral 은신 효과는 위의 정확한 token/reference 소유 규칙을 따른다.
- 필드는 owner당1개, 칼은2×최대9개, 폭풍의 칼날 비행은 동시1개/총3회다. 모든 투사체·폭발·필드에 유한 수명이 있다. 새 accepted super는 그 owner의 이전 expanded 잔여 효과만 정리한다.
- blink는 최대15블록,0.2블록 간격의 플레이어 AABB sweep,발/몸통/머리 collider ray,로드된 chunk/월드경계와 도착1.5블록 내 지면을 확인한다. 벽/천장/기둥에 몸이 끼는 후보는 버린다. 유효 후보가 없을 때 강제로 teleport하지 않는다. 허용되지 않은 게임모드·권한·노클립·중력 플래그는 사용하지 않는다.

## 서버 검사와 master Vision 대기열

새 `HunterW230GameTests`6개는 다음 실제 동작을 검증하도록 작성했다. worker는 중앙 빌드·서버·Vision을 실행하지 않는다. 단순 수치별 테스트를 추가하지 않았다.

1. 칼날 장전: 조기 클릭 무시, 자동14칼/2fan, 지연 폭발·벽 LOS, 실제 인벤토리 보존.
2. 폭풍결집: 실제 충돌, cast 후 유지되는 낙뢰/필드와 늦게 들어온 적 피해, 벽 차단·자연 만료.
3. 스펙트럼: 준비 후 이동, 교대 베기/강공격 contact, 연타 차단, 실제 은신·AI 표적 해제와 약/강 공격 전환. 선행 외부 효과와 같은 객체 외부 갱신의 보존, 사망·Loadout 교체 정리, 물리 플래그 보존.
4. 폭풍의 칼날: 자동1회+후속2회, 유효 순간이동·회오리 피해, 벽 반대편 보호·몸 충돌과 최종 정리.
5. 눈높이1블록 슬릿을 통과한 칼도 실제 플레이어 몸이 통과하지 못하면 순간이동/회오리를 거절.
6. 독립 field owner, 동일 값 Loadout 새 epoch로 폐기, 무관한 같은 owner flight 보존, 직업 왕복 후 부활 금지.

fixture는 명시 지면과 native fakecamera rotation heartbeat를 사용하고 skyAccess로 낮은 테스트 천장 오염을 막는다. 플레이어에 noGravity를 켜 충돌 검사를 우회하지 않는다. target은 AI/중력을 막아 피격 위치를 유지하되 벽 bbox와 겹치지 않게 둔다.

R1 Vision 반환은 네 cast 전체, 스펙트럼 정상 베기2회/강공격·이동, 지팡이 식립과 cast→필드 전환, Storm 첫/2/3회·벽 가까운 실패 후보를 포함해야 한다. worker가 프레임별 연락/가림/복귀를 검수하고 수정본을 반환한 뒤 master가 R2를 진행한다. 이 문서는 작성 단계이며 중앙 gate·R1/R2 통과를 선행 주장하지 않는다.

## Cloak 수정 이력

2026-10-28 master R1 초안 검수 요청으로 시각 상태 전용 cloak를 실제 scoped 바닐라 은신으로 보완했다. 26.3 실제 merged jar의 `LivingEntity.addEffect`가 신규 효과 객체를 직접 저장하고 기존 효과의 가상 `MobEffectInstance.update`를 호출하는 점을 javap로 확인했다. worker 구문 검사만 수행했으며 새 은신 동작의 중앙 GameTest·R1/R2 Vision은 아직 실행하지 않았다. 테스트 수는6개를 유지하고 기존 Spectral 검사만 확장했다. status에 `invisibility`, `cloakOwned`, `aiDrops`가 추가됐다. `cloaked`는 시전 의도 상태이며 실제 효과 존재 여부는 `invisibility`로 구분한다.

## 중앙 서버 R1 실패 진단 및 fixture-r3 반환

중앙 `docs/qa/2026-10-28/w230/server-r1-report.xml`과 `server-r1.log`를 읽었다. 전체18개 중13개 통과, 헌터6개 중1개 통과/5개 실패다. 아직 이 수정본을 실행한 결과는 아니다.

체력 fixture의2000은26.3 `Attributes.MAX_HEALTH` 상한1024를 넘었다. merged jar의 `RangedAttribute` 생성 인자(기본20,최소1,최대1024)를 javap로 확인했다. 따라서 무피해 대상의 `getHealth()==2000` 기대는 잘못이며, R1의 네 체력 assertion 실패에서 실제 벽 관통을 단정할 수 없다. fixture를200으로 고치고 생성 직후 `getHealth()==getMaxHealth()==200`을 확인한다. 피해·보호 기대는 유지하며, 실패 시 실제 HP/최대HP/좌표/몸 충돌/eye ray/field 원점·거리·ray를 기록한다.

Gathering의 벽 뒤 대조군이 실제 필드 반경4블록 안에 있고 collider ray가 막히는지를 명시 검사한다. Storm 피격 대상은 벽 앞6.5블록 위치로 옮겨 안전 blink 이후 벽 뒤 대조군도 실제 회오리 반경4블록 안에 놓이게 한다. 피해를 받을 수 없는 바깥 대조군으로 LOS 통과를 주장하지 않는다. 단검이 통과하는1블록 슬릿에 실제 플레이어 몸이 통과하지 못해야 한다는 기대도 유지한다.

Spectral R1 로그는 표적 실제 값을 남기지 않아 유효 표적 필터/콜백 순서 중 어느 것이 원인인지 아직 확정하지 못했다. 26.3 `Mob.getTarget`는 `asValidTarget`을 통과한 view이며 보유한 raw target과 다를 수 있음을 javap로 확인했다. scoped aggro 정리는 `getTargetUnchecked()==owner`의 실제 보유 선택을 대상으로 한다. fixture는 표적 할당 직후 raw target이 실제 수락됐는지 먼저 확인하고, 두 틱 더 관찰한 뒤 owner target만 null/무관 target 유지가 됐는지 확인한다. 실패 로그에 raw/valid target UUID, canAttackOwner, invulnerable, 난이도, cloakOwned/aiDrops를 기록한다. 기대를 완화하거나 aggro 검사를 제거하지 않는다.

수정 파일은 소유 runtime/GameTest/이 문서3개다. worker Java25 parse-only 통과, 중앙 재실행·Vision은 master 대기다. 전체 검사 수는6개를 유지한다.


## R1d 실제 PNG 검수 및 visual-r4 반환

중앙 server-r2 헌터6/6 통과는 master가 확인했다. 이번 변경은 그 동결본의 시각 수정이며 기존 충돌·피해·LOS·슬릿·은신·cleanup GameTest6개와 수치 JSON은 그대로 유지한다. worker는 빌드·서버·게임을 실행하지 않았다.

실제 원본은 `/private/tmp/destiny-w230-native-r1d/frames`에서 읽었다. 검수표는 정지 PNG의 범위만 말하며 동영상의 보간 품질이나 음원 청취를 확인한 결과가 아니다.

| 궁극기 | 실제 원본 표본 | 판정과 조치 |
|---|---|---|
| 폭풍결집 | `gathering_storm-cast-sample-02/05/07.png`, `gathering_storm-embedded-after-lightning.png` | 02에서 전방 적 피격, 05/07에서도 시전자의 손에 지팡이가 남는다. 투척 시 matching presentation의 가상 손을 비우도록 수정한다. 식립 모델은 지면에 세로로 서 있으므로 변경하지 않는다. |
| 칼날 장전 | `blade_barrage-cast-sample-01/02/08/10/15.png` | 본인 팔과 SUPER CHARGED 배너가 보이며 3인칭 시전 rig를 검수할 수 없다. sequence의 cameraIsPlayer=false만으로 실제 그림이 정상이라고 판정하지 않는다. master에게 초기 준비 후 짧은 3인칭 재캡처를 요청한다. runtime 모션/시간을 추측 변경하지 않는다. |
| 스펙트럼 칼날 | `spectral_blades-cast-sample-05.png`, `spectral_blades-light-1-sample-03.png`, `spectral_blades-light-2-sample-03.png`, `spectral_blades-heavy-sample-04.png`, `spectral_blades-airloop-sample-04.png` | start의 쌍칼과 약공격 자세가 보인다. heavy/air 표본에는 본인 rig가 보이지 않으므로 모든 프레임의 손/공중 자세를 통과 판정하지 않는다. 은신 시각이나 PvP 렌더 범위를 확대 주장하지 않으며 이번 수정은 없다. |
| 폭풍의 칼날 | `storms_edge-cast-sample-03.png`, `storms_edge-throw-2-sample-06.png`, `storms_edge-throw-3-sample-09.png` | 첫/후속 동작과 피격 효과, 마지막 1인칭 복귀가 보인다. 후속 동작의 손 단검은 잔여 charge/회오리 구간과 구분할 정확한 시각 근거가 부족해 제거하지 않는다. 이번 수정은 없다. |

폭풍결집의 발사 후보는 원본 release event 해독값이 아니며 현재5틱을 유지한다. 비행 지팡이는 근거리 적에 바로 닿아 장축을 분리 판정할 수 없다. `SimProjectile`의 공통 -Z 방향과 staff의 +Y 장축은 소스상 검토 사항이지만 이번 원본으로 오류를 확정하지 않았으므로 공유 회전이나 모델을 변경하지 않는다. R2에서는 표적을 멀리 두고 비행 중 원본을 추가하면 확인할 수 있다.

최소 runtime delta는 `throwStaff()`의 `ClassAbilityEffects.releaseHand(owner,path)` 1회 호출이다. master 소유 공유 API는 player/path가 일치하는 presentation에만 released flag를 유지하고 BM virtual hands와 fallback prop를 cleanup까지 비운다. 빈 `superItem`은 실제 장비 매핑을 복구하므로 사용하지 않는다. 실제 인벤토리/기능 수치/발사·낙뢰·필드 수명/LOS는 변경하지 않는다. 공유 API 구현과 중앙 typecheck는 master가 담당한다.

R2 확인 항목: 투척 전 지팡이 표시 → 투척 후 손 소품 부재(시전 종료까지) → 지면 식립과 cast 종료 후 필드 유지 → cleanup 및 실제 장비 복귀. 칼날 장전 3인칭 실제 이미지와 지팡이 원거리 비행축은 별도 미확인으로 남긴다. visual-r4는 아직 실제 게임 재검증 전이다.
