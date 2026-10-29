# W241 — 지향사격·공중 효율 탄퍼짐

## 요구·단계 기록

1. 사용자 확인으로 W240 FOV 새 팩은 Windows에서도 정상이다. 이번 배치는 무기마다 다른 무작위 지향사격, 공중 ADS 추가 오차, AE100 이상에서 추가 공중 오차0을 구현한다.
2. DDC·공식 고정 manifest 조사: 사격60종의 기본AE 존재, 검5종 누락, 캐시와 불일치0. Ace14/Izanagi6. 프레임 Precision HC +25는 기본stat과 별도 합산. 상세 근거 FINDINGS.md.
3. 고정slot4를 최신 dirty 통합본으로 갱신했다(48파일,221414입력). W238 잔여 도구/이전 문서는 /private/tmp/destiny-w241/pre-refresh-preserved 및 refresh-recovery에 보관하고 기존 통합본과 대조했다. 워크트리를 삭제하지 않았다. Rawls가 순수 수학/검증2파일, master가 런타임·데이터·명령·GameTest·Vision을 소유한다.
4. 기존 탄퍼짐은 bloom이 있는 연사에만 고정방향 오차를 주어 첫발hip/AE가 빠져 있었다. 공통 direction을 무작위 샘플로 교체하고 샷건 한 발의 펠릿은 하나의 발사축을 공유하도록 수정 중이다. 근접 공격과 검 caster는 제외한다.

## 설계 경계

- w241-accuracy.json의 반각(deg), 프레임/안정성 배율, AE0–100 선형감쇠와 원판 랜덤 분포는 Minecraft 임시 튜닝이다. 원작 확정값이 아니다.
- hip항=(기본hip각+bloom각)×(1−ADS진행)×기존accuracy퍽배율; air항=공중최대각×(1−clamp(AE/100)); 최종반각=hypot(hip,air).
- 완전ADS는 지상에서 추가오차0, 공중에서는AE100 이상일 때 추가오차0. AE100이어도 비ADS의 지향사격 페널티는 남는다. 반동/투사체중력·유도/산탄·융합 고유배열은 별도 유지한다.
- 물·용암·사다리 상태를 제외한 !onGround에서 공중 판정. 점프·낙하·비행 포함.
- `/destiny weapon airborne <bonus> [player]`: OP용 장착무기 추가AE(-100..200). 0으로기본복원. 기본+프레임+추가를 합산한 실효AE는0..100. 전투 아이템customdata에 저장하고 탄약 저장시 유지한다. 매발AE 컴포넌트를 변경하지 않는다.
- `/destiny weapon status [player]`: 기본/프레임/추가/실효AE, 공중판정, 현재탄퍼짐반각. 조회는 난수·item을 변경하지 않는다.



5. Worker 순수 수학8개 통과. 반환2파일 SHA256과 main의 provisional integration 바이트 일치. 무작위 원판 분포·수직시선·AE99/100초과·accuracy퍽0에서도공중오차 유지·AE100에서hip유지 검증. Master focused8개 및 main/gameTest 컴파일 통과(1분53초). 별도 읽기전용 worker 검수에서 실질 결함 없음.
6. 실서버25565를 정상stop한 후 빌드했다. CU에서 Finder 데스크톱 접근과 QA포트 비어있음을 확인했다. 기존48시간 잠자기방지는 보존한다. 전체JUnit1회 후 격리서버GameTest·Danmo4GB Vision 취합을 진행한다.

7. 전체JUnit2131/2131 통과(318suites,실패/skip0). 첫 실제GameTest는4/5통과. 유일한 hitscan fixture는 재사용QA의 Peaceful에서 Husk생성 실패; Normal변경 뒤에는 대상 생성 후 이동 및 미로딩 구간에 의존할 가능성을 확인했다. 결과원본 gametests.json/r1 보존. 제품의 미로딩chunk에서추적중단 정책은 유지하고, fixture만 전체 ray구간을 로드하고 최종위치에 Peaceful에서도 가능한 Pig를 생성하도록 수정했다. QA 난이도는 Peaceful로 복원했다. 서버stop 후GameTest만컴파일25초통과; 제품 변경이 없어JUnit전체를 반복하지 않는다.

8. 최종GameTest5/5통과. 30m fixture는 주어진 테스트영역/청크 밖 동작에 의존하여 두 번 더 실패했고, 원인 하나를 확정한 것으로 기록하지 않는다. 최종 fixture는 기존48블록 테스트구조 내 같은entity청크에서10m 비조준저격총으로 조준선에서벗어난표적의 실제HP감소와1발소모를 확인했다. 실제피해 경로를 mock하지 않았다. 제품코드는 초기전체JUnit 이후 변경하지 않았다.
9. Vision첫fixture 준비에서 다른차원의 미로딩위치 fill이 거절된것을 놓쳐 QA가 낙하사망했다. native lease는 player_not_controllable로 중단되고 중립으로 정리됐다. 격리Overworld12청크만 forceload하고 바닥/표적벽을 만든 뒤 리스폰복구중이다. 실서버월드는 건드리지 않는다.

10. Vision 초기 실패는 바닥 생성 명령의 거절을 놓친 fixture 오류로 기록했다. 격리 QA 클라이언트만 종료·재기동하여 즉시 리스폰으로 복구했다. 이후 공식 Danmo 62모드·4GB 클라이언트에서 native use/점프/ADS 입력과 실제 PNG를 취합했다. 지상 Ammit 지향사격26장, AE20 점프ADS30장, AE100 점프ADS29장을 캡처했다. 대표3장만 저장소에 보존한다.
11. Ammit AE20의 실제 공중 완전ADS 상태: 반각1.040°. 추가AE80을 부여한 실효AE100의 실제 공중 완전ADS 상태: bloom이 남아 있어도 반각0.000°. 두 sequence 모두 공중 관측6회, 입력 완료(returncode0), release 후 leaseActive=false/heldKeys=[]/pendingSteps=0/nativeInput중립을 확인했다. 지향사격 첫발 반각1.652°와 실제 탄약 감소도 확인했다. 서버 상태·native 소비·실제 피해 GameTest·PNG 검수를 각각 구분한다. PNG만으로 탄도 통계나 명중 정확도를 증명했다고 주장하지 않는다.
12. QA 추가AE를0으로 복원하고 immediate_respawn=false로 복원했다. 이번에 강제 로드한 Overworld12청크를 해제했다. 최종 중립 상태를 저장한 후 소유한 클라이언트와 격리서버를 종료했다. 독립48시간 caffeinate(PID79904)는 보존했다. slot4는 삭제하지 않고 idle-needs-refresh/W241로 반환했다.

## 결과·증거

- 전체 JUnit **2131/2131**, 318 suites, 실패/에러/skip0: `junit.json`, `full-junit.log`.
- 새 순수 수학8개 통과와 worker 소유파일 SHA256: `worker-result.json`, `targeted.log`.
- 최종 실제 GameTest **5/5**: `gametests-final.json`. 첫발 무작위·조회 순수성, AE99/100/초과 경계, bonus 탄약 저장 보존, Precision HC +25, 검 제외/사격60종 연결, 조준선 밖 표적의 실제 피해와1발소모, 실제 로켓 발사축을 확인했다.
- 초기 GameTest fixture 실패는 `gametests.json`, `gametests-r1.json`~`r3.json`에 보존했다. Peaceful Husk 생성 실패와 30m 표적 비명중을 제품 결함으로 확정하지 않았다. 최종10m fixture는 기존 테스트구조 안에서 실제 paid hitscan을 검증한다.
- Danmo 입력 원본(내장stdout JSON을 구조화하고 lease/token을 제거): `w241-r1-ammit-hip.json`, `w241-ammit-air-ae20.json`, `w241-ammit-air-ae100.json`; 요약 `vision-air-summary.json`, 공중 서버 상태txt2개, 마지막 `w241-final-neutral.json`.
- 대표 실제 화면: `frames/`의 PNG3개. 무기·플레이어 팔·HUD·ADS 표시를 직접 검수했다. 기존 격리fixture의 세로 비콘/검은 벽은 제품 셰이더 오류로 분류하지 않는다.
- 초기 바닥 미로딩 실패와 중립 복구 기록: `client-floor-failure.log`, `w241-floor-not-loaded-failure.json`, `w241-ammit-hip.json`.

## 플레이·튜닝

- 지상 완전 ADS는 추가 오차0. 공중 ADS는 AE가 높을수록 추가 오차가 감소하고 AE100 이상에서0이 된다. 비ADS에서는 AE100이어도 무기별 지향사격 퍼짐이 유지된다.
- 산탄총/융합소총 고유 패턴, 반동, 투사체 중력·유도는 별도 동작이다. 따라서 AE100이 모든 투사체의 최종 명중을 보장하지는 않는다.
- 기본AE는 공식 manifest 캐시, Precision HC +25는 DDC 근거다. 무기군별 퍼짐 반각·안정성/프레임 배율·선형 AE감쇠는 현행 원작 확정각도를 찾지 못해 Minecraft 임시값으로 구현했다. `src/main/resources/destiny/weapons/w241-accuracy.json`에서 조정 가능하다.

13. 최종 runServer 실서버 재개 완료: 192.168.35.237:25565 LISTEN, online-mode=true, andlist OP4, dynamic-fov-shader=true를 확인했다. BetterModel 초기화·타워 로드·Polymer 팩 생성 성공까지 확인했다(`live-server.json`). Gradle 로그는 줄끝 공백만 정리하여 보존했다. 기존 dirty 변경은 유지하고 이번 Runtime2hunk·GameTest등록1줄·pool slot4만 선택적으로 커밋한다.
