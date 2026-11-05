# Inverness-SR2 (uncommon scout, Precision) — base distant_relation

- Identity kept: purple/grey worn polymer bullpup — skeleton butt with diagonal strut and real slot, real thumbhole and real trigger-guard opening,
  raised front block, sloped forend underside, thin barrel neck + thick barrel sleeve, forked under-barrel bracket with ring, slab magazine behind the grip, boxy reflex sight.
- Elements: body 24 + magazine 1 = 25 (large volumes; panel lines/cable/vents are UV). Atlas 512x512 (T 22).
- Station map: nx image coords; trigger ix310 -> z 7.47; rear 0.0313 / front 0.0321 px per img px (butt 16.9, muzzle -8.26 = base); vertical 0.0317 anchored on the receiver top
  (iy52 -> 11.15) giving bore y 10.33 (base 10.36), trigger y 8.0..8.7 (base 8.43..8.6). Lateral 20 px/m about the rip centreline.
- Deviation: reflex sight moved 2.91 px forward / 0.20 down onto the base W151 box (z 4.3..6.6, window x 7.68..8.32, y 11.42..12.3); kept W148 aim tip is the reticle.
- Magazine z 8.8..12.3 (base 9.72..13.0), shortened 25% along its axis and raised 0.5: floor y 4.9 at the rotated corner (base 5.7) — the rip magazine is much longer than the base.
- Not verified: in-game ADS window centring, reload hand vs magazine, first-person view of the under-barrel bracket.

## Detail + Minecraft style pass (2026-11-05)
- Elements 25 -> 87 (body 84 + mag 3), T 18; atlas 512x512; kit STYLE pixel (palette/flat tol set in design.py).
- Detail: bevels, butt pad, stock ribs, body panel/rail, thumbhole + guard fillets, grip panel, receiver vents/port, front rail, split front block (rear part held to the base top), neck collar, barrel collar/tip, bracket ring, sight frame chamfers, mag floor/panel. Flat purple/grey blocks with a grey lower band and dark vents. ADS: front block rear part and receiver tops lowered; adscheck OK.
- Long unrotated slabs are split into ~2-3 px stepped segments (_w3lib.machine); rotated bars/barrels/bevel rods stay long.
- Shared helper _w3lib.py (copy per weapon): bevel/fit/clamp_tops (ADS profile), machine, painted camo blobs.
- Not verified: in-game hip/ADS/reload, colour under game lighting.

## Clean-edge pass (Chattering Bone negative reference)
- Elements 87 -> 101 (98 + 3). Stock strut (81 deg) -> 3 axis steps, sloped forend underside (98 deg) -> 4 axis steps; grip panel on the grip rotation. Removed 8 coplanar overlaps (sight mount vs receiver cap, bracket rings, collars).
- All: long slabs split into flush equal segments with recessed groove plugs (no alternating offsets); chamfer rods end 0.012 inside the slab ends; tidy() removes every coplanar overlap (lint: 0). Remaining <20 deg rotations are only real angled parts (grip, magazine, canister, butt plate) with their panels on the identical rotation. adscheck OK.

## Identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST (rip nx/px side views)
- 회보라색 외장과 회색 하부
- 외장 옆을 따라 올라가는 검정 케이블
- 낮은 사각 조준기
- 뒤 개머리판의 가로 빈 공간
- 옆면 검정 배출구와 세 통풍구
- 짙은 회녹색 후방 탄창

- 원본: `/tmp/w325-rips/inverness_sr2/source.archive`, 각 무기의 `proj_cache/nx_albedo.png`, `px_albedo.png`와 기존 rip 비교 화면. 에이스/이자나기의 실제 JSON·아틀라스 및 `/tmp/w325-ref-ace-izanagi.png`를 참조.
- 페인트: 보라색 패널 테두리, 은색 각인, 통풍 핀, 회녹색 탄창 무늬. 모든 면에서 special()이 명시 RGBA를 반환하며, 상단 1텍셀 하이라이트·하단 1텍셀 음각선·필요한 나사/봉합선을 직접 칠함. 투영 텍스처의 흐림을 사용하지 않음.
- 입체: 양쪽 외장 케이블을 정확히 맞닿는 짧은 사각 구간으로 추가.
- 이전 출력 요소 101개. 최종 수와 아틀라스는 아래 최종 검증 표 및 manifest.json 참조.
- 유지: grip/trigger/기존 조준선·모든 mag_ 원본 위치와 rotation, 원본 archive/캐시. kit.py와 render_model.py는 수정하지 않음.
- 확인: kit build, west/east/top/q/front 오프라인 렌더, 양면 문자 방향, adscheck, 양수 부피/동일 평면 중첩 검사, 탄창 계약 비교.
- 미검증: 실제 Minecraft 1/3인칭·ADS·장전·10–20개 표시. 이 결과는 오프라인 아트 검수이며 원작 완전 일치·인게임 수락·FPS 인증이 아님. 조준기는 기존 base 계약에 맞춘 근사이며 원작 리핑 조준기와 완전히 동일하지 않음.
- 해상도 선택: T20 시 512²를 초과해 512² 유지가 가능한 T18/19로 조정. 픽셀 글리프/선은 후처리 없이 그대로 보존됨.

### Final verified output
- body 114 + magazine 3 = 117; T19; atlas 512×512.
- adscheck OK; axis-aligned coplanar overlap 0; positive-volume and paint sampling OK.
- mag_ geometry unchanged.

## W123 material pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- darksteel: metal RGB(48, 52, 55), source relief detail=0.65.
- magpaint: paint RGB(49, 58, 53), source relief detail=0.8.
- polymer: polymer RGB(50, 51, 50), source relief detail=0.55.
- purple: paint RGB(81, 69, 88), source relief detail=0.85.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- rubber: rubber RGB(28, 29, 29), source relief detail=0.22.
- steel: steel RGB(91, 94, 97), source relief detail=0.65.
- special retains only logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_check.json).
- Geometry hash unchanged; 117 elements; atlas [512, 512]; T19; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

## W123 material R2 pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- darksteel: metal RGB(82, 89, 94), source relief detail=0.65.
- machined: steel RGB(134, 142, 146), source relief detail=0.65.
- magpaint: paint RGB(49, 58, 53), source relief detail=0.8.
- polymer: polymer RGB(59, 63, 61), source relief detail=0.55.
- purple: paint RGB(81, 69, 88), source relief detail=0.85.
- receiver_metal: metal RGB(84, 92, 96), source relief detail=0.7.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- rubber: rubber RGB(20, 22, 23), source relief detail=0.18.
- steel: steel RGB(91, 94, 97), source relief detail=0.65.
- R2: exposed receiver sideplates, rails, trigger guards and port rims use metal/steel; rubber darkened against polymer. Hand-authored magazine channels, cooling slots, grip ribs and cartridge separators added as sparse texel lines. special retains logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_r2_check.json).
- Geometry hash unchanged; 117 elements; atlas [512, 512]; T19; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

### R2 weapon-specific assignment
- 리시버 측판·하부·앞 블록 접합부·마운트·트리거가드→receiver_metal; 칼라·개머리판 리브·앞 레일→machined steel.
- 모티프: 2행×3열 냉각 슬롯과 탄창 삼각 마크.
- 고무/폴리머 기본색 luma 차이: 40.1.
- 원본에 없는 조준기/추가 면에는 detail=0과 wear=False를 모두 명시하여 원본 마모가 잘못 투영되지 않게 함.
