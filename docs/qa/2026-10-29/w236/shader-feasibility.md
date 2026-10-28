# 코어 셰이더 기반 손 경량화 조사

사용자 제공 CORE-SHADER-HUD-GUIDE (1).md를 참고했다. 셰이더로 손을 작게 그리는 것만으로는 로드 시 이미 만들어진 모델·tint 객체가 줄지 않는다. 손 형상과 스킨 전달 방식을 함께 변경해야 메모리가 줄어든다.

정확한26.3 `PlayerHeadSpecialRenderer`는 `minecraft:player_head`와 아이템 PROFILE 컴포넌트로 플레이어 전체 스킨 텍스처를 얻는다. 이 텍스처의 팔 영역으로 UV를 재배치하고 머리 형상을 팔로 바꾸는 코어 셰이더는 가능한 후속 후보이다. 다만 모델 자체는 고정 head/hat이므로 좌우·상완/전완·slim·소매·프로필 기본스킨 fallback·표식 구분을 구현해야 한다. OpenGL/Vulkan 양쪽의 실화면 검증은 아직 수행하지 않았다.

현재 채택 검토는 바닐라26.3 item-local transformation으로 반복 pose 형상을 공유하는 방법이다. 새 렌더 파이프라인보다 적용 범위가 작고 기존스킨·61pose를 유지한다. Shader만 추가해서 tint 데이터가 사라졌다고 주장하지 않는다. ItemDisplay 변환은 보간을 지원하지만, 바닐라가 손 렌더 직전 depth를 지우므로 기존1인칭 모델을 단순 교체할 수 없다.

아래는 작업자의 정확 버전 바이트코드 조사 원문이다. 원문 scratch 경로는 개발 당시 근거이며 배포 의존성이 아니다.

---

# W236 skin-arm shader feasibility — read-only conclusion

2026-10-29. Product Java/shader/client/assets and tests were not changed during this review.
The existing seven-test delta is `/tmp/w236-optimizer-active-route-test-delta.tar.gz`.
Compilation/JUnit were not run by this worker.

## Priority

Main's later third-pack measurements supersede the initial histogram: retained
2.73 GiB, 17.4M BakedQuads (~1.53 GB), and 20.4M CustomModelDataSource objects
(~490 MB). These are master-provided measurements, not worker measurements.
The eight-base strategy doubled hand-context tint graphs. Main is replacing it
with pose anchors grouped by C=D_left*inverse(D_right), verifying both contexts
before reusing an anchor, using inverse(anchor_R)*pose_R as the leaf-local matrix,
a combined firstperson [right,left] case, and the original non-firstperson fallback.
This is the current implementation direction; worker did not independently test
the matrix identity, grouping coverage, resulting counts or client heap/load time.
New helpers and matrix tests remain main-owned. Further tint-graph investigation
was stopped at main's explicit request.

## Native 26.3 findings

Evidence comes from the official client JAR
`/Users/qf/.gradle/caches/fabric-loom/26.3/minecraft-client.jar`, version 26.3,
protocol 777, resource format 97.1. `javap -c -p` evidence is saved separately;
no game was launched. The initial Loom merged-JAR inspection was replaced with
the official native JAR inspection; they are not byte-identical class files.

- The actual renderer is `PlayerHeadSpecialRenderer`, registered as
  `minecraft:player_head`. The native player_head item uses outer
  `minecraft:special`, base `minecraft:item/template_skull`, and inner
  `{ "type": "minecraft:player_head" }`.
- `PlayerHeadSpecialRenderer.extractArgument` reads `DataComponents.PROFILE` and
  `PlayerSkinRenderCache.getOrDefault`. The cache uses the full skin body texture,
  via `SkullBlockRenderer.getPlayerSkinRenderType` -> `RenderTypes.entityTranslucent`.
  Thus a profile-backed special renderer supplies the dynamically bound skin that
  ordinary white-texture/tinted cuboid models do not supply by themselves.
- `PlayerHeadSpecialRenderer.Unbaked.MAP_CODEC` is `MapCodec.unit`: no configurable
  arm geometry/UV field. It bakes `ModelLayers.PLAYER_HEAD` into `SkullModel`.
  `SkullModel.createHumanoidHeadLayer` is an 8x8x8 head plus inflated hat, on a 64x64
  skin atlas. `SpecialModelWrapper.Unbaked` accepts base/transformation/model;
  base supplies render properties, not replacement arm elements.
- Native `entity.vsh` forwards UV0 and `entity.fsh` samples Sampler0. Arm UV remap
  and geometry reshaping are therefore technically plausible in a core shader,
  but require an unambiguous marker and per-side/segment/slim/sleeve handling.
  This special renderer does not consume the current geometry CMD tint array.
  `PROFILE` is explicit per item; it does not implicitly mean the current viewer.
  Cache lookup can temporarily return a default skin. Sleeve visibility is not
  automatically inherited from the viewer's player-model part flags.

## Alternatives and limits

`WeaponSkinArms` currently sends 96 (slim) or 112 (classic) RGB values for each of
four genuine arm segments, using flag8/flag9 and color offsets 64/192/320/448.
`skin_arm_models_w204.py:142-184` makes shared pixel-plane parents but repeats tint
sources and pose references in item definitions. Native pose-anchor transform sharing targets
the baked-quad duplication while retaining one tint graph for both hand contexts
and the existing skin transport architecture; actual savings await main measurement.

Player-head + shader could subsequently remove the per-pixel tint arrays and
pixel-plane geometry. It would still retain pose matrices unless motion is moved
to GPU data/clock playback or entity transforms. Changing a shader alone while
retaining the existing emitted models will not remove their load-time BakedQuads.
No reduction percentage or 4 GB client result was measured for this alternative.

ItemDisplay has real interpolated transforms and can render a profile-backed
player-head item, but does not automatically render skinned player arms. It still
needs an arm geometry/texture solution, owner-specific packets, and camera alignment.
Native GameRenderer clears depth immediately before renderItemInHand; a world
ItemDisplay is not a drop-in replacement for that hand pass. This is a larger
rendering/animation redesign than native item-local matrix sharing.

Recommendation: proceed with main's verified-both-contexts pose-anchor optimization first.
Keep player-head shader remapping as a later prototype for tint/geometry reduction;
its visual correctness and OpenGL/Vulkan pipeline compatibility remain unverified.
The seven synthetic tests previously supplied use an opaque `minecraft:head` +
`kind:player` renderer object in two fixtures; this is only opaque reference data,
not a native 26.3 codec-valid renderer example. Product prototypes must use
`minecraft:player_head` as above.

## Evidence

- `/tmp/w236-native-head-javap.txt`: PROFILE extraction 54; fixed native head bake 107;
  unit codec 150; base properties 322; wrapper codec fields 383.
- `/tmp/w236-native-profile-javap.txt`: createResolved(GameProfile) 24;
  nonblocking/default cache path 269; full skin texture path 335; patch fields 472.
- `/tmp/w236-native-display-javap.txt`: head/hat geometry 17/45;
  ItemDisplay resolver 130; interpolation progress 1586;
  skin render type 2191; clear-depth then hand rendering 4167;
  player_head registration 4956.
- `/tmp/w236-native-entity.vsh`, `/tmp/w236-native-entity.fsh`: actual shader interface.
- `/tmp/w236-shader-native-provenance.json`: native JAR/version/SHA-256 record.
- Main source: `src/main/java/kim/biryeong/destiny/weapon/WeaponSkinArms.java`;
  generator: `scripts/skin_arm_models_w204.py` (both read-only).
- User guide: `/Users/qf/Downloads/CORE-SHADER-HUD-GUIDE (1).md` (read-only).

## Final handoff

Latest test delta: `/tmp/w236-optimizer-active-route-test-delta.tar.gz`.
Incremental active-route fix: `/tmp/w236-optimizer-active-route-fix.patch`.
Seven tests retained. Source item asset is required for every active root; mapped
roots alone require a hands wrapper, and unmapped roots must return the original.
Static checks passed. Java compilation and JUnit execution remain main-owned and
were not run by this worker. No further test or product changes were made.
