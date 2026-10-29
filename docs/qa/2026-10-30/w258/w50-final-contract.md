# W258 fourth-run W50 followup

소유 파일 1개만 변경: src/gametest/java/kim/biryeong/destiny/test/WeaponBowPresentationW50GameTests.java. 현재 main을 새 baseline으로 보존했으며 이전 scheduling 패치가 이미 통합된 상태에서 만든 delta다.

## 원인과 수정

로그의 tick17은 biting_winds drawTicks14 + shotAt 여유2 + buffered use1이다. `ticks`가 등록한 runtime callback과 buffered-use callback이 동일 시각에 예약돼 있다. `WeaponRuntime.beginUse`의 reload 중 buffer 분기(:294–296)는 holding을 설정하고 `updateBow`만 수행한다. float2는 현재 reload clock을 읽지만 reload float1을 쓰지는 않는다. float1은 `tickPlayer`의 `WeaponReloadPresentation.update`(:1171–1172)가 갱신한다. 따라서 buffered callback이 먼저 실행되면 float1은 지난 tick의0인데 nockFrame은 현재 진행률1/16을 기준으로 정확한3/60(.05)을 요구한다. 이 순서 의존성이 현재 코드와 tick17 실패에 부합한다. 실제 실패 로그는 CMD 값 자체를 기록하지 않아0/.05는 코드로 도출한 값이며 런타임 재관측값은 아니다.

buffered callback의 첫 동작으로 `tickPlayer`를 호출해 reload 소유자의 현재 틱 상태를 확정한 뒤, 기존 nockFrame을 입력 전/후 모두 수행한다. use 전후 전체 CMD exact equality, 원래 reloadDuration=n 및 remaining=n-1, ADS intent 없음도 추가 검증한다. 기존 정확 float1 계산, float2 frame, wire selector equality와 원본 ITEM_MODEL 불변 검사는 모두 유지한다. 검사 틱/shot/nock/draw 마감과 조기 release 시점을 옮기지 않았다. callback 내부에서 새 runAfterDelay를 등록하지 않는다.

## 소유권과 패킷 경로

- WeaponReloadPresentation.update(owner,...):92–117은 identity owner를 확인하고 float1을60구간으로 양자화한다. 초기 sentinel .375는60구간 경계값이 아니므로 이 테스트의 최초 nock에는 .001 충돌 offset이 없다. 완료 후 -1 무효화 계약도 그대로 유지한다.
- WeaponBowPresentation.write는 float2만 쓰며 나머지 CMD 목록을 보존한다. buffered beginUse가 reload selector를 대신 갱신하도록 제품을 바꾸지 않는다.
- WeaponCombatItem.use:83–87은 bow의 실제 server hold를 시작한다. ADS는 WeaponAiming.toggle의 left-click 경로이고 reload 중에는 suspend한다. 본 시나리오는 ADS toggle을 호출하지 않으며 추가 assertion으로 요청/입력 false를 확인한다.
- wire helper는 실제 player connection의 PacketContextProvider를 받아 PolymerItemUtils.getPolymerItemStack을 호출한다. WeaponCombatItem은 reload 우선 route, 원본 floats/strings/colors 및 grip flags를 투영하고 WeaponFirstPersonHands가 기존 wrapper를 적용한다. 기존 exact server↔wire 비교와 getter의 원본 불변 assertion은 수정하지 않는다.
- TestPlayers.create는 packet context/connection/accept-load를 초기화한다. drain은 EmbeddedChannel pending tasks와 outbound를 소비하는 도우미이며 WeaponRuntime reload clock을 직접 갱신하지 않는다. 이번 수정은 실제 outbound packet capture를 추가한 것이 아니며 wire projection 검증을 client 영상/네트워크 관측으로 과장하지 않는다.

## 검증과 handoff

Java tree-sitter 문법 검사 및 보존 baseline 대상 git apply --check 통과. main 종료 해시=baseline 확인. Gradle/Java/GameTest/server/client 실행 없음. 중앙 재실행 필요. baseline-manifest.json, result-manifest.json, main-baseline/, slot-before/, followup.patch, changed-files.txt, evidence.json을 함께 반환한다.
