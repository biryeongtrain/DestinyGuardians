# Damietta-LR2 (W325, rare sniper, Aggressive) — base bite_of_the_fox

- Identity kept: pale-blue/teal Arctic camo over brown furniture, long slim barrel with banded brake, dark top cover over
  the truss handguard, bipod (folded front leg under the barrel + splayed feet + rear leg with cap), boxy scope with
  big front ring and angled eyepiece hood, bolt knob right, thumbhole stock with side pads and camo butt, angled mag floor.
- Elements (r2): body+magazine 84+4 (r1 total 43).
- Fit: rip at 18.75 px/m shifted +0.3 px so the thumbhole grip post ((8.05,8.85)->(8.85,6.85)) sits on the base grip;
  muzzle z -15.25 (base -15.5), butt pad to 13.5. Receiver top 10.75, scope 10.95..12.22 (base top 11.96, hidden in ADS).
  Magazine kept at the rip place z 4.25..6.4 / y 6.72..8.9 around the base moving magazine (z 4.12..5.79, y 7.63..8.89);
  it is taller than the base mag (rip identity), reload offset/animation stays the base's.
- Unverified: in-game hip/3P framing, reload contact with the deeper magazine, bipod legs vs hand/arm in first person.
- r2 detail + ADS + W30 pixel style: kit STYLE 'pixel' (palette quantise + bevel lines) with flat material colours painted in special(); DMW-style split slabs (w9.chamfer_box = core + inset 1-step top/bottom plates, optional segments). adscheck OK: scope moved forward into the base scope box z 0.6..6.3 (SCOPE_Z + SCOPE_DY), top 11.9; mount/receiver tail <= 10.2; top cover starts behind z -1.6. Open truss handguard (frame bars + diagonal truss), banded brake, folded bipod leg with holes, bipod feet, stock pad lips. Paint: ice/teal blob camo over brown furniture.
- r3 Chattering-Bone cleanup (84+4): stock lower arm = 3 flush steps, magazine floor = 2 axis-aligned blocks (were rotated slabs), bipod feet axis-aligned, brake bands raised proud, spine moved off the scope mount, guard trimmed. w9 lint: 0 visible coplanar same-direction overlaps (w9.tidy recesses any left by 0.03), no near-parallel overlapping rotated slabs except real angled grip/trigger/stock joints.

## r4 Identity pass — Ace / Izanagi 기준 (2026-11-05)

### IDENTITY LIST

- 얼음색·청록 위장과 갈색 기계부
- 가느다란 긴 총열과 띠가 있는 제퇴기
- 접힌 전방 양각대와 펼친 후방 발
- 깊이 있는 삼각 트러스 핸드가드
- 검은 상부 덮개와 청색 스코프 렌즈
- 갈색 thumbhole 개머리판의 밝은 패드

입체: 제퇴기 측면 포트 web, 탄창 리브, 스코프 dial ridges. 페인트: 얼음 위장·패드 inset·슬롯·렌즈 반사.

- 요소: 88 → 114 (body 102 + magazine 12). T=20; atlas=[1024, 512]; PNG 21,970 bytes.
- 모든 노출 면을 special()로 직접 도색. 상단 1텍셀 밝은 선/하단 어두운 seam, 근거 있는 패널·고유 표식. Projection fallback 없음.
- 512 atlas는 T20에서 overflow여서 근접 면의 작은 선을 보존하려고 가로1024로 확대; kit가 사용 높이를 자동 잘라냄.
- 검증: kit build 성공, west/east/top/q/front 5방향 렌더 생성·검토, 원본 nx_albedo와 compare PNG 직접 비교, adscheck OK, visible coplanar same-direction 0, 양의 부피·유일 이름·1000 cap 확인.
- 에이스/이자나기의 원본 JSON·면 UV 및 기준 이미지를 실제 읽고, 긴 덩어리 위 선명한 표면 디테일 원칙을 적용. 개별 원작의 문양을 다른 무기에 복사하지 않음.
- 잔여: 기존 base 범위로 앞당긴 스코프와 더 깊은 탄창을 유지했다. 양각대와 팔 간섭·장전 손 접촉 미검증. 오프라인 렌더이며 실제 client, 팩 로드, 10–20개 FPS 수락을 뜻하지 않음.
- 비교: review/damietta_lr2_compare.png; 합본: ../_w9/identity_review.png

## r5 Material pass — W123 충신 / 영원한 갈증의 허기 기준 (2026-11-05)

이 절의 재질 처리가 r4의 전체 면 단색 special 도색을 대체한다. STYLE=material. 형상·파지·mag_ 분리는 변경하지 않았다.

참조: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, /tmp/w325-mat-try.png를 직접 확인했고 main의 generate_surface_w123_gnawing_hunger.py paint_tile() 및 generate_surface_w123_beloved.py Paint.tile()을 읽었다. 색상은 각 rip nx/px/pz albedo 팔레트 샘플을 대조했다.

| 재질 이름 | kind | RGB |
|---|---|---|
| ice | paint | (171, 201, 217) |
| brownmetal | metal | (89, 82, 74) |
| dark | dark | (16, 19, 20) |
| gunmetal | steel | (58, 57, 54) |
| steel | steel | (179, 187, 187) |
| brown | polymer | (89, 80, 71) |
| rubber | rubber | (25, 28, 27) |

- special() 잔여: 원본 좌표 기반 청록 위장 안료, 청색 렌즈·반사, 포구 중심.
- 면 투영: 원본 명암의 고주파 디테일만 재질 바탕에 결합. 새 id_/mag_id_ 형상·north/south 끝면·회전 grip/stock 위아래면은 detail=0. 위장은 예전 합성 noise 대신 실제 rip 좌표의 색상 mask를 사용.
- 출력: 요소 114, body 102+magazine 12; T=20; atlas [1024, 512]; PNG 240,330 bytes.
- 검증: kit build 성공, west/east/top/q/front 렌더 직접 확인, rip compare 검토, adscheck OK, visible coplanar-same-direction 0, JSON/UV/PNG/manifest SHA 확인.
- 한계: 정적 텍스처 재질 표현이며 런타임 PBR/동적 반사 복원은 아님. 실제 client 팩 로드·파지·ADS·장전·10–20개 성능 검증은 master 취합 대기. Gradle/Minecraft/commit 미실행.
- 합본: ../_w9/material_review.png; 재질 구현: ../_w9/materials9.py; 상세 face 할당: ../_w9/material_assignments.json

## r6 Material 2차 패스 (2026-11-05)

긴 총열 → 청회색 barrelsteel, 트러스·측판·트리거가드 → machined steel, 탄창 → brownmetal. ice paint는 외피 패널·optic·stock pad에 유지.

- 수작업 모티프: 스코프 turret 상단의 1텍셀 간격 눈금.
- 대비: rubber RGB(18,21,20), polymer (55,59,56), gunmetal (86,90,86), machined steel (112,119,116)로 단계 구분. 갈색 metal/white steel은 원본 계열 색을 별도 유지.
- 위장: source-aligned mask에 저주파 필터·12px 셀을 적용해 2–3색 큰 덩어리로 정돈. 위장 도장에 자동 wear를 꺼 작은 원본 잡티가 되살아나지 않게 함.
- 전체 요소 면적의 paint 비율(가려진 면 포함): 44.1% → 27.8%. 화면 면적/FPS 지표가 아님.
- geometry SHA 기준선과 동일(114요소); atlas [1024, 512] 유지; build·5방향 render·adscheck OK, 동일평면 0. kit.py 미수정.
- 비교: ../_w9/material_r2_review.png. 검사: ../_w9/material_r2_checks.txt. 인게임 QA·Gradle·commit 미실행.
