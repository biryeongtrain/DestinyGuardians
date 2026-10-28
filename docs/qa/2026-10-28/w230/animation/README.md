# W230 애니메이션 R1 인계 — 봉인 완료

`classes_w230.animation.json`과 `phase-contract-final.json`을 통합한다. model은 `guardian_classes_w230_r1`. 기존20클립은 deep-equal로 보존했고 신규47클립을 더해 총67클립이다. 모든 신규 클립은61포즈다. 플레이어 full skin rig의 geometry/UV/텍스처/그룹은 그대로이며 손가락을 추가하지 않았다.

## 원본을 실제로 확인한 범위

SSD의11개 실제 armature-only `source.blend`를 **격리 headless Blender5.4.0 Alpha**에서 열었다. 72본·30fps, Fists6개+추가40개=46action 전부를 실제 평가했다. 각 source 파일 SHA는 열기 전후 동일하다. `evidence/inspection.json` 및 직업별JSON에 실제 행렬/프레임/curve hash가 있다. live Blender, main, worktree, SSD에는 쓰지 않았다.

`source-library.animation.json`에는46개 source action을 모두 리타기팅해 보관했다. **자동으로 runtime에 매핑하는 라이브러리가 아니다.** `source-to-java.json`에 live 연결/미연결과 이유가 있다. 상수 포즈·공유 동작·미확인 variant·Additive도 이름만 보고 별도 공격/idle이라고 단정하지 않는다.

| 궁극기 | 원본에서 라이브에 연결한 범위 | 명시적으로 부족하거나 제품용으로 보완한 범위 |
|---|---|---|
| Fists | start80A8AD9A, start_air80A8AD9B, land80A8AD9C, 공유 air80A8A6AA | 독립 약공격 원본 미확인. forward cast두개는 library-only. 기존 authored idle/move 유지 |
| Blade Barrage | 전체 시전80A8AD86 | 모든 투척 변형/종료 상태가 확보된 것은 아님 |
| Spectral | 시전·공중시전, weak1/2/3, 확보된 공중 weak1/3 | idle/move/air는 authored. 공유 Arc Blade/dash/미확인 변형은 library-only |
| Gathering Storm | 창 투척 전체 시전80A8ABF2 | 지속 낙뢰·창 소품은 게임플레이/아트 담당 범위 |
| Storms Edge | cast80A8ACCE, blink_enter80A8ACF0 | 모든 점멸/회전공격이 확보된 것은 아님. 3프레임 blink는0.066667초 |
| Thundercrash | ground/air enter, constant flight loop, exit, exit_wall | loop 원본은 단일 평가 포즈. 이벤트 충돌/피해는 서버 담당 |
| Burning Maul | ground/air cast | carry/gait/air/quick/heavy는 authored. 원본 약/강공격을 확보한 것은 아님 |
| Ward | ground cast, air enter/loop/land | 돔 지속시간 동안 cast반복/플레이어 고정 금지 |
| Well | ground cast, air enter/land | 장판 지속시간 동안 cast반복/플레이어 고정 금지 |
| Chaos Reach | enter, constant beam idle, 짧은 exit | 긴 exit변형은 library-only. 광선/조준 이동은 서버 담당 |
| Nova Warp | ground/air cast Base | Additive charge-idle/exit는 library-only. runtime idle/move/air/release는 authored; 원작 base/mixing 미확정 |

## 시간·접촉 계약

최종 `phase-contract-final.json`과 `timing-manifest.json`이 early contract보다 우선한다. `durationTicks`는 ceil(seconds×20), `durationWithStartBlendTicks`는 시작1틱을 더한 값이다. 별도 종료 보간은 호출자가 소유한다. 원본 시전/공격 시간을 늘이거나 줄이지 않았다. root X/Z·점프 이동을 모델로 실행하지 않으며 서버가 이동을 소유한다. 모델에는 skin-floor Y 보정만 있다.

- Fists 지상:30+1=31틱. 공중진입14+1=15틱, 착지18+1=19틱.
- Thundercrash `_end_wall`은 실제 파일에 있다:14+1=15틱.
- Maul authored quick `_attack`:13+1=14틱. `_attack2`:18+1=19틱. 두 손목을 하나의 손잡이 축에 놓는 IK이며 item local +Y가 shaft축이다. 실제 소품 canonical/파지는 R1에서 맞춘다.
- **모든 `contact`는 null**. productProvisional은 손목 속도 등의 시각 후보 또는 authored 제품 결정이다. 원작 damage event를 해독한 값이 아니다.
- 실제 source Blender 키가1..1인 Thunder loop/Chaos idle/Nova additive idle은 전달 FrameCount7/3/9로 기간0.2/0.066667/0.266667초를 구분했다. 움직이는 원본 루프로 주장하지 않는다.

## 대표 회전 검수와 보정

대표 contact sheet6장을 `renders/`에 작성하고 source skeleton과 원래 Steve skin cubes를 대조했다. **진단용 단색 큐브이며 인게임/소품 렌더가 아니다.** 손에 보이는 노란 표시는 item축이다.

칼날 장전6→7프레임의 왼팔177.3도·스펙트럼18→19프레임의 손목106.5도·Nova4→5프레임의 손목151.5도는 실제 추출 `.blend` 행렬에서도 같은 급회전이다. `evidence/representative-fast-source.json`에 근거를 남겼다. 이를 단순 Euler오류라고 판정하거나, 추출 원본이라는 이유로 원작 게임에서도 그대로 보인다고 단정하지 않는다. 원작 게임의 layer mixing/transition/runtime smoothing은 이 전달본만으로 복원되지 않는다. **R1 native 영상에서 실제 flip이 보이는 구간만 제품 수정**하고 source library는 보존한다.

straight-joint bend plane 축 불안정은 실제 upper/forearm bone행렬의 axial twist로 보정했다. Fists ground의 인접 world회전 최댓값은 초기179.6도에서49.27도로 줄었다. source 방향은 유지했다.

Fists air는 원본 first/last 손목이84.37도 달라 실제 반복 시 pop이 생긴다. 라이브용만 마지막20%(1.2..1.5초)를 실제 첫 포즈로 부드럽게 연결했다. 총1.5초는 그대로며 원본46프레임 동작은 library에 보존했다. 수정 후 loop 끝점차이는 약0.0000012도다. `productAdaptation`에 원본과 변경 범위를 명시했다.

## 검증·후속

오프라인: 신규47클립61포즈/유한 값/시간/고유명/전체 rig그룹 확인, baseline20 deep-equal, geometry/UV/skin/groups 보존, 원본11blend SHA불변. 대표 이미지 검수 후 봉인했다. `validation.json`의 큰 인접 회전은 관찰값이며 전부 fail이라는 뜻이 아니다.

중앙 build/게임/CU/Vision/커밋은 실행하지 않았다. master가 **native R1 → 대표 PNG를 이 worker에 반환 → 필요한 delta → native R2**를 수행한다. 이번 반환은 플레이 가능한 서버 구현 전체 완료나 실게임 통과 주장이 아니다.

재현: scripts/inspect_extract.py를 Blender --background --factory-startup --disable-autoexec로 실행하고, scripts/build.py 및 scripts/validate_render.py를 numpy/Pillow가 있는 Python으로 실행한다. scripts/rig_engine.py는 W229엔진의 이 폴더 전용 사본이다. scripts/refresh_authored.py는 source35개를 그대로 두고 authored12개만 갱신한다. 각 입력 경로와 SHA는 provenance에 있다. 봉인 후 재실행하지 않고 후속 수정은 별도 delta로 반환한다.
