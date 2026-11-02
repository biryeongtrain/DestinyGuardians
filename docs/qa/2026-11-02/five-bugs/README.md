# 2026-11-02 재접속·캠페인 버그 및 소수점 체력 회복

## 구현

- 후방 카메라가 자신의 몸을 타깃으로 보내는 공격만 서버 입력으로 처리한다. 다른 잘못된 공격은 바닐라 검증을 유지한다.
- 클라이언트 월드 로드 ACK 뒤 전체 HUD spawn/metadata를 재전송해, 값이 변하지 않는 요소도 복구한다.
- 대장의 순간이동은 홈 반경, 높이 차이, 몸통 충돌, 이동 선분, 도달 가능한 경로를 모두 검사한다.
- 소유권 태그와 정확한 스킨이 일치하는 캠페인 대여 소총만 KINETIC으로 매핑한다. 샷건은 ENERGY에 자동 장착하며 기존 대여 무기의 슬롯을 이동할 때 원래 ItemStack/탄약을 보존한다. 재접속 시 과거 잘못된 배치를 이관한다.
- 체크포인트 재개와 재접속에서 BGM을 다시 시작한다. 클라이언트 월드 로드와 팩 준비를 모두 기다린다.
- 서버 플레이어의 음식/포만감은 20/5로 유지하고 exhaustion/timer를 초기화한다. FoodData 자연 회복·기아와 별도 Peaceful 회복을 차단한다. 능력·아이템의 명시적 heal은 유지한다.
- PvE 회복은 매 서버 틱 float 체력으로 적용한다. 실제 체력 피해만 대기를 재시작하며, 발사 및 추가 보호막만의 피해는 회복을 중단하지 않는다. 죽음/GuardianDown/관전자에는 적용하지 않고 Crucible의 기존 회복과 중복하지 않는다. 연결 해제/사망/차원 이동 시 상태를 정리한다.
- 체력 HUD의 반 픽셀 양자화를 제거하고, 증가 시 scale과 중심 위치를 2틱 보간해 왼쪽 끝을 고정한다. 피격 감소와 최초 표시는 즉시 반영한다.

## 회복 수치의 출처와 범위

2026-10-30 보관한 DDC Game Mechanics gid=1800463143, 행106-114를 대조했다. 원문/해시: [DDC 저장본](../../2026-10-30/w263/ddc-selected-rows.json).
이번에 외부 시트를 재조회한 것은 아니다.

- 기본 Health stat <=100, PvE 70 health +130 shields를 최대 Minecraft 체력에 비례한 단일 막대로 환산한다. 별도 34.5% PvE 피해 저항 추가나 고스탯 스케일링은 이번 범위가 아니다.
- Health: 1.75초=35틱 이후 21.89 HP/s /20씩, health 경계70에서 제한.
- Shields: 설명문106행의 5.3초=106틱 /39.5 HP/s를 사용한다. 표112/114행의4.9초/2.9초와 충돌하므로 원작 수치가 모두 일치한다고 주장하지 않는다. 기존 Crucible 설명문 선택과 일관되게 적용했다.
- 최대체력20일 때 health 구간은 틱당0.10945, shield 구간은 틱당0.1975다. PvP는 기존230 HP·31.25/39.5 경로를 그대로 사용한다.

## 자동 검사

- 최초 캠페인/음악 targeted JUnit: 183/183.
- 새 회복+기존 Crucible 회복 JUnit: 4/4.
- 실제 Fabric GameTest: **4/4 통과**, `health-gametest.log`, `final-gametest.log`.
  - 대여 슬롯 이관, 샷건 실제 발사 한 발 소비, 반복 지급 시 복제/보충 없음, escrow 복원.
  - 자기 자신 공격5회는 후방 카메라에서 접속 유지, 일반 상태 자기 공격은 바닐라 disconnect(의도한 음성 대조군).
  - 대장 열린 바닥 도달 성공, 벽/지붕/홈 반경 이탈 거절.
  - exhaustion에도 음식 고정, food 자연 회복 없음, natural regeneration=true와 PEACEFUL을 명시적으로 활성화한 상태에서 별도 자연 회복 없음, 명시적 fractional heal 유지, 지연35틱, 실제 피해 후 지연 재시작, fractional HUD width/보간 metadata, 관전자 회복 없음.
- 최종 전체 JUnit: **2457개 중2451 통과, 기존 자산 실패6개**, `health-full-result.json`. 이번 소스문자열 회귀 기대값 수정 후 추가 실패는 없다. 전체 green으로 보고하지 않는다.
- 실제 Gradle `jar`: `final-jar.log`. 결과와 해시는 `artifact.json`.
- 실패 이력 보존: 첫 대장 GameTest의 fixture 바닥 미생성 실패 후 실제 블록을 명시해 통과. 회복 GameTest 컴파일에서 private invulnerableTime 접근을 공개 setter로 고친 뒤 통과. `gametest-first-attempt.log`, `health-targeted-build.log`.

## 실제 클라이언트 / 서버 검증

요청한 copper-golem-vision-client-fabric-26-3 skill 및 minecraft-testing skill을 적용했다. 서버25600 / Vision8102, 전용 run 디렉터리만 사용했다.

1. 샷건 ENERGY와 소총 KINETIC 동시 장착. Native use로5→4, 재접속 후4/25 유지, 추가 use로4→3. `runtime-validation.json`, PNG.
2. 재접속 전후 PNG를 직접 검수했다. 목표 배지/제목/설명/키 안내, 체력/궁극기/능력/탄약의 변하지 않는 요소도 모두 복구됐다.
3. 서버 후방 검 카메라에서 native attack3회, 탄약50→47, 접속 유지. 해당 native 실행의 ray hit는 MISS였다. 정확한 자기 타깃 패킷 재현은 별도 GameTest 증거다.
4. 새 실행/재접속에서 `destiny_music:tutorial_rise` 서버 재생 dispatch를 확인했다. 실제 스피커 청취는 하지 않았다.
5. 강한 Hunger효과와 native 달리기/점프 후 food20, saturation5. `health-movement-during.json`에서 forward/sprint/jump native 입력과 Y80.7967 이동 확인. 마지막 입력은 모두 해제됐다.
6. 격리 바닥에서15 피해를 준 후 약11.3초 동안 실제 PNG90개와 RCON 체력을 수집했다. 1.637초5.0, 1.773초5.10945, 2.449초6.641748, 2.691초7.0, 보호막 지연 뒤 증가하여20.0으로 회복했다. `health-runtime.json`.
7. 실제 PNG를 잘라 만든 `health-recovery-strip.png`, `health-recovery.webp`를 보관했다. HUD는 고정된 왼쪽 끝에서 지속적으로 늘었다. 서버 샘플과 framebuffer는 같은 정확한 틱이 아니며, 첫 캡처는 피해 패킷 반영 전 전체 막대다. 스틸 비교는2번 프레임부터 사용한다. 90 캡처는 약8 FPS 샘플이며60 FPS 성능 인증이 아니다.

### 제한과 fixture 이력

대장 실제 캠페인에서 장시간 반복 blink 스트레스 및 BGM 스피커 청취는 수행하지 않았다. 실패6개는 기존 GoldenGun HUD/무기 geometry·UV·asset manifest 관련이며 이번 수정 범위 밖에 남아 있다.

회복 QA 최초 fill은 청크 미로드로 실패했고 플레이어가 추락해 GuardianDown에 들어갔다. 이때 native 입력은 player_not_controllable로 거절됐다. 바닥을 생성하고 전용 admin revive 후 정상 테스트했다. `health-fixture-before-load.png`는 성공 증거가 아니다. 최종 체력20, 기존 resistance4 복구, 타워 위치 복귀 후 서버/client를 종료했다. 일반 프로필·월드는 건드리지 않았다.

## 정리 및 변경 범위

CU Finder 상태로 잠금 해제를 확인했다. 기존 이 배치 소유 keep_awake coordinator(session76419, caffeinate77377, 상한7200초)를 재시작 구간에도 유지했다. 마지막 native 상태는 leaseActive=false / heldKeys=[] / pendingSteps=0, nativeInput 전부false. 서버/client 종료 후8102/25600의 LISTEN이 없음을 확인했다. 소유 awake coordinator를 종료했고 caffeinate77377도 해제했다.

기존 dirty/untracked 작업을 보존한다. 이번 delta는 `/tmp/destiny-five-bugs-baseline`과 비교했으며, 이미 추적 중인 파일은 이번 hunk만 staging한다. 기존 미추적 캠페인 파일 중 수정한 파일은 전체를 추가하므로 그 파일들의 기존 구현도 함께 기록된다. 전체 checkout을 clean 상태로 재현하는 커밋이라고 주장하지 않는다. 원격 push는 하지 않는다.
