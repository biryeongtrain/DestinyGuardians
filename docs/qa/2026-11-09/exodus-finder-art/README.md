# 엑소더스 화력팀 탐색기 이미지 · 2026-11-09

엑소더스의 추락의 목록 카드·상세 화면·배경이 악마의 소굴 배너를 참조하던 것을 전용 배너로 변경했다. Bungie 공식 manifest의 Exodus Crash 활동 1236031537에서 PGCR 이미지와 아이콘을 가져왔다. 출처는 `src/main/resources/destiny/fireteam/art.json`, PNG 해시·크기는 `assets.json`에 있다. 아이콘은 원작에서 정상 공격전들이 공유하는 공식 Vanguard 문양이며, 전용 풍경 배너는 엑소더스 블랙 추락 지점이다.

배너는 640×360, 아이콘은 96×96이다. 탐색기는 활동 팩을 받기 전에도 표시하므로 새 이미지와 item/model 정의는 공용 destiny 네임스페이스에 둔다. 활동 NBT·다운로드·진행 코드는 변경하지 않았다. importer도 함께 갱신했으며 재생성 중 달라진 무관한 캠페인 배너는 기존 바이트를 보존했다.

Gradle `jar` 성공. 실제 JAR 안의 새 item/model/texture 6개가 소스와 바이트 단위로 같고 JSON 참조가 연결되며 배너가 악마의 소굴 PNG와 다름을 확인했다. 이번 변경은 정적 이미지·참조 수정이므로 신규 단위 테스트/전체 gate는 추가 실행하지 않았다. 실제 화면 검증 결과는 아래에 추가한다.

## 실제 백그라운드 클라이언트

새 CoW 격리 서버/클라이언트 `/tmp/exodus-finder-art-qa/{server,client}`와 loopback 25638/8102를 사용했다. 기존 QA/일반 프로필은 보존했다. 3600초 제한 keep_awake master 및 `visionControlBackground=true`를 사용했다. 세 탐색기 캡처 모두 `backgroundMode=true`, `backgroundActive=true`, `windowActive=false`이다.

- `finder-category.png`: 악마의 소굴 세픽스와 엑소더스 블랙 풍경이 서로 다른 카드로 보이며 한국어 활동명이 맞다.
- 기존 OP fixture로 탐색기를 열고 포인터를 엑소더스 카드에 둔 뒤, 실제 native Space 입력으로 상세 화면을 열었다. `finder-detail.png`에서 전용 배너/활동명/네소스 표시를 확인했다.
- 상세 화면의 활동 목록 버튼에 포인터를 두고 native Space로 목록 복귀. `finder-returned-category.png`. 빈손 use 입력 시도는 화면을 바꾸지 않아 뒤로 가기 수락으로 세지 않았다.
- 최초 접속의 튜토리얼 안내와 월드 로딩 프레임은 수락에서 제외했다. 기존 튜토리얼 나가기 fixture 후 타워의 준비된 화면에서 검사했다.
- 생성된 공용 ZIP 안에 신규 정의/PNG 6개가 있고 두 PNG가 소스와 정확히 같다. 전용 팩을 다운로드하지 않은 상태에서 탐색기 이미지가 정상 표시됐다.
- 마지막에 OP 월드 이동 fixture로 탐색기를 정리하고 타워로 돌려놓았다. `final-neutral.png` 및 JSON: screen/overlay 없음, leaseActive false, heldKeys 빈 배열, pendingSteps 0. OS 키 입력/실제 이동 게임플레이/오디오 검증을 의미하지 않는다.

소유한 master/server/client와 awake assertion이 모두 종료됐고 8102/25638이 닫혔다. `cleanup.json`.
