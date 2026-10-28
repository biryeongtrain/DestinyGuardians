# W227 HUD — 2차 실제 PNG 후 한글 가독성 수정

Root: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-seventh_seraph_officer_revolver`

## 순차 통합 delta

- 변경 파일: `src/main/java/kim/biryeong/destiny/inventory/WeaponScreenHud.java` **한 파일만**.
- 필수 기준 SHA-256 / baseSha256: `deeaff1dec6f27f7ab87267aad975a6c9955ec007a32d2d7ad1485854c3356a6`.
- 반환 SHA-256: `45a4b296543f368d8da719c96b56377391f8bb195456c36e944272323b73f335`.
- main의 HUD가 위 base와 일치할 때만 적용합니다. Layout/test/helper/controller/input/server/테스트 코드는 변경하지 않았습니다. commit/push/build/세션 실행 없음.

## 실제 2차 PNG 검토

`view_image`로 아래 세 실제 PNG를 모두 직접 열었습니다.

- [equipment-open.png](/private/tmp/destiny-w227-native-r2/frames/equipment-open.png)
- [equipment-ace-hover.png](/private/tmp/destiny-w227-native-r2/frames/equipment-ace-hover.png)
- [equipment-power-equipped.png](/private/tmp/destiny-w227-native-r2/frames/equipment-power-equipped.png)

관찰: 글자 기준선과 능력치 트랙/탄창 행 정렬은 맞아졌고, hotbar/name/toast 가림 문제도 캡처에서 사라졌습니다. 반면 물리/에너지/파워, 카드 이름/탄약, 기본 능력치, 능력치 이름 등 작은 한글은 획 일부가 사라져 읽기 어렵습니다. 문자 폭에 맞춰 글자 크기를 줄이는 기존 textFit이 카드 이름에서 문제를 더 키웁니다. 이 수정은 그 크기와 축소 동작에 한정합니다.

## 수정 내용

- **표시 크기 전역 하한 18 reference px**를 text()와 textFit() 두 진입점에서 강제합니다. 18px보다 작아지는 렌더 경로가 없습니다.
- 물리/에너지/파워 분류, 헤더 보조 문구, 무기/소지 무기 제목, 버튼, 빈 칸/미장착, 선택 안내, 상세 희귀도/종류/속성/탄약/장착 상태/프레임, 능력치 이름/숫자, 탄창 라벨과 분당 발사 수: **20px**.
- 카드 이름/탄약, 기본 능력치 제목, 푸터와 열기 안내, 미리 보기 없음: **18px**. 푸터는 요청한 18px를 사용합니다.
- 상세 무기 이름과 탄창 숫자는 기존 **26px** 유지. 플레이어 이름 30px, 상세 빈 상태 제목 25px, 장비 탭 21px 유지.
- textFit()은 이제 **크기를 줄이지 않습니다**. 지정한 크기를 유지하고 초과 문구만 Unicode code point 단위로 `…` 말줄임합니다. 크기/폭 계산은 ASCII 6, 한글/CJK 9, 공백 4, 줄임표 6 font advance를 사용하며, 줄임표 폭을 먼저 확보합니다. surrogate pair를 자르지 않습니다.
- 카드 이름은 18px/138px 폭에 일반적인 한글 **6글자+…** 정도를 보여주며 이름 전체를 먼저 받습니다. 상세 이름도 전체 helper 문자열을 먼저 받고 26px/600px에서 폭을 넘는 경우만 말줄임합니다. 더 이상 임의 12/30 code point 선행 잘라내기나 폰트 축소가 없습니다.
- 상태 안내는 **20px/600px**에서 말줄임합니다. 카드 탄약 124px, 상세 속성 176px/탄약 192px, 프레임 560px 등의 기존 내용 폭은 유지합니다.
- 문자 정렬 보정 `y + pixels * 1.25f`는 유지하며, 커진 실제 크기를 그대로 사용합니다. 모든 논리 X/Y, 트랙/구분선/카드 크기, 프리뷰/패널, hit box, focus/navigation은 변경하지 않았습니다.
- 한국어 helper 계약과 `destiny:equipment_w227_` 전용 prefix, aboveHand=true, per-node 상태 cache/metadata 갱신/stale 제거를 보존했습니다. 모델/자산/셰이더 변경 없음.

## 검증과 남은 확인

- 읽기 전 원래 HUD SHA-256이 위 base와 정확히 일치함을 확인한 뒤 수정했습니다.
- 소스 점검: 18px 하한 두 경로, 축소식 제거, 말줄임표 폭 예약/code point 보존, 26px 상세 제목, 20px/600px 상태 안내, 기존 기준선 보정, aboveHand 양 경로, helper 5종 호출, 라이브러리 메서드 호환성, 줄끝/공백을 확인했습니다.
- Layout/test의 최초 해시가 그대로임을 확인했습니다. 모든 버튼과 카드 hit 좌표는 아래와 같습니다.
- master 보고상 수정 전 target-3 단위10/10·assemble·compileGametestJava, server-3 11/11, 2차 native가 통과했습니다. 이 결과는 이번 글꼴 크기 수정본에 대한 새 실행 결과가 아닙니다.
- worker는 이번 수정본을 컴파일/테스트/build하거나 server/client/native/Vision 세션을 실행하지 않았습니다. **새 PNG가 아직 없으므로 가독성 시각 통과는 주장하지 않습니다. master의 짧은 3차 Vision에서 작은 한글 획, 카드 말줄임, 기본 능력치 제목/첫 트랙 간격, 버튼/푸터를 확인해야 합니다.**

## 유지된 native 좌표

CENTER 1920×1080 기준, 중앙=(960,540), Box.x/y는 사각형 중심, +Y 아래. 초기 cursor=(240,360). 어떤 좌표도 이번 수정에서 이동하지 않았습니다.

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

## 변경 없는 파일 해시

- `src/main/java/kim/biryeong/destiny/inventory/WeaponScreenLayout.java`: `8c445819d076dcf012b1d253d25a946a805fb79fac032d767481340930698101`
- `src/test/java/kim/biryeong/destiny/inventory/WeaponScreenLayoutW227Test.java`: `1b1f7b8337597eb77778257ac319233709f02829d23a0e4b980e483699cadb92`
