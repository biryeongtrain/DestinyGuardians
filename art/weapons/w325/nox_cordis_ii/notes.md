# Nox Cordis II (W325, rare fusion rifle, Rapid-Fire) — base null_composure

- Identity kept: compact blue/white Arctic-camo box shroud with three black side windows + chevron (UV), open front cage
  over the barrel, stepped white muzzle with cyan bore, long white top rail, raked black grip into the black C-frame
  lower bar (two grey windows), blue battery unit (upright block + front box of the frame), skeletal stock with black
  butt plate.
- Elements (r2): body+magazine 85+6 (r1 total 29).
- Fit: uniform 37 px/m; rip top rail 13.2, battery centred on the base battery (z 0.23). Muzzle z -11.7 / butt 10.3
  (base -13.1..11.85: the rip is shorter; kept rip proportions instead of stretching). Grip post (5.35,9.0)->(6.45,5.2)
  over the base grip region. Battery = moving leaf, z -2.1..1.65, y 2.05..9.0 (base battery z -1.47..1.93, y 4.11..10.86;
  ours reaches ~2 px lower). W153 aim tip (z 0.4, y 14.2) kept as overlay, framed by notched sight ears (top 14.05),
  rest of the gun under 13.45.
- Unverified: in-game ADS alignment through the notch, battery reload path vs the fixed frame bar (battery drops along
  the frame front), first-person framing of the taller C-frame.
- r2 detail + ADS + W30 pixel style: kit STYLE 'pixel' (palette quantise + bevel lines) with flat material colours painted in special(); DMW-style split slabs (w9.chamfer_box = core + inset 1-step top/bottom plates, optional segments). adscheck OK: rail 13.05 front / 12.9 behind the sight (base 13.07/12.92), receiver/stock/butt <= 12.25 (base 12.28); hollow notched sight_* kept. Toothed rail, shroud side panels with ribs, end cap, frame windows, butt ribs, battery cell slots + latch. Paint: navy/white blob camo, pink rail, black furniture, green status light.
- r3 Chattering-Bone cleanup (85+6): grip texture strips now share the grip rotation axis (were offset parallel slabs). w9 lint: 0 visible coplanar same-direction overlaps (w9.tidy recesses any left by 0.03), no near-parallel overlapping rotated slabs except real angled grip/trigger/stock joints.

## r4 Identity pass — Ace / Izanagi 기준 (2026-11-05)

### IDENTITY LIST

- 흰색·남색 블록 위장
- 세 개 검정 셀과 흰 이중 화살표
- 연분홍 흰색 상부 톱니 레일
- 열린 전방 cage와 청록 포구
- 검정 C형 하부 프레임
- 세로로 내려오는 큰 위장 배터리와 검정 셀

입체: 안쪽으로 들어간 셀 코어, header/footer frame, 화살표 패널, 배터리 cell ribs. 페인트: 이중 화살표·작은 표식·격자·위장.

- 요소: 91 → 117 (body 103 + magazine 14). T=20; atlas=[1024, 1024]; PNG 29,060 bytes.
- 모든 노출 면을 special()로 직접 도색. 상단 1텍셀 밝은 선/하단 어두운 seam, 근거 있는 패널·고유 표식. Projection fallback 없음.
- 512 atlas는 T20에서 overflow여서 근접 면의 작은 선을 보존하려고 가로1024로 확대; kit가 사용 높이를 자동 잘라냄.
- 검증: kit build 성공, west/east/top/q/front 5방향 렌더 생성·검토, 원본 nx_albedo와 compare PNG 직접 비교, adscheck OK, visible coplanar same-direction 0, 양의 부피·유일 이름·1000 cap 확인.
- 에이스/이자나기의 원본 JSON·면 UV 및 기준 이미지를 실제 읽고, 긴 덩어리 위 선명한 표면 디테일 원칙을 적용. 개별 원작의 문양을 다른 무기에 복사하지 않음.
- 잔여: 배터리가 base보다 아래로 긴 기존 형태 유지. ADS notch의 실제 시야·배터리 낙하와 frame 간섭 미검증. 오프라인 렌더이며 실제 client, 팩 로드, 10–20개 FPS 수락을 뜻하지 않음.
- 비교: review/nox_cordis_ii_compare.png; 합본: ../_w9/identity_review.png

## r5 Material pass — W123 충신 / 영원한 갈증의 허기 기준 (2026-11-05)

이 절의 재질 처리가 r4의 전체 면 단색 special 도색을 대체한다. STYLE=material. 형상·파지·mag_ 분리는 변경하지 않았다.

참조: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, /tmp/w325-mat-try.png를 직접 확인했고 main의 generate_surface_w123_gnawing_hunger.py paint_tile() 및 generate_surface_w123_beloved.py Paint.tile()을 읽었다. 색상은 각 rip nx/px/pz albedo 팔레트 샘플을 대조했다.

| 재질 이름 | kind | RGB |
|---|---|---|
| pink | metal | (201, 184, 179) |
| navy | paint | (49, 58, 75) |
| polymer | polymer | (35, 38, 40) |
| steel | steel | (127, 135, 135) |
| dark | dark | (16, 19, 20) |
| greenlight | glow | (72, 181, 95) |
| white | paint | (193, 196, 193) |
| rubber | rubber | (25, 28, 27) |

- special() 잔여: 원본 좌표 기반 흰 위장 안료, 이중 화살표, 작은 로고, 상태등 반사, 청록 포구 중심.
- 면 투영: 원본 명암의 고주파 디테일만 재질 바탕에 결합. 새 id_/mag_id_ 형상·north/south 끝면·회전 grip/stock 위아래면은 detail=0. 위장은 예전 합성 noise 대신 실제 rip 좌표의 색상 mask를 사용.
- 출력: 요소 117, body 103+magazine 14; T=20; atlas [1024, 1024]; PNG 339,369 bytes.
- 검증: kit build 성공, west/east/top/q/front 렌더 직접 확인, rip compare 검토, adscheck OK, visible coplanar-same-direction 0, JSON/UV/PNG/manifest SHA 확인.
- 한계: 정적 텍스처 재질 표현이며 런타임 PBR/동적 반사 복원은 아님. 실제 client 팩 로드·파지·ADS·장전·10–20개 성능 검증은 master 취합 대기. Gradle/Minecraft/commit 미실행.
- 합본: ../_w9/material_review.png; 재질 구현: ../_w9/materials9.py; 상세 face 할당: ../_w9/material_assignments.json

## r6 Material 2차 패스 (2026-11-05)

노출 barrel core·cage post·트리거가드·latch → gunmetal, receiver grille·logo plate·pin → machined steel. 남색/흰 외피 위장은 큰 두 색 덩어리로 유지.

- 수작업 모티프: 1텍셀 이중 화살표와 작은 receiver 표식 유지.
- 대비: rubber RGB(18,21,20), polymer (55,59,56), gunmetal (86,90,86), machined steel (112,119,116)로 단계 구분. 갈색 metal/white steel은 원본 계열 색을 별도 유지.
- 위장: source-aligned mask에 저주파 필터·12px 셀을 적용해 2–3색 큰 덩어리로 정돈. 위장 도장에 자동 wear를 꺼 작은 원본 잡티가 되살아나지 않게 함.
- 전체 요소 면적의 paint 비율(가려진 면 포함): 48.6% → 45.0%. 화면 면적/FPS 지표가 아님.
- geometry SHA 기준선과 동일(117요소); atlas [1024, 1024] 유지; build·5방향 render·adscheck OK, 동일평면 0. kit.py 미수정.
- 비교: ../_w9/material_r2_review.png. 검사: ../_w9/material_r2_checks.txt. 인게임 QA·Gradle·commit 미실행.
