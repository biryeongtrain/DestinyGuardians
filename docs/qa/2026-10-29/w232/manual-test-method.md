# W232 manualOnly GameTest 실행 조사 (read-only)

## 결론

Fabric API 0.164.0+26.3의 정확 모듈은 fabric-gametest-api-v1 4.0.34+3434d6d95d다. 이 버전과 Minecraft 26.3에서 headless runGameTest는 manualOnly=true 테스트를 **filter가 있어도 무조건 제외한다**. manualOnly를 허용하는 JVM 속성은 조사한 경로에 없다. tower enabled=true로 바꿔도 이 제외를 우회하지 못한다. 이전의 'explicit filter로 manualOnly를 실행'이라는 해석은 이 headless 경로에 적용되지 않는다.

GameTestServer.evaluateTestsToRun는 testSelection이 있는 분기에서도 getTestsForSelection(...).filter(test -> !test.value().manualOnly())를 호출한다. 전부 제외되면 Test selection matcher (...) found no tests를 출력하고 System.exit(-1)로 실패한다. 없는 분기도 같은 manualOnly 제외다. 따라서 0개 성공으로 수락하면 안 된다.

## 권장: 소스 변경 없이 일반 개발 서버 + 단일 /test run 순차

외부 init 파일 tower-manual-server.init.gradle을 준비했다. worker는 이 파일을 실행하거나 main을 수정하지 않았다. source와 bytecode로 구성을 대조했지만 Gradle 실행 검증은 하지 않은 조사 산출물이다.

이 파일은 기존 gameTest run config의 source set/classpath를 유지하고 fabric-api.gametest 키를 제거하여 headless 서버 대체를 끈다. destiny.tower.enabled=true로 설정하고 runDir/workingDir을 /private/tmp/destiny-w232/qa/manual-tower-run에 격리한다. 별도 일반 개발 서버로 시작하므로 GameTest 리소스/entrypoint가 계속 classpath에 있다.

주의: fabric-api.gametest=false가 아니라 **키 자체를 제거**해야 한다. FabricGameTestRunner.ENABLED는 Boolean.getBoolean이 아니라 System.getProperty(...) != null이다. JAVA_TOOL_OPTIONS/JDK_JAVA_OPTIONS/다른 init 스크립트로 이 키를 추가하지 않는다. 기존 central headless filter init과 이 파일을 함께 적용하지 않는다. 일반 개발 환경에서는 FAPI가 runner 비활성이어도 tests를 등록한다.

master 실행 형태(조사 중 실행하지 않음):

```sh
rtk proxy ./gradlew --no-daemon --console=plain -I /private/tmp/destiny-w232-world/manualonly-research/tower-manual-server.init.gradle -Pgcb_server_dir=<소유 격리 GCB 경로> runGameTest
```

위 작업은 이름이 runGameTest여도 일반 개발 서버다. master가 해당 격리 runDir에 이미 승인된 eula와 필요한 서버/모드 설정을 준비해야 한다. headless 모드의 EULA 자동 우회는 이 모드에서는 작동하지 않는다. 종료는 소유 서버 console의 stop으로 처리한다.

일반 개발 서버는 FabricGameTestModInitializer.onInitialize의 `FabricGameTestRunner.ENABLED || isDevelopmentEnvironment()` 조건으로 테스트를 등록한다. TestCommand.register의 `test run <tests>`는 ResourceSelectorArgument와 TestFinder.Builder.byResourceSelection을 사용하고, 그 경로에는 manualOnly 제외가 없다. TestCommand.toGameTestInfo도 구조물 존재/차원만 검사하고 manualOnly를 검사하지 않는다.

서버 console에 아래 명령을 **하나씩** 입력한다(console에서는 선행 / 생략). 다음 명령을 보내기 전에 해당 테스트 완료/성공을 확인한다.

1. `test run destiny-test:tower_w232game_tests_persistent_open_has_independent_rules_and_finite_sparse_generation`
2. `test run destiny-test:tower_w232game_tests_transfer_cleans_abilities_preserves_mode_and_protects_only_tower`
3. `test run destiny-test:tower_w232game_tests_blocked_arrival_is_rejected_without_repairing_the_map`

이 ID는 FAPI TestAnnotationLocator.java:129-131,187-188의 정확 알고리즘(class simple name + '_' + method name, `([a-z])([A-Z])` 치환 후 Locale.ROOT 소문자)과 provider modId destiny-test에서 계산했다. 232 뒤의 Game 앞에는 추가 밑줄이 생기지 않으므로 tower_w232_game_tests가 아니라 **tower_w232game_tests**다.

자동 console 조정기가 사용할 완료 조건: 각 요청 뒤 새 로그 범위에서 `Running 1 test(s)...`, `Game Test complete! 1 test(s) were run`, `All required tests passed :)`를 확인한 후 다음 ID를 보낸다. `No tests to run`, `required test(s) failed`, 해당 ID의 `failed at`는 실패다. 이 문자열은 정확 26.3 assets/minecraft/lang/en_us.json 및 TestCommand.TestSummaryDisplayer의 summary 호출에서 확인했다. 로그 locale/로거 포맷이 다르면 translation key에 대응하는 실제 출력을 확인한다. 성공 로그가 없는데 단순히 100틱 경과만으로 다음 테스트로 넘기지 않는다.

새 /test run은 TestCommand.run 첫 줄에서 stopTests()를 호출한다. 따라서 3명령을 같은 틱/함수/console batch에 연속 송신하면 앞 runner를 중단할 수 있다. 세 테스트는 공유 타워를 사용하며 마지막 테스트는 headroom fixture를 잠깐 수정하므로 wildcard로 한 번에 실행하지 않는다. testsPerRow=1은 배치 동시성을 1로 제한하는 옵션이 아니므로 순차 실행의 근거로 사용하지 않는다.

## headless 자동 종료/XML gate가 반드시 필요한 경우

제품/main 변경 없이 격리 QA 소스 사본에서 3개 annotation의 manualOnly만 false로 바꾼 **QA 전용 컴파일 산출물**을 만들고, 그 사본의 runGameTest JVM에 destiny.tower.enabled=true와 fabric-api.gametest.filter=<단일 정확 ID>, fabric-api.gametest.report-file=<각각 다른 XML 경로>를 전달하는 방법이 가능하다. 3개 프로세스를 순차 실행하면 테스트 동시 실행을 피한다. master가 이 QA 전용 사본 변환을 명시적으로 관리하고 원본 delta와 변경 차이를 기록해야 한다. worker는 해당 소스 변환/컴파일을 수행하지 않았다.

fabric-api.gametest.filter는 FAPI가 Minecraft GameTestServer.create로 전달하는 selector이고 임의 Java regex가 아니다. 정확 ID를 사용하는 것이 확실하다. fabric-api.gametest.verify=true는 선택 테스트를 rotation별 100회 반복하므로 이번 기본 gate에 쓰지 않는다. FAPI runner는 repeatCount를 0으로 고정하며 이 조사 범위에서 별도 repeat JVM 속성은 없다. 일반 Gradle -Dfoo는 실행 게임 JVM 전달이 보장되지 않으므로 Loom RunConfiguration.systemProperties/JVM 인자에 설정해야 한다.

## 근거 파일

- Maven FAPI 0.164.0+26.3 POM: fabric-gametest-api-v1=4.0.34+3434d6d95d.
- 정확 모듈 sources: fabric-gametest-api-v1-4.0.34+3434d6d95d-sources/net/fabricmc/fabric/impl/gametest/FabricGameTestRunner.java:58-61, TestAnnotationLocator.java:129-131,164-176,187-188, FabricGameTestModInitializer.java.
- 정확 모듈 GameTestSystemProperties: ENABLED, REPORT_FILE, FILTER, VERIFY 네 속성. manualOnly override 없음.
- Minecraft 26.3 캐시 minecraft-merged.jar를 javap 및 CFR 0.152로 읽기 전용 해석. decompiled/net/minecraft/gametest/framework/GameTestServer.java:164-188; TestCommand.java:207-219,255-269,301-310,381-387,523-535; TestFinder.java:120-121. javap 텍스트도 함께 보존하여 decompiler 출력과 대조했다.
- Loom 1.18.2 정확 sources: FabricApiTesting.java:95-101은 gameTest run config를 server에서 상속하고 fabric-api.gametest 키와 gameTest source set을 설정한다. RunConfiguration.java:58,73,101,137-150은 JVM/runDir API. LoomTasks.java:193-215는 config 생성 시 run<Task> 등록. RunGameTask.java:41은 standardInput=System.in.

읽기 전용 조사/산출물 저장만 수행했다. Gradle, Minecraft, GameTest를 실행하지 않았고 main/worker slot 파일을 추가 수정하지 않았다.
