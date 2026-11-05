# Black Tiger-2sr (rare scout, Rapid-Fire, VEIST) — base aishas_embrace

- Identity kept: P90-style white/black VEIST bullpup — black butt, white upper with a real side window showing the orange-cartridge top magazine,
  black lower with real thumbhole + trigger opening, front lip, long square white shroud with three-dot detail, under-barrel claw, sloped window-sight fin + hood.
- Elements: body 23 + magazine 1 = 24. Atlas 512x512 (T 20).
- Station map (nx image coords): anchored on the grip bar (ix275 -> z 10.2 = base grip front strap); rear 0.026 / front 0.035 px per img px. The rip grip is far behind
  the base's relative to the muzzle, so with the hand kept the gun ends z 17.1 at the butt (base 15.78) and -6.1 at the muzzle (base -9.22) — muzzle flash may need the master's check.
  Vertical anchored on the rip reticle (y 12.3 = centre of the base W153 window); bore y 10.5 (base 10.09); trigger z 9.4 (base 8.19).
- Sight: window sight moved 0.9 px forward: reticle plane z 6.8 = base W153 aim tip; window x 7.67..8.33, y 12.06..12.62 (base 7.67..8.33 / 12.11..12.48). No own reticle (W148 tip kept).
- MAGAZINE (needs master decision): the rip magazine is the P90-style top magazine (z 10.0..13.8, y 10.2..11.0, inside the upper body window), so parts.magazine = that slab.
  The base aishas_embrace moving magazine hangs below (z 9.2..12.4, y 5.5..8.4); the reload transform will move the top magazine instead — check it does not cut through the body;
  fallback: rename mag_body -> win_mag (static, empty magazine part).
- Not verified: in-game hip/ADS framing, reload with the top magazine, claw vs left hand.

## Detail + Minecraft style pass (2026-11-05)
- Elements 24 -> 97 (body 95 + mag 2), T 18; atlas 512x512; kit STYLE pixel (palette/flat tol set in design.py).
- MAGAZINE FALLBACK (master decision): the P90 top magazine is now fixed body geometry (win_mag + orange cartridge strip win_cart). parts.magazine = small stub mag_stub + mag_stub_floor in the base aishas_embrace moving-magazine box (z 10.4..12.4, y 5.3..7.2, x-rotation 28). Detail: bevels, butt pad, side rail, VEIST plate (logo projected), front band, ejector, shroud ribs/tip + three-dot vents, claw teeth, grip panel, fillets; upper body sliced in z so its top follows the base stock curve. ADS: window sight moved further forward (SIGHT_DZ -1.35, reticle plane ~z 6.35, base aim tip 6.8) and the sloped fins replaced by short posts; upper body/stock tops clamped to the base profile; adscheck OK. Flat mint/black/orange blocks.
- Long unrotated slabs are split into ~2-3 px stepped segments (_w3lib.machine); rotated bars/barrels/bevel rods stay long.
- Shared helper _w3lib.py (copy per weapon): bevel/fit/clamp_tops (ADS profile), machine, painted camo blobs.
- Not verified: in-game hip/ADS/reload, colour under game lighting.

## Clean-edge pass (Chattering Bone negative reference)
- Elements 97 -> 87 (85 + 2). The upper body was cut into 0.55 px slices with different tops (sawtooth): now three clean steps following the base stock curve (ADS OK). Lower sweep (23 deg slab) -> 4 axis steps. Claw teeth slab removed. Removed 5 coplanar overlaps (side rail, magazine window vs cartridge strip).
- All: long slabs split into flush equal segments with recessed groove plugs (no alternating offsets); chamfer rods end 0.012 inside the slab ends; tidy() removes every coplanar overlap (lint: 0). Remaining <20 deg rotations are only real angled parts (grip, magazine, canister, butt plate) with their panels on the identical rotation. adscheck OK.

## Identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST (rip nx/px side views)
- 연한 민트색 상부와 검정 P90형 하부
- 상부 탄창 창 안 주황 탄약
- 갈색 VEIST 문자와 삼각 로고
- 긴 민트 총열 덮개와 세 검정 점
- 앞쪽 아래 갈고리
- 열린 민트색 조준기

- 원본: `/tmp/w325-rips/black_tiger_2sr/source.archive`, 각 무기의 `proj_cache/nx_albedo.png`, `px_albedo.png`와 기존 rip 비교 화면. 에이스/이자나기의 실제 JSON·아틀라스 및 `/tmp/w325-ref-ace-izanagi.png`를 참조.
- 페인트: 양면 VEIST 글리프/삼각 마크, 주황 탄약 분할, 민트 패널선, 세 점, 검정 폴리머 요철. 모든 면에서 special()이 명시 RGBA를 반환하며, 상단 1텍셀 하이라이트·하단 1텍셀 음각선·필요한 나사/봉합선을 직접 칠함. 투영 텍스처의 흐림을 사용하지 않음.
- 입체: 총구 끝 프레임을 비우고 기존 탄창 창/갈고리 형상 유지; fixed win_mag + mag_stub 계약 유지.
- 이전 출력 요소 87개. 최종 수와 아틀라스는 아래 최종 검증 표 및 manifest.json 참조.
- 유지: grip/trigger/기존 조준선·모든 mag_ 원본 위치와 rotation, 원본 archive/캐시. kit.py와 render_model.py는 수정하지 않음.
- 확인: kit build, west/east/top/q/front 오프라인 렌더, 양면 문자 방향, adscheck, 양수 부피/동일 평면 중첩 검사, 탄창 계약 비교.
- 미검증: 실제 Minecraft 1/3인칭·ADS·장전·10–20개 표시. 이 결과는 오프라인 아트 검수이며 원작 완전 일치·인게임 수락·FPS 인증이 아님. 조준기는 기존 base 계약에 맞춘 근사이며 원작 리핑 조준기와 완전히 동일하지 않음.
- 해상도 선택: T20 시 512²를 초과해 512² 유지가 가능한 T18/19로 조정. 픽셀 글리프/선은 후처리 없이 그대로 보존됨.

### Final verified output
- body 88 + magazine 2 = 90; T19; atlas 512×512.
- adscheck OK; axis-aligned coplanar overlap 0; positive-volume and paint sampling OK.
- mag_ geometry unchanged.

## W123 material pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- brass: gold RGB(175, 103, 43), source relief detail=0.3.
- darksteel: metal RGB(48, 52, 55), source relief detail=0.65.
- lower: polymer RGB(34, 44, 38), source relief detail=0.7.
- magcase: polymer RGB(69, 69, 60), source relief detail=0.4.
- mint: paint RGB(190, 208, 194), source relief detail=0.85.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- rubber: rubber RGB(28, 29, 29), source relief detail=0.22.
- silver: steel RGB(156, 170, 161), source relief detail=0.55.
- special retains only logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_check.json).
- Geometry hash unchanged; 90 elements; atlas [512, 512]; T19; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

## W123 material R2 pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- brass: gold RGB(175, 103, 43), source relief detail=0.3.
- darksteel: metal RGB(82, 89, 94), source relief detail=0.65.
- lower: polymer RGB(48, 60, 51), source relief detail=0.7.
- machined: steel RGB(134, 142, 146), source relief detail=0.65.
- magcase: polymer RGB(69, 69, 60), source relief detail=0.4.
- mint: paint RGB(190, 208, 194), source relief detail=0.85.
- receiver_metal: metal RGB(84, 92, 96), source relief detail=0.7.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- rubber: rubber RGB(20, 22, 23), source relief detail=0.18.
- silver: steel RGB(156, 170, 161), source relief detail=0.55.
- R2: exposed receiver sideplates, rails, trigger guards and port rims use metal/steel; rubber darkened against polymer. Hand-authored magazine channels, cooling slots, grip ribs and cartridge separators added as sparse texel lines. special retains logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_r2_check.json).
- Geometry hash unchanged; 90 elements; atlas [512, 512]; T19; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

### R2 weapon-specific assignment
- 탄창 뒤 프레임·배출구·갈고리·트리거가드·총구 캡→receiver_metal; 레일·앞 밴드·VEIST 판→machined steel.
- 모티프: 주황 탄약의 1텍셀 분할선, 기존 VEIST 및 세 점 유지.
- 고무/폴리머 기본색 luma 차이: 33.9.
- 원본에 없는 조준기/추가 면에는 detail=0과 wear=False를 모두 명시하여 원본 마모가 잘못 투영되지 않게 함.
