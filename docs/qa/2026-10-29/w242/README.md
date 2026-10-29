# W242 — 원본 리그 기반 사격 반동

## 구현 범위

- 전달본: `/Volumes/qf-ssd/Destiny-Weapon-Fire-Check-2026-10-29/fire-clips.csv`의 81행, 32개 공유 리그 그룹, 54개 고유 animation tag.
- 실제 `source.blend` 32개를 headless Blender 5.4에서 열어 81개 action의 무기 root 본 `4A0810C4`를 평가했다. 무기 FBX와 FirstPerson 팔 FBX를 구분했으며, 원본 SHA256은 전후 동일하다. 사용자 Blender scene은 저장하지 않았다.
- 현재 손 리그와 같은 그룹을 우선해 사격 무기 60종에 일반/ADS 클립을 연결했다. 여러 원본 변형이 존재하며 개별 무기의 원작 변형 선택 조건까지 확보된 것은 아니다.
- 원본 길이를 유지한 61 pose와 quaternion 보간을 사용한다. server 20Hz 갱신과 display 1 tick 보간이며, 60fps 네트워크 재생을 의미하지 않는다.
- 총과 스킨 팔 4개 display에 같은 강체 root를 적용한다. 이번 범위는 공통 반동이며 개별 손목·팔꿈치, bolt/slide 등 내부 부품의 독립 사격 모션은 복원하지 않았다. 기존 카메라 recoil·피격 flinch·탄퍼짐은 유지한다.
- 새 모델, 프레임별 아이템 graph, CMD selector를 추가하지 않았다. 약 514KB의 motion JSON은 서버 전용이며 클라이언트 팩에 포함되지 않는다.

## 좌표와 재생 정책

source X-forward/Z-up을 view -Z-forward/Y-up으로 변환한다. endpoint를 neutral로 삼아 복귀를 보장하고, 이미 반동 상태로 시작하는 Ace ADS에는 첫 1/30초 onset blend를 적용했다. `sourceUnitToView=1.0`은 Minecraft 시각 보정이다. 원작 카메라가 추출되지 않아 원작 camera recoil을 복원했다고 하지 않는다.

한 발당 원본 곡선을 겹쳐 재생하여 연사 때 매번 0으로 끊지 않는다. 중첩 상한 24개, 이동 .35 view meter, 회전 40도는 로컬 표시 보호 정책이며 Destiny 확정 수치가 아니다. 실제 유료 발사마다 한 번 적용하고, 산탄 pellet과 공유 탄약 fusion의 후속 bolt에는 중복 적용하지 않는다. pulse의 별도 유료 bullet은 각각 적용한다.

동일 owner/stack/level을 확인하고 교체·사망·접속 해제·스킬·수동 장전 시 정리한다. 자동 빈 탄창 장전만 이미 발사한 반동 tail을 이어 재생한다. 발사 당시 ADS 혼합값을 유지하여 장전 중 hip 곡선으로 갑자기 바뀌지 않게 했다. 탄약 지급과 장전 시작/완료 시간은 변경하지 않았다.

## 단계별 작업 기록

1. CSV와 실제 Blender action을 대조하고 root·손목·팔꿈치를 확인했다. `source-review.json`, `rig-preview-points.json`, `source-rig-review.png`를 보존했다. 마지막 PNG는 실제 평가 리그의 투영으로, 메시 렌더나 원작 카메라 화면이 아니다.
2. 61 pose를 추출하고 같은 스크립트로 재추출해 서버 JSON과 감사 JSON의 byte 일치를 확인했다. 추출기: `scripts/sample_fire_motion_w242.py`.
3. 기존 worktree slot 4를 최신 통합본으로 갱신했다(29개 변경 파일, 전체 입력 221,440개). Raman은 runtime 3파일, master는 추출·emit 연결·문서·GameTest·중앙 Vision을 담당했다. 새 source JSON 공급은 갱신 기준선에 별도로 등록했다.
4. 첫 worker targeted 9/9, master targeted 9/9와 GameTest 컴파일, 전체 JUnit 2,140/2,140, 실제 GameTest 2/2가 통과했다.
5. 공식 Danmo/4GB 격리 client에서 5종(Ace, Ammit, Recluse, Mindbender, Bad Omens)의 일반/ADS native 사격과 실제 PNG 244개를 캡처했다. 모든 시퀀스가 정상 완료되고 lease·키·native 입력이 중립으로 돌아왔다. 화면에서 Ace 들림/복귀, 연사 파지 접촉, 샷건 복귀를 확인했다.
6. 1차 이미지와 정확한 구간별 검수 결과를 담당 agent에게 전달했다. 큰 파지 분리/flip은 없었지만 Bad Omens의 즉시 자동 장전이 tick0 neutral 이후 반동을 지우는 경로를 확인했다.
7. agent 수정본을 해시 확인 후 통합했다. 자동 장전의 source tail과 발사 당시 ADS를 보존하도록 수정하고 실제 로켓 GameTest를 추가했다. worker 10/10, master targeted 10/10 및 GameTest 컴파일이 통과했다. 수정에 따라 최종 전체 JUnit을 다시 실행한다.

8. 최종 전체 JUnit 2,141/2,141이 통과했다. 로켓 GameTest 최초 실행은 테스트 helper가 Ace를 먼저 장착한 뒤 즉시 로켓으로 교체하여 실제 Handling 지연에 걸렸다. 무기 교체 제한을 제거하지 않고 helper를 처음부터 로켓으로 생성하도록 수정했다. 실패 로그를 보존하고 GameTest만 재컴파일·재실행한다. 제품 코드는 변경하지 않았다.

## 실패·진단 기록

- 최초 GameTest selector namespace 착오로 no matches가 나왔다. 올바른 selector는 `destiny-test:*w242*`이다. 실패 JSON을 별도 보존했다.
- fixture ACK에 `Unchanged`를 기대했으나 실제 명령은 `Marked`/`No blocks were filled`로 정상 수행되어 ACK 대기만 만료됐다.
- contact sheet에서 `usingItem`만으로 사격을 찾으면 양손 crossbow carrier가 누락됐다. 실제 `heldKeys`로 선택하도록 고쳤다. 이는 이미지 선택 스크립트 오류이다.
- 수정 후 첫 Gradle 명령은 `--tests`가 compileGametestJava 뒤에 붙어 CLI 파싱 오류가 났다. test 바로 뒤로 옮겨 정상 통과했다.
- 위 운영/스크립트 실패를 제품 테스트 통과로 세지 않는다. 과거 QA 증거는 수정하지 않았다.

## 2차 Vision과 정리

최종 전체 JUnit **2,141/2,141**, GameTest **3/3**이 통과했다. 담당 agent 수정본 통합 후 같은 5종의 일반/ADS native 입력을 다시 실행해 **238개 PNG**를 캡처했다. 모두 정상 완료 및 중립 해제를 확인했다. `vision2/contacts.png`를 직접 열어 검수했고, 로켓의 초기사격 들림과 장전 연결을 확인했다. 장전 종료 후 별도 캡처에서 1/1발, 예비4발, reloading=false와 원래 파지 복귀를 확인했다.

Vision v1은 Q 입력을 지원하지 않는다. 추가 수동 장전 확인에서 swap_offhand(F)를 잘못 사용해 장전이 발동하지 않은 결과를 실패 기록으로 남겼다. 해당 입력은 장전 통과로 세지 않는다. 수동 장전 정리는 실제 GameTest와 서버 명령 fixture로 검증하고, 실제 Q 키 입력은 이번 검증 범위에 포함하지 않는다. Windows 실기 검증은 이번 배치에서 수행하지 않았다.


서버 명령 fixture는 `execute as WeaponW129QA run destiny weapon reload`로 실행했다. 최초 player 인자 추측은 syntax 오류였으며 올바른 명령으로 재실행했다. 장전 중 12/13·reloading=true, 종료 후 13/13·false와 원래 파지 복귀를 확인했다. 단일 시작 캡처는 정확한 중간 장전 프레임을 보장하지 않는다.

최종 입력 중립을 저장하고 Resistance/Regeneration을 제거했다. 이번에 추가한 forceload 12개를 해제해 잔여 0개임을 확인했다. 소유 Danmo client와 격리 서버를 정상 종료했고 bounded QA coordinator도 종료했다. 독립 48시간 caffeinate PID79904는 유지했다. slot 4는 삭제하지 않고 다음 갱신을 기다리도록 반환한다.

리포지토리에는 반복된 전체 client state 대신 시퀀스 시작/종료·중립·클릭 소비·프레임별 tick/입력 bracket과 전체 sanitized 보고서 SHA256을 남겼다. 전체 로컬 보고서와 개별 원본 PNG는 `/private/tmp/destiny-w235/qa`에 보존되며, 검수 contact와 대표 PNG는 이 폴더에 포함했다.

## 접속용 서버 재개

Java 25의 Gradle `runServer`로 서버를 다시 열었다(session 78615). `online-mode=true`, port 25565, andlist OP4, dynamic FOV shader 활성화를 유지했다. Done·BetterModel 초기화·타워 1,151,116블록 준비·Polymer 팩 생성 성공과 LISTEN을 확인했다. 이번 변경의 client pack 항목은 0개다. 같은 LAN 접속 주소는 `192.168.35.237:25565`이며 서버는 종료하지 않고 유지한다.
