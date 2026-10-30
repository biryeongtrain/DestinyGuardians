# 배포 JAR 의존성 포함

사용자 요청으로 BetterModel과 minigame-lib에 Loom include를 추가했다. minigame-lib은 기존 composite build 소스를 사용한다. 기존 zip64 설정과 다른 미커밋 변경은 보존했다.

`./gradlew jar --offline --no-daemon --console=plain --max-workers=2` 성공. 결과 fabric.mod.json의 jars 목록에서 bettermodel/minigamelib을 확인했고 두 내장 JAR의 메타데이터와 하위 내장 JAR 경로도 확인했다. 게임 동작 변경은 없어 추가 실게임 검증이나 운영 서버 재시작은 하지 않았다. Fabric API·Polymer 등 나머지 외부 의존성 설치 방식은 기존과 같다.

파일 크기·버전·SHA-256은 [artifact.json](artifact.json)에 기록했다.
