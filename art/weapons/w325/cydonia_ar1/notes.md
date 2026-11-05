# Cydonia-AR1 (W325, uncommon, auto rifle Adaptive) over gnawing_hunger
- Identity kept: maroon + gunmetal paint, long slotted octagonal suppressor on a thin neck/collar, maroon top cover (low front with dark cap, ramp, high rear), vented dark mid rail, maroon under-tube with dark front cap, maroon fore plates, skeleton grip frame (front post + bottom bar) with raked grip, side lever, small reflex sight, skeleton stock (maroon block with dark insets, rear upright, slotted dark pad, long diagonal bar to the grip).
- Receiver/grip/magazine ("Middle"/"Magazine" objects) are the same mesh as Ros Lysis II's; the rip's two nested optics (TrueSight + Fastdraw) are modelled as one reflex frame.
- Elements: body 36 + magazine 2 = 38; atlas 512x512 (16 texels/px), projection only.
- Rip -> model: single uniform 25.7 px/m map (23 across); rip magazine centre -> z 3.3, reticle -> base eye line y 12.79. Muzzle z -9.47 (base -9.54), butt z 15.2 (base 15.45). Magazine z 2.09..4.66 / y 4.66..8.13 (base 2.12..4.53 / 4.42..8.97); grip z 7.14..8.29 at y 9.28 raked 18 deg (base 7.46..8.88 vertical); trigger z 6.2 (base 5.5).
- Sight: reflex window y 12.45..13.0 at z 6.3..6.95 open, W151 aim tip (z 2.8, y 12.71..12.87) kept (no_overlay false); everything in front of the sight on the centre line stays <= 12.3 (top cover). Rip lens/reticle not reproduced.
- Not verified: in-game first-person/ADS/reload; the aim tip sits 3.5 px in front of the reflex frame (the eye sees the dot through the frame window).

## W325 detail + pixel-style pass (2026-11-05)
- Elements 38 -> 126 (body 123 + magazine 3).
- Rebuilt in Dead Man Walking style: segmented maroon cover (3 blocks), mid rail with vent teeth, ribbed under-tube with octagonal nose, two-piece slotted suppressor, stepped receiver with rail teeth, stock block with dark insets and slotted pad. Flat palette maroon/dark/gunmetal (PALETTE 14).
- ADS (was 27 slices over): the rip's high rear cover is flattened to y 11.98 (base 12.04), receiver/rail <= 12.03; reflex sight is a hollow 'sight_*' frame. adscheck: only sight_* above base (z 6.04..6.79). Identity loss: the rip's raised rear cover hump is gone.

## Cleanup pass (Chattering Bone negative ref, 2026-11-05)
- See final report; zfight.py reports 0 coplanar overlaps; elements now {'body': 132, 'magazine': 3}.

## W325 identity pass — Ace/Izanagi 기준 (2026-11-05)
### IDENTITY LIST
- 적갈색 긴 상부 덮개·하부 튜브·측판
- 청회색 금속 리시버의 가로 슬롯과 계단형 패널선
- 소음기 전방의 실제 관통 슬롯
- 촘촘한 밝은 금속 환기 홈·하부 튜브 리브
- 적갈색 스켈레톤 개머리판·어두운 매립부
- 검은 사각 탄창의 창·홈과 짧은 반사 조준기

- Source: existing rip nx_albedo side + original rip quarter renders; main Ace/Izanagi native JSON and enlarged atlas comparison.
- Every visible face now uses exact hand-authored special() paint: flat materials, crisp 1-texel bright upper edges/dark lower seams, panel engraving, small bolt heads, original material blocks. No projection fallback remains. T=20, 512 atlas target.
- Large camo regions are deliberately hand-drawn 3-colour hard-edged blocks, not per-pixel photo grime. Original scratched wear is omitted.

### Final identity-pass validation
- Elements 135 -> 141 (body 138 + magazine 3); T 20; actual atlas 1024x512; PNG 13,329 bytes.
- kit build and west/east/top/q/front renders succeeded; source side/quarter comparison reviewed full-size.
- kit adscheck still reports only the open sight frame above the base profile; classified helper confirms 0 non-sight offenders. Sampled centre eye ray (x=8, y=YE) has 0 solid obstructions (intentional reticle excluded). Native ADS is not yet verified.
- zfight.py: 0 coplanar overlaps (unrotated/identically rotated scope); UV coordinates valid, unique names, magazine split preserved.
- 512-wide atlas overflowed at T20; 1024 width is retained for close first-person receiver/optic lettering and 1-texel seams. kit crops unused rows to 512, avoiding a full 1024-square image.
- Modelled a real through-slot in the front suppressor; painted maroon cover/foreplate contours, metal vent grooves, receiver slots, bolt heads, magazine framing and stock inset. Existing reduced cover height (ADS contract) remains.
- Remaining: in-game 1P/3P, hand contact, ADS, reload and 10-20-weapon display QA are master-owned and not run here. No Gradle/Minecraft or commit was performed.

## W325 MATERIAL pass (2026-11-05) — supersedes flat identity-paint appearance
- STYLE=material; full-face special fills removed from the active pipeline. Geometry and magazine split unchanged.
- Real source colours were sampled (../_m2tools/material-rip-samples.json); material maps and exact kind/RGB values are in ../_m2tools/material-report.md and material-definitions.json.
- Brushed steel/metal, matte paint, stippled polymer, cross-textured rubber are independently assigned; Sand Wasp magazine uses warm brass (gold kind); Home Again grip uses brown cloth weave.
- special only paints sparse original marks: VEIST glyphs/chevrons/perforations, source-derived camo patches, Home cloth selvage, Ros drum engraving/reticle and frame emitter pixels. Previous repeating block camo discarded.
- Unreliable narrow/chamfer/stretched projections use detail=0; all other mapped surfaces retain limited original relief.
- Final 141 elements; T20; atlas 1024x512; PNG 198,743 bytes.
- Build and 5 directions rendered, rip comparison reviewed. ADS profile: sight frames only; 0 non-sight offenders; centre-eye ray 0 solids (reticle excluded); zfight 0 reported overlaps. Native game/hand/reload/performance QA not run. No Gradle, Minecraft, commit or kit.py edits.

## W325 MATERIAL R2 — 최종 (2026-11-05)
- 가드·트리거·레일·핀을 steel, 개머리판 매립부를 dark로 재배정. 적갈색 외피는 실제 도색 영역이라 유지하고 인접 프레임 metal을 어둡게 분리.
- 수작업 모티프: 중간 레일 냉각 슬릿의 밝고 어두운 1텍셀 선, 탄창 양측 홈과 밝은 리브선 추가.
- 위장 3종은 원본 위치를 따른 2색 큰 덩어리로 정리. 넓은 외피·프레임의 불안정한 투영은 detail=0으로 차단하고 색/재질 결/패널 경계를 유지.
- 폴리머와 고무 명도 차이 47.59. 형상 SHA-256 동일, 141요소, 기존 아틀라스 [1024, 512] 유지.
- 새 공용 kit.py로 build + 5방향 render 완료. ADS는 개방형 sight_* 프레임만 상단 돌출, 비조준기 0; 중앙시선 0; 겹침 검사 0. 실제 게임 미검증. 커밋/Gradle/Minecraft/kit.py 수정 없음.
