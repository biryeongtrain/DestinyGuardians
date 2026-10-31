# W281 튜토리얼 표시 결함·전체 계정 1회 진입

## 최종 변경
- 고스트 atlas를 `textures/item/tutorial/ghost.png`로 옮겼다. Minecraft26.3 items atlas는 `item/`을 수집하므로 이전 `textures/tutorial/` 경로는 missing texture였다. 모델·생성기·회귀 검사도 수정했다.
- ItemDisplayRenderer의 기본 Y축 180도 회전을 보정해 눈이 플레이어를 향한다. 눈은 밝기15, 셸은10/12로 표시한다. 11개 display/902요소, 2tick 업데이트·보간을 유지한다.
- TextDisplay 반투명 배경을 제거해 사용자 스크린샷의 문자 시트 격자가 사라진 것을 실화면으로 확인했다. 정확한 클라이언트 셰이더 원인은 확정하지 않았다. 선택 이름은 눈높이를 피하도록 높이2.6/scale0.85, 아이콘은 높이3.4에 둔다.
- 영속 attachment `tutorial_completed_revision` 요구 버전1. 직업/접속 이력/이전 boolean 완료 여부와 무관하게 다음 접속 때 한 번 진입한다. 포털 완료 시1을 저장하고 이후 자동 진입하지 않는다. 중도 나가기는 완료로 세지 않는다. 기존 boolean은 유지한다.

## 실제 게임 검증 — Full Access 전환 후
사용자 지정 `copper-golem-vision-client-fabric-26-3`의 runtime/input-control 참조. 사용자가 격리 백그라운드 QA를 명시적으로 허용했다. 일반 프로필·월드는 조작하지 않았다.

- 서버: `/tmp/destiny-w281-server`, 신규 격리 월드 `w281-qa`, loopback25581, 오프라인 테스트 계정 MinigameQA. 클라이언트: `/tmp/destiny-w281-vision`, Vision8102, 26.3, HUD 표시, 한국어. GCB 없는 클라이언트이므로 Shift 조합 안내도 화면에 보인다.
- Java25/Gradle 산출 클래스로 실행하고 Polymer 팩 생성·클라이언트 로드를 확인했다. actual framebuffer PNG를 직접 열어 검수했다. OS/CU 접근 성공이나 음성 청취로 대신 보고하지 않는다.
- `01-awaken.png`: 첫 실제 실행. missing texture는 없어졌지만 눈이 반대여서 회전을 추가 보정했다.
- `02-legacy-awaken.png`: 이전 완료 boolean=true, class=hunter, revision 없음, 플레이 이력12000인 테스트 계정이 자동으로 tutorial에 진입. 눈·셸 표시 정상. `legacy-fixture.snbt` 참조.
- `native-walk.json`, `native-class.json`, `native-light-route.json`: native KeyMapping 이동으로 걷기·헌터 선택·빛 선택 방 접근. `03-class.png`에서는 근접 이름 가림이 남아 있어 이후 높이를 보정했다. `05-light-hall.png`에서는 깨진 격자 없이 솔라 아이콘·이름·여행자 파편·고스트를 확인했다.
- 완료 검증은 관리자 명령으로 ASCEND 단계와 포털 앞 위치만 설정한 뒤 전진 입력13tick으로 포털을 통과했다. 전체14단계 직접 플레이 통과가 아니다. 타워 전환 시 입력 runner가 `409 player_or_level_changed`로 lease를 중단했다. `finish-state.json`의 tower/heldKeys=[]와 `completed-fixture.snbt`의 revision1을 확인했다. `06-finish-tower.png` 참조.
- 서버와 클라이언트를 모두 종료하고 최종 표시 수정본으로 재시작했다. `rejoin-state.json`과 `07-rejoin-tower.png`: 완료 계정이 타워에 접속하며 튜토리얼이 자동 재시작되지 않는다. 이어 `/튜토리얼` 수동 재실행과 관리자 CLASS fixture에서 최종 안내판을 다시 검수했다. `08-final-class-selection.png`에서 근접 이름 가림이 없어졌고, `10-final-light-ghost.png`에서 최종 안내판·고스트를 확인했다. `native-final-light-selection.json`은 전진·정지로 솔라를 선택해 EQUIP로 진행한 결과다 (`11-final-equip.png`).

## 빌드와 테스트
- 초기 sandbox 상태에서는 Java 소스520개 직접 컴파일, targeted7개 통과, 수동 ZIP64 JAR 생성까지 했다. 현재 배포용 파일은 그 수동 JAR을 **최종 Gradle jar 산출물로 교체**했다.
- 최종 명령: Java25 `./gradlew test --tests '*TutorialGhostW280Test' --tests '*SoundAssetsW33Test' jar`. 7개 통과, JAR 생성 성공. `rebuild-final.log`, `build-artifact.json` 참조.
- 별도 전체 `build`의 `runGameTest`는 **101개 required test 실패**로 종료101. `gradle-build.log`에 HUD offhand cast/null, jump audio, weapon reload timing, solar camera 등의 실패가 있다. 변경 전 baseline 비교를 하지 않았으므로 기존 실패나 이번 변경과 무관하다고 단정하지 않는다. 전체 gate 통과로 수락하지 않는다.

## 실패와 검증 한계
- Full Access 전 초기 실행은 loopback bind `Operation not permitted`, SDL display 없음으로 exit255였다. `vision-launch.log`, `vision-crash.txt`는 그 실패를 보존한 기록이다. 이후 권한 변경으로 실제 클라이언트 실행은 가능해졌다. CU Finder preflight는 별도로 승인 거부가 계속되어 OS 잠금 검증 성공이라고 하지 않는다.
- 첫 서버는 non-PTY stdin이라 console을 사용할 수 없었고 TERM 후 shutdown 지연으로 소유 프로세스만 강제 종료했다. 이후 PTY 서버는 console stop으로 정상 종료했다.
- 한 번의 QA fixture에서 `tp`에 `at @s`를 빠뜨려 overworld로 이동·낙사했다. 제품 버그로 판정하지 않는다. 격리 서버 immediate_respawn 설정 및 Vision screen close로 복구한 뒤 올바른 차원에서 재검증했다. `native-finish.json`에 기록했다.
- 음원15개+처프3개 연결·파일/팩 검사는 했으나 실제 스피커 청취, 모든 능력 키 입력, 14단계 전 구간 재통과, 다중 플레이어 격리, 10~20고스트 부하 검증은 하지 않았다. 상용 품질/성능 인증으로 보고하지 않는다.
- `keep_awake.py --seconds 3600` master coordinator가 재시작 사이도 유지했다. 최종 cleanup은 아래 기록한다.

## 최종 cleanup
- `final-input-release.json`: leaseActive=false, heldKeys=[], pendingSteps=0. 수동 재실행 튜토리얼을 나가 타워로 복귀한 뒤 저장했다.
- 소유 최종 클라이언트 PID90486 TERM, PTY 서버 console stop으로 종료. 마지막 server/client 로그를 복사했다. master coordinator stop flag로 자신의 awake assertion만 해제했다. 일반 프로필·외부 원본·타인 프로세스는 변경하지 않았다.
- 관리자 fixture에서 AWAKEN→CLASS 직접 skip하면 각성 anchor가 남아 고스트가 뒤에 머문다 (`08`, `09`). 정상 WALK를 거친 경우에는 해제된다. 마지막 비교는 WALK→LIGHT fixture로 같은 정상 조건을 만들었다. 이 관리자 skip 동작 자체는 이번 제품 수정에 포함하지 않았다.
