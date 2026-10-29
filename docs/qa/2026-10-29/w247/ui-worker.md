# W247 UI worker — FROZEN

- Worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow`.
- WRITE-READY 수신 후 소유 Java 4개와 이 문서만 수정. main/다른 worker 파일 수정·복사, commit/stash/reset/clean/push, Gradle 빌드, 게임 입력 없음.
- 상태: Java 4개 FROZEN. master가 해시 감사·통합·컴파일·GameTest·실제 Vision PNG 검수한다. worker 검토만으로 제품 수락을 주장하지 않는다.

## UI 계약

- 기존 무기 노드 0–19와 페이지당 9개 wizard 유지.
- `WeaponScreenLayout`: `CHARACTER_TAB=20`, `LOADOUT_TAB=21`, `CLASS=22`, `SUBCLASS=23`, `GRENADE=24`, `MELEE=25`, `CLASS_ABILITY=26`, `SUPER=27`, `BACK_CHARACTER=28`, `NODE_COUNT=29`.
- stage `CHARACTER`: 닫기·탭·6필드만 표시/히트/탐색. 필드 순서와 ID는 CLASS, SUBCLASS, GRENADE, MELEE, CLASS_ABILITY, SUPER.
- stage `CHARACTER_OPTIONS`: 닫기·탭·grid 3–11·이전/다음 12/13·캐릭터 복귀 28. 옵션은 현재 페이지의 최대 9개.
- boolean `visible/hit/navigate` overload 및 stage 생략 overload는 legacy 0–19만 허용. 문자열 stage overload는 새 노드를 허용.
- 숨김 focus 복구: CHARACTER는 CLASS, CHARACTER_OPTIONS는 3, 무기 stage는 0. 컨트롤러의 활성화 전에 stage visibility도 확인.
- 캐릭터/로드아웃 탭은 실제 버튼. 캐릭터 탭 이동 시 무기 detached draft를 폐기하며 장착은 하지 않음. 로드아웃 탭은 LOADOUT으로 복귀.
- 옵션 선택은 중앙 서비스만 호출. 성공(null)이면 즉시 CHARACTER root로 복귀하고 이전 편집 필드에 focus, 실패 시 한국어 오류를 표시하고 옵션 화면 유지.
- NONE은 직업 옵션에 포함하지 않음. 하위직업/능력 후보는 각각 `CharacterLoadouts.subclasses`/`options`에서만 얻음. 공용 직업 능력의 소속 판단도 중앙 서비스에 위임.
- `CharacterLoadouts.subclass(data)==null`: 하위직업 이름 “미선택”, projection subclass `""`, 능력 옵션 없음. `CharacterView.EMPTY.subclass`도 `""`.

## Projection / snapshot

- `WeaponScreenView`는 기존 11/16/19 인자 생성자 호환 유지. canonical 생성자 마지막 인자 `CharacterView character` 추가.
- `characterMode()`와 `character()` 제공.
- `CharacterView(guardianClass, className, subclass, subclassName, field, fields, options)`.
- `CharacterField(id, name, value, enabled, reason)` — 캐릭터 화면에서 6개, 현재 장착값과 선택 불가 이유 포함.
- `CharacterOption(id, name, description, selected, enabled, reason)` — 현재 페이지 목록, 현재 선택 강조. 직업/하위직업 ID는 enum 이름, 능력 ID는 등록된 Identifier 문자열.
- projection 리스트는 `List.copyOf`로 복사하며 mutable GuardianData/Ability/ItemStack을 새 캐릭터 projection에 포함하지 않음.
- `public static Optional<WeaponScreenView> snapshot(ServerPlayer)`는 현재 연결에 속하는 세션의 저장된 view만 반환. open/refresh/render/guardian 초기화/게임 입력 부작용 없음. 서버 스레드에서 사용.
- 캐릭터 외 stage에서는 `character()`가 EMPTY이고 필드/옵션 목록은 비어 있음.

## 구현·검토

- 기존 DisplayHud Painter/색상/텍스트 크기 하한을 재사용. 새 SGUI, 패킷 경로, 자산 없음. root 6필드·현재 값, 9개 옵션 카드·현재 선택, 설명/선택 조건 패널, 페이지/뒤로/닫기 제공.
- 직접 읽은 layout 좌표를 사용하는 독립 Python 계산에서 LOADOUT/FAMILY/WEAPON/PERKS/CHARACTER/CHARACTER_OPTIONS별 표시 상자 비중첩, 모든 표시 노드 사이의 방향키 도달 가능성, 숨김 focus의 표시 노드 복구를 확인했다. 이는 Java 실행/JUnit/게임/Vision 결과가 아니다.
- 기존 생성자 위임·서비스 호출·페이지 슬라이스·성공/실패·클릭 visibility guard를 소스 검토했다.
- Java 컴파일·JUnit·GameTest·실제 PNG는 worker 미수행. master가 준비한 packet+snapshot GameTest와 legacy/new-stage geometry 회귀에 연결한다.

## master 취합 사항

- 서비스 Java는 이 worktree에 작성/복사하지 않음. 중앙 서비스 delta와 UI delta를 master가 함께 통합해야 함.
- 능력 옵션 설명은 현재 직업·속성·슬롯 및 즉시 장착 안내 중심이며 개별 능력의 상세 효과 설명은 포함하지 않는다. 필요한 보강은 master 검수 후 요청 가능.
- 소스 정적 geometry 계산은 통과했으나 실제 DisplayHud 글자·카드 간격과 화면 전환 시 노드 제거는 master Vision PNG로 확인해야 한다.
- master의 실제 PNG 검수 또는 컴파일/테스트 수정 요청 전까지 Java 소유 파일은 더 수정하지 않는다.

## WRITE-READY 직후 소유 Java 기준 SHA-256

| 파일 | SHA-256 |
| --- | --- |
| WeaponScreen.java | 1e8363c580c018ecb824d11f2d89c467e6cf9bbaaa8977f69140560a9648786b |
| WeaponScreenView.java | 9d86817d4fa9961bdcb3f2f221d1df50703247ff6d2276bf7186266bee761430 |
| WeaponScreenHud.java | 52752b53a32c755aac0afb35fe5c3c47ed047ca810f87d9a9b16b9ef178dd2af |
| WeaponScreenLayout.java | 689fbf1b7dfcf548ce3701de3111962b579a7b4b90f8a09b8441c0f7792ef5de |
