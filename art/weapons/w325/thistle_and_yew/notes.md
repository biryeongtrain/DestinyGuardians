# Thistle and Yew (common scout, Precision) — base distant_relation

- Identity kept: thumbhole polymer stock with two real holes (rear square, front oval), black cheek pad, light-blue receiver with top rail,
  grey forend with mount cap, exposed barrel + gas tube + gas block, octagonal suppressor with clamp, wide magazine behind the grip (same bullpup-ish layout as the base).
- Elements: body 47 + magazine 2 = 49 (well under the 1000 cap). Atlas 512x512 (T 22).
- Station map: authored in nx rip-image coordinates; trigger ix318 -> z 7.47 (base trigger), bore -> y 10.36 (base bore); rear 0.030, front 0.028 px/img-px, lateral 25 px/m.
  Butt ends z 16.8 (base 17.39), muzzle -8.27 (base -8.26).
- Magazine (mag_body + mag_floor) occupies z 9.8..13.05 like the base moving magazine; shortened 15% along its own axis so the floor sits near the base floor (5.2 vs 5.7); projection undoes it.
- The rip has no optic: the scope is authored on the base W151 box (open tube z 4.21..7.09, y 11.23..12.53, same inner walls) so the kept W148 aim tip lines up; painted by specials (dark metal), not a D2 asset.
- Grip axis ~10 deg rake, 0.6 px further back / 0.4 px higher than the base grip box (trigger 7.39..7.59, y 8.86..9.34, base 8.43..8.6).
- Not verified: in-game first-person/ADS/reload framing (master Vision); scope look is generic.

## Detail + Minecraft style pass (2026-11-05)
- Elements 49 -> 127 (body 122 + mag 5), T 18; atlas 512x512; kit STYLE pixel (palette/flat tol set in design.py).
- Detail: bevels on stock/receiver/forend edges, real thumbhole corner fillets, web plate, strap band, rail teeth, port lips + bolt, charging knob, cap/clamp screws, suppressor ring/cap, front post, scope tube/bell corner chamfers, magazine ribs/window. Long slabs split into stepped segments (DMW style). Flat colour blocks (polymer grey, light-blue receiver, black pads/suppressor, steel fittings). ADS: receiver/rail/forend tops lowered to the base action top; scope bells capped at the base optic roof; adscheck OK.
- Long unrotated slabs are split into ~2-3 px stepped segments (_w3lib.machine); rotated bars/barrels/bevel rods stay long.
- Shared helper _w3lib.py (copy per weapon): bevel/fit/clamp_tops (ADS profile), machine, painted camo blobs.
- Not verified: in-game hip/ADS/reload, colour under game lighting.

## Clean-edge pass (Chattering Bone negative reference)
- Elements 127 -> 132 (127 + 5). Butt pad and rubber were 4-6 deg slabs on top of each other: now two square blocks. Grip insert now uses the grip's exact rotation, inset 0.015 (was a separate near-parallel slab). Removed 9 coplanar overlaps (receiver vs rear slope, rail teeth vs receiver/scope bells, forend cap).
- All: long slabs split into flush equal segments with recessed groove plugs (no alternating offsets); chamfer rods end 0.012 inside the slab ends; tidy() removes every coplanar overlap (lint: 0). Remaining <20 deg rotations are only real angled parts (grip, magazine, canister, butt plate) with their panels on the identical rotation. adscheck OK.

## Identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST (rip nx/px side views)
- 회갈색 폴리머의 두 개 엄지구멍 개머리판
- 검정 뺨받침과 뒤 스트랩
- 푸른 회색 리시버와 은색 볼트/배출구
- 삼각 보강판과 사선 그립 요철
- 노출 검정 총열·가스관
- 검정 소음기와 넓은 후방 탄창

- 원본: `/tmp/w325-rips/thistle_and_yew/source.archive`, 각 무기의 `proj_cache/nx_albedo.png`, `px_albedo.png`와 기존 rip 비교 화면. 에이스/이자나기의 실제 JSON·아틀라스 및 `/tmp/w325-ref-ace-izanagi.png`를 참조.
- 페인트: 삼각 보강선, 은색 볼트 띠, 청회색 패널 음각, 폴리머 사선 요철, 탄창 프레임. 모든 면에서 special()이 명시 RGBA를 반환하며, 상단 1텍셀 하이라이트·하단 1텍셀 음각선·필요한 나사/봉합선을 직접 칠함. 투영 텍스처의 흐림을 사용하지 않음.
- 입체: 소음기 앞 캡을 네 면 프레임으로 분리해 실제 포구 깊이 확보.
- 이전 출력 요소 132개. 최종 수와 아틀라스는 아래 최종 검증 표 및 manifest.json 참조.
- 유지: grip/trigger/기존 조준선·모든 mag_ 원본 위치와 rotation, 원본 archive/캐시. kit.py와 render_model.py는 수정하지 않음.
- 확인: kit build, west/east/top/q/front 오프라인 렌더, 양면 문자 방향, adscheck, 양수 부피/동일 평면 중첩 검사, 탄창 계약 비교.
- 미검증: 실제 Minecraft 1/3인칭·ADS·장전·10–20개 표시. 이 결과는 오프라인 아트 검수이며 원작 완전 일치·인게임 수락·FPS 인증이 아님. 조준기는 기존 base 계약에 맞춘 근사이며 원작 리핑 조준기와 완전히 동일하지 않음.

### Final verified output
- body 130 + magazine 5 = 135; T20; atlas 512×512.
- adscheck OK; axis-aligned coplanar overlap 0; positive-volume and paint sampling OK.
- mag_ geometry unchanged.

## W123 material pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- blue: paint RGB(104, 121, 139), source relief detail=0.85.
- bolt: steel RGB(146, 152, 157), source relief detail=0.75.
- darksteel: metal RGB(48, 52, 55), source relief detail=0.65.
- optic: metal RGB(48, 53, 60), source relief detail=0.
- polymer: polymer RGB(79, 75, 71), source relief detail=0.8.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- rubber: rubber RGB(28, 29, 29), source relief detail=0.22.
- steel: steel RGB(117, 123, 127), source relief detail=0.65.
- strap: cloth RGB(40, 40, 39), source relief detail=0.2.
- special retains only logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_check.json).
- Geometry hash unchanged; 135 elements; atlas [512, 512]; T20; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

## W123 material R2 pass (2026-11-05, supersedes flat identity paint)
- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.
- blue: paint RGB(104, 121, 139), source relief detail=0.85.
- darksteel: metal RGB(82, 89, 94), source relief detail=0.65.
- machined: steel RGB(134, 142, 146), source relief detail=0.65.
- optic: metal RGB(48, 53, 60), source relief detail=0.
- polymer: polymer RGB(79, 75, 71), source relief detail=0.8.
- receiver_metal: metal RGB(84, 92, 96), source relief detail=0.7.
- recess: dark RGB(19, 22, 24), source relief detail=0.
- rubber: rubber RGB(20, 22, 23), source relief detail=0.18.
- steel: steel RGB(117, 123, 127), source relief detail=0.65.
- strap: cloth RGB(40, 40, 39), source relief detail=0.2.
- R2: exposed receiver sideplates, rails, trigger guards and port rims use metal/steel; rubber darkened against polymer. Hand-authored magazine channels, cooling slots, grip ribs and cartridge separators added as sparse texel lines. special retains logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_r2_check.json).
- Geometry hash unchanged; 135 elements; atlas [512, 512]; T20; ADS OK; 0 axis-aligned coplanar overlaps.
- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.

### R2 weapon-specific assignment
- 레일·배출구 테두리·하부 리시버→receiver_metal; 앞 슬릿·삼각판·볼트→machined steel.
- 모티프: 탄창 프레스 채널의 1텍셀 음각/하이라이트와 삼각 보강선.
- 고무/폴리머 기본색 luma 차이: 54.2.
- 원본에 없는 조준기/추가 면에는 detail=0과 wear=False를 모두 명시하여 원본 마모가 잘못 투영되지 않게 함.
