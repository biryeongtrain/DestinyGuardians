# W245 shader basecolor worker — 2026-10-29

지원 수식은 15 family / 24 pixel shader / 98 material이다. 최종 geometry coverage의 노출 124,098셀 중 107,420셀(86.56%)이 지원 재질이며, 노출 상위 30재질은 모두 포함한다. 이는 **수식 지원률**이다. 원본 색·엔진 렌더·UV 정합성의 완전 복원률이 아니다. framebuffer 배경과 합성해야 하는 projected_decal도 별도 제한을 두고 포함한 수치다. master는 블록 적용에서 이 family를 제외했다고 보고했다.

사용 원본은 `/Volumes/qf-ssd/Destiny-Tower-Materials-2026-10-29`의 README, Materials JSON, HLSL, DDS다. `PROVENANCE.json`: Charm v3.5.0 / source 058e2ec / game build 25932352. HLSL은 3Dmigoto 디컴파일 표현이다. 원본 데이터와 기존 textured GLB는 수정하지 않았다.

**UV 최종 정정:** upstream 058e2ec 확인으로 전달 VertexTexcoords0는 이미 scale/translation을 적용하고 V를 뒤집은 cooked export임을 확인했다. 앞서 전달 UV를 raw GPU UV로 취급하고 CHUNK UV 상수 누락 때문에 identity 근사라고 했던 판단을 철회한다. basecolor 수식은 동결했고 STATIC 전용 `uv_from_charm_export()` helper만 추가했다. STATIC export UV가 downstream에서 그대로 보존됐다면 sample 전 `(u,1-v)`로 바꾸며 scale/offset을 재적용하지 않는다. TerrainPart 경로는 미검증으로 분리한다.

## 반환 파일과 실행

- `scripts/tower/material_shader_w245.py`: NumPy/Pillow 모듈, 외부 게임/Blender 의존 없음.
- `docs/qa/2026-10-29/w245/shader-recipes.json`: 재질별 shader, 실제 pixel cbuffer snapshot, texture/channel, 수식, 누락 입력, 원본 SHA256, VS 근거.
- 이 문서. 위 3파일만 이 slot에 작성했다. Git add/commit/reset/clean, 게임/포트/Blender live 조작, Java 빌드는 수행하지 않았다.

```python
from material_shader_w245 import MaterialBaker
baker = MaterialBaker(material_root)  # 기본: 누락 pixel 입력은 invalid
ps_uv, uv_valid = baker.uv_from_charm_export(
    exported_uv, terrain=terrain_flags,
)  # STATIC V flip만 복원; terrain은 unchanged UV + invalid
rgb, valid = baker.sample(tag, ps_uv, inputs={
    "world_xyz": destiny_world_xyz,  # Nx3, 원본 단위/좌표계
    "normal": destiny_world_normal,  # Nx3, 원본 Z-up, 단위 normal
})
valid = valid.ravel() & uv_valid.ravel()
rgba = baker.bake(tag, size=256, uv_bounds=(umin, vmin, umax, vmax))
```

`sample` 출력은 sRGB float32 Nx3와 bool Nx1이다. `bake`는 uint8 H×W×4이며 alpha는 유효성 마스크다. shader G-buffer o0.w나 게임 투명도로 해석하지 않는다. unknown/unsupported는 zero RGB + invalid이고 slot0 fallback을 하지 않는다. DDS/입력 에러는 invalid와 `baker.last_errors[tag]`로 확인한다. `recipes`는 tag key dictionary이다.

의도적으로 대표값을 수락하려면 `MaterialBaker(root, allow_representative=True)`를 사용한다. 이 경우 누락 world.xy→PS UV, world.xyz→(u,v,0), normal→(0,0,1), TEXCOORD8→(1,1,1,1), dynamic cb→추출 static snapshot을 사용하며 valid는 그 명시된 근사를 사용할 수 있다는 뜻이다. 원본 exact라는 뜻이 아니다. 기본 모드에서도 RGB 추정치는 반환하지만 누락 입력이 있으면 valid=False다. 입력 배열이 있는 `world_xyz`로부터 world.xy를 자동 추출한다. `inputs["cb_overrides"]={register_index: float4}`로 알려진 동적 cb 값을 제공할 수 있다.

API key `instance8`은 **보간된 per-vertex TEXCOORD8 float4**의 기존 호출 이름이다. 확인된 per-instance tint가 아니다. 주요 VS는 `t0.Load(min(asuint(cb1[1].w), vertexID))`를 TEXCOORD8으로 출력한다. 이 Buffer와 vertexID clamp 상수는 자료에서 확보되지 않았다. `instance8=[0,0,0,0]`와 1 변형은 양 끝 대표 비교이며 원본 값으로 단정하지 않는다.

## upstream 확인: cooked export → PS TEXCOORD3

TowerWork.cs:182-194는 `LoadIntoExporterScene`에서 로드된 `ExporterMesh.Parts.MeshPart.VertexTexcoords0`를 그대로 JSON에 기록한다. GPU raw buffer를 직접 직렬화한 것이 아니다.

058e2ec 소스 경로는 다음과 같다.

1. [StaticMesh.cs:28-33](https://github.com/MontagueM/Charm/blob/058e2ec/Tiger/Schema/Static/StaticMesh.cs#L28): Load → StaticData.Load.
2. [StaticMeshData.cs:121-126,170-190](https://github.com/MontagueM/Charm/blob/058e2ec/Tiger/Schema/Static/StaticMeshData.cs#L170): BeyondLight GenerateParts → StaticPart.GetAllData.
3. [StaticPart.cs:58-80](https://github.com/MontagueM/Charm/blob/058e2ec/Tiger/Schema/Static/StaticPart.cs#L58): vertex buffer를 읽은 다음 TransformData 호출.
4. [Vector.cs:103-115](https://github.com/MontagueM/Charm/blob/058e2ec/Tiger/Schema/Vector.cs#L103): int UV는 32767로 나누어 float 정규화한다. float 입력은 그대로 저장한다.
5. [StaticPart.cs:108-118,140-147](https://github.com/MontagueM/Charm/blob/058e2ec/Tiger/Schema/Static/StaticPart.cs#L108): TexcoordScale/Translation을 적용하고 V를 뒤집는다.
6. [Exporter.cs:206-214,460-485](https://github.com/MontagueM/Charm/blob/058e2ec/Tiger/Exporters/Exporter.cs#L460): AddPart/ExporterPart는 해당 MeshPart를 유지하며 여기서 UV를 또 변환하지 않는다.

확인된 export 식은 `u_export = u_normalized*scale+offset_u`, `v_export = 1-(v_normalized*scale+offset_v)`다. 주요 VS의 PS 입력은 `normalizedUV*cb1[1].x+cb1[1].yz`이므로 이미 cook된 VertexTexcoords0에 CHUNK affine을 다시 적용하면 이중 변환이다. 정적 export에서 이미 cook된 transform을 CHUNK 미확보로 간주한 이전 설명은 잘못됐다.

STATIC geometry/GLB UV가 이 exported UV를 그대로 유지했다면 `ps_uv,uv_valid = baker.uv_from_charm_export(exportUV, terrain=terrain_flags)` 후 `sample(tag,ps_uv,...)`를 사용한다. 모듈 수준 `uv_from_charm_export()`도 같다. 출력은 float32 Nx2와 bool Nx1이며 terrain=True 또는 N개 mask의 terrain 항목은 UV를 그대로 유지하고 invalid다. 유효성은 sample valid와 합쳐야 한다. downstream이 V를 이미 되돌렸거나 별도 UV 변환을 했다면 그 경로를 먼저 대조하여 중복 flip하지 않는다. 모듈은 DDS v0=row0 규약과 PS UV 입력 계약을 유지하고 자동 flip을 하지 않는다.

[Terrain.cs:66-73,194-201](https://github.com/MontagueM/Charm/blob/058e2ec/Tiger/Schema/Other/Terrain.cs#L194)에서 group scale/offset과 V flip 메서드를 읽었으나 **TerrainPart의 실제 export pipeline 및 shader UV 대응은 미검증**이다. STATIC 계약을 terrain에 자동 적용하지 않는다. main의 terrain flag를 받아 helper가 terrain 항목을 invalid로 반환한다. 주요 30재질의 VS 6종은 아래 공통 affine을 사용하되 material tag만으로 STATIC/terrain 경로를 판별하지 않는다.

| VS | 근거 줄 | 변환 |
| --- | --- | --- |
| 80B4FB63 | 92 | rawUV × cb1[1].x + cb1[1].yz |
| 8113C0E0 | 80 | rawUV × cb1[1].x + cb1[1].yz |
| 8113C0F7 | 69 | rawUV × cb1[1].x + cb1[1].yz |
| 8113C0FC | 83 | rawUV × cb1[1].x + cb1[1].yz |
| 8113D445 | 92, 93 | rawUV × cb1[1].x + cb1[1].yz |
| 8113D459 | 92 | rawUV × cb1[1].x + cb1[1].yz |

`uv_from_raw` / `raw_uv_to_texcoord3` helper는 genuine uncooked, normalized GPU TEXCOORD0에만 해당한다. 현재 cooked VertexTexcoords0에는 사용하지 않는다. 실제 raw GPU 입력을 새로 확보해 처리할 때만 cb1[1]이 필요하며 그때 상수가 없으면 identity는 대표 근사다. Materials Vertex.CBuffers(cb0)와 CHUNK_MODEL cb1이 다르다는 설명 자체는 유지한다. exported cooked UV에는 해당 CHUNK scale/offset이 이미 반영됐다는 점이 이번 정정이다.

world 입력은 PS TEXCOORD4의 Destiny 원본 단위 및 축이어야 한다. Minecraft voxel xyz나 GLB Y-up 좌표는 원본 world texture 좌표가 아니다. 이 UV 정정으로 TEXCOORD8 Buffer 누락이나 Frame/TIME 입력 부재까지 해결되지는 않는다. 일부 deform VS의 TEXCOORD4에는 3D noise 변형이 있어 static 위치는 해당 효과의 대표 정지 근사다.

## 주요 수식과 지원 범위

| Family | 재질 수 | 노출 셀 |
| --- | ---: | ---: |
| mask_dye | 57 | 35401 |
| layer_detail | 16 | 43248 |
| graded_albedo | 3 | 1576 |
| affine_dye | 1 | 4612 |
| world_dye | 1 | 3680 |
| complex_dye_layers | 2 | 1460 |
| direct_albedo | 2 | 990 |
| world_detail | 1 | 0 |
| instance_layers | 1 | 964 |
| palette_masks | 6 | 8730 |
| uv_tint | 1 | 1557 |
| affine_additive | 2 | 992 |
| world_tint | 1 | 991 |
| normal_layers | 1 | 1215 |
| projected_decal | 3 | 2004 |

`8113C982`는 slot0을 단순 albedo로 쓰지 않는다. q=T1(uv*cb0[0].xy+cb0[0].zw), A=cb1+cb2*q.a, B=cb3+cb4*q.a, C=cb5+cb6*q.g. uv.x>0으로 A/B, uv.y>1과 T0.r로 C 혼합률을 정한 뒤 sat(cb8.x+cb8.y*T0.g)로 cb7과 섞는다. HLSL의 wxyz swizzle 뒤 o0.yzw는 이 RGB와 같다. T1이 sRGB로 선언됐으므로 green은 linear로 decode하지만 alpha는 decode하지 않는다. 비슷한 80B4F9B4/C946/C916과 C8A4/C9E4의 다른 index·channel 경로는 별도로 분기한다.

`layer_detail`은 단순 tint 배수가 아니다. T0/T2/T4로 dye mask와 ramp를 만들고, T1/T3로 detail ramp와 혼합률을 구하며 최종 noise RGB를 곱한다. C94B/DD37의 UV.y>1 분기와 DD37의 세 번째 dye ramp를 별도로 구현했다. 각 재질 JSON의 실제 cb snapshot을 사용한다.

`80B4F8A3`는 같은 T1에서도 red는 s2 Clamp, green은 s1 Wrap을 사용한다. 이 차이를 구현했다. graded family는 gain/contrast의 xy 순서가 일반 remap과 다르므로 HLSL 그대로 구현했다. normal/roughness texture는 basecolor 의존성이 없으면 읽지 않는다. projected_decal은 독립 색 기여만 계산하고 framebuffer depth/normal rejection과 배경 합성은 구현하지 않는다. 그 RGB/alpha를 표면 albedo/opacity로 단정하지 않는다.

지원하지 않은 655재질은 recipes에 unsupported로 명시한다. AABB 상위에만 있는 8113CFC7/CFE0 sky/effect 경로 등은 FRAME/VIEW/LUT/화면 buffer와 조명·대기 합성이 섞여 있어 basecolor로 임의 치환하지 않았다. 8113C163은 world 좌표와 Frame/TIME TFX의 cb2/3/4가 누락됐으므로 static cbuffer 동결 근사다. 모든 recipe의 `exact_original_color`는 False다.

## 색공간과 샘플링

- DX10 DDS sRGB enum 72/99/29 등은 메모리에서 같은 블록 압축의 UNORM enum 71/98/28 등으로만 바꿔 Pillow 디코더를 사용한다. DDS 파일과 압축 block byte는 수정하지 않는다.
- sRGB RGB는 IEC sRGB EOTF로 **linear 변환 후** bilinear filtering한다. alpha/Non-Color는 수치 그대로 사용한다. cb tint/ramp도 linear로 계산한다. 마지막에 sRGB OETF와 0..1 clipping을 적용한다.
- source row0=v0으로 읽고 숨은 V flip을 추가하지 않는다. Wrap/Clamp/Mirror 및 point/linear를 구분한다. shader derivatives, 실제 mip LOD/bias, anisotropic filtering과 엔진 조명·노출·톤매핑은 재현하지 않는다.
- cache 기본 예산은 256 MiB이며 단일 texture가 더 크면 그 한 장은 유지할 수 있다. texture 색공간까지 cache key에 포함한다.

## UV 범위 bake와 GLB 연결

아래 source UV 범위는 **PS UV로 변환한 범위**다. cooked export UV를 유지하는 GLB에서는 PS UV의 V 반전까지 atlas mapping/KHR transform에 합성해야 한다. 기존 baked GLB를 고친 것으로 보지 않는다.

UV.x의 0 및 UV.y의 1 비교는 texture wrap 이전의 좌표로 dye를 선택한다. 따라서 `bake(tag)`의 unit square를 그대로 repeat하면 원래 분기가 지워진다. 실제 source UV 범위별 `bake(...,uv_bounds=...)` 또는 triangle/mesh atlas가 필요하다. source UV를 유지하고 KHR_texture_transform으로 정규화한다면 scale=(1/span_u,1/span_v), offset=(-min_u/span_u,-min_v/span_v)이며 원본 변환/flip이 이미 있으면 합성해야 한다. cooked export 범위 자체를 PS 범위라고 간주하면 안 된다. atlas 바깥은 Clamp/gutter를 써야 한다. world/normal/vertex 채널이 공간에 따라 달라지는 family는 2D bounding-box만으로 완전 bake되지 않으며 각 bake texel의 입력도 공급해야 한다. range swatch는 사용된 입력 상태의 대표 preview다.

## 독립 검증과 바닥 어두움

별도 임시 HLSL register 해석기는 production family 식을 재사용하지 않고 디컴파일 statement의 swizzle, 비교, ternary 및 조건부 branch를 실행했다. sampler/색공간 로더는 공유하므로 이것은 GPU/DXBC 렌더 비교가 아니다.

- 24 shader별 무작위 257 UV(-2..3), world position, unit normal, TEXCOORD8 입력으로 수식 대조: 최대 linear 오차 2.98e-8.
- 지원 98재질 모두 실제 DDS/CB를 사용한 샘플링 통과, errors 없음. NaN/inf/unknown/빈 UV, strict missing-input 거부, world_xyz 자동 추출, affine 및 색공간 roundtrip 확인.
- `80B4E592`의 실제 노출 14,947 UV 추가 대조(과거 cooked export UV를 PS UV로 직접 사용한 입력 상태; 이번 V 정정 이전 수치): cb4.x=-80; m=sat(-80*mask+81*w). 대표 w=1이면 mask가 0..1인 모든 샘플에서 m=1. 따라서 linearRGB=(cb1.rgb+cb2.rgb*sat(T1.r))*T4.rgb. 구현과 최대 linear 오차 1.49e-8, sRGB 오차 5.96e-8.
- 해당 바닥 sRGB 중앙값 w=1: **0.3690487**. master가 관찰한 약 .37과 일치한다. w=0 중앙값 .3504489이지만 RGB 평균은 (.50781,.33931,.33348)로 붉은 dye가 드러난다. w를 바꿔도 밝기만 단조롭게 보정되는 구조가 아니다. 현재 어두움은 수식 오류로 확인되지 않았으며 누락된 TEXCOORD8과 원본 조명 부재를 남긴다. 현재 cooked export에는 CHUNK UV transform이 이미 반영돼 있으며, 위 중앙값은 V 정정 이전 sampling 결과이므로 spatial 색 검증으로 확대하지 않는다. 근거 없는 밝기 보정은 추가하지 않았다.

비교 swatch `/private/tmp/destiny-w245/shader-worker/top30-swatches.png`를 직접 열어 30재질을 검수했다. 각 쌍 왼쪽은 대표 TEXCOORD8=1, 오른쪽은 0이며 실제 cooked export UV 범위를 PS UV로 직접 간주했던 과거 비교다. 이미지의 rawUV/CHUNK missing 표기는 이번 upstream 확인으로 폐기됐으며 V 정정 후 검수 이미지가 아니다. 주요 layer의 회색↔빨강/파랑/흰색 변화와 canopy palette의 빨강/황토를 확인했다. 원작 화면 일치 검증은 아니다. 개별 swatch PNG와 equation/sampling/floor-focused JSON은 같은 임시 폴더에 있다.

master가 전달한 1차 Blender 전후 검수에서 천막 빨강/황토 회복, proposed overlay 93,834셀, 원본 미변형을 보고했다. 이는 master 수행 결과이며 worker가 Blender/Vision을 조작하거나 그 검증을 독립 완료한 것으로 기록하지 않는다.

## 남은 입력과 인계

우선 확보 대상은 TEXCOORD8의 vertex Buffer t0다. 현재 STATIC cooked export에는 CHUNK UV scale/offset을 다시 확보·적용할 필요가 없다. TerrainPart 경로는 추가 확인 대상이다. genuine raw GPU 입력 경로를 새로 구현할 때는 cb1[1]이 필요하다. Frame/TIME cb는 해당 family별로 따로 필요하다. master는 cooked→PS V 변환을 적용하고 vertex substitute를 대표 근사로 표시하며 geometry 변환에 맞는 원본 world/normal을 공급할 수 있다. 작은 패턴의 voxel 평균은 linear RGB에서 수행한 후 palette용 sRGB로 돌리는 것이 색공간상 맞다. 게임 원본 색 완전 복원을 주장하지 않는다.

최종 helper 요청에 따라 basecolor 수식은 유지하고 STATIC 전용 `uv_from_charm_export()` 및 raw/static 계약 metadata만 모듈에 추가했다. 모듈 최종 SHA256은 `af5feab3ef5e0dc2ab173514a38bc0a3351b5f823fde075fdb2bf402cdb4a7b3`다. `_evaluate` AST SHA256은 `8d783541ea2a3fbf4de5ab58d392da425ab51cc574bf2c7223f0b685ee63ab75`로 변경 전후 동일하다. helper의 STATIC/terrain mask, finite/empty, non-mutation, raw missing-CHUNK 보존, module/instance 호출 검증을 통과했다. upstream 원문 9파일과 SHA256·줄 근거는 임시 upstream/ 및 cooked-uv-evidence.json에 보관했다. 기존 UV 기준의 swatch/median 결과를 새 V 변환 검수 결과로 재표기하지 않았다.
