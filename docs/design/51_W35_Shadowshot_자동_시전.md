# W35 — Shadowshot 자동 발사

## 사용자 요구
발동 이후 추가 클릭 없이 영상처럼 준비→발사→활성화를 한 시퀀스로 실행한다.

## 서버 계약
`HunterSuper.activate`는 카메라·BetterModel limb·equipment·start 사운드 설치가 성공한 다음
Session.onActivated를 호출한다. Void만 여기서 기존 ShadowshotTiming.request와
ShadowshotLift/공격 애니메이션/draw 사운드를 시작한다. 생성자에서 먼저 발사 예약하지 않는다.
T+1..6 준비, T+7 화살1개와 fire, 이후 실제 충돌에서 impact와160틱 닻을 생성한다.
좌클릭은 Void 시전 타이밍에 관여하지 않으며 별도 장시간 aim 상태는 없다.
능력 세션은 release에서 완료되고 기존 animation/camera recovery는 계속 유지된다.

## 회귀 범위
무입력 release, 발사 전 취소, 클릭 spam, 중복 발동 거부, 실제 양손 장비 및 inventory 보존,
BetterModel draw/rest/recovery, 카메라 복원, 부양/지형, 착탄 약화·억제 및 sound packet.
[실행 증거](../qa/2026-10-23/w35/README.md). W34 음원은 그대로 사용한다.
