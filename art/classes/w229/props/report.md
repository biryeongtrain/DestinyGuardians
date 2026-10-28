# W229 신규 직업 궁극기 소품 — 통합 후보 R1

세 소품은 master 통합 가능한 아트 후보다. **1차 native Vision PNG 피드백 / 수정 / 2차 master 확인은 미완료**다. worker는 Gradle, 게임, Vision/CU, commit을 실행하지 않았다. repo와 원본/SSD/live Blender를 쓰지 않았고 출력은 이 폴더 안에만 만들었다.

## 통합

`integration-manifest.json`의 9개 파일만 repo의 대응 `src/main/resources/assets/destiny/` 경로로 복사한다. runtime item IDs는 `destiny:class_ability/titan/solar_super`, `destiny:class_ability/titan/void_super`, `destiny:class_ability/warlock/solar_super`다. 각 item은 `minecraft:model`로 같은 model ID를 가리킨다. melee는 master가 동일 모델로 alias하며 별도 복제본을 만들지 않았다. 코드/등록/효과 타이밍은 master 소유다.

| 소품 | cube 초안 | 최종 cube | adapter 출력 | 최종 합계 |
|---|---:|---:|---:|---:|
| Hammer of Sol | 79 | 21 | 200 | 221 |
| Sentinel Shield | 98 | 22 | 320 | 342 |
| Dawnblade | 95 | 35 | 176 | 211 |

79/98/95는 의미 있는 continuous shaft, ferrule, head mass, guard wing, dome/rim/back brace의 cube 초안이다. 수를 채우기 위한 디테일은 넣지 않았다. 최종은 새머리/부리/세 타격 이빨, 둥근 방패 돔, 검의 테이퍼·뾰족한 끝·연속 날개 가드를 위해 저작한 윤곽만 W115 adapter로 바꿨다. 원본 vertex/component/voxel/decimate 전사는 하지 않았다. 망치100 / 방패160 / 검88개 저작 삼각면이 각각 2개 native zero-depth masked cube plane으로 변환되며, 이 증가분까지 모두 센다. 이 plane들은 닫힌 prism/dome의 각 면이다. 큰 몸체를 앞뒤 alpha 사진 두 장으로 대체한 것이 아니다. 구멍/깊이/후면 지지대와 파지 bridge는 실제 형상이다.

## 원본과 UV

`evidence/headless-props.json`은 세 실제 .blend를 각자 `--background --factory-startup --disable-autoexec`, `open_mainfile(load_ui=False,use_scripts=False)`로 평가한 실측과 source hash다. 721/1094,1591/2606,6282/8476 vertices/triangles. armature/action은 모두 없다. 조사 worker index와 source SHA, UV/메시 수를 대조했고 모든 원본 파일의 해시가 읽기 후 일치했다. 외부 studio HDRI는 원본 전달에 없으므로 중립 studio 조명으로 대체했다. 소품 mesh/필수 DDS 누락은 없다. 원본 motion/손 bone은 None이며 invent하지 않았다.

원본의 실제 UV로 diffuse/normal을 읽은 독립 headless palette bake를 새 의미 부품의 앞/뒤에 재투영했다. 새 면 UV는 2048 RGBA atlas, 2px extruded gutter, 앞/뒤 분리다. 검의 음수 U 반복은 원본 Blender texture sampling에서 처리한다. 방패 중앙 기하 문양·미세 벌집·outer panel, 망치 새 눈/깃털/diamond grip, 검의 blade/guard 줄무늬를 원본 UV에서 가져왔다. broad volume과 단차는 geometry, 얕은 engraving은 UV다. 옆면은 정돈한 소재색이며 원본 UV를 전면 1:1 보존한 것과는 다르다. orthographic 재투영·새 단면에서 일부 fine detail 근사/늘어짐 한계가 남는다.

원본 diffuse만을 최종 안료라고 부르지 않는다. 망치 source shader는 검붉은 mask여서 별도 임시 solar orange/gold ramp를 사용했다. 방패는 source shader의 violet ramp를 참고해 grayscale diffuse에 정적 violet을 입혔다. 검은 source gold diffuse + 약한 normal relief를 사용했다. source Normal 강도 .45, 제한적인 밝기 보정/정적 studio relief이며 PBR/Fresnel/원작 발광 복원이 아니다. MRC 채널 의미는 추정하지 않고 native bake에 사용하지 않았다. 검 Emission DDS가 존재하지만 이번 static atlas는 diffuse/normal 기반이며 별도 원작 emission 복원은 하지 않았다. native triangle surface light_emission=3은 명시적인 임시 표시 보정이다. shader glow/동적 bloom은 master VFX와 별개다.

## 좌표와 export

모든 모델의 손 파지 원점은 model `[8,8,8]`. 망치와 검은 +Y(손잡이 끝→머리/칼끝), 방패 면은 +Z다. 망치는 raw `[Y,Z,X]`, 검/방패는 `[X,Z,-Y]`의 오른손 좌표계. 길이20u / 검 전체26u / 방패 지름20u의 uniform source scale을 썼다. 정확한 scale·source grip 기준·실제 visible bounds는 소품별 `*-uv-axis-budget.json`에 있다. alpha adapter의 비어 있는 사각 support 모서리 bounds와 실제 visible authored bounds를 분리해 기록했다.

망치 palm은 raw Z=0, 검은 raw Z=-.108의 static source grip 안이다. 방패 source 뒤 X brace/중앙 mount를 확인하고, native 팔이 plate를 관통하지 않도록 rear palm bridge 중심을 `[8,8,8]`로 두고 plate를 +Z로 옮겼다. canonical source palm z=-.052는 저작한 retarget offset이며 원본 bone/애니메이션 측정값이 아니다. master는 native 손·팔 간섭을 확인해야 한다.

기존 H28 `build_super_mesh_h28.py`, `HunterMeshCompiler.java`, H27 display를 읽었다. native cube 경로에서 item local=(coord-[8,8,8])/16이며 `thirdperson_righthand`는 rotation0/translation[0,2,0]/scale1로 H28 보정을 유지한다. BetterModel/java-mesh 입력에서만 쓰던 `(-(x-8)/16,(y-8)/16,-(z-8)/16)`의 X/Z flip을 cube JSON에 중복 적용하지 않았다. handed pose/limb root 자체를 변경하지 않았다. 1P/GUI는 후보 표시값이므로 native 검수 대상이다.

실제 Blockbench 5.1.4 `Codecs.java_block.compile({raw:true,cube_name:true})`로 망치79 cube 초안을 export하고 private view PNG를 저장했다. 이후 두 번째 새 소유 프로젝트를 구성하는 동안 localhost MCP endpoint가 끊겼다. shared 앱 재시작/기존 프로젝트 편집은 하지 않았다. 마지막 selection 복귀는 endpoint 단절 이후 확인하지 못했다. 이후 설치된 app.asar에서 **같은 compile 함수 원문을 읽기 전용 추출하여** 격리 Node Cube/Texture context로 여섯 draft/final을 export했다. live 망치79개와 모든 element/face UV/rotation 값이 일치함을 확인했다. `headless-codec.json` 참조. 이는 native exporter 확인이며 Minecraft native codec/pack 수락은 아니다.

삼각 경로는 repo의 `scripts/mesh/native_triangle_elements_w115.py`를 읽어 직접 사용했다. Minecraft26.3 Euler x/y/z 회전, 각 plane의 north/south 반전 UV 및 right-triangle alpha atlas다. `vertices`/`triangles` 같은 가상 바닐라 필드는 없다. 대각 cutout에 1.25 texel conservative coverage를 두어 subpixel 내부 실금을 줄였다. mipmap/거리에서 윤곽 alias와 seam은 native에서 확인해야 한다.

## 증거와 다음 단계

- `evidence/source-3way-contact.png`: 원본 shader의 독립 headless Blender 정면/단면/사선.
- `evidence/modeled-3way-contact.png`: 실제 설치 codec 출력 JSON과 atlas를 다시 읽은 독립 CPU renderer 정면/단면/사선.
- `inspection/*-final.bbmodel`: 정확한 native geometry/face UV/embedded atlas 편집 사본.
- `evidence/*-uv-axis-budget.json`: 섬별 pixel rect, 축/파지, cube+adapter 출력 예산.
- `integration-manifest.json`, `owned-manifest.json`, `outputs-manifest.json`, `SHA256SUMS`: 통합 범위와 해시.

master가 compile/pack load 후 세 소품 owner/observer 파지·앞/뒤·사선·투척/근접을 1차 Vision PNG로 전달하면 수정한다. 그 뒤 2차 master 확인 전에는 최종 수락으로 표시하지 않는다. native26.3 alpha/mip, MC/BetterModel hand standard frame, resource texture 로드와 10–20 동시 표시의 관측은 미검증이다. 원본 archive/.blend/DDS는 배포 묶음에 포함하지 않으며 원본/파생물의 재배포 권리를 보증하지 않는다.
