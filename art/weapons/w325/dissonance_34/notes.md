# Dissonance-34 (W325, rare sidearm Rapid-Fire) — base dead_man_walking_xx7463
- Identity kept: SUROS front casing with pointed roof and wide side pods (rip front view), seven-hole port pattern and SUROS logo (UV), side plate stepping back over the slide, narrow-roof slide, light muzzle cap, open trigger guard, 23 deg grip with checkered panels (UV), light heel plate.
- Elements: body 33 + magazine 2 = 35; atlas 512x512 (16 texels/px).
- Fit: uniform 45 px/m, rip rear -> z 9.4, rip top -> y 15.5; the rip falls on the base nearly 1:1 (muzzle -4.6/-4.75 vs base -4.84..-5.5 nose tip, heel y 6.8 vs 6.63, casing +-1.6 vs +-1.5). Nothing moved.
- Grip/magazine: grip core 23 deg about (y10, z6.98) = base filled_grip rake; mag shaft z 6.45..7.65 / heel z 6.35..9.4 vs base 6.35..7.55 / 6.25..9.25.
- Sight: front blade z -3.65..-3.1 top 15.78 (base 15.76, W153 tip 15.94), rear posts z 7.45..7.75 top 16.2 (base 16.34); NO_OVERLAY not set.
- Hand-painted: bore disc on the casing face, sight tops, trigger, magazine shaft. The rip's floating holo reticle plane (above the gun) is not modelled.
- Unverified: in-game first person/ADS/reload; whether the base hand pose clears the slightly wider side plate (x 6.62..9.38).

## W325 r2/r3 detail + style pass (2026-11-05)
- Elements 35 (33/2) -> 125 (122/3) body/magazine; atlas 512x512; kit STYLE pixel (palette quantise + 1-texel bevels), every panel painted flat in special() (flat_faces.json is empty).
- Dead Man Walking split: front casing in two chamfered pod sections + seam ring, raised muzzle bore ring, side plate, 3 slide segments with rear serrations, red port frame accent, 7 port holes and SUROS logo painted as crisp texels, checkered grip panels. ADS: slide top lowered 15.4 -> 15.2 (base rear slide 15.21), rear posts moved onto the base posts (z 7.45..7.71), rear cap 14.95. mag_release renamed frame_release (was wrongly in the moving magazine part).
- adscheck: OK (no slice above the base top profile behind the front third).
- Contract unchanged: grip, trigger, magazine elements/ids and muzzle/sight positions kept from r1 (except as noted).
- Unverified: in-game 1P/ADS/reload Vision; lettering legibility at 1P distance.

## W325 r4 cleanup vs the Chattering Bone negative reference (2026-11-05)
- tidy(): no coplanar overlapping faces left (lint 0 on body and magazine); chamfer bars recessed 0.012 px at the ends, parts touch without overlap.
- Remaining rotations are only real angled parts (grip, magazine, trigger, guard, stock slopes); all share their neighbour's frame.
- adscheck OK after rebuild. Unverified: in-game look.

## W325 r5 identity pass — Ace / Izanagi reference (2026-11-05)

### IDENTITY LIST
- 회갈색 SUROS 이중 폭 전방 케이싱
- 연두 SUROS 글자와 검은 명판
- 앞쪽 7개 환기구와 붉은 포트 띠
- 흰 총구 캡과 흰 탄창 바닥
- 검은 요철 그립과 하단 고정 나사

- 실제 시작 manifest 요소 124 → 123 (body/magazine은 현재 manifest 참조). 이전 r2/r3 문단의 숫자는 당시 기록이며 현재 값이 아님.
- 밀도 T=20, atlas 512×512, PNG 13,136 bytes.
- 입체: 방아쇠 3개 구간을 연결하고 방아쇠울 뒤쪽을 프레임까지 연장. 불필요하게 중복된 탄창 바닥 립 1개 제거. 방아쇠울 코너 폭을 구분하여 동일 평면 겹침 제거.
- 도색: SUROS 명판, 환기구 안쪽/금속 테두리, 금속 상하 경계, 그립 요철과 나사, 케이싱 상면 홈, 후단 인셋. 모든 면 special()에서 기본색과 상단 밝은 1텍셀/하단 어두운 1텍셀 경계를 직접 반환. projection fallback 표본 0.
- 검증: kit build, adscheck OK; west/east/top/q/front headless Blender 렌더. 일반 렌더의 잘리는 구도를 review/identity_render.py에서 재프레이밍. 변경 후 동일 법선의 동일평면 폴리곤 교차 lint 0 (1e-4 tolerance).
- 원본: 기존 /tmp/w325-rips/dissonance_34/ 및 proj_cache의 side view. 에이스·이자나기 native JSON/PNG와 /tmp/w325-ref-ace-izanagi.png를 비교 기준으로 사용. 외부 원본 수정 없음.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS. 오프라인 adscheck와 렌더는 인게임 수락을 대체하지 않음.
- 최종 사선/비교 이미지 확인: 모든 무기를 프레임 안에 재배치; 고유 색 블록·제조사 표식·그립 요철·포크/창/슬롯이 읽힘. 원작 곡선의 계단화 및 기존 base 대비 파지/힐 차이는 인게임 검수 대상.

## W325 r6 MATERIAL pass (2026-11-05)

위 r5의 넓은 면 평면 도색은 폐기하고 `STYLE=material`로 교체했다. 기존 W123 Beloved/Gnawing Hunger의 실제 코드와 게임/아틀라스 참고 이미지를 확인했다.

| 재질 이름 | kind | RGB / hex |
|---|---|---|
| casing | metal | (91, 86, 78) / #5B564E |
| slide | steel | (77, 74, 69) / #4D4A45 |
| frame | polymer | (43, 43, 40) / #2B2B28 |
| grip | rubber | (32, 30, 27) / #201E1B |
| silver | steel | (190, 191, 180) / #BEBFB4 |
| steel | metal | (92, 96, 94) / #5C605E |
| bore | dark | (17, 19, 20) / #111314 |
| magazine | steel | (48, 52, 54) / #303436 |

- special()에 남은 것: 연두 SUROS 문자, 7개 환기구의 안쪽/테두리, 작은 붉은 포트 띠, 앞 조준점.
- 베이스 면은 material()이 전부 명시적으로 배정한다. special() 표본 점유율 1.4%이며, 평면 전체를 덮던 경계/그립/베이스 칠은 제거했다.
- 원본 명암 detail은 측면에만 사용하고, 앞뒤/상하 면에는 0으로 설정하여 측면 무늬가 늘어나지 않게 했다. rubber 그립은 원본 명암을 끄거나 약하게 하고 cross 조직을 사용한다.
- 형상 변경 없음: 123요소, T20, atlas 512×512, PNG 135,238 bytes.
- 검증: build/adscheck OK, material 미배정 면 0, 동일 법선 coplanar 교차 0, 출력 SHA-256 일치. west/east/top/q/front 렌더와 원본 비교를 눈으로 확인했다.
- 정적 아틀라스 재질 표현이며 물리적 PBR 반사/거칠기 맵 재현은 아니다. native 1P/3P/ADS/장전/FPS 및 전체 ZIP은 master 통합 검증 대상.

## W325 MATERIAL pass 2 (2026-11-05)

- 재질 재배정: 케이싱·하부 프레임은 metal, 슬라이드·방아쇠울·조작부는 steel. 그립 코어 polymer와 rubber 패널 분리.
- 수작업 모티프: SUROS 하단 각인선과 끝점 두 개. 기존 문자와 7개 통풍구 유지.
- 최종 polymer/rubber 기본색 명도차 40.29/255 (Rec.709 가중 RGB 기준; 렌더 조명 후 픽셀 대비 수치가 아님). 전체 현재 색/종류는 review/material_r2_audit.json 참조.
- 형상 SHA-256이 변경 전 material_r2_baseline.json과 동일: 123요소, T20, atlas 512×512 유지. 형상 변경 없음.
- kit build 및 adscheck OK. 출력 SHA-256과 PNG 크기 일치. 재질 미배정 면 0, 동일 법선 coplanar 교차 0쌍.
- 검토 이미지: review/dissonance_34_material_r2_compare.png (현재 측면·사선·원본 비교). west/east/top/q/front headless Blender 렌더 생성 및 사선/통합 비교 육안 검토.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS·전체 배포 ZIP. Gradle/Minecraft/커밋 실행 없음.
