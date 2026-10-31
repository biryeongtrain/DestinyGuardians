# W285 궁극기 회전 및 GCB 탑승 예측

서버 코드만 변경. 클라이언트 소스/JAR는 수정하지 않았다. SSD 원본은 APFS 손상으로 읽을 수 없고 유일한 사본이므로 직접 수리/쓰기 없이 보존한다. 무기 장전 원본 Blender 검수와 수정은 아직 진행할 수 없다.

## 변경

- 헌터 아크도 다른 궁극기처럼 시선 yaw와 상체 pitch를 따른다. 하체는 수직을 유지한다.
- 화면의 고정된 몸체가 움직이는 rig를 가리고 있었다. 투명화 효과를 이용한 격리 진단에서 구분했고, 제품에서는 효과/실제 invisibility를 바꾸지 않고 owner의 모델 spawn 이후 BetterModel의 metadata/equipment disguise를 한 번 재전송한다. 종료 복원은 BetterModel의 기존 경로를 사용한다.
- camera stop 때 disguise 세션 상태를 즉시 초기화해 같은 tick 재시작도 재투영한다.
- GCB handshake로 확인한 4.2 이상은 보이지 않는 packet-only size-one Slime을 carrier로 사용한다. 기존 GCB MountPrediction이 Mob→local player→BM limbs에 적용된다. 실제 서버 플레이어는 탑승하지 않는다.
- carrier seat는 실제 passenger attachment로 보정하며, 서버 충돌 처리 후 변위를 velocity로 보내고 정지는0으로 보낸다. 충돌 검사하는 view camera는 별도 ItemDisplay이다. 구버전/미확인/바닐라는 기존 Display carrier를 유지한다.

## 실제 Vision 결과

Skill: `/Users/qf/.codex/skills/copper-golem-vision-client-fabric-26-3/SKILL.md`.
Minecraft26.3, 공식 GCB4.2.0, 승인된 격리 background native-input, QA server127.0.0.1:25581 / Vision8102. 실제 PNG를 열어 검수했다. F(swap_offhand)·attack·이동은 native KeyMapping overlay 입력이다. 직업/원소/게이지/평화 난이도/시작 좌표는 서버 fixture 명령으로 준비했다. OS 키 입력·음성 청취 증거는 아니다.

- `final-titan-yaw-retry`: 투명화 효과 없는 타이탄 아크. yaw0→90→180→0에서 뒤쪽 색면/굴곡 자세가 유지되며 배경만 바뀐다. 02/05/08/11 PNG 비교.
- `final-hunter-arc`: 헌터 아크 발동, 위/아래35도 조준, 공격, 질주/정지. 04/06 PNG에서 상체와 장비의 상하 방향을 확인.
- `final-warlock-solar`: 워록 태양 발동, 상하 조준, 공격, 전진/정지/후진/정지. 전체 캡처에서 camera151/vehicle150 유지. X500.5→504.42에서 정지→500.11에서 정지.
- `final-built-smoke`: 마지막 lifecycle 보강까지 포함한 최종 클래스에서 재검증. yaw/pitch, 질주 후 벽 X509.7에서 정지, 후진, 점프 Y81.02→80 착지 모두 동일 camera52/vehicle51 유지. 09/12 PNG 확인. 최종 JAR와 실행 클래스 바이트 일치 확인.
- `final-restored`: 자연 종료 후 camera=player, vehicle=-1, 입력 lease 해제. 관찰용 third_back 전환으로 원래 일반 스킨이 다시 보이는 실제 PNG 확인 후 first로 복원.

구체적인 한계: 표본 PNG는 연속 영상/FPS percentile이 아니다. 보간 기능의 적용과 이동/정지 동작을 확인했으며 지연 감소 수치를 측정하지 않았다. 바닐라/구버전은 자동 fallback 검사만 수행했고 실제 별도 클라이언트는 실행하지 않았다. 모든9개 궁극기/다인원 부하/팔 리깅 품질 전체를 인증하지 않는다.

## 진단 및 제외한 시도

- 초기 `titan-yaw` 등은 몸체 중복 문제를 재현한 실패 증거. 패킷 누락이라는 초기 가설은 서버→wire→읽기 전용 JDI에서 실제 Display yaw가 전달됨을 확인해 폐기했다. JDI로 클라이언트 메서드 호출/필드 변경은 하지 않았다. 긴 VM suspend로 연결 timeout이 생긴 진단은 성능·성공 근거에서 제외했다.
- `arc-turn`, `void-turn`: DeathScreen으로 입력 부적격. `titan-arc`: 이전 궁극기가 끝나기 전 class 변경이 거절되어 Titan 근거가 아니다.
- `final-titan-yaw`: 초기 접속 로딩 중 부적격. 성공은 retry 폴더에 따로 보존.
- `final-titan-pitch-move`: 이미 궁극기 종료 뒤의 일반 이동. 궁극기 pitch/mount 증거로 사용하지 않는다.
- `final-hunter-move`: 첫 프레임 벽 도착 뒤 궁극기 종료. 이후 점프/착지는 일반 이동이며 mount의 점프 검증으로 간주하지 않는다.
- 임시 `W285Debug`와 속성 기반 로그는 최종 소스에서 제거했다.

## 자동 검사 / 정리

최종 targeted4/4 통과. 최종 전체 build는1459개 중100 required failures로 실패했다. W283100개와 비교하면 W270 menu cleanup 실패가 추가되고 same-kind alias 실패가 사라졌다. 개수가 같다는 이유로 동일 실패라고 하지 않는다. 새 W2854개는 전체 실행에서도 실패 없음. `full-gate-comparison.json` 참조.

초기 전체 build:1458 tests/101 required failures(이전 W283100개보다 W270 audio menu cleanup1개 증가). 전체 통과로 표시하지 않는다.
첫 새 body-packet 테스트는 가짜 플레이어를 BM PlayerManager에 등록하지 않아 실패했다. 실제 접속 경로와 같은 등록을 fixture에 추가한 재검증은4/4 통과했다. 마지막 sharedFlags 패킷과 실제 서버 invisibility 유지, 같은 tick stop의 상태 초기화 및 최종 복원을 검사한다.

QA awake: keep_awake.py7200초 master coordinator, caffeinate PID36845; 일반/타 소유 assertion은 건드리지 않는다. 19:02:44 QA server/client 및 자기 coordinator 종료. Vision8102/QA25581 listener 없음. 최종 state는 lease=false, heldKeys=[], pendingSteps=0, nativeInput 전부false, camera=player, vehicle=-1, onGround=true. 소유 caffeinate36845도 종료했다.


## 산출물

`build/libs/destiny-guardians-0.1.0+26.3-w285-super-facing.jar` (215,129,376 bytes).
SHA256 `fb6e9c0a7cd982a55cad3ab623a0b6790ab8e0e26a182b4c4246ef65134dfd14`.
JAR 생성은 성공했지만 전체 Gradle build 명령은 위 GameTest 실패로 exit1이다. 임시 진단 클래스가 JAR에 없고, 검사한 서버 클래스와 JAR 클래스가 일치한다. 기존 작업 디렉터리의 다른 미커밋 변경도 빌드 입력이므로 이 산출물이 W285 변경만 포함한다고 주장하지 않는다.

추가 확인: 전체 실행에서 새로 실패한 W270 menu/loadout/death/disconnect 음성 테스트는 같은 최종 코드로 단독 실행하면1/1 통과했다. 전체 실행 상호작용 원인은 이번 범위에서 해결하지 않았으며 전체 gate 실패는 유지한다.
