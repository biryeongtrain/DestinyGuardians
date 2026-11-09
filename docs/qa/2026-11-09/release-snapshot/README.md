# 현재 작업 상태 보관·릴리스 검사 · 2026-11-09

사용자의 미커밋 변경 포함 요청에 따라 현재 DestinyGuardians 작업 폴더의 변경 949개 파일을 함께 보관한다. W327 무기 24종 카탈로그/생성·검토 자료, 퍽 확장·전투 연결·HUD·관련 회귀 검사 및 모델 변환 도구 변경을 포함한다. `.gitignore`로 제외된 런타임/캐시/빌드 폴더와 별도 저장소는 이 커밋의 대상이 아니다. 새 에셋은 기존 Git LFS 규칙을 따른다. 스크립트 3개의 끝 공백만 정리했으며 제품 로직을 추가 수정하지 않았다.

현재 전체 JUnit 2,838개에서 실패 3건을 확인했다. 실패는 이전 활동 팩 배치에서 확인했던 같은 세 메서드다: `MinorPveBalanceW342Test.directAbilityAndLightSuperMeetTheirTargetPools`, `GoldenGunHudW122AssetTest.dedicatedTransportPreservesTintAndOnlySuperSelectedBranchChanges`, `FireVariantsW98Test.inheritedAudioBytesAndExactlySixW98PlusSixteenW102ClipsFormClosedRuntimeInventory`. 각각 기존 피해 수치 불일치와 과거 QA/GameTest 파일 누락이며 전체 통과로 표현하지 않는다. 실제 결과는 `validation.json`에 있다.

기존 native triangle Python 검사 12개는 통과했다. 보관 대상 JSON 124개가 파싱되고 신규 파일에 자격 증명 패턴이나 심볼릭 링크가 없음을 확인했다. 테스트를 비활성화하거나 기대 수치를 변경하지 않았다.

공격전/팩/탐색기에 대한 기존 실제 화면 검증은 각 QA 기록의 범위대로 유효하다. 이번 저장 작업으로 새 무기·퍽 전체의 실전/시각 품질을 추가 수락한 것은 아니다. 기존 자료·미검증 범위도 함께 보관한다. 배포 JAR는 Java 25/Gradle 실제 빌드이며 별도 로컬 GCB-server 의존성을 포함한다. 그 의존성의 작업 상태와 내장 JAR 해시는 릴리스의 BUILD-INFO에 따로 기록한다.
