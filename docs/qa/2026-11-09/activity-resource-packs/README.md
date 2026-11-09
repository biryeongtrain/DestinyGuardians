# 공격전 전용 팩 · 2026-11-09

최종 지문·실행 소유권 보강본의 관련 검사 25개와 두 공격전 실화면 재검수를 완료했다. 운영 R2 전송/3인/스피커 검증과 기존 전체 검사 실패는 아래 범위대로 구분한다.

## 구현

- `rp-r2-uploader 1.1.0+26.3`을 GitHub 릴리스에서 정확한 버전으로 받아 JiJ로 포함한다. 내장 JAR의 SHA-256이 공개 릴리스와 같은 `9bd391f6f90c668a83314b67205a576256afbb2417fea73042b622c4b09c87e8`임을 확인했다.
- 전용 대사/음악은 최종 변환된 바이트에서 분리한다. 공용 모델·효과음·강하 음악·탐색기 그림은 공용 팩에 남긴다.
- 로딩 중 준비/다운로드/적용 상태를 표시하며 `SUCCESSFULLY_LOADED` 이후에만 월드로 배치한다. 180초 제한과 요청/연결/실행 소유권을 둔다.
- 입장 전 취소는 처음 수락한 실행 토큰만 정리한다. 퇴장에는 해당 전용 팩 UUID만 pop하며 공용 팩을 보존한다.
- 전용 입력/소유 목록 지문을 공용 ZIP에도 넣어 전용 에셋 변경 시 공용 해시도 바뀌도록 했다. 전용 ZIP가 없거나 손상되면 시작 캐시를 거부한다.

## 첫 실제 클라이언트 검사

격리 서버 `/tmp/destiny-activity-packs/qa/server`, 클라이언트 `/tmp/destiny-activity-packs/qa/client`, loopback 25638/8102만 사용했다. 일반 프로필/월드와 이전 QA는 보존했다. 7200초 제한 master awake와 명시적인 `visionControlBackground=true`를 사용했다.

| 시나리오 | 결과 |
|---|---|
| 엑소더스 다운로드 8초 지연 | 로딩 화면, 타워 좌표 유지 |
| 다운로드 도중 `/화력팀 취소` | 타워 유지, 늦은 입장 없음, 실행 종료 |
| 엑소더스 재시도 | ACCEPTED → DOWNLOADED → SUCCESSFULLY_LOADED → 엑소더스 월드 |
| 엑소더스 퇴장 | 타워 복귀, 클라이언트 팩 스택에 공용 UUID만 남음 |
| 악마의 소굴 HTTP 503 주입 | FAILED_DOWNLOAD, 타워 유지, 검은 로딩 해제 |
| 실패 조건 제거 후 재시도 | 전용 팩 적용 후 악마의 소굴 월드 입장 |
| 악마의 소굴 퇴장 | 타워 복귀, 공용 UUID 보존 |
| native 입력 정리 | 매 선택 후 lease 해제, heldKeys 빈 배열, pendingSteps 0 |

포인터 위치 지정과 플레이어 준비는 기존 OP fixture 명령이다. 선택/플레이는 실제 Vision native Space 입력 경로로 실행했다. 서버 fixture, native 입력, framebuffer를 구분하며 OS 키 입력이나 스피커 청취 검증으로 보고하지 않는다. `backgroundMode`와 `backgroundActive`는 true였다. 창이 비활성인 모든 상황의 FPS를 인증한 것은 아니다.

이 첫 검사에는 전용 지문 추가 전 JAR를 사용했다. `first-pass-artifact.json` 및 `first-pass-pack-audit.json`에 식별자가 있다. 지연/취소/실패 로그와 프레임을 최종 보강 후의 재검수와 혼동하지 않는다. 새 QA 계정의 Minecraft 첫 이동 안내 toast가 일부 첫 프레임에 남아 있다.

## 음원·팩 검사

`media-audit.json`: 악마의 소굴 61 OGG, 엑소더스 204 OGG의 바이트가 원본 생성 팩과 같다. 파일 참조 누락 0. 음원 리샘플링/절단은 하지 않았다. 첫 생성 공용 132,015,374바이트, 악마의 소굴 53,630,561바이트, 엑소더스 25,628,970바이트. 최종 지문은 작은 추가 메타데이터이므로 최종 공용 크기는 다시 기록한다.

## 검사 범위

첫 통합 JUnit 2,834개 중 기존 실패 3개. 이후 지문 보강과 실행 소유권 보강에 따라 최종 결과를 아래에 갱신한다. 처음 21개 targeted 검사는 실패 0이며, 그 뒤 추가된 회귀 검사를 이 숫자에 포함하지 않았다.

기존 실패: `MinorPveBalanceW342Test.directAbilityAndLightSuperMeetTheirTargetPools`, `FireVariantsW98Test.inheritedAudioBytesAndExactlySixW98PlusSixteenW102ClipsFormClosedRuntimeInventory`, `GoldenGunHudW122AssetTest.dedicatedTransportPreservesTintAndOnlySuperSelectedBranchChanges`. 이 작업에서 관계없는 수치와 과거 누락 QA 파일을 바꾸지 않았다.

실제 전송 검사는 로컬 AutoHost 경로다. 운영 Cloudflare R2 자격 증명을 사용한 업로드, 실제 3인 동시 접속, 스피커 청취, 180초 실제 타임아웃 및 플레이 중 강제 공용 팩 재로딩은 별도로 실화면 수락했다고 주장하지 않는다. R2 경로는 출시된 업로더 API와 연결했으며 API 실패 시 입장을 차단한다.

## 최종 보강 회귀

지문을 추가한 통합 JUnit 2,835개에서 같은 기존 실패 3개만 확인했다. 그 뒤 실행 토큰 취소와 지문 없는 이전 캐시 거부를 보강했다. 최종 관련 JUnit 25개는 실패 0이며 Java·GameTest 소스 컴파일과 Gradle `jar`가 성공했다. GameTest 실행을 통과했다고 의미하지 않는다.

두 번째 전체 검사는 지문 구현 전 실행 도중 중단했으므로 수락 결과로 세지 않는다. `full-gate-with-fingerprint.json`은 지문 구현 후 완료한 전체 검사, `final-targeted-gate.json`은 최종 소유권/이전 캐시 거부까지 포함한 25개 검사다.

실제 개발 서버에서 지문이 없는 이전 ZIP가 캐시 HIT 되는 것을 발견해 보강했다. 이제 복원 시 공용 ZIP의 지문 존재·스키마·현재 소유 목록을 먼저 확인한다. 전용 파일만 대응하는 과거 캐시는 수락하지 않는다. 배포 작업은 서로 다른 두 팩을 최대 2개 동시에 준비하며 같은 버전/활동의 요청은 하나로 합친다. 실패한 배포 결과는 새 출발 때 재시도할 수 있다.

현재 최종 빌드는 `artifact.json`, 최종 targeted 결과는 `final-targeted-gate.json`에 기록했다. 실제 재시작에서 `Cached base pack predates activity input fingerprints`로 이전 캐시를 거부하고 MISS → 새 생성으로 진행한 것을 확인했다.

## 최종 실화면 수락 · 정리

최종 JAR SHA-256: `6c4ee56ba77db8ec26cd8982835dbef79397ead16ec6eded5714115324aa0eda`.

- 최종 공용 ZIP **132,028,042바이트**, SHA-1 `b6b4e11fc30f9bf31bdee9a2b5d2419eec57c7f7`. 전용 입력 269개 지문이 포함됐다.
- 악마의 소굴 **53,630,561바이트**, 엑소더스 **25,628,970바이트**. 두 전용 ZIP의 해시가 첫 미디어 무변경 감사와 같아 같은 바이트 검증이 적용된다.
- 지문 있는 새 ZIP/전용 세트는 실제 재시작에서 **cache HIT**로 복원됐다. `fingerprinted-cache-hit.txt`.
- 최종 빌드로 다시 지연 다운로드 중 취소 → 타워 유지, 엑소더스 입장/퇴장, 악마의 소굴 팩 준비 실패 → 복구 후 새 출발 성공 → 퇴장을 확인했다. 최종 준비 실패는 격리 manifest를 잠시 숨기는 fixture이며 복구했다. 첫 검사에서의 HTTP 503 다운로드 실패와 별개다.
- 모든 최종 native 입력은 `backgroundMode=true`, `backgroundActive=true`이며 게임 창이 실제로 `windowActive=false`인 상태였다. 입력 해제/heldKeys/pendingSteps도 확인했다.
- 두 전용 팩을 모두 해제한 뒤 최종 클라이언트 팩 스택에는 같은 공용 UUID 하나만 남았다. `final-client-pack-stack.txt`.
- 최종 타워 화면에서 screen/overlay 없음, leaseActive false, heldKeys 빈 배열, pendingSteps 0. `final-accepted-neutral.json`.
- 최종 master의 awake 상한은 3600초였다. 소유 master/client/server/proxy와 awake assertion PID가 모두 종료됐고 8102/25638/25639가 닫혔다. `cleanup.json`. 이전 master도 종료됐다.

실행기 준비 과정에서 클라이언트가 서버보다 먼저 접속해 거절된 시도, 재시작 시 종료 직후 포트가 잠시 남은 시도가 있었다. 이때 native 입력은 not_in_world로 차단됐고 기능 수락에 포함하지 않았다. 서버 포트 준비 후 클라이언트를 시작하고 소유 포트 종료를 기다리도록 QA 실행기를 보정한 뒤 위 최종 시나리오를 완료했다.

최종 8개 수락 조건과 실제 좌표/화면 전이는 `native-validation.json` 및 `final-*-timeline.json`에 있다. 소유권 보강/이전 캐시 거부 뒤 25개 targeted 검사를 실행했고, 소스·팩·런타임을 더 바꾸지 않고 이 최종 실화면 검사를 수행했다.
