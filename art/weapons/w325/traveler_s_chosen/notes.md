# Traveler's Chosen (W325, common sidearm Adaptive) — base allied_demand
- Identity kept: white/lilac slide with raised front top and black side window, blue rear receiver, chrome dial, Traveler emblem plate (UV), green top dot, black railed dust cover with teeth, open trigger guard, raked grip with white frame + dark wood panels, beavertail.
- Elements: body 40 + magazine 2 = 42 (cubes only); atlas 512x256, 16 texels/px; 4-piece nose around a real bore.
- Fit: uniform 32 px/m, rip grip back -> z 10, slide top -> y 13.25. No suppressor on the rip, so the muzzle sits at z 1.0 (base slide/suppressor joint ~1.3-1.6); base length to -4.85 is not matched (intentional, original has no can).
- Grip/trigger/magazine land on the base unmoved: trigger z ~6.2 (base 6.6-7.0), magazine body z 8.2..9.3 / floor y 6.72 (base box z 8.15..9.8, y 6.66..10.35), grip rake 18 deg (base 12).
- Sight: front blade z 1.6..2.0 and hammer-wing rear notch z 8.35..8.85 top y 13.43 = base W151 heights; NO_OVERLAY not set (W148 dot used).
- Unverified: in-game first person/ADS/reload alignment, hand overlap with the 18 deg grip, look of the backstrap/beavertail seam close up.

## W325 r2/r3 detail + style pass (2026-11-05)
- Elements 42 (40/2) -> 77 (74/3) body/magazine; atlas 512x256; kit STYLE pixel (palette quantise + 1-texel bevels), every panel painted flat in special() (flat_faces.json is empty).
- slide in 3 chamfered segments + 4-piece nose/bore, slanted vents, proud emblem plate, bezelled chrome dial, split wood grip panels; flat lilac/black/blue/wood panels. ADS: beavertail lowered under the base backstrap profile, hammer ears removed (rear wings at the base W151 notch z 8.19..8.61, top 13.43).
- adscheck: OK (no slice above the base top profile behind the front third).
- Contract unchanged: grip, trigger, magazine elements/ids and muzzle/sight positions kept from r1 (except as noted).
- Unverified: in-game 1P/ADS/reload Vision; lettering legibility at 1P distance.

## W325 r4 cleanup vs the Chattering Bone negative reference (2026-11-05)
- tidy(): no coplanar overlapping faces left (lint 0 on body and magazine); chamfer bars recessed 0.012 px at the ends, parts touch without overlap.
- Remaining rotations are only real angled parts (grip, magazine, trigger, guard, stock slopes); all share their neighbour's frame.
- adscheck OK after rebuild. Unverified: in-game look.

## W325 MATERIAL pass 2 (2026-11-05)

- 재질 재배정: 라일락 paint, 파란 후방 metal, 리시버 steel, 방아쇠울 metal, 밝은 그립 프레임 steel, chrome 다이얼, wood 그립, rubber 등판으로 분리.
- 수작업 모티프: 푸른 중심과 여섯 붉은 살의 여행자 문양, 크롬 다이얼 눈금, 목재 그립 홈.
- 최종 polymer/rubber 기본색 명도차 45.08/255 (Rec.709 가중 RGB 기준; 렌더 조명 후 픽셀 대비 수치가 아님). 전체 현재 색/종류는 review/material_r2_audit.json 참조.
- 형상 SHA-256이 변경 전 material_r2_baseline.json과 동일: 75요소, T20, atlas 512×256 유지. 형상 변경 없음.
- kit build 및 adscheck OK. 출력 SHA-256과 PNG 크기 일치. 재질 미배정 면 0, 동일 법선 coplanar 교차 8쌍.
- 기존 notes의 교차 0 주장을 정정: guard_front/guard_corner, guard_corner/guard_bottom, guard_bottom/guard_rear, trigger_blade/trigger_tip 각각 east/west의 총 8쌍이 기존 형상에 존재. 이번 형상 금지 범위에 따라 수정하지 않음. 개별 면적은 review/material_r2_lint.json에 기록.
- 검토 이미지: review/traveler_s_chosen_material_r2_compare.png (현재 측면·사선·원본 비교). west/east/top/q/front headless Blender 렌더 생성 및 사선/통합 비교 육안 검토.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS·전체 배포 ZIP. Gradle/Minecraft/커밋 실행 없음.
