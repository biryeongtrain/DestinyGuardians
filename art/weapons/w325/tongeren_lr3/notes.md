# Tongeren-LR3 (W325, rare sniper, Rapid-Fire) — base apostate

- Identity kept: long maroon/bone boxy shroud with open front window (barrel + two collars visible through it), raised
  rear shroud with sight band, under-shroud skid with a through slot and hinge post, dark side armour plates with sloped
  lower edge, white top rail, maroon scope with dark hood + side turret, bolt knob right, hex-panel thumbhole stock,
  bone magazine with black window (UV), white trigger loop.
- Elements (r2): body+magazine 89+2 (r1 total 44).
- Fit: rip at 23.2 px/m authored in the rip frame then shifted DZ +0.4 (grip post (7.35,7.7)->(7.95,5.75) on the base
  grip, butt 13.5; muzzle -15.1 vs base -15.49). Magazine z 2.5..5.1 / y 6.0..7.6 sits in the base moving magazine span
  (z 0.54..5.04, y 6.88..9.1) but is lower/shorter than the base mag (rip shape kept).
- Scope (10.4..12.4) is hip/3P only (sniper ADS hides the gun, W45).
- Unverified: in-game hip/3P framing, reload hand contact on the small rip magazine, stock vs base hand pose.
- r2 detail + ADS + W30 pixel style: kit STYLE 'pixel' (palette quantise + bevel lines) with flat material colours painted in special(); DMW-style split slabs (w9.chamfer_box = core + inset 1-step top/bottom plates, optional segments). adscheck OK: scope compressed to z 2.5..6.4 (SCOPE_Z), shroud ramp/raise/sight band lowered to 10.8, stock upper split with a neck dip at z 8.9..9.2 (base 9.46). Shroud in 3 top plates + end lip, side slots, stepped side plates with bolts, toothed receiver rail, hex stock windows. Paint: maroon/bone/dark blocks.
- r3 Chattering-Bone cleanup (89+2): side-plate ramp slabs replaced by 3 axis-aligned steps per side; stock lower arm one slab (was 2 segments); guard/scope rim coplanar overlaps removed. w9 lint: 0 visible coplanar same-direction overlaps (w9.tidy recesses any left by 0.03), no near-parallel overlapping rotated slabs except real angled grip/trigger/stock joints.

## r4 Identity pass — Ace / Izanagi 기준 (2026-11-05)

### IDENTITY LIST

- 적갈색·뼈색 긴 박스형 슈라우드
- 전면 창에 드러나는 총열과 collar
- 실제 구멍이 난 하부 skid
- 큰 검정 측면 장갑과 밝은 inset
- 두 줄 육각형 개머리판 패널
- 적갈색 스코프와 뼈색 탄창의 검은 창

입체: 두 줄 얕은 stock inset, 전방 shroud fins. 페인트: 육각 bevel 무늬·패널선·뼈색 하단 띠·렌즈.

- 요소: 91 → 103 (body 101 + magazine 2). T=20; atlas=[1024, 512]; PNG 13,447 bytes.
- 모든 노출 면을 special()로 직접 도색. 상단 1텍셀 밝은 선/하단 어두운 seam, 근거 있는 패널·고유 표식. Projection fallback 없음.
- 512 atlas는 T20에서 overflow여서 근접 면의 작은 선을 보존하려고 가로1024로 확대; kit가 사용 높이를 자동 잘라냄.
- 검증: kit build 성공, west/east/top/q/front 5방향 렌더 생성·검토, 원본 nx_albedo와 compare PNG 직접 비교, adscheck OK, visible coplanar same-direction 0, 양의 부피·유일 이름·1000 cap 확인.
- 에이스/이자나기의 원본 JSON·면 UV 및 기준 이미지를 실제 읽고, 긴 덩어리 위 선명한 표면 디테일 원칙을 적용. 개별 원작의 문양을 다른 무기에 복사하지 않음.
- 잔여: 기존 scope 압축과 낮은 탄창 비율 유지. 게임의 hip/3P·탄창 손 접촉 미검증. 오프라인 렌더이며 실제 client, 팩 로드, 10–20개 FPS 수락을 뜻하지 않음.
- 비교: review/tongeren_lr3_compare.png; 합본: ../_w9/identity_review.png

- r4 최종 수정: 상단 육각 패널 끝을 stock-neck dip z 8.9..9.2 바깥으로 잘라 ADS 침범을 수정. 최종 출력 JSON을 대상으로 adscheck 재통과.

## r5 Material pass — W123 충신 / 영원한 갈증의 허기 기준 (2026-11-05)

이 절의 재질 처리가 r4의 전체 면 단색 special 도색을 대체한다. STYLE=material. 형상·파지·mag_ 분리는 변경하지 않았다.

참조: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, /tmp/w325-mat-try.png를 직접 확인했고 main의 generate_surface_w123_gnawing_hunger.py paint_tile() 및 generate_surface_w123_beloved.py Paint.tile()을 읽었다. 색상은 각 rip nx/px/pz albedo 팔레트 샘플을 대조했다.

| 재질 이름 | kind | RGB |
|---|---|---|
| bone | paint | (165, 150, 129) |
| gunmetal | metal | (63, 65, 61) |
| maroon | paint | (103, 62, 56) |
| dark | dark | (16, 19, 20) |
| rubber | rubber | (25, 28, 27) |
| polymer | polymer | (44, 47, 43) |

- special() 잔여: 육각 inset 테두리, 청색 렌즈·반사, 포구 중심. 적갈색·뼈색의 마모는 원본 relief.
- 면 투영: 원본 명암의 고주파 디테일만 재질 바탕에 결합. 새 id_/mag_id_ 형상·north/south 끝면·회전 grip/stock 위아래면은 detail=0. 위장은 예전 합성 noise 대신 실제 rip 좌표의 색상 mask를 사용.
- 출력: 요소 103, body 101+magazine 2; T=20; atlas [1024, 512]; PNG 293,677 bytes.
- 검증: kit build 성공, west/east/top/q/front 렌더 직접 확인, rip compare 검토, adscheck OK, visible coplanar-same-direction 0, JSON/UV/PNG/manifest SHA 확인.
- 한계: 정적 텍스처 재질 표현이며 런타임 PBR/동적 반사 복원은 아님. 실제 client 팩 로드·파지·ADS·장전·10–20개 성능 검증은 master 취합 대기. Gradle/Minecraft/commit 미실행.
- 합본: ../_w9/material_review.png; 재질 구현: ../_w9/materials9.py; 상세 face 할당: ../_w9/material_assignments.json

## r6 Material 2차 패스 (2026-11-05)

collar·전면 총열 팁·sight band·탄창·볼트·scope turret → 따뜻한 alloy steel. 적갈색 외피와 뼈색 stock 도장은 유지.

- 수작업 모티프: 탄창 상하단 1텍셀 접합선 + 기존 육각 테두리.
- 대비: rubber RGB(18,21,20), polymer (55,59,56), gunmetal (86,90,86), machined steel (112,119,116)로 단계 구분. 갈색 metal/white steel은 원본 계열 색을 별도 유지.
- 위장: source-aligned mask에 저주파 필터·12px 셀을 적용해 2–3색 큰 덩어리로 정돈. 위장 도장에 자동 wear를 꺼 작은 원본 잡티가 되살아나지 않게 함.
- 전체 요소 면적의 paint 비율(가려진 면 포함): 46.9% → 41.0%. 화면 면적/FPS 지표가 아님.
- geometry SHA 기준선과 동일(103요소); atlas [1024, 512] 유지; build·5방향 render·adscheck OK, 동일평면 0. kit.py 미수정.
- 비교: ../_w9/material_r2_review.png. 검사: ../_w9/material_r2_checks.txt. 인게임 QA·Gradle·commit 미실행.
