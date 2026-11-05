# Aachen-LR2 (W325, rare sniper, Adaptive) — base beloved

- Identity kept: green/white forest camo receiver + long fluted handguard (slash vents via UV), wide box muzzle brake
  with two real lateral ports, side laser box, boxy white objective housing scope with top/side turrets and rubber
  eyecup, right-side bolt knob, dark thumbhole stock with camo cheek panel, square magazine with camo floor plate.
- Elements (r2): body+magazine 74+3 (r1 total 46).
- Fit: rip at 17.3 px/m, muzzle z -15.58 / butt z 13.45 (base -15.5..13.5); y datum 12.6 = rip Z 0.27 lands barrel,
  trigger guard (z 6.8..8.55, y 7.92) and thumbhole grip (post (8.35,9.4)->(8.95,7.25)) on the base grip.
  Magazine moved onto the base moving magazine (z 3.95..6.55, y 6.45..8.6, x 7.58..8.54); its faces sample the rip
  magazine (rip z 4.85..7.1) through MAG_Z, magwell z 3.7..7.0 surrounds it.
- Scope: modelled for hip/3P only (sniper ADS hides the gun, WeaponScopes W45); top 12.58 like the base scope (12.56).
- Unverified: in-game hip/3P framing, reload hand contact on the re-placed magazine, thumbhole vs base hand pose.
- r2 detail + ADS + W30 pixel style: kit STYLE 'pixel' (palette quantise + bevel lines) with flat material colours painted in special(); DMW-style split slabs (w9.chamfer_box = core + inset 1-step top/bottom plates, optional segments). adscheck OK: scope compressed into the base scope box z 4.95..8.85 (SCOPE_Z warps the projection), top <= 12.55; stock/butt top 10.55. Segmented handguard plates, slanted vent slots, toothed under-rail slots, magwell lip, bolt rod, butt grooves. Paint: bone/olive/green blob camo on receiver/handguard/scope, dark furniture.
- r3 Chattering-Bone cleanup (74+3): stock lower arm = 2 flush steps (was 2 rotated slabs); brake front/rear rings, magwell lip recessed off coplanar faces. w9 lint: 0 visible coplanar same-direction overlaps (w9.tidy recesses any left by 0.03), no near-parallel overlapping rotated slabs except real angled grip/trigger/stock joints.

## r4 Identity pass — Ace / Izanagi 기준 (2026-11-05)

### IDENTITY LIST

- 뼈색·올리브·녹색 3색 위장
- 측면 포트 두 개가 열린 넓은 제퇴기
- 길고 가는 핸드가드와 사선 환기구
- 하얀 대물렌즈 하우징과 청색 유리
- 빨간 레이저 발광면
- 엄지 구멍이 열린 검정 개머리판과 사각 탄창

입체: 핸드가드 냉각핀, 탄창 리브, 스코프 측면 ring. 페인트: 위장·사선 환기구·패널선·렌즈 반사.

- 요소: 77 → 103 (body 94 + magazine 9). T=20; atlas=[1024, 512]; PNG 20,091 bytes.
- 모든 노출 면을 special()로 직접 도색. 상단 1텍셀 밝은 선/하단 어두운 seam, 근거 있는 패널·고유 표식. Projection fallback 없음.
- 512 atlas는 T20에서 overflow여서 근접 면의 작은 선을 보존하려고 가로1024로 확대; kit가 사용 높이를 자동 잘라냄.
- 검증: kit build 성공, west/east/top/q/front 5방향 렌더 생성·검토, 원본 nx_albedo와 compare PNG 직접 비교, adscheck OK, visible coplanar same-direction 0, 양의 부피·유일 이름·1000 cap 확인.
- 에이스/이자나기의 원본 JSON·면 UV 및 기준 이미지를 실제 읽고, 긴 덩어리 위 선명한 표면 디테일 원칙을 적용. 개별 원작의 문양을 다른 무기에 복사하지 않음.
- 잔여: 기존 base 범위에 압축된 스코프와 이동 탄창 위치를 유지했다. 게임의 hip/3P·장전 손 접촉 미검증. 오프라인 렌더이며 실제 client, 팩 로드, 10–20개 FPS 수락을 뜻하지 않음.
- 비교: review/aachen_lr2_compare.png; 합본: ../_w9/identity_review.png

## r5 Material pass — W123 충신 / 영원한 갈증의 허기 기준 (2026-11-05)

이 절의 재질 처리가 r4의 전체 면 단색 special 도색을 대체한다. STYLE=material. 형상·파지·mag_ 분리는 변경하지 않았다.

참조: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, /tmp/w325-mat-try.png를 직접 확인했고 main의 generate_surface_w123_gnawing_hunger.py paint_tile() 및 generate_surface_w123_beloved.py Paint.tile()을 읽었다. 색상은 각 rip nx/px/pz albedo 팔레트 샘플을 대조했다.

| 재질 이름 | kind | RGB |
|---|---|---|
| gunmetal | steel | (62, 66, 60) |
| bone | paint | (190, 184, 173) |
| dark | dark | (16, 19, 20) |
| polymer | polymer | (46, 48, 41) |
| redlight | glow | (155, 34, 30) |
| steel | steel | (145, 151, 141) |
| rubber | rubber | (25, 28, 27) |

- special() 잔여: 원본 좌표 기반 녹색 위장 안료, 사선 환기구, 청색 렌즈·반사, 포구 중심.
- 면 투영: 원본 명암의 고주파 디테일만 재질 바탕에 결합. 새 id_/mag_id_ 형상·north/south 끝면·회전 grip/stock 위아래면은 detail=0. 위장은 예전 합성 noise 대신 실제 rip 좌표의 색상 mask를 사용.
- 출력: 요소 103, body 94+magazine 9; T=20; atlas [1024, 512]; PNG 240,323 bytes.
- 검증: kit build 성공, west/east/top/q/front 렌더 직접 확인, rip compare 검토, adscheck OK, visible coplanar-same-direction 0, JSON/UV/PNG/manifest SHA 확인.
- 한계: 정적 텍스처 재질 표현이며 런타임 PBR/동적 반사 복원은 아님. 실제 client 팩 로드·파지·ADS·장전·10–20개 성능 검증은 master 취합 대기. Gradle/Minecraft/commit 미실행.
- 합본: ../_w9/material_review.png; 재질 구현: ../_w9/materials9.py; 상세 face 할당: ../_w9/material_assignments.json

## r6 Material 2차 패스 (2026-11-05)

리시버 측판·roof·sill·탄창·magwell → gunmetal, 볼트·스코프 ring → machined steel. 도장은 핸드가드·optic 외피의 원본 위장 부위로 제한.

- 수작업 모티프: 탄창 측면 3줄 1텍셀 압인 홈 + 기존 사선 냉각 슬릿.
- 대비: rubber RGB(18,21,20), polymer (55,59,56), gunmetal (86,90,86), machined steel (112,119,116)로 단계 구분. 갈색 metal/white steel은 원본 계열 색을 별도 유지.
- 위장: source-aligned mask에 저주파 필터·12px 셀을 적용해 2–3색 큰 덩어리로 정돈. 위장 도장에 자동 wear를 꺼 작은 원본 잡티가 되살아나지 않게 함.
- 전체 요소 면적의 paint 비율(가려진 면 포함): 41.5% → 27.2%. 화면 면적/FPS 지표가 아님.
- geometry SHA 기준선과 동일(103요소); atlas [1024, 512] 유지; build·5방향 render·adscheck OK, 동일평면 0. kit.py 미수정.
- 비교: ../_w9/material_r2_review.png. 검사: ../_w9/material_r2_checks.txt. 인게임 QA·Gradle·commit 미실행.
