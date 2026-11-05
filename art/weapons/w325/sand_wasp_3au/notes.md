# Sand Wasp-3au (W325, rare, VEIST auto rifle Rapid-Fire) over steelfeather_repeater
- Identity kept: long white suppressor, dark C-ring front grip with forward hook, dark raked pistol grip, camo receiver with the dark raised side plates, horizontal VEIST magazine in the side window (brass rounds + red/white front), tall holo arch, camo slab stock with the dark top rail and notched butt pad.
- Elements: body 54 + magazine 2 = 56 (cubes only, some rotated); atlas 512x512, 16 texels/px, kit projection only (no hand-painted specials).
- Rip map: uniform 28 px/m (26 across), rip grip top -> base grip (z 7.6), holo reticle centre -> eye line y 12.95; suppressor forward of the ring grip stretched to 46 px/m so the muzzle reaches z -8.3 (base -9.66, 1.4 px shorter). Butt 16.55 (base 16.59).
- Sight: holo arch window y 12.62..13.18 at z 3.95..5.15 stays open; no glass element; W151 aim tip (z -4.93, y 12.88..13.04) is kept (no_overlay false). Everything behind z 5.2 at the centre stays <= 12.85 (stock top lowered from the rip's 13.2 rise, butt spike split into two side ears).
- Magazine deviation: the rip magazine is the horizontal VEIST mag inside the receiver (z 4.72..11.3, y 9.92..10.7), not a box under the receiver like the base moving leaf (z 1.98..4.67, y 6.1..9.7). parts.magazine = that horizontal mag, so in the base reload it will translate/rotate out of the side window, away from where the base hand grabs; the window stays open while it is out. The rip front grip occupies the base magazine box instead.
- Pistol grip ~0.3 px forward and 1 px lower at the heel than the base grip; front grip at z 1.3..2.9 (base forearm z -3.9..1.9).
- Not verified: in-game first-person/ADS/reload, actual hand overlap, muzzle-flash origin vs the shorter suppressor.

## W325 detail + pixel-style pass (2026-11-05)
- Elements 56 -> 130 (body 127 + magazine 3: mag_body, mag_front, mag_spine). Geometry shared with Yellowjacket in _m2tools/veist.py.
- Dead Man Walking style: receiver/stock/lower/window lips split into machined blocks with chamfered edges and dark groove joints; octagonal two-piece suppressor with band; rail teeth, plate vents/bolts, cam disc, trigger tip, hook tip, grip front strap.
- Pixel style (kit default): PALETTE 16, FLAT_TOL 34; flat paint (special) for suppressor, dark polymer tops/caps, and the magazine as colour blocks (brass rounds with ribs, white front with red chevrons).
- ADS (in-game blocked): holo is now an open 'sight_*' frame; hood rails lowered to 12.58, stock top to 12.5, butt pad to 12.45, butt spike removed. adscheck: only sight_* elements above base (z 3.67..4.67, frame around the aim line); nothing else.
- Not verified in game after the fix.

## Cleanup pass (Chattering Bone negative ref, 2026-11-05)
- See final report; zfight.py reports 0 coplanar overlaps; elements now {'body': 142, 'magazine': 3}.

## W325 identity pass — Ace/Izanagi 기준 (2026-11-05)
### IDENTITY LIST
- 아이보리색 긴 소음기와 금속 띠
- 올리브·연회색 3색 위장 몸체와 개머리판
- 어두운 측면 판과 올리브색 VEIST 픽셀 로고
- 황동색 수평 탄창·백색 전면·붉은 사선
- 실제 빈 공간을 가진 C형 앞손잡이와 긴 홀로 조준기

- Source: existing rip nx_albedo side + original rip quarter renders; main Ace/Izanagi native JSON and enlarged atlas comparison.
- Every visible face now uses exact hand-authored special() paint: flat materials, crisp 1-texel bright upper edges/dark lower seams, panel engraving, small bolt heads, original material blocks. No projection fallback remains. T=20, 512 atlas target.
- Large camo regions are deliberately hand-drawn 3-colour hard-edged blocks, not per-pixel photo grime. Original scratched wear is omitted.

### Final identity-pass validation
- Elements 145 -> 145 (body 142 + magazine 3); T 20; actual atlas 1024x512; PNG 18,835 bytes.
- kit build and west/east/top/q/front renders succeeded; source side/quarter comparison reviewed full-size.
- kit adscheck still reports only the open sight frame above the base profile; classified helper confirms 0 non-sight offenders. Sampled centre eye ray (x=8, y=YE) has 0 solid obstructions (intentional reticle excluded). Native ADS is not yet verified.
- zfight.py: 0 coplanar overlaps (unrotated/identically rotated scope); UV coordinates valid, unique names, magazine split preserved.
- 512-wide atlas overflowed at T20; 1024 width is retained for close first-person receiver/optic lettering and 1-texel seams. kit crops unused rows to 512, avoiding a full 1024-square image.
- Existing geometry retained; painted VEIST pixel glyphs, 3-colour hard-edge camo, two-row magazine perforations, original coloured front chevrons, polymer grip grooves/stipple, stock contour seams.
- Existing horizontal-magazine/base-hand mismatch remains; this pass does not alter the reload contract or animation.
- Remaining: in-game 1P/3P, hand contact, ADS, reload and 10-20-weapon display QA are master-owned and not run here. No Gradle/Minecraft or commit was performed.

## W325 MATERIAL pass (2026-11-05) — supersedes flat identity-paint appearance
- STYLE=material; full-face special fills removed from the active pipeline. Geometry and magazine split unchanged.
- Real source colours were sampled (../_m2tools/material-rip-samples.json); material maps and exact kind/RGB values are in ../_m2tools/material-report.md and material-definitions.json.
- Brushed steel/metal, matte paint, stippled polymer, cross-textured rubber are independently assigned; Sand Wasp magazine uses warm brass (gold kind); Home Again grip uses brown cloth weave.
- special only paints sparse original marks: VEIST glyphs/chevrons/perforations, source-derived camo patches, Home cloth selvage, Ros drum engraving/reticle and frame emitter pixels. Previous repeating block camo discarded.
- Unreliable narrow/chamfer/stretched projections use detail=0; all other mapped surfaces retain limited original relief.
- Final 145 elements; T20; atlas 1024x512; PNG 262,721 bytes.
- Build and 5 directions rendered, rip comparison reviewed. ADS profile: sight frames only; 0 non-sight offenders; centre-eye ray 0 solids (reticle excluded); zfight 0 reported overlaps. Native game/hand/reload/performance QA not run. No Gradle, Minecraft, commit or kit.py edits.

## W325 MATERIAL R2 — 최종 (2026-11-05)
- 하부 리시버·전면 하우징 턱·창 끝을 steel 합금, 상부 띠·레일을 metal, 트리거를 steel로 재배정. 어두운 금속 측판과 밝은 합금 하부 분리.
- 수작업 모티프: VEIST 픽셀 각인과 황동 탄창의 두 줄 1텍셀 구멍·붉은 사선 유지.
- 위장 3종은 원본 위치를 따른 2색 큰 덩어리로 정리. 넓은 외피·프레임의 불안정한 투영은 detail=0으로 차단하고 색/재질 결/패널 경계를 유지.
- 폴리머와 고무 명도 차이 42.3. 형상 SHA-256 동일, 145요소, 기존 아틀라스 [1024, 512] 유지.
- 새 공용 kit.py로 build + 5방향 render 완료. ADS는 개방형 sight_* 프레임만 상단 돌출, 비조준기 0; 중앙시선 0; 겹침 검사 0. 실제 게임 미검증. 커밋/Gradle/Minecraft/kit.py 수정 없음.
