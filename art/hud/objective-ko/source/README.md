# 떠오르는 수호자 · 목표 HUD

첫 임무에서 화면 왼쪽에 보이는 목표 카드입니다. 한국어 플레이 영상 10분 08초의 ‘떠오르는 수호자 / 발사 기지에 진입’ 구간을 기준으로 했습니다. [장면 보기](https://www.youtube.com/watch?v=uOTPieELgPU&t=608s)

| 용도 | 파일 |
|---|---|
| 첫 목표를 그대로 표시 | [hud/objective-ko.png](hud/objective-ko.png) |
| 다른 목표 문구를 넣을 때 | [hud/objective-blank.png](hud/objective-blank.png) |
| 파란 방패 아이콘만 사용 | [layers/blue-tricorn-original.png](layers/blue-tricorn-original.png) |
| 바, 안내선, 빈 체크박스를 개별 배치 | [레이아웃과 글자 위치](hud/layout.json) |
| 글꼴 선택 및 원본 태그 확인 | [폰트 목록](evidence/fonts.json) |

두 HUD는 512×116 RGBA PNG입니다. 배경이 투명하며 왼쪽 모서리가 화면 가장자리에 닿도록 만들었습니다. 게임에서 다른 목표로 넘어갈 때는 빈 HUD 위에 문구를 그리면 됩니다. 제목의 왼쪽 위는 (116, 15), 목표 문장은 (116, 65)입니다. 예시의 두 줄은 각각 20 px입니다. 두 좌표는 글자가 차지하는 영역의 왼쪽 위를 가리킵니다.

## 게임 패키지에서 꺼낸 부분

- Charm 3.5.0의 Tiger 라이브러리로 설치된 게임 패키지를 읽었습니다. 목표 패널은 `thud_objective_panel_widget` (`80A9F1E5`)입니다. 패널과 재귀적으로 연결된 위젯 12개의 원본 바이트가 `native/widgets/`에 있습니다.
- 목표 카드 세 종류에서 배지 슬롯 키 `6F6B927C`가 나옵니다. 이 키는 아이콘 표 `80A9F8BA`에서 비트맵 `80A9F8B4`, 텍스처 `80C24619`, 픽셀 데이터 `80C24618`로 이어집니다. 같은 문양을 가진 판본 여섯 개의 테두리와 흰 로고를 게임 화면과 비교했고, 이 60×60 판본이 가장 가까웠습니다. 부트플로 패키지의 `80A04F2D`에도 동일 픽셀이 있습니다. PNG는 투명 여백을 포함해 원래 크기로 디코딩했습니다. DDS와 게임 원시 데이터가 모두 `native/bitmaps/`에 있습니다.
- 카드의 `title_text` 스타일 `949209A9`는 한국어 **Noto Sans KR Bold**에, `objective_text` 스타일 `22D26497`은 **Noto Sans KR Medium**에 연결됩니다. 같은 게임 패키지의 **Noto Sans KR Regular**와 **Noto Serif KR Medium**도 제공했습니다. 네 OTF는 원본 바이트이며 한글 완성형 U+AC00~U+D7A3이 모두 들어 있습니다. 글꼴 공지와 라이선스 전문은 `fonts/`에 있습니다. [Noto CJK](https://github.com/notofonts/noto-cjk)

## 평면 PNG를 만든 방법

원본 위젯에서 제목 바와 밑줄이 단색 비트맵 `80A9F497 → 80A9F496`을 참조합니다. 게임은 흰 1×1 픽셀을 늘리고 채색합니다. 전달용 PNG에서는 이 픽셀을 늘려 바를 만들고, 실제 화면에 보이는 파란색과 투명도를 근사했습니다. 그 위에 원본 방패를 놓았습니다. 체크박스와 아래쪽 안내선, 글자 위치는 1080p 영상에서 읽어 평면 좌표로 옮겼습니다. 게임 화면의 기울기, 카메라 움직임, 등장 효과는 이 정지 PNG의 검증 범위 밖입니다. Minecraft 클라이언트 적용은 시험하지 않았습니다.

태그와 바이트 오프셋, 글꼴 연결, 영상 점수는 [bindings.json](evidence/bindings.json)에 있습니다. [VALIDATION.json](VALIDATION.json)에 디코딩, 레이어 합성, 글리프 검증 결과를 기록했습니다.
