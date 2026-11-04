# W90 — 계층형 병렬 구현과 통합 Vision 검증

2026-10-25 운영 계약. 실제 할당·결과는 [현재 W93 작업 큐](../qa/2026-10-25/w93/parallel-work-queue.json)에 둔다. [W90](../qa/2026-10-25/w90/parallel-work-queue.json)·[W91](../qa/2026-10-25/w91/parallel-work-queue.json)은 역사적 checkpoint다. W91의791GT/681JUnit 통과 뒤 실제 화면 실패를 발견해 W92에서 trusted outbound projection과 실제 encoder 회귀를 구현했다. W92최종799GT/681JUnit 강제2회·동일JAR·실제46PNG(원본15개 직접검사)·캐시 감사를 통과해 **W91 대상 범위만 시각 수락**했다. L1의 별도 wire시험/자식1차리뷰, 총괄의 공유통합/직렬gate/단일취합Vision을 유지했다. HUD softness/원음 식별/다른 legacy모델 경계와 전체 목표는 남는다. 아래 NEXT는 구현 계약·backlog이며 각 QA의 최종 결과와 구분한다.

사용자 부재중에는 허용된 Computer Use로 QA 안내·채팅·포커스 같은 UI 장애를 직접 처리한다. 잠금·인증·보안 경고는 우회하지 않는다. 일반 프로필/월드·사용자 앱/미저장 프로젝트·영구 전원 설정은 보존한다. 동일 SDL 시작 멈춤은 무한 재기동하지 않고 로그를 보존해 원인을 진단한다.

## 지휘 계층과 소유권

`topmaster → L1 domain lead → L2 구현/시험 child → 필요하면 더 깊은 child`로 운영한다. L1은 단순 작업자가 아니라 범위 분해·재위임·1차 리뷰·결과 취합을 책임진다. 실제로 분리 가능한 작업만 재위임하며 단일 문서 같은 leaf를 계층 수를 채우려고 쪼개지 않는다.

| L1 작업 분담 | 책임 / leaf 범위 | 공유 경계 |
|---|---|---|
| cleanup lead (신규) | 완료/실패 teardown 분해, 공통 helper와 consumer 정리·리뷰 | topmaster가 기존 부모 작업을 명시 인계한 뒤 exact-file 확정 |
| spawnisolated lead (기존 workerA) | 격리 spawn helper·오염 진단 분해·리뷰 | cleanup helper/동일 consumer를 중복 수정하지 않음 |
| visual lead (기존 workerB) | HUD softness prototype, 이후 무기 모델·모션·음향의 별도 child 검토 | 공유 HUD/runtime/registry 통합은 topmaster |
| workflow lead (이 sidecar) | 본 문서와 JSON 큐 | 문서 leaf로 유지, child 생성 없음 |

topmaster는 전체 우선순위·도메인 간 계약·공유 파일 통합·최종 수락·직렬 gate·최종 Vision batch를 소유한다. journal(`13_헌터_구현_로그.md`), index(`00_문서_안내.md`), 모든 README 갱신도 topmaster 전용이다. 실제 수락·완료·하위 위임 상태는 큐의 taskTree에 기록한다. 도구가 없는 L1은 이를 보고하고 별도 앱 task 생성으로 우회하지 않는다.

**재귀 생성 권한과 도구 노출은 다르다.** 사용자는 후손 재위임을 허용했지만, 프롬프트만으로 하위 세션의 생성 도구를 켤 수는 없다. 직접 spawn이 가능한 lead는 직접 위임한다. 불가능한 lead는 파일 범위·수락 기준을 담은 자식 작업 요청을 총괄에 반환하고, 총괄이 가용 native 도구로 생성할 수 있다. 이때 `logicalParent=L1`과 `spawnedBy=topmaster`를 따로 기록하여 직접 재귀 호출처럼 보고하지 않는다. leaf 조사에는 불필요한 중계 child를 만들지 않는다.

1. topmaster가 플랫폼의 **실제 가용 child 슬롯**을 확인해 네 L1이 공유할 상한을 배정한다. 깊은 child도 같은 총량에 센다. 도구가 수치 한도를 제공하지 않으면 lead별 허용 동시 child 수를 작게 배정하고 실제 spawn 수락 여부를 기준으로 한다. 슬롯 거절은 대기열에 남기며 무한 재시도나 앱 task 우회를 하지 않는다. 슬롯을 기다리는 lead는 재귀 생성하지 않는다.
2. L1은 자식에게 부모의 허용 파일 중 **겹치지 않는 exact-file 부분집합**, 금지 범위, 의존성, 수락 기준, 비Vision 검사와 native manifest를 넘긴다. 소유권·금지는 모든 후손에 전이된다. 새 파일·생성 출력·테스트·fixture도 쓰기 소유권에 포함한다.
3. child가 기준 소스 식별자/dirty-file hash와 파일 목록을 되읽어 수락해야 `accepted`다. 공유 파일이 필요하면 패치 제안과 인터페이스를 L1에 반환한다. 소유 범위 확대·형제 파일 수정은 topmaster가 재배정하기 전 금지다.
4. child는 자기 파일만 작업한다. **worker/후손은 commit, Gradle/build, 서버·클라이언트·사용자 앱 기동/조작을 하지 않는다.** 테스트 코드는 작성 가능하나 실행 gate는 중앙에서 직렬화한다. 고유 출력 경로의 비변이 정적 검사만 로컬 수행한다.
5. 완료 child는 변경 파일/근거/검사 결과/미실행 항목/시나리오/미확정 사항을 L1에 반환한다. L1이 diff·경계·테스트 의미를 1차 리뷰하고 수정 재위임 또는 `reviewed`로 취합한다. 완료·회수된 child를 닫아 슬롯을 반환하고 task tree에 결과·종료 상태를 보고한다. 부모/타 lead를 닫지 않는다.
6. topmaster가 L1 결과를 재검토하고 공유 호출부·모델 선택자·registry를 순서대로 통합한다. 모든 쓰기가 멈춘 후보의 source/JAR/pack pin과 gate 결과를 확정한 뒤 **한 번의 통합 Vision 세션**으로 검증한다. worker별 별도 클라이언트는 없다.

## 실제 무기 NEXT — QA와 별도로 제품을 개선

카탈로그는 `WeaponCatalog`가 W30 전설63행에 `WeaponExotics.append`를 더하는 구조다. [W30 선정표](45_W30_무기_선정표.md)는 초기 시제품 기록이며 현재 전투 구현 전체를 설명하지 않는다. 없는 최신 프레임이나 정확한 D2 수치를 임의 추가하지 않는다.

| 우선 | 구체적 개선 / 코드·명세 근거 | 분리 파일 / 의존성·불확실성 |
|---|---|---|
| N1 | **이자나기 일반/연마 장전 모델과 완료 강화 총신 cue**. [W84 남은 작업](99_이자나기의_짐_연마된_칼날.md), `WeaponReloadPresentation.supports`는 Beloved/Duke/Ammit만 지원 | visual의 전용 presentation·새 모델 bank·전용 시험. 원본 `izanagi.bbmodel` 보존. 완료 강화 상태와 진행 중 장전을 분리; 원작 프레임 시점 미실측이면 로컬 연출로 표시. Q/Ctrl+Q는 native v1 미지원 |
| N2 | **Austringer↔Beloved 수납/꺼내기 모션**. [W58 시각 후속](73_W58_무기_교체_Handling.md), `WeaponSwapCycle`의 STOW/READY를 연출에 반영 | visual의 별도 swap presentation·모델 bank·시험. 기존 deadline/탄약/ADS 권한 유지. N1과 다른 파일에서 병렬 준비하고 공유 runtime 연결은 topmaster 직렬 통합. 원작 손 IK·정확한 클립은 미확보 |
| N3 | **잠자리 속성별 전용 폭발 음향**. [W77 임시 재사용](92_W77_잠자리_정밀_처치_폭발.md), `WeaponDragonfly.killed`는 수류탄 impact를 호출 | visual 아래 별도 audio child: 출처 manifest·새 Ogg/event 제안·전용 시험. 식별 가능한 제공 음원 확보가 선행; 미확보면 후보 유지. 공유 sounds.json·호출부는 topmaster. 전용 VFX도 남지만 이 태스크와 합치지 않음 |
| N4 | **일반 활 LATE 피로의 피해/정확도·강제 해제 동작**. `WeaponBowWindow`는 정보 전용, [W74](89_W74_활_최적_발사창_HUD.md)·[W88 조사](../../art/weapons/w88/reference-notes.md)에서 정량값 미확정 | gameplay lead 지정·근거 수락 전 구현 대기. Biting Winds/Whispering Slab 별도 곡선·최대 유지·강제발사 profile은 null. 4초나 창 만료 즉시 발사를 발명하지 않음 |

N1~N3도 이 큐 작성으로 착수·완료된 것이 아니다. N4 조사 부족으로 나머지 구현을 막지 않는다. 각 항목의 파일 그룹·비Vision 회귀·native 시나리오는 JSON에 명시한다.

## handoff와 중앙 검증 순서

각 leaf는 native manifest를 제출한다: `taskId, candidatePin, capability, fixtureId, setup, inputSteps, serverOracle, framePlan, audioClaim, cleanup, result`가 필수다. 처음에는 pin/result가 null인 계획이다. L1이 검사하고 topmaster가 통합 순서를 정한다. 지원되지 않는 입력은 `not_run_capability`로 남기며 직접 서버 명령을 native 입력 성공으로 바꾸어 쓰지 않는다.

1. **통합 전 수락:** exact-file 충돌·미검토 child·회수되지 않은 쓰기 권한이 없어야 한다. cleanup/spawnisolated 계약을 먼저 통합하고 성공/실패/timeout/취소 정리를 검사한다. `runBeforeTestEnd`를 finally로 간주하지 않는다. 기존 exact victim·피해·탄약 assert를 유지한다.
2. **중앙 비Vision gate:** topmaster만 관련 JUnit/asset audit → 해당 GameTest → 전체 회귀/build를 직렬 실행한다. 모든 shell은 `rtk`로 시작한다. 공유 Gradle/output/팩 생성 동시 실행 금지. 첫 실패 로그를 보존하고 원인과 변경 근거 없이 통과할 때까지 반복하지 않는다.
3. **후보 고정:** final source/dirty hash, JAR, headless/native 팩과 shader/FOV 변형을 각각 기록한다. native 서버 팩과 실제 다운로드 cache를 비교한다. 파일이 바뀌면 기존 pin·결과는 이전 후보 기록으로 남기고 해당 gate를 재수락한다.
4. **Vision 단일 batch:** 중립/접속/팩 smoke → 기존 Ace 강화탄·Salvo 유지/해제·ADS 무발사 → 4방향 피격/HUD HP6·5·1 pulse/회복 → N1 장전/강화 cue → N2 교체/중단 → N3 속성별 정밀 처치/음향 → N4(근거 수락 때만) 활 window/late → 일반 활 재노킹·검 접촉/가드·궁극기 진입/복귀 회귀 → 최종 중립/정리. 이번 후보에 통합되지 않은 NEXT는 `not_integrated`로 제외 사유를 남긴다.
5. **종료 보고:** task tree에 lead/child/깊이/소유 파일/수락·리뷰·통합·종료 상태와 실패·미검증 목록을 담는다. topmaster가 journal/index/README와 통합 결과를 갱신한다. 결함 수정 후 새 후보가 필요하면 새 batch 사유를 기록하며 과거 PNG를 재사용하지 않는다.

## 공유 fixture와 증거 경계

- topmaster만 격리 QA server/profile/world와 단일 Vision client를 소유한다. spawn-disabled 환경·고정 arena·표적 UUID/종/위치/AABB·엄폐·team·HP/흡수·loadout을 시나리오마다 기록한다. 실행 전 corridor 전체 후보를 확인하고 예상 밖 entity는 실패/진단으로 남긴다. production 필터 변경이나 숨은 적 삭제로 통과시키지 않는다.
- fixture는 task/run 소유 표적·observer·team·예약·투사체·HUD/session을 추적한다. 성공/실패/timeout/취소 때 멱등 정리하고 원래 상태를 복원한다. 공용 gamerule/team을 여러 child가 바꾸지 않는다. 다음 시나리오는 이전 teardown 확인 후 시작한다.
- 각 시나리오는 입력 lease 획득 → bounded sequence → `finally release` → state 확인으로 닫는다. lease/heldKeys/pendingSteps/nativeInput 중립과 서버 use/ADS/임시 camera/session 정리를 확인한다. 정지로 ACK만 있고 실제 해제 확인이 없으면 실패/불명으로 남기고 후속 입력을 중단한다. 사용자 물리 키를 일괄 release하지 않는다.
- 서버 fixture 명령은 준비/표적 피해 증거다. native receipt는 입력 적용 증거, HP·탄약·정확 victim은 서버 판정 증거, 실제 PNG는 화면 증거다. 전후 state bracket은 정확한 서버 tick/렌더 frame 동기화가 아니다.
- 오프라인 모델/alpha 검사·JUnit·팩 일치는 framebuffer 검증을 대체하지 않는다. sound event/packet/OpenAL 초기화는 실제 청취 증거가 아니다. audio capture/청취가 없으면 청감 미검증이다. 이 batch를 무기 전수·OS 키보드·다인 성능·완전한 D2 복원 완료로 확대하지 않는다.

## W90 통합 판단

spawn 구현은 L1이 Java 자식1개에 위임한 뒤 리뷰/종료했고 master가 소스를 검토했다. visual L1은 하위 도구가 없어 자식을 만들지 않았으며 그 제한을 명시했다. 두 softness bank는70파일 재구성 검사 대상인 offline 후보로 보존하고 아직 product runtime/asset에 넣지 않는다. 작은 viewport의 재절단/moire 위험을 다음 N1~N3 기능 묶음과 함께 Vision으로 판단한다. test-only 종료/격리 개선만으로 무의미한 native 재기동을 하지 않는다. 전체 목표는 계속 진행 중이다.

## W93 후속 수락

W92의W91범위수락뒤기존Reload/Insert/Aim/Bow경계를계층형리뷰로수선했다. [W93 QA](../qa/2026-10-25/w93/README.md):809GT/681JUnit강제2회·native135PNG/25원본직접검사·6무기/10native sequence·source8452pin/실제캐시수락. 기존N1/N2모션의추가legacy경계는해결했으나W93-N1활nock상단사각형을새미해결로기록한다. 원음N3/활피로N4/softness/원작손IK는완료가아니다. native발견결함은pins를몰래바꾸지않고별도후속으로진단한다.

## W94 현재 취합 결과

[particle-only 진단](../qa/2026-10-25/w94/README.md)은 master가QA전용jar/단일native입력batch를소유하고L1은계획/L2첫리뷰,L2는정적경계·픽셀검토를맡았다. source8452pin/asset7013제품불변,18native/341PNG/19master원본검사·정리완료. 기본→차단→복원으로큰근접trail기여근거를확보했으나제품수정/반경/다인수신자는아직미수락이다. 다음취합대상은발사자near-eye제외후보이며기존observerlattice/게임시계를유지한packet회귀와native를분리한다.

## W95 현재 취합 결과

[owner-only 제품 보정](../qa/2026-10-25/w95/README.md)은 L1실제packetGT/L2정적리뷰를 master가 통합하고 강제815GT/689JUnit2회 뒤 단일Vision8sequence/161PNG로 확인했다. 관전자 원래lattice와 게임시계를 보존하며 정지self-camera 대표의 큰중앙방해감소만 수락한다. 작은dust/특정W93상단solidrectangle은 남고 native다인·성능·원작정량·청취를 수락하지 않는다. N3/N4/HUDsoftness 후속은 유지한다. 최종보고서 전용L1/L2의 실제생성자와 논리부모는 [queue](../qa/2026-10-25/w95/parallel-work-queue.json)에 구분한다.

## W96 현재 취합 결과

[선택적 critical HUD softness](../qa/2026-10-25/w96/README.md)는 shader L1/helper10JUnit·GT L1/3nativeencoded회귀를master가통합해818GT/699JUnit강제2회후113PNG/2해상도단일취합batch로경계개선·회복만수락했다. W89모델/texture/시계는보존하고actualpack의정확shaderentry2개만변경했다. lowHPammo패널가림W96-N1은historicalW89에도있고원인미분리이므로전체레이어링은후속. shaderL2의별도task생성/pendingwrite와최종nativebrokerL2의logicalparent를queue에구분한다. 전체goal/N3/N4/W93-N1/손IK/다인성능은유지한다.

## W97 현재 취합 결과 — 후보만 준비

[저체력ammo layer진단](../qa/2026-10-25/w97/README.md)은master가QAprobe/직렬컴파일/실행을소유하고L1새2GT/L2reverse-Z검토를병렬수행했다. L1첫리뷰·master최종소스리뷰후두family종료. 후보GT컴파일만성공했고native첫SDL정지로PNG/입력/개입0이므로제품/기존assert는미수정이다. 부재중UI복구권한은잠금/인증우회나바뀐전제없는재기동허가가아니다. 시도1실패/정리/기존8472pin·7013asset·팩동일성을보존하고실제가역근거후통합한다. 전체목표는진행중이다.


## W98 현재 취합 결과

[발사음 변주](../qa/2026-10-25/w98/README.md)는 master가 변환·공유 sounds·직렬gate·서버팩을 통합하고 L1은 N3 원음 재탐색, L2는 실제 유료 발사/거리 PLAY2GT를 맡았다. L1 첫 리뷰 후 master가 원본을 검토했다. 정확3이벤트의 기존 Fire_1 보존/Fire_2·3 추가만 수락하며, 820GT/704JUnit 강제2회·7019asset/실제 서버팩 감사까지다. 이번 client/입력/PNG/청취는0이다. N3 식별은 여전히 부족하며 W97 native blocker를 우회한 완료 주장이 아니다.
