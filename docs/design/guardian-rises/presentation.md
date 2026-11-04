# Guardian Rises — 연출 레인 (W300 presentation)

작성 2026-11-01 · 상태: 구현 + 오프라인 검사 완료, **인게임 Vision·청취 미검증**
범위: `RisingServices.Presentation` 구현(오프닝 스캔, 고스트 동행, 출항), 음성·자막, 포스트 효과, 효과음.
계약: `campaign/RisingServices.java`(master 소유, 무변경). 등록: `RisingPresentation.init()` — master가 모드 초기화에서 호출.

## 출처 구분 (중요)

| 항목 | 출처 |
|---|---|
| 고스트 한국어 음성 37줄 | 추출본 `audio/voice_ko/*.wav` 원본 길이 그대로, mono 48 kHz Vorbis, W280과 같은 `loudnorm=I=-19:TP=-2:LRA=7` |
| 자막 37줄 | 추출본 `dialogue-ko.csv`의 `korean` 열 **원문 그대로** (`subtitles_ko.json`, 원본/출력 SHA-256 기록) |
| 오프닝 자막 2줄 `rg.opening.found` "…찾았어요. 드디어.", `rg.opening.scan` "움직이지 마세요. 당신의 빛을 되돌려 놓을게요." | **W300 창작 자막 전용** (`authored=true, voice=false`). 추출본에 부활 첫마디가 없다(README·VALIDATION `not_verified`). 음성을 만들거나 다른 대사로 위장하지 않았다 |
| 효과음 6종 scan_loop / revive / ship_power / ship_takeoff / transmat / ambient_cosmodrome | **창작 합성음** (`scripts/campaign/rising_audio.py`, 고정 시드). 추출본 `audio_banks/`, `music-banks.json`이 비어 있어 원본 효과음 없음 |
| 심장 박동 | 바닐라 `entity.warden.heartbeat` (pitch 0.82) |
| 오프닝·스캔·출항 타이밍, 카메라, 빛 부채꼴, 포스트 셰이더 `rg_scan`/`rg_revive` | **창작 연출**. 추출본에 오프닝 영상·애니메이션·VFX·이륙 카메라 없음 |
| 고스트/우주선 모델·클립 | w300-models 레인 `rg_ghost`, `rg_ship` (BetterModel). 없으면 고스트는 기존 튜토리얼 Generalist Shell 표시로 대체, 우주선은 입자만 |

제외 대사: 쇼 한 결말 제거(사용자 확정)로 `80b75f70`, `80b75f73`(쇼 한), `80b75f6c`, `80b75f6a`, `80b75f69`(쇼 한 무전 반응) 미사용. `80b75f68`, `80b75f6d`는 원본 1바이트 무효 → 미포함, 대체 없음.

## 오프닝 (openingScan) — 타임라인 (tick)

| t | 화면 | 소리/자막 |
|---|---|---|
| 0 | `blackout`(시안 광원만 통과) + 실명 안개 + HUD 숨김 + 이동 잠금, 시선은 위로(누운 낮은 각도) | 심장 박동 시작(60 bpm, 셰이더 박동과 같은 위상) |
| 16 | 고스트 전송 등장 — 어둠 속 눈의 빛 하나(키 + 후광) | transmat |
| 28 |  | [창작 자막] …찾았어요. 드디어. |
| 40 | 껍질 열림 `shell_open` |  |
| 52–148 | `scan`: 차갑게 눌린 장면 + 화면 스윕 밴드 + 주사선 + 박동 가장자리 광; 몸을 머리→발 빛 부채꼴(블록 디스플레이 4선 + 점 입자)으로 1초 주기 스윕 | scan_loop ×2, [창작 자막] 움직이지 마세요… |
| 148 | 다시 어둠, 부활음 상승 | revive |
| 184 | `revive` 블룸(따뜻한 흰빛 + 광선), 실명 해제, 시선이 낮은 각도에서 고스트 눈높이로 30 tick 이징 |  |
| 198–200 | 정상 장면, HUD 복귀 | 환경음 루프, 80b75f5c "당신의 빛은 강해요, 수호자." |
| 214 | 이동 반환, `done` | 직업 대사 54/56/58 → 후속 53/59/5e 큐 대기 (직업 없음이면 생략) |

탑 출발 전 Gateway 이동 시작에는 80b75f7c(우주선이 필요해요) → 80b75f7d(무기부터)를 디렉터가 재생하는 것을 권장한다.

## 고스트 동행 (GhostCompanion)

- 소유자 전용 BetterModel `rg_ghost` DummyTracker. 클립 idle(상시)/speak(대사 중)/scan/shell_open/shell_close/transmat/look.
- 따라다니기: 시야 오른쪽 위 약 40°, 0.8 앞, 눈높이 +0.38 — 화면 중앙을 피한다. ADS(`WeaponAiming.progress>0.05`) 중에는 오른쪽 어깨 뒤로 빠져 조준 화면에서 사라진다.
- 대사 중에는 플레이어 눈을 보고, 평소에는 플레이어 시선 방향을 본다.
- `ghostScan(target)`: 대상과 플레이어 사이로 날아가 1.4×2.0 영역을 위→아래 스윕, 대상 위치에서 scan_loop. 이동 잠금 없음.
- 캠페인 월드(`destiny:guardian_rises/*`)에서 `voice()`를 부르면 고스트가 없을 때 생성한다. 캠페인 밖으로 월드 이동 시 제거.

## 출항 (departure)

0 고스트가 선체를 좌→우 스윕(2.8 s) · 56 `power_up` + ship_power + 엔진 광입자 · 100 고스트 transmat, revive 섬광 아래에서 HUD 숨김·플레이어를 선체 옆 낮은 광각 지점으로 이동(카메라 역할, 조기 종료 시 원위치) · 116 `takeoff` + ship_takeoff, 상승 후 전방 가속, 시선이 매 tick 절반씩 추적 · 206 `ship_flash` · 212 `fade` 검정 → `done`. 검정은 `close()`까지 유지(디렉터가 탑으로 이동 후 close).

우주선은 이 장면 전용 소유자 비공개 `rg_ship` 트래커를 shipPos/shipYaw에 새로 띄운다. **구역에 정적 우주선 소품이 있다면 출항 전에 디렉터가 숨겨야 겹치지 않는다.**

## 음성 큐 (voice)

- `voice(player, id)` 반환값 = 그 줄이 **끝날 때까지의 tick**(대기 포함). 미등록 id는 0(경고 1회).
- 줄 사이 6 tick 숨. 현재 줄은 끊지 않고, 대기 3줄 초과 시 가장 오래된 대기 줄을 버린다(긴 음성 누적 방지). 같은 id는 중복 대기하지 않는다.
- 음성은 플레이어에 붙은 엔티티 사운드라 질주·텔레포트에도 따라온다. 자막: 평상시 하단 중앙 카드(DisplayHud, 크루시블 배너 스프라이트), 시네마틱(HUD 숨김) 중에는 액션바 — GUI라 포스트 효과에 가려지지 않는다.

## 카메라·잠금 — 클라이언트 모드 없음

- 서버 주도 카메라(`minigame-lib` CameraViews)는 실제 엔티티만 다시 동기화하고 BetterModel/Polymer 패킷을 막으므로 고스트·우주선이 사라진다. 그래서 **플레이어 자신의 시점**을 쓴다.
- 잠금: 이동속도·점프 −100% 일시 수정자 + 앵커 위치 고정(0.3 이상 벗어나면 되돌림) + 낙하 거리 초기화.
- HUD 숨김: 그 클라이언트에만 관전자 모드 이벤트 + 비행/보행 속도 0 능력 패킷을 보낸다(서버 게임모드는 그대로). 핫바·손·조준점이 사라지고 아이템 사용도 막힌다. 서버측 mayfly를 잠시 켜 비행 킥을 막고, 10 tick마다 재전송한다. `HIDE_HUD=false`로 끌 수 있다.
- 시선 제어는 `ClientboundPlayerRotationPacket`(20 Hz 계단). 오프닝 이징과 출항 추적에만 쓴다.
- 해제는 장면 종료·조기 close·사망·접속 종료·서버 정지에서 정확히 1회: 수정자 제거, mayfly 원복, 실제 게임모드/능력 재전송, 위치 재동기화, 소유 포스트 효과·실명 제거.

## 포스트 효과 (26.3 post_effect JSON, 코덱 파싱 테스트 통과)

| id | 셰이더 | 용도 |
|---|---|---|
| guardian_rises/blackout | rg_scan, 노출 0 | 완전 암흑, 채도 높은 시안(고스트 눈·빛)만 + 후광, 가장자리 심장 박동 |
| guardian_rises/scan | rg_scan | 차갑게 눌린 장면, 스윕 밴드, 주사선, 박동 |
| guardian_rises/revive | rg_revive | 따뜻한 흰빛 블룸 + 광선 |
| guardian_rises/ship_flash | rg_revive | 거의 흰 도약 섬광 |
| guardian_rises/fade | minecraft:post/blit ×0 | 검정 |

애니메이션은 바닐라 `Globals.GameTime`만 사용한다(서버 uniform 전송 없음). **주의:** `GuardianRisesInstances`가 `setShouldTickTime(false)`라 인스턴스 레벨 gameTime이 멈춘다. 클라이언트는 20 tick마다 멈춘 값으로 재동기화되므로 셰이더 주기를 모두 1초(20 tick)로 맞춰 끊김 없이 돌게 했고, 서버측 스윕/박동은 같은 추정(`clientTime`)을 쓴다. 다만 멈춘 gameTime은 상태이상·쿨다운 등 getGameTime 기반 게임플레이 15개 파일에도 영향을 주므로 master에게 `setShouldTickTime(true)` 검토를 요청했다.
블랙아웃 키는 실명 안개 아래에서 설계했다: 밝은 낮 하늘(옅은 파랑)은 채도 키를 대부분 통과하지 못하지만 일부 남을 수 있어 오프닝은 항상 실명과 함께 쓴다.

## 오프라인 검사 (이 레인에서 수행)

- `./gradlew compileJava` 성공.
- `RisingSubtitlesTest` 4건: 음성 37줄(자막·ogg·sounds.json 연결), 창작 2줄 표기, 쇼 한 제외, 효과음 이벤트, 자막 줄바꿈, 포스트 JSON 5종 실제 `PostChainConfig.CODEC` 파싱 + 셰이더 uniform 블록 선언. `PostEffectCodecW179Test` 회귀 통과.
- `glslangValidator -S frag`(globals 인클루드 전개) rg_scan/rg_revive 통과 — 실제 GPU/드라이버 컴파일은 아님.
- 오디오: 37줄 원본 SHA-256 대조, 디코드 검사, 재실행 바이트 동일(결정성), sounds.json 기존 항목 바이트 동일·끝에만 추가.
- CPU 에뮬레이션 미리보기(근사, GPU 결과 아님): 증거 폴더 `preview-contact.png`.

## 인게임에서 master가 확인할 것 (미검증)

1. 오프닝 전체: 암흑 속 눈빛 가시성, 스캔 부채꼴 가독성, 밴드/박동 애니메이션(멈춘 gameTime 포함), 블룸 강도, 시선 이징 계단감, 자막 위치(액션바/카드), 이동 잠금·HUD 숨김(관전자 위장)과 해제 후 게임모드·능력·손 복귀, 비행 킥 없음.
2. 조기 종료: 오프닝·출항 중 접속 종료/사망/close 각 1회 → 포스트·실명·잠금·위치·고스트 원복.
3. `rg_ghost`/`rg_ship` 실제 모델의 방향(yaw 규약)·크기·클립 이름 일치, 대체 고스트 경로.
4. 동행 고스트가 화면 중앙·ADS 조준을 가리지 않는지, 10~20 tick 이동 시 끊김.
5. 실제 청취: 음성 음량(-19 LUFS) 대비 효과음(-15.5~-24 LUFS), 합성 효과음 품질, 심장 박동과 화면 박동 동기, 환경음 루프 이음매.
6. 출항: 관점 지점이 지형 안에 끼지 않는지, 우주선 추적 프레이밍, 검정 유지 후 탑 이동→close.

## r2 (2026-11-01, master Vision r2 반영) — 인게임 재검증 필요

| 문제 (Vision 근거) | 수정 |
|---|---|
| 출항 중 무기·핫바·HUD 노출 (dep/grid, d01) | `Departure.begin`에서 `lock.hideHud(true)` + 전투 HUD 제거. 고스트는 스캔/정지 지점에만 있고 transmat 후 숨김 |
| 오프닝·출항 중 커스텀 HUD(좌하단 능력/궁극기, 상단 중앙 체력 바) 노출 (open/o008) | 관전자 위장은 서버 `isSpectator()`를 바꾸지 않아 `CombatHud`가 계속 그렸다. `CombatHud.cinematic` 술어(1줄 + 조건 1개, **hud 레인 파일**)를 추가하고 `RisingPresentation.hudHidden`을 연결. `RisingObjectives.render`도 같은 조건으로 숨김(**디렉터 레인 파일, 조건 1개**) |
| 오프닝 회색 픽셀 덩어리 (o008 우·하단) | 자기 몸 스캔 시 스윕선이 카메라를 통과해 입자(흰 END_ROD는 블랙아웃 키에서 회색)가 화면 가득 커졌다. 눈 반경 2블록 안 입자 금지, END_ROD 제거, 채도 높은 시안 dust만. 자기 스캔이면 가로 빔(블록 디스플레이)도 숨김 |
| 오프닝 종료 급변 | 200 대사 시작(HUD 숨긴 채) → 212부터 고스트가 30tick 동안 천천히 어깨 위치로 → 240 바닐라 HUD → 254 전투 HUD → 246 이동 반환·done |
| 탑 도착 급변/로딩 화면 | 출항 검정(212)에서 도착 대기 등록. `stopAll`은 이때 FADE를 유지하고, 26.3 `ServerPlayer`는 차원 이동 후 포스트 효과 목록을 재전송한다. `AFTER_PLAYER_CHANGE_LEVEL`(캠페인 밖)에서 `Curtain` 시작: 검정 30tick 유지 → 5단계 페이드 30tick, 중간에 창작 자막 `rg.arrival.tower` "도착했어요, 수호자. 여기가 탑이에요."(음성 없음). 탑 이동이 30초 넘게 실패하면 검정을 풀어 준다. 클라이언트 "지형 불러오는 중" 화면은 서버가 막을 수 없고 검정 위에서 열리고 닫힌다 |
| 13번 부두 우주선 없음 | 계약 추가 `Presentation.shipProp(player, pos, yaw)` → `ShipProp`: 소유자 전용 `rg_ship`, 밝기 하한 13(빛 부품 15), idle, `engine_*_glow` 부품 끔(`togglePart(false)`), 크기 ×1.35. `RisingMission`: DOCK13 구역 도착부터 SHIP_DEFENSE, DEPARTURE 연출 시작 직전까지 유지; departure가 같은 트래커를 인수(위치 재설정, 엔진 점등) → 두 척 동시 표시 없음. pause/사망/스킵/close/retire에서 닫힘 |
| 우주선 어둡고 평평 | ShipProp/출항 우주선 모두 밝기 하한 13 |
| 인스턴스 진입 팝인 | 비캠페인→캠페인 이동 시(다른 장면 없을 때) 짧은 진입 커튼(10+20tick). 오프닝이 시작되면 즉시 오프닝 블랙아웃으로 교체 |

포스트 효과 추가: `guardian_rises/fade_1..5` (blit 배율 0.12/0.28/0.48/0.70/0.88 — 26.3 포스트 체인은 서버 uniform이 없어 계단식).

인게임 확인 항목: 우주선 ×1.35가 격납고 입구 대비 적절한지(모델 1.0 기준 약 6.9×9블록 → 9.3×12.1), `ModelScaler.value`/`togglePart`가 실제로 크기·엔진 부품에 적용되는지, 도착 검정이 차원 이동 뒤에도 유지되는지, 계단식 페이드의 끊김, 전투 HUD가 시네마틱 동안 사라지고 순차 복귀하는지, o008 회색 블록 소멸.

## r3 (2026-11-01, Vision r3) — 무기 획득 표식 · 인게임 재검증 필요

문제: `prop.rifle`(Breach 75.6,23.7,148.7 yaw 151)과 `prop.shotgun_cache`(199.9,22.5,92.7 yaw 35)에 아무것도 렌더되지 않아 어두운 통로에서 집을 대상이 보이지 않았다.

- 계약 추가: `Presentation.pickup(player, pos, yaw, kind)` → `PickupHandle`(`close()` 조용히 제거, `collect()` 획득 효과 후 제거). kind `rifle` | `shotgun_cache`.
- `Pickup` 장면(창작 연출, 추출본에 획득 VFX 없음): 지급되는 대여 무기와 같은 `WeaponModels.create(WeaponCatalog halfdan_d / dust_rock_blues)` 아이템 모델을 소유자 전용 ItemDisplay(FIXED, 밝기 15)로 표시.
  - 소총: 바닥에 눕혀 약간 기울임, 4 cm 상하 흔들림, 천천히 회전.
  - 은닉품: 블록 디스플레이 상자(광택 심층암 몸체·흑암 뚜껑, 청록 발광 띠, 보라 표식 — 몰락자 팔레트 근사), 뚜껑 위 산탄총.
  - 시안 dust 빛기둥(END_ROD 없음, 눈 1.5 m 안 미발생), 6 m 안에서 시안 발광 외곽선(바닐라 glowing, 벽 너머로도 보일 수 있음).
  - 획득: 밝은 dust 섬광 + 상승 기둥 + `transmat` 합성음(pitch 1.25), 그다음 제거.
- `RisingMission`: 독립 필드 `pickup`. BREACH 구역에서 BREACH_DARK~ARM_YOURSELF 동안 소총 미획득이면 소총 표식, SUPPLY_CACHE에서 산탄총 미획득이면 은닉품 표식. 단계 이탈·pause·retire(사망 재시작·스킵·close)에서 조용히 닫힘, `grantRifleNow/grantShotgunNow`에서 collect. 획득 반경 2.5 → `PICKUP_RADIUS = 3.0`(소총·은닉품 모두).
- 참고: 실제 맵에서 `checkpoint.arm_yourself`는 소총에서 2.13 m라 ARM_YOURSELF 체크포인트 재시작 시 배치 직후 바로 획득된다(r3 이전에도 2.5 m 기준으로 동일).

인게임 확인: FIXED 컨텍스트에서 무기 모델 방향·크기(바닥에 눕는지, 바닥에 묻히지 않는지), 상자 비율·yaw, 빛기둥·외곽선 가독성, 획득 섬광/소리.

## r4 (2026-11-01, Vision r3 dep) — 인게임 재검증 필요

| 문제 | 수정 |
|---|---|
| 출항 내내 1인칭 무기(ProfileWeaponView 소유자 전용 DisplayHud)가 화면에 남음 | `weapon/ProfileWeaponView`에 `suppressed` 술어 1개 + `update()` 조건 1개(**weapon 레인 파일, 최소 변경**). `RisingPresentation.hudHidden`(시네마틱 잠금 또는 순차 복귀 대기)에 연결 → 오프닝·출항·도착 커튼 동안 제거되고, 풀린 뒤 첫 tick에 기존 경로가 다시 만든다(복구는 기존 update 경로 1회). 레거시 손 경로는 관전자 위장으로 이미 숨겨짐 |
| 우주선이 화면에 거의 안 보임 (d02–d10) | 시작 0–6 tick 검정 컷 후 선체 3/4 전면 약 11블록(×SCALE/1.35) 지점으로 시점 이동: 고리 위 후보 각도/반경/높이 중 충돌 없고 선체 중심까지 시야가 트인 첫 지점(`level.clip`). 가로 1/3 이상을 목표로 한 거리(수평 FOV ≈107° 기준 약 48° 폭). 스캔·시동 동안 선체 중심을 계속 조준. transmat 섬광 아래에서 후측면 약 15블록으로 컷, 이륙 중 진행 방향을 약간 앞서 0.85 비율로 추적해 중앙 유지, 섬광(206) → 검정(212) |
| 도착: 검정 ~1 s 후 페이드 없이 탑 | 원인 추정: 클라이언트 "지형 불러오는 중" 화면이 유지 시간을 먹음. `Curtain`이 이제 클라이언트 적재 완료(`hasClientLoaded`, 자기 청크 전송 완료, 청크 배치 미승인 0, 6 tick 연속; 최대 10 s)를 기다린 뒤 유지 시작. 유지 40 tick(2 s) → 5단계 페이드 30 tick. 커튼 전체가 시네마틱(HUD·무기 숨김) |
| 도착 자막이 완료 채팅에 가려짐 | 완료 채팅을 `RisingPresentation.afterArrival`로 미뤄 커튼 종료 시 전송(`RisingCampaign.finish` 1줄 교체, **디렉터 레인 파일**). 검정 위에 "임무 완료" 타이틀 카드(굵은 흰색, 부제 "━━━━━━   떠오르는 수호자   ━━━━━━" 금빛) — 창작 연출. 페이드 시작 때 창작 자막 `rg.arrival.tower`를 액션바로 |

범위 밖: 채팅 "[MinigameQA: 단계 이동: DEPARTURE]"는 운영자 명령 출력이라 손대지 않았다.
