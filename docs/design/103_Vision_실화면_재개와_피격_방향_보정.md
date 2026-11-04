# W88 — Vision 실화면 재개와 피격 방향 보정

## 실제 화면에서 찾은 오류

사용자의 잠금 해제·화면 켜짐 확인 후 격리 QA를 재개했다. 이전 초기 SDL 정지는 이번 두 세션에서 재현되지 않았다. 이는 이전 정지의 원인이 확정됐다는 뜻은 아니다.

W86의 회전 축 수정은 맞았지만 방향 부호가 틀렸다. 실제 `displayhud_clip`은 **X축을 반전**한다. `-bearing`으로 Z 회전하면 오른쪽 공격이 화면 왼쪽에 표시된다. 실제 framebuffer에서 이를 재현하고 `+bearing`으로 고쳤다. `setRightRotation`의 첫 번째 인자가 Z라는 기존 보정은 유지한다.

- 기존 4방향 GameTest에 raw quaternion뿐 아니라 shader X mirror를 거친 texture 상단 anchor의 화면 좌표 검사를 추가했다.
- 변경 전 오른쪽 marker 중심은 화면 중심 대비 X=-89.85px, 변경 후 +88.86px다. 왼쪽은 +90.06→-91.06px다.
- 앞/뒤를 포함한 4방향 실제 PNG의 붉은 marker 픽셀 감사도 통과했다. 피해 흔들림과 flinch 때문에 정중앙 축에서 약간 벗어날 수 있다. 캡처는 state로 앞뒤를 감싼 것이며 정확한 서버 tick 동기화가 아니다.

## 검증 범위

동일 수정 JAR로 **755 required GameTest / 662 JUnit, 전체 강제 2회 통과**. 시험 수를 늘리거나 원래 피해·탄약 assert를 약화하지 않았다. 기존 6588 asset와 162 sound event, library와 Vision source는 변경하지 않았다.

수정 전/후 각각 Vision 실제 입력 7시나리오를 확인했다.

1. Ace: 정밀 처치/Firefly/빈 탄창 재장전으로 Mori6, 강화 몸통1발로5, 유료 빗나감5발로0, 일반 몸통 피해, ADS 무발사.
2. Salvo: 기본 양손 유지 중 미폭발, 해제 후 피해·벽 차폐, 유지 중 직접 적중 폭발, 각1발 지불과 재장전.
3. 모든 native sequence 뒤 lease/virtual/native 입력 중립을 확인했다. 방향 HUD의 피해는 서버 fixture 명령으로 만들었으며 플레이어 공격 입력의 증거라고 하지 않는다.

headless FOV=false 팩과 native FOV=true 팩은 구분한다. native 서버 팩과 실제 다운로드 cache는 byte-exact다. OpenAL 초기화·서버 sound event 로그는 청취 성공의 증거가 아니다.

## 남은 실제 결함

**낮은 체력의 붉은 주변부가 충분히 보이지 않는다.** HP5에서 top health bar는 붉어지지만 주변부는 두 캡처에서 확인되지 않았다. 독립 조사 결과 26.3 item alpha cutoff는0.1이며, HP5 pulse의 frame1/2는 모든 texel이 이 cutoff 미만이다. 이것은 사라지는 phase를 설명하지만 모든 phase의 native 원인을 확정하지는 않는다. 약1.2초 간격 두 캡처가24tick 주기에 겹쳤을 가능성도 있다.

잘못된 `render_type` 필드나 전역 shader override는 넣지 않았다. 다음 작업은 active alpha/frame envelope를 국소 보정하고 전체 pulse를 서로 다른 시점·HP로 캡처하는 것이다. 상단 bar가 표시된 것만으로 주변부까지 완료됐다고 보고하지 않는다.

일반 활 fatigue의 정확한 최대 유지/강제 발사 시간과 late damage/accuracy 곡선도 여전히 미확정이다. 새 공식 전문·현재 manifest/DDC/Clarity를 조사했으나 임의의4초 타이머는 추가하지 않았다. Oathkeeper의4초 피해 보너스 만료는 일반 활 강제발사 시간이 아니다.

## 추적

- [실제 PNG·native 입력·서버 결과·실패 보존](../qa/2026-10-25/w88/README.md)
- [주변부 독립 진단](../qa/2026-10-25/w88/critical-analysis.md)
- [활 추가 조사](../../art/weapons/w88/reference-notes.md)

QA 최초 fixture의26.3 item modifier key/ACK/gamerule 오류와 포커스 중단도 로그에 보존했다. 일반 world/profile, 사용자 Blender/Blockbench, 전역 MCP와 영구 전원 설정은 변경하지 않았다. 잠자기 방지는 각 검증에만 제한하고 종료했다. 전체 목표는 진행 중이다.
