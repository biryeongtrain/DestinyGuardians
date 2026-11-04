# BetterModel 초기 리소스팩 생성 순서 (W121)

설치 기준 BetterModel3.5.1 / Polymer0.18.4+26.3. 초기 autohost 팩 IO reload와 동기 BetterModel SERVER_STARTED reload가 겹쳐 최초 팩이 실패하던 문제를 좁은 init-only redirect로 해결했다.

- 이미 구성 정책을 통과한 AutoHost.init 요청만 보류한다. 그 두 callsite cardinality는 require2/allow2와 bytecode regression으로 보호한다.
- DEFAULT 이후 SERVER_STARTED phase에서 public reload 결과 성공을 관측한 경우만 실행. 성공 미관측·실패·stop은 차단, 초기 요청은 coalesce. ready 이후 일반 init 요청은 원래 동작. 임의 sleep/main-thread wait/retry 없음.
- 명시 generate 명령, 임의 ResourcePackCreator 빌드, 다른 모드의 동시 reload까지 직렬화하는 API는 아니다. 실패 원인 해결 후 운영자 재생성은 별도다.
- 실제 cold(download)/warm 자동 생성·disabled 미생성, 정확7target bytes/atlas/part assembly 감사 완료. 기본 art 후보 opt-in은 유지하며 모델 source/HUD/sound는 바꾸지 않았다.
- source 형상 보존 회전 cuboid/alpha contour card와 raw mesh JSON 허용 여부를 혼동하지 않는다. native art·반복 FPS 수락은 다음 단계다.

[W121 증거 및 제한](../qa/2026-10-25/w121/README.md), [native 잔여](../qa/NATIVE_QUEUE.md).
