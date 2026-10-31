# W280 검증 기록 — 실화면 수락 대기

- 원본 확인: background Blender로 `.blend` 로드, idle 액션/slot 평가, 루트 이동·눈 방향 측정. `blender-inspect.log`, `model-build.log`.
- 무결성: 선택 음원18개와 blend가 전달 FILE-HASHES.json과 일치. `source-integrity.json`.
- 음원: 선택18개 모두 FFmpeg 전체 Vorbis decode 통과. 청취는 하지 않았다.
- 모델: 실제 Minecraft26.3 CuboidModel 파서가11개 모델/902요소 수용, atlas alpha/참조 검사 통과.
- 컴파일: 튜토리얼 패키지6개 Java 파일을 Java25 javac와 기존 runServer 의존성 classpath로 직접 컴파일, exit0. `javac.log`.
- 테스트: `TutorialGhostW280Test`2개 + 기존 `SoundAssetsW33Test`4개, 총6개 통과. 음원 기존 provenance 검사에 정확한 W280 manifest와 해시를 추가했다. `targeted-tests.log`.
- 코드 검토: 읽기 전용 worker가 지적한 고정 위치 음성, Polymer 관전자 누출, 자동/수동 holder 이중 tick을 수정하고 재컴파일했다.
- 렌더: `model-preview.png`는 생성 모델 JSON을 재구성한 Blender 렌더. 초기16px 삼각 마스크의 톱니를 보고64px로 확대했다. Minecraft PNG가 아니다.
- 일반 `gradlew compileJava`는 홈 캐시 lock 쓰기 거부. APFS CoW 임시 캐시를 준비했으나 Gradle FileLockContentionHandler 소켓 생성이 sandbox에서 거부됨 (`compile.log`). Gradle 전체 build/gate 통과로 보고하지 않는다.
- CU inventory는 반환됐으나 Finder 화면 확인 요청이 “Computer Use was not approved to use Finder”로 거부됐다. 따라서 잠금 상태 확인 불가. 보안 설정/인증을 우회하지 않았고 QA client/server를 실행하지 않았다. 8102 listener 조회는 비어 있었다.
- 실제 native 입력, client pack 로드, 화면/프레임 성능, 스피커 청취는 미검증. 이전 W279 결과로 대신 인증하지 않는다.
- 완료 커밋 없음. 기존 사용자 변경과 원본 보존. 임시 직접 컴파일 결과는 `/tmp/destiny-w280-classes`, 임시 Gradle cache는 `/tmp/destiny-w280-gradle`에 남겼다. 게임/awake 프로세스는 만들지 않았다.

## 사용자 요청 후 JAR 빌드

Gradle 실행 제한이 지속되어 Java25 `javac --release 25 -proc:none`으로 현재 main 소스519개 전체를 별도 출력 경로에 컴파일했다. 현재 리소스를 ZIP64 JAR로 패키징하고 fabric.mod.json의 버전을 치환했다. 기존 빌드의 nested dependency 목록을 유지하며 GCB/minigame-lib는 기존 로컬 빌드 JAR, 외부 의존성은 이전 Gradle 산출물의 JAR을 사용했다. 의존성 프로젝트 재빌드나 전체 Gradle build 통과를 뜻하지 않는다.

새 클래스 기준 targeted JUnit6개 통과 (`build-targeted-tests.log`). 산출물 정보·해시·검사 결과는 `build-artifact.json`. 기존 JAR은 보존한다. 이 패키징으로 인게임 QA 대기가 해소되지는 않는다.
