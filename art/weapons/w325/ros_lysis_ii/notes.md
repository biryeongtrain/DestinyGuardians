# Ros Lysis II (W325, rare, auto rifle Adaptive) over gnawing_hunger
- Identity kept: frost blue-teal camo over brown frame, shroud with stepped nose, top fin, dark vent cover and three round drums per side, twin muzzle prongs + under-barrel spike, ribbed lower block, light angled fore plates, skeleton grip frame (front post + bottom bar) with raked grip, boxy Red Dot-OAS scope with green ring reticle, stock with dark top / light rail / brown lower with sloped chin / light rear upright / brown pad.
- The rip contains two optics (Quickdraw nested inside the Red Dot-OAS); the outer OAS is modelled and projected.
- Elements: body 54 (incl. 5 reticle quads) + magazine 2 = 56; atlas 512x512 (16 texels/px). OCC_TOL 0.035 m so the rip shroud sides (inside the drum/cage envelope) project instead of being inpainted.
- Rip -> model: 25.7 px/m (21 across: drums at x 6.85..9.15, inside the base cage 6.89..9.11), rip magazine centre -> z 3.3, OAS reticle -> base eye line y 12.79; forward of z -5 compressed to 20.4 px/m (muzzle prongs end z -10.05, base -9.54). Butt z 14.5 (base 15.45, ~1 px shorter).
- Contract: magazine z 1.95..4.52 / y 4.43..7.9 (base 2.12..4.53 / 4.42..8.97); grip z 7.0..8.15 at y 9.05 raked 18 deg back (base 7.46..8.88, vertical); trigger z 6.0 (base 5.5).
- Sight: NO_OVERLAY like W302 Khvostov; own green ring reticle (4 dashes + centre dot, shade false, light 15) at z 4.55 centred x 8 / y 12.785 inside the scope window (y 12.5..13.1, x 7.68..8.32, open front to back).
- Not verified: in-game first-person/ADS/reload, reticle legibility at ADS distance, drum clipping with the support hand.

## W325 detail + pixel-style pass (2026-11-05)
- Elements 56 -> 137 (body 134 + magazine 3: mag_body, mag_window, mag_pad).
- Segmented chamfered shroud/receiver/rib block/stock, vent slats on the cover, 7 under ribs, drum hubs, raked fin, muzzle block with bore, spike tip, fore bolts, ejector, grip panel, scope front bezel + dials.
- Pixel style PALETTE 18, FLAT_TOL 30; flat frost prongs/spike, dark slats/ribs.
- ADS: scope renamed 'sight_*' (hollow box open front/back, reticle sight_reticle_*); receiver top now ends at z 8.4 with a sloped tail before the stock. adscheck: only sight_* above base (z 4.29..7.54).

## Cleanup pass (Chattering Bone negative ref, 2026-11-05)
- See final report; zfight.py reports 0 coplanar overlaps; elements now {'body': 146, 'magazine': 3}.

## W325 identity pass — Ace/Izanagi 기준 (2026-11-05)
### IDENTITY LIST
- 밝은 서리색·청록색 3색 위장
- 양쪽 3연 밝은 원형 덮개·어두운 대각 홈
- 쌍갈래 포구와 밝은 하부 스파이크
- 검갈색 하부 리브·스켈레톤 그립 프레임
- 긴 상자형 OAS 조준기와 녹색 링 레티클
- 밝은 개머리판 레일·청록 측면과 갈색 패드

- Source: existing rip nx_albedo side + original rip quarter renders; main Ace/Izanagi native JSON and enlarged atlas comparison.
- Every visible face now uses exact hand-authored special() paint: flat materials, crisp 1-texel bright upper edges/dark lower seams, panel engraving, small bolt heads, original material blocks. No projection fallback remains. T=20, 512 atlas target.
- Large camo regions are deliberately hand-drawn 3-colour hard-edged blocks, not per-pixel photo grime. Original scratched wear is omitted.

### Final identity-pass validation
- Elements 149 -> 143 (body 140 + magazine 3); T 20; actual atlas 1024x512; PNG 18,090 bytes.
- kit build and west/east/top/q/front renders succeeded; source side/quarter comparison reviewed full-size.
- kit adscheck still reports only the open sight frame above the base profile; classified helper confirms 0 non-sight offenders. Sampled centre eye ray (x=8, y=YE) has 0 solid obstructions (intentional reticle excluded). Native ADS is not yet verified.
- zfight.py: 0 coplanar overlaps (unrotated/identically rotated scope); UV coordinates valid, unique names, magazine split preserved.
- 512-wide atlas overflowed at T20; 1024 width is retained for close first-person receiver/optic lettering and 1-texel seams. kit crops unused rows to 512, avoiding a full 1024-square image.
- Removed six square cap hubs; the three raised octagonal discs per side now carry one continuous world-coordinate ring and diagonal slot. Painted frost/teal camo, pale panel contours, bronze-gray frame, stippled grip, inset magazine.
- Remaining: in-game 1P/3P, hand contact, ADS, reload and 10-20-weapon display QA are master-owned and not run here. No Gradle/Minecraft or commit was performed.

## W325 MATERIAL pass (2026-11-05) — supersedes flat identity-paint appearance
- STYLE=material; full-face special fills removed from the active pipeline. Geometry and magazine split unchanged.
- Real source colours were sampled (../_m2tools/material-rip-samples.json); material maps and exact kind/RGB values are in ../_m2tools/material-report.md and material-definitions.json.
- Brushed steel/metal, matte paint, stippled polymer, cross-textured rubber are independently assigned; Sand Wasp magazine uses warm brass (gold kind); Home Again grip uses brown cloth weave.
- special only paints sparse original marks: VEIST glyphs/chevrons/perforations, source-derived camo patches, Home cloth selvage, Ros drum engraving/reticle and frame emitter pixels. Previous repeating block camo discarded.
- Unreliable narrow/chamfer/stretched projections use detail=0; all other mapped surfaces retain limited original relief.
- Final 143 elements; T20; atlas 1024x512; PNG 316,203 bytes.
- Build and 5 directions rendered, rip comparison reviewed. ADS profile: sight frames only; 0 non-sight offenders; centre-eye ray 0 solids (reticle excluded); zfight 0 reported overlaps. Native game/hand/reload/performance QA not run. No Gradle, Minecraft, commit or kit.py edits.

## W325 MATERIAL R2 — 최종 (2026-11-05)
- 후방 리시버 두 구간을 노출 frame metal, 밝은 레일·포구 갈래·스파이크를 steel로 재배정. 넓은 프레임 투영 잡티 제거.
- 수작업 모티프: 3연 덮개 대각 각인 유지, 후방 작동부에 연속 얇은 패널선 추가.
- 위장 3종은 원본 위치를 따른 2색 큰 덩어리로 정리. 넓은 외피·프레임의 불안정한 투영은 detail=0으로 차단하고 색/재질 결/패널 경계를 유지.
- 폴리머와 고무 명도 차이 49.34. 형상 SHA-256 동일, 143요소, 기존 아틀라스 [1024, 512] 유지.
- 새 공용 kit.py로 build + 5방향 render 완료. ADS는 개방형 sight_* 프레임만 상단 돌출, 비조준기 0; 중앙시선 0; 겹침 검사 0. 실제 게임 미검증. 커밋/Gradle/Minecraft/kit.py 수정 없음.
