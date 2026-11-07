# W336 — R2 궁극기 대기·이동

R2 원본을 기준으로 9개 궁극기의 대기·이동 루프 41개를 적용했다. 스펙트럼 칼날은 사용자가 선택한 R2 `spectral_blades` 연결표를 사용한다. 이전 R1 결과와 ACC99940 지정은 대체됐으며 제품 입력에 섞지 않았다.

## 소스와 적용

읽기 전용 입력은 `/Users/qf/Downloads/Destiny-Super-Idle-Movement-2026-11-07-R2`이다. 전체 315개 파일의 크기·해시를 확인했다(`intake-integrity-r2.json`). 두 담당 에이전트가 별도 headless Blender로 실제 `Guardian_Super_Composed_R2.blend`의 105개 액션·72개 본과 선택한 합성 동작을 평가했다. 원본 행렬에는 rest가 이미 포함되어 있어 계층을 한 번만 합성했다.

R2에서 정정한 상태 그룹·32바이트 레이어 해석을 따른다. 불타는 망치의 group39 전신 additive와 6.8667초 대기 주기, 폭풍몰입·신성 차원의 실제 animated idle/move를 포함한다. 상체를 고정하던 R1 마스크는 폐기했다. 골반·몸통·쇄골·팔·손목·다리의 원본 움직임을 함께 리타게팅하고, 본 길이 차이와 기존 아이템 bind 축만 보정했다. 루트 XZ 이동은 서버 이동과 중복되지 않도록 내보내지 않는다.

지상은 전후좌우를 구분한다. 각 플레이백이 소유하는 방향 상태는 충돌 후 실제 위치 차이를 시선 기준으로 변환하며, 두 틱 연속 정지하면 대기로 돌아간다. 벽에 막힌 입력 의도로 걷기를 재생하지 않는다. floating 두 종류는 R2 공통 move를 사용한다. 시전·공격 단발 모션을 우선하고 종료 후 현재 이동 상태로 복귀한다.

원본 재생 주기와 기본 2틱 표시 보간을 유지했다. 기존 시전·공격·회피 소스 3개는 정확한 해시가 그대로다(`cast-attack-sources-preserved.json`). 사운드·공격 판정·강공격 60틱·전기 지팡이 회피 40틱·RMB 입력 전달·은신 로직은 변경하지 않았다. 새 로더는 R2 표시가 없는 데이터와 ACC로 연결된 Spectral 데이터를 거부한다. 모델 이름에는 새 리소스 해시를 넣어 기존 설치본 캐시를 재사용하지 않는다.

## 검증

실제 Gradle `assemble compileGametestJava` 후 별도 JVM에서 관련 8개 클래스의 단위 검사 45개를 통과했다. JAR CRC 및 새 리소스 2개·기존 모션 3개와 최종 소스의 바이트 일치를 확인했다. 정확한 명령·산출물 경로·해시는 `build-final-validation.json`에 있다.

실제 서버의 그룹 검사는 Arc/Spectral/Hammer의 같은 세션에서 네 방향, 정지, 벽 충돌, 공격 우선순위, 복귀, 장비·세션 정리를 검사한다. 초기 실패는 전체 공격 시간 내내 옆으로 이동시켜 테스트 통로의 바깥 경계에 도달한 배치 오류였다. 제품의 실제 정지 판정은 올바르게 idle을 선택했다. 기존 검사를 유지하면서 공격 첫 4프레임의 이동과 복귀 이동을 분리했고, 복귀 구간에는 실제 변위 검사도 추가했다. 초기 XML과 진단은 `initial-gametest.xml`, `initial-gametest-diagnosis.md`에 보존했다. 수정 후 실제 서버 재실행은 제품 그룹 검사 1개(세 세션)와 프레임워크 확인 1개 모두 통과했다. `gametest.xml`, `server-validation.json` 참조.

master가 격리 Vision native 입력으로 9종의 실제 PNG 시트를 직접 확인했다. Arc Staff, named Spectral, Fists of Havoc, Hammer of Sol, Sentinel Shield, Burning Maul, Stormtrance, Daybreak, Nova Warp가 대상이다. 대기 주기·전후좌우 이동·정지·공격 후 복귀를 확인했다. `master-png-review.json`은 화면 판정, `native-summary.json`은 실제 위치·입력 해제 상태, `native/`는 대표 이동 시트다. 전체 PNG와 상태는 `/tmp/w336-super-locomotion/qa/native`에 보존했다.

불타는 망치 첫 대기 검수 중 수동 F5가 감지되어 즉시 입력을 해제했다. 사용자의 입력 중단 응답 후 해당 케이스부터 새로 실행했다. 중단된 자료는 `/tmp/w336-super-locomotion/qa/interrupted-physical-input-maul`에 보존했다. 앞선 5종 결과는 덮어쓰지 않았다. Spectral은 기존 cast→LMB로 은신을 풀어 몸을 관찰했다. 긴 검수에서 자연 종료와 마지막 복귀가 겹친 Spectral/Shield는 새 궁극기를 쓰는 짧은 sequence로 다시 확인했다. 두 종류 모두 같은 궁극기가 살아 있는 상태에서 공격→이동→대기로 돌아오는 실제 화면을 확인했다.

샘플 화면에서 폭발적인 팔다리 변형·미싱 텍스처·분리된 소품은 관찰하지 못했다. 모든 프레임·각도의 무관통이나 손가락 접촉 보증은 아니다. 16본 블록 리그에는 독립 손가락·발가락이 없다. Arc/Fists는 후보 연결, Sentinel은 공유 방패 상태, floating weight1은 전달 패키지의 preview preset이다. 미해석 procedural·속도 가중치를 복원했다고 주장하지 않는다. GCB 클라이언트의 추가 프레임 보간은 구현·검수하지 않았다. FPS는 창 상태에 따라 20–99의 단발 스냅샷을 보였으며 프레임타임 분포·동일 조건 비교를 하지 않아 성능 또는 60fps 인증은 아니다. 이번 배치의 별도 사운드 청취 수락도 없다.

## 정리와 산출물

QA 종료 전 실제 현재 crossbow·플레이어 시점·HUD 복구와 virtual/native 중립을 확인했다. 자기 client Java PID만 종료하고 별도 Gradle daemon 그룹은 보존했다. 서버 정상 종료·8102/25610 포트 해제 뒤 임시 pause-when-empty 값을 60으로 복구했다(`native-cleanup-verified.json`).

배포 팩은 188,236,924바이트로 250,000,000바이트 목표 이내이며 CRC를 통과했다. 팩 해시는 이전과 같다. 새 애니메이션은 서버 포즈 데이터다. 최종 JAR은 `/Users/qf/IdeaProjects/DestinyGuardians/build/libs/destiny-guardians-0.1.0+26.3.jar`이며 실제 Gradle 산출물이다. 소스 담당의 delta/manifest에 있는 native pending은 반환 당시 상태이고, master의 최종 화면 판정은 이 문서와 `master-png-review.json`을 따른다.


최종 수락: 실제 Gradle 빌드·관련 단위 45개·실제 서버 그룹 검사·9종 실제 화면 검수 통과. 초기 실패와 수동 입력 중단 기록을 보존했다. 제품 변경 후속 수정 없이 테스트 배치만 고쳤으며, native 검수된 제품 소스와 JAR 해시는 그대로다.
