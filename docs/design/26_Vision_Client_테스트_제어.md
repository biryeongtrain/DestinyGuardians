# 26. Vision Client 테스트 입력·안전 제어

2026-10-22. **설계 초안 / 미구현.** 다음 gameplay 기능보다 먼저 실제 클라이언트 이동·공격을 재현할 테스트 제어를 마련한다.
이번 변경은 이 문서뿐이다. 원본 Vision 프로젝트를 읽었으며 수정·빌드·실행·HTTP 호출·CU 재시도는 하지 않았다.

## 1. 현재 증거와 완료 경계

- H18 QA 기록: GameTest 100 / JUnit 49 통과, 최종 JVM의 Arc·Void·Solar·복원 스크린샷과 state 저장. 이 문서에서 재실행하거나 독립 검증하지 않았다.
- **실제 OS 키/마우스 조작은 미검증이다.** 전달된 CU 기록에서 Java가 앱 inventory에 없었고 `getApp("java")` / ID 선택이 유효하지 않았다. 정확한 GraalVM bundle `com.oracle.java.jdk`도 `Running application not found`를 반환했다.
- 화면 잠금 해제나 앱 재탐색으로 나중에 해결될 수 있지만, 현재 CU가 Java 창에 연결됐다고 쓰지 않는다. 사용자 탭 전환·다른 앱 키 입력·클라이언트 재시작으로 우회하지 않는다.
- Vision 입력 API가 구현돼도 **클라이언트 내부 가상 입력 검증**이다. 실제 CU 키/마우스·OS focus 경로 검증과 분리해 기록한다. HTTP `/look` 성공도 물리 마우스 검증은 아니다.
- 서버 명령으로 능력을 직접 발동한 결과는 렌더링/서버 기능 증거이지 클라이언트 입력 전송 증거가 아니다. 입력 API도 서버 `GuardianAction` 직접 호출이나 능력 패킷 합성으로 대신하지 않는다.

## 2. 원본에서 확인한 현행 API

읽은 원본: `/Users/qf/IdeaProjects/copper-golem-vision-client-26.3`, HEAD `3e01430`, 조사 시 working tree clean.
아래 경로는 원본 프로젝트 기준이며, QA용 복사본·런타임 주입본과 구분한다.

| 현재 클래스/파일 | 실제 역할 |
|---|---|
| `src/main/java/com/coppergolem/visionclient/VisionClientMod.java` | 초기화, HTTP 시작/종료, 선택적 autoconnect. `coppergolem.vision.port` 기본 8100; Gradle client run 설정 기본 8102 |
| `.../VisionHttpServer.java:46–96` | `127.0.0.1` bind, 아래 11개 context, HTTP worker 4개 |
| `.../VisionHttpServer.java:172–182` | `Minecraft.execute` 후 최대 10초 대기. timeout이 이미 큐에 넣은 작업을 취소하지는 않음 |
| `.../ClientAuxControl.java` | state, HUD, perspective, focus-loss pause 옵션, 화면 닫기. 클래스 설명도 gameplay input을 의도적으로 제외 |
| `.../CameraControl.java` | `setLook` / `turn`: LocalPlayer yaw·pitch·head yaw 변경. 이동/공격 없음 |
| `.../ScreenshotCapture.java:24–48` | 실제 render target PNG, 클라이언트 스레드 예약과 임시 파일 정리, 최대 10초 대기 |
| `.../ClientPerception.java`, `.../ClientMapScanner.java` | scene / volume / navigation 관측 |
| `mcp-bridge/vision-mcp-bridge.mjs` | stdio MCP→고정 `http://127.0.0.1:${VISION_PORT}`. env 기본 8100; 현행 일반 fetch에는 명시적 abort deadline 없음 |

| 현행 HTTP 경로·파라미터 | MCP 도구 | 주의 |
|---|---|---|
| `GET /state` | `vision_client_state` | 읽기: inWorld, hasPlayer, dimension/world, windowActive, hudHidden, pauseOnLostFocus, perspective, screen, overlay, yaw/pitch. 위치·속도·camera/vehicle ID·lease 정보 없음 |
| `GET /screenshot` | `vision_screenshot` | 실제 PNG. `hideHud`는 HTTP 파라미터가 아니라 bridge의 HUD 임시 변경·복원 옵션 |
| `GET /scene?dist=64` | `vision_scan_scene` | 구조 관측, screenshot 아님 |
| `GET /volume?radius=8&yRange=6` | `vision_scan_volume` | 블록 관측 |
| `GET /nav?radius=12&yRange=8` | `vision_scan_nav` | 이동 가능성 관측, 실제 이동 아님 |
| `GET /look?yaw=90&pitch=0` | `vision_look` | 시선 변경 |
| `GET /turn?dyaw=10&dpitch=0` | `vision_turn` | 상대 시선 변경 |
| `GET /hud?hidden=false` | `vision_set_hud`, `vision_toggle_hud` | 상태 변경 |
| `GET /perspective?mode=first` | `vision_set_perspective` | first / third_back / third_front / toggle. 서버 강제 카메라 검증 때 사용 금지 |
| `GET /pause_on_lost_focus?enabled=false` | `vision_set_pause_on_lost_focus` | 옵션 변경; 관측이라고 숨기지 않음 |
| `GET /screen?action=close` | `vision_close_screen` | in-world player 필요. 현재 소스에는 `confirm` 동작 없음 |

`vision_capture_observation`은 state/scan을 묶고 map memory에 기록한다. 기본 `normalizeView=true`는
화면 닫기·HUD 숨김·first person·pause 옵션 변경을 한다. **읽기 전용 진단에 쓰지 않는다.**
`normalizeView=false`도 기본 `mcp-bridge/map-memory/`에 쓸 수 있으므로 원본 읽기 전용 조사에는 부적합하다.
`vision_plan_test_scenario` / route 도구는 계획·서버 명령을 제안할 뿐 gameplay를 실행하지 않는다.
원본에는 movement/attack/use/lease/emergency-release/metrics endpoint가 없다. 별도 QA 사본의 `/metrics` 등을 원본 API로 문서화하지 않는다.

## 3. 최소 구현 구조 — 제안, 아직 존재하지 않음

추가 책임은 `ClientInputControl`(lease·가상 입력·틱 스케줄), `ClientControlDiagnostics`(읽기 snapshot),
작은 tick/keybinding hook, `VisionHttpServer`의 인증된 제어 route, 기존 Node bridge의 테스트 도구로 나눈다.
현재 원본 의존성은 Loader이며 Fabric API tick event가 설치돼 있다고 가정하지 않는다. hook을 추가하려면 26.3용 mixin 설정을 명시적으로 마련한다.

로컬 26.3 bytecode에서 확인한 연결 지점:

- `KeyboardInput.tick()` → `ClientInput.keyPresses`와 이동 벡터를 생성한다.
- `LocalPlayer.sendChanges()`는 Input 변경을 먼저 보내고, 탑승이면 Rot를 보낸다. H18 fake mount에서도 **이 입력 경로를 유지**해야 한다.
- `KeyMapping.isDown()` / `consumeClick()`, `Minecraft.tick()` / `handleKeybinds()`가 네이티브 입력 소비 지점이다.
- `Minecraft.startAttack()` / `startUseItem()`는 private이다. 직접 호출·패킷 합성 대신 실제 keybinding 소비 경로를 사용한다.
- `setDown(true)`만으로 attack의 `consumeClick()` edge는 생기지 않는다. 반대로 매 틱 click을 넣으면 한 번 클릭이 자동 연사가 된다.

가상 down 상태와 **소유한 일회성 click edge**를 허용된 option KeyMapping identity에만 overlay한다.
물리 key state/click counter를 덮어쓰거나 LocalPlayer.input을 교체하지 않는다. `KeyMapping.click(key)`는 동일 물리 키에 묶인 다른 mapping까지 건드릴 수 있으므로 무차별 사용하지 않는다.
취소는 overlay·미소비 edge만 지운다. `KeyMapping.releaseAll()`로 사용자가 누른 키까지 놓거나 이전 물리 상태를 복원하지 않는다.
이 hook 방안은 설계이며, toggle sneak/sprint·focus·키 재바인딩과의 실제 합성은 구현 테스트 게이트다.

### 입력 목록과 의미

| 종류 | 허용 입력 | 계약 |
|---|---|---|
| hold | forward, backward, left, right, jump, sneak, sprint | 논리 키 이름 사용. 반대 방향 동시 지정은 400으로 거부. 대각선 감속은 네이티브 계산 사용 |
| action | attack, use | press 때 edge 정확히 1개, hold 상태는 별도 유지. hold attack을 주기적 entity attack이라고 약속하지 않음 |
| pulse | swap_offhand | 1회 edge. H18 실제 발동 경로 검증에 필요; 기본 F지만 물리 키 코드에 고정하지 않음 |
| aim | 기존 look/turn 또는 sequence의 유한 yaw/pitch | 정상 LocalPlayer 시선 갱신. pitch [-90,90], yaw 유한값 정규화. lease 중 다른 제어자의 시선 변경 거부 |

drop·chat·명령 실행·inventory 클릭·creative 조작·connect/disconnect·텔레포트·임의 키 코드·임의 패킷은 초기 범위에서 제외한다.
attack/use는 현재 hit result에 대한 네이티브 동작이다. 블록 파괴·아이템 사용 부작용이 있으므로 허가된 QA 구역/대상에서만 실행한다.

## 4. Lease, 틱 길이, 긴급 해제

아래 수치는 **초기 안전 제한 제안**이다. HTTP 응답 시간이나 screenshot 수를 게임 틱으로 환산하지 않는다.

| 항목 | 계약 |
|---|---|
| 소유권 | 클라이언트 instance당 active lease 1개. 두 controller 경합은 409, 강제 선점 없음 |
| lease TTL | monotonic wall clock 2,000ms; bridge heartbeat 권장 500ms. 갱신해도 같은 lease 절대 수명 30초를 넘지 못함 |
| 단일 입력 | `ticks` 정수 1..100, 기본 1. 보통 20 client ticks/s라면 100틱≈5초일 뿐, server tick/벽시계 보장은 아님 |
| 예약 sequence | 최대 32 step, capture 8장, 전체 200 client ticks, wall deadline 15초. lease TTL은 별도로 계속 적용 |
| scenario | bridge 전체 wall deadline 최대 120초. 필요시 명시적으로 lease 재획득하되 무한 loop/자동 재접속 없음 |
| 기준 틱 | 제어기 자체 monotonic `clientTick`. 적용 틱 T부터 T+N 직전까지 N번 입력 소비; T+N 소비 전 해제. 1틱 pulse가 0틱/2틱이 되지 않게 검사 |
| 요청 식별 | instanceId + leaseId + generation + 증가 seq/requestId. 중복 요청은 같은 결과 반환, click/수명 재적용 금지 |
| 완료 | HTTP accepted는 큐 등록일 뿐. appliedStartTick / releasedTick / outcome으로 실행 완료를 구분 |

입력은 클라이언트 틱의 **네이티브 키 소비 전** 적용하고 소비 후 잔여 길이를 감소시킨다. END tick에서만 setDown하는 방식은 1틱 지연·누락 위험이 있다.
server TPS=1일 때도 client tick은 독립적이다. 서버 능력의 7틱 double tap 창을 client 7틱과 동일하다고 주장하지 않는다.

다음 중 하나면 갱신 없이 해제하고 미실행 step/edge를 폐기한다:

1. 정상 길이 종료, release, lease TTL/절대 수명/요청 deadline 초과.
2. disconnect, player/level 교체, 차원 변경, 사망, 화면/overlay 열림, 허용 서버 이탈, client 종료.
3. window focus 상실 또는 실제 사용자 키/마우스 조작 감지. 기본은 사용자에게 즉시 제어 반환.
4. tick 오류·sequence 실패·bridge 통신 실패. bridge `finally`에서 release를 시도하되 **클라이언트 TTL이 최종 방어선**이다.

focus 없는 QA가 꼭 필요하면 세션별 명시적 opt-in을 별도 승인한다. pause 옵션 변경·mouse grab을 몰래 수행하지 않는다.
네이티브 continuous attack은 mouse grab 조건도 있으므로 조건이 안 맞으면 `unsupported_context`를 반환한다. OS 잠금 중 조작 성공을 가장하지 않는다.

**긴급 해제:** 인증된 `POST /control/release`는 leaseId 없이도 해당 instance의 모든 **가상** 입력을 멱등 취소한다.
인증되지 않은 로컬 요청이 다른 QA 세션을 끊게 하지 않는다. 다른 controller의 lease 해제는 명시적 emergency 도구로만 노출한다.
현재 틱이 멈춰도 HTTP 측은 원자적 generation을 먼저 무효화하고 cleanup을 큐에 넣을 수 있다. 하지만 main/render thread가 정지한 동안 실제 키 소비·패킷 해제 완료를 보장할 수는 없다.
진단에 `revoked`와 `appliedReleased`를 구분한다. 재개 후 첫 입력 소비 **이전** TTL/generation을 재검사한다.
HTTP timeout/취소 뒤 남은 `Minecraft.execute` 작업도 적용 시 deadline/generation을 다시 확인하여 늦게 키를 누르지 못하게 한다.

## 5. 제안 HTTP / MCP 계약

**이 절의 경로와 도구는 전부 신규 제안이다. 현행 서버에 호출하지 않는다.** request/response는 JSON, 신규 mutation은 POST만 허용한다.

| 제안 route | 제안 MCP 도구 | 요청/결과 핵심 |
|---|---|---|
| `GET /control/state` | `vision_control_state` | 읽기 snapshot, capabilities, 제어 허용 여부/거절 사유. lease 갱신 없음 |
| `POST /control/lease` | `vision_control_acquire` | instanceId, controller label, requestId → leaseId, generation, expiresInMs, clientTick |
| `POST /control/renew` | bridge 내부 heartbeat | leaseId/generation/seq. 만료 뒤 부활 금지 |
| `POST /control/input` | `vision_input_hold` | leaseId/generation/seq, down 목록, ticks. 기존 가상 hold를 **전체 교체**; 빈 목록은 중립. 기존 click/sequence와 충돌하면 거부 |
| `POST /control/pulse` | `vision_action_press` | leaseId/generation/seq, action=attack/use/swap_offhand. 1 client tick edge/down 후 해제 |
| `POST /control/sequence` | `vision_test_sequence` | leaseId/generation/seq, 상대 tick별 input/aim/pulse/capture step. 전체 검증 후 원자적 예약, 부분 실행 시작 금지 |
| `POST /control/release` | `vision_control_release`, `vision_emergency_release` | 일반 해제는 leaseId 확인; emergency는 instanceId·명시적 mode. 둘 다 인증 필요 |

예: lease 획득 뒤 `input {down:["forward","sprint"],ticks:40}`는 40틱 동안 전진/달리기이며, 응답 자체가 2초 이동 성공을 뜻하지 않는다.
sequence에서 step offset 0은 accepted 다음 적용 가능한 틱이다. 같은 틱은 `state 교체 → aim → action edge → 소비 → capture 요청` 순서를 고정한다.
swap 전에 sneak가 서버에 전달돼야 하는 조합은 별도 틱으로 배치한다. 네트워크/서버 수신 순서까지 같은 틱으로 보장하지 않는다.
예약 sequence 중 외부 input/pulse는 409; release만 언제나 허용한다. seq gap은 재동기화 오류로 반환하고 추측 실행하지 않는다.

### 읽기 전용 진단

`/control/state`는 옵션 변경·화면 닫기·heartbeat·카메라 변경·파일 기록을 하지 않는다. 다음을 한 클라이언트 틱 snapshot으로 제공한다:

- protocol/capabilities, instanceId, clientTick, snapshot monotonic age, inWorld·dimension·허용 서버 식별자, player 존재/생존, screen/overlay/focus/mouseGrabbed.
- local body XYZ/velocity/onGround, yaw/pitch, camera entity ID/type/XYZ, vehicle ID/type, perspective. **local 값**이며 서버 authoritative 위치와 구분한다.
- lease 상태·잔여 TTL·가상 held keys·예약 step 수·마지막 적용/해제 틱·취소 원인. 인증 token과 full lease secret은 출력하지 않는다.
- stale/클라이언트 응답 불가 여부. main thread를 기다릴 수 없으면 기존 immutable snapshot의 나이를 표시하거나 503; 새 snapshot인 척하지 않는다.
- FPS를 추가한다면 `Minecraft.getFps()` 및 `getFrameTimeNs()` snapshot이라는 출처를 표시한다. frame percentile이 필요하면 실제 render-frame 표본을 별도로 수집한다. screenshot 간격·HTTP 속도를 FPS로 사용하지 않는다.

## 6. 보안·동시성 제한

- 기본 gameplay control은 off. 명시적 QA 실행 옵션과 허용 test server가 있어야 enable한다. 관측 API가 있다고 자동으로 gameplay 권한을 부여하지 않는다.
- listener는 계속 **127.0.0.1만 bind**한다. `0.0.0.0`, LAN 공개, 외부 터널을 지원 범위로 만들지 않는다. bridge는 `VISION_PORT`를 1024..65535의 정수로 검증하고 고정 loopback host를 유지한다. 임의 base URL/redirect는 금지한다.
- localhost는 인증이 아니다. 시작 시 생성한 충분히 긴 random control token을 `Authorization: Bearer`로 요구한다. token은 URL·응답·map memory·screenshot manifest·일반 로그에 넣지 않는다. bridge에는 env/권한 제한 runtime secret 파일로 전달하며 저장소에는 남기지 않는다.
- 신규 제어 route는 정확한 path/method, loopback peer, Host, Origin을 검사한다. 브라우저 Origin 요청은 거부하고 wildcard CORS를 내보내지 않는다. JSON content type·8KiB body·unknown field·정수 범위·finite float를 검증한다. malformed/NaN/Infinity는 기본값으로 치환하지 않는다.
- 제어 활성화 시 기존 `/look`, `/turn`, HUD/perspective/pause/screen mutation도 인증 경계를 적용한다. active lease 중 충돌하는 관측 normalizer의 변경은 409로 거부한다. 기존 무인증 GET mutation을 신규 제어의 안전한 선례로 복사하지 않는다.
- 현재 HttpServer context는 prefix 매칭이므로 신규 route는 suffix까지 exact match를 확인한다. 허용하지 않은 method 405, 인증 401/403, 불량 입력 400, 상태 경합 409, oversized 413, 과다 요청 429, stale/deadline은 구조화된 오류로 구분한다.
- action queue·HTTP 대기열·scenario step·PNG 수/용량을 제한한다. 신규 control은 instance당 pending operation 1개, 일반 요청 최대 20/s부터 시작한다. emergency release는 이 일반 제한과 slow scan/screenshot 대기열에 막히지 않게 별도 처리한다.
- 두 클라이언트는 다른 port/instanceId/token/출력 폴더를 사용한다. 포트만 같다고 같은 JVM으로 간주하지 않는다. 다른 PID 종료·사용자 profile 수정·원본 source 패치·임의 파일 경로 쓰기는 API에 넣지 않는다.

## 7. Scenario capture와 이번 검증 순서

capture는 bridge가 승인된 run 폴더 아래 저장하고, 사용자 label은 안전한 basename으로 제한한다.
원본 프로젝트 기본 map-memory나 실행 중인 사용자 profile에는 쓰지 않는다. 단일 sequence 최대 PNG 8장, 전체 scenario 최대 32장/128MiB; 초과하면 입력부터 해제한다.
렌더링 후 프레임에 capture를 예약하고 clientTick/frame 번호·monotonic timestamp를 함께 기록한다. render thread에서 screenshot future를 기다리지 않는다.
기존 `/screenshot`만 사용할 때는 전후 state로 구간을 기록하고 **정확한 해당 tick의 프레임이라고 단정하지 않는다.**

manifest: runId, 원본/사용 artifact 구분, client instance·버전, scenario/입력 계획, requested/applied/released ticks,
wall 시작/종료, server tick(별도 읽기 진단이 있을 때만), camera/body/vehicle·HUD 상태, 실제 capture timestamp,
PNG 이름/해시, assert 결과, 취소·지연·누락, 마지막 release ACK. secrets·인증 profile 원문은 제외한다.
실패도 부분 증거를 보존하고 checkpoint한다. `finally release → 해제 snapshot 확인`이 끝나기 전 성공으로 종료하지 않는다.

| 우선 scenario | 실제 클라이언트 입력과 캡처 | 통과 기준 |
|---|---|---|
| 기본 이동 | 중립 → forward 40틱 → 중립 10틱; 좌/우/후진·대각선 반복 | body 이동, 해제 뒤 가속 입력 0, 카메라와 실제 위치를 분리 기록 |
| 점프/air jump | jump 1틱 → 중립 → 공중에서 재press | 실제 Input 상승 edge, 서버 반응 관측. 단순 서버 velocity 주입으로 대체하지 않음 |
| 회피 4방향 | 방향 hold 중 sneak 1틱 / release 2틱 / sneak 1틱 | 현행 `InputRouter.DOUBLE_TAP_TICKS=7` 서버창 안에 수신됐는지 확인; anticipation/contact/recovery/restored 프레임 |
| 궁극기 발동 | 충분히 중립 유지 → sneak 선행 → 다음 틱 swap_offhand pulse → 해제 | 현행 `InputRouter`의 sneak+F 경로. 에너지/쿨타임 준비는 별도 승인된 fixture로 표시 |
| Arc/Void 공격 | 서버 카메라 적용 뒤 client aim 변경·이동/점프·attack pulse | 서버 수신 yaw/pitch·실제 primary·카메라/몸·최종 회복을 함께 확인. 수동 `/perspective`로 카메라 효과를 만들어내지 않음 |
| Solar 대조 | 같은 발동·조준·attack press | 기존 시점 유지, 정상 발사/회복; Arc/Void 카메라 증거와 별도 |
| 물리/소유권 | 허가된 낙하 fixture, 벽/천장/물, 중간 release, 진짜 외부 cinematic 선점 | 낙하 피해·충돌·복원·외부 카메라 보존. fixture 순간이동은 입력 성공 증거에서 제외 |
| 안전 실패 | bridge 중단/TTL 만료·화면 열림·사망·차원·경합 | 가상 입력/미소비 edge/예약 0, 늦은 재활성화 없음 |

capture는 idle/before → anticipation → contact/release → recovery → restored를 기본으로 한다. 고정 offset은 **샘플링 계획**이지 실제 접촉 판정이 아니다.
실제 서버 event tick/관측 프레임과 대조하여 phase label을 확정하고 맞는 프레임이 없으면 미확인으로 남긴다.
렌더링 pass, synthetic input pass, server 수신 pass, CU pass를 각각 기록한다. CU 재연결 후에는 가상 lease를 먼저 해제하고 실제 키/마우스 baseline을 따로 실행한다.

## 8. Endpoint / bridge / 입력 테스트와 우선순위

아래는 **추가해야 할 테스트**다. 이번 문서 작업에서 실행한 테스트가 아니다.

| 계층 | 반드시 검증할 계약 |
|---|---|
| 순수 lease scheduler | 1/2/100틱 정확한 소비 횟수, T+N 해제, 만료/30초 절대 상한, monotonic clock, 중복 seq/idempotency, stale generation·늦은 큐 작업 거부, 중간 release 후 예약 0 |
| HTTP | exact route/method·auth/Host/Origin·8KiB/finite/range·off-by-default·허용 서버·instance mismatch·409/429. 네 worker가 scan에 묶여도 release 무효화 경로 보존 |
| 실제 client hook | key rebinding, hold와 click 구분, attack 1회당 edge 1개, use release, swap 1회, native diagonal, jump 재press, toggle sneak/sprint, 사용자 입력과 충돌 시 양보. 정상 상태와 H18 fake passenger 모두 |
| 진단 | 조회만으로 lease가 연장되거나 키/시점/HUD가 변하지 않음; stale snapshot 표시, secrets 누출 없음 |
| bridge mock HTTP | `node:test` 등으로 실행: URL/POST/body/header·strict schema·deadline/AbortController·401/409/500·HTTP200의 `{error}`도 isError·JSON parse 실패·중복 재시도 시 click 미반복 |
| bridge 수명 | acquire→500ms heartbeat→bounded 실행→finally release; timeout/취소/SIGINT/stdio 종료·PNG 실패·client별 오류 격리. 프로세스 강제 종료는 client TTL로 해제됨을 별도 확인 |
| capture | PNG signature/비어 있지 않음, tick/frame 연결 또는 명시적 구간, HUD/시점 무단 normalize 없음, 용량 상한/경로 traversal 차단, 부분 manifest와 마지막 해제 증거 |
| E2E | 이동·점프·swap·attack이 일반 클라이언트 입력/전송 경로를 거쳐 서버에 수신됨. body/aim/능력 결과·실제 PNG가 일치하고 외부 cinematic을 종료하지 않음 |

현재 build.gradle에는 새 제어기 테스트용 의존성/태스크가 없다. 구현 단계에서 순수 로직 테스트 harness와 client mixin integration 검사를 명시적으로 추가하며 기존 GameTest 수치를 재사용하지 않는다.
bridge 테스트는 mock 서버·임시 디렉터리를 사용하고 Minecraft나 사용 중인 클라이언트에 연결하지 않는다.

1. **P0 / gameplay 작업 재개 전:** off-by-default·인증·lease/틱 scheduler·TTL/generation·emergency release·읽기 진단. 순수/HTTP 안전 테스트 통과가 먼저다.
2. **P1:** 이동/점프/sneak/sprint, attack/use edge, swap pulse와 26.3 hook. 로컬 fixture에서 실제 전송 확인. focus/toggle/mouse-grab 제약을 capability에 표시한다.
3. **P2:** MCP bridge 도구·bounded heartbeat/sequence·capture manifest·실패 복구와 mock 테스트. 원본 Vision 변경은 다음 기능 전 별도 선행 단계로 수행하고 QA 사본과 배포 artifact를 혼동하지 않는다.
4. **P3:** H18 회피/Arc/Void/Solar/물리/외부 소유권 scenario. 성공·실패 원본 증거를 보존한 뒤 다음 gameplay 기능으로 넘어간다.
5. **별도 CU 게이트:** Java 앱 inventory/bundle 연결 문제 해결 후 실제 OS 입력 검증. 해결 전에는 Vision 내부 입력 통과만 보고하고 CU 완료라고 표기하지 않는다.

현재 완료는 **원본 API·26.3 연결 지점 정적 조사와 이 설계 초안 작성**뿐이다. 신규 endpoint·bridge 도구·입력 lease·테스트·실제 키/마우스 검증은 모두 미구현/미실행이다.
