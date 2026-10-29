# W258 GameTest 현행 계약 갱신

최종 결과: **GameTest 1,418/1,418 통과(exit0)**. 보간 관련 JUnit 6/6 및 Danmo/OpenGL·4GB native 입력·화면 확인 완료. 기존 파생 자산 불일치 JUnit4개는 별도 미해결이다. `final-result.json`을 기준으로 아래 단계별 실패 이력을 읽는다.

사용자 요청: `일단 게임테스트도 수정해줘.` W257 리소스팩 검증과 병행한다.

## 기준선

- 전체 GameTest 중단 전232실패/55클래스. 실패목록 `/private/tmp/destiny-w257/gametest-failures.json`, 원본log `aborted-broad-gametest.log`. 전체완료수치가 아니다.
- 전체JUnit2225개 중4개실패. 이전부터 알려진모델/manifest기준불일치4개와동일하다.
- slot4 ADS·표현·wire20클래스/90실패; slot5 장전·탄약15클래스/67실패; slot1 능력·탄도20클래스/75실패. master는공통fixture와단위자산검사·중앙실행·Vision통합소유.
- 테스트삭제/비활성화/manual전환이나 단순기대값완화로통과시키지않는다. 현재제품의leftclickADS/속도기반zoom/원본시전시간/AE·hipcone조건에맞게fixture와계약검증을갱신한다. 실제제품결함은분리수정한다.

## 통합 진행

- W257 팩 최적화 커밋: `852b713f`. Danmo4GB 실게임 팩 검증 완료 후 QA 런타임 정상 종료.
- 세 슬롯의 55개 파일을 각 main-baseline SHA256 확인 후 통합. 소유 GameTest 488개를 보존했다.
- 첫 컴파일에서 Bow fixture 생성자 인자 누락 1건을 발견하여 담당 worker 후속 패치로 수정.
- 현재 전체 headless GameTest를 4GB로 실행 중이다. JUnit 자산/manifest 기존4실패는 이 GameTest 수정과 별개로 남아 있다.

## 중앙 1차 실행

- 55파일 통합 후 compileGametestJava 통과. headless 1,418개를 시작했다.
- 13번째 배치에서 native GameTestInfo callback-map 반복 중 NPE로 실행기 종료. 전체 완료 수치 없음. 마지막 progress-bar 관측은 658통과/14실패/672완료였으며 나머지는 미완료다.
- JVM max4GiB 확인. 이 실행 종료 원인은 OOM이 아닌 callback-map 오류다. 팩 준비 완료도 확인되지 않았다.
- XML reporter는 종료 시 보고서를 쓰므로 crash에서 실패명 증거가 누락됐다. 다음 실행은 즉시 실패명을 출력하는 native reporter를 사용한다.
- 원본로그 `/private/tmp/destiny-w258/first-run.log`, `first-native.log`. 중첩 예약과 missing-attribute fixture를 담당 worker에게 재의뢰했다.

## 중앙 2차 전체 실행

- 1,418개 완료, 1,294통과 / 124실패. 기존 callback-map crash는 발생하지 않았다.
- 팩 생성 및 profile graph 게시 성공. 그러나 가속 headless 틱1200이 비동기팩 준비보다 먼저 끝나 초기4개 UI검사가 timeout했다. master는 테스트 소스셋에서만 팩 그래프 준비 후 테스트 clock을 시작하도록 수정한다. 실제 서버 superclass tick/작업큐는 계속 처리하고 wall-clock120초 실패한도를 둔다.
- 완료 후 드러난 추가51클래스(기존 미완료 구간)를 5개 고정슬롯으로 분담. slot2 모델경로27, slot3 퍽20, 기존slot4 추가1, slot1 추가2, slot5 추가1. 기존worker4개 pending_init은 종료해 슬롯소유권을 회수했고 기존 파일은 모두 slot-before로 보존했다.

## 준비 순서 targeted 확인

- 테스트 전용 GameTestPackReadinessMixin에서 superclass server tick 후, testTracker 생성 전에 실제 profile graph 게시를 기다린다. 그래프 임의 주입/가짜 준비는 없다.120초 wall-time 실패한도를 두며 테스트 deadline은 준비 뒤 시작한다.
- 4GB 실행에서56.025초 후 실제 게시 확인. ClassAbilityW255 3개 전부 통과, exit0. 프로덕션 소스/서버 기동에는 적용되지 않는다.

## 제품 결함 및 H20 fixture 재검토

- 일반 무기 사용자의 WeaponFireMotion.visible 조회가 Guardians.runtime을 생성하던 경로를 runtimeIfPresent로 변경. 기존 Subsistence 회귀의 미생성 assertion은 보존했다.
- H20 공격의 원본 peak는 과거 H26의 .05/.10 고정구간과 다르다. 전체 source window에서 동일한 단일틱 >60도(배치 >90도) 기준을 검사한다.
- H20 배치/복귀는 같은 world tick에서 BM clock만 반복하던 fixture를 실제 서버틱과 PlayerAnimations lifecycle 관찰로 교체. 프레임은 실제틱당2회 그대로 검사한다.
- staff support .025 이내 조건은 보존하고 완료된 BM tick 이후의 양손 display sample을 함께 관찰한다. 원본 회전과 native 차이를 자동으로 정상화하지 않았다.

## 중앙 3차 및 H20 보간 조사

- 첫 compile에서 HeatingUp fixture의 중복 local 변수명을 수정. 이 시도는 테스트 실행 전 실패이며 통과0으로 집계하지 않는다.
- 재실행은 실제 profile graph 준비23.715초 후1,418개 시작. H20의 native sample 누락을 `AssertionError`로 던져 실행기 전체가 중단되는 fixture 결함을 확인했다. GameTest assertion으로 바꾸어 실패가 해당 검사에 귀속되도록 수정한다.
- H20 support는 완료틱 관측에서도 첫틱0.0500878블록으로 재현됐다. 기준0.025는 유지한다.
- BM3.5.1 bytecode의 `frame()`은 `(time+.001)*40`이고 delay는 이를 정수 반올림한다. 기존 local-pose sampler가 float `progress()`를 그대로 사용해 새25ms 키에서도 약3.85% 미래 포즈를 혼합했다. 정수 delay와 같은 정수 duration으로 phase를 계산하는 수정 및 실제 BM state-machine 회귀검사를 추가한다. 현재 검증 중이며 해결 확정 전이다.
- 밀집 원본과25ms 설치본의 half-key 분석은 별도 보간 한계 증거다. source FK 수치를 native/client 화면 검증으로 취급하지 않는다.

## H20 원인 확인과 수정

- phase 단위검사6/6 통과. 실제 BM 상태기의 초기 phase0, 중간 phase0.5와 기존 격자/스코프 검사를 함께 수행했다.
- native H20 target에서 support 최대3.054738E-7블록, attack peak130.795°로 각각 기존0.025/60°조건 통과. deploy만 sample 소실 실패가 남았다.
- `RenderedBone.equals/hashCode`는 모델 원본의 bone UUID를 사용해 서로 다른 플레이어의 같은 뼈도 같다고 판정한다. `WeakHashMap` 포즈 캐시가 이를 합치고 다른 owner 종료 때 삭제했다. `MapMaker.weakKeys()`의 identity semantics로 플레이어별 live bone을 분리했다. 약한 참조 수명은 유지한다.
- SuperCamera 테스트는 전역 PlayerAnimations.tick을 직접 호출해 같은 배치의 H20 clock을 함께 진행시켰다. 수동 clock 테스트12개를 별도 환경 w258_camera_clock으로 분리했다. 수치 기준과 내부 camera assertion은 변경하지 않았다.
- JUnit 기존4실패는 `junit-assets-unresolved.md`에 실제 파생 geometry/HUD manifest 불일치로 기록했다. 테스트 기대값을 갱신하지 않았다. 이번 GameTest 회귀 정리와 별도인 자산 생성 체인 수정이 필요하다.

## 중앙 4차 전체 실행

1,418개 완료,1,415통과/3실패(exit1). H20 세 검사는 native contact·공격130.795°·deploy168.250°·실제틱당2평가·ready복귀 전부 통과. 장전 모델 경로와 일반사격 runtime 미생성 회귀도 통과. 남은 실패는 WeaponBallisticsW43 head/body, WeaponBowPresentationW50 buffered draw, StatsForAllW176 장거리 실제피해이며 담당 슬롯별 후속 수정 중이다. 실행기 crash는 없다.

## W258 Danmo 실화면 확인

수정 제품으로 격리 Danmo/OpenGL·4GB에서 native 수류탄/아크 궁극기 입력 완료. 실제PNG에서3인칭 전개·지팡이 자세 변경·활성 유지·종료 후1인칭 현재 무기복귀를 확인했다. 마지막 lease 없음/키 없음/pending0/native중립/self-camera를 확인하고 소유 QA client/server를 종료했다. 증거는 `vision/summary.json`, `vision/arc-review.jpg`.

이 캡처는60fps 부드러움 인증이나 client inter-key 오차 수학검증이 아니다. 이번 반복 실행은 server-pack reload log→player join 약87초였다. W257의단일14.31초 결과를 일반적인 로드시간 보장으로 쓰지 않는다. ZIP약33%감소는 유지되지만 item atlas16384²와 환경별 로드비용은 남는다.

마지막3개 fixture반환은baseline/result SHA256대조 후 통합했다. 테스트수는 유지하고 마지막 전체실행 중이다.

## 중앙 5차 전체 실행

1,418개 완료,1,417통과/1실패(exit1). 직전3개 실패는 모두 통과. 기존 Outlaw 비치명 정밀타격 테스트가 hip cone의 무작위 표본에 따라 head/body가 모두8.049988피해로 나온 경우를 검출했다. 이 검사의 명중 조건을 명시하는 후속 fixture 수정 중이다. 이 결과를 전체 통과로 표기하지 않는다.

## 커밋 범위

이번 전체회귀가 사용하는 GameTest 등록부·테스트전용 mixin·cleanup/packet fixture·환경 JSON이 기존에 미추적/미커밋 상태였다. 새 readiness mixin과 수정검사만 단독커밋하면 등록·도우미 의존성이 빠지므로, 실제 실행한 GameTest 소스셋의 관련변경을 명시적 파일목록으로 함께 포함한다. 다른 제품소스·모델·외부원본·캐시는 이 범위에 포함하지 않으며 기존작업본을 보존한다.

## 최종 수락

Outlaw의 실제 ray를 동일seed로검사·재생한 뒤 전체1,418개가 모두 통과했다(exit0, native suite2.111분). 테스트삭제·disabled/manual전환 없이 현재입력·시전/장전·팩게시 계약에 맞췄으며, 기존정밀/피해/소유권 조건을 유지했다. 수락된 자산검사4실패는 기대값을 완화하지 않고 별도결함으로 남겼다.

제품수정은 일반발사 조회의 불필요한 GuardianRuntime 생성 방지, 정수엔진delay와 포즈phase정렬, 플레이어별 약한identity 포즈캐시다. 무기/수류탄/궁극기 자산을 이번 GameTest 수정 때문에 재생성하지 않았다. 고정5개worktree는 삭제하지 않고 다음배치 재사용 대기 상태로 유지한다.

## 운영 테스트 서버 재개

커밋 `71e0afe0` 이후 `runServer`로 재개했다. `Done`, BetterModel 로딩, Polymer 팩 생성 성공을 확인했다. 실제 서버 JVM의 MaxHeapSize=4,294,967,296 bytes(4GiB), online-mode=true, andlist OP4, LAN `192.168.35.237:25565`를 확인했으며 서버는 켜 둔다. 기동 증거는 `server-start.json`. 격리 QA client/server는 종료하고 이번 배치의 bounded awake만 해제한다.
