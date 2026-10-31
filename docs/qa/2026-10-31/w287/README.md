# W287 튜토리얼 첫 자동소총과 E 메뉴 안내

서버 코드만 변경. 첫 사격 전에 EQUIP 단계에서 Halfdan-D(일반탄, 자동 사격)를 임시 지급하고 실제 선택 슬롯까지 바꾼다. 메뉴를 직접 열어 무기를 생성해야 했던 조건과 2분 대기를 없애고, 40틱 후 첫 표적 단계로 진행한다. 열린 장비 창은 사용자가 닫을 때까지 기다린다. FIRE 직접 진입 시에도 빈손이면 지급한다.

기존 TutorialLoan의 영속 보관/복원 경로를 사용한다. 원래 장비3칸, 선택 슬롯, 장비 모드 상태를 보관하며 종료 때 복원한다. 무기군 실습까지 같은 보관본을 사용하고, 실습 종료 후 원래 무기가 없는 계정에는 남은 훈련용 자동소총을 다시 빌려준다. 이 소총도 튜토리얼을 나가면 회수된다. E에서 새로 만든 일반 장비는 기존 복원 경로로 보존한다.

직업 안내 대사에 선택이 고정되지 않는다는 설명을 추가했다. 직업 선택 화면의 지속 키 안내와 선택 직후 토스트에도 E키에서 변경 가능하다고 표시한다. 첫 무장 대사와 첫 사격 목표 목록에는 E키에서 무기 설정/변경 가능하다는 안내가 나온다. 새로운 설명은 자막/HUD이며 새 음성 녹음은 추가하지 않았다.

## 검증

초기 targeted GameTest1/1 통과: 원래 아이템이 있는 플레이어가 메뉴 조작 없이 소총을 즉시 들고, 첫 표적 단계로 자동 진입하며, 무기군 교체와 종료 후 원래3칸/선택 슬롯/모드가 복원되는 실제 서버 동작 확인. 전체 실행에는 빈 장비 계정이 무기군 실습 후에도 소총을 유지하고 마지막 종료 시 회수하는 검사를 추가했다.

## 화면 검증 제약

`/Users/qf/.codex/skills/copper-golem-vision-client-fabric-26-3/SKILL.md` 및 runtime/input-control references를 읽었다. Computer Use inventory 조회는 가능했으나 앱 선택은 Codex safety rejection, Finder `Computer Use was not approved to use Finder`로 거부됐다. 프로젝트 AGENTS.md의 “시작 전 Computer Use로 잠금 상태, Vision port/process 소유권을 확인한다” 조건 중 잠금 상태를 확인할 수 없었다. 따라서 클라이언트/입력을 시작하지 않았고 Vision PNG·native 입력·음성 청취는 미검증이다. 앱 권한이나 잠금 설정을 우회하지 않았다. 시작 전 Vision8102/QA25581 listener 없음. 이번 배치에서 client/server용 caffeinate는 만들지 않았다. 자동 GameTest 서버만 자체 실행/종료했다.

## 최종 결과와 산출물

전체1,463 GameTest에서 새 튜토리얼 검사(빈 장비 복구 추가분 포함)는 통과했다. 전체는101 required failures로 exit1이다. W286의100개 실패는 모두 유지되고 W270 same_kind_aliases 음성 테스트1개가 추가됐다. 이 음성 테스트는 동일 최종 코드에서 단독 실행하면1/1 통과했다. 전체 실행 상호작용의 원인은 이번 범위에서 해결하지 않았으며 전체 통과로 보고하지 않는다. `full-gate-comparison.json` 참조.

서버 JAR `destiny-guardians-0.1.0+26.3-w287-tutorial-starter.jar`, 215,132,586 bytes. SHA256 `6c615f1ab79f44972f92e88b56fdb60f18b70dd1048ac07c80ae2fc6fbae3f8c`. 전체 Tutorial 클래스가 실행 build/classes와 바이트 일치함을 확인했다. 현재 작업본의 기존 미커밋 제품 변경도 포함한다. 배포/원격 push는 하지 않았다. 이번 변경의 서버 동작은 검증했으나 화면 검수는 위 권한 제약으로 남아 있다.
