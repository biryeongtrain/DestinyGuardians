# 탑 고스트 안내 채팅 버튼 수정

문제: 첫 안내에서 `[ 나중에 ]`를 누르면 알 수 없는 명령 오류가 났다. `/안내`의 항목을 `StringArgumentType.word()`로 읽고 있었으며, Brigadier 1.3.11의 unquoted word는 ASCII 영숫자와 `_-.+`만 허용한다. 버튼이 보내는 `시작`, `나중에`와 네 주제 모두 이 경로에서 해석되지 않았다.

수정: `/안내`, `/guide`의 여덟 항목을 각각 literal로 등록했다. 나중에 선택은 활성 세션 유무와 관계없이 미루기 확인을 보내며, 기존 완료·일회성 선물 비트를 보존하고 초대를 다시 띄우지 않는다. `/안내` 또는 기존 시작 버튼으로 다시 시작할 수 있다.

## 검증

- `compileGameTestJava`: 성공.
- 격리 서버 GameTest **3/3 통과**, 실제 시험 시간 1.850초. 실제 프로필 그래프 준비 156,259ms 뒤 시험 시계를 시작했다. `gametest-result.txt`.
- 일반 플레이어의 두 명령 별칭, 여덟 한글 항목, 잘못된 항목·추가 인자 거부를 확인했다.
- 실제 서버가 보낸 초대 컴포넌트에서 두 `RunCommand`를 추출하고, 클라이언트 클릭 명령과 같은 `ServerboundChatCommandPacket` 처리 경로로 미루기·재시작을 확인했다. 미루기 응답, 재초대 억제, 완료·선물 비트 보존도 확인했다.
- 완료 후 실제 다시 보기 메뉴의 네 버튼 명령을 추출해 실행하고 완료 기록 보존과 활성 안내 종료를 확인했다.
- 전체 JUnit 결과는 `full-gate.json`, 실제 Gradle 생성 JAR와 포함된 `Guide.class` 일치는 `artifact.json`에 기록했다. 기존 UI 폰트 작업의 전체 검사 결과를 비교 기준으로 삼았다.
- 전체 JUnit은 **2,842개 중 3개 실패**, 이전과 같은 `FireVariantsW98Test`의 기존 음원 자료 누락, `GoldenGunHudW122AssetTest`의 기존 검사 소스 누락, `MinorPveBalanceW342Test`의 기존 피해량 기대값 불일치다. 이번 수정의 새 실패는 없지만 전체 검사를 통과한 것으로 표시하지 않는다. JAR 단독 작업도 별도로 확인했다.

이번 검증은 실제 서버 명령·패킷 처리 검증이다. 클라이언트에서 마우스로 채팅 버튼을 누르는 시각 검증은 수행하지 않았다. 일반 Minecraft 프로필이나 사용자 월드를 열지 않았다.

## 실행·정리

임시 실행 폴더는 `/tmp/tower-guide-click-qa/gametest`, 필터는 `destiny-test:guide_command_game_tests*`다. 초기 실행에서는 JavaExec `workingDir`만 지정한 설정이 Loom에 의해 덮여 기존 개발용 GameTest 폴더가 선택됐다. 시험 시작 전 해당 소유 프로세스를 종료했고(exit 143), Loom의 `gameTest` runDir까지 별도로 지정한 새 격리 폴더에서 최종 3개 시험을 통과했다. 최종 실행은 `keep_awake.py --seconds 1200`으로 감쌌으며, 서버와 해당 잠자기 방지 프로세스가 종료됐음을 확인했다. Vision 클라이언트는 실행하지 않았다.

재현 명령: `./gradlew --no-daemon runGameTest -I /tmp/tower-guide-click-qa/gametest.init.gradle --console=plain`. 임시 초기화 설정은 다음과 같다.

```groovy
gradle.projectsEvaluated {
    rootProject.loom.runs.each { run ->
        if (run.name == "gameTest") run.runDir "/tmp/tower-guide-click-qa/gametest"
    }
    rootProject.tasks.named("runGameTest") {
        systemProperty "fabric-api.gametest.filter", "destiny-test:guide_command_game_tests*"
        systemProperty "destiny.gametest.packTimeoutSeconds", "600"
    }
}
```
