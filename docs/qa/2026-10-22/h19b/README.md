# H19B — 활 3인칭 방향과 drawn export 보정

2026-10-22 · `feat/hunter`, base `3278f5b` · MC26.3 / Java25 / BetterModel3.5.1 / Polymer0.18.4+26.3. Vision `e1ed588`은 변경하지 않았다.

## 수정

- 실제 MC26.3 왼손 display 변환은 JSON Y/Z 회전을 반전한다. 왼손 JSON Y+90, 오른손 Y−90으로 유효 Y−90을 맞췄다. rest/drawn의 grip·translation·scale은 유지했다.
- BB string index196을 runtime index196에 그대로 적용하던 결함을 고쳤다. runtime string은201이었다. 고유 bounds로 대응해 직선 시위만 제거하고 wisp를 보존한다.
- 새 시위/화살의 BB 픽셀 UV를 vanilla에 복사하던 결함을 고쳤다. 올바른 runtime faces의 0..16 UV를 재사용한다. BB 픽셀 UV와 편집용 group 구조도 유지한다.
- body rig/애니메이션·gameplay Java·발사7틱·카메라 offset은 변경하지 않았다. [설계/단계29](../../../design/29_H19B_활_3인칭_방향_보정.md).

## 검증

- [최종 빌드](final-build.txt): `runGameTest test build`, **GameTest104/104 · JUnit60/60**, 실패/오류/스킵0. [JUnit XML](junit/).
- 실제 `ItemTransform.apply(context.leftHand(), ...)`를 호출해 두 모델×두 손의 grip/nock/tip/shot 방향을 검사한다. [변환 수정 전 실패](regression-before.xml), [geometry 수정 전 실패](geometry-before.xml)를 보존했다.
- parser/handed bytecode는 `ItemTransform.javap.txt`, `LayerRenderState.javap.txt`. 독립 감사로 BetterModel LEFT_ITEM→THIRD_PERSON_LEFT_HAND와 추가180도 보정 없음도 확인했다.
- [validation](validation.json): JAR와 dev class84개·source asset142개 byte 동일, 생성 팩의 두 item definition/두 model 동일. scratch fixture에서 generator를 다시 실행해 BB/JSON byte 동일성과 group 전체 큐브 참조를 확인했다.

## 실제 화면 — 최종 새 JVM/팩

서버 명령은 hunter/void/energy/좌표 및 isolated display fixture에만 사용했다. 사격은 Vision의 인증 lease→KeyMapping overlay→native click/바닐라 패킷 경로다. **OS/CU가 아니며 HUD normalization은 하지 않았다.** 의도적인 background QA override를 사용했다.

| 확인 | 실제 증거 |
|---|---|
| 활 앞뒤 반전 수정 | [수정 전 PNG](before-ready.png) / [수정 후 PNG](after-ready.png) / [같은 영역 crop 비교](before-after-crop.png) |
| 당긴 시위와 장전 화살 | [최종 측면 PNG](after-drawn.png): 화살은 화면 왼쪽 발사 방향, V 시위는 몸 쪽. 손/머리에 가린 접점은 exact contact 통과로 해석하지 않는다 |
| 실제 발사/회복 | [측면 WebP](final-side.webp), [contact](final-side-contact.jpg), [발사 후 궤적 PNG](after-projectile.png), [capture times](final-side-frames.json) |
| owner 후방 카메라와 복원 | [WebP](final-owner.webp), [당김 PNG](after-owner-draw.png), [self 복원 PNG](after-owner-restored.png), [capture times](final-owner-frames.json) |
| 두 hand context의 drawn geometry | [isolated 실제 PNG](isolated-drawn-contexts.png): 두 V자 시위·화살이 표시되고 직선 시위는 사라짐. 오른쪽 개체가 LEFT_HAND, 왼쪽이 RIGHT_HAND이며 entity yaw180. 플레이어 손 접점 검증을 대신하지 않음 |

[최종 native report](final-native.json)는 completed/released, heldKeys/pendingSteps/nativeInput 중립을 기록한다. 원본은 `/tmp/destiny-h19b-frames/final-{side,owner}/`의 PNG이며 문서에 선택본과 WebP/contact를 보존했다. PNG 간격은 요청 .04초가 아니라 metadata 측정값을 따른다. 두 화면은 정확한 같은 tick에 동기화하지 않았다.

crop은1708×956 원본에서 동일 영역 `(650,320)-(1050,800)`만 잘라 캡션/여백을 더했다. 전후 rest 모델의 비슷한 회복 자세를 비교하며 exact animation frame 일치나 렌더링 편집물이 아니다. 튜토리얼 toast는 새 observer QA 디렉터리의 기본 UI다.

## 중간 실패와 남은 범위

- `pregeometry/`는 handed 변환만 고친 중간 JVM이다. 활 방향은 나아졌으나 drawn shape가 여전히 잘못되어 최종 geometry 인수 근거로 사용하지 않는다. `isolated-drawn-unaccepted.png`도 남겼다.
- 중간 `shot-native.json`은 준비를 별도 실행한 뒤 기다리는 동안 궁극기가 종료돼 self-camera에서 attack했다. 전송 completed를 궁극기 사격 성공으로 표현하지 않는다. 최종은 capture와 발동/사격 전체 시퀀스를 같은 shell에서 시작해 재검증했다.
- 최초 observer는 기본 VSync로 OpenGL swap에 멈췄고 다음 시도는 접근성 onboarding에 멈췄다. 자체 scratch options만 VSync/pause/onboarding을 조정해 재시작했다. 사용자 원본 옵션·다른 클라이언트·Blockbench를 종료하거나 수정하지 않았다.
- 기존 H19의 **5TPS animation/contact 비동기**, partial draw 접점 차이, 머리/손 가림은 이번 방향/export 수정으로 해결됐다고 주장하지 않는다. 실제 지연/여러 방향 조준·벽 근접·인증 스킨·OS 입력·다인 부하·원작 음향도 새 검증 범위 밖이다.
- Blockbench native preview나 공식 메시 사용을 주장하지 않는다. 기존 자체 저작 BB/JSON 재생성 경로다. client 로그의 기존 HUD missing-particle/end_of_frame 경고도 보존한다.

## 정리와 보존

[cleanup-native](cleanup-native.json), [서버 최종 로그](server-final.txt): 임시 display2개 제거, VFX0/beam0/camera false, Arc/energy0/스폰/낮·맑음·20TPS 복구, virtual/native 중립. 자체 서버 정상 stop exit0, 자체 actor/observer만 SIGTERM 종료. [cleanup](cleanup.json)에 포트 비점유를 기록한다.

설치 H15/H19 body·기존 H17 ZIP·원본 Vision options/September artifact·전역 MCP는 덮어쓰지 않았다. 보존 해시와 Vision clean 상태는 validation에 있다. 이번 JAR로 기존 H17 ZIP을 교체하지 않았다.
