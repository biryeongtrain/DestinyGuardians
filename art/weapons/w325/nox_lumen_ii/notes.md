# Nox Lumen II (W325, rare fusion rifle, High-Impact, Omolon) — base erentil_fr4

- Identity kept: long dark shroud with vent slots (UV), white front cap with pointed lower fin and muzzle nub, white
  under-rail dropping into the white diagonal arm, white receiver grille, side canister, two-eared front sight, raked
  grip, skeletal stock (top tube + diagonal strut + ribbed butt), big lower battery module with white top rail.
- Elements (r2): body+magazine 68+9 (r1 total 29).
- Rip extract: the archive misses generic Bungie detail textures (digital camo / battleworn); kit extract baked them
  magenta. proj_cache was extracted with art/weapons/w325/_w9/extract_relink.py (relinks those files by name from other
  read-only rips in /tmp/w325-rips, then runs the unchanged kit extractor).
- Fit: uniform 33 px/m, cap z -9.15 / butt 15.5 (base -9.41..15.56), top 13.45. Moving leaf = the whole rip battery
  module (z -1.4..8.4, y 3.45..7.2) instead of the base's thin cartridge (z 2.02..3.38): intentional rip identity; it
  drops as one block on the base reload timing. W153 aim tip (z 2.46, y 14.2..14.52) kept as overlay inside the sight
  ears (x 7.55..7.8 / 8.2..8.45, top 14.55, centre open above 13.9).
- Unverified: in-game ADS through the ears, large battery block during reload (hand contact / clipping with grip),
  rip hand loop under the battery not modelled.
- r2 detail + ADS + W30 pixel style: kit STYLE 'pixel' (palette quantise + bevel lines) with flat material colours painted in special(); DMW-style split slabs (w9.chamfer_box = core + inset 1-step top/bottom plates, optional segments). adscheck OK: rear receiver dropped to 12.4 behind z 5.2 (base 12.46), sight ears narrowed to z 2.27..2.75 (hollow sight_* frame around the aim tip). Shroud in 3 top plates + side vent rows + white line, stepped cap, lower cells, grille, mech panels, ribbed butt, battery windows. Paint: gunmetal + white accents, black grip.
- r3 Chattering-Bone cleanup (68+9): battery nose and white rail drop rebuilt as stepped blocks (were crossing rotated slabs); receiver tail as 2 steps; grip strips aligned to the grip axis; shroud lip recessed. w9 lint: 0 visible coplanar same-direction overlaps (w9.tidy recesses any left by 0.03), no near-parallel overlapping rotated slabs except real angled grip/trigger/stock joints.

## r4 Identity pass — Ace / Izanagi 기준 (2026-11-05)

### IDENTITY LIST

- 건메탈 긴 몸체와 흰색 전면 캡
- 흰색 대각 지지대·하부 띠
- 측면 냉각핀과 흰색 격자 그릴
- 상부 톱니 레일과 열린 조준 귀
- 골격 개머리판과 검정 사선 스트럿
- 큰 하부 배터리와 실제 구멍이 난 후방 pull loop

입체: 배터리 pull loop, 냉각핀, 상부 rail teeth, canister band. 페인트: 흰 격자·길게 파인 선·배터리 도어·그립.

- 요소: 77 → 118 (body 106 + magazine 12). T=20; atlas=[1024, 512]; PNG 15,059 bytes.
- 모든 노출 면을 special()로 직접 도색. 상단 1텍셀 밝은 선/하단 어두운 seam, 근거 있는 패널·고유 표식. Projection fallback 없음.
- 512 atlas는 T20에서 overflow여서 근접 면의 작은 선을 보존하려고 가로1024로 확대; kit가 사용 높이를 자동 잘라냄.
- 검증: kit build 성공, west/east/top/q/front 5방향 렌더 생성·검토, 원본 nx_albedo와 compare PNG 직접 비교, adscheck OK, visible coplanar same-direction 0, 양의 부피·유일 이름·1000 cap 확인.
- 에이스/이자나기의 원본 JSON·면 UV 및 기준 이미지를 실제 읽고, 긴 덩어리 위 선명한 표면 디테일 원칙을 적용. 개별 원작의 문양을 다른 무기에 복사하지 않음.
- 잔여: 새 배터리 pull loop는 magazine leaf에 포함된다. 실제 reload 손 접촉·loop와 그립 간섭 미검증. 오프라인 렌더이며 실제 client, 팩 로드, 10–20개 FPS 수락을 뜻하지 않음.
- 비교: review/nox_lumen_ii_compare.png; 합본: ../_w9/identity_review.png

## r5 Material pass — W123 충신 / 영원한 갈증의 허기 기준 (2026-11-05)

이 절의 재질 처리가 r4의 전체 면 단색 special 도색을 대체한다. STYLE=material. 형상·파지·mag_ 분리는 변경하지 않았다.

참조: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, /tmp/w325-mat-try.png를 직접 확인했고 main의 generate_surface_w123_gnawing_hunger.py paint_tile() 및 generate_surface_w123_beloved.py Paint.tile()을 읽었다. 색상은 각 rip nx/px/pz albedo 팔레트 샘플을 대조했다.

| 재질 이름 | kind | RGB |
|---|---|---|
| polymer | polymer | (42, 39, 35) |
| white | steel | (183, 188, 187) |
| gunmetal | metal | (83, 79, 73) |
| dark | dark | (16, 19, 20) |
| paint | paint | (75, 70, 65) |
| rubber | rubber | (25, 28, 27) |
| steel | steel | (113, 111, 104) |

- special() 잔여: 포구 중심만 special(). 흰 grille·금속·고무·배터리는 전체 material bake.
- 면 투영: 원본 명암의 고주파 디테일만 재질 바탕에 결합. 새 id_/mag_id_ 형상·north/south 끝면·회전 grip/stock 위아래면은 detail=0. 위장은 예전 합성 noise 대신 실제 rip 좌표의 색상 mask를 사용.
- 출력: 요소 118, body 106+magazine 12; T=20; atlas [1024, 512]; PNG 341,774 bytes.
- 검증: kit build 성공, west/east/top/q/front 렌더 직접 확인, rip compare 검토, adscheck OK, visible coplanar-same-direction 0, JSON/UV/PNG/manifest SHA 확인.
- 한계: 정적 텍스처 재질 표현이며 런타임 PBR/동적 반사 복원은 아님. 실제 client 팩 로드·파지·ADS·장전·10–20개 성능 검증은 master 취합 대기. Gradle/Minecraft/commit 미실행.
- 합본: ../_w9/material_review.png; 재질 구현: ../_w9/materials9.py; 상세 face 할당: ../_w9/material_assignments.json

## r6 Material 2차 패스 (2026-11-05)

mech·stock tube·butt housing·배터리 main/tail → gunmetal, 트리거·sight base → machined steel. 흰색 steel 지지대와 검정 rubber를 구분.

- 수작업 모티프: receiver grille에 1텍셀 가로/세로 격자 홈.
- 대비: rubber RGB(18,21,20), polymer (55,59,56), gunmetal (86,90,86), machined steel (112,119,116)로 단계 구분. 갈색 metal/white steel은 원본 계열 색을 별도 유지.
- 위장: source-aligned mask에 저주파 필터·12px 셀을 적용해 2–3색 큰 덩어리로 정돈. 위장 도장에 자동 wear를 꺼 작은 원본 잡티가 되살아나지 않게 함.
- 전체 요소 면적의 paint 비율(가려진 면 포함): 20.8% → 3.7%. 화면 면적/FPS 지표가 아님.
- geometry SHA 기준선과 동일(118요소); atlas [1024, 512] 유지; build·5방향 render·adscheck OK, 동일평면 0. kit.py 미수정.
- 비교: ../_w9/material_r2_review.png. 검사: ../_w9/material_r2_checks.txt. 인게임 QA·Gradle·commit 미실행.
