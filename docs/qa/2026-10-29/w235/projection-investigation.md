# Projection 매크로 / Globals UBO — 읽기 조사 결과

범위: MC 26.3 로컬 release client JAR, 정확한 Iris 1.11.6+mc26.3 및 Sodium 0.9.2+mc26.3 JAR. main/server/QA/profile 변경·기동 없음. post-effect 및 pack 공급경로 비교는 수행하지 않았다. `/tmp`에만 소스 열람용 사본·보고서를 생성했다.

## 결론

**Dynamic FOV include의 기여 여부를 확인하는 master A/B는 유효하다. 다만 현재 MC 26.3 코드에서는 `ProjMat` 멤버 rename 자체나 단순한 `Globals` layout 누락을 원인으로 확정할 수 없다.**

1. native `Projection`은 단일 std140 mat4이다. `ProjMat` → `MinigameLibProjMat` rename은 첫 mat4의 offset 0 / 64-byte payload를 바꾸지 않는다. CPU는 멤버 이름을 찾아 값을 쓰지 않고 `Std140Builder.putMat4f()`로 UBO를 채운다. backend는 descriptor set/binding으로 uniform block 이름을 `_uniform_00_NN`으로 바꾼 뒤 block 단위로 연결한다.
2. **native entity/item/text/block/outline의 기반 snippet에는 이미 `GLOBALS_SNIPPET`이 있다.** `PreparedRenderType.draw()`는 `RenderSystem.bindDefaultUniforms()`를 호출한다. 이 함수는 global settings buffer가 nonnull이면 `setUniform("Globals", globalUniform)`를 수행한다. 따라서 displayhud.glsl의 과거 주석만으로 현재 26.3에서 unbound라고 판단할 수 없다.
3. shader의 활성 descriptor가 native pipeline layout에 정말 없다면 frontend `PipelineBuilder`는 `Unable to find shader defined uniform (Globals)`를 던지고 해당 pipeline 컴파일을 실패시킨다. GL binding 0으로 조용히 방치하는 처리가 아니다. 제공된 사용자 로그에는 이 오류나 `Couldn't compile pipeline`이 발견되지 않았다.
4. 정확한 Iris의 `MixinGlProgram` binding 재작성은 `this instanceof IrisProgram`일 때만 적용된다. `MixinShaderManager_Overrides`도 `IrisRenderingPipeline && shouldOverrideShaders()`로 제한된다. `MixinPipelineBuilder`는 vertex-format extension 억제 플래그만 감싸며 uniform layout 검사를 제거하지 않는다. 확인한 경로에서 shaders disabled 상태의 native `Projection.ProjMat` 멤버 이름을 하드코딩하여 참조하는 처리는 없다.

**아직 미검증:** 문제 프레임의 실제 GL UBO binding 값, globalSettingsUniform의 null/stale 여부, GPU가 받은 GameTime 및 matrix 값, 사용자 client JAR와 로컬 release JAR의 byte 동일성. master가 dynamic-fov=true로 재현하더라도 이는 include 기여 증거이며, unbound 또는 NVIDIA driver bug의 단독 증명은 아니다.

## 정확한 native binding 연결

아래 경로는 이 폴더의 열람용 decompile이며 원본 JAR에 대한 `javap -p -c` 출력도 `bytecode/`에 보관했다. CFR가 재구성하지 못한 일부 switch/메서드는 원본 bytecode를 우선한다.

| 단계 | 코드 근거 |
|---|---|
| native layout 선언 | `minecraft-source/net/minecraft/client/renderer/RenderPipelines.java:47-70,87` — GLOBALS_SNIPPET → MATRICES_FOG → ENTITY/ITEM; TEXT/OUTLINE에도 Globals 포함. BLOCK은 GENERIC_BLOCKS의 Globals를 상속 |
| block 이름 | `minecraft-source/net/minecraft/client/renderer/BindGroupLayouts.java:50-56` — `Projection`, `Globals`는 UBO description. mat4 멤버 이름은 명시하지 않음 |
| projection upload | `minecraft-source/net/minecraft/client/renderer/ProjectionMatrixBuffer.java:60-65` — 단일 mat4를 std140로 기록 |
| shader reflection 검사 | `minecraft-source/com/mojang/renderpearl/frontend/shaders/PipelineBuilder.java:214-245` — block descriptor 이름을 layout에서 조회, 없으면 컴파일 예외, 있으면 새 binding 할당 |
| GL block 이름 정규화 | `mc-source/com/mojang/renderpearl/backend/opengl/GlPipelineRecompiler.java:179-218` — descriptor set/binding을 이용하여 block 이름 정규화 |
| GL program binding | `mc-source/com/mojang/renderpearl/backend/opengl/GlProgram.java:88-142` — 정규화한 block을 glGetUniformBlockIndex / glUniformBlockBinding으로 연결 |
| 실제 draw 기본값 | `minecraft-source/net/minecraft/client/renderer/rendertype/PreparedRenderType.java:47-58` → `minecraft-source/com/mojang/blaze3d/systems/RenderSystem.java:379-395` — Projection/Fog/Globals/Lighting 설정 |
| 이름 → frontend index | `minecraft-source/com/mojang/renderpearl/frontend/FrontendRenderPass.java:177-190` — compiled pipeline의 uniformIndices 맵으로 변환 |
| GL buffer range | `mc-source/com/mojang/renderpearl/backend/opengl/GlCommandEncoder.java:468-496` — program의 Uniform.Ubo.blockBinding을 사용해 glBindBufferRange. switch decompile의 지역 변수 재구성은 부정확하므로 대응 bytecode 참조 |
| Iris guard | `iris-source/net/irisshaders/iris/mixin/MixinGlProgram.java:53-58,117-127`; `MixinShaderManager_Overrides.java:84-110`; `MixinPipelineBuilder.java:32-42` |

## Dynamic FOV include가 실제로 추가하는 것

열람한 optional/projection.glsl은 Globals include와 GameTime 읽기를 추가한다. `GameTime >= 0` 또는 orthographic이면 raw projection을 반환하고, 음수 시각에서 1..179 FOV를 해석하여 matrix [0][0], [1][1]만 바꾼다. `#define ProjMat minigamelib_projection()`로 각 사용처가 함수 평가로 대체된다. 이름 변경과 달리 **활성 Globals descriptor 및 runtime projection 연산이 추가되는 변화**다.

native Globals 정의에서 GameTime은 std140 offset 28이다: ivec3 CameraBlockPos(0), GlintAlpha(12), vec3 CameraOffset(16), GameTime(28), vec2 ScreenSize(32), MenuBlurRadius(40), UseRgss(44). 첫 64바이트 projection UBO를 Globals로 잘못 읽는다면 GameTime이 행렬 일부로 해석될 수는 있으나, 위 정상 binding 코드가 그런 오연결을 한다는 증거는 없다.

`Projection` block 이름과 payload가 유지되고 단일 멤버 이름만 바뀐 것은 native 연결을 끊는 조건이 아니다. Globals가 추가되어 descriptor 순번이 달라져도 native frontend map → renamed block → Ubo.blockBinding 연결은 함께 갱신된다. 순번 변화만으로 alias가 생긴다고 단정할 수 없다.

## Sodium / NVIDIA 조사에서 남길 관련 근거

- ITEM fast encoder와 ModelPart 팔은 `EntityVertex` 36-byte 형식으로 합류한다. Position float3@0, Color@12, UV0 float2@16, Overlay@24, Light@28, Normal signed normalized byte4@32. native ENTITY와 맞으며, 20-byte CompactChunkVertex는 terrain 전용이다.
- Sodium terrain은 자체 `u_Globals { mat4 u_ProjectionMatrix; ... }`와 `u_ProjectionMatrix`를 사용한다. 따라서 native minecraft projection include가 entity/item에 영향을 주면서 Sodium 지형은 정상인 관찰과 **양립한다**. 원인 확정은 아니다.
- 사용자 NVIDIA 로그는 ARB_vertex_attrib_binding / ARB_direct_state_access 사용을 기록한다. Mac과 달라질 수 있는 backend 경로이나, 이 분기가 `ProjMat` 또는 `MinigameLibProjMat` 문자열을 참조하지 않는다.
- MC `GlDevice`는 NVIDIA에서 BufferStorage를 강제로 Mutable로 선택한다. user enabled extensions에 ARB_buffer_storage도 없다. 현재 증거로 persistent-mapping 원인을 주장하지 않는다.
- NVIDIA threaded optimization workaround는 사용자 로그 577-582행에서 context에 적용된 것이 확인된다. workaround 누락으로 간주하지 않는다.

## master에게 반환할 최소 판정 기준

- 현재 진행 중인 **같은 pack/같은 scene에서 dynamic-fov include 유무만 바꾸는 A/B**가 우선이다. sidecar는 기동·파일 수정하지 않았다.
- true에서만 깨진다면 optional projection include를 우선 대상으로 좁힐 수 있다. 이후 설명은 `Globals 활성화/값`, projection 함수 연산, shader compiler 결과 중 실제 증거에 따라 선택한다.
- layout 누락 주장을 하려면 위 compile-error 문자열 또는 실제로 native와 다른 pipeline layout/bind 경로를 제시해야 한다. GPU UBO null/stale/alias 주장은 문제 draw의 binding/버퍼 값 확인이 필요하다.
- 단일 mat4 rename만으로는 native block binding 실패를 설명할 수 없다는 점은 코드로 확인됐다.

추가 자료: `projection-globals-evidence.md`(발췌), `projection-globals-provenance.json`(입력 해시), `source-provenance.json`(정확 Sodium tag/commit), `bytecode/`(exact JAR 명령어 출력).
