# Requiem-43 (W325, rare shotgun, Pinpoint Slug) — base first_in_last_out

- Identity kept: SUROS mint/red livery, long rectangular shroud over a dark under-barrel, white fore-grip block,
  receiver with recessed ejection window + SUROS logo, red rear bead, raked chunky grip, white stock tube into the
  open "hook" stock with red comb band and slot (slot/logo/stripes via projected UV).
- Elements (r2): body+magazine 69+0 (r1 total 30).
  Atlas 512x512 (T=20). Helpers: art/weapons/w325/_w9/w9.py (box/bar/post/RipMap, preview/measure/compare).
- Fit: rip at 24.67 px/m, muzzle z -8.36 / butt z 16.5 (base -8.38..16.56). Receiver top 12.25 (+hump 12.38, bead 12.24)
  stays under the W148 optic eye line (~13.4). Grip axis (7.5,10.2)->(9.22,6.78) on the base grip (z 7.5..9.5);
  trigger guard z 6.3..7.75 y 9.15. Barrel stops at z 3.7; shell port z 3.7..5.6 is open below y 10.32 with side walls
  for the base shell path (z 3.88..5.42, y 9.67..10.25).
- Deviation: no front sight (rip has none); ADS relies on the W148 overlay dot (NO_OVERLAY not set).
- Unverified: in-game first-person/ADS framing, shell-insert clipping against the port walls, 3P display.
- r2 detail + ADS + W30 pixel style: kit STYLE 'pixel' (palette quantise + bevel lines) with flat material colours painted in special(); DMW-style split slabs (w9.chamfer_box = core + inset 1-step top/bottom plates, optional segments). adscheck OK: wrist top split into 5 segments following the base falling profile, comb starts z 11.02, butt pad top 11.5. Muzzle crown frame around a real bore, ribbed under-barrel, segmented shroud/comb plates, closed guard, collars. Paint: flat SUROS mint/red/dark blocks, red comb band, wordmark as pale texels.
- r3 Chattering-Bone cleanup (69+0): wrist top = 5 axis-aligned steps (was 5 small-angle slabs); crossing stock lower arm/front strut replaced by 3 stepped rear blocks; collars centred on the tube axis; tube extended into the block; guard parts trimmed to meet without overlap. w9 lint: 0 visible coplanar same-direction overlaps (w9.tidy recesses any left by 0.03), no near-parallel overlapping rotated slabs except real angled grip/trigger/stock joints.

## r4 Identity pass — Ace / Izanagi 기준 (2026-11-05)

### IDENTITY LIST

- 민트색 긴 SUROS 슈라우드와 붉은 사선 두 줄
- 옅은 SUROS 픽셀 문자
- 흰색 전방 손잡이와 검정 하부 총열
- 붉은 comb 밴드와 실제 관통 슬롯
- 흰 연결 튜브를 가진 갈고리형 개머리판
- 검정 기울어진 그립과 사각 포구

입체: comb 관통 슬롯, 총열 collar, 포트 레일, butt tread. 페인트: SUROS 글자·사선·붉은 띠·모서리·그립 stipple.

- 요소: 69 → 89 (body 89 + magazine 0). T=20; atlas=[1024, 512]; PNG 12,209 bytes.
- 모든 노출 면을 special()로 직접 도색. 상단 1텍셀 밝은 선/하단 어두운 seam, 근거 있는 패널·고유 표식. Projection fallback 없음.
- 512 atlas는 T20에서 overflow여서 근접 면의 작은 선을 보존하려고 가로1024로 확대; kit가 사용 높이를 자동 잘라냄.
- 검증: kit build 성공, west/east/top/q/front 5방향 렌더 생성·검토, 원본 nx_albedo와 compare PNG 직접 비교, adscheck OK, visible coplanar same-direction 0, 양의 부피·유일 이름·1000 cap 확인.
- 에이스/이자나기의 원본 JSON·면 UV 및 기준 이미지를 실제 읽고, 긴 덩어리 위 선명한 표면 디테일 원칙을 적용. 개별 원작의 문양을 다른 무기에 복사하지 않음.
- 잔여: 본체 중간의 계단형 wrist와 shell port를 기존 base contract에 유지했다. 실제 shell 삽입·파지 확인은 master Vision 대기. 오프라인 렌더이며 실제 client, 팩 로드, 10–20개 FPS 수락을 뜻하지 않음.
- 비교: review/requiem_43_compare.png; 합본: ../_w9/identity_review.png

## r5 Material pass — W123 충신 / 영원한 갈증의 허기 기준 (2026-11-05)

이 절의 재질 처리가 r4의 전체 면 단색 special 도색을 대체한다. STYLE=material. 형상·파지·mag_ 분리는 변경하지 않았다.

참조: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, /tmp/w325-mat-try.png를 직접 확인했고 main의 generate_surface_w123_gnawing_hunger.py paint_tile() 및 generate_surface_w123_beloved.py Paint.tile()을 읽었다. 색상은 각 rip nx/px/pz albedo 팔레트 샘플을 대조했다.

| 재질 이름 | kind | RGB |
|---|---|---|
| white | steel | (183, 190, 186) |
| dark | dark | (16, 19, 20) |
| gunmetal | metal | (67, 65, 64) |
| mint | paint | (134, 156, 151) |
| redlight | glow | (155, 34, 30) |
| polymer | polymer | (52, 49, 47) |
| rubber | rubber | (25, 28, 27) |
| red | paint | (139, 40, 40) |

- special() 잔여: SUROS 글자, 빨간 사선·밴드, comb 민트 경계. 나머지는 재질 bake.
- 면 투영: 원본 명암의 고주파 디테일만 재질 바탕에 결합. 새 id_/mag_id_ 형상·north/south 끝면·회전 grip/stock 위아래면은 detail=0. 위장은 예전 합성 noise 대신 실제 rip 좌표의 색상 mask를 사용.
- 출력: 요소 89, body 89+magazine 0; T=20; atlas [1024, 512]; PNG 171,132 bytes.
- 검증: kit build 성공, west/east/top/q/front 렌더 직접 확인, rip compare 검토, adscheck OK, visible coplanar-same-direction 0, JSON/UV/PNG/manifest SHA 확인.
- 한계: 정적 텍스처 재질 표현이며 런타임 PBR/동적 반사 복원은 아님. 실제 client 팩 로드·파지·ADS·장전·10–20개 성능 검증은 master 취합 대기. Gradle/Minecraft/commit 미실행.
- 합본: ../_w9/material_review.png; 재질 구현: ../_w9/materials9.py; 상세 face 할당: ../_w9/material_assignments.json

## r6 Material 2차 패스 (2026-11-05)

리시버 핀·버튼·포트 레일 → 밝은 machined steel, 트리거가드·방아쇠·총열 리브 → gunmetal. 기존 민트·빨강 외피만 도장 유지.

- 수작업 모티프: SUROS 각인 글자와 사선 띠 유지.
- 대비: rubber RGB(18,21,20), polymer (55,59,56), gunmetal (86,90,86), machined steel (112,119,116)로 단계 구분. 갈색 metal/white steel은 원본 계열 색을 별도 유지.
- 위장: source-aligned mask에 저주파 필터·12px 셀을 적용해 2–3색 큰 덩어리로 정돈. 위장 도장에 자동 wear를 꺼 작은 원본 잡티가 되살아나지 않게 함.
- 전체 요소 면적의 paint 비율(가려진 면 포함): 31.8% → 31.8%. 화면 면적/FPS 지표가 아님.
- geometry SHA 기준선과 동일(89요소); atlas [1024, 512] 유지; build·5방향 render·adscheck OK, 동일평면 0. kit.py 미수정.
- 비교: ../_w9/material_r2_review.png. 검사: ../_w9/material_r2_checks.txt. 인게임 QA·Gradle·commit 미실행.
