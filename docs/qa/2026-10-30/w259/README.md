# W259 헌터 회피 원본 모션

## 결과

- 도박꾼·명사수 회피를 각각 앞·뒤·좌·우 4방향 원본으로 연결했다.
- 관련 JUnit **14/14**, 헌터 GameTest **55/55**, Danmo/OpenGL 4GB native 입력 **16/16** 완료.
- 생성된 리소스팩은 **63,149,782 bytes**로 W257/W258과 동일하다. 새 텍스처나 신체 메시를 추가하지 않았다.
- 시작 전환에서 몸체가 잠깐 빠지는 캡처는 남아 있다. 원본 회피 동작·복귀와 별도로 아래 한계를 기록한다.

## 1. Blender 원본 확인

전달본은 `/Volumes/qf-ssd/Destiny-Hunter-Dodge-Motions-2026-10-30`이다. 3개 `source.blend`를 별도 headless Blender 5.4 alpha와 `--disable-autoexec`로 직접 열었다. 72본·20액션을 각 61포즈로 평가하고 입력 파일 SHA-256이 바뀌지 않았음을 확인했다. 사용자 Blender 창과 SSD 원본은 수정하지 않았다.

도박꾼 4클립, 명사수 12클립, empower 4클립이다. 원본은 30fps, 프레임 1..30 또는 1..31이며 길이는 29/30초 또는 1초다. 이 값은 전달된 모션 길이이며 원작 무적 시간·이동 거리·쿨다운 근거가 아니다. [평가 근거](source-evaluation.json).

재평가 명령: `Blender --background --factory-startup --disable-autoexec --python scripts/animation/sample_class_ability_w255.py -- --source-root <전달본> --output <외부 평가 JSON>`.

## 2. 워크트리 재사용과 병렬 작업

고정 slot1을 재사용해 348파일을 갱신했다. 이전 W258의 메타데이터 밖 fixture 복사본을 발견해 `/private/tmp/destiny-w259/slot-reconcile`에 먼저 보관했다. 30파일은 main과 같았고 H20만 이전 W258판이어서 검증을 마친 main으로 갱신했다. 이후 정상 refresh를 완료했다. [갱신 기록](worktree-refresh.json).

worker는 새 generator·애니메이션·timing·manifest 4파일을 담당했다. master는 런타임 연결·테스트·Vision을 담당했다. 반환 파일은 [SHA-256](worker-accepted-hashes.json)을 대조한 뒤 통합했다. worker는 종료했고 slot1은 다음 작업에 재사용할 수 있다.

## 3. 변환과 런타임 연결

도박꾼의 기존 `h15_roll_*` 4개를 원본으로 교체하고, 명사수는 `h15_dodge_marksman_*`로 분리했다. 명사수는 연속 태그군 `80A8AA4F/50/48/4A`를 기본 세트로 선택했다. 다른 take의 원작 무기·자세별 선택 조건은 미확정이므로 임의 규칙으로 연결하지 않았다. empower 역시 현재 플레이 가능한 능력이 없어 audit 자료로 보존했다. 자세한 원본 선택 근거는 `art/abilities/w259/dodge-motion-manifest.json`에 있다.

각 클립에 61평가포즈와 원본 길이를 유지한다. 설치 시 기존 `SourceAnimationGrid`의 25ms 격자로 변환하며, 기존 one-shot 진입 보간 1틱은 원본 길이와 별도다. 완전 신전 구간의 팔꿈치·무릎 회전면을 연속화하고 누적 전신 회전을 보존했다. 수평 root 이동은 서버 이동과 중복되지 않도록 생략한다.

시전 순간의 yaw를 시각 모델에 고정해 이동 방향 때문에 몸이 다시 돌아가지 않게 했다. 실제 조준·속도·기존 무적 구간·회피 효과·카메라 정책은 유지했다. 새 설치 이름은 `guardian_hunter_w259_r1`이며 기존 설치 모델은 덮어쓰지 않는다.

## 4. 자동 검사

[JUnit 14/14](unit-result.json): 모션 선택·원본 길이·설치 버전·기존 보간 경로를 확인했다. 기존 전체 JUnit의 별도 자산 불일치 4건은 이번 범위에서 수정하지 않았으며, 이번 결과를 전체 JUnit 통과로 해석하지 않는다.

[헌터 GameTest 55/55](gametest-result.json): 기존 cardinal dodge 검사를 두 종류×네 방향으로 확장했다. 실제 선택된 clip과 조준·속도·6틱 무적·인벤토리 보존·정상 종료를 확인했다. 테스트 삭제나 비활성화는 없다.

## 5. Vision 1차 → worker 검수 → 2차

격리 Danmo/OpenGL·4GB에서 GCB/F5의 `third_front` 시점을 사용했다. 실제 native Shift 두 번과 WASD 입력으로 두 종류×네 방향을 실행했다. 원본·정적 변환·실게임 PNG를 비교해 도박꾼의 몸 말기와 명사수의 낮추기→세우기→복귀를 확인했다.

master가 1차 PNG 4장을 담당 worker에게 전달했고, worker도 직접 비교했다. 역방향 회전·관절 뒤집힘·장비 이탈을 발견하지 않아 불필요한 포즈 수정 없이 같은 4파일을 반환했다. 이후 밝은 낮 환경에서 동일 8시나리오를 다시 실행했다. 총 16시나리오·170 PNG이며 종료 후 lease 해제, 키 없음, pending 0, native 입력 중립, 원래 카메라 복귀를 확인했다. QA client/server는 종료했다.

[시나리오 기록](vision/summary.json) · [도박꾼 4방향](vision/second-gambler-review.jpg) · [명사수 4방향](vision/second-marksman-review.jpg)

## 한계

- 시작 시 일부 sample01에서 몸체가 빠지고 sample02부터 정상 표시되는 현상이 두 번 모두 관측됐다. 공통 모델 소환 전환과 부합하지만 원인은 이미지로 확정하지 않았다. 원본 포즈로 가리지 않고 별도 표시 문제로 남겼다.
- 색상으로 구분된 QA 리그 외형은 이전 W258 아크 캡처에서도 확인된다. 이번 결과는 실제 인증 사용자 스킨 일치 검증이 아니다. 기존 BetterModel 외형 경로를 유지한 모션 검증이다.
- 캡처는 입력 상태로 전후를 기록한 표본이며 60fps 연속 프레임·부드러움 인증이 아니다. Windows 재검증도 하지 않았다.
- 이번 변경은 원본 모션 연결이다. 강제 후방 회피 카메라나 empower 능력을 새로 추가하지 않았다.
