# Madrugada SR2 (rare scout, Lightweight, Omolon) — base patron_of_lost_causes

- Identity kept: Omolon compact — black rubber butt, green-camo thumbhole stock with white rim (real thumbhole), tilted battery canister + hinge on the stock top,
  OMOLON receiver with the two black port bores (painted specials) and side lever/disc, rail + rear peep, three-rod open fore-end (dark rods + white barrel, diagonal strut),
  dark front block with white front-sight plate, straight magazine in front of the trigger.
- Elements: body 28 + magazine 2 = 30. Atlas 512x512 (T 20).
- Station map: one uniform 0.036 px per img px (rip is a compact 0.8 m gun), trigger ix288 -> z 6.67 (base trigger), bore iy77 -> y 10.52 (base threaded-muzzle centre);
  butt z 16.7 (base 16.1), front block -5.7 (base muzzle -8.93: the rip has no barrel past the front block). Grip ~z 7.3..8.6 (base 8.3..9.6); trigger y 7.5..8.3 sits ~1.2 below the base trigger (8.9..9.95) because the bore is anchored. Lateral 30 px/m.
- Sight: rear post rebuilt as an open peep ring around the base W153 ADS line (opening x 7.75..8.25, y 12.4..12.95, z 5.9..6.7); kept W148 aim tip (z 6.05..6.15, y 12.66..12.7) sits inside it. No own reticle.
- MAGAZINE (needs master decision): kept in front of the trigger like the rip (z 2.5..5.3, floor y 4.9); the base moving magazine is behind the grip (z 10.6..13.4), so the reload
  hand will grab ~8 px behind it. Moving it behind the grip would erase the Omolon layout; if the reload looks wrong, the fallback is a static magazine (rename mag_ -> body).
- Not verified: in-game hip/ADS (peep framing), reload, muzzle flash at the shorter front (-5.7).

## Detail + Minecraft style pass (2026-11-05)
- Elements 30 -> 84 (body 82 + mag 2), T 18; atlas 512x512; kit STYLE pixel (palette/flat tol set in design.py).
- MAGAZINE FALLBACK (master decision): the Omolon magazine in front of the trigger is fixed body geometry (fixed_mag*). parts.magazine = small stub mag_stub + mag_stub_floor in the base patron magazine box (z 11.2..13.2, y 5.7..7.7, x-rotation -8). Detail: bevels, butt slot rim, stock rim/pad, hinge knob, grip ribs, receiver frames, port rings, canister band, rod clamp, barrel collar/ring, front plate/vents/sight ears. Painted olive/dark-olive/bone camo blobs, bone frames, black rubber, red OMOLON band, port bores as flat black discs. ADS: canister lowered 0.11 (was +0.19 over the base); adscheck OK.
- Long unrotated slabs are split into ~2-3 px stepped segments (_w3lib.machine); rotated bars/barrels/bevel rods stay long.
- Shared helper _w3lib.py (copy per weapon): bevel/fit/clamp_tops (ADS profile), machine, painted camo blobs.
- Not verified: in-game hip/ADS/reload, colour under game lighting.

## Clean-edge pass (Chattering Bone negative reference)
- Elements 84 -> 92 (90 + 2). Stock pad now shares the lower stock rotation (was a slab at a different angle crossing it); canister band and grip ribs share their parent's rotation. Removed 21 coplanar overlaps (receiver frames, stock rim/caps, hinge/strut, peep base, barrel collar).
- All: long slabs split into flush equal segments with recessed groove plugs (no alternating offsets); chamfer rods end 0.012 inside the slab ends; tidy() removes every coplanar overlap (lint: 0). Remaining <20 deg rotations are only real angled parts (grip, magazine, canister, butt plate) with their panels on the identical rotation. adscheck OK.

## Identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST (rip nx/px side views)
- 짙고 밝은 올리브 위장 개머리판
- 뼈색 구조 프레임과 엄지구멍
- 붉은 OMOLON 문자
- 대소 두 원형 측면 포트
- 붉은 띠가 둘린 상부 배터리
- 흰 총열과 검정 위아래 막대의 열린 전방부
- 앞 고정 탄창

- 원본: `/tmp/w325-rips/madrugada_sr2/source.archive`, 각 무기의 `proj_cache/nx_albedo.png`, `px_albedo.png`와 기존 rip 비교 화면. 에이스/이자나기의 실제 JSON·아틀라스 및 `/tmp/w325-ref-ace-izanagi.png`를 참조.
- 페인트: 올리브 3색 위장, 양면 붉은 OMOLON 글리프, 흰 포트 테두리, 전방 통풍선/그립 리브. 모든 면에서 special()이 명시 RGBA를 반환하며, 상단 1텍셀 하이라이트·하단 1텍셀 음각선·필요한 나사/봉합선을 직접 칠함. 투영 텍스처의 흐림을 사용하지 않음.
- 입체: 두 측면 포트를 관통 구멍과 입체 프레임으로 추가; 원형을 사각 구멍+픽셀 원형 테두리로 해석; fixed_mag + mag_stub 유지.
- 이전 출력 요소 92개. 최종 수와 아틀라스는 아래 최종 검증 표 및 manifest.json 참조.
- 유지: grip/trigger/기존 조준선·모든 mag_ 원본 위치와 rotation, 원본 archive/캐시. kit.py와 render_model.py는 수정하지 않음.
- 확인: kit build, west/east/top/q/front 오프라인 렌더, 양면 문자 방향, adscheck, 양수 부피/동일 평면 중첩 검사, 탄창 계약 비교.
- 미검증: 실제 Minecraft 1/3인칭·ADS·장전·10–20개 표시. 이 결과는 오프라인 아트 검수이며 원작 완전 일치·인게임 수락·FPS 인증이 아님. 조준기는 기존 base 계약에 맞춘 근사이며 원작 리핑 조준기와 완전히 동일하지 않음.
- 해상도 선택: 작은 OMOLON 글자와 근접 포트 프레임을 보존하려 T24 / 1024×512 사용. 512² T17도 적재 가능했지만 문자가 덜 선명했음.

### Final verified output
- body 122 + magazine 2 = 124; T24; atlas 1024×512.
- adscheck OK; axis-aligned coplanar overlap 0; positive-volume and paint sampling OK.
- mag_ geometry unchanged.

## W123 material pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- barrelsteel: steel RGB(185, 182, 172), source relief detail=0.6.
- battery: metal RGB(137, 124, 90), source relief detail=0.65.
- bone: paint RGB(190, 183, 171), source relief detail=0.75.
- darksteel: metal RGB(48, 52, 55), source relief detail=0.65.
- olive: paint RGB(62, 77, 40), source relief detail=1.0.
- polymer: polymer RGB(40, 42, 36), source relief detail=0.65.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- red: paint RGB(144, 45, 36), source relief detail=0.25.
- rubber: rubber RGB(28, 29, 29), source relief detail=0.22.
- special retains only logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_check.json).
- Geometry hash unchanged; 124 elements; atlas [1024, 512]; T24; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

## W123 material R2 pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- barrelsteel: steel RGB(185, 182, 172), source relief detail=0.6.
- battery: metal RGB(137, 124, 90), source relief detail=0.65.
- bone: paint RGB(190, 183, 171), source relief detail=0.75.
- darksteel: metal RGB(82, 89, 94), source relief detail=0.65.
- machined: steel RGB(134, 142, 146), source relief detail=0.65.
- olive: paint RGB(62, 77, 40), source relief detail=1.0.
- polymer: polymer RGB(58, 62, 51), source relief detail=0.65.
- receiver_metal: metal RGB(84, 92, 96), source relief detail=0.7.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- red: paint RGB(144, 45, 36), source relief detail=0.25.
- rubber: rubber RGB(20, 22, 23), source relief detail=0.18.
- R2: exposed receiver sideplates, rails, trigger guards and port rims use metal/steel; rubber darkened against polymer. Hand-authored magazine channels, cooling slots, grip ribs and cartridge separators added as sparse texel lines. special retains logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_r2_check.json).
- Geometry hash unchanged; 124 elements; atlas [1024, 512]; T24; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

### R2 weapon-specific assignment
- 하부 리시버·포트 링·고정 탄창·힌지·트리거가드·앞 판·리시버 프레임·레일→receiver_metal; 포트 깊이 프레임·총열 칼라→machined steel.
- 모티프: 그립 수평 리브 1텍셀 음각/밝은 선, OMOLON 및 올리브 위장 유지.
- 고무/폴리머 기본색 luma 차이: 38.0.
- 원본에 없는 조준기/추가 면에는 detail=0과 wear=False를 모두 명시하여 원본 마모가 잘못 투영되지 않게 함.
