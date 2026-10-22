# H19 — 공허 활 사격과 실제 카메라 이동

2026-10-22, `feat/hunter`, base `2731705`. Minecraft26.3 / Java25 / Fabric Loader0.20.1 / BetterModel3.5.1 / Polymer0.18.4+26.3.
테스트용 Vision은 별도 repo `feat/test-input-control`의 `e1ed588`이며 이번에 수정하지 않았다.

## 변경과 출처

- 왼손 지지/오른손 cheek draw, V자 시위+nocked arrow, .30초 시각 릴리스/.90초 회복 clip. 준비→raise→draw→hold→release→follow-through→ready.
- 실제 투사체는 primary 즉시가 아니라 **서버7틱**에 한 번 발생한다. 반복 primary는 draw를 재시작하거나 화살을 복제하지 않는다. cleanup은 pending shot을 취소한다.
- 새 `guardian_hunter_h19` 설치·에셋. H15와 아티스트 설치 파일을 덮어쓰지 않는다. 다른8개 clip/기존10개 ID와 스킨·갑옷 rig 유지.
- Void 어깨 카메라1.15m, Arc .45m, 공통 rear3m. Solar는 강제 카메라 없음.
- 실제 연결의 `tickPlayer`가 native 이동을 이전 좌표로 복원하던 문제를 카메라 소유 중 연결 bookkeeping만 갱신해 보정했다. travel 중복 호출이나 몸 teleport 추가 없음.
- [레퍼런스·설계28](../../../design/28_H19_궁극기_활_연출.md), [카메라 원인27](../../../design/27_H19_카메라_이동_작업.md).

Bungie의 [Void3.0 설명](https://www.bungie.net/7/en/News/article/51021), 워터마크가 있는 [Shadowshot 이미지](https://destiny.wiki.gallery/images/7/7e/Shadowshot.jpg)와 [후속 이미지](https://destiny.wiki.gallery/images/c/c6/Shadowshot2.jpg)를 참고한 자체 저작이다. 원본 메시/모캡/공식 스프라이트 추출물이 아니다. 연결된 공식 영상은 접근 제한으로 보지 못했다. Deadfall 단발을 유지하며 Moebius 다중 발사를 새로 구현하지 않았다.

## 자동 검증

- [최종 빌드](final-build.log): `runGameTest test build` 성공, **GameTest104/104 · JUnit59/59**, 실패/오류/스킵0. [JUnit XML](junit/).
- 새 테스트: draw1~6틱 유지/7틱 단발·중복 억제/cleanup 취소, full-chain wrist/nock/cheek FK와 전신/기존8개 clip 보존, bow2상태 리소스, Void 카메라 framing, 실제 connection wrapper를 거친 이동 누적/한 틱 대조/충돌/낙하/unowned.
- [정적 FK](static-fk.log): 완전 draw에서 접점 오차<.001 BB단위. 엔진 handed transform이나 화면 검증을 대신하지 않는다.
- 레이아웃 검사 통과. 구형 helper가26.3 JSON GameTest fixture 등록을 탐지하지 못한 경고1개. 실제104개 실행으로 구별한다.
- [초기 컴파일](initial-compile.log): Holder SoundEvent 수정 전. [초기 테스트](initial-tests.log)3개/[두 번째](second-tests.log)1개 실패는 즉시 발사/기존 짧은 회복을 기대하던 assertion이다. 새 계약으로 갱신하고 전체를 다시 통과시켰다. 통과한 것처럼 초기 로그를 지우지 않았다.

## 실제 PNG / native 입력 — 최종 JVM

인증 HTTP + Vision `KeyMapping` overlay→native consumer→바닐라 패킷 경로다. **OS/CU 입력이 아니며 서버 `/guardian action`을 실제 클릭 증거로 사용하지 않았다.** 서버 명령은 class/energy/위치 등 fixture 준비와 진단에만 썼다. HUD normalization 없음. 의도적인 background QA override 사용으로 물리 focus 검증도 아니다.

| 확인 | 증거 | 범위 |
|---|---|---|
| 공허 준비/당김/회복/복원 | [20TPS WebP](void-normal.webp), [contact](void-normal-contact.jpg), [PNG 당김](void-draw.png), [회복](void-followthrough.png), [복원](void-restored.png) | 실제 framebuffer. [native 시퀀스](void-native.json), [캡처 시간](void-normal-frames.json). 정확한 contact frame 계측은 아님 |
| Arc 강제3인칭 이동 | [report](arc-camera-move/report.json), [이동 후 PNG](arc-camera-move/after.png) | forward+sprint100틱, body Z100.5→139.7826204683161, remote camera 유지 |
| Void 강제3인칭 이동 | [report](void-camera-move/report.json), [이동 후 PNG](void-camera-move/after.png) | 같은100틱, body Z100.5→128.55679864354747; cameraX99.35로 넓어진 어깨 offset 확인 |
| Solar 예외/공격 입력 | [super](solar-native-super/report.json), [attack](solar-native-attack/report.json), [PNG](solar-native-attack/after.png) | self camera 유지·발사 효과. 적을 fixture로 두지 않았으므로 적중/피해 실증은 아님 |
| 후방 회피 회귀 | [report](dodge-native/report.json) | body Z100.5→94.84827336457819. 첫 시점 owner limb 숨김 정책 유지. 방향4종 렌더링을 새로 촬영한 것은 아님 |

각 run은 completed/released, heldKeys/pendingSteps/nativeInput 중립을 별도로 확인했다. 상태와 PNG는 시간 bracket이며 단일 서버 tick과 일치한다고 주장하지 않는다. 실제 서버 로그의 authoritative body와 입력 진단도 보존한다. native 이동은 단일 로컬 연결의 평지에서 검증했다. 벽/낙하는 이번에는 GameTest 증거다.

재현: Vision repo에서 token을 환경으로만 공급하고 `VISION_PORT=8102`, `node scripts/control-smoke.mjs camera_move OUTDIR`. fixture는 `tp VisionControlQA 100.5 -60 100.5 0 8`, hunter, arc/void, energy100. 공허 촬영의 정확한 steps는 `void-native.json`에 있다. 캡처는 기존 `scripts/capture_hunter_frames.py`, interval .06초/4초였으나 실제 PNG 처리 간격은 metadata의 측정값을 따른다.

## 실패·한계 — 숨기지 않는 인수 범위

- **5TPS 동기화 미완료.** [저속 관찰](void-slow.webp), [발췌 contact](void-slow-contact.jpg), [native report](void-slow-native.json), [시간](void-slow-frames.json). BetterModel clip은 약벽시계 .90초에 회복하지만 gameplay release는 서버7틱이다. 회복 후 화살이 나오는 차이를 확인했다. 저속 화면을 정상20TPS contact 통과 근거로 사용하지 않는다.
- 먼저135 client-tick 저속 시퀀스는15초 runner deadline을 초과했다. lease=false/heldKeys=[]/native 중립을 확인하고33틱 시퀀스로 다시 관찰했다. client tick을 벽시계20Hz로 가정하면 안 된다. 관찰 뒤 server tick rate20으로 복원했다.
- partial draw .15초에서 완전 drawn 모델로 전환되어 약2.24모델 단위의 접점 차이가 있다. 완전 draw 접점은 정적 검증 통과이나 후방 시점에서 손/시위 일부가 여전히 가려진다. 네트워크 지연·보간을 포함한 exact frame 동기화는 후속이다.
- 로컬 오프라인 계정의 스킨 폴백 색 전환, 기존 HUD missing-particle texture 경고와 `minecraft:end_of_frame` 경고가 로그에 있다. 새로운 bow missing-model 오류는 관찰하지 않았지만 경고 없는 클라이언트로 표현하지 않는다.
- Blockbench MCP 응답 실패로 JSON 저작 경로를 사용했다. 앱/미저장 탭을 강제 재시작하지 않았으며 네이티브 Blockbench 프리뷰 통과는 아니다.
- Arc/Solar 및 일반 스킬 전체 모션을 이번에 다시 만든 것이 아니다. 다인·지연/청크 경계·벽 근접 가림·OS 키/마우스·실제 GCB transport와 저속 TPS 개선이 남아 있다.

## 출처 시점 / 보존

`preframing/`는 최초 H19 JVM(.45m Void shoulder, nocked shaft Y보정 전)으로 최종 화면의 근거와 구별한다. 최종 JVM은 `final-build.log` 뒤 시작한 서버/클라이언트다. QA tool token/lease credential은 저장하지 않는다.
JAR와 dev class/리소스 byte 일치, 팩/설치 모델, 소스·증거 해시는 `validation.json`에 기록한다. H15 설치 모델, 원본 Vision options/September artifact, 기존 H17 배포 ZIP은 유지한다. 이 작업의 JAR로 기존 배포 ZIP을 검증 완료품처럼 덮어쓰지 않았다.

종료 시 fixture 복구와 자체 프로세스 정리 결과는 `cleanup.json`, 실제 로그는 `server.log`/`client.log`를 참고한다.
