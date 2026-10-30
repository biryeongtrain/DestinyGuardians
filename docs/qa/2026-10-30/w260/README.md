# W260 시련의 장 — 점령

상태: 점령전 플레이 흐름과 대표 시각 경로 검증 완료. 운영 서버 재개와 커밋은 아래 최종 기록을 따른다. 모든 능력·인원 구성의 전수 검증을 뜻하지 않는다.

## 사용자 목표와 수락 조건

| 요구사항 | 구현/검증할 실제 동작 | 현재 증거 |
|---|---|---|
| 탑 → 시련의 장 | `/메뉴` 참가 버튼과 `/시련의장`, 플레이 후 탑 복귀 | r4 native 메뉴 참가, r8 실제 경기 후 탑 복귀 확인 |
| 단일 세션 | 서버당 점령전 state 하나, 중복 참가 멱등 | ControlMatch 27 tests 통과 (`74a00e18`) |
| 무제한 참가 | 팀/세션 인원 제한 없음, 작은 팀 배정 | 모션 배우 수와 참가 상한을 분리 |
| 중간 참가 | 진행 중 점수·거점을 초기화하지 않고 합류 | r3/r4 실제 런타임 중간 참가·기존 상태 보존 확인 |
| 점령 규칙 | A/B/C, 경합, 중립화, 점령, 처치 배점, 타이머, 결과 | 순수 상태27 tests·A점령/적처치 실제 런타임 확인 |
| 사망/부활/퇴장 | 생명당 처치 1회, 부활 대기, 정상 나가기/접속 종료/서버 종료 복구 | r6 강화 GameTest 통과, r8 실제 client/server 위치 일치 확인 |
| 맵과 재질 | 전달 GLB + 재질/텍스처 베이크, 보행 가능한 바닥·천장·스폰·거점 | 자벨린-4 761,803블록 생성·보행 확인 |
| 시작 연출 | 맵 소개 → 양측 수호자 원본 모션 → 정상 카메라 복귀 | r8 자기·아군·적 배우와 소개 HUD 표시, 정상 카메라 복귀 확인 |
| 적 스킬 빨강 | 양쪽 관전자에게 상대편만 빨간 표시, 아군 원래 색 | r8 같은 화면의 아군/적 지팡이·가닥·방벽·균열·수류탄 비교 통과 |
| 실검증 | 상태 단위 검사, 서버 통합 GameTest, Danmo4GB Vision | 중앙42+carrier8, 후속24 회귀 통과·강화 lifecycle1490틱·native 이동/부활 확인 |

## 자료와 해석 범위

- `/Volumes/qf-ssd/Crucible-Assets-2026-10-28`: 32개 일반 PvP 맵을 포함한 39개 맵의 메시·배치·음원. 자벨린-4를 첫 플레이 가능한 맵으로 만든다. 색상 GLB는 휴리스틱 결과이므로 완전한 원작 재질로 간주하지 않는다. 자동 파이프라인과 원본 대응을 남겨 다른 맵을 추가할 수 있게 한다.
- `/Volumes/qf-ssd/Destiny-Crucible-Materials-2026-10-29`: 재질·텍스처·셰이더 참고. 원본 shader를 Minecraft에서 실행하는 것이 아니라 UV/대표 표면 색을 베이크하여 블록으로 환산한다.
- `/Volumes/qf-ssd/Destiny-Crucible-Intro-Handoff-2026-10-29/HANDOFF.md`: Trials 입장 연결 몸체 6클립, 각446프레임. 일반6v6 완성 컷씬·플레이어 슬롯·카메라 궤적은 미복원이다. source.blend 직접 평가 후 모션을 변환하고, 카메라와 팀 배치는 직접 구성한 것으로 표시한다. 보조4/2관절 트랙을 임의로 카메라나 플레이어 동작으로 분류하지 않는다.

## 규칙 출처와 서버 정책

[Bungie 활동 안내](https://help.bungie.net/hc/en-us/articles/360048720992-Destiny-2-Activities)의 Control 설명에서 거점 점령당 팀1점, 더 많은 거점을 보유할수록 처치 점수 증가,150점 승리를 확인했다(2026-10-30 조회). 10분 제한·1/2/3점 처치·중립화 및 점령 시간은 별도 로컬 튜닝/2차 자료와 구분한다. 인원 무제한과 단일 세션은 사용자의 명시적 변형이다. Zone Control의 지속 점수 규칙과 혼동하지 않는다.

서버당 한 경기, 두 팀 최소1명씩이면 인트로 시작. 경기 도중 참가자는 기존 점수/거점을 유지하며 작은 팀에 들어간다. 한 팀이 비면 즉시 종료하지 않고 재접속/추가 참가 유예를 둔다. 경기 결과 뒤 탑으로 돌아온다. 맵은 Fantasy 임시 월드에 생성하고 탑/오버월드 블록을 변경하지 않는다. 경기 내 아이템 보존 및 아군 피해 차단을 적용하고 참가 전 게임모드/스코어보드 팀을 복원한다.

## 병렬 작업과 이전 파일 보존

고정 worktree slot1: 맵, slot2: 점령 상태 로직, slot3: 원본 모션/인트로. master: Runtime/탑 메뉴/팀·피해/적 색상/음원/HUD/중앙 검증. worker는 서버·Vision·공유 의존성을 조작하지 않는다.

초기 refresh는 slot2/3의 이전 fixture 수정이 메타데이터 소유 범위 밖에 있어 중단됐다. `/private/tmp/destiny-w260/reconcile`에 각 drift 목록과 이전 바이트/메타데이터를 보관했다. slot2의 추가27경로, slot3의 추가22경로를 검토했다. HeatingUpW177의 로컬변수 `dir`→`forward` 수정만 최신 통합본과 달랐고, 나머지는 main과 동일했다. 해당 한 파일을 최신 통합본과 맞춘 뒤 검증한 경로만 이전 소유 목록에 추가하고 정상 refresh를 다시 실행했다. main이나 다른 프로젝트/워크트리는 삭제하지 않았다.

## 서버/리소스 운영

기존 W259 `runServer`의 console relay로 접속자0명을 확인한 후 정상 `stop`했다. 빌드 중 운영 서버 소스를 재사용하지 않는다. 테스트 서버/클라이언트는 각각4GB를 유지한다. 새 운영 기동은 구현 및 검증 후 별도 기록한다.

샤크스 한국어14음원을 자막 의미/태그에 따라 선별했다. 원본 SHA-256 일치, 총401,460바이트. 개별 음원의 선택은 재구성한 서버 이벤트 배정이며 원본 Wwise event graph를 완전히 복원했다는 뜻이 아니다. 14파일 디코딩은 통과했다. 이벤트 연결은 검사했으며 실제 음성 청취 평가는 미수행이다.

## 최초 검증 계획 (이하 단계별 이력)

1. 각 worker delta 통합, Java25 컴파일과 targeted 상태/자산 검사.
2. 실제 서버에서 참가·대기·양팀 시작·3거점 점령/경합·처치점수·부활·중간참가·퇴장/복귀 회귀.
3. 맵/인트로 실제 PNG, 양팀 시점에서 적 수류탄·방벽/균열·궁극기 색상, 팩 로딩/음원 재생 확인.
4. 1차 이미지 담당 worker에 전달 → 수정/확인 → 2차 Vision. 카메라/입력/시각모델/이벤트 cleanup 확인.
5. 검수 완료 범위만 커밋. 미완료와 기존 별도자산 테스트 실패4개를 섞지 않는다.

## 중앙 통합·1차 QA

Control/Intro7파일을 기준 해시 확인 후 통합했고, `compileJava compileTestJava` 통과. 이어 점령 JUnit27/27 + 모션설치1/1, GameTest 소스 컴파일이 통과했다. 첫 Gradle 호출은 `--tests` 옵션을 compile 작업 뒤에 잘못 놓아 실행 전 실패했고, 올바른 task 순서로 수정했다.

파티클22파일을 별도 기준 해시와 대조해 통합했다. ability callsite는 소유자를 전달하며 적에게만 빨간 파티클을 선택한다. 원래 색칠할 수 없는 vanilla 불꽃/portal은 적에게 red dust로 대체한다. 모델은 관전자별 `_enemy` stack/tracker를 사용한다. 중앙 재컴파일 및 양팀 실검증은 진행 중이다.

Danmo/OpenGL4GB에서 `tower-ready.png`, `control-waiting.png`로 탑→자벨린-4 전송·실제 맵·대기 HUD를 확인했다. 첫 HUD가 체력바에 붙어 Y200으로 조정했고 2차 확인은 남아 있다. worker가 PNG를 보고 Alpha 스폰 yaw를 -105도로 조정했다. 원본 roof는 상하 표면과 G-buffer material 근거상 시설 외피로 분류하여 보존했다. 소개 카메라는 원본 벽을 통과하지 않는 경로로 보정했다.

첫 통합 GameTest는 중간 참가·아군 차단·A 점령까지 진행하고 tick560 적 사망에서 실패했다. 기존 fixture의 PlayerList/native connection tick 부재를 제거하고 실제 placeNewPlayer 경로로 교체했다. 재검증 전이므로 사망/부활 통과로 보고하지 않는다.

첫 QA 서버 종료는 `Saving worlds`에서 대기했다. 같은 PID82691의 두 스레드 덤프와 서버 스레드 진단에서 `destiny:tower shouldTick=false, loaded=0, hasWork=true`를 확인했다. 허용된 격리 QA에만 attach한 외부 진단 agent로 해당 월드의 tickWhenEmpty를 true로 돌리자 정상 종료(exit0)했다. 원인에 맞춰 Tower/Crucible SERVER_STOPPING에서 작업 배출을 활성화한다. 별도 QA 원본/운영 월드 파일을 삭제하거나 강제 종료하지 않았다. 근거 `/private/tmp/destiny-w260/stop-probe/`.

샤크스14 OGG 전부 ffmpeg로 디코딩했고 유한 PCM/비영 피크를 확인했다. 음성 청취 여부는 false로 유지한다.

## 2차 통합 준비

- 인트로 관전자 delta를 SHA-256 기준 확인 후 통합했다. 카메라 준비·청크 진입·샷 전환·중간 참가마다 해당 배우의 현재 포즈를 재전송하며 원본 모션을 다시 시작하지 않는다. PlayerAnimations의 정확한 tracker 연결은 별도 통합 중이다.
- 26.3 ServerPlayer bytecode에서 `isChangingDimension()` 또는 `!hasClientLoaded()`이면 피해가 거절되는 것을 확인했다. embedded fixture는 실제 양수 teleport ID에만 응답하고 차원 respawn 뒤 player-loaded 응답을 보내도록 수정했다. CameraViews의 음수 가상 ID는 서버 몸체 위치에 적용하지 않는다. 실제 재실행 전이므로 이 수정만으로 실패 해결을 확정하지 않는다.
- 통합 GameTest에 상대 팀 퇴장→30초 유예→승리 결과→10초 뒤 탑 자동 복귀를 추가했다. 전투/부활/수동 퇴장과 동일 실제 런타임 경로에서 검사한다.
- 2차 QA는 `/private/tmp/destiny-w260/vision-r2`에 새 로그를 사용하며 기존 1차 증거를 덮어쓰지 않는다. 기존 소유 coordinator PID80509가 실행 중임을 확인했고 Mac은 Finder 데스크톱 상태다.

2차 중앙 검사에서 점령27, 파티클5, 모션설치1, 거점음성1 총34개가 통과했다. GameTest는 26.3 teleport ACK가6필드임을 반영한 뒤 컴파일 통과했다. 이전의1필드 호출 컴파일 실패 로그도 보존했다. 실제 통합 테스트는 진행 중이다.

공통 소개 무대는 Alpha(93.5,81,13.5), Bravo(101.5,81,13.5), yaw0으로 구성했다. 맵100틱→양팀 wide130틱→Alpha85틱→Bravo85틱. 원본의 지하/수평 root 진입을 잘라내지 않으며, 최종 착지 높이와 카메라/배우 proxy 시선은 베이크 voxel로 검사했다. 실제 모델 자기 시점의 carrier 위치와 손/얼굴 방향은 Vision에서 확인한다.

샤크스 음성의 미연결 상태였던 우위/전면점령4종을 거점 소유 변화에 연결했다. 최종 상태의 가장 큰 변화1개만 시청자 팀 기준으로 재생하므로 동시 점령의 중복 음성이 생기지 않는다.

2차 서버에서는 tick560 실제 적 처치/점수 반영까지 통과했다. 이후 embedded 연결의 keep-alive 미응답으로30초에 A/B가 끊겨 tick670 부활 검사가 실패했다. 실제 keep-alive ID 응답을 fixture에 추가한다. 프로덕션 무적/접속 제한을 우회하지 않는다. 실제 Vision client는 QA의 max-players=2 때문에 입장이 거절되어 입력을 실행하지 않았다. QA 설정만8명으로 늘려 fake3+실제1 동시 검증을 허용한다.

2차 서버 정상 stop은 약2초 내 exit0을 반환했다. 이전 Fantasy empty-world 저장 대기 수정이 새 소스로 동작함을 확인했다. client도 소유 relay로 종료했다. 정지 후 궁극기 손 소품13종의 viewer별 빨간 모델 전송2파일을 기준해시 확인 후 통합했다. 갑옷/스킨/실제 인벤토리는 변경하지 않는 ITEM_MODEL 투영이다.

## 3차 서버·Vision

- 중앙40/40 및 GameTest 컴파일 통과. 실제 통합1개는1490틱에서 정상 완료: 중간 참가, 아군 피해 차단, A점령, 적 처치1점,5초 부활, 복귀 무적, 수동퇴장,30초 유예 후승리,10초 결과뒤탑복귀. 뒤이은 real-client 상대역 fixture도90초 정상 종료했다.
- embedded fixture의 텔레포트 응답에서 서버 현재좌표를 사용해 이동 경고830건이 남았다. 이것을 숨기지 않고 실제 ClientPacketListener처럼 수신 PositionMoveRotation을 누적한 좌표로 응답하도록 보완한다. 부활 검사에도 실제 바닥 안전성 검사를 추가했다. 기존 pass를 새 강화검사의 pass로 간주하지 않는다.
- Danmo/OpenGL4GB: intro25장 확보, 경기 후 native forward 입력이 완료되고 키/lease가 중립으로 돌아왔다. 실제 PNG에서 상대모션은 보였으나 자기 배우가 누락되고 일부 컷은 상단 전경·우측worldborder가 들어온다. intro/map worker에 검수이미지를 전달했다. 시작연출 수락은 보류한다.
- 적 궁극기 색상 캡처는 상대역90초 종료 후 잘못 실행됐다. bot 명령은 No entity/player 반환이며 해당 PNG는색상검증증거가아니다. 추가로 console tp의 차원문맥을 빠뜨려 실제 QA 캐릭터를 overworld 공중에 옮겨 사망시켰다. 현재 QA계정의 DeathScreen 복구가 필요하며, 다음 fixture명령은 반드시 execute as ... at @s를 사용한다. 운영 계정/월드는조작하지않았다.
- client/server는 소유 relay로 종료했고 서버는다시약2초내exit0. 새 저장대기수정은2차연속정상종료.

## 4차 강화 검증과 수정

- 실제 수신 PositionMoveRotation을 누적해 ACK하는 fixture로 교체한 뒤 가짜 플레이어의 이동 경고가 사라졌다. 강화한 안전 바닥 assertion은 tick670에 실패했다. 따라서 r3의 완료 결과는 위치 안전성까지 증명하지 않는다.
- 실제 Vision 계정에서도 kill→5초 부활을 실행했다. client는 arena(-117.5,84,42.5)를 보지만 서버 debug는(0.5,200.1,0.5), ground=false였다. fixture만의 결함으로 분류하지 않는다. 정확한 위치 덮어쓰기 원인은 아직 확정하지 않았다. Fabric AFTER_RESPAWN은 PlayerList.respawn TAIL임을 bytecode로 확인했다.
- r5 Runtime은 AFTER_RESPAWN에서 새 player를 기록하고 다음 END_SERVER_TICK에 arena로 전송한다. 전송 전 canAct=false이며 중간 차원 전환을 퇴장 처리하지 않는다. 중앙40tests/compileGametestJava 통과, 실런타임 결과 대기.
- r4 실제 `/메뉴` 화면에서 native forward/attack으로 시련의 장 참가에 성공했다. 다만 차원 변경에 따른 input runner 취소를 전체 sequence 성공으로 세지 않는다. 버튼 문구 잘림은 단축 예정.
- r4 적 아크 시전 PNG에서는 빨간 dust는 확인했으나 손의 지팡이는 청록색으로 남았다. 담당 worker에 이미지와 실패를 전달했으며 수락 보류.
- r4 재접속으로 QA 계정이 살아서 탑으로 복구됨을 확인했다. client/server 모두 소유 relay로 종료했고 서버 exit0.
- 검수 완료된 순수 상태/27tests만 `74a00e18`에 커밋했다. 나머지 통합 범위는 미완료다.

## 5차 준비

맵 worker의 r4 야외 무대 좌표를 적용했다. Alpha(32.5,85,85.5), Bravo(40.5,85,85.5); map100→wide130→Alpha85→Bravo85 유지. 전체 화면 ray 샘플로 천장/경계 가림을 확인했으나 실제 PNG 수락은 남았다. 원본 terrain과 모션 root를 변형하지 않았다.

5차의 지연 전송만으로는 강화 GameTest가 통과하지 않았다. 26.3 ServerGamePacketListenerImpl 바이트코드를 대조한 결과, `PlayerList.respawn`은 새 플레이어를 반환하고 **호출자인 바닐라 handleClientCommand가 connection.player 교체·resetPosition·client-load timer 재시작**을 수행한다. Runtime의 직접 호출은 반환값을 버려 네트워크 연결이 옛 객체를 계속 가리켰다. Runtime을 PERFORM_RESPAWN의 바닐라 handler 호출로 바꾸고 fixture에 `next.connection.getPlayer()==next` 검사를 추가했다. r6 재검증 전이다. r5 실제 QA 계정은 접속 직후 죽은 상태여서 별도 소유 recovery fixture로 복구했고 탑 복귀 성공 후 종료했다.

6차 통합 준비: 손 소품은 BetterModel의 `bone(String)`이 태그를 제거한 이름으로 비교하는데 raw 태그 이름을 전달해 항상 null이던 결함을 수정했다. 기존 LimbEquipment와 같은 rawName predicate를 사용한다. 중앙42tests(기존40+본 바인딩2)와 GameTest 컴파일 통과. 자기 배우는 별도 packet-only 표시기준점으로 limb passengers만 옮기며 HUD/다른 배우는 유지한다. 추가8개 packet regression도 통과. 실제 클라이언트 수락은 진행 중이다.

6차 강화 lifecycle GameTest가1490틱에서 정상 완료했다. 중간 참가·A점령·아군 피해 차단·적 처치 점수·5초 부활뿐 아니라 **교체된 connection.player 동일성 및 실제 안전 바닥 도착** 검사가 통과했다. 상대퇴장 유예→승리→탑 복귀 및 원래 모드/팀 복구도 통과. [결과](gametest-r6.json). 실제 Vision 부활 위치 교차 확인은 별도로 진행한다.

## 6차 실제 화면 결과

- 실제 계정 kill→자동 부활 후 client와 server 모두(-117.5,84,34.5), alive/ground/eligible true. 기존 위치 불일치가 수정됐다.
- 인트로14/18 PNG에 자기 배우와 상대 배우 모두 표시된다. 새 야외 무대는 기존 천장 전경/worldborder 문제를 제거했다. 담당 worker에게 2차 검수를 전달했다. 인트로 HUD가 WAITING 문구에 남는 문제는 CameraViews 필터가 HUD 업데이트를 버리는 경로로 확인해 r7에서 owned sending 범위로 보완한다.
- 적 방벽·균열의 모델/파티클 및 수류탄 파티클이 빨간색이다. 적 아크 지팡이는 일부 청록 픽셀이 남아 worker 재검수 중이다.
- 후속 native 이동은 transport/중립 cleanup은 완료했으나 상대 fixture가90초에 종료되어 forfeit pause 중이었고 실제 이동은0이었다. 이를 gameplay 이동 통과로 세지 않는다. 같은 이유로 자기 균열 시전도 false였다. 자기 원색 검증으로 사용하지 않는다.
- r7 상대역 수명을300초로 늘리고 같은 팀 상대역을1명 추가해 동일 세션에서 본인/아군/적 비교를 수행한다. 소유 QA fixture이며 세션 인원 제한을 변경하는 코드가 아니다.
- 첫 visual script는 플레이어 개인 메시지를 console ACK로 기다려 timeout했다. 실제 참가 상태를 확인하고 다음 스크립트로 넘어갔다. 입력 중복이나 효과 시전 중복은 없었다.
- 메뉴 나가기 후 실제 탑 복귀 PNG 확인. 클라이언트/서버 소유 종료, 서버exit0.

## 7차 회귀와 색상 마감

전체 JUnit2278개 중7개 실패를 확인했다. 메뉴 새 CRUCIBLE node30 및 샤크스14파일의 정확 provenance를 기존 검사에 반영했고 황금총 HUD 생성기를 실제 재실행해 현재 소스 기록을 갱신했다. 관련24tests/compileGametestJava 통과. 기존 W112 silhouette/W115 surface/W168 Austringer/W179 Mindbender4실패는 그대로 남아 있으며 전체 pass라고 보고하지 않는다. [전체 실행](full-r7.json), [24개 재검사](regression-r7.json).

r6 아크 지팡이는 본체는 빨갛게 바뀌었지만 별도 전기 가닥 자산에 enemy variant가 없어 청록색이 남았다. worker가 arc_filament_h25/void_filament_h25/void_spark_h25에 적 전용 item/model/PNG9개를 만들었다. 기존 geometry/UV/alpha를 보존했고3개 PNG 총12288픽셀 알파 일치, source/output SHA를 확인해 통합했다. [출처](../../../../art/abilities/w260-energy-enemy.json). 원본 색은 본인/아군에 유지한다.

7차 실제 검증은 추가 아군 fixture의 이름 `ControlVisionAlly`17자가 Minecraft player_info_update의16자 제한을 넘어 encoder disconnect로 실패했다. 제품 색상 비교 성공으로 세지 않는다. `ControlAllyQA`로 수정하고 fixture login에 이름 길이 검사를 넣었다. 서버/클라이언트 정상 종료 후8차 재시작한다. 첫7차 클라이언트도 서버리스닝 전 접속해 거절됐으므로 readiness 확인 후 소유 세션만 재시작했다.


## 8차 최종 Vision 수락

Danmo/OpenGL·클라이언트4GB·서버4GB에서 실제 QA 1명과 아군/적 상대역 각1명을 배치했다. 서버 ready를 확인한 뒤 접속했다.

- [인트로](vision-r8/intro-14.png): 본인·아군·적 모델, 원본 입장 포즈, 올바른 `시련의 장 / 점령 · 자벨린-4` HUD 표시. 검수 프레임에 천장/월드보더 가림 없음. 맵 담당은 r6 동일 좌표 구도를 수락했다.
- [아크](vision-r8/team-arc-3.png): 왼쪽 아군 청록 지팡이·전기 가닥, 오른쪽 적 빨간 지팡이·가닥·dust. 색상 담당의 2차 이미지 검수도 수락했다. 작은 청록 소용돌이는 AMPLIFIED→파티클 표시가 활성인 바닐라 SPEED II 경로로 확인했다(Statuses.java:48). 별도 상태효과 입자는 원색이 남는다.
- [방벽](vision-r8/team-barricade.png), [균열](vision-r8/team-rift.png), [수류탄](vision-r8/team-grenade-3.png): 같은 화면에서 아군 원색과 적 빨강을 비교했다. [본인 균열](vision-r8/self-rift.png)은 원래 흰색 유지.
- native 전진10틱+중립3틱을 완료했다. 위치는(-117.5,84,34.5)→(-115.4185447283675,84,33.942418366106935)로 이동했으며 서버 기록과 일치했다. [상태](vision-r8/playing-native-positions.json).
- kill 후5초 자동 부활: 실제 client/server 모두(-117.5,84,42.5), alive/ground/eligible 확인. [서버](vision-r8/respawn-server.json)·[클라이언트](vision-r8/respawn-state.json).
- [탑 복귀](vision-r8/tower-return.png) 후 dimension=destiny:tower, 자기 카메라·생존·접지 확인. [정리 상태](vision-r8/cleanup-state.json)는 lease=false, heldKeys=[], pendingSteps=0, 모든 native 키false다.

첫 r8 visual_round는 아크가 아직 활성인 동안 직업 변경을 요청해 제품이 정상 거절했다. console ACK 대기 timeout으로 해당 스크립트는 exit1이다. 궁극기 종료 후 직업 변경을 확인하고 visual_finish에서 방벽·균열·수류탄·자기 효과·복귀를 이어서 완료(exit0)했다. 단일 스크립트 전체 성공으로 기록하지 않는다.

격리 QA 서버는 정상 stop/exit0, 소유 client는 wrapper stop(SIGINT/-2)으로 종료했다. 운영 사용자나 일반 프로필은 종료하지 않았다.

## 최종 범위와 한계

- 자벨린-4 한 맵, Control 단일 세션, 중간 참가, 세션 자체 참가 상한 없음. 운영 서버 max-players=20과 세션 정책은 별개다.
- 순수 상태27검사, 중앙 관련42검사, 자기 배우8검사, 후속24회귀 및 강화 GameTest1490틱을 통과했다. 전체 JUnit2278개 실행의7실패 중 이번 관련3건만 후속 회귀로 해결했다. 기존 W112/W115/W168/W179 자산 불일치4건은 남아 있다.
- Trials 전달6클립을 이용한 직접 구성 입장 연출이며 원작6v6 컷씬 전체 복원이 아니다. 모든 화면비/FOV/대규모 인원 배치를 검증하지 않았다. r6 복귀 직후 일부 청크가 잠깐 비었다가 복구되는 전환 품질 한계가 있었다.
- 대표 아군/적 VFX 비교를 완료했으며 모든 능력 조합 전수 검증·Windows 검증·사운드 청취 평가 완료를 주장하지 않는다.
- 테스트 대상은 기존 미커밋 작업을 포함한 통합 working tree다. W260 변경만 분리 커밋하므로 clean HEAD 전체가 동일하게 검증됐다고 해석하지 않는다. 다른 작업의 변경은 보존한다.

색상 담당은 r8 방벽·균열·수류탄·본인 균열의 색 구분도 수락했다. 수류탄은 주변 입자 표본이며 투사체/전체 수명 검증은 아니다.

## 최종 커밋·운영 서버 재개

점령 상태와27tests는 `74a00e18`, 런타임·맵·인트로·적 색상·검수 증거는 `a87f4f98`에 커밋했다. 기존 무관한 dirty/untracked 작업은 보존했다. 일부 공유 파일은 W260 delta만 index에 분리해 커밋했으며 테스트는 통합 working tree 기준이다.

`runServer`로 운영 서버를 재개했다: **192.168.35.237:25565**, online-mode=true, andlist OP4, 실제 JVM 최대 힙4GiB. BetterModel 로딩과 Polymer 팩 생성 완료를 확인했다. 최종 운영 팩은 **63,726,887 bytes**이며 샤크스14음원이 포함되어 있다. [기동 확인](server-start.json). 서버는 켜 두고 격리 QA client/server 및 이번 소유 잠자기 방지 coordinator만 정상 종료했다. 고정 worktree는 다음 작업용으로 보존했다.
