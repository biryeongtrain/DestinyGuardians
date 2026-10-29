# W249 — 장전 드롭 예측 복구·인벤토리 메뉴

## 요청

Shift+Q를 메뉴에서 제거하고 장전·특수 장전에 남긴다. 탄약이 충분할 때 Q로 무기만 클라이언트에서 사라지는 동기화 결함을 수정한다. 추가 요청으로 `/메뉴` 및 E 인벤토리 키로 열기·닫기를 지원한다.

## 진행 기록

1. 재사용 slot1을 현재 통합본으로 refresh하고 입력 라우터·현행 사용 문서 5개를 worker에게 배정했다. master는 실제 패킷 후킹·예측 복구·레시피 감지·검증을 담당한다.
2. Minecraft26.3 바이트코드를 확인했다. `Minecraft.handleKeybinds` → `MultiPlayerGameMode.dropItem`은 `Inventory.removeFromSelected`를 먼저 실행한 뒤 DROP_ITEM/DROP_ALL_ITEMS를 서버에 전송한다. 서버의 이벤트 취소만으로 로컬 삭제는 복구되지 않는다.
3. 탄창이 가득 찬 장전 거절은 서버 아이템 변화가 없으므로 remote-slot diff가 보내지지 않을 수 있다. 처리한 drop 패킷 뒤 선택 슬롯을 명시 재전송하도록 고친다. 실제 source를 교체하지 않고 기존 recipient Polymer/profile 투영 경로를 통과한다.
4. 사용자 지정 `/Users/qf/IdeaProjects/InventoryRedirection`의 두 mixin을 읽었다. highlighted recipe의 seen 패킷으로 클라이언트 로컬 인벤토리 열기를 감지하고 container-close 이후 재장전하는 방식이다. 해당 저장소는 읽기 전용으로 보존한다.

5. worker 소유 5파일을 해시 기준으로 통합했다. 전체 worktree 감사에서 범위 밖 변경은 없었다.
6. E 감지는 실제 crafting_table 표시를 복제한 client-only synthetic recipe display 4개로 구현했다. 각 crafting 탭에서 감지되며 세대마다 ID를 바꿔 같은 인벤토리 열기의 중복 seen 패킷이 두 번 토글하지 못한다. 실제 recipe 해금·서버 책 설정은 수정하지 않는다.
7. 메뉴의 Q 닫기 기능을 제거하고 E·우클릭·`/메뉴` 토글로 안내를 바꿨다. 기존 F 및 GCB 0 보조 입력은 유지한다.

## 검증 기록

- 컴파일 및 메뉴 JUnit 23개 통과 (`junit.json`).
- 최초 Gradle 검사 명령에서 --tests 인자를 잘못 배치해 실행이 거절됐다. 수정 후 JUnit은 정상 실행했다.
- 최초 GameTest 필터는 CamelCase 이름을 가정해 no matches였다. 실제 snake_case selector `destiny-test:*w249*`로 수정했다.
- 1차 회귀의 예비탄0 검사는 무한 예비탄을 쓰는 primary 무기를 잘못 사용했다. special 무기로 바꾸어 검증했다. 레시피 패킷 역시 실제 해금 알림과 synthetic beacon을 구분해 검사하도록 고쳤다.
- 2차에서 서버 RecipeBookSettings는 equals를 구현하지 않아 복사 객체 비교가 실패했다. 모든 책 유형의 open/filter 값과 실제 crafting_table 해금 여부를 각각 비교하도록 고쳤다.

실제 입력/서버 wire/framebuffer 결과는 구분해 추가한다.

- 3차 서버 회귀 6/6 통과: full-mag/예비탄0 복구, ShiftQ/재장전중 Q, 이자나기 ShiftQ·CtrlQ, 메뉴중 Q, recipe 세대 토글·일반레시피 구분·해금 불변·비OP /메뉴 열기닫기, vanilla 흙 버리기 (`gametest.json`, `gametest.xml`). 실제 서버 핸들러와 인코딩된 clientbound 패킷을 검증했으며 native 키 증거와 구분한다.

## 병렬 검수 후 보완

- worker가 recipe 목록이 많으면 합성 beacon이 첫 페이지 밖에 놓일 수 있음을 지적했다. 26.3 ClientRecipeBook/RecipeBookPage 바이트코드도 HashMap 분류→페이지당20개 버튼만 초기화하는 것을 확인했다. 관리형 E book은4개 beacon만 client-local replace하여 페이지를 보장한다.
- 실제 작업대·화로 등 서버 메뉴를 열기 직전에 서버의 원래 recipe book·설정을 다시 전송한다. 공중/궁극기 등의 메뉴 guard 거절 때도 원본 책을 복원한다. 실제 해금·제작 가능 여부는 서버 원본을 유지한다.
- E 감지를 위해 관리 중에는 클라이언트 crafting book을 열림·필터 해제로 두어야 한다. 이는 선택한 recipe 감지 방식의 전제다. 외부 제작 화면에서는 원래 서버 설정으로 복원한다.
- AFTER_RESPAWN으로 교체된 ServerPlayer에 새 세대를 재무장한다.
- 1차 Danmo 화면: `/메뉴` 열기·닫기·재열기, native 캐릭터 탭 선택, native 우클릭 닫기와 무기count1 복귀 통과. 실제 framebuffer PNG를 열어 한국어 문구와 닫기 [E] 안내를 검수했다.
- CUA에서 데스크톱 잠금 해제 상태는 확인했지만 Java QA 앱 바인딩은 Invalid app이었다. Vision native v1에는 Q/E 키가 없어 실제 Q/E 키 입력 자체는 미검증이다. 서버 handler+encoded wire 검증을 실제 키 입력으로 보고하지 않는다.

- 4차 회귀도6/6 통과했다. replace=true와 실제 작업대 openMenu의 원본 레시피 복원을 추가 확인했다.
- 일반 recipe unlock/remove 및 초기/데이터팩 recipe 동기화 뒤에는 이미 관리 중인 사용자만 새 beacon 세대로 재무장한다. 실시간 해금 알림이 목록에 쌓여 감지가 다시 페이지 밖으로 밀리는 것을 막는다.

- 최종 소스 컴파일·메뉴 JUnit23개·서버 회귀6개 모두 통과했다. recipe 실제 해금 후 마지막 client book이4beacon replace 상태로 유지되는 것도 검사했다. 리스폰 이벤트 연결은 컴파일/부팅 확인이며 실제 사망→리스폰 E 키 시나리오는 미검증이다.
- 자기 QA 클라이언트와 QA 서버를 종료했고 외부 QA init을 원래대로 복원했다. slot1은 통합·감사를 완료하고 삭제 없이 다음 refresh 대기로 남겼다. 기존48시간 assertion은 유지한다.

- 최종 병렬 정적 검수에서 잠긴 상자처럼 createMenu가 null을 반환하는 경우의 재무장 누락을 추가 발견했다. 운영 서버를 정상 save/stop한 뒤 openMenu 실패 반환에서도 inventoryMenu이면 재무장하도록 수정했다. null provider 실제 호출→새 seen→메뉴 열림 회귀를 추가했다.

- 외부 메뉴 열기 실패 보완 후 최종 회귀6/6 재통과했다. 최종 로그는 `/private/tmp/destiny-w249/gametest-final2.log`다.

## 완료

기능 커밋: `94d800ef`. 관련 delta만 커밋하고 기존 dirty 소스·등록·다른 worktree 변경은 제외했다. `runServer`로 운영 서버 재개 후25565 listen과 Polymer 팩 생성 성공을 확인했다. 같은LAN 접속은 `192.168.35.237:25565`, online-mode=true, andlist OP4다. QA용8102·25611은 비었고 기존48시간 caffeinate PID79904는 유지했다. 이번 W249 전용 coordinator만 종료한다.
