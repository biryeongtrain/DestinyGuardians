주의: parent-fix가 유효한 최종 인계다. 기존 delta-r2의 동결6파일은 바이트 보존하지만 신규4clip 다리 parent 오적용 때문에 통합 권고를 철회한다. 상세 change/cas는 parent-fix-cas.json을 따른다.

W229 R2 아트 인계 — frozen / master 통합·2차 Vision용

최종 모델은 guardian_classes_w229_r2다. frozen-manifest.json에 기재된 full animations JSON, full model, provenance, motion61samples, timing, validation 6파일은 master 통합 승인 이후 바이트 불변이다. /destiny/animation/classes_w229.animation.json에 해당하는 full resource는 destiny/animation/classes_w229.animation.json이고 루트의 동명 파일과 같다. animations-delta.json은 교체/추가7개만 있는 보조 delta다. installed r1을 덮어쓰지 않는다.

20개 clip: R1의13개는 animation JSON·61samples·timing record까지 그대로 유지했다. 잘못된 WarlockSolar cast f28 idle만 교체하고6개를 추가했다. R1 전체 artifact6개의 해시도 불변이다.

| clip | 시간 | 출처와 적용 범위 |
|---|---:|---|
| w229_titan_solar_move | 0.8s | R1 hammer f48 upper/item 그대로 + 명시 MC-authored lowerbody gait |
| w229_titan_void_move | 0.5s | R1 shield cast f43 upper/item 그대로 + 실제 Sentinel sprint80A8A9AD f1..16 legs |
| w229_warlock_solar_idle | 22/30s | 실제 sword_catch_idle80A8B370 f1..23 루프, Daybreak 전용 연결은 미확정 |
| w229_warlock_solar_move | 22/30s | 같은 sword-catch upper/item 원본시간 그대로 + 명시 MC-authored lowerbody gait |
| w229_warlock_solar_air | 2.0s | sword-catch f1 upper sampled hold61회 + 일반 Warlock glide80A8AB5E f1..61 legs |
| w229_titan_arc_idle | 0.8s | 전부 authored temporary fist-ready hold, 원본 action/hash 없음 |
| w229_titan_arc_move | 0.8s | 같은 authored upper + 명시 MC-authored lowerbody gait |

원본 조사: SSD manifest2171clips/54groups의 이름·query/container·event 연결을 전수 조회하고, 미분류 static pose121개와 Daybreak 인접 미분류/generic ready·glide 등 총236action을31개 .blend에서 직접 별도 headless 평가했다. 원본 Daybreak 일반10+event-linked2에는 dedicated idle/move/airloop 이름·연결이 없다. source worker의 별도 조사도 동일하게 exact source를 확정하지 못했다. 이 결과는 게임 전체에서 해당 모션이 없다는 증명이 아니다. 추가 탐색은 사용자 요청대로 종료했고 unresolved state selector는 후속 문서로 남긴다.

80A8B370은 실제 source_query_named sword_catch_idle, Replacement layer의 별도23frame 루프다. 동일72bone skeleton과 기존 retarget mapping, one-handed wrist/item 축, evaluated pose 유한성·원본 방향 대응과 endpoint를 검증했으므로 임시 source-derived sword carry로 채택했다. Daybreak·archangel·thermal_sword 전용 state link나 source prop mesh가 확인됐다는 뜻은 아니다. source의 원래 runtime Base/Replacement mixing도 미해독이다. 따라서 올바른 장착 sword 방향/파지와 제품상 carry 적합성은 master2차 Vision에서 결정한다. rejected cast f28을 최종idle로 재사용하지 않았다.

Hammer catch80A8AD1E도 실제 .blend에서 평가/해시 확인했지만 super link가 없고 이번 요구의 기존 Titan ready upper 유지에 불필요해 채택하지 않았다. Sentinel sprint는 이름상 exact family role다. 다리 world 방향을 고정 ready hip 아래로 다시 표현했으며 원본 전체 sprint를 그대로 쓴 것으로 주장하지 않는다. generic glide 역시 Daybreak 전용 airloop가 아니라 출처를 밝힌 하체 조합이다. Fists of Havoc rip은 미확정이며 source worker 추가 요청으로 작업을 중단하지 않았다.

모든 신규/교체 clip은 최대61pose이고 현재 모두61개다. 원본 기반 루프는 모든 정수30fps frame을 보존하고 직접 평가한 fractional sample을 추가했다. source duration을 늘리거나 줄이지 않았다. authored legs는 hip +/-32도 교대 swing과 trailing knee 최대32도 flex의 in-place gait이며 Source rip 아닌 lowerbody gait다. root X/Z 이동은0, skin-floor Y보정만 있어 gameplay 이동을 만들지 않는다. Item group·PLAYERskin·손가락 없는 limb·기존21Hunter animation/geometry/UV는 보존했다.

추가 검증은 supplemental-validation.json을 참조한다. 동결 이후 별도 headless 재평가3actions/183pose에서 실제 source 행렬64416scalar를 재대조해 오차0, action FCurve hash와 원본 .blend 전후 hash 일치를 확인했다. JSON의 numeric rounding, source leg 방향, 기존13clip timing/sample 불변, 상체/item local 불변도 검사했다. 신규 loop endpoint world rotation 차이는 최대약0.0000025도 수준이며 기존 cast/attack은 loop가 아니므로 endpoint 일치를 요구하지 않는다. 이 결과는 native60fps/접촉/게임 shader·armor 수락이 아니다.

샘플 schema 주의: TitanVoid move와 WarlockSolar air의 sourceFrame/sourceSeconds는 하체 원본 clock이다. sourceMatrices는 각각 고정 upper shield f43 / sword-catch f1 reference이고, 실제 움직이는 하체 source는 lowerBodySourceMatrices다. 그 밖의 upper/lower 출처는 frozen provenance.r2Changes 및 supplemental-validation.mixedSampleInterpretation에 명시했다. 렌더 위쪽은 이 upper source reference, 아래쪽은 실제 조합한 Steve skin FK다. 소스 전체몸과 조합 결과의 일치 주장으로 읽지 않는다. TitanArc 위쪽은 source가 없어 빈 공간이다.

타이밍은 기존 report의8.7도 보간 한계·contact null의 미해독 구분·product provisional 적용값·Hammer audio f15=10clip ticks 설명을 모두 유지한다. Nova 전체 cast는 _attack뿐이므로 activation 첫tick attack을 유지하고 start를 추가하지 않는다.

Java API 권고(소스 수정 없음): 이미 master가 추가한 run==null + logical _idle 요청에서만 actual displacement/grounded로 _move/_air를 선택하는 계약을 사용한다. logical request는 _idle로 보존하여 정지·착지 때 돌아갈 수 있게 하고, 같은 active clip을 매tick 새로 시작하지 않는다. resolver는 w229_를 guardian_classes_w229_r2만 탐색하며 hasClip/resolveExact로 absent와 fallback 선택을 구분한다. 이동속도에 따른 시간배율을 쓴다면 runtime product tuning으로 따로 기록하고 source cast duration에는 적용하지 않는다. start/attack run 우선권, superItem의 pri_right_item/pli_left_item 장착, source root를 gameplay로 쓰지 않는 규칙을 유지한다. 추가 public API 변경은 필수가 아니다.

1차 Vision 결함/근거/잔여검수는 vision1-review.md, PNG hash와 client tick brackets는 vision1-frame-evidence.json, 새7clip FK storyboard는 renders/에 있다. 게임제어·build·project code 변경은 수행하지 않았다. 아트 R2 동결 인계 완료이며 최종 인게임 수락은 master2차 Vision 후다.

Full animation JSON SHA256: c37d9e0ad7d6aac7fef19c3e2723e7c3d8fb9b360362aa0a00d9121279dfc1f8


parent-fix 정정과 동결 이력

최초 R2 동결본의 leg local 변환에서 phip_hip을 parent로 잘못 가정했다. 실제 rig는 prl_right_leg/pll_left_leg가 player_root 직속이다. 추가 원본 방향검증이 최대 벡터차0.425742(약24.58도)를 발견했고 기존 동결6파일을 손대지 않은 채 parent-fix 별도 delta를 만들었다. 통합되기 시작한 최초 R2의 SHA를 CAS baseline으로 명시했다.

수정 범위는 TitanSolar move, TitanVoid move, WarlockSolar move/air 4개 local leg rotation과 이에 따른 visual floor Y뿐이다. 모든 상체·item local과 나머지16clip은 불변이다. 수정본도20clip/61pose이고 모델명은 guardian_classes_w229_r2다. 원본 sample matrices/clock 자체는 최초 동결본과 동일하므로 독립 Blender 재평가64416scalar 오차0 근거가 그대로 적용된다. 수정된 FK와 원본 실제 하체 방향의 최대 벡터차6.47365705e-16, serialized animation69,540scalar 비교의 rounding 최대4.99987607e-10이다. 최초 동결본의 offline_pass는 이 추가 실패로 수락 철회이며 supplemental-validation.json은 수정본에만 적용된다.

현재 native R2는 master가 수정본 CAS 통합 후 검수할 단계다. 이번 worker는 native client/server/CU를 조작하지 않았다. 기존 cast/attack8.7도 근사 한계와 contact product provisional은 변화 없다.
