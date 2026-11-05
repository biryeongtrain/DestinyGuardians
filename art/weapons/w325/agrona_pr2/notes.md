# Agrona PR2 (W325, rare, Lightweight pulse) over chattering_bone

- Identity kept: teal/ice Omolon stubby body, white front tube + grey OMOLON barrel shroud over a real through gap,
  receiver S-curve hump and dotted vent, black side hoses (proud bars both sides), long raked grip, skeletal
  battery-cell magazine (real window + cable), white stock tube under a tapered stock, dark butt pad, tall box scope.
- Elements: body 33 + magazine 5 = 38. Atlas 512x512, T 16. Low count because the rip is mostly large flat volumes.
- Map: non-uniform 30 px/m along the length, 26 px/m across (width x1.07): rip is 0.77 m long but very tall; this
  1.15 stretch brings receiver height (~3 px) and length near the base while keeping the Omolon block shapes.
  Whole model shifted +0.6 z: grip top z 7.0-8.6 / trigger 6.2-6.4 vs base grip ~7.7-9.6; magazine z 10.5-12.5 vs
  base moving magazine 10.8-13.3. Muzzle -5.45 (base -8.66): rip's short nose kept, not stretched.
- Scope moved 2.0 px forward and 0.13 up (part transform), hollow box z 3.4-8.55 with a 0.8 px aperture centred x 8 /
  y 12.93 (chattering_bone W151 pin tip 12.93). Box ends painted dark; W148 overlay dot kept.
- Known: the OMOLON decal is mirrored on the right side exactly as in the rip. Not verified in game.

## W325 detail + style pass (2026-11-05)
- Elements: 38 -> body 120 + magazine 7 = 127 (atlas 512x512).
- Style: Dead Man Walking break-up (machined(): long slabs split into segments with engraved joint seams), chamfered
  silhouette edges (chbox), rails with teeth, ribs, vents, separate panels; kit STYLE 'pixel' palette bake + Painter
  flat colours where the projection smeared.
- ADS: kit.py adscheck OK. tall rip scope replaced by a compact hollow box (sight_*) inside chattering_bone's hood envelope (z 6.85-8.12, top 13.5), aperture centred y 13.0.
- Contract (grip, trigger, magazine box/part ids, muzzle) unchanged from the first pass.
- Not verified in game after this pass (offline Blender renders only).

## W325 cleanup pass vs the Chattering Bone negative reference (2026-11-05)
- Elements now body 133 + magazine 7 = 140; adscheck OK.
- Fixed: (chattering_bone base) vent ramp + hump merged into one ramp; 6.7 deg stock wedge + cap replaced by 4 axis-aligned chamfered comb steps; grip panel/backstrap/foot on one grip axis; hose clamps on the hose axis; trigger guard parts meet without overlap.
- All designs end with dezfight(): coplanar overlapping faces are pulled 0.012 px inward (no z-fight slivers).
- Remaining checker hits are deliberate proud side panels on the same axis and angled grip/magazine meeting the body.

## W325 identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST
- 짙은 청록색 총몸과 흰색 전방 튜브
- 회색 튜브의 청록 OMOLON 및 스톡의 작은 흰 OMOLON 표기
- 밝은 테두리의 중앙 관통 개구부
- 총몸 측면의 검정 호스·은색 클램프
- 빈 배터리 프레임 탄창과 청록 셀·금속 접점
- 열린 청록 박스 조준경과 하늘색 측면 발광부

- 입체 변경: 중앙 총몸을 앞/뒤/위/아래/계단 부분으로 나누어 실제 관통 창 생성. 스톡의 두께 0 요소 제거.
- 페인트: 모든 노출 면을 `special()`로 직접 칠함. 부품별 단색, 실제 1텍셀 상단 하이라이트/하단 이음선, 원본 기반 패널선·핀·손잡이 스티플·상기 고유 표식. 투영 얼룩/무작위 노이즈 없음.
- 밀도/아틀라스: T20. kit build의 1024×512 작업 아틀라스를 `art/weapons/w325/lost_and_found/identity_pack.py <id>`로 손실 없이 512×512로 재배치. 중복 UV 섬만 공유하고 모든 면 RGBA를 정확히 비교함. 재빌드 후 반드시 이 재배치 단계를 실행.
- `identity_geometry.py`: 서로 다른 피벗/회전까지 월드 평면에서 비교하고 겹친 작은 면을 0.009px 안쪽으로 정리. 같은 방향 공면 겹침 0건(평면 1e-5, 투영 면적 0.0002 기준). 반대 방향으로 맞닿는 정상 접합면은 제외.
- 검토: kit build, ADS profile OK, west/east/top/q/front 오프라인 Blender 렌더. `review/identity_checks.json`, `review/*_compare.png`에 근거 보관.
- 미검증: 실제 Minecraft 1/3인칭, ADS 화면, 분리 장전, 10~20개 표시 및 FPS. 원본 PBR·마모는 Minecraft에 맞는 제한된 색과 선으로 해석했으며 원본과 정밀 동등하다고 주장하지 않음.
- 최종 출력: 140 → 141요소 (본체 134 + 탄창 7), PNG 12,942바이트.

## W325 MATERIAL pass (2026-11-05) — 이전 flat-paint 외관 대체

- W123 Gnawing Hunger / Beloved의 재질 및 페인트 코드, 제공된 인게임/아틀라스 이미지를 비교. 아래 재질은 원본 외관 기반의 RGBA 재해석이며 원본 PBR을 복구한 결과는 아님.
- `STYLE=material`; 전체 면을 채우던 flat special()은 최종 경로에서 제거. 각 부품을 도장·브러시드 금속·폴리머·고무 등으로 명시 분리.
- 재질 매핑 (RGB):
  - `teal_enamel` → `paint` / `(43, 78, 86)`
  - `white_ceramic` → `paint` / `(184, 204, 211)`
  - `gunmetal` → `metal` / `(55, 64, 65)`
  - `steel` → `steel` / `(143, 172, 183)`
  - `polymer` → `polymer` / `(65, 61, 57)`
  - `rubber` → `rubber` / `(28, 31, 31)`
  - `recess` → `dark` / `(18, 27, 31)`
  - `lens` → `lens` / `(41, 94, 111)`
  - `cell_glow` → `glow` / `(94, 174, 187)`
  - `contact` → `steel` / `(170, 186, 163)`
- special(): OMOLON 글자, 측면 발광부·배터리 셀의 작은 반사점, 조준경 다이얼 링만 유지.
- 투영: 5×5 지점의 원본 유효 coverage가 60% 미만인 면, 끝면, 얇은 챔퍼는 detail=0. 재질 결/음영은 유지. 현재 전체 출력 면 중 587면은 이 경로이며 숨겨진 면도 포함한 수치. 아그로나 중앙 후방 판은 실제 호스와 원본 호스 실루엣 중복을 피하려고 추가로 detail=0 처리.
- 출력: 141요소 그대로. 지오메트리 SHA-256 동일 확인. T20, 최종 아틀라스 512×512, PNG 198,574바이트.
- 재현: kit build 후 `art/weapons/w325/lost_and_found/identity_pack.py <id>` 실행. 재배치는 면별 RGBA 그대로 유지. `material_review.py`로 비교 이미지 재생성.
- 확인: ADS OK, 같은 방향 공면 겹침 0, 파트/기하 불변, 출력 해시, west/east/top/q/front 오프라인 렌더. 실제 Minecraft·팩 로드·파지·장전·FPS는 미실행.

## Material R2 (2026-11-05)

흰 튜브·리시버 창 패널·프레임·가드·개머리 트림을 밝은 강철로 분리. 청록 도색과 고무 호스 유지.

수작업 모티프: OMOLON 각인과 리시버 창 패널의 1텍셀 고정점·짧은 슬롯. 폴리머/고무 기본 명도 차이 40.86.

형상 해시 불변, 아틀라스 [512, 512], 겹침 0, ADS OK, 출력 해시 확인. kit.py 수정 없음. Blender 5시점 렌더 확인용이며 Minecraft 검수 아님.
