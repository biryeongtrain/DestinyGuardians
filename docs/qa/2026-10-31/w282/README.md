# W282 고스트 한국어 음성

- 원본: `/Users/qf/Downloads/Destiny-Ghost-Korean-2026-10-31`, 읽기 전용. 기존 선택15개 모두 동일 dialogue/WEM 태그의 `locale=ko`, `decoded_non_silent` 파일에 대응한다. 파일 SHA256을 manifest-ko.csv와 FILE-HASHES.json 양쪽에 대조했다. 전체 전달물에 누락된2개 고유 태그는 이 선택에 없다.
- 대사15개를 한국어로 교체하고 비언어 처프3개는 기존 해시 그대로 유지했다. mono48kHz Vorbis q4, loudnorm -19LUFS/-2dBTP/LRA7, 자르거나 가속하지 않았다. OGG 전체 디코딩·비무음·원본 대비 길이 오차50ms 이내 확인. 총663144bytes, 이전보다124744bytes 증가.
- 각 자막 유지 시간은 한국어 PCM 길이의 ceil(seconds*20)+10tick. 워록9.288초/196tick, 헌터8.243초/175tick. 정상 단계 전환에서 현재 음성이 끝날 때까지 기다리는 기존 정책을 사용한다. 의미 유사 대사를 전용 능력 대사로 재분류하지 않았다.
- 재생성: `python3 scripts/audio/build_tutorial_ko_w282.py`. 전체 원본 선택을 먼저 검증하고 임시 디렉터리에서 인코딩·디코딩을 마친 후 제품 파일을 교체한다. 과거 W280 provenance는 보존하고 현재 pinned audio 검사는 `art/ghost/w282/audio-manifest.json`을 참조한다.

## 검사
- Java25 Gradle `test --tests '*TutorialGhostW280Test' --tests '*SoundAssetsW33Test' jar`: 7개 통과 및 JAR 생성 성공 (`build.log`, JUnit XML).
- 실제 JAR 안의18개 OGG 해시와 자막 JSON을 현재 manifest와 대조했다 (`build-artifact.json`).
- 이번은 음성 자산·대사 시간 교체여서 전체 GameTest를 반복하지 않았다. W281의 전체 gate101개 실패는 해결한 것으로 보고하지 않는다.

## 실화면 QA
기존 사용자 허용 범위의 격리 `/tmp/destiny-w281-server`와 `/tmp/destiny-w281-vision`을 재사용한다. Vision26.3 skill의 native/background 범위를 유지한다. 포트8102/25581이 비어 있음을 확인하고 시작했다. CU inventory는 조회했으나 앞선 세션의 OS 화면 접근 거부가 해결됐다고 주장하지 않는다. master keep_awake1800초로 전체 배치를 감쌌다.

실제 스피커 청취 및 원작 한국어 발음 대조는 미검증이다. 파일 해시·전체 디코딩·팩 로드·자막 화면 검증을 청취 증거로 대신하지 않는다.

- 서버 생성 팩18개 해시 대조 통과 (`generated-pack-hashes.json`). 클라이언트의 실제 downloads 캐시에서도15개 한국어/3개 처프 해시가 모두 일치하는 팩1개를 확인했다 (`client-pack-verification.json`). 로그에는 새 server pack ResourceManager 로드와 sound engine 시작이 기록됐다. 청취 결과는 아니다.
- 관리자 명령으로 WALK→CLASS 및 워록 원 앞 위치를 준비한 후, native 전진12tick/대기36tick으로 워록 선택. `native-warlock-selection.json` 및 `02-warlock-line.png`: LIGHT 단계로 진행하면서 워록 한국어 자막이 정상 표시된다. 실제 PNG를 열어 고스트·줄바꿈을 확인했다. 전체 튜토리얼 재통과는 하지 않았다.
- `final-state.json`: leaseActive=false, heldKeys=[], pendingSteps=0. 튜토리얼을 나가 저장한 뒤 소유 client PID96381 TERM, server console stop으로 정상 종료했다. master coordinator를 stop flag로 종료해 자신의 awake assertion을 정리했다. 다른 앱/일반 프로필은 변경하지 않았다.
