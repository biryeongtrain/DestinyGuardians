# Lost and Found (W325, common, Rapid-Fire pulse) over claws_of_the_wolf

- Identity kept: tan bullpup thumbhole stock with dark swept cheek piece, magazine behind the raked pistol grip,
  dark slotted handguard with tan collar, upper gas tube with a through slot, gas block ramp, mini tube sight.
- Elements: body 53 + magazine 2 = 55 (11 rotated). Atlas 512x512, T 16. Real holes: thumbhole, tube slot,
  trigger guard loop, recessed handguard slots and right-side ejection port.
- Map: uniform 27.73 px/m (rip butt -> z 16.8, muzzle lands -8.65), width x1.2 (rip receiver ~1.2 px wide).
- Contract fit: grip top z 6.5-8.3 / trigger z 5.9-6.05 vs base grip 7.0-8.9 / trigger ~6.2; magazine z 10.1-12.9
  (base moving magazine 9.7-12.9), longer than the base (bottom y 4.9 vs 6.4) by design (rip proportions).
- Sight: rip mini tube lowered 0.22 px (part transform in model2world) so its 0.54 px aperture is centred on the base
  ADS line x 8 / y 12.5 at z 3.45-4.62 (base W151 front pin z 4.15, tip 12.46); nothing behind it rises above y 12.3.
  W148 overlay dot kept (NO_OVERLAY False); tube ends painted plain dark (special).
- Not verified: in-game first person, ADS framing, reload alignment, lighting in Minecraft (offline Blender renders only).

## W325 detail + style pass (2026-11-05)
- Elements: 55 -> body 136 + magazine 6 = 142 (atlas 512x512).
- Style: Dead Man Walking break-up (machined(): long slabs split into segments with engraved joint seams), chamfered
  silhouette edges (chbox), rails with teeth, ribs, vents, separate panels; kit STYLE 'pixel' palette bake + Painter
  flat colours where the projection smeared.
- ADS: kit.py adscheck OK. tube sight is now only the hollow ring (z 4.05-5.22) + low foot; the sight_housing block behind it was removed (in-game ADS: it filled the screen centre). Rear lowered/narrowed: receiver top 11.70, cheek 11.6, top bar/butt 11.42/10.98, stock half-width 0.62 (was 0.86, base stock is 1.2 px wide).
- Contract (grip, trigger, magazine box/part ids, muzzle) unchanged from the first pass.
- Not verified in game after this pass (offline Blender renders only).

## W325 cleanup pass vs the Chattering Bone negative reference (2026-11-05)
- Elements now body 138 + magazine 6 = 144; adscheck OK.
- Fixed: grip panel/backstrap/base now share the grip's exact axis (were 1.3-8 deg off and crossing); 14 deg stock belly slab + wrist replaced by a 4-block axis-aligned step belly; slanted magazine plate -> flat plate.
- All designs end with dezfight(): coplanar overlapping faces are pulled 0.012 px inward (no z-fight slivers).
- Remaining checker hits are deliberate proud side panels on the same axis and angled grip/magazine meeting the body.

## W325 identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST
- 황갈색 불펍 총몸과 엄지 구멍 스톡
- 짙은 녹회색 긴 칙패드·홈 난 전방 손잡이
- 드러난 상부 가스관과 관통 슬롯
- 총구 브레이크의 실제 포트
- 작은 열린 튜브 조준경
- 그립 뒤의 세로 리브 탄창

- 입체 변경: 기존 포트/튜브 개구부/썸홀/조준경/레일/탄창 입체를 유지. 추가 큐브 없이 리브·패널 재질 대비를 살림.
- 페인트: 모든 노출 면을 `special()`로 직접 칠함. 부품별 단색, 실제 1텍셀 상단 하이라이트/하단 이음선, 원본 기반 패널선·핀·손잡이 스티플·상기 고유 표식. 투영 얼룩/무작위 노이즈 없음.
- 밀도/아틀라스: T20. kit build의 1024×512 작업 아틀라스를 `art/weapons/w325/lost_and_found/identity_pack.py <id>`로 손실 없이 512×512로 재배치. 중복 UV 섬만 공유하고 모든 면 RGBA를 정확히 비교함. 재빌드 후 반드시 이 재배치 단계를 실행.
- `identity_geometry.py`: 서로 다른 피벗/회전까지 월드 평면에서 비교하고 겹친 작은 면을 0.009px 안쪽으로 정리. 같은 방향 공면 겹침 0건(평면 1e-5, 투영 면적 0.0002 기준). 반대 방향으로 맞닿는 정상 접합면은 제외.
- 검토: kit build, ADS profile OK, west/east/top/q/front 오프라인 Blender 렌더. `review/identity_checks.json`, `review/*_compare.png`에 근거 보관.
- 미검증: 실제 Minecraft 1/3인칭, ADS 화면, 분리 장전, 10~20개 표시 및 FPS. 원본 PBR·마모는 Minecraft에 맞는 제한된 색과 선으로 해석했으며 원본과 정밀 동등하다고 주장하지 않음.
- 최종 출력: 144 → 144요소 (본체 138 + 탄창 6), PNG 11,579바이트.

## W325 MATERIAL pass (2026-11-05) — 이전 flat-paint 외관 대체

- W123 Gnawing Hunger / Beloved의 재질 및 페인트 코드, 제공된 인게임/아틀라스 이미지를 비교. 아래 재질은 원본 외관 기반의 RGBA 재해석이며 원본 PBR을 복구한 결과는 아님.
- `STYLE=material`; 전체 면을 채우던 flat special()은 최종 경로에서 제거. 각 부품을 도장·브러시드 금속·폴리머·고무 등으로 명시 분리.
- 재질 매핑 (RGB):
  - `tan_enamel` → `paint` / `(126, 99, 74)`
  - `green_polymer` → `polymer` / `(39, 49, 43)`
  - `gunmetal` → `metal` / `(61, 66, 63)`
  - `steel` → `steel` / `(134, 145, 139)`
  - `rubber` → `rubber` / `(26, 31, 28)`
  - `black_recess` → `dark` / `(19, 25, 23)`
  - `optic_rim` → `lens` / `(49, 83, 72)`
- special(): 총구 안쪽 검정과 조준경 테두리의 작은 반사점만 유지.
- 투영: 5×5 지점의 원본 유효 coverage가 60% 미만인 면, 끝면, 얇은 챔퍼는 detail=0. 재질 결/음영은 유지. 현재 전체 출력 면 중 606면은 이 경로이며 숨겨진 면도 포함한 수치. 아그로나 중앙 후방 판은 실제 호스와 원본 호스 실루엣 중복을 피하려고 추가로 detail=0 처리.
- 출력: 144요소 그대로. 지오메트리 SHA-256 동일 확인. T20, 최종 아틀라스 512×512, PNG 185,847바이트.
- 재현: kit build 후 `art/weapons/w325/lost_and_found/identity_pack.py <id>` 실행. 재배치는 면별 RGBA 그대로 유지. `material_review.py`로 비교 이미지 재생성.
- 확인: ADS OK, 같은 방향 공면 겹침 0, 파트/기하 불변, 출력 해시, west/east/top/q/front 오프라인 렌더. 실제 Minecraft·팩 로드·파지·장전·FPS는 미실행.

## Material R2 (2026-11-05)

리시버 띠·레일·가드·가스 블록을 금속, 총열과 슬리브를 밝은 강철로 분리. 황갈색 외피 유지.

수작업 모티프: 탄창 1텍셀 패널 홈과 짧은 리브 끝 눈금. 폴리머/고무 기본 명도 차이 40.64.

형상 해시 불변, 아틀라스 [512, 512], 겹침 0, ADS OK, 출력 해시 확인. kit.py 수정 없음. Blender 5시점 렌더 확인용이며 Minecraft 검수 아님.
