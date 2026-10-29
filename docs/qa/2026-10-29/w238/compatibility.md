# PROFILE 손 표시 호환성

수락 결과는 README와 실제 캡처·로그를 기준으로 판단한다. 정적 분석, 오프라인 셰이더 검사, 실제 게임 검증의 범위를 구분한다.

| 환경/기능 | 확인 결과와 한계 |
|---|---|
| 공식 Danmo 4.6_263c, 62개 JAR | 원본 staged와 SHA256 전수 일치. Vision dev classpath를 추가한 격리 프로필, Java25, 4GB에서 새 팩 로드와 타워 진입 성공 |
| Iris 설치, 외부 셰이더팩 미선택 | 이번 실제 검증 구성. Iris 설치 자체와 외부 셰이더팩 활성화를 구분한다 |
| 외부 Iris 셰이더팩 활성화 | 코어 셰이더 재정의 경로와 충돌한다. 새 손·총 표시를 보장하지 않으며 현재 지원 범위 밖이다 |
| 다른 리소스팩/모드의 entity/item 코어 셰이더 덮어쓰기 | 충돌 가능. 서버 생성 시 기반 SHA를 검사하지만 클라이언트의 다른 덮어쓰기까지 방지하지는 못한다 |
| Windows/Danmo 4GB | Mac 결과를 Windows OOM 해결의 확정으로 간주하지 않는다. 새 팩의 Windows 실기 검증은 추가로 필요하다 |
| Vulkan | glslang 컴파일·링크 125개 조합 통과. 실제 GPU 실행을 뜻하지 않는다. 이번 Mac은 OpenGL 실기다 |
| OptiFine 26.3 | 공식 대상 릴리스를 확인하지 못했다. 호환 여부 미확인 |
| Danmo GCB F5 | 시점 변경 통지를 받으면 개인 디스플레이 5개 제거, 1인칭 복귀 시 재생성. 최종 R5 앞/뒤 전환에서 제거, 1P 복귀와 빈손 제거 확인. 통신 지연이 있으며 재접속할 때 기존 3인칭 상태의 초기 통지가 생략되는 GCB 한계가 있다 |
| 바닐라 F5 | 서버가 로컬 시점 패킷을 받지 않으며 현재 셰이더 입력에도 isFirstPerson이 없다. 자동 숨김을 보장하지 못한다 |
| 스킨/소매 | PROFILE을 네이티브 스킨 렌더러가 바인딩한다. classic/slim·좌우·소매 표식으로 UV를 바꾼다. 독립 W237 검증과 실제 무기 W238 검증을 구분한다 |
| 동작 부드러움 | 기존 61포즈 총기 모델 선택 유지. 팔은 서버 목표 포즈와 1틱 네이티브 디스플레이 보간을 사용한다. GPU에서 원본 애니메이션을 연속 재생하는 방식은 아니다 |

예약 좌표와 밝기 표식을 모두 만족할 때만 새 분기에 들어간다. 일반 머리와 월드 모델은 기존 셰이더 경로를 사용한다. 기존 픽셀 손 소스는 보존하며 `-Ddestiny.weapon.legacyPixelArms=true`로 되돌릴 수 있다. 이 옵션은 서버 재기동과 팩 재생성이 필요하다.

관련 자료: [Iris](https://irisshaders.dev/), [Minecraft 26.3](https://feedback.minecraft.net/hc/en-us/articles/48913133328013-Minecraft-Java-Edition-26-3), [OptiFine](https://optifine.net/downloads). native 26.3와 공식 Danmo GCB4.0 JAR의 정적 분석 결과를 포함한다.
