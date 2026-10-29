# W247 중앙 캐릭터 로드아웃 서비스 — worker 반환

- 상태: **FROZEN**. master 통합·검증 대기. 이 문서 이후 worker 수정 없음.
- 작업본: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1`.
- 기준: master WRITE-READY, HEAD `60ac7271bf2d3b19cf49c08acf367f4ba954ac5d` 및 master가 확인한 dirty 포함 기준선. WRITE-READY 이전에는 main 읽기 전용 검토만 수행했다.
- delta: 신규 `src/main/java/kim/biryeong/destiny/guardian/CharacterLoadouts.java`와 본 문서만 작성했다. 다른 worker/master 변경분은 복사하지 않았다.

## 확정 API / UI 조회 계약

| API | 반환 계약 |
| --- | --- |
| `static Element subclass(GuardianData)` | 등록된 현재 SUPER의 직업·슬롯·ARC/SOLAR/VOID 원소를 검증하여 추론. null data, NONE, 누락/unknown/wrong-class/wrong-slot/지원하지 않는 원소의 SUPER는 `null`. 조회로 저장값을 보정하지 않는다. |
| `static List<Element> subclasses(GuardianClass)` | ARC/SOLAR/VOID 순서. 해당 직업에 등록된 SUPER가 있는 원소만 반환. null/NONE은 빈 목록. |
| `static List<Ability> options(GuardianClass, Element, AbilitySlot)` | 등록된 동일 직업·슬롯·원소만, Identifier 문자열 오름차순의 불변 목록. 동일 직업의 KINETIC CLASS_ABILITY/JUMP만 공통 허용. null 인수, NONE, KINETIC 하위직업은 빈 목록. |
| `static String selectClass(ServerPlayer, GuardianClass)` | 성공 `null`, 실패 한국어. NONE 전환도 지원. |
| `static String selectSubclass(ServerPlayer, Element)` | 성공 `null`, 실패 한국어. ARC/SOLAR/VOID만 지원. |
| `static String selectAbility(ServerPlayer, AbilitySlot, Identifier)` | 성공 `null`, 실패 한국어. 현재 SUPER와 다른 원소의 SUPER를 직접 장착할 수 없다. |

서비스는 UI 노드 ID를 정의하지 않는다. 메뉴 controller가 자신의 노드를 위 API의 직업·원소·슬롯·Identifier에 매핑한다. getter 결과가 null/빈 목록이면 메뉴에서 하위직업 미선택 상태로 표현할 수 있다.

## 선택 / 정규화 / lifecycle

- 모든 선택은 서버 메인 스레드, alive, removed/disconnected 아님, spectator 아님을 먼저 검증한다. 활성 SUPER는 동일 선택까지 실패하며 기존 세션을 유지한다. 실패 검사에는 attachment/runtime 생성 접근자를 쓰지 않는다.
- 유효한 동일 직업·하위직업·능력 선택은 cleanup, 저장값 보정, 에너지 변경, HUD 갱신 없는 no-op이다.
- 직업 전환은 목적 직업의 저장 Loadout을 복원한다. 저장 SUPER의 유효 원소를 사용하며, 없거나 잘못되면 ARC를 사용한다. 각 슬롯에서 등록·직업·슬롯·원소가 맞는 저장 선택은 유지하고 나머지만 해당 preset으로 교체한다. preset 대체값도 전부 검증한 뒤 변경한다.
- NONE 전환은 모든 직업별 저장 Loadout을 보존한다. 이후 기존 직업으로 돌아오면 저장값을 복원·정규화한다.
- 하위직업 전환은 목적 원소에 호환되는 기존 능력과 KINETIC 공통 CLASS_ABILITY/JUMP를 유지하고 나머지만 preset으로 바꾼다. 같은 원소의 대체 SUPER 선택은 유지된다.
- unknown ID, wrong class/slot/element, 미등록 preset은 실제 변경 전에 거절한다. 누락/잘못된 SUPER는 하위직업 선택 또는 직업 전환 정규화로 복구하며, 임의 능력 선택으로 원소를 추측하지 않는다.
- 실제 변경 직전에 `AbilityService.cleanup`을 한 번 호출한다. 이어 기존 runtime의 dodge 무적 틱만 종료한다. runtime 자체, 점프 사용 횟수, 입력 capability와 액션 이력은 보존한다.
- 실제 직업/NONE·하위직업·SUPER 변경만 super energy를 0으로 만든다. 다른 능력 변경은 기존 에너지를 유지한다. 쿨다운 setter/reset/tick 호출은 없다.
- `WeaponScreen.close`, 세션 retirement, freeze modifier 제거를 호출하지 않는다. `CombatHud.update`의 기존 메뉴 활성 분기를 사용한다. 기존 CODEC와 데이터 스키마는 수정하지 않았다.

## 수행한 확인 / master 인계

- 지정 RTK/AGENTS, main guardian/ability, 기존 command NONE 처리, cleanup 경로와 메뉴 freeze/HUD 분기를 읽기 전용으로 검토했다. refresh 이후 작업본 의존 API를 재확인했다.
- 소유 Java 파일의 diff 공백 검사와 코드 검토를 수행했다. 새 파일의 `git diff --no-index --check /dev/null <file>`는 진단 출력이 없었으며, 새 파일 차이로 종료 코드 1을 반환했다.
- null 조회 안전성: `subclass(null)`은 null. `options`는 class/element/slot 중 하나라도 null이면 빈 목록. 선택 API도 null player/class/element/slot/Identifier를 한국어 실패로 처리한다.
- Gradle/컴파일/테스트/게임 입력/Vision은 실행하지 않았다. full scan/export, commit/stash/reset/clean/push도 수행하지 않았다. hash 검증·통합·전체 작업본 범위 감사는 master 담당이다.
- master 회귀: NONE 왕복 저장값 보존, 동일 선택의 에너지·cooldown·runtime 무변경, 저장 Loadout 복원/불완전·오염 슬롯 정규화, KINETIC 공통 슬롯 허용, 잘못된 요청의 무변경, active SUPER 실패 시 세션 동일성, 메뉴 선택 후 세션/freeze 유지. 특히 서로 다른 직업/원소/SUPER 변경의 에너지 0 및 모든 슬롯 cooldown 보존을 확인한다.

컴파일/서버 회귀/Vision 수락 전까지 이 반환을 통합 검증 완료로 간주하지 않는다.
