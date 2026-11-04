# W107 — native use/release·탄약 동시 진단

## 목적과 변경 경계

W106의 준비 후 짧은 입력은 기대40 대신39였고, 이후 추가22 sound dispatch와41 endpoint도 충분히 설명되지 않았다. 이를 감추거나 자동 무기를 무조건1발로 제한하지 않는다. 실제 client 송신·server 수신·탄약 결제·release를 함께 기록할 수 있도록 **기본 꺼짐인 관측기**만 추가한다. 발사 cadence, Handling gate, 장전, 파지별 입력 lease는 그대로다.

서버는 `-Ddestiny.weapon.useTrace=true`와 `-Ddestiny.weapon.useTrace.player=<정확한 QA 이름>`을 모두 요구한다. `WeaponUseTrace`는 기존 runtime과 현재 mainhand의 읽기 전용 projection만 기록하며 상태 생성·binding·clock 진행·패킷 전송을 하지 않는다. 패킷 관측은26.3 실제 `ensureRunningOnSameThread(...ServerLevel)` 직후다. `WeaponRuntime`의 begin/release/paid/tick에도 void 관측만 붙였다. 프로세스당4096행으로 제한하고 무제한 저장·백그라운드 writer를 만들지 않는다.

Vision Client도 `-PvisionUseTrace=true`가 명시된 경우에만 활성화하며, 기존 native control opt-in과 정확한 QA 서버·client thread·현재 listener를 추가로 확인한다. 실제 listener send RETURN의 use/release, inventory handler RETURN, 기존 virtual query의 반환값, raw key mapping을 관측한다. 입력 query를 새로 호출하거나 lease를 만료/소비시키지 않는다. 별도4096행 상한이다.

## 해석 제한

- client `USE_SENT`는 local send 반환이지 ACK/서버 결제가 아니다. inventory handler 반환도 적용 성공의 보장은 아니다.
- release packet sequence는 바닐라0이므로 use sequence와 같다고 만들지 않고 시간순으로 대조한다. client/server tick은 서로 다른 시계다.
- 기존 cancellable action router와 injection 상대 순서는 확정하지 않았다. 이번 실제 release 행은 확인했지만 Q/F 등의 전체 action coverage를 주장하지 않는다. use-on-block/entity 패킷도 범위 밖이다.
- 동기 로그는 비용이0이 아니고 타이밍에 영향을 줄 수 있다. 관측 아래의 새 통과가 이전 무계측 실패를 설명하지 않는다.
- held identity는 `identityHashCode`라 영구적 고유 ID가 아니다. 같은 실행의 같은 fixture 구간에서만 corroboration으로 쓴다.

## 현재 검증

서버 **869 GameTest/760 JUnit 강제2회**, Vision **52 JUnit/31 Node**, 잠자기 helper **6 운영 테스트**를 통과했다. 기존754 JUnit에 trace 계약6개만 추가했고 GameTest/리소스팩은 변경하지 않았다.

격리 Vision에서는7개 native sequence와15PNG를 남겼다. 짧은 native 입력은 중간 캡처 off/on 각각41→40, 같은 stack의 빈장전 후 별도 fresh 입력은 native0→41→40 / two-hand0→41→37, native10client-tick hold는41→33이었다. two-hand는 기존6server-tick lease로 여러 발이 가능하므로 최종40을 억지로 요구하지 않는다. 이번 결과는 현재 입력 경계의 제한 수락이지 W106 원인 해결 선언이 아니다. paired capture 두 경우가 모두40이므로 screenshot이 원인이었다는 주장도 하지 않는다.

## 운영과 후속

QA에는 bounded `scripts/qa/keep_awake.py`를 적용했다. 실제 assertion 소유 PID99786과 시작/종료 기록을 남기고 종료 후 자기 assertion만 해제했다. 앞으로도 repo `AGENTS.md`의 필수 wrapper 규칙을 따른다. 암호·인증·자동 잠금 보안 설정은 바꾸지 않으며 수동 잠금/덮개/OS 정책까지 막는 보장은 없다.

W106 원래 실패는 그대로 보존한다. 다음은 다른 무기·파지·교체/장전 입력 경계를 이 관측기로 확장하고, 재현되는 문제에 한해 원인에 맞는 제품 수정을 한다. 이전 HUD/활 표현·청취·다인/성능 미검증도 유지한다. 전체 무기/HUD 목표는 active다.

[실행 증거·감사](../qa/2026-10-25/w107/README.md) · [native 로그 대조](../qa/2026-10-25/w107/native-trace-review.md) · [화면 검토](../qa/2026-10-25/w107/native-visual-review.md) · [잠자기 방지](../qa/KEEP_AWAKE.md).
