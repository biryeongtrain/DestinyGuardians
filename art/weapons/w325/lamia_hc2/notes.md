# Lamia HC2 (rare, Adaptive Omolon hand cannon) — W325 skin over austringer

- Identity kept: maroon two-tier Omolon slab (Omolon logo, rings, perforated light vent band), green energy cell in the
  frame window, real gap between the upper barrel block and the lower front block (red/blue status lights), red frame with
  light trim, red trigger-guard loop (real opening), dark stippled grip panel in a red front strap, finger hook at the toe.
- Elements: body 16, magazine (energy cell) 2 = 18. Atlas 512x512, T 16.
- Calibration: cell centre (nx img 149,59.5) -> z 3.40, y 12.10; 40 px/m, SX 38; barrel block ahead of img x 185 stretched
  1.10x -> muzzle -5.66 (base -6.32); grip bottom 6.6 (base 6.29).
- Deviation: the Lamia cell sits much further forward of its grip than the austringer cylinder, so the cell centre is
  0.94 px ahead / 0.33 px below the base moving-leaf centre (z 1.85..4.95 vs base 2.82..5.86) and the grip front strap is
  ~0.5 px behind the base; check the reload swing of the cell in game.
- Top slab lowered 14.22 -> 13.92 (texture squashed 1.4x in that band); rear-sight ears 14.10 at the rip rear sight (z 6.0..7.2,
  behind the base notch z 4.95..5.5). Grip + rear body squeezed horizontally to 0.8 behind the front strap.
- Not verified: in-game first person / ADS eye line / reload; projection checked only in offline renders.

## W325 detail + style pass (2026-11-05)
- Elements 18 -> body 92 + magazine 13 = 105; atlas 512x512 (pixel STYLE, PALETTE 14-16).
- DMW/W30 style: long slabs split into machined segments (hc.slab: core + side plates = 1-step chamfer, recessed grooves),
  end caps, real muzzle bores, window rims, bolts, notch rear sight + front blade, octagonal banded cylinder (mag_drum*),
  rounded trigger-guard corners. Faces painted as flat rip-colour blocks + decals (hc.Painter, rip-image px), kit draws bevel lines.
- ADS: hc.ads_clip clips every body element to the base top profile (mirror of kit adscheck); kit adscheck = OK.
  Clipped parts are grip/tang/rear-stock tops behind the hammer (z > ~6), i.e. behind the rear sight, none on the eye line.
- Magazine part ids renamed mag_core/mag_side -> mag_drum_*/mag_core (still mag_ prefix = parts.magazine); box within base moving leaf as before.
- Not verified: in-game 1P/ADS/reload Vision.

## Clean-geometry pass (Chattering Bone negative reference)
- grip side panels (23.7 deg) now share the core rake (21.2 deg), flush on the core sides.
- Coplanar overlapping faces (z-fighting) removed by hc.deconflict (0 left); cylinder core no longer shares end planes with its bands.
- Elements now body 92 + magazine 13 = 105; adscheck OK.

## W325 identity pass — Ace/Izanagi (2026-11-05)

### IDENTITY LIST
- 적갈색 Omolon 외장
- 황갈색 타공 띠
- 연결된 두 고리 문양과 OMOLON 글자
- 녹회색 에너지 셀
- 청색·적색 상태등
- 검정 그립 패널

- 요소 105 → 119 (body 106, magazine 13). T=20, atlas=[512, 512].
- 주요 실루엣 유지. 3열 타공 띠·이중 고리·읽을 수 있는 OMOLON 글자·후방 원형 문양·상태등·셀 홈을 면별 페인트했다. 후방 문양은 ADS 보정으로 낮아진 표면 안쪽에 배치했다.
- 모든 노출 면에 flat 소재색·1texel 밝은 윗변/어두운 아랫변을 special()로 작성했다. 투영 노이즈는 사용하지 않는다. east/west 글자 방향은 각각 보정했다.
- 검증: kit build/JSON/PNG 출력, adscheck OK, west/east/top/q/front 5방향 오프라인 렌더 및 원본 비교. 비회전 요소의 동일 방향 coplanar overlap 0개.
- 미검증: 실제 Minecraft 1P/3P/ADS/장전·손 접촉·10–20개 표시 성능·팩 로드. 오프라인 결과를 인게임 수락으로 보고하지 않는다.
- 원본: 해당 proj_cache의 rip side views와 /tmp/w325-rips/lamia_hc2/src. 기준: main checkout Ace 87 elements/512², Izanagi 79 elements/512² 및 /tmp/w325-ref-ace-izanagi.png.
- 최종 정면 보완: 총구 안쪽을 가리던 외장 부피를 분할 제거하여 실제 recessed bore를 확보했다. 모든 총구의 중심 ray에서 앞쪽 차폐 0개. Ballyhoo는 기존 bore가 열려 있어 형상 유지. Azimuth는 돌출 튜브도 관통 공간과 recessed plug로 재구성했다.

## W325 MATERIAL pass (2026-11-05, 이전 flat-paint 외관 대체)

- 기준: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, W123 Gnawing Hunger paint_tile와 Beloved Paint.tile을 읽고 비교했다.
- STYLE=material, T20. 기하·탄창 분리·조준선 계약은 material_geometry_baseline.json과 동일하다.
- 재질(키 → kind / RGB):
  - blue_lamp → glow / (51, 159, 194)
  - cell → metal / (92, 112, 98)
  - dark_steel → metal / (57, 60, 59)
  - maroon → paint / (107, 62, 57)
  - recess → dark / (15, 18, 19)
  - red_lamp → glow / (204, 43, 45)
  - rubber → rubber / (35, 37, 36)
  - sight → polymer / (26, 29, 30)
  - warm_alloy → steel / (184, 170, 142)
- special()에 남긴 표현: 황갈색 타공 띠, Omolon 고리·글자·후방 문양, 상태등 하이라이트. 전체 면 단색 채움·일괄 테두리·인공 그립 체크는 제거했다.
- 재질 바탕은 원본 색을 기준으로 소재별 금속 결·도장 입자·고무 교차 패턴·폴리머 요철을 구분한다. 원본 투영은 표면 명암만 사용하며 실제 PBR/반사 셰이더는 아니다.
- 늘어짐 방지: 앞/뒤 끝면, 기울어진 그립·후방 프레임·stock/tang 면은 detail=0. 위/아래는 detail<=0.25.
- 검증: build 및 adscheck OK, geometry unchanged, atlas [512, 512], 119요소 유지. west/east/top/q/front 렌더 생성·검토.
- 실제 Minecraft 1P/ADS/장전·팩 로드·성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.

## W325 MATERIAL R2 pass (2026-11-05)

- 재배정: barrel_block/lower_tail/muzzle을 따뜻한 steel, frame_mid/cell/guard를 적갈색 metal로 분리.
- 세부 모티브: 가는 타공열, 적색 외피 안쪽 연결 링과 OMOLON 문자. 전체 면 채움으로 금속을 가리지 않고 가는 선·점 중심으로 작성했다.
- 금속/도장/폴리머/고무 구분, 원본 색 기반 마모색, plate 경계와 이음선을 사용했다. 투영 부적합 끝면·그립·상하면의 source-wear는 껐다.
- 검증: 최종 kit build/5방향 오프라인 render 완료. 형상 기준선과 완전 동일, 119요소, T20, atlas 512×512 유지. R2 ADS 수학 검사 OK 후 최종 변경은 텍스처만 적용했다.
- 실제 Minecraft 1P/3P/ADS/장전·팩 로드·10–20개 표시 성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.
