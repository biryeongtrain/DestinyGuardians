# Guardian Rises — map pipeline (W300 lane `w300-map`)

작성 2026-11-01. 범위: 추출 GLB → Minecraft 블록 구역(.zone) + 구역 마커 + 서버 배치 코드.
상태: 오프라인 생성·렌더 리뷰·단위 테스트까지 완료. **인게임(서버/클라이언트) 배치·조명·성능·동선은 미검증** — 마지막 절의 master 체크리스트 참조.

## 1. 산출물

| 파일 | 역할 |
|---|---|
| `scripts/campaign/rising_maps.py` | 파이프라인 전체 (GLB 파싱, 크롭, 복셀화, 팔레트, 형상, 마커, .zone 기록, 리뷰 렌더) |
| `src/main/resources/data/destiny/guardian_rises/zones/{gateway,breach,divide,dock13}.zone` | 구역 블록 템플릿 (gzip, 아래 형식) |
| `.../zones/markers.json` | 구역 로컬 좌표 마커 + 출처 메모 |
| `campaign/map/ZoneTemplate.java` | 로더(검증·캐시) + 예산 배치기 `Build` (`RisingServices.ZoneBuild`) |
| `campaign/map/RisingZones.java` | `RisingServices.Zones` 구현, `init()`이 등록 + 비동기 사전 로드 |
| `campaign/map/ZonePalette.java` | 허용 블록 화이트리스트 (스크립트 `PALETTE_DEF`와 동기) |
| `src/test/.../campaign/map/ZoneTemplateTest.java` | 왕복·경계·마커 문법·예산 배치 종료·번들 데이터 일관성 |

재생성 (원본 폴더는 읽기 전용, 출력은 결정적 — gzip mtime 0):

```
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --python scripts/campaign/rising_maps.py -- build   --zone all   # ~2분
$B -b --factory-startup --python scripts/campaign/rising_maps.py -- srcview --zone all   # 원본 GLB 렌더(Workbench)
$B -b --factory-startup --python scripts/campaign/rising_maps.py -- voxview --zone all   # 복셀 결과 레이마칭 렌더
$B -b --factory-startup --python scripts/campaign/rising_maps.py -- montage --zone all   # 원본|복셀 비교판
$B -b --factory-startup --python scripts/campaign/rising_maps.py -- analyze --zone all   # 보행 도달성 맵
$B -b --factory-startup --python scripts/campaign/rising_maps.py -- survey --glb the_breach --box x0 y0 z0 x1 y1 z1 --res 0.5 --out f.png
```

Blender는 headless 이미지 로더(텍스처)와 원본 렌더에만 쓰인다. 복셀화 자체는 numpy.

## 2. 좌표와 축척

원본 JSON/CSV는 Destiny Z-up. GLB 루트 노드가 `(x,y,z)->(x,z,-y)`를 이미 갖고 있으므로 스크립트는 **자식 노드 TRS를 원본 공간에서 읽고 한 번만** Minecraft 좌표 `(x, z, -y)`로 바꾼다 (GLB에 축 변환 재적용 없음). 구역 로컬 블록 = `floor((mc - zone_min) * SCALE)`.

**SCALE = 1.0 (1 블록 = 1 m).** Destiny 수호자(~1.9 m)와 Minecraft 플레이어(1.8 m)가 같은 비율이라 문·통로·차량·난간이 원본 비례로 읽힌다. 1.25배는 원본의 도약 위주 단차를 더 키워 (점프 1.25블록) 보행성이 나빠지고, 파일·배치 블록 수가 ~2배가 되어 채택하지 않았다. 아래 보행 분석상 1.0으로 네 구역 모든 진행 마커가 바닐라 이동으로 도달 가능하다.

## 3. 크롭 (원본 Z-up 좌표, m)

각 구역 = **core**(플레이 동선, 전 인스턴스·정밀 샘플) + **vista**(경관 셸: 최대 변 ≥ 12 m 인 큰 인스턴스만, 0.5 m 샘플, core 밖만). 3 km 이상 인스턴스(스카이돔)는 제외.

| 구역 | core | vista | 근거 |
|---|---|---|---|
| gateway | (285,-1065,-40)–(425,-770,92) | (150,-1150,-60)–(600,-700,130) | 활동 데이터에 배치가 없어 지형 리뷰로 결정. 고속도로 차량 정체열 x≈320–360, y −1050→−830이 장벽(y≈−820, 높이 ~85 m)의 관문으로 이어짐. 33 km 버블 중 이 경로만 사용 |
| breach | (335,-845,-6)–(565,-645,40) | 없음 (실내) | `actors.csv` breach_catwalks 배우 x 390–533, y −679–−820, z 8–18; o_weapon(410.6,−793.7), o_chest_weapon(534.9,−737.7), o_breach_gating_back/garage. 차고 북쪽 참호(y≈−676)까지 포함 |
| divide | (95,-705,-20)–(450,-470,70) | (-50,-850,-40)–(600,-350,160) | graveyard_public 배우 x 205–275, y −572–−597, o_graveyard_chest(229,−575.6); 참호(Breach 출구)부터 격납고 관문까지 |
| dock13 | (20,-680,-15)–(190,-480,60) | (-100,-800,-40)–(350,-350,150) | hangar_ship 배우(104–127,−533–−543), o_hangar_gating(109.6,−533.6), hangar_roof_broken_b(78.5,−567) |

조사용 상면 래스터: `w300-evidence/map/survey/*.png` (Breach z 슬라이스, Gateway 경로, Divide/Dock 광역).

제외 처리: 구름 카드 텍스처 `8108F04A`(Gateway `80C8358D` 운해), 텍스처 없는 ≤4삼각형 대형 평면(차단벽/수면/안개 판: Gateway `80C83591`, Breach `80C7A654`). 알파는 **이진 컷아웃 텍스처**(α<0.1 비율 >15%, 이진 >80%)에서만 불투명도로 쓴다 — Destiny 기본색 텍스처의 알파는 대부분 다른 데이터라 일괄 적용하면 벽이 사라진다.

## 4. 복셀화와 형상

- 삼각형을 0.25 m(core)/0.5 m(vista) 무게중심 격자로 표면 샘플 → 블록당 2×2×2 하위 점유 비트, 평균 색(텍스처 128² 박스 필터, 원본 sRGB 기본색), 지형 비율, 법선(상/하/수직) 비율.
- **지형 채움:** 지형 표면 아래 3블록을 같은 재질로 채움(충돌·투시 방지). 그 아래 다른 지오메트리를 만나면 멈춤. 3블록으로 제한해 배치 블록 수를 1/4로 줄였다(Gateway 445만 → 97만).
- **반블록:** 하위 점유가 아래 절반뿐이고 위가 비고 위향 면이 많으면 하단 반블록, 위 절반뿐이면 상단 반블록. 경사로·계단이 0.5블록 단차가 되어 자동 오르기(0.6) 안에 든다.
- **기둥/가로등:** 두 수평축 모두 얇은 수직 셀은 한 열로 중복 제거 후 벽 블록 기둥(`*_wall`, up=true). 고립된 굵은 수직 열도 벽 기둥, 얇은 고립선은 `iron_chain`.
- **난간:** 한 축이 얇고 바닥 위 1–2칸인 수직 셀은 `iron_bars`, 연결 상태(east/north/south/west)는 스크립트가 계산해 저장(배치 시 이웃 갱신 없이도 올바른 모양).
- **스무딩:** 26이웃 다수결(≥10표, 자기 표 ≤3)로 반점 제거.

## 5. 팔레트 (`PALETTE_DEF` ↔ `ZonePalette`)

블록 평균색은 로컬 26.3 클라이언트 jar의 바닐라 텍스처에서 직접 계산(`jar_texture_rgb`). 분류는 Lab 최근접(a,b 가중 1.25)에 다음 제약:

| 가족 | 블록 | 쓰임 |
|---|---|---|
| snow/ground/rock | snow_block, coarse/rooted dirt, dirt, soul_soil, podzol, packed_mud, moss_block, brown_terracotta, granite, calcite, andesite, stone, tuff, cobbled_deepslate | **지형 전용 허용 집합**(지형 샘플은 이것만) |
| concrete | smooth_stone, polished_andesite/diorite, stone_bricks, polished_tuff, cyan_terracotta, white_concrete | 장벽 패널·콘크리트 |
| metal/dark | polished_deepslate, deepslate_tiles, smooth_basalt, iron_block, polished_blackstone, netherite_block | 강재·어두운 금속 |
| rust/paint | waxed (exposed) cut copper, terracotta 계열, mud_bricks, orange/yellow concrete, yellow_terracotta | 녹·위험 도장(주황) |
| teal | waxed weathered/oxidized cut copper, prismarine, dark_prismarine | 청록 포인트 |

구조물 샘플은 흙/이끼(+400)·눈(+80) 패널티(흰 차량을 눈으로 만들지 않음). 채도 보정은 크로마 >10인 구조물만 최대 +25% (회색 바닥이 분홍 테라코타로 가던 문제 수정). 산화·무작위 틱 블록을 피하려 구리는 전부 waxed, 중력 블록(모래·자갈·콘크리트 파우더) 없음, 잔디 블록 대신 moss_block.

## 6. 보행·경계·조명

- 보행 모델: 발 칸+머리 칸 통과 가능, 아래 지지, 4방향 이동, 1블록 오르기, 최대 12블록 낙하. core 범위 안에서만 BFS.
- **결과(spawn.player 기준 도달 칸 / 하늘 노출 비율):** gateway 34,170 / 0.89, breach 10,287 / 0.15, divide 53,970 / 0.73, dock13 3,177 / 0.12. 모든 trigger/checkpoint/exit/enemy 마커가 도달 가능하며 빌드가 이를 강제(불가 시 실패). `w300-evidence/map/reach-check.log`.
- 보정 지오메트리(FIXUPS): **현재 필요 없음(빈 목록)**. 경사로/채움/비움 기능은 있으나 사용하지 않았다.
- **경계 barrier:** 도달 가능한 바닥이 core 경계에 닿는 곳에 보이지 않는 barrier 벽(발 −1 ~ +3). gateway 2,464 / breach 385 / divide 1,510 / dock13 0 블록. vista는 걷는 곳이 아니다.
- **조명:** 원본 조명 리소스(SExpensiveLight 등)는 위치 해독이 없어 재현하지 않았다. 대신 **전환 가능한 구리 전구**를 천장에 박는다: `light.*` 마커 = 고정구 블록 좌표, 태그 `block`(켠 상태), `unlit`(끈 상태), `level`, `phase`, `mount`.
  - `phase=always`는 빌드 시 켜짐(waxed_weathered_copper_bulb, 밝기 8: Breach 시작의 희미한 비상등, 격납고 관문, Gateway 관문 랜턴).
  - `phase=breach_lightup`/`ship_scan`은 **꺼진** waxed_exposed_copper_bulb(밝기 12)로 배치 — 감독이 고스트 점등 시 `lit=true`로 바꾸면 된다. 구리 전구는 신호 없이 `lit` 상태를 유지한다.
  - 천장이 없으면 바닥 랜턴(mount=floor). phase가 always가 아니면 빌드에 넣지 않고 감독이 배치.
  - Breach는 덮인 실내라 하늘빛이 거의 없다(도달 칸의 15%만 하늘 노출) → 어둠 속 빛 웅덩이 연출이 가능하나 인게임 밝기 미확인.

## 7. 마커 (`markers.json`)

좌표는 **구역 로컬 블록 좌표, 발 위치, x/z 칸 중심(+0.5)**. 월드 = origin + pos (`RisingZones.markers`가 더해 줌). Yaw는 Minecraft 도(0=+Z 남, −90=+X 동, 180=북). 문법은 `RisingServices.Marker` javadoc 그대로이며 Java가 로드 시 검증(문법·중복·enemy kind·구역 범위·spawn.player 존재).

| 구역 | 마커 (요약) |
|---|---|
| gateway | spawn.player·checkpoint.wake(차량 잔해 남단, 장벽을 향함), ghost.scan(눈앞 1.9 m, 발 +1.45 m, 플레이어를 향함, `look_at=spawn.player`), trigger.wall_entrance(관문, r6), light.gate_warm, exit.breach(관문 아래 터널 끝) |
| breach | spawn.player(원본 Ghost 배치), ghost.scan, trigger.breach_dark, trigger.rifle/prop.rifle(o_weapon), checkpoint.arm_yourself, enemy.breach_first/far/chest/corridor/garage.N, trigger.cache/prop.shotgun_cache(o_chest_weapon), trigger.breach_exit·exit.divide(차고 북쪽 참호), light.* 8개 |
| divide | spawn.player(참호), trigger.divide_enter, checkpoint.divide_walker, trigger.walker_arena(r20), enemy.divide_lure/walker/reinforce.N, prop.heavy_cache(o_graveyard_chest), prop.skiff_drop(원본 Skiff 배치, 공중 85,−577,83.5), exit.dock13(격납고 관문) |
| dock13 | spawn.player·trigger.dock_enter·checkpoint.dock_13(관문 안쪽), prop.ship(파손 지붕 아래 — 이륙 구멍), trigger.ship, exit.tower, enemy.dock_defense.N, light.hangar_gate, light.ship_bay |

`prop.*`/`ghost.scan`/`light.*`는 보행 칸 스냅을 하지 않는다(정확 위치). enemy 태그: `kind`(dreg|vandal|captain|shank|walker), `order`(구역 내 교전 순서).

**적 수(배우 수 ≠ 스폰 수, 활성 ≤ 24):**

| 교전 | 구성 | 원본 근거 |
|---|---|---|
| breach_first (1) | dreg 3, vandal 1 | dreg/slag/vandal (452–490, −797–−806) |
| breach_far (2) | dreg 3 | dreg (532–533, −816–−820) |
| breach_chest (3) | dreg 2 | dreg (532.9, −744) |
| breach_corridor (4) | dreg 5, vandal 1 | dropdown dreg 8 (465–508, −715–−728) |
| breach_garage (5) | captain 1, vandal 3, dreg 4 | garage captain/vandals/dregs |
| divide_lure (1) | dreg 2, vandal 3, shank 3 | lure 분대 dreg 2, vandal 3, shank 6 |
| divide_walker (2) | walker 1 | **저작**: 원본 Walker 좌표(82,−577.5,84)는 스키프 투하 공중점이라 지상 개활지(반경 3, 높이 9 비움 검사)를 선택 |
| divide_reinforce (3) | dreg 3, vandal 1 | **저작** (기획서 ‘Walker와 증원’) |
| dock_defense (1) | dreg 3, vandal 2, shank 2 | hangar mixed/shank 분대 |

`fallen_slag`(소스 이름)는 dreg로 취급. 같은 좌표에 겹친 원본 배우(예: Breach 449.6,−758.1의 장면 분대 15개 — 파이프 위 연출 지점으로 보행 불가)는 스폰에 쓰지 않았다. 스폰 칸은 원본 배우 점에 가까운 도달 가능 바닥에서 3칸 이상 간격으로 고른다.

**출처 구분:** markers.json `provenance`에 마커별 `src:`(추출 배치) / `authored:`(W300 설계) 표기. Gateway 전체, ghost.scan, 모든 trigger 반경, checkpoint, exit, light, Walker 지상 위치, divide_reinforce, prop.ship 위치는 **원본 데이터가 없는 저작물**이다. 원본 회전은 Z축 요(forward 축 미검증)로만 변환했다.

## 8. .zone 형식 v1

gzip 스트림, 빅엔디안:

```
"DGZONE01" | int sx, sy, sz | u16 n | n × (u16 len, utf8 block state)   # index 0 = minecraft:air
int runs | runs × (varint palette index, varint length)                 # 선형 index = (y*sz + z)*sx + x
```

Java 로더는 크기(≤1024×384×1024), 팔레트(≤256, 0번 air, 나머지 `ZonePalette.allowed`), 런 합 = 부피, 후행 바이트 없음을 검사하고 16³ 비지 않은 섹션만 바이트 배열로 보관한다(템플릿은 불변, 구역별 1회 디코드 후 모든 인스턴스가 공유).

| 구역 | 크기 (x×y×z) | 비공기 블록 | 파일 |
|---|---|---|---|
| gateway | 450×190×450 | 966,391 | 423,067 B |
| breach | 230×46×200 | 334,233 | 190,663 B |
| divide | 650×200×500 | 1,540,274 | 848,111 B |
| dock13 | 450×190×450 | 515,230 | 214,828 B |
| 합계 | | 3,356,128 | 1.68 MB (+ markers.json 27 KB) — 예산 8 MB 이내 |

## 9. 런타임 API (감독용)

```java
RisingZones.init();                                   // 모드 초기화에서 1회: 등록 + 템플릿 비동기 사전 로드
var zones = RisingServices.zones().orElseThrow();
var build = zones.begin(level, Zone.GATEWAY, origin); // 서버 스레드, 빈(void) 영역 전제
// 매 tick: if (build.step(2_000_000L)) -> 완료; build.progress() 0..1; 취소: build.cancel() (멱등)
var markers = zones.markers(Zone.GATEWAY, origin);    // 월드 좌표
```

- `step`은 공기를 건너뛰고 비공기만 `setBlock(UPDATE_CLIENTS | UPDATE_SKIP_ALL_SIDEEFFECTS)` — 이웃/형상 갱신·드롭·onPlace 없음. 섹션 열(x,z) 순서, 섹션 안 아래→위. 128블록마다 시간 확인; 예산 0이어도 매 호출 최소 128블록(또는 한 섹션 끝) 진행.
- 청크: 소유 비영속 티켓 `TicketType(0, LOADING|KEEP_DIMENSION_ACTIVE)`로 필요한 청크만 비동기 로드(`addTicketAndLoadWithRadius`, 서버 스레드 블로킹 없음), 끝난 열은 6열 창 뒤 해제, `cancel`/완료 시 전부 해제. 해제된 청크는 런타임 월드 저장소로 내려갔다가 플레이어 접근 시 다시 로드된다(이 동작은 인게임 미확인 — 아래 체크리스트).
- 높이: `origin.y ≥ level.getMinY()` 이고 `origin.y + sy − 1 ≤ level.getMaxY()` 아니면 예외. 오버월드 타입(−64..319)에서 divide(200) 포함 전 구역은 origin.y = −40..120이면 들어간다.
- 구역 간 간격: 가장 큰 구역이 650×500이므로 origin을 x 또는 z로 1024블록 이상 띄우면 겹치지 않는다(vista 포함). 구역 전환은 exit/trigger 마커에서 감독이 텔레포트.
- 블록 단가 미측정: 3.36 M setBlock(+조명 엔진 작업)을 2 ms/tick이면 수 분 단위가 될 수 있다. 첫 구역(Gateway 97만)은 로딩 화면 중, 다음 구역은 앞 구역 플레이 중 미리 짓는 운용을 권장.

## 10. 리뷰 이미지 (`w300-evidence/map/renders/`)

- `*_compare.png`: 왼쪽 원본 GLB(Blender Workbench, 텍스처색), 오른쪽 복셀 결과(블록 텍스처 평균색 레이마칭), 같은 카메라(보행 칸 스냅, 눈높이 1.62 m, 세로 FOV 70°). gateway: wake/cars/gate/tunnel/overview, breach: start/weapon/arena/chest/corridor/garage/overview, divide: enter/courtyard/hangar_gate/overview, dock13: gate/hangar/overview.
- `*_top.png` 복셀 상면, `*_markers_top.png` 마커 오버레이(노랑 spawn, 청록 ghost, 초록 trigger, 빨강 enemy, 자홍 prop, 흰 exit, 주황 light, 파랑 checkpoint), `*_walk.png` 도달 바닥(초록)/비도달(파랑), `breach_cut*.png` 높이 단면.
- 렌더러는 근사다: Minecraft 조명·AO·실제 텍스처 디테일·barrier 비가시 여부를 재현하지 않는다(barrier/light는 렌더에서 투명 처리).

## 11. 재현하지 않은 것 / 알려진 한계

- 원본 셰이더·지형 블렌딩·데칼·안료·조명·포그·반사. 기본색 텍스처 평균만 사용 → 표면 디테일(패널 줄, 녹 흐름, 파이프 곡면)은 1 m 블록으로 뭉개진다.
- 유리 판별 없음(창은 주변 재질로 막히거나 빈칸). 케이블·전선은 사슬/난간/블록 조각으로 근사.
- 차량은 흰 블록 덩어리(실루엣·색만 유지). 가로등은 벽 블록 기둥+블록 머리.
- 구역 사이 높이·위치 연속성 없음: Gateway 출구(관문 아래 터널, z≈−3)와 Breach 시작(Ghost, z 17.4)은 다른 높이 — 감독의 화면 전환/텔레포트 전제.
- Divide는 일부 지붕(격납고 지붕 z≈32 등)에 걸어 올라갈 수 있다(진행 막힘은 아님). vista 지형은 저해상도 LOD 카드라 평평한 사각 패치가 보인다.
- 콜리전/내비메시가 추출에 없어 충돌은 렌더 메시 표면에서 추정. 보행 분석은 Minecraft 이동의 근사(점프 대시·스프린트 점프·0.6폭 끼임 미모델).
- 블록 배치·조명 갱신 비용, 청크 해제 후 재로드, 실제 어둠/밝기, 마커 위치의 체감(엄폐·시야) 모두 인게임 미검증.

## 12. master 인게임 확인 항목

1. 네 구역 각각 `begin`→`step` 완료 시간과 MSPT(2 ms 예산), 완료 후 블록 누락/잔여 티켓 0, 청크 해제→재접근 시 블록 유지.
2. Gateway spawn에서 장벽 방향 낮은 시점·고스트 스캔 위치(ghost.scan) 시야, 관문→exit.breach 실제 보행.
3. Breach 어둠(밤/낮 모두), 비상등 1개의 빛 웅덩이, `light.*`를 `lit=true`로 바꿨을 때 밝기·위치, rifle/cache 프롭 위치가 바닥/상자 위에 맞는지.
4. 각 교전 스폰이 바닥 위·벽 밖인지, Walker 개활지 크기(rg_walker 모델 실측과 비교), 참호→Divide→격납고 동선, barrier 경계에서 걸림 체감.
5. Dock 13 prop.ship 위치가 파손 지붕 아래 이륙 경로와 맞는지(rg_ship 크기), 격납고 내부 밝기.
6. iron_bars/벽 기둥/반블록 형태가 이웃 갱신 없이 의도대로 보이는지(클라이언트 렌더).

## 13. r2 조명 패스 (2026-11-01, master Vision 피드백)

증상(실클라이언트, 인스턴스 시간 2000): Dock 13 스폰·격납고 내부가 거의 암흑, Divide 지붕 아래 구간 어두움. 시뮬레이션도 동일: Dock 스폰 칸 블록광 0, 보행 칸 3,177 중 2,041이 4 미만.

**시뮬레이터 (`rising_maps.py` `block_light`/`sky_light`/`lighting_pass`):** 바닐라 규칙대로 광원 L → 이웃 L−1, 투명 칸으로만 전파. 투명 = air/light/barrier/iron_bars/iron_chain/lantern/*_wall. 반블록·눈층은 **불투명으로 보수 처리**(실제로는 옆으로 새므로 시뮬레이션은 과소평가만 함). 하늘빛 = 열린 열 15, 이후 −1 전파(낮 기준). 경로 = spawn.player에서 도달 가능한 발 칸(core 내부). 유효광 = max(블록광, 하늘빛). 지붕 아래 = 하늘빛 < 4.

**목표와 빌드 실패 조건 (`LIGHT_TARGETS`):** dock13 = 전체 경로 최소 4, 지붕 아래 평균 7–10(배치 목표 8.5). divide = 지붕 아래 경로만 최소 4. 미달이면 SystemExit로 빌드 실패. 함선 구역(prop.ship 반경 9, 높이 ±4의 경로 칸)은 ship_scan 점등 시 **블록광만으로** 평균 ≥ 11.5(밤에도 성립).

**배치 규칙:** 가장 어두운 경로 칸부터 근처(수평 3, 위 2–6) 벽/천장의 노출된 완전 블록을 구리 전구로 교체(밝기 12 우선, 15는 이득 1.33배일 때). 걸 곳이 없으면 머리 위 투명 칸에 보이지 않는 `light[level=11]`. 평균 목표 후 남은 칸이 어둡게 남아 대비가 유지된다(지붕 아래 분포는 4–14).

| | 경로 칸 | 최소 | 평균 | p10 | <4 |
|---|---|---|---|---|---|
| dock13 이전 (전체/지붕 아래) | 3,177 / 2,046 | 0 / 0 | 4.18 / 0.22 | 0 / 0 | 2,041 / 2,041 |
| dock13 이후 | 3,177 / 2,046 | 4 / 4 | 9.70 / 8.54 | 6 / 6 | 0 / 0 |
| divide 이전 (전체/지붕 아래) | 53,970 / 4,006 | 0 / 0 | 13.07 / 0.49 | 7 / 0 | 4,006 / 4,006 |
| divide 이후 | 53,970 / 4,006 | 4 / 4 | 13.60 / 7.34 | 8 / 5 | 0 / 0 |

고정 조명(빌드 시 켜짐, 마커 없음 — 정적 블록): dock13 전구12 29·전구15 46·fill 3, divide 전구12 84·전구15 40·fill 11.
함선 구역: 빌드 시 블록광 평균 0(낮에는 지붕 파손부 하늘빛으로 유효 14.9), ship_scan 점등 시 블록광 최소 10·평균 11.53. 이를 위한 `light.ship_bay_1..28`(phase=ship_scan): mount=ceiling 13개는 꺼진 waxed_copper_bulb가 빌드에 포함(켜려면 `block` 상태로 교체), **mount=fill 15개는 빌드에 없음 — 감독이 `block`(=`light[level=15]`)을 해당 좌표에 배치**. 기존 `light.ship_bay`(바닥 랜턴)는 유지. 마커 문법 변경 없음, RisingZones 동작 변경 없음.

증거: `w300-evidence/map/r2/` — `light_{dock13,divide}.json`(전/후 히스토그램 포함), `dock13_light_compare.png`(왼쪽 이전/오른쪽 이후: spawn, spawn 반대편, dock_enter→함선, 방어 구역, trigger.ship), `divide_light_compare.png`, `dock13_bay_scan_compare.png`(블록광만: 빌드 vs ship_scan 점등), `build-r2.log`. 렌더 밝기 곡선은 바닐라 lightmap 근사(밝기 옵션·감마 미반영)라 실화면보다 어둡다.

미검증: 실제 클라이언트 밝기 체감(밝기 설정·감마), 반블록 투과로 인한 실제 값 상승, fill light 마커를 감독이 배치하는 경로, 전구가 원본 벽 무늬를 끊는 시각적 위치.

## 14. r3 QA 기준 경로 (리소스 미포함)

`rising_maps.py routes --zone all` → `w300-evidence/map/r3/routes.json`. 보행 모델(`reach`와 동일: 4방향, 1블록 오르기, 12블록 낙하, core 내부)로 spawn.player에서 목표 순서대로 BFS 최단 경로. 목표 칸 = trigger/exit 반경 안의 도달 칸, `light.arena_one`은 고정구 아래 반경 4. 웨이포인트는 수평 3–6블록 간격(`select_waypoints`), `jump: true` = 다음 웨이포인트까지 바닥이 0.6블록 넘게 오름(반블록 단차는 점프 불필요). y = 바닥 표면 높이.

| 구역 | 스텝 | 점프 | 웨이포인트 |
|---|---|---|---|
| gateway | 194 (+ 무점프 대안 224) | 20 (대안 0) | 48 |
| breach | 505 | 7 | 116 |
| divide | 463 | 50 | 103 |
| dock13 | 55 | 2 | 12 |

Gateway 판정과 단서 제안은 `r3/README.md`, `gateway_tunnel_cues.json`, `gateway_lane_cues.json`. 최단 경로는 차량 지붕을 넘는 직선(점프 20)이고, 사람이 걷기 쉬운 무점프 동쪽 차선(x≈196–204)이 따로 있다.

## 15. r4 경로 단서 조명 + 번들 routes.json

빌드 순서: 마커 → barrier → **`route_cues`** → `lighting_pass`. `route_cues`는 점프 비용 8의 Dijkstra(`guidance_route`)로 spawn.player→목표 순서(ROUTES) 경로를 만들고, 단서를 블록으로 배치·마커화한 뒤 도달성을 다시 검사한다(마커 도달 불가·경로 칸 막힘이면 빌드 실패).

- **Gateway 터널** (`CUE_TUNNEL`, wall_entrance 이후 경로): 최소 6·평균 8 미달이면 빌드 실패. 결과 0/5.2 → 7/11.3. `light.gate_trail_1` 벽 전구(12), `_2.._4` 바닥 랜턴.
- **Gateway 차선 빵부스러기** (`CUE_LANE`): 무점프 차선을 따라 ~32스텝마다 바닥 랜턴 `light.gate_lane_1..6`. 자리를 못 찾으면 ±8스텝 내에서 이동, 그래도 없으면 빌드 실패.
- **Divide 전환점** (`CUE_TURNS`, 최대 6): 직선 고스트 궤적의 ≥30%가 블록 안에 묻히고 경로가 목표 방향에서 ≥45° 꺾이는 구간을 묶어 길이×각도 순 상위만 사용 → 5곳 `light.route_turn_1..5`.
- **보행 폭 규칙** (`_lantern_site`): 랜턴은 경로 칸 위 금지, 마커 ±1 금지, 장애물에 붙이거나 2칸 바깥. 랜턴에 인접한 보행 칸 어느 것도 1칸 폭으로 남기지 않는다(독립 검증 `r4/verify.json` narrowed=[]).
- 모든 단서는 `phase=always`, 태그 `block/mount/level`(+전구는 `unlit`), 마커 문법 변경 없음.

`zones/routes.json` (번들, 5.9 KB): `{"schema":1,"format":…,"zones":{zone:[[x,y,z,jump],…]}}`, 구역 로컬, y=바닥 표면, jump=1은 다음 점 전에 점프 필요. 웨이포인트 수평 간격 3–6(테스트 강제). Gateway는 무점프 차선이 주 경로.

| 구역 | 스텝 | 점프 | 웨이포인트 |
|---|---|---|---|
| gateway | 222 | 0 | 50 |
| breach | 507 | 0 | 118 |
| divide | 473 | 16 (r3 최단 경로 50) | 98 |
| dock13 | 55 | 0 | 12 |

`ZoneTemplateTest.bundledRoutesAreWalkable`: 모든 구역 존재, 점이 비공기 아닌 바닥 위·머리 공간, 간격 3–6. 같은 변경에서 테스트 헬퍼 `passable`이 `minecraft:light_gray_terracotta`를 light 블록으로 오인하던 접두사 버그를 고쳤다(마커 검사도 더 엄격해졌고 통과).

## 16. r5 경로 종점 = 목표 트리거 내부

`check_route_objectives`: 각 구역 경로의 **목표 웨이포인트**와 **목표에 가장 가까운 웨이포인트**가 목표 반경 − 1.5 m(`ROUTE_GOAL_INSET`) 안, 높이 태그 이내에 있어야 하며 마지막 웨이포인트는 최종 목표여야 한다 — 아니면 빌드 실패. 반경은 감독의 `RisingMission.near`와 같은 의미(수평 radius, 수직 height; light.* 목표는 고정구 아래 4 m). 경로 목표 칸 선택도 같은 인셋을 쓴다. `trigger.ship` radius 5 → **7**을 생성기에 고정. `ZoneTemplateTest.bundledRoutesAreWalkable`가 각 구역 경로 끝이 최종 목표 안(감독 판정식)인지도 검사한다. 결과 표: `w300-evidence/map/r5/route_*.json` `objective_checks`.

## 17. r6 Dock 13 웨이브 분할 + Skiff 힌트 마커

**웨이브.** `dock_defense` 단일 웨이브(7)를 `order` 1/2/3 세 웨이브로 나눴다(Ghost 7a/52/74가 3웨이브 이상을 전제). 합계 14.

| order | encounter | 구성 | 위치 |
|---|---|---|---|
| 1 | `dock_defense` | dreg 2, vandal 1, shank 2 | 기존 착륙장(지붕 아래) |
| 2 | `dock_ship_west` | dreg 2, vandal 2 | `prop.ship` 서쪽, 지붕 구멍 아래 열린 하늘 |
| 3 | `dock_ship_east` | captain 1, vandal 2, dreg 2 | `prop.ship` 동쪽, 지붕 구멍 아래 열린 하늘 |

웨이브 2/3 영역은 `area`의 `avoid`(함선 중심 6 m 제외)와 `sky`(열린 하늘 기둥, `open_column`)로 고른다. 실제 거리 6.0–9.0 m.

**Skiff 힌트.** `skiff_hints()`가 `lighting_pass` 뒤에 `SkiffDrop.Sky`와 같은 탐색(고도 9,7,11,5,13…30, 반경 24, 탑승자 = 최밀집 지상 유닛 10 m 이내, 충돌 7×5×7 = `SkiffZoneScanTest`)으로 `prop.skiff_<encounter>`를 쓴다. `SKIFF_HINTS`에서 `dock_ship_west`/`dock_ship_east`는 필수(못 찾으면 빌드 실패), `dock_defense`/`breach_corridor`는 선택. 결과 `w300-evidence/map/r6/skiff_*.json`, `skiff-zone-scan.md`.

- `prop.skiff_dock_ship_west` 172.5, 64, 213.5 — 탑승자 4/4 가시, 오프셋 0.4 m
- `prop.skiff_dock_ship_east` 181.5, 65, 222.5 — 탑승자 5/5 가시, 오프셋 1.8 m
- `dock_defense`, `breach_corridor`: 40 m 내 보이는 하늘 없음 → 마커 없음. 스캔도 SKIP이므로 정상 스폰된다.

**감독 측 확인 필요.** `SkiffDrop.Choice.openingByShip(DOCK13)`은 "Dock 13은 단일 웨이브"라는 전제로 웨이브 0도 Skiff 대상으로 둔다. 분할 후 웨이브 0은 지붕 아래라 런타임 탐색이 SKIP하여 결과는 정상 스폰이지만, 주석/의도가 이제 맞지 않는다(맵 레인 소유 아님 — 미변경).
