# Ballyhoo Mk.27 (rare, Adaptive hand cannon) — W325 skin over austringer

- Identity kept: wide brown top shroud with light diagonal strap, teal distressed frame/barrel, light frame window around a
  teal cylinder, dark under-barrel lug with two pins, hanging front loop (real opening) on a light mount, round light
  trigger guard (real opening), dark grip with medallions and light heel plate.
- Elements: body 27, magazine (cylinder) 2 = 29. Atlas 512x512, T 16.
- Calibration: rip cylinder centre (nx img 128.5,56.5) -> austringer cylinder centre z 4.34 y 12.43; 38 px/m (cylinder
  z 2.94..5.74 inside the base moving box 2.82..5.86). Barrel ahead of the frame stretched 1.115x: muzzle -5.7 (base -6.32;
  the rip is a stubby gun, full base length would distort it).
- Fits: shroud/top strap lowered to 13.85/13.92 (rip 14.40) under the austringer sight line, rear-sight ears 14.10 at z
  4.95..5.55; grip + light frame rear squeezed horizontally to 0.75 behind the front strap so the stock follows the base grip
  outline (offline overlay); grip split upper/lower to follow the curved back edge.
- Not verified: in-game first person / ADS / reload swing; the hanging loop sits below the barrel where the base has nothing
  (check it does not clip the support hand in FP).

## W325 detail + style pass (2026-11-05)
- Elements 29 -> body 92 + magazine 13 = 105; atlas 512x512 (pixel STYLE, PALETTE 14-16).
- DMW/W30 style: long slabs split into machined segments (hc.slab: core + side plates = 1-step chamfer, recessed grooves),
  end caps, real muzzle bores, window rims, bolts, notch rear sight + front blade, octagonal banded cylinder (mag_drum*),
  rounded trigger-guard corners. Faces painted as flat rip-colour blocks + decals (hc.Painter, rip-image px), kit draws bevel lines.
- ADS: hc.ads_clip clips every body element to the base top profile (mirror of kit adscheck); kit adscheck = OK.
  Clipped parts are grip/tang/rear-stock tops behind the hammer (z > ~6), i.e. behind the rear sight, none on the eye line.
- Magazine part ids renamed mag_core/mag_side -> mag_drum_*/mag_core (still mag_ prefix = parts.magazine); box within base moving leaf as before.
- Not verified: in-game 1P/ADS/reload Vision.

## Clean-geometry pass (Chattering Bone negative reference)
- grip upper/lower/heel (14-16 deg, crossing edges) -> one 14.8 deg rake stack; 42 deg side straps (stuck out of the shroud) -> painted flush stripe.
- Coplanar overlapping faces (z-fighting) removed by hc.deconflict (0 left); cylinder core no longer shares end planes with its bands.
- Elements now body 92 + magazine 13 = 105; adscheck OK.

## W325 identity pass — Ace/Izanagi (2026-11-05)

### IDENTITY LIST
- 갈색 상부 덮개와 백청색 대각 띠
- 청록색 총몸·실린더
- 은청색 실린더 창과 방아쇠울
- 앞쪽 매달린 고리
- 갈색 그립의 십자 메달·밝은 굽

- 요소 105 → 105 (body 92, magazine 13). T=24, atlas=[1024, 512].
- 주요 실루엣 유지. 상부 덮개의 체결 띠·리벳, 청록 패널 윤곽, 앞쪽 핀의 받침, 그립 체크·메달 각인과 해머 요철을 페인트했다.
- 모든 노출 면에 flat 소재색·1texel 밝은 윗변/어두운 아랫변을 special()로 작성했다. 투영 노이즈는 사용하지 않는다. east/west 글자 방향은 각각 보정했다.
- T20/512에서 atlas overflow가 발생했다. 근접 그립/각인/후면 픽셀을 확보하려 T24와 1024x512(빈 행 crop)를 선택했다.
- 검증: kit build/JSON/PNG 출력, adscheck OK, west/east/top/q/front 5방향 오프라인 렌더 및 원본 비교. 비회전 요소의 동일 방향 coplanar overlap 0개.
- 미검증: 실제 Minecraft 1P/3P/ADS/장전·손 접촉·10–20개 표시 성능·팩 로드. 오프라인 결과를 인게임 수락으로 보고하지 않는다.
- 원본: 해당 proj_cache의 rip side views와 /tmp/w325-rips/ballyhoo_mk_27/src. 기준: main checkout Ace 87 elements/512², Izanagi 79 elements/512² 및 /tmp/w325-ref-ace-izanagi.png.
- 최종 정면 보완: 총구 안쪽을 가리던 외장 부피를 분할 제거하여 실제 recessed bore를 확보했다. 모든 총구의 중심 ray에서 앞쪽 차폐 0개. Ballyhoo는 기존 bore가 열려 있어 형상 유지. Azimuth는 돌출 튜브도 관통 공간과 recessed plug로 재구성했다.

## W325 MATERIAL pass (2026-11-05, 이전 flat-paint 외관 대체)

- 기준: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, W123 Gnawing Hunger paint_tile와 Beloved Paint.tile을 읽고 비교했다.
- STYLE=material, T20. 기하·탄창 분리·조준선 계약은 material_geometry_baseline.json과 동일하다.
- 재질(키 → kind / RGB):
  - blue_steel → steel / (171, 199, 202)
  - brown_shell → metal / (86, 77, 66)
  - dark_steel → metal / (57, 60, 59)
  - grip → polymer / (44, 34, 28)
  - recess → dark / (15, 18, 19)
  - sight → polymer / (26, 29, 30)
  - silver → steel / (177, 184, 184)
  - teal → paint / (54, 86, 91)
  - teal_drum → metal / (59, 93, 96)
- special()에 남긴 표현: 백청색 대각 띠, 덮개 체결선·리벳, 그립 메달 각인. 전체 면 단색 채움·일괄 테두리·인공 그립 체크는 제거했다.
- 재질 바탕은 원본 색을 기준으로 소재별 금속 결·도장 입자·고무 교차 패턴·폴리머 요철을 구분한다. 원본 투영은 표면 명암만 사용하며 실제 PBR/반사 셰이더는 아니다.
- 늘어짐 방지: 앞/뒤 끝면, 기울어진 그립·후방 프레임·stock/tang 면은 detail=0. 위/아래는 detail<=0.25.
- 검증: build 및 adscheck OK, geometry unchanged, atlas [1024, 512], 105요소 유지. west/east/top/q/front 렌더 생성·검토.
- 실제 Minecraft 1P/ADS/장전·팩 로드·성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.

## W325 MATERIAL R2 pass (2026-11-05)

- 재배정: 갈색 하부 shell을 금속, frame_front를 밝은 청록 steel로 분리; 청록 도장은 외피에 유지.
- 세부 모티브: 리벳과 앞쪽 핀 아래 가는 세로선. 전체 면 채움으로 금속을 가리지 않고 가는 선·점 중심으로 작성했다.
- 금속/도장/폴리머/고무 구분, 원본 색 기반 마모색, plate 경계와 이음선을 사용했다. 투영 부적합 끝면·그립·상하면의 source-wear는 껐다.
- 검증: 최종 kit build/5방향 오프라인 render 완료. 형상 기준선과 완전 동일, 105요소, T20, atlas 1024×512 유지. R2 ADS 수학 검사 OK 후 최종 변경은 텍스처만 적용했다.
- 실제 Minecraft 1P/3P/ADS/장전·팩 로드·10–20개 표시 성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.
