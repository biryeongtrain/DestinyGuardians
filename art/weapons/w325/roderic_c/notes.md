# Roderic-C (W325, rare sidearm Precision) — base lonesome
- Identity kept: HAKKE compact pistol — orange serrated slide rear with HAKKE logo, pale silver front slide and recoil housing (diagonal colour split from the rip UV), black frame with white slide-stop bar and takedown button, white trigger, fat stippled grip, white floorplate.
- Elements: body 21 + magazine 2 = 23; atlas 512x512.
- Fit: 48 px/m, rip rear -> z 11.0 (0.8 px rearward of a pure height fit), slide top -> y 14.69 = base breech top. Muzzle at -1.65 (base barrel to -4.3: the original is a short compact, not stretched).
- Trigger z 5.7..6.2 (base 5.9..6.8); grip 22 deg about (y 9, z 8.85) spanning z ~7.1..10.4 local (base 7.7..10.0, 10 deg) — wider and more raked than the base, checked against the rip silhouette overlay; magazine body local z 8.2..9.5 on the base box, floorplate perpendicular to the grip like the rip.
- Sight: front blade z -1.2..-0.75 top 15.06, rear wings z 8.44..8.98 top 15.15 = base W151 heights; NO_OVERLAY not set.
- Unverified: in-game first person/ADS/reload; hand overlap with the 22 deg grip (base pose was authored for 10 deg).

## W325 r2/r3 detail + style pass (2026-11-05)
- Elements 23 (21/2) -> 96 (93/3) body/magazine; atlas 512x512; kit STYLE pixel (palette quantise + 1-texel bevels), every panel painted flat in special() (flat_faces.json is empty).
- slide in chamfered segments with a seam groove where the base top dips (z 6.55..7.0), 4-piece nose + guide rod, rear serrations, HAKKE lettering, diagonal orange/silver split, rail slots, beavertail, finger grooves. ADS: slide built 13.2..14.6 (base shield roof 14.62) and model2world stretches it back onto the rip slide. mag_catch renamed frame_catch. guard_bottom now starts at z 4.05 (meets the chamfered corner).
- adscheck: OK (no slice above the base top profile behind the front third).
- Contract unchanged: grip, trigger, magazine elements/ids and muzzle/sight positions kept from r1 (except as noted).
- Unverified: in-game 1P/ADS/reload Vision; lettering legibility at 1P distance.

## W325 r4 cleanup vs the Chattering Bone negative reference (2026-11-05)
- tidy(): no coplanar overlapping faces left (lint 0 on body and magazine); chamfer bars recessed 0.012 px at the ends, parts touch without overlap.
- Remaining rotations are only real angled parts (grip, magazine, trigger, guard, stock slopes); all share their neighbour's frame.
- adscheck OK after rebuild. Unverified: in-game look.

## W325 r5 identity pass — Ace / Izanagi reference (2026-11-05)

### IDENTITY LIST
- 주황 뒤 슬라이드와 연한 은색 앞 슬라이드의 사선 경계
- 검은 HAKKE 문자
- 4개 후방 세레이션
- 흰 슬라이드 스톱·분해 레버·방아쇠
- 두 은색 고정핀을 가진 검은 요철 그립
- 흰 탄창 바닥과 은색 반동 하우징

- 실제 시작 manifest 요소 94 → 94 (body/magazine은 현재 manifest 참조). 이전 r2/r3 문단의 숫자는 당시 기록이며 현재 값이 아님.
- 밀도 T=20, atlas 512×512, PNG 10,193 bytes.
- 입체: 전방 개방 보어와 가이드 로드 유지. 방아쇠울 세 접합부 폭을 구분하고 프레임 캐치를 살짝 돌출시켜 그립과 같은 면 겹침 제거.
- 도색: HAKKE 문자 재정렬, 그립 요철과 두 원형 핀, 슬라이드의 1텍셀 경계, 프레임 고정점, 분해 레버 홈, 후면 인셋. 모든 면 special()에서 기본색과 상단 밝은 1텍셀/하단 어두운 1텍셀 경계를 직접 반환. projection fallback 표본 0.
- 검증: kit build, adscheck OK; west/east/top/q/front headless Blender 렌더. 일반 렌더의 잘리는 구도를 review/identity_render.py에서 재프레이밍. 변경 후 동일 법선의 동일평면 폴리곤 교차 lint 0 (1e-4 tolerance).
- 원본: 기존 /tmp/w325-rips/roderic_c/ 및 proj_cache의 side view. 에이스·이자나기 native JSON/PNG와 /tmp/w325-ref-ace-izanagi.png를 비교 기준으로 사용. 외부 원본 수정 없음.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS. 오프라인 adscheck와 렌더는 인게임 수락을 대체하지 않음.
- 최종 사선/비교 이미지 확인: 모든 무기를 프레임 안에 재배치; 고유 색 블록·제조사 표식·그립 요철·포크/창/슬롯이 읽힘. 원작 곡선의 계단화 및 기존 base 대비 파지/힐 차이는 인게임 검수 대상.

## W325 r6 MATERIAL pass (2026-11-05)

위 r5의 넓은 면 평면 도색은 폐기하고 `STYLE=material`로 교체했다. 기존 W123 Beloved/Gnawing Hunger의 실제 코드와 게임/아틀라스 참고 이미지를 확인했다.

| 재질 이름 | kind | RGB / hex |
|---|---|---|
| orange | paint | (175, 96, 39) / #AF6027 |
| silver | steel | (181, 197, 187) / #B5C5BB |
| frame | polymer | (29, 38, 34) / #1D2622 |
| grip | rubber | (24, 28, 27) / #181C1B |
| lever | steel | (184, 191, 181) / #B8BFB5 |
| magazine | metal | (42, 49, 49) / #2A3131 |
| bore | dark | (13, 17, 17) / #0D1111 |
| serration | metal | (100, 63, 30) / #643F1E |

- special()에 남은 것: HAKKE 문자, 은색·주황 사이의 사선 색 경계(강철 결 포함), 그립의 두 고정핀.
- 베이스 면은 material()이 전부 명시적으로 배정한다. special() 표본 점유율 2.2%이며, 평면 전체를 덮던 경계/그립/베이스 칠은 제거했다.
- 원본 명암 detail은 측면에만 사용하고, 앞뒤/상하 면에는 0으로 설정하여 측면 무늬가 늘어나지 않게 했다. rubber 그립은 원본 명암을 끄거나 약하게 하고 cross 조직을 사용한다.
- 형상 변경 없음: 94요소, T20, atlas 512×512, PNG 122,956 bytes.
- 검증: build/adscheck OK, material 미배정 면 0, 동일 법선 coplanar 교차 0, 출력 SHA-256 일치. west/east/top/q/front 렌더와 원본 비교를 눈으로 확인했다.
- 정적 아틀라스 재질 표현이며 물리적 PBR 반사/거칠기 맵 재현은 아니다. native 1P/3P/ADS/장전/FPS 및 전체 ZIP은 master 통합 검증 대상.

## W325 MATERIAL pass 2 (2026-11-05)

- 재질 재배정: 주황 paint를 후방 슬라이드에 한정. 프레임·레일·비버테일·캐치는 metal, 방아쇠울은 steel.
- 수작업 모티프: HAKKE 하단 각인선과 탄창 바닥 1텍셀 압인 리브 두 개. 기존 글자와 나사 유지.
- 최종 polymer/rubber 기본색 명도차 40.21/255 (Rec.709 가중 RGB 기준; 렌더 조명 후 픽셀 대비 수치가 아님). 전체 현재 색/종류는 review/material_r2_audit.json 참조.
- 형상 SHA-256이 변경 전 material_r2_baseline.json과 동일: 94요소, T20, atlas 512×512 유지. 형상 변경 없음.
- kit build 및 adscheck OK. 출력 SHA-256과 PNG 크기 일치. 재질 미배정 면 0, 동일 법선 coplanar 교차 0쌍.
- 검토 이미지: review/roderic_c_material_r2_compare.png (현재 측면·사선·원본 비교). west/east/top/q/front headless Blender 렌더 생성 및 사선/통합 비교 육안 검토.
- 미검증: native 1P/3P·ADS·장전·10~20개 표시·FPS·전체 배포 ZIP. Gradle/Minecraft/커밋 실행 없음.
