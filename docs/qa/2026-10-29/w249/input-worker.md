# W249 입력 worker 반환 기록

상태: FROZEN — 지정 5개 파일의 delta를 반환하며 추가 수정은 하지 않는다.

## 기준선과 범위

- main: `/Users/qf/IdeaProjects/DestinyGuardians`
- worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1`
- 양쪽 HEAD: `b2eb348659b09fd4917fa252cd7b6fd39af53708`
- 사용자 refresh 완료/WRITE-READY 이후 지정 파일만 수정했다. 수정 전 네 기존 파일의 SHA-256은 main/worktree가 모두 같았고, 본 기록은 양쪽 모두 없었다.
- RTK 및 main/worktree AGENTS.md를 읽었다. `.codegraph/`가 없어 CodeGraph는 사용하지 않았다. 모든 shell은 `rtk`로 실행했다.

## 정확한 변경 목록

1. `src/main/java/kim/biryeong/destiny/input/InputRouter.java`: Shift+DROP_ITEM의 WeaponScreen.open 조기 분기를 제거했다. live 무기 drop 분기에서 이자나기이며 Shift 또는 DROP_ALL_ITEMS이면 reloadHoned, 나머지는 reload로 보낸다. 메뉴 활성 guard 및 drop 분기 밖의 코드는 보존했다. 장전 성공·거절과 관계없이 모든 live 무기 drop은 true를 반환한다.
2. `docs/design/캐릭터_로드아웃.md`: /메뉴·기본 E 토글과 GCB 0 보조 입력, 우클릭 닫기를 안내하고 Q 계열 장전 의미 및 Shift+Q 메뉴 열기 제거를 명시했다. Q 닫기 안내를 제거했다.
3. `docs/design/W227_무기_장비_화면.md`: /메뉴·기본 E 토글과 GCB 0 보조 입력, E/우클릭 또는 /메뉴 닫기를 안내했다. Q/F 닫기 안내를 제거하고 Q 계열 장전 및 메뉴 중 버리기만 취소함을 명시했다.
4. `docs/design/W228_테스트_무기고와_퍽_선택.md`: 동일한 최신 열기/닫기와 장전 의미를 반영했다. 기존 /destiny inventory test 진입 안내는 유지했다.
5. `docs/qa/2026-10-29/w249/input-worker.md`: 본 한국어 반환 기록을 새로 작성했다. 과거 QA는 수정하지 않았다.

## 입력 경로의 정적 검토

| 상태/무기 | Q (DROP_ITEM) | Shift+Q (DROP_ITEM+Shift) | Ctrl+Q (DROP_ALL_ITEMS) |
| --- | --- | --- | --- |
| 메뉴 닫힘 / 일반 live 무기 | reload | reload | reload |
| 메뉴 닫힘 / 이자나기 | reload | reloadHoned | reloadHoned |
| 메뉴 열림 | 메뉴 활성 guard에서 true | 메뉴 활성 guard에서 true | 메뉴 활성 guard에서 true |

- Shift+Ctrl+Q도 이자나기는 reloadHoned, 일반 live 무기는 reload다.
- live 무기 drop 경로의 반환은 장전 호출 결과에 의존하지 않는다. 잔탄 없음·탄창 가득 참·기타 거절 상황에서도 버리기 취소 경로가 유지된다.
- 메뉴 열림 상태에서는 InputRouter가 장전을 시작하지 않는다. 제품의 Q 메뉴 닫기 제거와 숨겨진 슬롯 복구는 master의 별도 변경을 통합해야 한다.
- 비무기에 대한 전역 Shift+Q 메뉴 열기도 제거된다. 무기가 아니면 기존 후속 입력 경로로 진행한다.
- 실제 Java/서버 실행 결과가 아닌 소스 분기 검토다.

## 수행한 확인과 한계

- 변경 전후 diff에서 InputRouter의 변경은 메뉴 활성 guard 다음부터 기존 START_DESTROY_BLOCK 분기 전까지로 한정됨을 확인했다. guard 이전과 이후 나머지 소스는 기준선과 동일하다.
- InputRouter의 WeaponScreen.open 호출 제거, 이자나기 조건, 일반 무기 reload 및 무조건 true 반환을 정적으로 확인했다.
- 설계 문서 세 곳의 /메뉴·E 토글·GCB 0, Q/Shift+Q/Ctrl+Q 의미, 메뉴 중 Q의 닫기·장전 차단 설명을 확인했다. Q/F 닫기 안내는 제거했다.
- 지정 경로만 대상으로 git diff --check를 수행했다. 변경 전후 파일 해시는 아래에 기록했다.
- Java 실행, build, 게임 입력, 중앙 회귀, Vision은 실행하지 않았다. commit/stash/reset/clean/push 및 fullscan도 실행하지 않았다.
- main에는 쓰지 않았다. sync/UI/WeaponRuntime/mixin/recipe hooks, 무기 모델 및 장전 모션은 수정하지 않았다.

## master 통합 후 확인 항목

- 일반 live 무기의 Q/Shift+Q/Ctrl+Q 장전 성공·거절에서 아이템 보존과 canceled drop 명시 슬롯 재전송.
- 이자나기 Q 일반 장전, Shift+Q/Ctrl+Q 특수 장전과 각 거절 조건.
- 메뉴 활성 중 Q 계열 입력이 닫기나 장전을 유발하지 않고 drop만 취소하며 hidden 슬롯을 복구하는지 확인.
- /메뉴 토글, native E 열기/닫기, 우클릭 닫기, HUD [E] 표시 및 기존 GCB 0 보조 입력.
- native E recipe 감지와 명시 슬롯 재전송은 master 독립 소유다. worker는 WeaponScreen.java/mixin/recipe hooks/tests를 수정하지 않았다.

## SHA-256 기준선과 반환본

본 기록 자체의 반환 해시는 순환 참조를 피하려고 임시 반환 manifest에만 기록한다.

| 파일 | 수정 전 SHA-256 | 반환 SHA-256 |
| --- | --- | --- |
| `src/main/java/kim/biryeong/destiny/input/InputRouter.java` | `5c719debe247e9a673bfdcc98eaa3acda0df43603716dae77491cc9be05d6dbb` | `36ab80d21e6e8c31a0abd2973a43e08bfb1c1b4a7ae703957ef74f5fe7725c1b` |
| `docs/design/캐릭터_로드아웃.md` | `aa4e39a27f80a11c1176c7919136d438adc7f54a80c059d070ec1c1d4b46f1f6` | `275201470c01f9b695d2a326d84d14433bcd00e0360bf8a6c39566b7c598f601` |
| `docs/design/W227_무기_장비_화면.md` | `e772464d69e3b1f6b58ecba2ffd4b443af7e7238d1abee06eb917ad5c21d7273` | `50900b21523c5b739e2e6168b147560faf91a751821bfb3ad9bcbf74e4ecf9e8` |
| `docs/design/W228_테스트_무기고와_퍽_선택.md` | `bb628ad1b1fe0f7aaf2e8aac7e67f1f4855fc8ef440d01c5f23e767d5024eb5e` | `8eba5f79678eedde16d115804482793cc559021836c7a8a0430f352e60db4334` |
