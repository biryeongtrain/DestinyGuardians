# H28 — Blender 원본 메시 확인과 직접 변환 시험

> 후속 사용자 승인 후 [게임 통합42](42_H28_원본_메시_게임_통합.md)를 진행했다.
> 아래의 연구-only/미패키징 표기는 이 조사 단계의 기록이며, 후속에서는 로컬 통합을 위한
> 변환 파생 geometry/RGB/composite를 추가한다. 원본 binary/원본 texture 배포와는 구분한다.

2026-10-23. 사용자가 Blender/애드온을 실행한 뒤 실제 리핑 파일을 열어 확인했다.
**H27 cuboid 재구성을 최종안으로 취급하지 않는다.** 이번 단계는 원본 확인과
오프라인 변환 가능성 검증까지다. 게임에서 선택되는 모델은 아직 H27이며 교체하지 않았다.

## 1. 실행 및 장면 보존

- Blender 5.4.0 Alpha의 실행 중인 로컬 애드온 API(`127.0.0.1:9876`)로 연결했다.
  Codex에 등록된 Blender 전용 도구는 없어서 애드온의 JSON TCP 프로토콜을 사용했다.
  전역 MCP 설정/애드온 설치 파일은 수정하지 않았다.
- 기존 `Scene`의 Cube/Camera/Light를 삭제하지 않고 새 검토 장면을 만들었다.
  현재 창은 `Destiny ORIGINAL MESH - Review`다. 기존 장면으로 전환할 수 있다.
- FBX를 별도 장면에 가져온 뒤, 재질 확인용 `.blend`에서는
  `bpy.data.libraries.load(...).meshes`만 append했다. `open_mainfile`이나 원본 스크립트 실행은 하지 않았다.
  재질/이미지/노드 그룹은 메시 의존성으로 로드된다. 사용자 장면/원본 파일에 저장하지 않았다.
- 원본 mesh-local 좌표와 UV를 보존했다. 비교 장면에서만 uniform object scale로
  두 모델 높이를 3으로 맞췄다. 이는 실제 게임 크기나 원본 게임의 월드 단위를 뜻하지 않는다.

## 2. 직접 확인한 형상

| 항목 | Arcstrider Staff | Nightstalker Bow |
|---|---:|---:|
| 정점 | 7,162 | 1,266 |
| `.blend`/Blender FBX import 유효 삼각형 | 9,196 | 1,410 |
| FBX 인코딩된 삼각형 | 9,196 | 1,721 |
| 정점 인덱스가 반복되는 퇴화 면 | 0 | 311 |
| 로컬 장축 | Z | Z |
| 유효 face의 인덱스 집합과 native mesh 일치 | 전체 일치 | 전체 일치 |

활의 1,721/1,410 차이는 추정으로 넘기지 않고 재검사했다. FBX에 같은 정점 인덱스를
반복하는 면이 311개 있으며, 이를 제외한 face의 정점 인덱스 집합은 native 1,410면과
정확히 일치한다. 임의 디테일 삭제나 LOD 감소의 근거가 아니다. H27의 1,721은
바이너리에 들어 있던 면 수로서 당시 기록을 유지한다.

- **지팡이:** 서로 다른 끝 칼날, 실제 단면과 관통 슬롯, 목/링/슬리브의 밀도와 그립 무늬를 확인했다.
  단순 막대/평면 실루엣이 아니다. 홈 중 일부는 형상이고 일부는 normal/색 무늬다.
- **활:** 연속 곡면의 폭/두께 변화, 중앙 덩어리와 안쪽 분기 돌기가 중요하다.
  H27의 tangent cuboid를 더 촘촘히 만드는 것보다 원본 메시 기반 변환이 적합하다.
- 원본 활의 시위는 **휴지 자세의 직선**이다. 애니메이션 clip은 두 FBX 모두 없다.
  원본을 그대로 교체하면 H22의 당긴 V형 시위/화살과 손 접점을 잃는다.
  활의 6개 해시 이름 본만으로 발사 모션을 얻었다고 주장하지 않는다.

## 3. 재질과 렌더

FBX만 import하면 텍스처 연결이 복구되지 않았다. `.blend`의 메시/재질 의존성을
append한 뒤 압축파일 안의 이미지로 경로를 연결해 front/oblique/back 렌더를 만들었다.
각 방향에서 clay와 source-material을 비교했다(EEVEE, 1200×1400, 정사영, AgX).

- 지팡이: Diffuse/MRC/Normal DDS, 각 512×1024. Diffuse는 sRGB,
  MRC/Normal은 Non-Color. 소스 그룹 입력 연결은 확인했으나 packed MRC의 각 채널 역할을 단정하지 않는다.
- 활: `80C2E9EF.png`(512²)가 Base Color 경로, `48A4D880.png`(256²)가
  MATCAP/ColorRamp를 거치는 Emission 경로에 연결된다.
  함께 들어 있던 `80C2E9F0.png`의 역할은 확인되지 않았다.
- 이는 **리핑 자료 작성자의 Blender 재질**이며 Bungie 런타임 셰이더 인증본이 아니다.
  Cycles/EEVEE 재질을 vanilla Minecraft에 그대로 이식할 수 있다는 뜻도 아니다.
- 원본 메시 재질 렌더를 직접 열람했다. 이 이미지는 Minecraft 적용 결과가 아니다.

로컬 결과(임시 경로라 정리/재부팅으로 사라질 수 있음):

- `/tmp/destiny-drive-reference/blender-review/source-material-oblique.png`
- `/tmp/destiny-drive-reference/blender-review/clay-front.png`
- `/tmp/destiny-drive-reference/blender-review/destiny-original-mesh-review.blend`

검토 `.blend`는 새 검토 장면의 의존성만 별도 저장했다. 사용자 원래 장면은 저장하지 않았다.

## 4. 원본 메시 → java-mesh 직접 변환 시험

BetterModel 3.5.1이 사용하는 **java-mesh 0.0.1의 실제 MeshBuilder**를 별도 JVM에서 호출했다.
Blender 원본 mesh-local 정점/삼각형/active-loop-UV를 내보내고 `load(List<MeshShape>)`로 변환했다.
큐브 재저작이나 수동 가짜 변환기가 아니다. 다만 **BetterModel 전체 pack 생성/손 장착 시험은 아니다.**

| 측정 | 지팡이 | 활 |
|---|---:|---:|
| 입력 삼각형 | 9,196 | 1,410 |
| 출력 composite 파트 | 27,588 | 4,230 |
| composite JSON 바이트 | 7,495,792 | 1,103,432 |
| 단일 entry ZIP 바이트 | 1,133,872 | 150,469 |
| finite 행렬 수치 | 441,408 | 67,680 |
| 고유 constant tint | 993 | 197 |
| 빌더가 선택한 primitive | double | single |

두 모델 모두 입력 삼각형당 3파트가 출력됐고 행렬 수치는 모두 finite였다.
파트 수는 엔티티 수나 GPU 드로콜 수가 아니다. ZIP 크기도 최종 Polymer 팩 크기가 아니다.
짧은 변환 실행 시간은 JSON 생성 시간일 뿐 FPS 성능 판정에 사용하지 않는다.

시험 좌표는 `(x,z,-y) * 16/raw_z_extent`(오른손 좌표계, 높이16)로 정규화했다.
UV V는 이미지 top-origin으로 뒤집었다. 이 변환은 손 장착의 yaw/미러/display 설정을 검증한 것이 아니다.
원본 UV는 0~1 밖도 사용한다(지팡이 U 최대 약2). 단순 clamp 재저작을 하면 패턴이 달라질 수 있다.

### 확인된 손실/위험

1. java-mesh는 텍스처를 **삼각형별 평균 RGB의 상수 tint**로 바꾼다.
   원본 픽셀 무늬/알파, normal/MRC, MATCAP/emission 셰이더를 보존하지 않는다.
   이번 입력도 base 이미지뿐이며 원본 재질 bake나 완전한 shader 변환은 아니다.
2. 지팡이 27,588파트를 그대로 배포하는 것은 과도할 수 있다. 기하 디테일 보존과
   변환 비용 사이에서 실루엣/칼날 슬롯/링을 보호한 simplification을 비교해야 한다.
   전부 같은 비율로 decimate하거나 고정 VFX 예산을 장비에 무비판적으로 적용하지 않는다.
3. 원본 활의 직선 시위를 분리하고 H22의 당김 좌표와 합쳐야 한다.
   body 원본 메시와 별도 string/arrow를 결합하는 방향을 우선 검토한다.
4. 메시 primitive의 single/double 선택은 빌더 출력 관찰일 뿐, 게임에서 뒷면이 정상이라는 증거가 아니다.

## 5. 다음 통합 순서와 회귀 계약

1. 활 body의 원본 메시 변환과 지팡이 디테일 보호 경량화 후보를 **새 H28 ID**로 준비한다.
   원본 토폴로지/재질 그대로와 Minecraft 근사 결과를 구분해 비교한다.
2. 기존 장비 item-model 경로와 BetterModel mesh composite를 연결하는 변환/pack 생성 시험을 한다.
   먼저 손 방향/크기/뒷면/팩 누락을 확인한 뒤 런타임 선택을 교체한다.
3. 활 nock `(16.24,8,8)`, tip `(11.27,-4/20,8)`, 당긴 시위와 화살,
   좌/우 context 미러와 안쪽 Ry180을 유지한다. 지팡이 grip `(8,8,8)`/support `(8,12,8)`도 유지한다.
4. H26_r2의 빠른 전개/공격, 서버 애니메이션 clock, 후방 카메라, H25의 실제 장착 위치 VFX를 회귀 검사한다.
5. 모델을 선택한 최종 빌드로 GameTest/JUnit과 Vision20TPS/측면/발사/다인/성능을 새로 수행한다.

**이번에는 런타임/리소스팩/게임 선택 모델을 변경하지 않았다.** GameTest나 Vision을 새로
실행했다고 기록하지 않으며 H27의 과거 통과 수치를 H28 검증으로 재사용하지 않는다.

## 6. 근거와 배포 경계

[H28 QA](../qa/2026-10-23/h28-source/README.md)에 native 집계, FBX 퇴화면 대조,
변환 결과/해시, 사용 코드와 실패 복구를 기록했다. Blockbench MCP는 이 단계에서 호출하지 않았다.
원본 파일/텍스처/렌더/변환 composite는 모두 `/tmp`에 두고 Git/JAR/리소스팩에 넣지 않았다.
출처와 권리 고지는 [H27 검토](40_H27_원본_모델_검토.md)를 따른다. 공개 Drive는 재배포 허가가 아니다.
