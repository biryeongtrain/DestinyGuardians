# Guardian Rises — Fallen 런타임 (W300 fallen lane)

상태: 컴파일·단위 테스트 통과(오프라인). **인게임 미검증** — 실제 클라이언트에서의 모델 부착, 히트박스/정밀 판정,
텔레그래프 가독성, Walker 전투 흐름, 성능은 master의 Vision QA가 필요하다.

## 출처 구분 (provenance)

- 추출본(`/Users/qf/Downloads/Rising-Guardian-2026-11-01`)에는 Fallen/Walker **모델(FBX)만** 있고 애니메이션 클립·AI 규칙·수치·
  무기 VFX는 없다(README: "애니메이션 재생 클립은 이번 FBX에 포함하지 않았습니다").
- 따라서 이 문서와 `campaign/fallen/*`의 **모든 AI 행동, 수치(체력·피해·쿨다운·텔레그래프), 무기/사망/블링크 VFX, Walker 페이즈 설계와
  타이밍은 원작 참고 기반의 자체 저작(original authored)** 이다. DDC 대조 수치가 아니며 원작 확정값으로 표기하지 않는다.
- 사운드는 바닐라 SoundEvents를 임시 대체로 사용한다(추출 오디오 뱅크의 Fallen 효과음 매핑은 미조사).
- 모델/클립 이름은 계약(`RisingServices.Models`)을 따르며 실제 모델·클립은 w300-models 레인 산출물이다.

## 구성

| 파일 | 역할 |
| --- | --- |
| `RisingFallen` | `init()`: 엔티티 타입 6종 등록(Fabric registry + 기본 속성 + Polymer), 틱 이벤트, `RisingServices.register(Fallen)`. 서비스 `spawn/setActive`, 레벨당 활성 AI 예산(24) |
| `FallenMob` | `Monster + PolymerEntity`. 클라이언트에는 **항상 투명한 좀비**로 보이고 몸체는 BetterModel. 서버 AABB가 실제 피격 볼륨 |
| `FallenBrain` | 보병/생크 상태기계(목표·이동·엄폐·블링크·공격 텔레그래프) |
| `FallenArchetypes` | 종류별 자체 저작 수치(순수 데이터, 테스트 대상) |
| `FallenWeapons` | 시뮬레이션 투사체(엔티티 없음, 파티클 궤적), 근접, 폭발, 플레이어 피해 경로, VFX |
| `FallenModels` | BetterModel 트래커 부착·클립 상태기계·폴백 블록 디스플레이 |
| `WalkerBoss` | 순수 `Machine`(페이즈/풀/중복 제거) + `Runtime`(앵커·부위 엔티티·이동·포격) |

엔티티 ID: `destiny:rising_dreg`, `rising_vandal`, `rising_captain`, `rising_shank`, `rising_walker`, `rising_walker_part`.

### master 통합 요청 (소유 범위 밖)

1. `src/main/resources/data/destiny/tags/entity_type/weapon_precision_humanoids.json`에
   `"destiny:rising_dreg"`, `"destiny:rising_vandal"`, `"destiny:rising_captain"` 추가.
   `WeaponPrecision`은 이 태그의 타입에만 상단 25% 머리 치명타를 준다. 추가 전에는 Fallen 헤드샷이 일반 피해다.
2. `DestinyGuardians.onInitialize()`에서 `kim.biryeong.destiny.campaign.fallen.RisingFallen.init()` 호출(레지스트리 동결 전, 멱등).
3. 미션 중 보호막/체력 회복 정책은 Fallen 레인 밖이다(현재 비시련 플레이어는 바닐라 회복). 첫 미션 난이도 체감은 이 정책과 함께 확인 필요.

## 피격·피해 경로

- 플레이어 → Fallen: 기존 무기 시스템을 그대로 사용한다. `Combat.isEnemy`(Mob/Enemy) 통과, 히트스캔(`WeaponHitscan`)은 서버 AABB
  히스토리, 투사체/능력은 `Combat.damage` → `hurtServer`. 정밀 판정은 위 태그 추가 후 상단 25%.
  캡틴 보호막은 흡수량(absorption)으로 구현하므로 `WeaponPrecision` 규칙상 **보호막이 있는 동안 치명타 없음** → 보호막을 깨고 머리를
  노리는 판독 규칙이 된다(의도).
- 환경 피해(낙하·질식·익사 등 엔티티 없는 피해)는 Fallen을 죽이지 않는다(필수 적이 조용히 "처치"되는 것 방지). 공허 낙하는
  `discard()` → `lost()`. `/kill`(BYPASSES_INVULNERABILITY)은 처치로 처리된다.
- Fallen → 플레이어: `FallenWeapons.hurt`가 피해자 최대 체력의 비율로 native `hurtServer`를 호출한다. 흡수/오버실드, 사망, 
  `PlayerDamageMixin` → `IncomingDamageHud` 방향 표시가 그대로 적용된다. 피해 타입은 기존 `destiny:crucible`(scaling `never`)이라
  월드 난이도(peaceful/easy)에 따라 0/반감되지 않는다. 버스트 사이 무적 프레임(`damageCooldownTime`)은 0으로 둔다(Destiny식).
  공격자 엔티티가 원점이므로 피격 방향 HUD가 사수 위치를 가리킨다. 크리에이티브/관전자는 표적이 아니다.

## 종류별 행동 (자체 저작)

수치는 `FallenArchetypes` 기준, `Difficulty.FIRST_MISSION(health 1.0, damage 0.6, accuracy 0.55)` 적용 전 값.
피해는 "피해자 최대 체력 대비 비율".

| 종류 | 히트박스 w×h | 체력(+보호막) | 역할 | 주 공격 | 보조 |
| --- | --- | --- | --- | --- | --- |
| Dreg | 0.8×1.9 | 20 | 돌격: 지그재그 접근, 1.8 이내 정지 | 쇼크 블레이드 근접 24% (텔레그래프 9t, 정면 ±70°, 사거리 2.6) | 쇼크 피스톨 6%, 1.15 b/t |
| Vandal | 0.8×2.3 | 34 | 중거리 9–17 유지, 좌우 스트레이프, 엄폐 탐색, 압박 시 블링크(쿨 170t+) | 와이어 라이플 3연발 각 7.5% (텔레그래프 12t, 1.55 b/t, 간격 4t) | 근접 18% |
| Captain | 1.0×2.6 | 70 (+36 보호막, 5초 무피격 후 초당 20% 재생) | 6–13 유지, 느린 전진 | 쇼크 블라스트 구체 28% 범위 2.6 (텔레그래프 20t, 0.72 b/t) | 근접 22% |
| Shank | 0.9×0.9 비행 | 14 | 대상 주위 7–15 반경 선회, 발 높이+2.1~3.5 | 아크 4연발 각 4.5% (텔레그래프 10t, 1.2 b/t) | – |

- 모든 공격은 **무기 위치 충전 파티클(점점 수렴·밝아짐) + 사운드 + 애니메이션** 후에만 발사된다. 투사체는 엔티티 없는 서버 시뮬레이션
  점으로, 매 틱 파티클 궤적(아크=청색 선, 구체=큰 청백 구+전기 스파크+험, 포탄=주황 화염 궤적)을 남겨 보이고 피할 수 있다.
  블록에 막히고, 플레이어 AABB만 맞는다(아군 Fallen 오사 없음).
- 조준: 대상 가슴 + 이동 속도 × 비행시간 × 리드율(0.25+0.5·정확도), 정확도 원뿔(정확도 1 → 0.6°, 0.15 → 약 7°).
  스트레이프하는 플레이어는 회피 가능.
- 피격 반응: 피격 클립(8틱 스로틀) + BetterModel 데미지 틴트 + 에테르(옅은 청백) 파티클. 단발 피해 ≥ (체력+보호막)의 30% 또는
  보호막 파괴 시 경직(12/18틱, 공격 취소, `stagger` 클립). 보호막 피격/파괴/복구 각각 아크 셸 VFX·사운드.
- 블링크(반달): 1.5초 내 누적 피해 ≥ 22%이면 70% 확률로 측면 4–7블록, 서 있을 수 있고 대상과 시야가 트인 지점으로 순간 이동
  (양 끝 흰 잔상 + reverse portal + 사운드).
- 엄폐(반달): 90–160틱마다 또는 체력 55% 미만 시, 주변 3–9블록 10개 지점을 샘플링해 대상 눈높이에서 시야가 막히고 선호 거리 내인
  가장 가까운 지점으로 달려가 50–80틱 머문 뒤 다시 스트레이프.
- 사망: 즉시 `defeated()` 1회 → `death` 클립(HOLD_ON_LAST) 재생 동안 에테르 증발 파티클이 점점 강해지고 마지막에 구름/섬광 →
  클립 길이(20–80틱, 모델 없으면 24틱) 후 제거. 경험치·전리품 없음.
- 리시(leash): 홈에서 34블록 이상 벗어나면 홈 근처(8블록)로 복귀.

## 애니메이션 상태기계 (`FallenModels`)

- 기반 루프 레이어: idle / walk / run (생크 fly). 5틱 히스테리시스, **클립이 바뀔 때만** BetterModel 호출(`replace`로 교체) → 정지 상태에서 애니메이션 패킷 추가 없음.
- 1회 오버레이: spawn, shoot, melee, hit, stagger (Walker: fire, leg_break, stagger, recover). 끝나면 기반 레이어로 자연 복귀.
- 유지: Walker `weakpoint_open`(HOLD_ON_LAST, recover에서 해제), `death`(HOLD_ON_LAST).
- 액션→클립 이름 우선순위 표(`FallenModels.CLIPS`)로 생크(walk 없음→fly)와 Walker(shoot→fire) 차이를 흡수한다.
- 모델/클립 누락: 모델별 1회 경고 로그. 모델이 없으면 서버 히트박스는 그대로 두고 Polymer 블록 디스플레이 실루엣(몸통 + 정밀 머리 영역은 밝은 유리)을 붙인다. 클립 하나만 없으면 해당 동작만 생략.
- 클라이언트 기반 엔티티: `modifyRawTrackedData`로 공유 플래그에 투명 비트를 강제(서버 `isInvisible()`은 false 유지 → BetterModel
  `follow-mob-invisibility`가 모델을 숨기지 않음).

### 조명·판독성 (Vision r1 대응)

- r1에서 확인된 버그(트래커 부착 ClassCastException → 전부 폴백)는 master가 `ModEntity.of(mob)`로 수정했고 이 레인에 반영했다.
- 밝기 오버라이드: 이름이 `_glow`로 끝나는 본은 `brightness(15,15)`(발광). 나머지 본은 몸 높이(최대 2.5블록)의 실제 광량을 10틱마다 샘플링해
  `brightness(max(blockLight, 5), skyLight)`를 적용하고 값이 바뀔 때만 전송한다.
  - 하한 5 선택 이유: 조명 없는 방에서도 셰이딩이 남은 어두운 실루엣(바닐라 라이트맵 기준 약 1/3 밝기)으로 읽히되, 램프·발광 본보다 확실히
    어둡게 유지된다. 실외에서는 샘플링한 하늘 빛이 그대로 쓰여 주야 조명이 평탄해지지 않는다. 고정 (6,15)는 어두운 실내 적을 실외처럼
    밝히고 밤낮 차이를 지우므로 택하지 않았다.
- 공격 충전 글로우: 텔레그래프 동안만 `glowColor(아크색/주황)+glow(true)`를 `_glow` 본에(없으면 모델 전체) 켜고 발사/취소/경직/사망 시 끈다.
  글로우 외곽선은 벽 너머로 보이지만 공격은 사수가 시야를 확보했을 때만 시작하므로 노출은 자기 윈드업(7–30틱)으로 제한된다.
  **실제 가독성은 미검증** — 과하면 master 판단으로 끌 수 있다(`FallenModels.charge`).

## r3 수정 (master Vision r3 대응)

- **후퇴 버그:** 기존 이동은 스폰점 반경 13 안의 무작위 웨이포인트(플레이어 쪽 편향 4.5)라 스폰점이 플레이어에게서 ~35 m면 22 m까지
  다가왔다가 45–50 m로 멀어졌다(wk5.log: player 고정, d 22→50). 이제 아레나 반경 **8**, 웨이포인트는 `holdPoint`:
  중심에서 **플레이어 쪽으로** 2.5–5 m(플레이어와 12 m 이내로는 접근하지 않음) ± 측면 3 m. 중심보다 플레이어에게서 멀어지지 않고(테스트),
  선회로 플레이어를 정면에 둔다. 교전 거리는 마커 배치(플레이어 동선 15–30 m)가 결정한다.
- **피드백:** 바닐라 보스바 2개(72블록 이내 플레이어): 빨강 NOTCHED_10 "워커 — 코어 N / 230", 단계 바(노랑=다리 장갑 합계와 남은 비율,
  흰색=다리 파괴/경직, 빨강=약점 노출 남은 시간, 파랑=회복). 값이 보이게 바뀔 때만 패킷 전송. 다리 피격마다 금속 틱(3틱 스로틀),
  다리 파괴 시 폭발+충격파 링+이중 굉음. 단계 전환마다 INFO 로그
  `[Walker] phase=… legArmor=a/b core=c/d cycles=n pos=x,y,z`. (`walker` 앵커 체력 1000은 표시용이 아니며 변하지 않는 것이 정상.)
- **TTK 보정:** 실제 halfdan_d(high_impact 오토, 3.45/3틱, 탄창 33, 장전 44틱, 20.75 m까지 100%, 30 m 76%)로 시뮬레이션
  (다리 명중 55%, 약점 45%, 공백에 재장전). `Tuning.BASE` 다리 90→**150**, 코어 420→**230**: ≤22 m 평균 약 63–66 s, 노출 2–3회;
  30 m 약 95 s; 완벽 조준도 노출 2회(약 28 s). 스윕: `w300-evidence/fallen/r3/sweep/sweep.txt`, 결과: `r3/walker-ttk-halfdan.txt`
  (WalkerBossTest가 매 실행 갱신·강제).
- **Resistance IV 사망:** 원인은 Fallen 피해에 쓰던 `destiny:crucible` 타입이 `minecraft:bypasses_resistance`(+armor/enchantments)
  태그에 들어 있어 저항이 무시된 것. 새 타입 `destiny:fallen`(scaling never, message_id mob, 우회 태그 없음)으로 바꿔 저항·방어구·흡수가
  일반 몹 피해처럼 적용된다. 추가로 1회 요청 피해 상한 최대 체력 35%, 1초(20틱) 누적 요청 상한 55% → 완전 체력에서 한 방/한 연사로
  쓰러지지 않는다(완화 전 기준, 테스트). 사망 로그의 "by player"는 crucible의 message_id였다.

## r4 수정 (사용자 피드백: 보스바 제거, 고스트 안내, 적 머리 위 체력바)

- **바닐라 보스바 제거.** r3의 `WalkerBars`/`phaseLabel`/`phaseProgress` 삭제. QA INFO 로그(`[Walker] phase=…`)는 유지하고, 다리 파괴
  (Machine.hit 안에서 일어나 tick 전환으로 보이지 않던 것)와 처치(`phase=DEAD`)도 이제 로그에 남는다.
- **고스트 콜아웃** (`FallenCallouts`, 자체 저작 자막 전용 — 추출 음성에 해당 대사 없음. `subtitles_ko.json`에 `authored=true, voice=false`로
  5줄 추가, 기존 항목 불변):
  | 시점 | id | 문장 |
  | --- | --- | --- |
  | 전투 시작(첫 표적 획득) | `rg.walker.legs` | 다리를 노려요! 다리 장갑을 부숴야 해요. |
  | 다리 파괴(경직 포함) | `rg.walker.leg_broken` | 다리가 부서졌어요! 쓰러졌어요! |
  | 약점 노출 | `rg.walker.exposed` | 약점이 드러났어요! 주황색 코어를 쏴요! |
  | 회복 | `rg.walker.recover` | 다시 일어나요, 다리를 계속 공격해요! |
  | 처치 | `rg.walker.down` | 해냈어요! 워커가 쓰러졌어요! |
  사이클(Machine.cycles)마다 같은 줄 1회, 일반 줄은 80틱 쿨다운(쿨다운 중이면 버림, 큐에 쌓지 않음), 약점 노출·처치는 우선이라 쿨다운 무시.
  `RisingServices.presentation().voice(p, id)`로 같은 레벨 72블록 이내 전투 참가자에게만 보낸다(큐/자막은 presentation 담당).
  기존 음성 `80b75f7f "조심해요! 보행 탱크에요!"`는 디렉터가 등장 시 재생하므로 중복하지 않았다.
- **적 머리 위 체력바** (`FallenHealthBars` 렌더 + `HealthBarModel` 순수 로직):
  - 빌보드 Polymer TextDisplay 묶음(EntityAttachment). 이름(작은 글씨, 가운데 위) + 얇은 막대.
    막대는 단일 공백 텍스트 디스플레이의 배경색 사각형 3개(채움 | 흰색 최근 손실 | 어두운 빈칸)를 서로 겹치지 않게 이어 붙이고
    X 스케일로 폭을 정한다 → 글리프 틈 없는 연속 막대, 리소스팩 자산 불필요.
  - 색: 일반(드렉·반달·생크) 빨강 `E5463B`, 정예(캡틴) 주황 `F0913A` + 위쪽 별도 보호막 줄(하늘색), 보스(워커) 노랑 `F2D24B`, 폭 3블록.
    워커는 코어 비율이고, 장갑 단계 동안 아래에 다리 4개 핍(각자 채움, 파괴 시 비움)을 표시.
  - 흰 잔상: 피해 직후 12틱 유지 후 틱당 3.5%씩 실제 값까지 줄어듦.
  - 표시: 일반 적은 피해 후 5초(100틱) 또는 20 m 이내 플레이어가 조준 원뿔(9°) 안에 두고 시야가 트였을 때(5틱마다 검사).
    워커는 활성(전투 중)이고 살아 있는 동안 항상. 사망 즉시 사라짐.
  - 비용: 상태는 매 틱 폴링하지만 100단계로 양자화한 프레임/핍이 바뀔 때만 요소를 갱신(바뀐 값만 데이터 트래커로 전송).
    표시될 때만 홀더 생성, 숨김·사망·제거(onRemoval: 디스폰·인스턴스 종료·서버 종료) 시 파괴. 저장되지 않는 클라이언트 측 디스플레이뿐이라
    서버 재시작 후 잔여물 없음.
  - 높이: 일반 = 히트박스 높이 + 0.5, 워커 = 앵커 기준 6.6(선체 위). 모든 플레이어에게 동일하게 보임(소유자별 아님).
  - r5 크기 보정(Vision r4 hb_h.png: 흰 잔상 앞 틈): 26.3 `DisplayRenderer.TextDisplayRenderer.submitInner`를 javap로 확인 —
    `rotate(π,Y)·scale(-0.025)`, `translate(1-w/2, -h)`, `submitTextBackground(-1,-1,w,h)`, 공백 폭 4, h=9.
    공백 배경은 x∈[-0.05, +0.075]·sx, y∈[0, 0.25]·sy 블록(폭 0.125, 왼쪽 끝 = 이동점 - 0.4·폭, 바닥 = 이동점).
    r4는 폭을 0.15·가운데 기준으로 잡아 사각형마다 17% 좁고 중심이 어긋나 틈이 생겼다. 이제 `span()`으로 정확히 이어 붙인다(단위 테스트).
    크기: 일반 0.9×0.06, 캡틴 1.1×0.07, 워커 3.0×0.12 블록; 이름 한 줄(9 px) 높이 0.18블록(워커 0.24) → nameScale 0.8(워커 1.07).

## r7 스키프 증원 연출 (`SkiffDrop`, 자체 저작)

연출 전용이다. 스폰 타이밍은 `RisingEncounters.Run`이 그대로 결정하고, 연출 실패·예외는 스폰을 지연·취소하지 않는다.

- 신호: `RisingEncounters.Cues`에 기본 메서드 `incoming(index,total,wave,ticks)`(이전 웨이브가 처음 얇아진 순간, 리드
  `WAVE_DELAY`=30틱)와 `spawned(index,total,wave)`(웨이브 엔티티 생성 직후)를 추가. 둘 다 `presentation()`의 try/catch로 감싼다.
  `RisingMission.Host`의 `waveIncoming/waveSpawned`(기본 no-op) → `RisingCampaign.Session`이 `SkiffDrop.incoming/spawned` 호출.
- 선택(`Choice`, 순수): Gateway 제외, 첫 웨이브 제외(리드 없음), Walker 웨이브 제외, 생크 제외 지상 유닛 2기 이상.
  탑승자 = 가장 밀집한 지상 유닛 기준 10 m 이내(먼 마커·생크는 평소처럼 스폰). 런타임은 투하 지점 위가 하늘에 열려 있을 때만 띄운다.
- 타이밍(`Timing`, rg_skiff 클립 길이 기준): arrive 80틱을 리드에 맞춰 최대 3배속(리드 30 → 2.67배, 30틱 안에 종료),
  호버 높이 9, drop 52틱, 드롭 후 46틱 대기 후 depart 80틱 뒤 제거. drop 신호가 오지 않으면 240틱 후 스스로 떠난다.
- 드롭: 방금 생성된(tickCount≤2) 탑승 FallenMob을 위가 비어 있으면 5블록 띄워 짧게 낙하(FallenBrain 스폰 유예 안), 트랙터 입자.
  접근 방향은 가장 가까운 플레이어 → 투하 지점.
- 소리: 도착 `skiff_flyover`, 드롭 `skiff_enemy_spawner` (64 m). 폴백: BetterModel/rg_skiff가 없으면 경고 1회 후 입자 기둥+소리만.
- 정리: `RisingFallen`이 END_SERVER_TICK에 `tick`, 레벨 언로드 시 `clear(level)`, 서버 종료 시 `clearAll`.
- 테스트: `SkiffDropTest`(타이밍·선택·접근 방향), `RisingEncountersTest.skiffCuesLeadEachReinforcementWaveAndNeverBlockSpawns`
  (첫 웨이브 incoming 없음, 리드 30, 얇은 구간당 1회, 던지는 큐가 스폰을 막지 않음).
- 미검증(인게임): 스키프 모델 원점/높이/방향, 클립 배속 체감, 탑승자 낙하가 지형에 끼지 않는지, Breach 실내에서 하늘 판정이 맞는지,
  Dock 13 방어 웨이브의 실제 웨이브 구성으로 발동되는지, 소리 청취.

## r9 Dock 13 스키프 미표시 (master Vision ghost-r13 대응)

서버 로그상 웨이브 1·2 모두 HINT로 스키프가 생성됐는데 화면에 보이지 않았다. 원인(코드·로그·모델 근거, 실화면 미검증):

1. **선체 크기 무시:** r8 판정은 원점 주변 7×5×7만 확인했다. rg_skiff 실측(bbmodel 요소 x ±40 px, y −44.5~33 px, z −120~131.8 px)은 5×4.8×**15.7** 블록이다.
   Dock 힌트 높이(구역 로컬 y64/65)에서는 선체 앞뒤가 격납고 지붕 속에 묻힌다(아래 표 "old rule hull fits = false"). 지붕 위로 반쯤 나온 선체는 바닥에서 보이지 않는다.
2. **BetterModel sight-trace:** `config.yml sight-trace: true`이고 `TrackerModifier.DEFAULT`가 이를 따른다. 트래커의 애니메이션 패킷은 플레이어 시선이 원점 쪽 시야각(±45° 수직, ±80° 수평에 거리 보정) 안일 때만 전송된다.
   arrive 클립 첫 키프레임은 원점에서 앞으로 87.5블록, 위로 16블록이다. 시선이 다른 곳일 때 생성되면 선체가 그 먼 지점(지붕 밖)에 남을 수 있다(디바이드는 시선이 그쪽이라 보였다). 이 트래커만 `sightTrace(false)`로 생성한다.
3. **표시 시간:** lead 30틱에서 arrive는 2.67배속으로 30틱 안에 끝난다. 이어서 drop 후 46틱 뒤 출발, 80틱 뒤 제거되어 로그 시점부터 약 7.8초만 존재했다.
   로그상 동쪽 웨이브 판정은 03:40:48, 지붕 관찰 위치(14503,127,2282)로의 텔레포트는 03:41:40(52초 뒤)이라 그 프레임에는 이미 스키프가 없었다. 서쪽 웨이브 직후 시선 고정 `tp … facing` 명령은 03:40:39 인자 오류로 실패했다.
   이제 drop 후 110틱 대기한다(판정부터 제거까지 약 11초).

수정:
- `Sky.hullFits`: 선택된 방향의 16.5×5.5 선체 바닥 전체 아래까지 하늘이 열려 있어야 한다(높이맵, 블록 조회 없음). 방향은 접근 방향부터 ±45°, ±90°, ±135°, 180° 순서로 시도한다.
  힌트 마커 열은 유지하고 높이만 조정한다(힌트 높이 → 아래로 2씩 → 위로 2씩 +8까지). Dock 결과는 y64→66, y65→67.
- `Sky.approachClear`: arrive 클립 마지막 26 m 경로가 하늘 아래인 방향을 우선한다(지붕을 뚫고 나타나지 않게).
- 지켜보는 플레이어(가장 가까운 비관전자) 눈에서 선체(배·중심·상단 중 하나)가 보이는 지점을 우선한다. 없으면 탑승자만 보는 첫 지점(추가 조회 15,000 상한).
- 로그 추가 필드: `yaw`, `viewer`, `viewerSees`, `arrive`, `tracker viewers`.
- 비용: 선체 판정이 높이맵만 써서 번들 맵 최대 10,548 조회(r8 3,465–100,001).

Dock 13 오프라인 스캔(구역 로컬, 관찰자 = 함선 구역 QA 위치 / 관문 스폰):

| wave | encounter | viewer | hint | old rule (hint as-is) hull fits | result | hover | yaw | viewer sees | seen by riders | reads |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | dock_ship_west | ship bay (184.5,46,211.5) | 172.5, 64.0, 213.5 | false, viewer sees true | HINT | 172.5, 66.0, 213.5 | 82 | true | 4 | 87 |
| 1 | dock_ship_west | spawn (215.5,45,185.5) | 172.5, 64.0, 213.5 | false, viewer sees false | HINT | 172.5, 66.0, 213.5 | 57 | false | 4 | 7172 |
| 2 | dock_ship_east | ship bay (184.5,46,211.5) | 181.5, 65.0, 222.5 | false, viewer sees true | HINT | 181.5, 67.0, 222.5 | 6 | true | 5 | 110 |
| 2 | dock_ship_east | spawn (215.5,45,185.5) | 181.5, 65.0, 222.5 | false, viewer sees false | HINT | 181.5, 67.0, 222.5 | 41 | false | 5 | 7806 |

관문 스폰에서는 두 웨이브 모두 격납고 벽에 가려 보이지 않는다. 함선 구역(웨이브가 실제로 싸우는 바닥)에서는 둘 다 보인다.

전 구역 재스캔:

| zone | wave | encounter | size | eligible | riders | drop centroid (zone-local) | sky directly above | result | hover (zone-local) | offset m | seen by | unique block reads |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BREACH | 0 | breach_first | 4 | false | 3 | 129.8, 24.0, 154.5 | roofed | - | - | - | - | 0 |
| BREACH | 1 | breach_far | 3 | true | 3 | 197.5, 23.0, 173.5 | roofed | OFFSET | 199.5, 53.0, 189.5 | 16.1 | 1 | 994 |
| BREACH | 2 | breach_chest | 2 | true | 2 | 198.0, 23.0, 98.5 | roofed | OFFSET | 198.5, 30.0, 120.5 | 22.0 | 2 | 254 |
| BREACH | 3 | breach_corridor | 6 | true | 3 | 143.8, 20.0, 79.5 | roofed | SKIP (no visible sky in 40 m / budget) | - | - | - | 367 |
| BREACH | 4 | breach_garage | 8 | true | 4 | 78.0, 15.0, 70.0 | roofed | SKIP (no visible sky in 40 m / budget) | - | - | - | 10548 |
| DIVIDE | 0 | divide_lure | 8 | false | 2 | 255.5, 46.0, 222.0 | open | - | - | - | - | 0 |
| DIVIDE | 1 | divide_reinforce | 4 | true | 4 | 288.5, 45.0, 247.3 | open | DIRECT | 288.5, 54.0, 247.5 | 0.0 | 4 | 25 |
| DIVIDE | 2 | divide_walker | 1 | false | 0 | 287.5, 45.0, 244.5 | open | - | - | - | - | 0 |
| DOCK13 | 0 | dock_defense | 5 | false | 2 | 227.0, 45.0, 192.5 | roofed | - | - | - | - | 0 |
| DOCK13 | 1 | dock_ship_west | 4 | true | 4 | 172.8, 46.0, 213.3 | open | HINT | 172.5, 66.0, 213.5 | 0.4 | 4 | 60 |
| DOCK13 | 2 | dock_ship_east | 5 | true | 5 | 183.3, 47.0, 222.1 | open | HINT | 181.5, 67.0, 222.5 | 1.8 | 5 | 83 |

Breach 4(garage)는 이제 건너뛴다. r8의 15.9 m 오프셋 지점은 16블록 선체가 들어갈 하늘이 아니었다(같은 "지붕에 묻힌 스키프" 결함). Breach 1·2는 유지된다.

## r8 스키프 하늘 탐색 (master Vision r7: 스키프 미출현 대응)

원인: r7은 투하 지점 바로 위 `canSeeSky`만 확인했다. Breach는 실내, Dock 13은 지붕 있는 격납고라 모든 웨이브가 조용히 건너뛰어졌고
(인스턴스 차원은 하늘빛이 없어 `canSeeSky`는 늘 false일 수 있음), Dock 13은 웨이브가 1개(`dock_defense`, index 0)라 "첫 웨이브 제외"에도 걸렸다.

- **로그:** 웨이브당 1회 INFO `[skiff] ZONE wave N (encounter): eligible=… riders=… ground=… sky=DIRECT|OFFSET|HINT|none hover=… offset=… seenBy=… lead=… search=…us/…reads fallback=…`.
  같은 웨이브는 400틱 안에 다시 판정하지 않는다(체크포인트 재시도는 다시 기록).
- **하늘 판정(`Sky`, 순수):** 충돌 박스 기준 블록과 MOTION_BLOCKING 높이맵으로 판정(하늘빛 불필요). 선체 7×5×7 비어 있음 + 선체 중심 위로 하늘.
  순서: ① `prop.skiff_<encounter>` 마커 힌트 ② 투하 중심 바로 위(높이 9,7,11,5,…,30) ③ 지상 유닛(탑승자 우선, 최대 8명) 중 가장 가까운 유닛 기준
  24 m, 이어 40 m 이내 열을 거리순으로, 지상 유닛 눈높이 중 하나에서 선체 배까지 시야가 트인 첫 지점. 블록 조회 60,000회 상한(초과 시 건너뜀).
- **오프셋 연출:** 바로 위가 아니면 탑승자를 띄우지 않고, 스키프 배에서 그 자리에 스폰된 지상 유닛까지 트랙터 빔(스키프에서 보이는 유닛만, 나머지는 소환 입자만).
- **Dock 13:** 방어전 웨이브가 하나뿐이라 공격대 자체가 스키프로 도착하도록 index 0 허용(`Choice.openingByShip`). 리드 없이 스폰 순간 도착(0틱 → 3배속 arrive).
- 테스트: `SkiffDropTest`(가상 격자: 개활지 DIRECT, 지붕 구멍 OFFSET, 벽 뒤 구멍 배제/전부 가려지면 건너뜀, 완전 지붕·암반 예산, 힌트 우선/막힌 힌트 무시, 결정성, Dock 첫 웨이브),
  `SkiffZoneScanTest`(번들 zone/markers를 map lane 로더로 읽어 아래 표 생성, Breach·Dock·Divide 각각 최소 1회 스키프 단언).

오프라인 스캔(구역 로컬 좌표, 충돌은 팔레트 이름 근사):

| zone | wave | encounter | size | eligible | riders | drop centroid (zone-local) | sky directly above | result | hover (zone-local) | offset m | seen by | unique block reads |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BREACH | 0 | breach_first | 4 | false | 3 | 129.8, 24.0, 154.5 | roofed | - | - | - | - | 0 |
| BREACH | 1 | breach_far | 3 | true | 3 | 197.5, 23.0, 173.5 | roofed | OFFSET | 199.5, 30.0, 184.5 | 11.2 | 3 | 2463 |
| BREACH | 2 | breach_chest | 2 | true | 2 | 198.0, 23.0, 98.5 | roofed | OFFSET | 196.5, 28.0, 112.5 | 14.1 | 1 | 1485 |
| BREACH | 3 | breach_corridor | 6 | true | 3 | 143.8, 20.0, 79.5 | roofed | SKIP (no visible sky in 40 m / budget) | - | - | - | 3465 |
| BREACH | 4 | breach_garage | 8 | true | 4 | 78.0, 15.0, 70.0 | roofed | OFFSET | 78.5, 24.0, 65.5 | 4.5 | 6 | 1978 |
| DIVIDE | 0 | divide_lure | 8 | false | 2 | 255.5, 46.0, 222.0 | open | - | - | - | - | 0 |
| DIVIDE | 1 | divide_reinforce | 4 | true | 4 | 288.5, 45.0, 247.3 | open | DIRECT | 288.5, 54.0, 247.5 | 0.0 | 4 | 270 |
| DIVIDE | 2 | divide_walker | 1 | false | 0 | 287.5, 45.0, 244.5 | open | - | - | - | - | 0 |
| DOCK13 | 0 | dock_defense | 7 | true | 3 | 227.5, 45.0, 193.2 | roofed | OFFSET | 182.5, 52.0, 202.5 | 46.0 | 1 | 2586 |

- Breach 3(복도) 건너뜀: 40 m 안에 탑승자가 볼 수 있는 하늘이 없다(조회 3,465회, 예산 아님).
- 계획 문서의 "Graveyard 증원"은 Divide(`graveyard_public`)의 `divide_reinforce`(index 1)이다 — 개활지 DIRECT.
- Dock 13: 동쪽 3인조(226–228,193)는 격납고 동벽 안쪽이라 앞마당이 보이지 않는다. 서쪽 반달(202.5,182.5)이 함선 구역 지붕 구멍 쪽 (182.5,52,202.5)을 본다.
  빔은 그 유닛에게만, 나머지는 소환 입자. master에게 맵 데이터 제안(아래, 이 레인은 맵 파일을 수정하지 않음).

### master/map lane 제안 (맵 데이터, 미적용)

1. `dock_defense`를 `order` 1/2/3으로 나눠 실제 증원 웨이브를 만들기(감독 대사 7a·52·74가 웨이브 3개 이상을 전제). 2·3웨이브를 함선 구역(지붕 구멍 아래, prop.ship 주변)에 두면 DIRECT 투하가 된다.
2. 원하는 고정 위치가 있으면 `prop.skiff_dock_defense`(예: 구역 로컬 182.5, 52, 202.5) 또는 `prop.skiff_breach_corridor` 마커. `prop.*`는 이미 id 문법을 통과한다.

## Walker (`WalkerBoss`)

한 개의 보스 상태(`Machine`)와 AI 없는 부위 엔티티 6개(다리 4, 약점 1, 선체 1). 부위는 클라이언트에 전송하지 않는 서버 전용 충돌 볼륨으로
앵커 기준 레이아웃(`WalkerBoss.LAYOUT`)에 매 틱 배치된다. 수백 개 AI 엔티티 없음.

페이즈(틱): `ARMORED` → (임의 다리 장갑 0) `LEG_BREAK` 24 → `STAGGER` 22 → `EXPOSED` 170 → `RECOVER` 38 → `ARMORED`.

| 풀 | 값 (×Difficulty.health) | 규칙 |
| --- | --- | --- |
| 다리 장갑 | 150 × 4 (r3) | ARMORED에서만 피해. 파괴된 다리는 RECOVER 후 60%로 복구, 나머지는 유지 |
| 코어 | 230 (r3) | EXPOSED 동안 약점 피격만 ×1.5 적용, 0이면 처치 |
| 선체/앵커 | – | 항상 튕김(스파크 + 금속음) |

- 샷 중복 제거: (공격자 ID, 직접 엔티티 ID, 서버 틱) 키당 **첫 유효 적중만** 반영. 튕긴 적중은 키를 소모하지 않음(폭발이 선체를 먼저 스쳐도
  다리에 반영). 키는 2틱 후 만료.
- 부위 엔티티는 큰 체력 풀(1000)을 가지며 받은 "실제 반영량"만큼만 피해를 받아 히트마커/데미지 숫자가 보이고, 다음 틱에 복구된다.
- 공격(ARMORED에서만): 주포 — 30틱 충전(포구 주황 충전 + 소닉 차지음) 동안 대상의 현재 발밑에 **지면 경고 링**, 포물선 포탄(약 0.9 b/t)
  착탄 시 반경 3.4 폭발 42%(거리 감쇠, 시야 차단 시 무효), 쿨 110–140틱. 대인 포 — 10틱 텔레그래프 후 아크 5연발 각 7%, 쿨 50–70틱.
- 이동(r3): 스폰 지점(=마커) 중심 반경 8 안, 플레이어 쪽 hold point로 보행(0.055 b/t, 22틱마다 쿵 소리), 충돌 시 정지.
  대상 쪽으로 2.4°/틱(충전 중 1.2°/틱) 회전. 높이는 스폰 높이 고정(평지 아레나 가정).
- 다리 파괴: 폭발·용암·연기 + 금속 굉음, 진행 중 포격 취소. EXPOSED: 약점 주황 발광 파티클, 종료 1.5초 전 경고음. 처치: 큰 폭발 → `death`
  클립 동안 연쇄 폭발(최소 60틱) → 제거.
- 일반탄만으로 완료 가능(단위 테스트 + 시뮬레이션). 순수 상태기계 시뮬(Walker의 공격/이동 무시, 적중률 가정):

```
auto_rifle 65%   ≈ 46 s (2 사이클)     auto_rifle 100% ≈ 28 s (1 사이클)
hand_cannon 60%  ≈ 75 s (3 사이클)     shotgun 50%     ≈ 76–95 s
```
(`w300-evidence/fallen/sim/walker-sim.txt`). 실제 체감 시간은 이동·엄폐·포격 회피가 더해져 길어진다.

## 서비스 계약 동작

- `spawn(level, kind, pos, yaw, tuning, listener)`: 엔티티 생성·구성 후 `addFreshEntity`(실패 시 예외). 생크는 pos+2.5 높이.
  Walker는 앵커를 반환하고 부위를 함께 생성. 기본 활성.
- `setActive(entity, false)`: AI 정지(이동/공격/회전 없음, idle). 정지 상태 피격 시 hit 클립만 재생하고 블링크/경직/어그로 없음.
- 활성 AI 예산: 레벨당 24(Walker 앵커 1 포함, 부위 제외). 초과 요청은 대기열에서 슬롯이 비면 활성화.
- `defeated()`는 처치 시 정확히 1회(사망 즉시). `lost()`는 처치 없이 제거될 때 1회(discard, 공허, 청크 언로드, 서버 종료).
  엔티티는 저장되지 않는다(`shouldBeSaved=false`) → 재시작 후 유령 적 없음.
- `/summon destiny:rising_vandal` 등은 FIRST_MISSION 수치·리스너 없이 동작(QA용). `rising_walker_part` 단독 소환은 즉시 제거.

## 성능

- 목표 탐색 20틱마다 레벨 플레이어 목록만 순회, 경로 갱신 ≤10틱, 엄폐 샘플링은 필요 시 10점, LOS는 바닐라 Sensing 캐시.
- 투사체는 엔티티가 아닌 리스트(서버 전체 최대 384), 틱당 블록 레이캐스트 1회 + 근처 플레이어 AABB 검사.
- BetterModel 호출은 클립 변경 시에만.

## 테스트 (오프라인)

`./gradlew test --tests 'kim.biryeong.destiny.campaign.fallen.*'` — `FallenArchetypesTest` 10, `WalkerBossTest` 9 통과.
아키타입 무결성(모델/클립 계약, 액션→클립 해석), 체력 순서·자동소총 처치 시간, 텔레그래프/투사체 속도 가독성, 단일 적 초당 피해 상한,
난이도 스케일/NaN 방어, 정밀 머리 영역 크기, Walker 페이즈/게이팅/중복 제거/종료성/소프트락 없음/일반탄 완료.

## 미검증 — master 인게임 확인 항목

1. 모델 부착: rg_dreg/vandal/captain/shank/walker가 실제 엔티티를 따라가고 기반 좀비가 보이지 않는지(투명 플래그 강제 + BetterModel 숨김).
   모델 원점·스케일과 서버 히트박스(위 표) 정렬, 특히 Walker 다리/약점 레이아웃(`WalkerBoss.LAYOUT`)과 모델 본 `leg_*`/`weakpoint` 위치.
2. 헤드샷: 태그 추가 후 머리 치명타 숫자, 캡틴 보호막 중 치명타 없음.
3. 클립 전환: idle/walk/run 깜박임 없음, shoot/melee가 텔레그래프와 맞는지, death 홀드 후 제거, Walker weakpoint_open 유지/recover 해제.
4. 텔레그래프 가독성(1·3인칭, 어두운 Breach 조명), 투사체 회피 가능성, 피격 방향 HUD, 플레이어 사망/보호막.
5. 반달 엄폐/블링크가 Breach 지형에서 벽 속으로 들어가지 않는지, 생크 비행이 천장/벽에 끼지 않는지.
6. Walker 전 사이클(다리→경직→약점→회복) 및 일반탄 단독 완료, 포탄 지면 경고, 아레나 이탈 없음.
7. 24개 활성 + Walker에서 TPS/FPS, 모델 패킷량.
8. `defeated`/`lost` 콜백이 디렉터 카운터와 정확히 맞는지(처치·공허·인스턴스 종료).

## 알려진 한계

- 특수/중화기 탄약 보너스 없음: 몹 대상 피해원은 탄약 종류를 싣지 않아(`GuardianDamageSource`는 플레이어 대상 전용) Walker에서 특수탄 우대를
  구현하지 않았다. 샷건은 근거리 약점에서 유리하지만 수치상 보정 없음.
- Walker 부위 위치는 고정 레이아웃(본 실시간 추적 아님). 걷기 애니메이션의 다리 흔들림과 최대 ~0.5블록 어긋날 수 있다.
- Walker는 지형 높이를 따라가지 않는다(평지 아레나 전제). 폴백 실루엣은 Walker 회전을 반영하지 않는다.
- 사운드는 바닐라 대체음.
- 엔티티 없는 피해원(일부 지속/환경 피해)은 Fallen에 들어가지 않는다.
