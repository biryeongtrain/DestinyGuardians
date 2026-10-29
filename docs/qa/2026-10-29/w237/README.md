# W237 실제 스킨 코어 셰이더 시험

사용자가 제공한 CORE-SHADER-HUD-GUIDE (1).md의 바닐라 데이터 신호→셰이더 분기 원리를26.3 native 코드와 대조해 구현한다. 이번 단계는 기존 픽셀별 tint 손을 전부 대체하기 전에 실제 PROFILE 스킨을4개의 저비용 팔 조각에 투영할 수 있는지 확인하는 독립 실험이다.

## 단계와 현재 범위

1. native PlayerHeadSpecialRenderer는 소유자 PROFILE의 전체 스킨을 직접 bind하지만 좌우/상완/전완 설정이 없다. 일반 held special renderer는 CMD tint를 소비하지 않아 기존4leaf만으로 구분하기 어렵다.
2. 처음 후보였던 범위 밖 brightness 신호는 폐기했다. Polymer DisplayElement는 pack한 int를 보내지만 native DisplayRenderer의 getBlock/skyLightLevel이 LightCoordsUtil.block/sky의 &15 마스크를 거쳐 큰 값이 잘린다.
3. 정상 밝기 block0..15/sky13과 전용 Position.y=-10,000,000 lane을 함께 사용한다. 평상시 월드·기존 HUD·일반 player_head는 새 분기에 들어가지 않는다.
4. owner-only ItemDisplayHud4개에 같은 native player_head 특수 모델과 플레이어의 ResolvableProfile을 사용한다. shader가 head cube UV를 classic/slim 팔의 upper/forearm UV로 바꾸고 소매를 합성한다. hat mesh와 내부 elbow cap은 그리지 않는다.
5. 별도 텍스처·RGB 픽셀마다 큐브·스킨색별 tint 리스트를 추가하지 않는다. 양팔은4개 head cube carrier를 사용한다. 머리+hat의 실제 제출 geometry 비용은 남지만 shader에서 hat을 discard한다.
6. 독립 hinge sweep만 시연한다. 기존61장전pose나 무기/팔 전체의 native hand pass를 아직 교체하지 않았다. 따라서 팩 전체775MB 손 JSON을 없앴다거나 동일한 게임플레이/장전이 완성됐다고 주장하지 않는다.

## 실행

기본 비활성이다. 격리 서버에만 -Ddestiny.weapon.profileArmsProbe=true를 준다. OP 명령: /destiny armprobe <player> classic|slim|off. 60초 만료, 사망·차원 이동·disconnect·서버 종료에 정리한다. 프로토타입은 전용 고정 화면 위치에 그려지며 실제 무기 파지 위치가 아니다. 실서버의 기존 손 route는 유지한다.

## Danmo 검증 구성

공식 Modrinth Danmo4.6_263c(TL0AN9Uv)의62개 모드 JAR를 원본 staged와 바이트 단위로 맞췄다. 일반 사용자 프로필은 변경하지 않았다. 기존 QA의 구버전 렌더 모드·RenderScale 조합은 /private/tmp/destiny-w237/client-mods-user-render-preserved에 보존했다. 공식 배포본에는 RenderScale이 없다. Vision은 관찰/입력을 위한 dev classpath 추가이므로 완전한 무계측 공식 실행과 구분한다. MaxHeapSize4G, Mac Apple M4 Pro OpenGL 환경이다. Windows/Vulkan 실기 결과로 간주하지 않는다.

## 검사 진행

- Java compile 통과.
- native26.3 OIT rank2/coeff8/attachment2 포함80 define조합 ×OpenGL/Vulkan compiler=160 링크 통과. 첫 두 시도는 검사 harness의 OIT define 누락으로 실패했고 정확 native 상수 반영 후 통과했다. 모든 native pipeline 조합을 자동 열거한 결과는 아니다.
- 실제 opt-in pack 로드·classic/slim PNG·관절 움직임·제거 복귀를 R3에서 확인했다.

## 도입 판단 시 주의점

세계 디스플레이와 기존 native 1P 총을 혼합하면 native hand pass가 깊이를 지우는 순서 때문에 겹침이 달라진다. 실제 적용하려면 총과 팔을 같은 표시 경로로 옮기는 작업 또는 별도 합성 경로가 필요하다. shader 컴파일과 독립 팔 표시 성공만으로 기존 무기 장전과의 시각적 동등성이나 Windows OOM 해소를 확정하지 않는다.

## 1차 실제 화면 결과

공식 Danmo62개·Loader0.19.5·Iris1.11.7·Sodium0.9.2, Apple M4 Pro OpenGL에서 native pack을 받고 월드에 진입했다. classic/slim 두 너비의 팔4조각이 실제 표시됐으며, 캐릭터 Efe의 우측 금색 팔찌와 좌측의 비대칭이 native 손/원본 스킨과 맞았다. 기존 gun/arms는 별도 기존 route로 오른쪽 아래에 유지된다. owner-only personal HUD를 사용하지만 두 번째 계정 observer 시험은 하지 않았다.

약2.25초 neutral native sequence를 캡처했다. 표면 UV는 유지되지만 forearm이 wrist 주위로 돌아 elbow가 벌어지는 문제를 발견했다. master가 elbow 고정 translation으로 수정했다. worker에게1차 PNG와 문제를 전달하여 source UV 비대칭 검토를 받았다. worker는 네이티브 PROFILE codec·light mask 경로4개 JUnit을 반환했고, main에서 중복 CMD 플래그 구현을 제거하도록 요청한 최종 delta를 통합했다.

normal head control은 처음 UUID를 문자열로 전달한 두 fixture가26.3 codec에서 실패했다. int-array UUID로 수정한 R3에서 같은 PROFILE 머리가 정상 cube로 표시되고, 예약 lane의 팔만 remap되는 것을 PNG로 확인했다. 실패한 control 캡처는 정상 머리 증거로 쓰지 않는다. off 명령 뒤 실험 팔이 사라지고 기존 HUD/바닐라 손이 남았다.

R1 VM.flags의 MaxHeapSize=4,294,967,296 bytes. GC.run 이후 heap used3,123,389KiB(약2.98GiB). 기존 무기 손 graph를 유지한 팩 위에 실험을 추가한 값이며, 새 방식으로 전환했을 때의 절감 측정이 아니다. 실험 item/base JSON은 합158bytes, patched entity shader8,571bytes. 생성 ZIP140,002,632bytes. 큰 손 JSON은 아직 남아 있다.

2차 확인: elbow 수정·helper 통합·upstream shader SHA pin 추가 후 같은 공식 Danmo 구성에서 재검증한다.

## 2차 검수에서 발견한 NONE 문맥 보정

R2의 neutral 캡처에서 helper 통합·classic/slim·off는 동작했으나, 최대 회전 프레임에서 forearm 연결부가 여전히 벌어졌다. 따라서 R2를 elbow 수정 완료로 수락하지 않았다. native ModelRenderProperties/LayerRenderState와 비교하니 NONE은 base display.none 보정을 사용하지 않아 T(-.5) 잔여 오프셋이 남았다. probe item의 SpecialModelWrapper.Unbaked가26.3 transformation(Transformation.EXTENDED_CODEC)을 지원하는 것을 javap으로 확인했다. base 모델은 빈{}로 두고 item-local T(.5,.5,.5)를 넣어 보정했다. native matrix codec·실제 elbow 원점 검사와 R3 Vision으로 확인한다.

전체 JUnit2106개(실패·오류·skip0)는 R2 통합 시점에 통과했다. 이후 변경은 독립 probe의 item-local 변환과 이에 대한 native codec 회귀 검사이며, 관련5개를 재실행한다.


## 최종 R3 수락 결과

공식 Danmo4.6_263c의62개 JAR가 원본과 바이트 단위로 일치하는 상태에서 재접속하여 최종 팩을 로드했다. classic85ticks, slim70ticks의 neutral 캡처로 실제 PROFILE 스킨·소매·팔찌·팔꿈치 연결을 확인했다. R3 item-local T(.5,.5,.5) 보정 후 관절 연결이 붙었고, off 뒤 실험 팔4조각만 사라졌다. 관련 native codec·carrier 검사5개가 모두 통과했다. R3 shader pair는160개 프로그램 컴파일에 사용한 바이트와 동일하다.

증거: screenshots/profile-arms-classic-r3.png, profile-arms-slim-r3.png, classic-elbow-r3.png, probe-off-r3.png. neutral-r3.json은 leaseActive=false, heldKeys=[], pendingSteps=0을 기록한다. 두 번째 플레이어 관찰·만료·차원 전환을 실기로 시험한 결과는 아니다.

최종 item/base JSON 합180bytes, patched entity shader8,571bytes. 생성 ZIP140,002,633bytes(SHA1 ec2f162efd86bac5d31da0b8a4b707d379487c23). 기존 손 graph는 유지되므로 전체 팩은 여전히 약140MB이며, 4GB Windows OOM 해결이나 실제 메모리 절감이 확인됐다는 의미는 아니다. Apple OpenGL에서 성공했고 Windows/Vulkan은 컴파일 검사만 했다. 새 시스템으로 전체 무기·장전 pose를 이식하려면 총과 팔의 표시 경로·깊이 순서를 함께 통합해야 한다.

검증 종료 시 native 입력 lease가 해제된 것을 확인한 뒤 소유한 QA client/server를 정상 종료했다. 별도의48시간 잠자기 방지 프로세스는 유지한다. 실서버는 probe 기본 비활성 설정으로 복귀한다.


R3 클라이언트 로그에는 RRLS의 Failed to force-reload texture 1건과 ModernFix의 perf.dynamic_resources 규칙 불일치 2건이 있다. 이후 팩 로드와 월드 진입, classic/slim/off 캡처는 완료됐다. 이 실행에서 OOM 또는 셰이더 compile/link 실패는 관찰되지 않았다. RRLS/ModernFix 메시지의 원인 자체를 해결하거나 무관하다고 확정한 결과는 아니다.


## 실서버 복귀

실험 기능을 끈 runServer가192.168.35.237:25565에서 다시 기동했고, online-mode=true 및 andlist OP4를 유지했다. 생성 팩140,164,518bytes의 SHA1은cae10eba39084e2ed0a1cd8b2eecc63f14be06a3로 이전 실서버 팩과 일치한다. ZIP 모든 entry의 실제 바이트도 같고 probe item/셰이더 분기는 없다(live-restore.json). 이번 Danmo 실행은 Iris가 설치돼 있으나 외부 shaderpack은 선택하지 않은 상태였으며, 외부 shaderpack과의 동시 사용은 검증하지 않았다.
