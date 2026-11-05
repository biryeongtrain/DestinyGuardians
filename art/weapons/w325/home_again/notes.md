# Home Again (W325, uncommon, auto rifle Rapid-Fire) over steelfeather_repeater
- Identity kept: olive receiver with framed magwell plate, ejection port and side lever ring, curved black magazine with rubber floor bulge, worn dark handguard with two oval slots + under-rail teeth and curved belly, thin barrel with sleeve and slotted brake, small hooded red-dot, brown wrapped raked pistol grip, skeleton stock with two real windows, centre post, diagonal lower bar, flared pad.
- Elements: body 37 + magazine 3 = 40; atlas 512x512 (16 texels/px). Special: the rip's oval handguard slots are through-holes, painted as dark recesses (design.special) so they are not inpainted away.
- Rip -> model: single uniform 24 px/m map; rip magazine centre -> z 3.3, red-dot reticle -> eye line y 12.95. The rip already matches the base: muzzle z -8.87 (base -9.66), butt pad z 14.9 (base body 16.59 / full 15.34), mag z 1.95..4.7 x y 6.35..9.9 (base 1.98..4.67 x 6.11..9.72, ours raked ~10 deg forward like the rip), grip top z 7.0..8.35 at y 10.5 raked 13 deg (base grip z 6.7..9.7).
- Sight: red-dot window y 12.75..13.15 open at z 2.75..3.75, W151 aim tip kept (no_overlay false); handguard top 12.2 and stock top 11.67 stay under the eye line.
- Not verified: in-game first-person/ADS/reload; the side lever ring protrudes 0.45 px on the -x side (may clip the left hand in some reload frames).

## W325 detail + pixel-style pass (2026-11-05)
- Elements 40 -> 119 (body 115 + magazine 4: mag_neck, mag_body, mag_rib, mag_floor).
- Segmented chamfered handguard/receiver/stock blocks with groove joints, octagonal barrel/sleeve, slotted brake, framed magwell plate (light frame strips), port + bolt handle, pin, wrapped brown grip, ribbed magazine, pad chamfers.
- Pixel style PALETTE 16, FLAT_TOL 30; handguard oval slots repainted dark via special (pixel bake had erased them); brown grip, black magazine flat.
- ADS: red-dot renamed to 'sight_*' (hollow frame, window y 12.75..13.15); adscheck only sight_* above base (z 2.42..3.67).

## Cleanup pass (Chattering Bone negative ref, 2026-11-05)
- See final report; zfight.py reports 0 coplanar overlaps; elements now {'body': 123, 'magazine': 4}.

## W325 identity pass — Ace/Izanagi 기준 (2026-11-05)
### IDENTITY LIST
- 올리브색 리시버와 밝은 금속 탄창 삽입구 테두리
- 두 개의 실제 관통 통풍구가 있는 짙은 회색 핸드가드
- 브레이크의 관통 슬롯·얇은 총열
- 갈색 대각선 감김 그립
- 검은 곡선 탄창과 돌출 바닥
- 두 개의 빈 창을 가진 검은 스켈레톤 개머리판

- Source: existing rip nx_albedo side + original rip quarter renders; main Ace/Izanagi native JSON and enlarged atlas comparison.
- Every visible face now uses exact hand-authored special() paint: flat materials, crisp 1-texel bright upper edges/dark lower seams, panel engraving, small bolt heads, original material blocks. No projection fallback remains. T=20, 512 atlas target.
- Large camo regions are deliberately hand-drawn 3-colour hard-edged blocks, not per-pixel photo grime. Original scratched wear is omitted.

### Final identity-pass validation
- Elements 127 -> 141 (body 137 + magazine 4); T 20; actual atlas 512x512; PNG 14,678 bytes.
- kit build and west/east/top/q/front renders succeeded; source side/quarter comparison reviewed full-size.
- kit adscheck still reports only the open sight frame above the base profile; classified helper confirms 0 non-sight offenders. Sampled centre eye ray (x=8, y=YE) has 0 solid obstructions (intentional reticle excluded). Native ADS is not yet verified.
- zfight.py: 0 coplanar overlaps (unrotated/identically rotated scope); UV coordinates valid, unique names, magazine split preserved.
- Modelled new real through-windows in the handguard and through-slots in the brake; painted olive receiver contours, ejection metal, brown diagonal grip wrapping, magazine grooves. Centre-ray check caught the old sloped sight lip crossing the eye line; replaced it with a flush horizontal roof lip.
- Remaining: in-game 1P/3P, hand contact, ADS, reload and 10-20-weapon display QA are master-owned and not run here. No Gradle/Minecraft or commit was performed.

## W325 MATERIAL pass (2026-11-05) — supersedes flat identity-paint appearance
- STYLE=material; full-face special fills removed from the active pipeline. Geometry and magazine split unchanged.
- Real source colours were sampled (../_m2tools/material-rip-samples.json); material maps and exact kind/RGB values are in ../_m2tools/material-report.md and material-definitions.json.
- Brushed steel/metal, matte paint, stippled polymer, cross-textured rubber are independently assigned; Sand Wasp magazine uses warm brass (gold kind); Home Again grip uses brown cloth weave.
- special only paints sparse original marks: VEIST glyphs/chevrons/perforations, source-derived camo patches, Home cloth selvage, Ros drum engraving/reticle and frame emitter pixels. Previous repeating block camo discarded.
- Unreliable narrow/chamfer/stretched projections use detail=0; all other mapped surfaces retain limited original relief.
- Final 141 elements; T20; atlas 512x512; PNG 168,115 bytes.
- Build and 5 directions rendered, rip comparison reviewed. ADS profile: sight frames only; 0 non-sight offenders; centre-eye ray 0 solids (reticle excluded); zfight 0 reported overlaps. Native game/hand/reload/performance QA not run. No Gradle, Minecraft, commit or kit.py edits.

## W325 MATERIAL R2 — 최종 (2026-11-05)
- 하부 리시버·방아쇠 상자·후단판·가드·트리거를 metal, 탄피 배출부 테두리·탄창 삽입구 턱을 steel로 재배정. 올리브색은 외부 판에 한정.
- 수작업 모티프: 갈색 천 감김 가장자리 유지, 탄창에 1텍셀 어두운 홈과 밝은 리브선 추가.
- 위장 3종은 원본 위치를 따른 2색 큰 덩어리로 정리. 넓은 외피·프레임의 불안정한 투영은 detail=0으로 차단하고 색/재질 결/패널 경계를 유지.
- 폴리머와 고무 명도 차이 46.17. 형상 SHA-256 동일, 141요소, 기존 아틀라스 [512, 512] 유지.
- 새 공용 kit.py로 build + 5방향 render 완료. ADS는 개방형 sight_* 프레임만 상단 돌출, 비조준기 0; 중앙시선 0; 겹침 검사 0. 실제 게임 미검증. 커밋/Gradle/Minecraft/kit.py 수정 없음.
