# Guseva-C (rare, Aggressive Hakke hand cannon) — W325 skin over duke_mk_44

- Identity kept: white "glass"-finish Hakke shroud (HAKKE lettering, olive panels), orange top strap and sloped orange
  stock top with red ++ marking, dark square cylinder in a light frame window, toothed bottom rail, hanging front peg, side
  flashlight with blue lens (rip +x side = model west), dark trigger group with real guard opening, brown raked grip.
- Elements: body 25, magazine (cylinder) 2 = 27. Atlas 512x512, T 16.
- Calibration: rip cylinder centre (nx img 142,59) -> duke cylinder centre z 3.77 y 12.80; 39 px/m, SX 38 (cylinder
  z 2.36..5.09 vs duke moving 2.30..5.24). Shroud ahead of img x 175 compressed 0.94x -> muzzle -6.22 (base -6.17).
- Fits: top rail clamped 14.95 -> 14.88 under the duke sight line; rear-sight ears to ~14.78 at z ~3.4..4.2; grip + rear
  stock squeezed horizontally to 0.85 behind the front strap (rip grip is much wider/more raked than the duke's).
- Flashlight reaches x 6.1 (base min x 6.38): check it does not clip the first-person camera/hand.
- Not verified: in-game first person / ADS / reload; offline renders only.

## W325 detail + style pass (2026-11-05)
- Elements 27 -> body 90 + magazine 7 = 97; atlas 512x512 (pixel STYLE, PALETTE 14-16).
- DMW/W30 style: long slabs split into machined segments (hc.slab: core + side plates = 1-step chamfer, recessed grooves),
  end caps, real muzzle bores, window rims, bolts, notch rear sight + front blade, octagonal banded cylinder (mag_drum*),
  rounded trigger-guard corners. Faces painted as flat rip-colour blocks + decals (hc.Painter, rip-image px), kit draws bevel lines.
- ADS: hc.ads_clip clips every body element to the base top profile (mirror of kit adscheck); kit adscheck = OK.
  Clipped parts are grip/tang/rear-stock tops behind the hammer (z > ~6), i.e. behind the rear sight, none on the eye line.
- Magazine part ids renamed mag_core/mag_side -> mag_drum_*/mag_core (still mag_ prefix = parts.magazine); box within base moving leaf as before.
- Not verified: in-game 1P/ADS/reload Vision.

## Clean-geometry pass (Chattering Bone negative reference)
- 29.6 deg orange stock slope slab -> two flush axis-aligned steps; grip upper/lower/base -> one 17.8 deg rake; hidden bolt under the flashlight removed.
- Coplanar overlapping faces (z-fighting) removed by hc.deconflict (0 left); cylinder core no longer shares end planes with its bands.
- Elements now body 92 + magazine 7 = 99; adscheck OK.

## W325 identity pass — Ace/Izanagi (2026-11-05)

### IDENTITY LIST
- 백색 HAKKE 외장·올리브 패널
- 주황 상부 스트랩·계단 후방
- 붉은 이중 십자 표시
- 짙은 각진 실린더
- 측면 청색 렌즈 손전등
- 하부 톱니 레일과 앞쪽 핀
- 갈색 요철 그립

- 요소 99 → 106 (body 99, magazine 7). T=24, atlas=[1024, 512].
- 주요 실루엣 유지. HAKKE를 실제 픽셀 글자로, 후방 표시를 선명한 이중 십자로 그렸다. 올리브 패널 윤곽·하부 사각 표시·청색 렌즈 하이라이트·손전등 리브·그립 체크를 페인트했다.
- 모든 노출 면에 flat 소재색·1texel 밝은 윗변/어두운 아랫변을 special()로 작성했다. 투영 노이즈는 사용하지 않는다. east/west 글자 방향은 각각 보정했다.
- T20/512에서 atlas overflow가 발생했다. 근접 그립/각인/후면 픽셀을 확보하려 T24와 1024x512(빈 행 crop)를 선택했다.
- 검증: kit build/JSON/PNG 출력, adscheck OK, west/east/top/q/front 5방향 오프라인 렌더 및 원본 비교. 비회전 요소의 동일 방향 coplanar overlap 0개.
- 미검증: 실제 Minecraft 1P/3P/ADS/장전·손 접촉·10–20개 표시 성능·팩 로드. 오프라인 결과를 인게임 수락으로 보고하지 않는다.
- 원본: 해당 proj_cache의 rip side views와 /tmp/w325-rips/guseva_c/src. 기준: main checkout Ace 87 elements/512², Izanagi 79 elements/512² 및 /tmp/w325-ref-ace-izanagi.png.
- 최종 정면 보완: 총구 안쪽을 가리던 외장 부피를 분할 제거하여 실제 recessed bore를 확보했다. 모든 총구의 중심 ray에서 앞쪽 차폐 0개. Ballyhoo는 기존 bore가 열려 있어 형상 유지. Azimuth는 돌출 튜브도 관통 공간과 recessed plug로 재구성했다.

## W325 MATERIAL pass (2026-11-05, 이전 flat-paint 외관 대체)

- 기준: /tmp/w325-mat-game.png, /tmp/w325-mat-tex.png, W123 Gnawing Hunger paint_tile와 Beloved Paint.tile을 읽고 비교했다.
- STYLE=material, T20. 기하·탄창 분리·조준선 계약은 material_geometry_baseline.json과 동일하다.
- 재질(키 → kind / RGB):
  - alloy → steel / (176, 185, 174)
  - brown_grip → polymer / (59, 44, 33)
  - dark_steel → metal / (57, 60, 59)
  - drum → metal / (53, 48, 40)
  - lens → lens / (64, 132, 171)
  - light → metal / (43, 48, 44)
  - orange → paint / (209, 94, 59)
  - recess → dark / (15, 18, 19)
  - sight → polymer / (26, 29, 30)
  - white_enamel → paint / (215, 217, 204)
- special()에 남긴 표현: 올리브 색띠, HAKKE 글자, 붉은 이중 십자, 렌즈 고리·반사점. 전체 면 단색 채움·일괄 테두리·인공 그립 체크는 제거했다.
- 재질 바탕은 원본 색을 기준으로 소재별 금속 결·도장 입자·고무 교차 패턴·폴리머 요철을 구분한다. 원본 투영은 표면 명암만 사용하며 실제 PBR/반사 셰이더는 아니다.
- 늘어짐 방지: 앞/뒤 끝면, 기울어진 그립·후방 프레임·stock/tang 면은 detail=0. 위/아래는 detail<=0.25.
- 검증: build 및 adscheck OK, geometry unchanged, atlas [1024, 512], 106요소 유지. west/east/top/q/front 렌더 생성·검토.
- 실제 Minecraft 1P/ADS/장전·팩 로드·성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.

## W325 MATERIAL R2 pass (2026-11-05)

- 재배정: 측판·후방/window 프레임·grip_stock을 steel, 실린더를 metal로 분리; 백색 코어·주황 상부 도장 유지.
- 세부 모티브: 손전등 가는 리브선, HAKKE 문자, 붉은 후방 표시. 전체 면 채움으로 금속을 가리지 않고 가는 선·점 중심으로 작성했다.
- 금속/도장/폴리머/고무 구분, 원본 색 기반 마모색, plate 경계와 이음선을 사용했다. 투영 부적합 끝면·그립·상하면의 source-wear는 껐다.
- 검증: 최종 kit build/5방향 오프라인 render 완료. 형상 기준선과 완전 동일, 106요소, T20, atlas 1024×512 유지. R2 ADS 수학 검사 OK 후 최종 변경은 텍스처만 적용했다.
- 실제 Minecraft 1P/3P/ADS/장전·팩 로드·10–20개 표시 성능은 미검증. 커밋/Gradle/Minecraft 실행 없음.
