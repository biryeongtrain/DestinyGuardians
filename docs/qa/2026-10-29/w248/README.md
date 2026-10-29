# W248 — 캐릭터 선택창 색상·문양

## 요청과 범위

직업·하위직업 선택을 이름, 고유 문양, 밝은 강조색으로 함께 구별한다. W247의 마우스 포인터 유지와 선택 제한을 보존한다.

## 진행 기록

1. 재사용 slot1을 현재 dirty main snapshot으로 refresh했다. 기존 작업 복구 ZIP과 소유 경로 manifest는 외부 임시 QA 폴더에 보관한다.
2. 자산 worker는 6개 흰색 RGBA 아이콘과 tint 가능한 평면 모델을 담당한다. master는 카드·현재 구성·설명 패널과 실게임 검증을 담당한다.
3. 직업은 헌터 파랑, 타이탄 빨강, 워록 금색; 원소는 전기 하늘색, 태양 주황, 공허 보라색이다. 이는 읽기 쉬운 UI 강조색이며 Bungie 공식 직업 색상이라고 주장하지 않는다.
4. 색상 카드 안에서도 선택 중 텍스트와 금색 표시를 따로 유지한다. hit box·입력 서비스·능력 제한은 변경하지 않는다.

## 검증

- Java 컴파일 및 기존 메뉴 JUnit 23개 통과 (`junit.json`). 새 art-only 테스트는 추가하지 않았다.
- 새 18개 자산 경로·manifest SHA-256 일치, 총 16,608 bytes (`asset-validation.json`).
- worker 소유 경로 21개 변경, 범위 밖 변경 없음 (`worktree-audit.json`).
- QA 생성 팩에 새 18개 자산 포함 확인.
- QA 클라이언트 최초 접속은 서버 빌드 완료 전이라 connection refused였다. 이는 제품 실패가 아니며 아직 실게임 통과로 집계하지 않는다. 서버가 준비된 뒤 재접속한다.
- Danmo 4GB / OpenGL + Vision Client: 직업 3종·하위직업 3종 선택, 현재 구성 반영, 능력 목록, 무기 탭→새 무기→무기군 복귀, native 우클릭 닫기 통과 (`vision-validation.json`, 17 checks).
- 빈 공간 (600,230)에서 42 client ticks 동안 포인터가 유지되고 focus=-1로 남는 것을 확인했다. W247 자동 커서 재배치 결함은 재발하지 않았다.
- 실제 framebuffer PNG를 열어 직업 카드, 세 원소 카드, 워록 태양 구성의 문양·색·글자 겹침을 검수했다. 아이콘 자산은 수정 요청 없이 수용했고 worker에도 결과를 전달했다.
- 아이콘 ITEM_MODEL도 HUD 캐시에 포함해, 동일 위치에서 문양만 바뀌어도 갱신된다. 무기 미리보기와 기존 단색 타일 캐시를 유지한다.
- QA 소스 변경 없음. 리소스팩 최초 접속은 빌드 전 연결 거절이었고, 서버 준비 확인 후 소유 QA 클라이언트를 재시작해 위 결과를 얻었다.

## 실제 화면

- `frames/class-choices-final.png`: 헌터·타이탄·워록, 현재 선택 금색 표시와 hover 설명.
- `frames/subclass-choices-final.png`: 전기·태양·공허 색상과 공식 원소 문양.
- `frames/warlock-root.png`: 캐릭터 구성의 문양과 색상 반영.

PNG는 실제 QA 캡처이며 ignored 증거 폴더에 보관한다. 생성한 미리보기와 구분한다.

## 종료·재사용

QA native 입력이 모두 중립이며 lease가 해제된 것을 확인한 뒤 소유 클라이언트와 QA 서버를 종료했다. 8102·25611 포트가 비었고 외부 QA init 파일을 원래대로 복구했다. slot1은 삭제 없이 W248 통합 완료·다음 refresh 대기로 남겼다. 나머지 worktree 상태와 기존 dirty 파일은 보존했다.

운영 서버를 `runServer`로 다시 열었다. 25565 listen, online-mode=true, andlist OP4, Polymer 팩 생성 완료 및 새 자산 18개 포함을 확인했다. 기존 48시간 잠자기 방지 프로세스는 유지하고 이번 QA 전용 assertion만 종료한다.
