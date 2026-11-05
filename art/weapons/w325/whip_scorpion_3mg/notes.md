# Whip Scorpion-3mg (W325, rare SMG Lightweight) — base the_recluse
- Same rip mesh as Furina-2mg (identical bounds; side silhouettes compared row by row, identical), only the albedo differs: black/grey camo, lime rail windows, VEIST stock logo, pale shroud.
- design.py imports the Furina geometry/model2world/specials (art/weapons/w325/furina_2mg/design.py); the kit projects this weapon's own proj_cache, so the atlas is its own.
- Elements: body 27 + magazine 1 = 28; atlas 512x512. Fit notes, sight hoop and magazine split are identical to Furina-2mg (see its notes.md).
- Unverified: in-game first person/ADS/reload. If Furina's geometry is changed later, rebuild this id too.

## W325 r2/r3 detail + style pass (2026-11-05)
- Elements 28 (27/1) -> 105 (102/3) body/magazine; atlas 512x512; kit STYLE pixel (palette quantise + 1-texel bevels), every panel painted flat in special() (flat_faces.json is empty).
- geometry and painting code imported from furina_2mg/design.py; only COLS differs (black/charcoal camo, lime windows, lime panel line, lime VEIST logo). ADS identical to Furina.
- adscheck: OK (no slice above the base top profile behind the front third).
- Contract unchanged: grip, trigger, magazine elements/ids and muzzle/sight positions kept from r1 (except as noted).
- Unverified: in-game 1P/ADS/reload Vision; lettering legibility at 1P distance.

## W325 r4 cleanup vs the Chattering Bone negative reference (2026-11-05)
- tidy(): no coplanar overlapping faces left (lint 0 on body and magazine); chamfer bars recessed 0.012 px at the ends, parts touch without overlap.
- Remaining rotations are only real angled parts (grip, magazine, trigger, guard, stock slopes); all share their neighbour's frame.
- adscheck OK after rebuild. Unverified: in-game look.

## W325 r5 identity pass — Ace / Izanagi reference (2026-11-05)

### IDENTITY LIST
- 검정·회색 위장 VEIST 몸체
- 연두 이중 환기구 띠와 패널선
- 개머리판 상단의 연두 VEIST 문자
- 백색 포크 총구와 회색 칼라
- 삼각형 스켈레톤 스톡
- 네 통과 슬롯 전방 핀과 개방 조준 고리

- 실제 시작 manifest 요소 103 → 105 (body/magazine은 현재 manifest 참조). 이전 r2/r3 문단의 숫자는 당시 기록이며 현재 값이 아님.
- 밀도 T=20, atlas 1024×512, PNG 16,335 bytes.
- 입체: Furina의 변경 형상과 전체 면 도색을 공유하며 이 무기의 독립 색상과 아틀라스를 재생성.
- 도색: Furina 도색 구조를 공유하되 검정/회색 위장, 연두 환기구·로고·띠, 흰 총구의 팔레트를 유지. 모든 면 special()에서 기본색과 상단 밝은 1텍셀/하단 어두운 1텍셀 경계를 직접 반환. projection fallback 표본 0.
- 검증: kit build, adscheck OK; west/east/top/q/front headless Blender 렌더. 일반 렌더의 잘리는 구도를 review/identity_render.py에서 재프레이밍. 변경 후 동일 법선의 동일평면 폴리곤 교차 lint 0 (1e-4 tolerance).
- 원본: 기존 /tmp/w325-rips/whip_scorpion_3mg/ 및 proj_cache의 side view. 에이스·이자나기 native JSON/PNG와 /tmp/w325-ref-ace-izanagi.png를 비교 기준으로 사용. 외부 원본 수정 없음.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS. 오프라인 adscheck와 렌더는 인게임 수락을 대체하지 않음.
- 아틀라스 예외: 512²에서 T20 패킹이 546행으로 넘쳤음. 가까운 조준부/리시버의 2열 환기구와 작은 로고를 유지하기 위해 1024 폭을 사용하고 실제 512행으로 크롭. 최종 전체 배포 ZIP은 master 통합 시 확인 필요.
- 최종 사선/비교 이미지 확인: 모든 무기를 프레임 안에 재배치; 고유 색 블록·제조사 표식·그립 요철·포크/창/슬롯이 읽힘. 원작 곡선의 계단화 및 기존 base 대비 파지/힐 차이는 인게임 검수 대상.

## W325 r6 MATERIAL pass (2026-11-05)

위 r5의 넓은 면 평면 도색은 폐기하고 `STYLE=material`로 교체했다. 기존 W123 Beloved/Gnawing Hunger의 실제 코드와 게임/아틀라스 참고 이미지를 확인했다.

| 재질 이름 | kind | RGB / hex |
|---|---|---|
| receiver | paint | (34, 35, 38) / #222326 |
| shroud | steel | (205, 201, 208) / #CDC9D0 |
| rail | steel | (132, 141, 146) / #848D92 |
| collar | steel | (156, 151, 160) / #9C97A0 |
| polymer | polymer | (25, 27, 29) / #191B1D |
| rubber | rubber | (21, 23, 25) / #151719 |
| bore | dark | (12, 17, 20) / #0C1114 |
| lens | lens | (27, 67, 86) / #1B4356 |

- special()에 남은 것: 자기 원본 projection에서 추출한 회색 위장 조각, 연두 VEIST·2열 환기구·좁은 패널선, 렌즈 하이라이트.
- 베이스 면은 material()이 전부 명시적으로 배정한다. special() 표본 점유율 5.1%이며, 평면 전체를 덮던 경계/그립/베이스 칠은 제거했다.
- 원본 명암 detail은 측면에만 사용하고, 앞뒤/상하 면에는 0으로 설정하여 측면 무늬가 늘어나지 않게 했다. rubber 그립은 원본 명암을 끄거나 약하게 하고 cross 조직을 사용한다.
- 형상 변경 없음: 105요소, T20, atlas 1024×512, PNG 157,063 bytes.
- 검증: build/adscheck OK, material 미배정 면 0, 동일 법선 coplanar 교차 0, 출력 SHA-256 일치. west/east/top/q/front 렌더와 원본 비교를 눈으로 확인했다.
- 정적 아틀라스 재질 표현이며 물리적 PBR 반사/거칠기 맵 재현은 아니다. native 1P/3P/ADS/장전/FPS 및 전체 ZIP은 master 통합 검증 대상.
- stock_web·stock_brace·housing_front는 새 형상과 원본 투영이 일치하지 않아 detail=0. 긴 몸체의 위장 조각은 자기 원본 cache의 밝은 도장을 stencil로 선택하며, 임의의 큰 camo blob은 제거했다.

## W325 MATERIAL pass 2 (2026-11-05)

- 재질 재배정: Furina 재질 배정 상속. 회색 외측 패널 paint, 밝은 청회색 구조 metal, polymer와 rubber 분리.
- 수작업 모티프: 하부 리시버 고정 리벳 줄. 회색 위장·녹색 VEIST와 통풍 띠 유지.
- 최종 polymer/rubber 기본색 명도차 50.72/255 (Rec.709 가중 RGB 기준; 렌더 조명 후 픽셀 대비 수치가 아님). 전체 현재 색/종류는 review/material_r2_audit.json 참조.
- 형상 SHA-256이 변경 전 material_r2_baseline.json과 동일: 105요소, T20, atlas 1024×512 유지. 형상 변경 없음.
- kit build 및 adscheck OK. 출력 SHA-256과 PNG 크기 일치. 재질 미배정 면 0, 동일 법선 coplanar 교차 0쌍.
- 검토 이미지: review/whip_scorpion_3mg_material_r2_compare.png (현재 측면·사선·원본 비교). west/east/top/q/front headless Blender 렌더 생성 및 사선/통합 비교 육안 검토.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS·전체 배포 ZIP. Gradle/Minecraft/커밋 실행 없음.
