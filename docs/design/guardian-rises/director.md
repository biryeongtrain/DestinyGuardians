# A Guardian Rises — 미션 디렉터·진입 흐름 (W300 director lane)

작성 2026-11-01 · 상태: 구현 + 단위 테스트 통과, **인게임 미검증** (Minecraft client/server, Vision, 청취 모두 미실행).

## 1. 범위와 계약

- 첫 접속 튜토리얼 진입을 "떠오르는 수호자" 미션으로 교체한다. `-Ddestiny.guardianRises=false`이면 구 튜토리얼(`Tutorial`)로 즉시 되돌아간다(기본값 true).
- 디렉터는 `campaign/RisingServices`(master 소유 계약)만 사용한다. 구역(Zones)·몰락자(Fallen)·연출(Presentation)이 등록되지 않았거나 예외를 던져도 크래시하지 않고 플레이어/로그에 명확한 오류를 남긴 채 대기한다. 운영자는 `/destiny rising skip|abort`로 복구한다.

| 파일 | 역할 |
|---|---|
| `campaign/RisingCampaign` | 진입·직업 선택·대기열·Fantasy 인스턴스·구역 빌드 예산·재접속·사망·완료·명령어. `RisingMission.Host` 구현 |
| `campaign/RisingMission` | 순수 단계 스크립트(월드 타입 없음). 단계별 비트, 음성 큐, 트리거, 구역 전환, 체크포인트, QA skip, pause/resume |
| `campaign/RisingEncounters` | `enemy.ENCOUNTER.N` 마커 → 웨이브 계획, 토큰 기반 Run(봉인·재생성·스테일 콜백 차단), 실루엣 장식 |
| `campaign/RisingObjectives` | 한 줄 목표 HUD(튜토리얼 트래커 재사용), GCB/비GCB 키, 20s/45s 길잃음 안내, 낙하 복구 |
| `campaign/RisingLoadout` | TutorialLoan 영구 escrow 위에 소총/산탄총 지급, 정확히 1회 반환 |
| `campaign/GuardianRisesProgress` | 기존 상태기계 + `replaceEnemy`(봉인 후 분실 적 교체), `forceStage`(QA), 조회자 |
| `campaign/GuardianRisesInstances` | 변경 없음(PREPARING→READY→RUNNING→DRAINING→CLOSED, 1개 동시 준비) |
| `tutorial/Tutorial` | 플래그 분기, 캠페인 HUD 브리지, JOIN 시 진행 중 대여 보존, `active()`에 Rise 음악 범위 포함 |

## 2. 진입 흐름

1. `TowerSpawnWorld` 접속 처리 → `Tutorial.shouldStart` → `RisingCampaign.shouldStart` (새 미션 revision `guardian_rises_completed_revision` < 1, 구 튜토리얼 완료와 무관). 완료 후에는 강제하지 않는다. `/튜토리얼`은 자발적 재도전(체크포인트 저장본이 있으면 이어감).
2. 직업이 없으면(NONE) **CHOOSING**: 채팅 클릭 버튼 `[타이탄] [헌터] [워록]`(`/destiny rising class <id>`) + HUD 안내 "E에서 언제든 변경 가능". E 메뉴로 골라도 감지한다. 기존 직업은 유지한다. 원작의 직업 선택 원/속성 제단은 사용하지 않는다.
3. **QUEUED → PREPARING**: `GuardianRisesInstances.prepare`(동시 준비 1개, 용량 `-Ddestiny.guardianRises.capacity` 기본 16). 진입 구역(체크포인트의 구역)을 전역 빌드 큐로 준비. 대기 중에는 피해 무시·느린 낙하, 직업 선택 후엔 실명(어둠에서 시작하는 연출 보존). 로딩 HUD에 진행률.
4. 진입 구역 완성 → **READY**(직업 선택 중이어도 준비 슬롯을 즉시 반환) → 직업 확정 시 **RUNNING**: 장비 escrow, 미션 시작, 첫 배치는 미션의 `place`가 수행(플레이어는 READY 전 인스턴스에 들어가지 않음).

### 구역 배치와 빌드 예산

- 구역 원점: `x = 2048 + 4096·zone.ordinal(), y = 64, z = 2048` (GATEWAY, BREACH, DIVIDE, DOCK13). 서로 4096 블록 떨어져 시야 밖 선행 빌드 가능.
- 전역 빌드 큐: 서버 tick당 **총 2 ms**(`BUILD_BUDGET_NANOS`), 한 번에 하나의 작업을 순차 처리. 실행 중인 플레이어가 출구에서 기다리는 구역은 현재 머리 작업 바로 뒤로 우선 배치. 구역 입장 시 다음 구역을 즉시 예약(선행 빌드).
- 구역 전환: 출구 트리거 → 다음 구역이 준비되었으면 실명 30틱 페이드 + 텔레포트, 아니면 "고스트가 앞길을 살피고 있어요…" 후 대기(진행 단계는 이미 전환되어 체크포인트 저장).

## 3. 단계 스크립트

음성 ID는 추출본 `dialogue-ko.csv`의 한국어 고스트 WEM 태그(실제 음원·자막은 presentation lane)이다. **배치 시점·트리거 반경·대체 경로·웨이브 규칙·추가 대사 위치는 모두 본 lane의 창작 설계**이며 원작 타이밍을 해독한 것이 아니다.

| 단계 | 구역/앵커 | 비트 | 진행 조건 | 음성 |
|---|---|---|---|---|
| GHOST_SCAN (체크포인트) | GATEWAY `spawn.player` | `openingScan(눈 위치)`, Rise 1회 시작 | 연출 done(90초 안전 타임아웃, 서비스 없으면 2초 후) | 오프닝 대사는 presentation |
| GATEWAY | — | 목표: 장벽 | `exit.breach`(없으면 `trigger.wall`) 반경 3 | 64, 60 · 길잃음 79 |
| BREACH_DARK | BREACH 진입 앵커 | 실루엣(`enemy.*dark*`/`*silhouette*`) 정지 상태 스폰 | `trigger.rifle` r4 또는 `prop.rifle` r9 → `ghostScan(소총, 50틱)` done | 55, 5d · `trigger.breach_dark` r4 → 80 |
| ARM_YOURSELF (체크포인트) | `checkpoint.arm_yourself` | 소총 지급(`prop.rifle` r2.5) → 손에 들면 3초 후 | 소총 장착 확인(미수령 상태로 전투 금지) | 50 · 장착 시 61 · E 안내 |
| BREACH_FIGHT | — | 실루엣 제거, BREACH 전투 웨이브 | 봉인 + 전원 처치(시간 성공 없음) | 1웨이브 62, 이후 65(보행탱크면 7f), 절반 처치 6b |
| SUPPLY_CACHE | — | 산탄총+기본 특수탄(`prop.shotgun_cache` r2.5) | 수령 후 `exit.divide`(없으면 `trigger.breach_exit`) | 5c, 67 · 수령 6f |
| DIVIDE_WALKER (체크포인트) | `checkpoint.divide_walker` | `trigger.walker_arena` r8(없으면 즉시/30초) 진입 시 전투, Walker는 항상 마지막 웨이브 | Walker 포함 전원 처치 | 81 · Walker 7f+78 · 추가 웨이브 7b |
| DOCK_13 (체크포인트) | DIVIDE에서 이동 → DOCK13 `checkpoint.dock_13` | 신호 추적, 부두 도착 | `exit.dock13` → DOCK13, `trigger.ship` r6 / `prop.ship` r12 | 82 · 15초 83 · 부두 84 |
| SHIP_DEFENSE | — | `ghostScan(우주선)` 지속 + DOCK13 웨이브 | 전원 처치 | 77 · 웨이브별 7a, 52, 74, 7b |
| DEPARTURE | — | 2초 후 `departure(우주선)` | done(화면 암전) → 반납·탑 이동·revision 저장 성공 | 75 |
| COMPLETE | 탑 | 인스턴스 회수 | — | — |

- 음성은 디렉터 큐에서 한 번에 하나(반환 길이 + 8틱, 길이 0이면 60틱)씩 내보내며 단계가 바뀌면 이전 단계 대사는 폐기한다.
- 마커 누락: 비전투 목표는 오류를 1회 보고 후 5초 뒤 진행(막힘 방지). **전투 마커 누락은 자동 성공시키지 않는다**(오류 보고 후 대기, 운영자 skip).
- 능력: GHOST_SCAN·DEPARTURE·구역 이동 중엔 사용 차단, 나머지는 즉시 사용 가능(능력 강제 사용 관문 없음).
- 피해: GHOST_SCAN·GATEWAY·BREACH_DARK·DEPARTURE·이동/완료 중 플레이어 피해 무시. 전투 단계는 Fallen lane의 `Difficulty.FIRST_MISSION` 튜닝 피해를 받는다.

## 4. 전투 규칙 (RisingEncounters, 창작 설계)

- 구역의 `enemy.*` 마커(실루엣 제외)를 encounter 이름별 웨이브로 묶는다(마커 번호 자연 정렬). `wave=N` 태그가 우선, `kind=walker`는 항상 마지막 단독 웨이브. 웨이브당 최대 24 AI.
- 다음 웨이브: 직전 웨이브 생존 ≤1(웨이브 3명 이하면 0) 상태로 30틱 유지 시. 시간만으로 넘어가지 않는다.
- 봉인: 마지막 웨이브의 모든 필수 스폰 성공 후에만 `sealEncounter`. 스폰 실패는 40틱마다 재시도, 5회째 오류 보고.
- 분실(`lost`): 처치가 아니면 그 슬롯을 40틱 후 같은 종류로 재생성하고 `replaceEnemy`로 교체 — 분실 적 때문에 막히거나 빨리 끝나지 않는다.
- 모든 콜백은 시작 시의 progress token에 묶인다. 사망·skip·재시작 후 이전 세대의 처치/분실은 무시된다.

## 5. 사망·낙하·길잃음·재접속·재시작

- 사망: `ALLOW_DEATH`를 가로채 체력 회복·실명 2초 → 현재 교전 초기화 후 체크포인트에서 재개(죽음 화면/탑 귀환 없음). DEPARTURE 중엔 같은 단계 재시작.
- 낙하: 구역 마커 최저 Y − 24 아래면 마지막 안전 지면으로, 1분 내 3회째는 단계 앵커로 복귀(피해 없음).
- 길잃음: 목표에 3블록 이상 가까워지지 않은 채 20초 → 방향·거리 안내, 45초 → 고스트 빛 궤적 + 대사 1회(GATEWAY 79, 그 외 76).
- 재접속: 접속 종료 시 체크포인트 저장, 연출 정지, 적 정지. **120초 이내** 재접속하면 같은 인스턴스에서 이어간다(오프닝/출발은 재생, 진행 중 전투 유지). 인스턴스 밖으로 복귀했다면 현재 단계 앵커로 재배치. 120초 초과 시 인스턴스를 회수하고 다음 접속 때 저장된 체크포인트에서 새 인스턴스로 복원.
- 서버 재시작: 저장된 체크포인트(UUID attachment `guardian_rises_progress`: checkpoint, music, rifle, shotgun)로 복원. 엔티티 ID는 저장하지 않는다. 대여 escrow는 기존 TutorialLoan 영구 attachment로 JOIN 시 반환되고, 새 인스턴스 진입 시 다시 보관·지급(플래그 기준)한다.
- 인스턴스 밖으로 나감(`/tower`, `/tp` 등): 체크포인트 저장, 장비 반환, 인스턴스 회수. 미완료이므로 다음 접속 시 다시 이어진다.

## 6. 완료·멱등성

`departure` done → (1) escrow 반환(정확히 1회, TutorialLoan.restore 기반) (2) `TowerSpawnWorld.teleport`, 실패 시 오버월드 스폰 (3) 이동 성공 시에만 revision 저장 + 진행 attachment 삭제 + COMPLETE. 이동 실패는 40틱마다 재시도하는 안전 상태로 남고 중복 지급하지 않는다. 롤백 대비로 구 튜토리얼 revision도 완료로 표시한다(플래그를 false로 되돌려도 완료자를 구 튜토리얼에 강제하지 않음).

## 7. 음악

`Tutorial.active(p)`는 이제 "구 튜토리얼 세션 또는 Rise를 시작한 연결의 Rising 실행 중"을 뜻한다. `ActivityMusic`의 TUTORIAL 장면(tutorial_rise, 1회 재생)이 그대로 작동한다. `musicStarted`는 진행 이력으로 저장한다. 체크포인트 복원·재접속 때는 새 연결의 음악 장면을 다시 활성화하며, 리소스팩과 클라이언트 월드 로딩이 끝난 뒤 Rise를 처음부터 1회 재생한다. 같은 연결에서 정상 재생이 끝나면 반복하지 않는다. 완료/중단 시 `ActivityMusic.tutorialEnded`.

## 8. 운영 명령 (op 2)

- `/destiny rising start [player]` — 대기열 추가(저장 체크포인트에서).
- `/destiny rising status` — 세션 상태, 인스턴스 상태, 빌드 대기, 단계/체크포인트/구역/남은 적/실제 엔티티 수/오프라인 시간/오류 수.
- `/destiny rising skip <stage>` — 자기 세션의 단계 이동(이전 단계 지급품 지급, 해당 앵커로 배치).
- `/destiny rising abort [player]` — 체크포인트 저장 후 중단, 탑 귀환.
- 일반: `/destiny rising class <titan|hunter|warlock>`(선택 단계에서만), `/튜토리얼 나가기`(Rising 중단).

## 9. Master 연결 필요 지점

- `RisingCampaign.init()`은 `Tutorial.init()`에서 호출된다(추가 연결 불필요).
- 서비스 등록: `RisingZones.init()`, `RisingFallen.init()`, `RisingPresentation.init()`(및 모델 설치)를 `DestinyGuardians` 초기화에서 호출해야 한다(소유 범위 밖).
- `ActivityMusic.tick`: 현재 `Tutorial.active(player)`를 그대로 쓰면 된다(Rising 음악 범위 포함). 변경 불필요.
- `TowerSpawnWorld` AFTER_RESPAWN 가드: `Tutorial.active` 사용 중. 사망은 `ALLOW_DEATH`로 가로채므로 일반적으로 도달하지 않지만, 방어적으로 `|| RisingCampaign.active(newPlayer)` 추가 권장(파일 소유 밖).
- `AbilityService`: `Tutorial.allows`가 `RisingCampaign.allows`로 위임(변경 불필요).
- 다른 lane과의 마커 이름 규약(이 문서 3장 표): `spawn.player`, `ghost.scan`, `trigger.{wall,breach_dark,rifle,breach_exit,cache,divide_enter,walker_arena,dock_enter,ship}`, `prop.{rifle,shotgun_cache,ship}`, `checkpoint.{arm_yourself,divide_walker,dock_13}`, `exit.{breach,divide,dock13}`, `enemy.<encounter>.<n>`(kind/wave 태그), 실루엣은 encounter 이름에 `dark` 또는 `silhouette` 포함. `trigger`의 `radius`/`height` 태그가 있으면 기본 반경보다 우선한다.
- 마커 좌표는 발 위치로 간주해 그대로 텔레포트한다.

## 10. 검증

수행: `./gradlew compileJava`(성공), `./gradlew test --tests 'kim.biryeong.destiny.campaign.*'` 20개 통과 — 전체 단계 진행, 체크포인트 재시작과 스테일 처치, 완료 멱등(탑 이동 실패 후 재시도 1회), 플래그/등록 판정, 연출 서비스 부재 안전 진행, 전투 마커 누락 시 시간 성공 없음, 구역 빌드 대기, pause/resume과 Rise 1회, 웨이브·봉인·재시도·분실 재생성·실루엣.
참고: 같은 실행 묶음의 `sound.FireVariantsW98Test`, `sound.ReviewedAudioW234Test`는 오디오 인벤토리 수 불일치로 실패하며 본 lane 파일과 무관(작업본 시드의 기존 상태).

미검증(Master 인게임 필수): 실제 Fantasy 인스턴스 생성/회수, 2ms 예산과 MSPT, 텔레포트·페이드·실명 연출 체감, Polymer HUD 겹침(트래커 vs 자막), 채팅 클릭 직업 선택, E 메뉴 감지, 소총/산탄총 지급 슬롯과 반환, 사망 가로채기(무기·능력 정리 후 재개), 낙하 복구, 재접속 120초 경계, 서버 재시작 복원, 탑 이동 실패 경로, Rise 1회 청취, 두 플레이어 동시 진행 격리.

## r2 — 경로를 따르는 고스트 안내 (2026-11-01, master Vision 피드백)

문제: 직선 14 m 궤적이 차체·벽에 묻히고, Gateway 계단·터널과 Dock 13처럼 꺾인 동선에서 길을 잃는다(`/private/tmp/destiny-w300-vision/r2/gw/a.png`, `dock_de.png`).

- `RisingRoutes`(신규, 순수): map lane의 `data/destiny/guardian_rises/zones/routes.json`(zone-local 발 위치, 바닥 표면 y, `jump`, 선택적 `objective`)을 1회 파싱·캐시하고 구역 원점(`RisingCampaign.Session.origin`)을 더해 월드 좌표로 변환한다. 파일이 없거나 깨진 지점은 건너뛰며, 2점 미만 구역은 경로 없음으로 처리한다.
- 구간 선택: 플레이어에서 가장 가까운 웨이포인트(높이 차 2배 가중, 위아래 겹친 계단/터널 오인 방지) → 목표 위치에 가장 가까운 웨이포인트 방향으로 최대 5개 / 22 m. 이미 지나친 가장 가까운 점은 버려 뒤로 끌지 않는다. 목표가 뒤쪽이면 역방향, 목표 웨이포인트를 넘어서 그리지 않는다. 마커 이름과 무관하게 목표 좌표로 구간을 정한다.
- 그리기(`RisingObjectives.trail`): 플레이어 발 → 구간 점들을 바닥 +0.3 m로 잇는 고스트색 먼지 빵부스러기, 위상이 매 tick 앞으로 흘러 방향이 읽힌다. 첫 1.2 m는 카메라 앞을 비운다. 점프 지점은 위로 솟는 END_ROD(약 1개/강 3개)로 표시. 경로가 없을 때만 기존 직선 14 m로 대체. 모든 입자는 소유자에게만 전송.
- 조건 완화: 이동·집기 목표(Hint MOVE/GRAB/SWAP/EQUIP_MENU)는 단계 시작 2초 후부터 **약한 궤적**(30틱마다, 간격 1.3 m, 크기 0.75 — 약 17입자/1.5초). 3블록 이상 가까워지지 않은 채 **10초** → 방향 문구(기존 20초), **25초** → 강한 궤적(10틱마다, 간격 0.6 m, 크기 1.2, 목표 표시, 약 4입자/tick 이하)과 고스트 재촉 1회(기존 45초). 전투 목표는 길을 잃었을 때만 궤적. 연출이 HUD를 숨기는 동안(`RisingPresentation.hudHidden`) 궤적도 끔.
- 실제 r3 routes.json(증거 폴더 사본) 파싱 점검: GATEWAY 48점/점프 18, BREACH 116/7, DIVIDE 103/35, DOCK13 12/2. 시작점에서의 구간 20.7~25.8 m, 6점 (`w300-evidence/director/r2/routes-probe.txt`). 번들 리소스에는 아직 routes.json이 없으므로 map lane 반영 전까지는 직선 대체가 동작한다.
- 연결: `RisingCampaign.running()`의 `objectives.tick(...)` 호출에 `zone, origin` 두 인자만 추가(기존 5인자 오버로드 유지).
- 미검증: 실제 화면에서 입자 가시성(어두운 Dock 13, 차체 사이), 밀도/흐름 체감, 점프 화살표 판독, 클라이언트 입자 부하, routes.json 실제 좌표와 지형 정합. Master Vision 필요.
