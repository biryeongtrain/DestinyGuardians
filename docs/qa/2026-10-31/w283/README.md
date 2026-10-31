# W283 서버 GCB 마우스 입력 · 무기군 실습

## 구현
- 기존 GCB handshake/version 감지 및 KEY_ATTACK/KEY_USE 이벤트만 사용. 좌클릭 발사, 우클릭 홀드 ADS. 비GCB는 기존 좌클릭 ADS 토글/우클릭 발사를 유지한다.
- 글레이브는 GCB 좌클릭 투사체/우클릭 무료 근접, 검은 기존 native 조작이다. UI 도움말/수신자별 아이템 설명/튜토리얼 안내를 맞췄다.
- 실제 서버 판정 18개 무기군 대표 무기/탄종 설명을 재장전 다음에 추가했다. 장비 escrow attachment와 소유 표식으로 대여/반환/재접속 복구한다. 최종 판정 전 다음 대여품으로 바뀌지 않으며, 교체 전 버튼 해제를 기다린다.
- 클라이언트 소스/배포물은 수정하지 않았다. 테스트만 공식 GCB 4.2.0 JAR을 격리 프로필에 추가했다. 공식 해시는 build-artifact.json에 기록했다.
- 기존 GCB가 client-only 화면/포커스 상태를 전송하지 않는 한계: 300 server ticks(20 TPS에서 15초) 이후 누락된 발사 해제를 취소하고 새 클릭을 요구한다. 즉시 채팅/일시정지 취소가 아니다. 우클릭 ADS는 실제 해제 이벤트까지 남을 수 있다.

## 자동 검사
- 초기 focused GameTest 6/6 통과: initial-six-tests.log.
- 추가 후 focused GameTest 8/8, 관련 JUnit 28/28 통과: targeted.log 및 XML 4개.
- 전체 build에서 1455 GameTests 중 100 required failures. full-build.log. HUD offhand, jump audio, 기존 reload presentation 등의 실패가 남아 있다. 이전 W281의 101개와 숫자를 비교해 이번 변경과 무관하다고 단정하지 않는다. 전체 gate 성공이 아니다.
- 인게임에서 발견한 무기 교체 입력 잔류를 수정한 최종 focused GameTest 8/8 및 jar 성공: final-build.log. 전체 1455개를 다시 실행하지 않았다.
- 최종 JAR과 QA runtime의 변경 class 바이트 일치를 확인했다: build-artifact.json.

## 인게임 환경과 증거 구분
Vision26.3 skill 및 input-control reference의 native KeyMapping/vanilla packet 경로, 사용자 허용 격리 background 모드. `/tmp/destiny-w281-server` 127.0.0.1:25581, `/tmp/destiny-w281-vision` 8102, MinigameQA. 기존 일반 프로필/월드는 변경하지 않았다. 최초 port 비어 있음 확인. CU inventory는 조회했으나 Finder 관측은 권한 거부되어 OS 잠금 해제를 시각적으로 확인했다고 하지 않는다. 전용 Vision actual framebuffer를 사용했다. master keep_awake coordinator 3600초, 자체 종료 flag `/tmp/destiny-w283-coordinator-stop`.

첫 launch는 낡은 runServer argfile이 GCB-server 1.2.0 jar를 가리켜 종료한 뒤 1.2.1로 고쳐 재시작했다. 종료 중 비동기 pack generation의 ClosedChannel 경고는 그 취소된 실행이며 최종 pack 로드 성공과 구분한다.

### 첫 번째 실제 실행
- 운영자 명령은 `/튜토리얼` 및 `/튜토리얼 단계 arsenal` 시작 fixture에만 사용했다. 표적 피해/처치는 서버 발사 명령으로 대체하지 않았다.
- ADS-only native 우클릭 유지/해제: 서버 ADS 0→1→0, 탄창11/11 유지, 02-ads-only.png. 좌클릭 사격으로 표적 처치 후 Ammit 전환: native-01-handcannon.json 및 03-first-kill.png.
- native attempt 02 자동 소총→파동, 03 파동→정찰, 04 정찰 첫 시도, 05 정찰 재시도→기관단총, 06 기관단총→보조, 07 보조→활. 파일의 05~07 label은 최초 예상 순서이며 실제 무기는 이 기록과 server-before-handoff-fix.log를 따른다.
- 08 활 첫 발: 표적 HP9; 09 두 번째 발 후 산탄총으로 전환. 10 산탄총, 11 저격총 통과.
- 12 융합 후 Retraced Path로 교체됐으나 중립 대기 중 physical_user_input으로 control_epoch_changed. 완료 receipt가 아니므로 native-12-fusion.json에 취소를 기록했고 physical-interruption-state.json을 보관했다. 재개 전 추적소총94/94·표적HP20을 확인했다. 사용자 물리 입력과 자동 입력의 경계를 그대로 남겼다.
- 13 추적→유탄. 14~16 유탄 세 발로 표적 처치(HP20→8.976834→0.066758→처치). 17 글레이브 투사체→기관총. 중화기 탄종 설명/슬롯3는 after-17-glaive.png.
- 18 기관총→중화기유탄, 19 중화기유탄→로켓, 20 로켓→선형융합. 21 선형융합 처치 뒤 아직 누른 RMB가 새 검의 강공격으로 이어져 검 탄약46과18/18 진행이 나타남. 이를 정상 검 실습으로 수락하지 않고 수정했다. after-21-linear-fusion.png는 이 결함의 증거다.

### 최종 재검증
- 최종 JAR과 동일 class로 서버/공식 GCB 4.2.0 클라이언트를 다시 실행했다. 운영자 `단계 linear_fusion_rifle`로 마지막 두 무기만 fixture 배치했다. 앞선 16종을 최종 빌드에서 전부 재실행한 것은 아니다.
- 선형 융합 좌클릭+우클릭 유지 중 표적을 처치해도 17/18에서 무기를 유지하고 “버튼을 놓고 설명 듣기”를 표시했다(final-01-hold-blocks-handoff.png). 해제 후 새 검이 탄약50/50과 살아 있는 표적으로 시작했다(final-02-sword-ready.png, server-final-gcb.log). 검으로 의도하지 않은 강공격이 넘어가지 않았다.
- 해당 handoff sequence와 검 입력 시도는 physical_user_input으로 완료 receipt가 취소되었다. 빈 출력 파일을 성공으로 남기지 않고 취소 설명으로 기록했다. 검 재시도에서는 실제 KEY_ATTACK true/false 전송 뒤 표적이 사라지고 기동 훈련10/15로 넘어갔다(final-03-sword-result.png). 원래 빈 인벤토리[]도 복원됐다. 서버/화면 결과는 관측했으나 물리 입력 개입이 있어 이 sequence를 무중단 자동 입력 통과로 세지 않는다.
- 첫 final fixture 직후 호출은 world transition의 INELIGIBLE로 입력 전 거절됐다. 이후 eligible 상태를 확인한 다음 실행했다. final-after-sword-state.json에 lease 해제/빈 heldKeys를 확인했다.
- GCB JAR만 격리 mods에서 빼고 같은 QA 클라이언트를 재실행했다. client-final-vanilla.log의 GCB 미설치 안내, GCB 초기화 부재와 native 결과를 확인했다. 클라이언트 코드는 수정하지 않았다.
- 비GCB 좌클릭2틱+해제10틱: sequence 성공, Austringer11/11 유지, ADS1.0. 우클릭80틱+해제40틱: sequence 성공, 유지 중7/11·ADS1.0, 해제 후 표적 처치 인정/Ammit33/33 교체. vanilla-native-01/02 JSON, vanilla-01/02 PNG 및 server-final.log. 튜토리얼도 “우클릭 사격” 안내를 유지했다.
- 종료 전 `/튜토리얼 나가기`로 대여품 회수 및 원래 인벤토리[] 복원을 확인했다. vanilla-final-neutral-state.json의 leaseActive=false, heldKeys=[], pendingSteps=0, 모든 nativeInput=false를 확인했다. QA client/server를 종료하고 자체 keep_awake coordinator 종료 flag를 만들었다. 일반 프로필/외부 awake assertion은 변경하지 않았다.

## 미검증 범위
직접 스피커 청취, OS 물리 클릭 자동화, 다중 접속 부하/FPS 인증은 수행하지 않았다. 신규 무기군 설명은 자막이며 새로운 한국어 성우 음원이 아니다. 관련 동작 검증을 전체 상용 품질 인증으로 확장하지 않는다.
