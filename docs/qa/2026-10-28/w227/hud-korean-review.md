# W227 HUD — 1차 Vision 후 한국어·문자 기준선 수정

Root: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-seventh_seraph_officer_revolver`

## 반환 범위와 순차 통합

- 현재 delta.json은 `src/main/java/kim/biryeong/destiny/inventory/WeaponScreenHud.java` **한 파일만** 포함합니다.
- 기존 통합본 필수 기준 SHA-256 / baseSha256: `7e74344b09bd2ae1a0db8f2355d557b5b6a75530d9dc49a8ef4bd796d53c932e`.
- 이번 반환본 SHA-256: `deeaff1dec6f27f7ab87267aad975a6c9955ec007a32d2d7ad1485854c3356a6`.
- 기존 `ebb512cc23d5714e1daf4b14ed9372e9171fec984321e55af833971dc1c4167b` → `7e74344b09bd2ae1a0db8f2355d557b5b6a75530d9dc49a8ef4bd796d53c932e` 수정본 다음에 적용하는 delta입니다. 현재 main이 위 baseSha256과 다르면 덮어쓰지 않습니다.
- WeaponScreenLayout.java와 WeaponScreenLayoutW227Test.java는 수정하지 않았고 최초 반환 해시 그대로임을 재확인했습니다. WeaponScreenText helper, controller/input, 자산, 무기 모델/애니메이션, 라이브러리/셰이더는 수정하지 않았습니다.

## 실제 PNG 검토와 세로 보정

`view_image`로 다음 두 실제 PNG를 직접 열어 확인했습니다.

- [equipment-open.png](/private/tmp/destiny-w227-native/frames/equipment-open.png)
- [equipment-energy.png](/private/tmp/destiny-w227-native/frames/equipment-energy.png)

관찰: 플레이어 이름은 헤더 상단에 걸쳐 있고, 능력치 이름/숫자는 트랙보다 위에 있으며, 탄창 숫자는 구분선과 겹칩니다. 카드/트랙/칸 프레임 자체는 같은 방향으로 치우치지 않았습니다. 1708×960 캡처의 16:9 기준 축척은 약 0.889이므로, 30px 이름의 예상 보정량은 37.5 기준 px ≈ 33.3 캡처 px, 12px 능력치는 15 기준 px ≈ 13.3 캡처 px, 26px 탄창 숫자는 32.5 기준 px ≈ 28.9 캡처 px입니다. 관찰된 크기 비례 상향 오프셋과 맞습니다.

`TextDisplayHud.getLocationVector()`는 한 줄 rawText에서 Y offset=-scale/8을 적용합니다. 현재 명시적인 한 빈 줄 spacer/native glyph baseline과 합쳐 실제 글자 중심이 약 scale/4 위에 놓이는 현상을 1차 PNG에서 확인했습니다. scale=pixels×5이므로 **text()의 최종 위치만 `setLocation(x, y + pixels * 1.25f, 130)`로 보정**했습니다. 글자 맞춤으로 크기가 줄어드는 경우 보정에도 실제 fitted pixels를 사용합니다. 모든 논리 Y, 트랙, 버튼, hit box 및 focus 좌표는 그대로입니다.

이 수정의 예상 결과는 이름을 헤더 안에 넣고, 능력치 이름/숫자를 트랙 중심에 맞추며, 탄창 숫자와 탄창 라벨을 같은 행에 놓는 것입니다. **수정 후 이미지는 아직 없으므로 시각적 통과를 주장하지 않습니다. master의 2차 Vision 검수가 필요합니다.**

## 한국어 표시와 helper 연동

- 캐릭터/장비/무기, 물리/에너지/파워, 소지 무기, 경이/전설, 장착 중/미장착/빈 칸, 이전/다음/닫기, 선택/빈 목록/미리 보기 안내를 한국어로 변경했습니다.
- 능력치 제목은 **기본 능력치**이며 충격/사거리/안정성/조작성/재장전 속도, 탄창, 분당 발사 수로 표시합니다. 숫자는 기존 pinned base stat/Card.rounds/capacity 그대로이며 활성 버프 값으로 바꾸지 않았습니다.
- 동적 표시: `WeaponScreenText.weapon(card.id(), card.name())`, `family(card.family())`, `frame(card.frame())`, `damage(card.damage())`, `ammo(card.ammo())`. helper는 master 제공 계약만 사용하며 이 슬롯에서 생성하거나 수정하지 않았습니다. frame은 반환된 완성 문구를 그대로 쓰고 FRAME/프레임을 추가하지 않습니다.
- 푸터: `마우스 포인터 · WASD 선택` / `좌클릭·Space 장착 · 우클릭·Q 닫기`. 열기 안내: `열기: /destiny inventory 또는 웅크리기+Q`.
- 카드 무기 이름/탄약, 상세 무기 이름/종류/프레임/속성/탄약, 상태 메시지에 한글/CJK advance=9, ASCII=6, 공백=4의 보수적 폭 예산으로 축소 맞춤을 적용했습니다. 카드 이름은 12 code point까지 보여주고 상세에서 더 긴 이름을 표시합니다. 카드 이름 138px, 카드 탄약 124px, 상세 이름/상태 600px 등 고정된 내용 폭을 지킵니다. 버튼 문구는 짧은 한국어라 156px/152px 기존 hit 폭 안에 들어갑니다. 실제 한글 폰트 모양과 가독성은 2차 Vision 대상입니다.
- 1차 PNG에 보인 두 영어 상태 안내는 한국어로 매핑했습니다. 기타 `view.message`는 controller가 제공하는 동적 문자열을 유지하므로 master는 한국어로 전달해야 합니다. 플레이어 이름, 수치, 키 이름과 명령어는 원래 값을 유지합니다.

## 보존된 HUD 동작

- 공개 진입점 `render(ServerPlayer, WeaponScreenView)`, `remove(ServerPlayer)`와 `destiny:equipment_w227_` 전용 prefix 유지.
- 전체 패널/프리뷰/문자/포커스/포인터의 aboveHand=true 유지. 기존 z100..152 레이어 유지; master가 셰이더 유효 범위를 확인한 조건 그대로입니다.
- 기존 `destiny:gui/hud/solid` 틴트 geometry와 `WeaponModels.create(WeaponCatalog.find(id))` + GUI context 프리뷰 유지. 소유 인벤토리 변경 없음.
- 기존 node 상태 cache/metadata batch/stale node 제거 유지. 틱마다 respawn하지 않으며 별도 UUID 세션 map 없음.
- 장착 목록은 slot으로 매칭하고 grid는 controller가 제공한 spare carried 페이지를 그대로 표시합니다.

## 변경 없는 native 좌표

CENTER 정렬 1920×1080 기준, 화면 중앙=(960,540), +Y 아래. Box.x/y는 사각형 중심입니다. 초기 focus0 포인터=(240,360). 표시/입력은 같은 bounds()를 사용하고 현재 delta는 어떤 box도 이동하지 않습니다.

| 노드 | 기능 | 중심 X | 중심 Y | 폭 | 높이 |
| --- | --- | --- | --- | --- | --- |
| 0 | 물리 장착 칸 | 240 | 360 | 156 | 156 |
| 1 | 에너지 장착 칸 | 240 | 540 | 156 | 156 |
| 2 | 파워 장착 칸 | 240 | 720 | 156 | 156 |
| 3 | 소지 무기 1행 1열 | 540 | 360 | 156 | 156 |
| 4 | 소지 무기 1행 2열 | 720 | 360 | 156 | 156 |
| 5 | 소지 무기 1행 3열 | 900 | 360 | 156 | 156 |
| 6 | 소지 무기 2행 1열 | 540 | 540 | 156 | 156 |
| 7 | 소지 무기 2행 2열 | 720 | 540 | 156 | 156 |
| 8 | 소지 무기 2행 3열 | 900 | 540 | 156 | 156 |
| 9 | 소지 무기 3행 1열 | 540 | 720 | 156 | 156 |
| 10 | 소지 무기 3행 2열 | 720 | 720 | 156 | 156 |
| 11 | 소지 무기 3행 3열 | 900 | 720 | 156 | 156 |
| 12 | 이전 | 540 | 860 | 156 | 48 |
| 13 | 다음 | 900 | 860 | 156 | 48 |
| 14 | 닫기 | 1740 | 112 | 152 | 52 |

## 확인 범위

- 1차 PNG 두 장 실제 열람, TextDisplayHud offset/scale 소스 확인, HUD 호출 메서드를 로컬 라이브러리 선언과 대조, helper 계약 호출 5종(weapon은 2인자), 단일 보정 위치, aboveHand 양 경로, frame suffix 제거, 소유 경로/해시/줄끝 확인을 수행했습니다.
- master 보고: 이전 targeted source/build 및 UI pure test 10개 통과. 1차 native에서 WASD/포인터/Ace 장착/에너지 선택/닫기 통과. 이 결과는 수정 전 통합본에 대한 master 결과이며 이번 반환본 실행 결과가 아닙니다.
- 이번 worker는 컴파일/테스트/build/client/server/native 입력/Vision 세션을 실행하지 않았습니다. main/commit/push 및 helper/controller 변경도 없습니다. master가 helper 통합 후 컴파일하고 vanilla hotbar/name 표시 정리와 함께 2차 native/Vision을 진행합니다.

## 변경 없는 파일 해시

- `src/main/java/kim/biryeong/destiny/inventory/WeaponScreenLayout.java`: `8c445819d076dcf012b1d253d25a946a805fb79fac032d767481340930698101`
- `src/test/java/kim/biryeong/destiny/inventory/WeaponScreenLayoutW227Test.java`: `1b1f7b8337597eb77778257ac319233709f02829d23a0e4b980e483699cadb92`
