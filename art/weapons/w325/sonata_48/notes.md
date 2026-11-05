# Sonata-48 (rare scout, Precision, SUROS) — base distant_relation

- Identity kept: short SUROS bullpup — angled butt plate, rear carry loop with real slot, grey upper / red lower body with SUROS logo, dark slotted rear-sight hump,
  forward pistol grip with flared heel, ribbed dark handguard, perforated white muzzle sleeve + spike, vertical magazine behind the grip.
- Elements: body 24 + magazine 3 = 27 (big clean volumes; the logo/slots/vents are UV). Atlas 512x512 (T 22).
- Station map: nx image coords; trigger ix302 -> z 7.47 (trigger y 8.6 = base); rear 0.031, front 0.033 px/img-px (front 6% stretched so the spike ends z -7.25; base muzzle -8.26);
  vertical 0.031 anchored on the receiver top (iy43 -> y 11.15) so the base ADS line clears it; bore y 9.93 (base 10.36). Lateral 20 px/m.
- Magazine moved 1.0 px forward and shortened 15% from its top: z 10.6..13.9 (base 9.72..13.0), floor y 5.6 (base 5.7). The rip mag sits ~1.9 px further back than the base.
- Rear peep sight: rebuilt as an open ring around the base W151 window (x 7.72..8.28, y up to 12.25, z 6.9..7.8), 0.25 taller than the rip post so the window clears; kept W148 aim tip (z 4.3) is the reticle.
  The ring is at the trigger station (z 6.9..7.8) — slightly behind the base scope rear (7.09/7.5): check the ADS camera does not clip it.
- Grip bottom y 5.7 (base grip loop bottom 6.17): longer grip than the base.
- Not verified: in-game ADS/peep framing, reload hand vs the moved magazine, muzzle flash vs the shorter muzzle (-7.25).

## Detail + Minecraft style pass (2026-11-05)
- Elements 27 -> 84 (body 79 + mag 5), T 20; atlas 512x512; kit STYLE pixel (palette/flat tol set in design.py).
- Detail: bevels, stock panel, carry-handle fillets, red band + logo slot, sight-house vents, peep ring corner chamfers, grip panel, trigger guard bar, handguard ribs, front vent, muzzle collar/tip, mag rib/lip. Flat mint/red/dark blocks; SUROS lettering repainted as flat mint strokes. ADS: peep ring moved 0.84 forward into the base scope zone (z 6.06..6.97, still an open ring named sight_ring_*), body tops lowered; adscheck OK.
- Long unrotated slabs are split into ~2-3 px stepped segments (_w3lib.machine); rotated bars/barrels/bevel rods stay long.
- Shared helper _w3lib.py (copy per weapon): bevel/fit/clamp_tops (ADS profile), machine, painted camo blobs.
- Not verified: in-game hip/ADS/reload, colour under game lighting.

## Clean-edge pass (Chattering Bone negative reference)
- Elements 84 -> 101 (96 + 5). Butt pad now shares the butt plate rotation (was 18.4 vs 18.0 deg -> crossing edges). Grip panel on the grip rotation. Red band no longer z-fights the body segments (12 overlaps), muzzle collar end pulled in.
- All: long slabs split into flush equal segments with recessed groove plugs (no alternating offsets); chamfer rods end 0.012 inside the slab ends; tidy() removes every coplanar overlap (lint: 0). Remaining <20 deg rotations are only real angled parts (grip, magazine, canister, butt plate) with their panels on the identical rotation. adscheck OK.

## Identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST (rip nx/px side views)
- 민트색 상부와 진홍색 중앙 띠
- 밝은 SUROS 문자
- 검정 조준기 하우징과 사선 은색 통풍무늬
- 후방 운반손잡이의 실제 구멍
- 흰 천공 소염기와 가는 연장 총구
- 검정 후방 탄창과 세 리브 핸드가드

- 원본: `/tmp/w325-rips/sonata_48/source.archive`, 각 무기의 `proj_cache/nx_albedo.png`, `px_albedo.png`와 기존 rip 비교 화면. 에이스/이자나기의 실제 JSON·아틀라스 및 `/tmp/w325-ref-ace-izanagi.png`를 참조.
- 페인트: 양면 SUROS 글리프, 민트 패널선, 진홍 띠, 조준기 은색 사선, 탄창/그립 요철. 모든 면에서 special()이 명시 RGBA를 반환하며, 상단 1텍셀 하이라이트·하단 1텍셀 음각선·필요한 나사/봉합선을 직접 칠함. 투영 텍스처의 흐림을 사용하지 않음.
- 입체: 소염기 실제 두 줄 통풍창, 검정 내총열, 앞쪽 개방 프레임.
- 이전 출력 요소 101개. 최종 수와 아틀라스는 아래 최종 검증 표 및 manifest.json 참조.
- 유지: grip/trigger/기존 조준선·모든 mag_ 원본 위치와 rotation, 원본 archive/캐시. kit.py와 render_model.py는 수정하지 않음.
- 확인: kit build, west/east/top/q/front 오프라인 렌더, 양면 문자 방향, adscheck, 양수 부피/동일 평면 중첩 검사, 탄창 계약 비교.
- 미검증: 실제 Minecraft 1/3인칭·ADS·장전·10–20개 표시. 이 결과는 오프라인 아트 검수이며 원작 완전 일치·인게임 수락·FPS 인증이 아님. 조준기는 기존 base 계약에 맞춘 근사이며 원작 리핑 조준기와 완전히 동일하지 않음.
- 제한: 원본의 둥근 소염기 천공은 두 줄 사각 통풍창으로 재해석함.

- 탄창 립의 기존 동일 평면 겹침 한 곳만 0.012px 안쪽으로 정리함(mag_lip.to[1]). 탄창 배치/장전 pivot은 유지.

### Final verified output
- body 119 + magazine 5 = 124; T20; atlas 512×512.
- adscheck OK; axis-aligned coplanar overlap 0; positive-volume and paint sampling OK.
- mag_lip top face only: -0.012px; reload anchor unchanged.

## W123 material pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- darksteel: metal RGB(48, 52, 55), source relief detail=0.65.
- mint: paint RGB(157, 178, 171), source relief detail=0.8.
- polymer: polymer RGB(46, 46, 47), source relief detail=0.65.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- red: paint RGB(133, 37, 40), source relief detail=0.85.
- rubber: rubber RGB(28, 29, 29), source relief detail=0.22.
- silver: steel RGB(192, 198, 199), source relief detail=0.55.
- special retains only logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_check.json).
- Geometry hash unchanged; 124 elements; atlas [512, 512]; T20; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

## W123 material R2 pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- darksteel: metal RGB(82, 89, 94), source relief detail=0.65.
- machined: steel RGB(134, 142, 146), source relief detail=0.65.
- mint: paint RGB(157, 178, 171), source relief detail=0.8.
- polymer: polymer RGB(59, 62, 64), source relief detail=0.65.
- receiver_metal: metal RGB(84, 92, 96), source relief detail=0.7.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- red: paint RGB(133, 37, 40), source relief detail=0.85.
- rubber: rubber RGB(20, 22, 23), source relief detail=0.18.
- silver: steel RGB(192, 198, 199), source relief detail=0.55.
- R2: exposed receiver sideplates, rails, trigger guards and port rims use metal/steel; rubber darkened against polymer. Hand-authored magazine channels, cooling slots, grip ribs and cartridge separators added as sparse texel lines. special retains logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_r2_check.json).
- Geometry hash unchanged; 124 elements; atlas [512, 512]; T20; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

### R2 weapon-specific assignment
- 중앙/후방 베이스·손잡이·하부 블록·트리거가드→receiver_metal; 조준기 링·소염기 칼라/팁→machined steel; 민트 외피·진홍 띠는 도장 유지.
- 모티프: 고무 핸드가드의 가는 리브, SUROS와 사선 조준기 마크 유지.
- 고무/폴리머 기본색 luma 차이: 39.8.
- 원본에 없는 조준기/추가 면에는 detail=0과 wear=False를 모두 명시하여 원본 마모가 잘못 투영되지 않게 함.
