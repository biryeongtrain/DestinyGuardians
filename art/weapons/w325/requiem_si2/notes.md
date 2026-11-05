# Requiem SI2 (W325, rare sidearm Adaptive Burst) — base high_albedo
- Identity kept: long blue-white camo receiver, white sight housing with a recessed black screen and green top dot, white rear cap/bump, long dark lower rail, square open trigger guard, white trigger, raked grip with magazine channel (UV), the signature long raked heel plate.
- Elements: body 26 + magazine 2 = 28; atlas 512x512 (16 texels/px).
- Fit: 40 px/m, rip receiver rear -> z 11.32, top -> y 14.11; muzzle at -2.95 (base -1.6 brace / -3.48 nozzle). Below y 12.3 the model is stretched x1.1 (inverse in model2world) so the grip foot reaches the base magazine base (y ~5.85 vs 5.81).
- Grip: 17 deg core + 29 deg backstrap (rip edges 18/28 deg; base grip 17 deg). Magazine: sloped foot z 7.05..9.3 + shaft inside the grip front half (base shaft sits at z 8.09..9.25, ~0.8 px further back) — reload drop will read slightly forward of the base path.
- Heel plate shortened from rip z 13.55 to 12.9 to stay under the wrist; it is body (fixed), the magazine foot is the moving part.
- Sight: front post z -1.6..-1.3 top 14.45, rear ears z 8.7..9.3 top 14.62 = base W153 heights; NO_OVERLAY not set.
- Unverified: in-game first person/ADS/reload; wrist clearance of the heel plate; screen recess depth read at distance.

## W325 r2/r3 detail + style pass (2026-11-05)
- Elements 28 (26/2) -> 99 (96/3) body/magazine; atlas 512x512; kit STYLE pixel (palette quantise + 1-texel bevels), every panel painted flat in special() (flat_faces.json is empty).
- receiver in 3 chamfered segments with side slots and 4-piece muzzle/bore, bevelled white housing with recessed screen, frame rail/body in segments, red/blue LEDs, OMOLON lettering, heel plate rib; flat 2-colour blue/white camo blobs. ADS: housing 14.2 (base spine 14.11 + 0.15 tolerance), rear cap 13.8, sight dot is paint only.
- adscheck: OK (no slice above the base top profile behind the front third).
- Contract unchanged: grip, trigger, magazine elements/ids and muzzle/sight positions kept from r1 (except as noted).
- Unverified: in-game 1P/ADS/reload Vision; lettering legibility at 1P distance.

## W325 r4 cleanup vs the Chattering Bone negative reference (2026-11-05)
- tidy(): no coplanar overlapping faces left (lint 0 on body and magazine); chamfer bars recessed 0.012 px at the ends, parts touch without overlap.
- Remaining rotations are only real angled parts (grip, magazine, trigger, guard, stock slopes); all share their neighbour's frame.
- adscheck OK after rebuild. Unverified: in-game look.

## W325 r5 identity pass — Ace / Izanagi reference (2026-11-05)

### IDENTITY LIST
- 청색·백색 위장 긴 슬라이드
- 흰 사각 하우징 속 짙은 청색 스크린
- 검은 프레임의 OMOLON 문자·세 점 표식
- 적색·청색 상태등과 녹색 상부 점
- 흰 방아쇠와 긴 검은 후방 힐 플레이트

- 실제 시작 manifest 요소 94 → 94 (body/magazine은 현재 manifest 참조). 이전 r2/r3 문단의 숫자는 당시 기록이며 현재 값이 아님.
- 밀도 T=20, atlas 512×512, PNG 10,221 bytes.
- 입체: 사각 스크린의 실제 오목한 공간 유지. 방아쇠 상단을 프레임까지 연결하고 하단 폭을 구분. 방아쇠울 코너 겹침 제거.
- 도색: 스크린 청색 반사/상태선, 슬라이드 홈과 인셋, OMOLON 문자·점, 그립 요철, 하우징 끝 이음선, 후방 힐 선. 모든 면 special()에서 기본색과 상단 밝은 1텍셀/하단 어두운 1텍셀 경계를 직접 반환. projection fallback 표본 0.
- 검증: kit build, adscheck OK; west/east/top/q/front headless Blender 렌더. 일반 렌더의 잘리는 구도를 review/identity_render.py에서 재프레이밍. 변경 후 동일 법선의 동일평면 폴리곤 교차 lint 0 (1e-4 tolerance).
- 원본: 기존 /tmp/w325-rips/requiem_si2/ 및 proj_cache의 side view. 에이스·이자나기 native JSON/PNG와 /tmp/w325-ref-ace-izanagi.png를 비교 기준으로 사용. 외부 원본 수정 없음.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS. 오프라인 adscheck와 렌더는 인게임 수락을 대체하지 않음.
- 최종 사선/비교 이미지 확인: 모든 무기를 프레임 안에 재배치; 고유 색 블록·제조사 표식·그립 요철·포크/창/슬롯이 읽힘. 원작 곡선의 계단화 및 기존 base 대비 파지/힐 차이는 인게임 검수 대상.

## W325 r6 MATERIAL pass (2026-11-05)

위 r5의 넓은 면 평면 도색은 폐기하고 `STYLE=material`로 교체했다. 기존 W123 Beloved/Gnawing Hunger의 실제 코드와 게임/아틀라스 참고 이미지를 확인했다.

| 재질 이름 | kind | RGB / hex |
|---|---|---|
| navy | paint | (36, 49, 73) / #243149 |
| ivory | paint | (209, 205, 198) / #D1CDC6 |
| frame | polymer | (38, 42, 44) / #262A2C |
| grip | rubber | (27, 31, 33) / #1B1F21 |
| steel | steel | (113, 123, 127) / #717B7F |
| darksteel | metal | (43, 49, 52) / #2B3134 |
| screen | lens | (18, 34, 47) / #12222F |
| bore | dark | (12, 16, 20) / #0C1014 |
| magazine | steel | (57, 64, 68) / #394044 |

- special()에 남은 것: 원본 projection에서 추출한 청백 위장 조각, OMOLON 문자, 적/청 상태등, 녹색 상부 점, 스크린의 짧은 청색 상태선.
- 베이스 면은 material()이 전부 명시적으로 배정한다. special() 표본 점유율 6.7%이며, 평면 전체를 덮던 경계/그립/베이스 칠은 제거했다.
- 원본 명암 detail은 측면에만 사용하고, 앞뒤/상하 면에는 0으로 설정하여 측면 무늬가 늘어나지 않게 했다. rubber 그립은 원본 명암을 끄거나 약하게 하고 cross 조직을 사용한다.
- 형상 변경 없음: 94요소, T20, atlas 512×512, PNG 112,457 bytes.
- 검증: build/adscheck OK, material 미배정 면 0, 동일 법선 coplanar 교차 0, 출력 SHA-256 일치. west/east/top/q/front 렌더와 원본 비교를 눈으로 확인했다.
- 정적 아틀라스 재질 표현이며 물리적 PBR 반사/거칠기 맵 재현은 아니다. native 1P/3P/ADS/장전/FPS 및 전체 ZIP은 master 통합 검증 대상.

## W325 MATERIAL pass 2 (2026-11-05)

- 재질 재배정: 남색 외피만 paint. 하부 리시버·레일·중앙 이음·조준기 받침은 metal, 방아쇠와 울·핀은 steel.
- 수작업 모티프: OMOLON 세 점 삼각형과 하단 각인선. 위장무늬를 2색 큰 덩어리로 정리.
- 최종 polymer/rubber 기본색 명도차 44.64/255 (Rec.709 가중 RGB 기준; 렌더 조명 후 픽셀 대비 수치가 아님). 전체 현재 색/종류는 review/material_r2_audit.json 참조.
- 형상 SHA-256이 변경 전 material_r2_baseline.json과 동일: 94요소, T20, atlas 512×512 유지. 형상 변경 없음.
- kit build 및 adscheck OK. 출력 SHA-256과 PNG 크기 일치. 재질 미배정 면 0, 동일 법선 coplanar 교차 0쌍.
- 검토 이미지: review/requiem_si2_material_r2_compare.png (현재 측면·사선·원본 비교). west/east/top/q/front headless Blender 렌더 생성 및 사선/통합 비교 육안 검토.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS·전체 배포 ZIP. Gradle/Minecraft/커밋 실행 없음.
