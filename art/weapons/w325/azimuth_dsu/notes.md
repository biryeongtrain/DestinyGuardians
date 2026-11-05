# Azimuth DSu (rare, Aggressive hand cannon) — W325 skin over duke_mk_44

- Identity kept: green/white camo slab frame (same receiver/grip family as Mos Ultima II), olive slotted top rib, large
  dark side panel, protruding round barrel tube with bore, light cylinder in the frame window, light trigger guard (real
  opening), dark grip with medallions and slanted heel plate.
- Elements: body 28, magazine (cylinder) 2 = 30. Atlas 512x512, T 16.
- Calibration: rip cylinder centre (nx img 131,55) -> duke cylinder centre z 3.77 y 12.80; 38 px/m, SX 38. Cylinder
  z 2.30..5.15 matches the duke moving leaf (2.30..5.24); grip squeezed only 0.95 and lies on the duke grip outline.
- Deviation: the rip is 0.59 m long, ~2x the duke's barrel length ahead of the frame: shroud/side panel compressed 0.62x
  and the protruding tube to 0.37x -> muzzle -6.67 (base -6.17). Texture of those parts is squashed accordingly.
- Top rib 14.37, rip rear sight ears 14.7 at z ~5.4..6.4: under the duke sight line (~14.95), so nothing lowered.
- Not verified: in-game first person / ADS / reload; offline renders only.

## W325 detail + style pass (2026-11-05)
- Elements 30 -> body 88 + magazine 13 = 101; atlas 512x512 (pixel STYLE, PALETTE 14-16).
- DMW/W30 style: long slabs split into machined segments (hc.slab: core + side plates = 1-step chamfer, recessed grooves),
  end caps, real muzzle bores, window rims, bolts, notch rear sight + front blade, octagonal banded cylinder (mag_drum*),
  rounded trigger-guard corners. Faces painted as flat rip-colour blocks + decals (hc.Painter, rip-image px), kit draws bevel lines.
- ADS: hc.ads_clip clips every body element to the base top profile (mirror of kit adscheck); kit adscheck = OK.
  Clipped parts are grip/tang/rear-stock tops behind the hammer (z > ~6), i.e. behind the rear sight, none on the eye line.
- Magazine part ids renamed mag_core/mag_side -> mag_drum_*/mag_core (still mag_ prefix = parts.magazine); box within base moving leaf as before.
- Not verified: in-game 1P/ADS/reload Vision.

## Clean-geometry pass (Chattering Bone negative reference)
- same frame fix as Mos (grip on one 20.7 deg rake).
- Coplanar overlapping faces (z-fighting) removed by hc.deconflict (0 left); cylinder core no longer shares end planes with its bands.
- Elements now body 94 + magazine 13 = 107; adscheck OK.

## W325 identity pass — Ace/Izanagi (2026-11-05)

### IDENTITY LIST
- 세이지·크림색 위장 총몸
- 올리브 상부 통풍 리브
- 긴 돌출 총구 튜브
- 검정 측면 패널
- 밝은 실린더·방아쇠울
- 검정 체크 그립·십자 메달

- 요소 107 → 129 (body 116, magazine 13). T=24, atlas=[1024, 512].
- 모스와 같은 리브 창 구조를 적용했다. 기존 큰 위장 구획을 보존하고 측면 점검선·검정 패널 테두리/슬롯·실린더 홈·그립 체크를 페인트했다.
- 모든 노출 면에 flat 소재색·1texel 밝은 윗변/어두운 아랫변을 special()로 작성했다. 투영 노이즈는 사용하지 않는다. east/west 글자 방향은 각각 보정했다.
- T20/512에서 atlas overflow가 발생했다. 근접 그립/각인/후면 픽셀을 확보하려 T24와 1024x512(빈 행 crop)를 선택했다.
- 검증: kit build/JSON/PNG 출력, adscheck OK, west/east/top/q/front 5방향 오프라인 렌더 및 원본 비교. 비회전 요소의 동일 방향 coplanar overlap 0개.
- 미검증: 실제 Minecraft 1P/3P/ADS/장전·손 접촉·10–20개 표시 성능·팩 로드. 오프라인 결과를 인게임 수락으로 보고하지 않는다.
- 원본: 해당 proj_cache의 rip side views와 /tmp/w325-rips/azimuth_dsu/src. 기준: main checkout Ace 87 elements/512², Izanagi 79 elements/512² 및 /tmp/w325-ref-ace-izanagi.png.
- 최종 정면 보완: 총구 안쪽을 가리던 외장 부피를 분할 제거하여 실제 recessed bore를 확보했다. 모든 총구의 중심 ray에서 앞쪽 차폐 0개. Ballyhoo는 기존 bore가 열려 있어 형상 유지. Azimuth는 돌출 튜브도 관통 공간과 recessed plug로 재구성했다.

## W325 MATERIAL pass (2026-11-05, 이전 flat-paint 외관 대체)

- 기준: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, W123 Gnawing Hunger paint_tile와 Beloved Paint.tile을 읽고 비교했다.
- STYLE=material, T20. 기하·탄창 분리·조준선 계약은 material_geometry_baseline.json과 동일하다.
- 재질(키 → kind / RGB):
  - black_polymer → polymer / (47, 49, 46)
  - cream → paint / (219, 210, 190)
  - cylinder → metal / (149, 164, 137)
  - dark_steel → metal / (57, 60, 59)
  - olive_alloy → metal / (112, 109, 89)
  - panel → polymer / (42, 46, 38)
  - recess → dark / (15, 18, 19)
  - rubber → rubber / (35, 37, 36)
  - sage → paint / (165, 177, 140)
  - sight → polymer / (26, 29, 30)
  - silver → steel / (177, 184, 184)
- special()에 남긴 표현: 크림 위장 구획, 나사 홈, 그립 메달 각인, 가늠자 점. 전체 면 단색 채움·일괄 테두리·인공 그립 체크는 제거했다.
- 재질 바탕은 원본 색을 기준으로 소재별 금속 결·도장 입자·고무 교차 패턴·폴리머 요철을 구분한다. 원본 투영은 표면 명암만 사용하며 실제 PBR/반사 셰이더는 아니다.
- 늘어짐 방지: 앞/뒤 끝면, 기울어진 그립·후방 프레임·stock/tang 면은 detail=0. 위/아래는 detail<=0.25.
- 검증: build 및 adscheck OK, geometry unchanged, atlas [1024, 512], 129요소 유지. west/east/top/q/front 렌더 생성·검토.
- 실제 Minecraft 1P/ADS/장전·팩 로드·성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.

## W325 MATERIAL R2 pass (2026-11-05)

- 재배정: 측면 패널을 짙은 금속, rear/window/guard/rim을 밝은 steel로 분리; sage/cream 위장은 유지.
- 세부 모티브: 측판의 1텍셀 상단/좌측 선과 이중 세로 슬롯. 전체 면 채움으로 금속을 가리지 않고 가는 선·점 중심으로 작성했다.
- 금속/도장/폴리머/고무 구분, 원본 색 기반 마모색, plate 경계와 이음선을 사용했다. 투영 부적합 끝면·그립·상하면의 source-wear는 껐다.
- 검증: 최종 kit build/5방향 오프라인 render 완료. 형상 기준선과 완전 동일, 129요소, T20, atlas 1024×512 유지. R2 ADS 수학 검사 OK 후 최종 변경은 텍스처만 적용했다.
- 실제 Minecraft 1P/3P/ADS/장전·팩 로드·10–20개 표시 성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.
