# Parsec TSu (W325, rare fusion rifle, High-Impact, Häkke) — base erentil_fr4

- Identity kept: mint-white Häkke shroud with dark face plate and side window panel (UV), top rail, low bumper with
  bore rod, dark under-edge sloping into the lower frame, white front frame block with side box, dark raked grip,
  skeletal stock (top tube, dark rear post, white lower wedge, butt), big lower battery block with orange stripe.
- Elements (r2): body+magazine 73+7 (r1 total 28).
- Fit: uniform 36 px/m, muzzle z -9.05 / butt 14.6 (base -9.41..15.56; rip is shorter, proportions kept), top 13.45.
  Moving leaf = the whole rip battery block (z 0.2..9.4, y 2.45..5.4) instead of the base's thin cartridge
  (z 2.02..3.38): rip identity, drops as one block on the base reload timing. W153 aim tip (z 2.46, y 14.2..14.52) kept
  as overlay inside sight ears (top 14.55, centre open above 13.85); rip TrueSight post left out.
- proj_cache extracted with art/weapons/w325/_w9/extract_relink.py (only the iridescence lookup was relinked).
- Unverified: in-game ADS through the ears, reload drop of the large battery block, hand pose on the grip.
- r2 detail + ADS + W30 pixel style: kit STYLE 'pixel' (palette quantise + bevel lines) with flat material colours painted in special(); DMW-style split slabs (w9.chamfer_box = core + inset 1-step top/bottom plates, optional segments). adscheck OK: receiver rear block dropped to 12.4 behind z 3.8 (base 12.46), sight ears z 2.27..2.8 (hollow sight_* frame). Toothed rail, chamfered shroud panels, face-plate vents, side window/strips, receiver vents, stock post ribs, battery slots + orange stripe. Paint: white body with mint wear blobs, dark furniture.
- r3 Chattering-Bone cleanup (73+7): stepped lower stock (was a slab poking out over the grip), under-slope and battery tail as steps, grip strips aligned, coplanar shroud/top/window/band faces separated. w9 lint: 0 visible coplanar same-direction overlaps (w9.tidy recesses any left by 0.03), no near-parallel overlapping rotated slabs except real angled grip/trigger/stock joints.

## r4 Identity pass — Ace / Izanagi 기준 (2026-11-05)

### IDENTITY LIST

- 흰색·민트색 몸체와 검정 전면 환기구
- 두 개 긴 측면 띠와 검정 작은 창
- 민트색 상부 화살표형 inset
- 흰색 전방 범퍼와 낮은 포구
- 검정 C형 그립 프레임·골격 개머리판
- 큰 하부 배터리의 도어선과 주황 띠

입체: 측면 창 가로 bar, receiver fins, 배터리 latch. 페인트: 민트 inset·배터리 도어·패널선·렌즈 및 모서리.

- 요소: 80 → 102 (body 89 + magazine 13). T=20; atlas=[1024, 512]; PNG 20,195 bytes.
- 모든 노출 면을 special()로 직접 도색. 상단 1텍셀 밝은 선/하단 어두운 seam, 근거 있는 패널·고유 표식. Projection fallback 없음.
- 512 atlas는 T20에서 overflow여서 근접 면의 작은 선을 보존하려고 가로1024로 확대; kit가 사용 높이를 자동 잘라냄.
- 검증: kit build 성공, west/east/top/q/front 5방향 렌더 생성·검토, 원본 nx_albedo와 compare PNG 직접 비교, adscheck OK, visible coplanar same-direction 0, 양의 부피·유일 이름·1000 cap 확인.
- 에이스/이자나기의 원본 JSON·면 UV 및 기준 이미지를 실제 읽고, 긴 덩어리 위 선명한 표면 디테일 원칙을 적용. 개별 원작의 문양을 다른 무기에 복사하지 않음.
- 잔여: 큰 배터리 전체가 기존 moving leaf를 따른다. 실제 ADS와 reload 손 접촉 미검증. 오프라인 렌더이며 실제 client, 팩 로드, 10–20개 FPS 수락을 뜻하지 않음.
- 비교: review/parsec_tsu_compare.png; 합본: ../_w9/identity_review.png

## r5 Material pass — W123 충신 / 영원한 갈증의 허기 기준 (2026-11-05)

이 절의 재질 처리가 r4의 전체 면 단색 special 도색을 대체한다. STYLE=material. 형상·파지·mag_ 분리는 변경하지 않았다.

참조: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, /tmp/w325-mat-try.png를 직접 확인했고 main의 generate_surface_w123_gnawing_hunger.py paint_tile() 및 generate_surface_w123_beloved.py Paint.tile()을 읽었다. 색상은 각 rip nx/px/pz albedo 팔레트 샘플을 대조했다.

| 재질 이름 | kind | RGB |
|---|---|---|
| dark | dark | (16, 19, 20) |
| white | paint | (195, 208, 202) |
| polymer | polymer | (34, 42, 37) |
| mint | paint | (164, 186, 173) |
| gunmetal | metal | (60, 72, 64) |
| rubber | rubber | (25, 28, 27) |
| orange | paint | (183, 99, 41) |

- special() 잔여: 원본 좌표 기반 민트 안료, 작은 검정 창, 상부 민트 inset, 포구 중심. 주황 띠는 paint 재질.
- 면 투영: 원본 명암의 고주파 디테일만 재질 바탕에 결합. 새 id_/mag_id_ 형상·north/south 끝면·회전 grip/stock 위아래면은 detail=0. 위장은 예전 합성 noise 대신 실제 rip 좌표의 색상 mask를 사용.
- 출력: 요소 102, body 89+magazine 13; T=20; atlas [1024, 512]; PNG 477,283 bytes.
- 검증: kit build 성공, west/east/top/q/front 렌더 직접 확인, rip compare 검토, adscheck OK, visible coplanar-same-direction 0, JSON/UV/PNG/manifest SHA 확인.
- 한계: 정적 텍스처 재질 표현이며 런타임 PBR/동적 반사 복원은 아님. 실제 client 팩 로드·파지·ADS·장전·10–20개 성능 검증은 master 취합 대기. Gradle/Minecraft/commit 미실행.
- 합본: ../_w9/material_review.png; 재질 구현: ../_w9/materials9.py; 상세 face 할당: ../_w9/material_assignments.json

## r6 Material 2차 패스 (2026-11-05)

리시버·front frame·rail·bumper → barewhite steel, disc·vents → machined steel, junction band·guard·trigger → gunmetal. shroud·배터리 외피의 흰색/민트 도장은 유지.

- 수작업 모티프: 배터리 서비스 도어에 1텍셀 사각 접합선.
- 대비: rubber RGB(18,21,20), polymer (55,59,56), gunmetal (86,90,86), machined steel (112,119,116)로 단계 구분. 갈색 metal/white steel은 원본 계열 색을 별도 유지.
- 위장: source-aligned mask에 저주파 필터·12px 셀을 적용해 2–3색 큰 덩어리로 정돈. 위장 도장에 자동 wear를 꺼 작은 원본 잡티가 되살아나지 않게 함.
- 전체 요소 면적의 paint 비율(가려진 면 포함): 76.3% → 50.8%. 화면 면적/FPS 지표가 아님.
- geometry SHA 기준선과 동일(102요소); atlas [1024, 512] 유지; build·5방향 render·adscheck OK, 동일평면 0. kit.py 미수정.
- 비교: ../_w9/material_r2_review.png. 검사: ../_w9/material_r2_checks.txt. 인게임 QA·Gradle·commit 미실행.
