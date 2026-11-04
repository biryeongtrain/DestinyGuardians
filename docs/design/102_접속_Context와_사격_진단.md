# W87 — 접속 PacketContext와 사격 진단

[검증 결과](../qa/2026-10-25/w87/README.md) · [Ace 독립 분석](../qa/2026-10-25/w87/ace-analysis.md)

## 원칙

원작 무기 피해·탄약·장거리 안전 정책을 시험에 맞춰 바꾸지 않는다. W86의 HUD·무기·음향·모든 클라이언트 자산과 실제 서버 JAR는 그대로 보존한다. 발견된 문제가 테스트 환경에서 비롯됐으면 생산 기능 수정으로 표현하지 않는다.

## 시네마틱 청크 경고의 실제 원인

Polymer 0.18.4+26.3의 `PlayerChunkSenderMixin`은 이미 대상 connection의 PacketContext를 사용한다. 따라서 CameraViews의 scope 누락이라는 초기 가설은 틀렸다.

같은 경고를 내는 `BlockEntityInfoMixin`에는 두 분기가 있다.

1. 현재 PacketContext가 없다.
2. Context는 있지만 `REGISTRY_ACCESS`가 없다.

Fabric networking 6.3.10은 실제 로그인 생성자에서 `SERVER_INSTANCE`와 `REGISTRY_ACCESS`, 로그인 검증에서 `GAME_PROFILE`을 연결한다. 기존 embedded PLAY fixture는 이 과정을 생략해 `CONNECTION`만 있던 상태다. 실제 BE가 있는 청크를 전송하면 두 번째 분기에 들어간다.

`TestPacketContexts.initialize`는 폐기 가능한 테스트 connection에 한해 같은 서버·레지스트리·프로필 identity를 설정한다. 기존 다른 identity가 있으면 덮어쓰지 않고 실패한다. 전역 scope, 가짜 레지스트리, production fallback 또는 인증 우회를 만들지 않는다. Fabric의 공개 ReadKey가 실제 Key인 현재 버전을 검사하며 API 변경 시 조용히 통과하지 않는다.

실제 로그인 생성자를 호출하는 별도 negative control은 생성자 전/후의 원래 동일 Context를 관측한다. 이것은 인증·실제 클라이언트 로그인 성공을 뜻하지 않는다. 다른 시험은 두 connection의 중첩/예외 scope 복구와 실제 CameraViews.tick → PlayerChunkSender → chest BE 포함 chunk/light packet의 native codec round trip을 검사한다.

## Ace 장거리 사격 진단

W86 Gate2에서 유료 발사는 승인됐지만 먼 Husk의 HP가1000으로 남았다. 과거 로그에는 실제 선택 target/guarded endpoint가 없어 유일한 원인을 복원할 수 없다. 원인 해결·역사적 실패 재현으로 표시하지 않는다.

W86에 추가했던 진단에도 실제 차이가 있었다. `shot()`은 조준 상태와 pitch/yaw를 reset하는데 진단은 그 전의 ray를 읽었고, 직접 entity query로 production block clip·wall tie 정책을 생략했다.

W87은 **reset 직후, beginUse 직전**에 원래 private `loadedEnd`와 `trace`를 읽기 전용으로 관측한다. 실제 emission/탄약 지급/시계를 호출하거나 바꾸지 않는다. 실패하면 eye, normalized direction, full/guarded endpoint, hit type/location, expected UUID/AABB, selected UUID를 함께 남긴다. 원래 실제 HP·.85거리·.33 floor·1.68배율·실탄·Mori6→5 assertion은 그대로다.

두 controlled 회귀를 추가했다.

- 같은 ray에 가까운 적을 넣으면 실제 유료 사격은 가까운 적에게만 피해를 주고 먼 적은 그대로 남는다. 이는 기존 `first != null`만으로는 충분하지 않음을 보이며, 과거 Gate2에도 그 적이 있었다는 증거는 아니다.
- 서로 다른 z의 네 clear corridor에서 실제 처치 →55tick full reload →65tick 유료 원거리 사격을 수행한다. 강제 chunk load·EPS/AABB 확대·재시도 없이 원래 falloff 피해를 확인한다.

## 남은 일

역사적 Gate2 원인은 여전히 미확정이다. 다시 실패하면 이번 동일 경로 진단으로 trace 선택과 native damage admission을 먼저 분류한다. 안정성을 가장하려고 실패를 지우거나 생산 guard/피해를 약화하지 않는다.

Vision 실화면/입력·회전 부호/크기·원작 체감, 원작 모델·음향·전용 모션과 남은 무기 특성/다인 부하는 별도 미완료다. 이번 headless 검증을 전체 목표 완료로 취급하지 않는다.
