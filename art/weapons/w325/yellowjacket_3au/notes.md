# Yellowjacket-3au (W325, rare, VEIST auto rifle Rapid-Fire) over steelfeather_repeater
- The rip uses the same VEIST frame mesh as Sand Wasp-3au (identical Back/Front/Magazine/Stock object bounds); only the optic and the paint differ. Body solids and rip->model map are copied from sand_wasp_3au/design.py; the optic is a compact upright red-dot frame (mount, two cheeks, top bar, sill, rear lobes) instead of the long holo arch.
- Identity kept: grey/black VEIST camo, lime magazine visible through the side window with the white chevron front, white suppressor, dark C-ring front grip + raked pistol grip, VEIST logo on the receiver (projected).
- Elements: body 54 + magazine 2 = 56; atlas 512x512 (16 texels/px), projection only.
- Fit: same as Sand Wasp (grip top z 7.6, eye line y 12.95 through the frame window y 12.62..13.3 at z 3.95..5.05, W151 aim tip kept, muzzle z -8.3 vs base -9.66, butt 16.55, centre <= 12.85 behind z 5.3).
- Magazine deviation (same as Sand Wasp): parts.magazine is the horizontal VEIST mag in the receiver window (z 4.72..11.3, y 9.92..10.7), not the base under-receiver box; reload motion will pull it out of the side window, away from the base hand position.
- Red-dot glass left open (no glass/reticle geometry); the rip's red lens tint is not reproduced.
- Not verified: in-game first-person/ADS/reload.

## W325 detail + pixel-style pass (2026-11-05)
- Elements 56 -> 128 (body 125 + magazine 3). Same veist.py frame as Sand Wasp (see its notes); red-dot is an open 'sight_*' frame (cheeks, top, sill, lobes lowered to 12.7, side knobs).
- Pixel style PALETTE 16, FLAT_TOL 34; lime magazine as flat blocks with white/lime chevron front.
- ADS: stock top 12.5, pad 12.45, rear rail 12.5; adscheck: only sight_* above base (z 3.67..4.67).
- Not verified in game after the fix.

## Cleanup pass (Chattering Bone negative ref, 2026-11-05)
- See final report; zfight.py reports 0 coplanar overlaps; elements now {'body': 141, 'magazine': 3}.

## W325 identity pass — Ace/Izanagi 기준 (2026-11-05)
### IDENTITY LIST
- 밝은 회백색 긴 소음기
- 검정·회색 3색 위장 몸체와 개머리판
- 라임색 VEIST 로고·수평 탄창과 흰색 사선 전면
- C형 검은 앞손잡이·뒤로 기운 그립
- 컴팩트 개방형 레드닷과 붉은 주황색 프레임 발광부

- Source: existing rip nx_albedo side + original rip quarter renders; main Ace/Izanagi native JSON and enlarged atlas comparison.
- Every visible face now uses exact hand-authored special() paint: flat materials, crisp 1-texel bright upper edges/dark lower seams, panel engraving, small bolt heads, original material blocks. No projection fallback remains. T=20, 512 atlas target.
- Large camo regions are deliberately hand-drawn 3-colour hard-edged blocks, not per-pixel photo grime. Original scratched wear is omitted.

### Final identity-pass validation
- Elements 144 -> 144 (body 141 + magazine 3); T 20; actual atlas 1024x512; PNG 18,871 bytes.
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
- Final 144 elements; T20; atlas 1024x512; PNG 224,007 bytes.
- Build and 5 directions rendered, rip comparison reviewed. ADS profile: sight frames only; 0 non-sight offenders; centre-eye ray 0 solids (reticle excluded); zfight 0 reported overlaps. Native game/hand/reload/performance QA not run. No Gradle, Minecraft, commit or kit.py edits.

## W325 MATERIAL R2 — 최종 (2026-11-05)
- 하부 리시버·전면 하우징 턱·창 끝을 steel 합금, 상부 띠·레일을 metal, 트리거를 steel로 재배정. 측판을 어둡게, 폴리머를 밝게 분리.
- 수작업 모티프: 라임 VEIST 각인과 탄창의 두 줄 1텍셀 구멍·라임 사선 유지.
- 위장 3종은 원본 위치를 따른 2색 큰 덩어리로 정리. 넓은 외피·프레임의 불안정한 투영은 detail=0으로 차단하고 색/재질 결/패널 경계를 유지.
- 폴리머와 고무 명도 차이 56.02. 형상 SHA-256 동일, 144요소, 기존 아틀라스 [1024, 512] 유지.
- 새 공용 kit.py로 build + 5방향 render 완료. ADS는 개방형 sight_* 프레임만 상단 돌출, 비조준기 0; 중앙시선 0; 겹침 검사 0. 실제 게임 미검증. 커밋/Gradle/Minecraft/kit.py 수정 없음.
