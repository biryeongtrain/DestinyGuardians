# 공용 UI 글꼴 선명도 · 2026-11-09

사용자가 올린 화력팀 탐색기의 글자 계단 현상을 개선한다. 기준 커밋은 `49d53da5a`이며 같은 1708×960 framebuffer에서 실제 변경 전·후 탐색기/상세/장비 화면을 검수한다.

## 구현

- 보존된 Noto Sans KR Medium OTF에서 원본 곡선을 가져와 이름을 Guardian UI Sans로 변경한 TrueType 파생 글꼴을 생성한다. 원본·파생 해시와 OFL 출처는 `art/hud/ui-font`에 있다. 26.3의 ttf provider는 CFF OTF를 거부하므로 quadratic TrueType 윤곽으로 변환한다.
- 20px 논리 크기, 2배 oversampling으로 실제 윤곽을 그린다. 기존 11,364자에 대한 advance를 유지한다. 클라이언트/FreeType의 실제 getGlyph 검사로 모든 글자 폭 일치를 확인했다. 초기 TTF 시도에서 14개 영문/기호가 반 픽셀 달랐으며 최소 TrueType 프로그램으로 auto-hinter 경로를 막고 grid fitting을 비활성화한 뒤 해결했다. 이 진단 실패는 통과 결과에 포함하지 않는다.
- HudPainter만 새 글꼴을 선택하며 기존 배율·위치·wrap/ellipsis 지표는 유지한다. 기존 목표/튜토리얼의 bitmap font 파일은 변경하지 않는다.
- 최종 생성된 text vertex/fragment shader에 작은 패치를 합성한다. screen-fixed grayscale HUD 글리프에만 coverage를 bilinear로 샘플링하고 낮은 알파 가장자리를 보존한다. 일반 GUI/월드 글자, colored bitmap, ShaderFX 효과, RGBMap, 애니메이션 글리프 경로를 유지한다. 새 client mod나 전역 sampler 변경은 없다.

## 오프라인 검사

새 native font 검사 1개와 shader 계약 검사 3개 통과. 전체 JUnit 2,842개에서 이전과 같은 실패 3개만 남았다. 비교 결과는 `full-gate.json`에 있다. 기존 native 테스트를 우회하거나 기대 수치를 바꾸지 않았다. 글꼴 생성기는 FontTools 4.62.1로 재생성한 바이트가 정확히 같은지 --verify로 확인했다. Gradle jar 별도 실행 성공, 산출물 CRC 및 새 font/provider/include 바이트 일치를 확인했다. 최종 JAR는 `artifact.json`으로 식별한다.

## 실제 화면 검사

격리 CoW 서버/클라이언트 `/tmp/destiny-ui-font/qa/{server,client}`, loopback 25638/8102, 7200초 제한 master keep_awake, 명시적인 background native 모드만 사용한다. 일반 프로필·기존 QA·원본 글꼴과 dependency 저장소 소스는 보존한다. before/after 입력·화면·팩·정리 결과는 아래에 추가한다.

## 실제 화면 결과

- `before-finder.png`와 `after-finder.png`: 같은 1708×960에서 제목, 설명, 모집 안내, 카드 이름과 footer의 계단 현상이 줄었고 기존 카드/텍스트 배치가 유지된다.
- `before-detail.png`와 `after-detail-settled.png`: 한국어 긴 설명의 줄바꿈과 버튼 위치를 유지한다. OP point fixture로 포인터를 둔 뒤 native Space로 엑소더스 상세를 열고 활동 목록 버튼으로 복귀했다.
- `after-gear.png`, `after-toast.png`: 장비 화면 및 실제 보상 획득 알림의 글자가 새 글꼴로 표시된다. 보상은 격리 계정의 OP loot fixture다. 랜덤 보상 품목은 전후가 달라 동일 문구의 픽셀 비교로 세지 않는다. 장비 화면의 분홍/파랑 QA 모델은 기존 fixture이며 이 작업의 모델 변경이 아니다.
- `after-finder-small.png`, `after-detail-small-settled.png`, `after-gear-small.png`: 격리 옵션으로 요청한 1280×720이 실제 framebuffer 크기와 일치하며 작은 본문·긴 한글·버튼·footer가 잘리지 않고 표시된다. 장비 화면의 닫기 버튼을 native Space로 실행해 종료했다.
- 모든 기록의 backgroundMode/backgroundActive는 true다. 1708×960의 탐색기 전후, 장비, 획득 알림은 실제 windowActive false였다. 상세의 한 캡처는 창이 활성화된 상태였으며 `native-validation.json`에 실제 값을 그대로 기록했다. native 입력 이후 lease 해제, heldKeys 빈 배열, pendingSteps 0을 확인했다.
- 이전의 튜토리얼/월드 로딩 및 Finder와 Gear를 동시에 연 준비 프레임은 수락에서 제외했다. 최종 검사는 기존 OP 튜토리얼 나가기/월드 이동으로 화면 소유권을 정리한 뒤 각 UI를 따로 열었다. `final-neutral-settled.png`에서 장비 닫기 후 타워와 비어 있는 입력 상태를 확인했다.

생성된 실제 공용 팩은 **133,269,192바이트**로 기준 **132,359,120바이트**보다 **910,072바이트** 증가했다. 새 글꼴은 2,200,564바이트이며 ZIP 압축 후 전체 팩 증가는 약 0.91MB다. 실제 ZIP에서 font/provider/filter를 확인했고 ShaderFX case 13개가 그대로 남았다. 클라이언트에서 font/shader 로드 오류가 없었다. `pack-audit.json`.

지원 범위는 검사한 Mac 클라이언트의 위 두 해상도다. Windows/Vulkan·4K·FPS를 추가 인증하지 않았다. 기존 RGB bitmap objective/tutorial 글꼴을 새 UI 글꼴로 전환한 것으로 표현하지 않는다.

실행한 master/server/client 및 소유 awake assertion이 모두 종료됐고 8102/25638이 닫혔다. `cleanup.json`. 사용자 일반 프로필과 이전 QA는 수정하지 않았다.
