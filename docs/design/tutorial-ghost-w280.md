# W280–W281 튜토리얼 고스트·음성

2026-10-31. W279 위에 적용한 변경. 기존 봉인 QA를 수정하지 않았다.

## 전달 자료와 모델
다운로드 폴더의 중첩 `Destiny-Ghost-Tutorial-2026-10-31/Destiny-Ghost-Tutorial-2026-10-31`을 읽기 전용으로 사용했다. 선택 음원 18개와 blend의 SHA256을 전달 FILE-HASHES.json과 대조했다. 원본 blend는 별도 background Blender에서 열고 idle 액션/슬롯의 실제 평가 메시를 사용했다. 사용자 앱 scene은 조작하지 않았다.

Generalist Shell의 셸 8개, 내부 코어 2개, 발광 눈 1개를 11개 item display로 변환했다. 원본 루트 이동을 제거하고 코어→눈 방향을 모델 전방으로 정렬했다. 총 902개 native triangle 출력 요소, 2048px 단일 alpha atlas. 알베도는 감소된 삼각면별 샘플 색으로 근사했으며 normal/gstack·안료 셰이더·원본 세부 질감의 완전 재현은 아니다. 눈은 밝기15, 셸은 W281에서 밝기10/12 하한을 적용했다. W281은 native item atlas 경로와 기본 Y축180도 회전도 보정했다.

코드 부유와 말하는 동안의 완만한 방사형 셸 벌림을 사용한다. 원본 open/close 액션 재생이라고 주장하지 않는다. 약 0.6블록 폭으로 사용하며 기존 어깨 앞 위치와 시선 추적을 유지한다. owner 전용 관전자 관리, 자동 holder tick 해제, 2tick 간격 업데이트와 보간을 적용했다. 엔티티/기하량은 정적 예산이며 실측 FPS 인증은 아니다.

## 음성
원음 15개: 각성, 이동, 직업별 선택 3개, 빛, 장비, 사격 경고, 사격 칭찬, 도약, 능력 성공 3개, 궁극기 충전, 마지막 전설 대사. 추가로 ghost_link_tickle 처프 3개. 재장전과 능력 조작 전용 원음은 자료에 없어 기존 무성 안내를 유지한다. 원음 자막은 전달 한국어 문자열을 사용한다.

선택 WAV만 mono 48kHz Vorbis q4로 변환했다. 길이 자르기 없이 loudnorm I=-19/TP=-2/LRA=7 적용. 음성 15개는 stream, 짧은 처프는 비스트리밍. 총 OGG 538400 bytes. 모델·아이템·atlas·음원 41개 파일 합계 1124352 bytes (중앙 sounds.json 및 메타데이터 제외).

음성은 owner에게만 entity sound packet으로 보내 이동 중에도 owner를 따라간다. 활성 원음은 정상 단계 전환에서 끝까지 재생하고, 다음 대사는 대기한다. 오래된 미재생 안내는 제거한다. 강제 단계 이동·완료·종료 시 해당 음성 ID만 stop하며 다른 소리는 건드리지 않는다. 원음이 없는 안내에는 개인 처프가 재생된다.

## 재생성
- 모델: Blender background에서 전달 blend를 열고 `scripts/build_tutorial_ghost_w280.py` 실행.
- 음원: `python3 scripts/audio/build_tutorial_w280.py` (스크립트의 전달 경로와 기존 FFmpeg 경로 사용).
- 검토 렌더: Blender background factory scene에서 `scripts/qa/render_ghost_w280.py` 실행. 실제 생성된 native model JSON/atlas를 재구성한 Blender 렌더이며 Minecraft 캡처가 아니다.
- 출처·변환 manifest: `art/ghost/w280/`.

## 검증과 수락 조건
`docs/qa/2026-10-31/w280/README.md` 참고. Java 직접 컴파일 및 targeted JUnit 6개 통과. 이 기록 당시에는 인게임 수락 전이었다. 이후 실제 클라이언트 검증·최종 Gradle 빌드·전체 gate 실패는 `docs/qa/2026-10-31/w281/README.md`에 기록했다. 모델 실루엣·크기·눈·셸 동작·ADS 가림·음성 청취와 이동 시 음성 위치·조기 단계 전환·종료·재시작·동시 플레이어 격리를 격리 client/server에서 확인해야 한다. 10~20개 표시 시 눈에 띄는 깨짐/끊김도 미검증이다. 상용 게임 수준의 품질이나 최적화를 검증 완료했다고 볼 수 없다.

전달 `README.md`와 `VALIDATION.json`은 영어 원음만 포함하며 한국어는 자막 CSV라고 명시한다. 한국어 더빙 파일은 이번 전달본에 없다.
