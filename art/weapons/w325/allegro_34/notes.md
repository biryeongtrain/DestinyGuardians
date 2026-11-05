# Allegro-34 (rare, Adaptive hand cannon) — W325 skin over austringer

- Identity kept: long olive/grey slab shroud with two light top slots and side vent row, white frame around a rounded-square
  cylinder, round white hammer + light beavertail, dark lower frame block, white trigger-guard loop (real opening), chunky dark grip with heel flare.
- Elements: body 26, magazine (cylinder) 2 = 28. Atlas 512x512, T 16. hc.py = shared authoring helpers (image-px -> model px).
- Calibration: rip cylinder centre (nx img 140,56.5) -> austringer cylinder centre z 4.34 y 12.43; 36 px/m along, 38 px/m lateral.
  Cylinder z 3.08..5.60 sits inside the base moving leaf box (2.82..5.86, centre y 12.43) so the reload swing lines up.
- Fits: top strap lowered to 13.92 and shroud to 13.80 (rip 14.30/13.94) under the austringer sight line; rear-sight ears
  x<=7.72 / >=8.28 up to 14.10 at z ~5.1..5.7 (green dots projected from the rip); W148 overlay dot kept (no NO_OVERLAY).
  Grip squeezed to 0.7 of the rip thickness about the front strap (front strap coincides with the base, back stays <= base butt);
  beavertail shortened 8.62 -> 8.10. Muzzle -6.46 (base -6.32).
- Not verified: in-game first person / ADS eye line / reload swing / lighting; projection only checked in offline renders.

## W325 detail + style pass (2026-11-05)
- Elements 28 -> body 105 + magazine 13 = 118; atlas 512x512 (pixel STYLE, PALETTE 14-16).
- DMW/W30 style: long slabs split into machined segments (hc.slab: core + side plates = 1-step chamfer, recessed grooves),
  end caps, real muzzle bores, window rims, bolts, notch rear sight + front blade, octagonal banded cylinder (mag_drum*),
  rounded trigger-guard corners. Faces painted as flat rip-colour blocks + decals (hc.Painter, rip-image px), kit draws bevel lines.
- ADS: hc.ads_clip clips every body element to the base top profile (mirror of kit adscheck); kit adscheck = OK.
  Clipped parts are grip/tang/rear-stock tops behind the hammer (z > ~6), i.e. behind the rear sight, none on the eye line.
- Magazine part ids renamed mag_core/mag_side -> mag_drum_*/mag_core (still mag_ prefix = parts.magazine); box within base moving leaf as before.
- Not verified: in-game 1P/ADS/reload Vision.

## Clean-geometry pass (Chattering Bone negative reference)
- grip core/butt/side panels on one 22.7 deg rake line (butt was a separate 12.7 deg slab, panels poked out); 20 deg trigger tip, 45 deg hammer hub and guard nose replaced by flush axis-aligned steps.
- Coplanar overlapping faces (z-fighting) removed by hc.deconflict (0 left); cylinder core no longer shares end planes with its bands.
- Elements now body 105 + magazine 13 = 118; adscheck OK.

## W325 identity pass — Ace/Izanagi (2026-11-05)

### IDENTITY LIST
- 올리브 상부와 회색 긴 외장
- 백색 가로 슬롯 두 개
- 하부 이중 통풍공 열
- 백색 실린더 창·해머·방아쇠울
- 검정 요철 그립

- 요소 118 → 125 (body 112, magazine 13). T=24, atlas=[1024, 512].
- 주요 실루엣 유지. 이중 통풍공, 슬롯 테두리, 올리브 원형 핀, 하부 패널선, 해머 원형 각인, 그립 체크와 실린더 홈을 페인트했다.
- 모든 노출 면에 flat 소재색·1texel 밝은 윗변/어두운 아랫변을 special()로 작성했다. 투영 노이즈는 사용하지 않는다. east/west 글자 방향은 각각 보정했다.
- 검증: kit build/JSON/PNG 출력, adscheck OK, west/east/top/q/front 5방향 오프라인 렌더 및 원본 비교. 비회전 요소의 동일 방향 coplanar overlap 0개.
- 미검증: 실제 Minecraft 1P/3P/ADS/장전·손 접촉·10–20개 표시 성능·팩 로드. 오프라인 결과를 인게임 수락으로 보고하지 않는다.
- 원본: 해당 proj_cache의 rip side views와 /tmp/w325-rips/allegro_34/src. 기준: main checkout Ace 87 elements/512², Izanagi 79 elements/512² 및 /tmp/w325-ref-ace-izanagi.png.
- 최종 정면 보완: 총구 안쪽을 가리던 외장 부피를 분할 제거하여 실제 recessed bore를 확보했다. 모든 총구의 중심 ray에서 앞쪽 차폐 0개. Ballyhoo는 기존 bore가 열려 있어 형상 유지. Azimuth는 돌출 튜브도 관통 공간과 recessed plug로 재구성했다.
- 총구 cavity 추가 후 T20/512가 518행으로 넘쳐 T24/1024x512로 변경했다.

## W325 MATERIAL pass (2026-11-05, 이전 flat-paint 외관 대체)

- 기준: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, W123 Gnawing Hunger paint_tile와 Beloved Paint.tile을 읽고 비교했다.
- STYLE=material, T20. 기하·탄창 분리·조준선 계약은 material_geometry_baseline.json과 동일하다.
- 재질(키 → kind / RGB):
  - black_polymer → polymer / (47, 49, 46)
  - dark_steel → metal / (57, 60, 59)
  - drum → metal / (77, 79, 74)
  - fastener → steel / (131, 141, 140)
  - frame → metal / (52, 53, 49)
  - olive → paint / (86, 102, 55)
  - recess → dark / (15, 18, 19)
  - rubber → rubber / (35, 37, 36)
  - shell → steel / (159, 165, 157)
  - shroud → metal / (64, 65, 61)
  - sight → polymer / (26, 29, 30)
  - silver → steel / (177, 184, 184)
  - white → steel / (210, 215, 204)
- special()에 남긴 표현: 백색 슬롯, 이중 통풍공, 올리브 사선 띠, 해머 고리, 핀 각인. 전체 면 단색 채움·일괄 테두리·인공 그립 체크는 제거했다.
- 재질 바탕은 원본 색을 기준으로 소재별 금속 결·도장 입자·고무 교차 패턴·폴리머 요철을 구분한다. 원본 투영은 표면 명암만 사용하며 실제 PBR/반사 셰이더는 아니다.
- 늘어짐 방지: 앞/뒤 끝면, 기울어진 그립·후방 프레임·stock/tang 면은 detail=0. 위/아래는 detail<=0.25.
- 검증: build 및 adscheck OK, geometry unchanged, atlas [1024, 512], 125요소 유지. west/east/top/q/front 렌더 생성·검토.
- 실제 Minecraft 1P/ADS/장전·팩 로드·성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.

## W325 MATERIAL R2 pass (2026-11-05)

- 재배정: receiver/frame와 실린더를 노출 금속으로 분리; 올리브 도장은 상부 외피에 유지.
- 세부 모티브: 실린더 이중 타공열, 가는 슬롯, 해머 링. 전체 면 채움으로 금속을 가리지 않고 가는 선·점 중심으로 작성했다.
- 금속/도장/폴리머/고무 구분, 원본 색 기반 마모색, plate 경계와 이음선을 사용했다. 투영 부적합 끝면·그립·상하면의 source-wear는 껐다.
- 검증: 최종 kit build/5방향 오프라인 render 완료. 형상 기준선과 완전 동일, 125요소, T20, atlas 1024×512 유지. R2 ADS 수학 검사 OK 후 최종 변경은 텍스처만 적용했다.
- 실제 Minecraft 1P/3P/ADS/장전·팩 로드·10–20개 표시 성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.
