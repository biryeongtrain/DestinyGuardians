# Vinegaroon-2si (W325, rare sidearm Lightweight) — base farewell
- Identity kept: VEIST pale-yellow slide with sloped top, ejection slot, rear window and logo (UV), teal stripe band, octagonal suppressor with collar + knurled ring, knuckle frame with real trigger opening, lower finger opening, white spine bar and the hooked front fin, green perforated magazine block with white floor.
- Elements: body 40 + magazine 3 = 43 (suppressor 18 of them); atlas 512x512.
- Fit: 34 px/m with z = 7.83 + rip_y*34 (trigger z ~5.75 vs base 5.0..5.4, muzzle -5.3 vs base -4.87), y ref rip top 0.145 -> 13.75; mag floor y 6.82 vs base heel 6.88; grip/mag rake 16 deg vs base 14; mag shaft local z 7.5..8.7 vs base 7.57..8.85.
- Sight: the rip has no irons — added a clamped front blade on the suppressor at the base W151 aim point (z -1.15..-0.85, top 14.1) and two rear ears on the slide (z 7.0..7.8, top 14.3); NO_OVERLAY not set.
- Simplified: the fin is three straight slabs (rip edge is a smooth concave hook); frame rear hump and grip are boxes, not the rip's curves.
- Unverified: in-game first person/ADS/reload; whether the base hand pose sits well in the narrower knuckle frame.

## W325 r2/r3 detail + style pass (2026-11-05)
- Elements 43 (40/3) -> 80 (76/4) body/magazine; atlas 512x512; kit STYLE pixel (palette quantise + 1-texel bevels), every panel painted flat in special() (flat_faces.json is empty).
- slide with real ejection slot and rear window openings, bevelled frame band, suppressor end cap + band + bore, fin tip, frame pins, proud grip shells, magazine lip; flat yellow/teal/black, VEIST lettering, perforated green magazine block. ADS: slide top lowered to 13.42..13.62 (base upper rail 13.61).
- adscheck: OK (no slice above the base top profile behind the front third).
- Contract unchanged: grip, trigger, magazine elements/ids and muzzle/sight positions kept from r1 (except as noted).
- Unverified: in-game 1P/ADS/reload Vision; lettering legibility at 1P distance.

## W325 r4 cleanup vs the Chattering Bone negative reference (2026-11-05)
- tidy(): no coplanar overlapping faces left (lint 0 on body and magazine); chamfer bars recessed 0.012 px at the ends, parts touch without overlap.
- Remaining rotations are only real angled parts (grip, magazine, trigger, guard, stock slopes); all share their neighbour's frame.
- adscheck OK after rebuild. Unverified: in-game look.

## W325 r5 identity pass — Ace / Izanagi reference (2026-11-05)

### IDENTITY LIST
- 노랑 슬라이드와 청록 VEIST 문자
- 검정 소음기의 두 아이보리 띠·회색 널링 칼라
- 측면의 실제 두 직사각 창
- 짙은 녹색 프레임과 검은 전방 갈고리
- 아이보리 세로 브리지·녹색 구멍 탄창 바닥
- 검은 하부 그립 패널과 금속 고정점

- 실제 시작 manifest 요소 85 → 91 (body/magazine은 현재 manifest 참조). 이전 r2/r3 문단의 숫자는 당시 기록이며 현재 값이 아님.
- 밀도 T=20, atlas 512×512, PNG 15,541 bytes.
- 입체: 전방 갈고리를 6개의 큰 계단에서 모서리가 맞닿는 12개 단계로 세분화. 방아쇠 팁 접합 폭 구분. 실제 슬라이드 창과 탄창 분리 유지.
- 도색: 널링 격자, 소음기 띠·긴 홈, 노랑 슬라이드 상단 광택선, 청록 사선 마킹, 그립 요철·고정핀·하부 패널, 갈고리 인셋. 모든 면 special()에서 기본색과 상단 밝은 1텍셀/하단 어두운 1텍셀 경계를 직접 반환. projection fallback 표본 0.
- 검증: kit build, adscheck OK; west/east/top/q/front headless Blender 렌더. 일반 렌더의 잘리는 구도를 review/identity_render.py에서 재프레이밍. 변경 후 동일 법선의 동일평면 폴리곤 교차 lint 0 (1e-4 tolerance).
- 원본: 기존 /tmp/w325-rips/vinegaroon_2si/ 및 proj_cache의 side view. 에이스·이자나기 native JSON/PNG와 /tmp/w325-ref-ace-izanagi.png를 비교 기준으로 사용. 외부 원본 수정 없음.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS. 오프라인 adscheck와 렌더는 인게임 수락을 대체하지 않음.
- 최종 사선/비교 이미지 확인: 모든 무기를 프레임 안에 재배치; 고유 색 블록·제조사 표식·그립 요철·포크/창/슬롯이 읽힘. 원작 곡선의 계단화 및 기존 base 대비 파지/힐 차이는 인게임 검수 대상.

## W325 r6 MATERIAL pass (2026-11-05)

위 r5의 넓은 면 평면 도색은 폐기하고 `STYLE=material`로 교체했다. 기존 W123 Beloved/Gnawing Hunger의 실제 코드와 게임/아틀라스 참고 이미지를 확인했다.

| 재질 이름 | kind | RGB / hex |
|---|---|---|
| yellow | paint | (190, 184, 108) / #BEB86C |
| teal | polymer | (30, 51, 46) / #1E332E |
| steel | steel | (117, 125, 121) / #757D79 |
| suppressor | metal | (31, 34, 35) / #1F2223 |
| fin | metal | (28, 30, 32) / #1C1E20 |
| grip | rubber | (25, 33, 31) / #19211F |
| ivory | steel | (183, 190, 171) / #B7BEAB |
| green | paint | (61, 105, 86) / #3D6956 |
| bore | dark | (12, 16, 17) / #0C1011 |

- special()에 남은 것: VEIST 문자와 청록 사선, 소음기의 두 아이보리 띠(도장 입자 포함), 탄창 바닥의 작은 구멍.
- 베이스 면은 material()이 전부 명시적으로 배정한다. special() 표본 점유율 2.1%이며, 평면 전체를 덮던 경계/그립/베이스 칠은 제거했다.
- 원본 명암 detail은 측면에만 사용하고, 앞뒤/상하 면에는 0으로 설정하여 측면 무늬가 늘어나지 않게 했다. rubber 그립은 원본 명암을 끄거나 약하게 하고 cross 조직을 사용한다.
- 형상 변경 없음: 91요소, T20, atlas 512×512, PNG 125,649 bytes.
- 검증: build/adscheck OK, material 미배정 면 0, 동일 법선 coplanar 교차 0, 출력 SHA-256 일치. west/east/top/q/front 렌더와 원본 비교를 눈으로 확인했다.
- 정적 아틀라스 재질 표현이며 물리적 PBR 반사/거칠기 맵 재현은 아니다. native 1P/3P/ADS/장전/FPS 및 전체 ZIP은 master 통합 검증 대상.
- 투영 수정: 노랑 슬라이드의 명암 detail을 .20으로 낮추고 spine·mag_floor·mag_lip은 0. 소음기 널링 칼라만 steel의 cross 조직으로 구분.

## W325 MATERIAL pass 2 (2026-11-05)

- 재질 재배정: 상부 노란 외피만 paint. 슬라이드 하단·청록 구조 띠·프레임·방아쇠울·하단은 metal, 검은 핀은 metal.
- 수작업 모티프: 소음기 은색 칼라에 1텍셀 교차 널링. VEIST 문자와 소음기 띠 유지.
- 최종 polymer/rubber 기본색 명도차 51.3/255 (Rec.709 가중 RGB 기준; 렌더 조명 후 픽셀 대비 수치가 아님). 전체 현재 색/종류는 review/material_r2_audit.json 참조.
- 형상 SHA-256이 변경 전 material_r2_baseline.json과 동일: 91요소, T20, atlas 512×512 유지. 형상 변경 없음.
- kit build 및 adscheck OK. 출력 SHA-256과 PNG 크기 일치. 재질 미배정 면 0, 동일 법선 coplanar 교차 0쌍.
- 검토 이미지: review/vinegaroon_2si_material_r2_compare.png (현재 측면·사선·원본 비교). west/east/top/q/front headless Blender 렌더 생성 및 사선/통합 비교 육안 검토.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS·전체 배포 ZIP. Gradle/Minecraft/커밋 실행 없음.
