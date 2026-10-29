# 후속02 — callback map 순회 중 예약 제거

기준은 최초20파일 반환본 + followup-01이며, 이번 delta는10파일이다. W43은 followup-01 수정본을 기준으로 하므로 먼저 followup-01을 적용해야 한다. 기존 반환 manifest와 patch는 보존했다.

로컬 Minecraft26.3 jar의 javap 읽기 결과(GameTestInfo-bytecode.txt): runAtTickTimeMap은 Object2LongOpenHashMap이다. tickInternal은 entry iterator에서 Runnable.run을 호출한 다음 iterator.remove를 호출한다. 실행 중 새 callback 삽입으로 재해시가 발생하면 현재 iterator가 무효화될 수 있다. sequences는 CopyOnWriteArrayList이며 callback map 루프가 끝난 뒤 tickAndContinue를 호출한다. sequence 생성/재귀 등록은 해당 map을 변경하지 않는다.

- 8개 파일의 exactAim:40개 runAfterDelay 등록 및 그 마지막 callback에서 action 실행하던 구조를, 미리 조립한 하나의 sequence에 thenExecuteAfter(1)을40번 연결하는 구조로 교체. 실제 서버 틱40개, AE/ADS precondition, 발사와 후속 상대 deadline은 유지한다. 마지막 action은 map 순회 이후 실행되어 후속 runAfterDelay 등록이 안전하다. W77 T+24에서 exactAim 시작/다음 token case의 exactAim 시작도 map 등록을 하지 않는다.
- W78 reloadDeadline: 후속 예약을 추가하는 T+2 및 remaining+2 callback 자체를 sequence 실행으로 옮겼다. 관측만 하는 remaining-1/후속8틱 callback은 그대로다.
- H20SuperTiming/ShadowshotLift: 기존 재귀 tick→runAfterDelay(1)→tick 구조를 사전에 전체 조립한 sequence로 변경했다. 각 실제 서버 틱에 정확히 한 번 step/검증하는 assertion과 원래 total·contact/lift 시간은 유지한다.
- profileReady는 원래 sequence에서 action을 호출하므로 변경하지 않았다.

20개 전체 문법 파싱과 callback AST 검사 완료: 직접 중첩 runAfterDelay 호출0개. 간접 등록 경로인 exactAim 및 위 재귀 tick을 별도로 제거했다. GameTest 이름/개수·수치/assertion·timeout 변경 없음. 빌드·runtime 미실행. 중앙 재실행으로 crash 해소 및 timing을 확인해야 한다.
