# H20 읽기 전용 source oracle

제품/테스트/자산 변경 및 build/runtime 실행 없음. 이 폴더의 JSON/helper/bytecode 증거만 생성했다.

## 산출물과 재현

- `staff-world-y.json`: attack/deploy의 모든 25ms 및 50ms(phase0/phase25) 원시 world-Y 축, 구간별 각도와 최대 구간. 이어서 dense source / installed 25ms resample 각각의 12.5ms 모든 support/wrist 좌표, 오차, 축 및 최대값. 모든 입력/helper SHA256 포함.
- `sample_staff_axes.py`: `rtk proxy python3 -B /private/tmp/destiny-w258/h20-source-oracle/sample_staff_axes.py`로 stdout JSON 재현. 제품 파일은 읽기만 한다.
- FK helper: `/Users/qf/IdeaProjects/DestinyGuardians/scripts/build_hunter_animation_h19.py`의 sample/fk/vector/point 및 build_hunter_animation_h15.py.

축은 pri_right_item local +Y를 전체 부모·bind 회전으로 변환한 authoring world 벡터다(+X right, +Y up, -Z front). clip 시간이며 BM start transition 시간은 포함하지 않는다. native display 좌표로 바로 대입하지 않는다. 고정 직교 basis 변환은 두 축 사이 각도를 보존하지만, native timing/로컬 Euler 보간/레이어 영향은 별도다.

## 원본 각도

50ms phase0 인접 최대:
- attack 0→50ms: 130.795391742°.
- deploy 250→300ms: 168.250137993°.

공격 초기 전환을 제외해도 100→150ms 66.356131014°, 200→250ms 64.289751220°이므로 원본의 한 틱 >=60° sweep 조건은 유지할 근거가 있다. 오래된 50→100ms는 13.655651051°다. clip 전 구간에서 최대 인접 sweep을 측정하면 한 초기 전환에만 기대지 않을 수 있다.

50ms phase25 인접 최대: attack 125→175ms 111.382595769°, deploy 125→175ms 140.708599561°. JSON은 phase0과 phase25를 명시적으로 구분한다.

## 12.5ms support 검사와 해석 제한

(로컬 Euler 채널을 각 모델의 실제 키 사이에서 선형 보간 → 계층 FK → right local(0,6,0)와 left local origin 비교. 블록 단위. deploy는 item hidden인 0~25ms 이전을 최대 visible 집계에서 제외하되 원시 행은 전부 보존.)

| 데이터 | attack 최대 halfkey 오차 | deploy 최대 halfkey 오차 |
|---|---|---|
| dense W199 source | 0.001774916990 @237.5ms | 0.001805444538 @437.5ms |
| installed 25ms resample | 0.499580851798 @12.5ms | 0.477098930304 @212.5ms |

25ms 정렬 키의 약 1e-8 오차만으로 inter-key 접촉을 보장할 수 없다는 명확한 반례다. 재샘플이 원본의 밀집 키 기반 접촉 제약을 중간점에서 보존하지 않는다. 단 이 수치는 native 오차 .0500878의 정확한 재현이 아니며, native BM이 해당 반키 시간을 실제 평가하는지/첫 transition/클라이언트 positional chord+rotation 보간 중 어느 경로인지 아직 구분하지 않는다. **제품 결함 확정으로 쓰지 말 것.** 현재 native cache는 클라이언트 보간된 픽셀이 아니라 서버에서 transform에 전달한 값이다.

## BM frame callback 순서 확인

로컬 3.5.1 sources JAR/Tracker.java는 없어서, 실제 사용 중 bettermodel-api-3.5.1.jar를 javap -p -c -l로 읽었다. `Tracker.javap.txt`, `ScheduledPacketHandler.javap.txt`에 전체 결과 보존.

- Tracker.java 원래 line120: 기본 handler가 lambda$new$5 → animationTick 호출.
- animationTick 원래 lines216–220: scriptProcessor.tick → pipeline.tick(viewBundler).
- frame(handler) 원래 lines289–290: 기존 handler.then(새 handler)로 뒤에 추가.
- ScheduledPacketHandler.then 원래 lines968–971: 기존 handle 먼저, 추가 handle 다음.
- Tracker.tick 원래 lines204–213: 짝수 frame이면 queued tasks 처리 → handler.handle(위 갱신과 추가 callback 포함) → bundlerSet.send.

따라서 H20 tracker.frame callback은 animation/pipeline 갱신 **뒤**, bundle send **앞**이다. 프로젝트 BetterModelClockMixin은 서버틱당 tick을 두 번 실행하며 i==1에만 publishing=true. BetterModelPoseMixin은 sendTransformation을 첫 25ms 단계에서 생략하고 두 번째만 실제 transform 후 EquipmentDisplaySamples.record한다. callback 자체는 두 단계 모두 실행되므로 첫 callback은 이전 published cache를 읽을 수 있고, 두 번째는 이번에 새로 발행한 cache를 읽는다. 이를 25ms 독립 native 표본으로 세면 안 된다. `destiny$serverFrames` 증가도 tick() 반환 뒤이므로 callback 내부의 프레임 카운터는 완료 후 값보다 1 작다.

master의 실제 server tick 진행 후 완료된 tick에서 1회 관측하는 방향이 이 순서에 맞다. 다만 GameTest callback이 END_SERVER_TICK PlayerAnimations.tick보다 먼저 실행되면 관측은 직전 완료틱 값이다. 모델의 실제 frame counter delta와 clip 시작 시점을 함께 기록하여 off-by-one을 분리할 필요가 있다.
