# Armillary PSu (rare scout, Precision) — base distant_relation

- Identity kept: bullpup-style polymer lower with real thumbhole, slot window in the upper stock and real trigger-guard opening,
  blue/white worn camo receiver + forend, light rail rib, dark ringed shroud, perforated muzzle brake, splayed bipod, big slab magazine behind the grip, boxy reflex sight.
- Elements: body 39 + magazine 2 = 41. Atlas 512x512 (T 20).
- Station map: nx image coords; trigger ix302 -> z 7.47; rear 0.0317 / front 0.0289 px per img px; vertical anchored on the receiver top (iy58 -> y 11.15 = base action top)
  so the bore sits at y 9.85 (base 10.36, -0.5) — chosen so the base ADS line/aim tip clears the tall receiver. Lateral 21 px/m (receiver half width 0.68).
- Deviation: the sight is moved 2.36 px forward / 0.10 down onto the base W151 sight box (z 4.3..7.1, window y 11.45..12.3, x 7.66..8.34) — in the rip it sits
  over the trigger (inside the ADS camera range); the rip's long light arm from the sight to the receiver is dropped. W148 aim tip kept (no own reticle).
- Magazine z 8.7..13.5 (base 9.72..13.0, the rip mag is much larger), shortened 25% along its axis; floor y 4.8 (base 5.7).
- Bipod legs (2 thin rotated bars, ±7 deg splay) hang to y ~7.0 under the forend z -4..-0.3: may touch the base left-hand pose — check in first person.
- Not verified: in-game ADS window centring, muzzle flash offset from the lower bore, reload hand vs the bigger magazine.

## Detail + Minecraft style pass (2026-11-05)
- Elements 41 -> 112 (body 108 + mag 4), T 18; atlas 512x512; kit STYLE pixel (palette/flat tol set in design.py).
- Detail: bevels, stock panel/vent, slot rim, thumbhole + trigger-guard fillets, grip panel, receiver band, eject port, charging handle, rail teeth, shroud rings, muzzle cap/collar, top-bar clamp, bipod pin, sight frame chamfers, mag floor/panel. Painted 3-colour navy/white/grey camo blobs (no projection noise). ADS: rail/rib/rcv_top lowered to the base top, sight hood -0.06; adscheck OK.
- Long unrotated slabs are split into ~2-3 px stepped segments (_w3lib.machine); rotated bars/barrels/bevel rods stay long.
- Shared helper _w3lib.py (copy per weapon): bevel/fit/clamp_tops (ADS profile), machine, painted camo blobs.
- Not verified: in-game hip/ADS/reload, colour under game lighting.

## Clean-edge pass (Chattering Bone negative reference)
- Elements 112 -> 122 (118 + 4). Butt toe (14.6 deg slab) replaced by 3 flush axis steps. Grip panel uses the grip's exact rotation. Mag floor kept inside the magazine width. Removed 11 coplanar overlaps (stock strip/band, rail teeth, bipod pin, top-bar clamp, muzzle collar). Bipod legs (7 deg splay) kept: real angled part, they only touch the mount.
- All: long slabs split into flush equal segments with recessed groove plugs (no alternating offsets); chamfer rods end 0.012 inside the slab ends; tidy() removes every coplanar overlap (lint: 0). Remaining <20 deg rotations are only real angled parts (grip, magazine, canister, butt plate) with their panels on the identical rotation. adscheck OK.

## Identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST (rip nx/px side views)
- 흰 가장자리와 남색 에나멜 리시버
- 검정 엄지구멍 개머리판
- 흰 수평 띠/열방출 핀
- 흰 천공 소염기
- 흰 펼친 양각대
- 넓은 검정 후방 탄창과 격자 보강

- 원본: `/tmp/w325-rips/armillary_psu/source.archive`, 각 무기의 `proj_cache/nx_albedo.png`, `px_albedo.png`와 기존 rip 비교 화면. 에이스/이자나기의 실제 JSON·아틀라스 및 `/tmp/w325-ref-ace-izanagi.png`를 참조.
- 페인트: 남색 바탕, 흰 프레임/띠, 열방출 핀선, 조준기 조정 다이얼, 탄창 격자. 모든 면에서 special()이 명시 RGBA를 반환하며, 상단 1텍셀 하이라이트·하단 1텍셀 음각선·필요한 나사/봉합선을 직접 칠함. 투영 텍스처의 흐림을 사용하지 않음.
- 입체: 소염기를 두 줄 사각 통풍창과 매입 검정 내총열로 재구성.
- 이전 출력 요소 122개. 최종 수와 아틀라스는 아래 최종 검증 표 및 manifest.json 참조.
- 유지: grip/trigger/기존 조준선·모든 mag_ 원본 위치와 rotation, 원본 archive/캐시. kit.py와 render_model.py는 수정하지 않음.
- 확인: kit build, west/east/top/q/front 오프라인 렌더, 양면 문자 방향, adscheck, 양수 부피/동일 평면 중첩 검사, 탄창 계약 비교.
- 미검증: 실제 Minecraft 1/3인칭·ADS·장전·10–20개 표시. 이 결과는 오프라인 아트 검수이며 원작 완전 일치·인게임 수락·FPS 인증이 아님. 조준기는 기존 base 계약에 맞춘 근사이며 원작 리핑 조준기와 완전히 동일하지 않음.
- 제한: 원본의 둥근 소염기 천공은 두 줄 사각 통풍창으로 재해석함.
- 해상도 선택: T20 시 512²를 초과해 512² 유지가 가능한 T18/19로 조정. 픽셀 글리프/선은 후처리 없이 그대로 보존됨.

### Final verified output
- body 139 + magazine 4 = 143; T18; atlas 512×512.
- adscheck OK; axis-aligned coplanar overlap 0; positive-volume and paint sampling OK.
- mag_ geometry unchanged.

## W123 material pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- darksteel: metal RGB(48, 52, 55), source relief detail=0.65.
- navy: paint RGB(40, 52, 75), source relief detail=1.0.
- polymer: polymer RGB(40, 43, 44), source relief detail=0.7.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- rubber: rubber RGB(28, 29, 29), source relief detail=0.22.
- silver: steel RGB(188, 188, 183), source relief detail=0.6.
- steel: steel RGB(117, 123, 127), source relief detail=0.65.
- white: paint RGB(190, 186, 182), source relief detail=0.7.
- special retains only logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_check.json).
- Geometry hash unchanged; 143 elements; atlas [512, 512]; T18; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

## W123 material R2 pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- darksteel: metal RGB(82, 89, 94), source relief detail=0.65.
- machined: steel RGB(134, 142, 146), source relief detail=0.65.
- navy: paint RGB(40, 52, 75), source relief detail=1.0.
- polymer: polymer RGB(59, 64, 66), source relief detail=0.7.
- receiver_metal: metal RGB(84, 92, 96), source relief detail=0.7.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- rubber: rubber RGB(20, 22, 23), source relief detail=0.18.
- silver: steel RGB(188, 188, 183), source relief detail=0.6.
- steel: steel RGB(117, 123, 127), source relief detail=0.65.
- R2: exposed receiver sideplates, rails, trigger guards and port rims use metal/steel; rubber darkened against polymer. Hand-authored magazine channels, cooling slots, grip ribs and cartridge separators added as sparse texel lines. special retains logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_r2_check.json).
- Geometry hash unchanged; 143 elements; atlas [512, 512]; T18; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

### R2 weapon-specific assignment
- 하부 리시버 측판·spine·레일·트리거가드→receiver_metal; 전방 띠·냉각 리브·핀→machined steel.
- 모티프: 냉각 리브의 1텍셀 암부/밝은 선.
- 고무/폴리머 기본색 luma 차이: 41.2.
- 원본에 없는 조준기/추가 면에는 detail=0과 wear=False를 모두 명시하여 원본 마모가 잘못 투영되지 않게 함.
