# 공통 증원 시스템

2026-11-04. 악마의 소굴에서 사용하는 대기열·시도 예산·선택 지점 경고를
`kim.biryeong.destiny.activity.reinforcement`로 분리했다.
공격전·던전·레이드 세션마다 별도 인스턴스를 소유한다. 전역 singleton은 사용하지 않는다.

## 연결 계약

- `ReinforcementQueue<P>`: `enqueue(id, payload, gap, notBefore)`로 중복 없는 FIFO를 만든다.
  `reserve(activeTick, admission)`은 시간과 수용 조건이 충족된 첫 팩만 반환한다.
  `admission`은 살아 있는 적뿐 아니라 예약·유실 복구 중인 적과 보스용 여유 슬롯까지 센다.
- 실제 월드 삽입에 성공한 첫 멤버에서만 `arrived(packId, activeTick, warningTicks)`를 호출한다.
  `gap`은 동일한 경고 길이의 연속 팩 도착 간격이다. 실제 도착에서 경고 길이를 뺀 시각으로
  기준을 늦춰 막힌 입구에서 오래 대기한 팩 뒤에 다음 팩이 한꺼번에 쏟아지는 것을 막는다.
  다른 경고 길이를 쓰는 활동은 해당 팩의 경고 길이를 전달하고 다음 예약/도착 간격 정책을 정한다.
- `SpawnAttemptBudget<K>`: 안정적인 슬롯 ID와 eligible 조건, 실제 시도 callback을 넘긴다.
  한 틱의 시도 수를 제한하며 다음 틱은 마지막 시도 다음 슬롯부터 돈다.
  generation 변경이나 종료가 발생하면 callback에서 false를 반환해 스냅샷을 즉시 중단한다.
- `SpawnWarnings<K,P,B>`: 실제 선택한 지점과 충돌 예약을 경고가 끝날 때까지 보존한다.
  지점을 바꾸면 `begin`으로 전체 경고를 다시 시작한다. 준비 시점이 되어도 투입 직전에
  실제 지형·플레이어 거리·경로·다른 예약을 다시 검사해야 한다.

`P`는 활동별 팩 또는 지점 자료형이다. 공통 코드에는 DevilsPlan, 적 종족, 좌표,
Minecraft 서버, 수송선 모델 의존성이 없다. 가변 payload는 호출자가 변경하지 않는다.

## 세대·취소·일시정지

서버 스레드에서만 호출한다. 활동의 activeTick을 사용하고 전체 팀 일시정지 동안 시계를
진행시키지 않는다. 한 명의 접속 종료로 다른 참가자의 증원을 취소하지 않는다.

전멸/구간 전환/종료는 먼저 활동 generation을 무효화하고, 대기열 `reset`, 예산 `reset`,
경고 `clear` 및 활동 소유 엔티티/연출 제거를 수행한다. 늦은 spawn/처치/연출 callback은
활동 어댑터가 generation을 검증한다. 공통 큐의 `reset`만으로 외부 callback을 취소할 수는 없다.
선택 취소는 `cancelQueued(predicate)`, 전체 대기 취소는 `cancelQueued()`를 쓴다.
취소한 팩 ID는 같은 세대에서 재등록되지 않는다. 취소·유실을 처치로 보고하지 않는다.

## 악마의 소굴 어댑터

`DevilsDirector`는 위 큐와 예산을 실제 사용한다. 최대 팩/몹 수, 3인 고정 난이도,
보스 체력 단계, 필수 처치와 체크포인트는 기존 활동에 남겼다.
`DevilsSpawnTelegraphs`는 `SpawnWarnings`에 DevilsSpatial.Point/AABB를 연결한다.
기존 `incoming`, `spawnTelegraph`, `spawned` 이벤트는 연출용이다. 연출 실패는 적 투입을
취소하거나 새 적을 추가할 근거가 아니다.

수송선의 도착·퇴장 렌더러와 비행 경로는 이번 공통화에 포함하지 않았다.
공통 모듈에 수송선 의존성을 넣지 않으므로 포탈·문·강하 연출에도 같은 전투 경로를 쓸 수 있다.

## 대형 연출 모델의 팩 텍스처 배치

공통 `compat.pack.PackAtlasRouting`은 `destiny/pack/atlas_routes.json`의 PNG SHA-256과
생성 namespace/prefix로 텍스처를 찾는다. 생성된 sprite 이름을 고정하지 않는다.
원본 픽셀·UV·모델을 변경하지 않고 원래 atlas 끝에 정확한 sprite filter,
대상 atlas 끝에 single source를 추가하며 기존 source는 보존한다.
현재 dl_skiff의 4096 hull / 1024 emission PNG를 items에서 blocks로 옮긴다.
이 선택은 Minecraft 26.3의 모델 material lookup에 맞춘 것이며 임의의 target atlas가
모든 렌더러에서 작동한다고 보장하지 않는다. 새 모델은 실제 생성 팩/클라이언트 로드를 검증한다.
