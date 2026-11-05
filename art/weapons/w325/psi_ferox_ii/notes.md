# Psi Ferox II (W325, uncommon, Lightweight pulse) over chattering_bone

- Identity kept: dark purple Veist bullpup, sloped receiver hump (integrated rear hood), truss handguard (recessed band
  between solid posts, diagonal struts from the rip texture), see-through wire carry bracket, round sling swivel,
  front hook, suppressor with slot, enclosed hand loop (real hole), raked grip, raked magazine with slanted base,
  wider rear stock cage and narrow butt pad.
- Elements: body 35 + magazine 2 = 37. Atlas 512x512, T 16.
- Map: uniform 25 px/m read frame; barrel/suppressor ahead of z -5.3 compressed x0.62 (piecewise z map, inverse in
  model2world) so the muzzle lands at -9.0 instead of -11.25; whole model shifted -0.2 z.
- Contract fit: hand loop/grip land almost exactly on chattering_bone's loop and grip (grip top z 8.1-9.8, trigger
  z 7.1-7.3); magazine z 10.65-12.8 (base 10.8-13.3), bottom y 5.0-5.8 (base 6.8).
- Sight: no optic on the rip; hump top kept at y 12.78 under the base ADS line 12.93, W148 overlay dot is the aim point.
- Not verified in game; ADS view over the hump (hump may frame the lower half of the view) needs the master's check.

## W325 detail + style pass (2026-11-05)
- Elements: 37 -> body 122 + magazine 5 = 127 (atlas 512x512).
- Style: Dead Man Walking break-up (machined(): long slabs split into segments with engraved joint seams), chamfered
  silhouette edges (chbox), rails with teeth, ribs, vents, separate panels; kit STYLE 'pixel' palette bake + Painter
  flat colours where the projection smeared.
- ADS: kit.py adscheck OK. hump shortened to the base optic hood span (top 12.72), step 12.5 in front, tail 12.32; purple panels painted flat (PALETTE_KEEP).
- Contract (grip, trigger, magazine box/part ids, muzzle) unchanged from the first pass.
- Not verified in game after this pass (offline Blender renders only).

## W325 cleanup pass vs the Chattering Bone negative reference (2026-11-05)
- Elements now body 122 + magazine 5 = 127; adscheck OK.
- Fixed: loop bar/web/rim on one axis, grip panel/foot on the grip axis, truss struts kept inside the window, receiver ramp ends under the chamfer, slanted magazine base -> flat block.
- All designs end with dezfight(): coplanar overlapping faces are pulled 0.012 px inward (no z-fight slivers).
- Remaining checker hits are deliberate proud side panels on the same axis and angled grip/magazine meeting the body.

## W325 identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST
- 보라색 상부와 짙은 녹회색 하부
- 실제 관통된 전방 트러스 창과 대각 보강대
- 상부의 가는 손잡이 브래킷
- 평행 슬롯이 있는 보라색 소음기
- 낮은 일체형 후방 조준부와 홈 난 스톡 케이지
- 넓은 손 보호대와 대각 음각 탄창

- 입체 변경: 전방 트러스 뒤의 막힌 코어를 제거해 대각 보강대 사이를 실제 관통 창으로 변경.
- 페인트: 모든 노출 면을 `special()`로 직접 칠함. 부품별 단색, 실제 1텍셀 상단 하이라이트/하단 이음선, 원본 기반 패널선·핀·손잡이 스티플·상기 고유 표식. 투영 얼룩/무작위 노이즈 없음.
- 밀도/아틀라스: T20. kit build의 1024×512 작업 아틀라스를 `art/weapons/w325/lost_and_found/identity_pack.py <id>`로 손실 없이 512×512로 재배치. 중복 UV 섬만 공유하고 모든 면 RGBA를 정확히 비교함. 재빌드 후 반드시 이 재배치 단계를 실행.
- `identity_geometry.py`: 서로 다른 피벗/회전까지 월드 평면에서 비교하고 겹친 작은 면을 0.009px 안쪽으로 정리. 같은 방향 공면 겹침 0건(평면 1e-5, 투영 면적 0.0002 기준). 반대 방향으로 맞닿는 정상 접합면은 제외.
- 검토: kit build, ADS profile OK, west/east/top/q/front 오프라인 Blender 렌더. `review/identity_checks.json`, `review/*_compare.png`에 근거 보관.
- 미검증: 실제 Minecraft 1/3인칭, ADS 화면, 분리 장전, 10~20개 표시 및 FPS. 원본 PBR·마모는 Minecraft에 맞는 제한된 색과 선으로 해석했으며 원본과 정밀 동등하다고 주장하지 않음.
- 최종 출력: 127 → 127요소 (본체 122 + 탄창 5), PNG 11,744바이트.

## W325 MATERIAL pass (2026-11-05) — 이전 flat-paint 외관 대체

- W123 Gnawing Hunger / Beloved의 재질 및 페인트 코드, 제공된 인게임/아틀라스 이미지를 비교. 아래 재질은 원본 외관 기반의 RGBA 재해석이며 원본 PBR을 복구한 결과는 아님.
- `STYLE=material`; 전체 면을 채우던 flat special()은 최종 경로에서 제거. 각 부품을 도장·브러시드 금속·폴리머·고무 등으로 명시 분리.
- 재질 매핑 (RGB):
  - `violet_enamel` → `paint` / `(78, 65, 85)`
  - `green_polymer` → `polymer` / `(39, 47, 42)`
  - `gunmetal` → `metal` / `(58, 62, 59)`
  - `steel` → `steel` / `(120, 126, 125)`
  - `rubber` → `rubber` / `(27, 31, 28)`
  - `recess` → `dark` / `(21, 23, 25)`
  - `lens` → `lens` / `(40, 83, 90)`
- special(): 작은 조준부 반사점과 총구 안쪽만 유지. 이전의 전체 보라색 채움과 임의 탄창 줄무늬 제거.
- 투영: 5×5 지점의 원본 유효 coverage가 60% 미만인 면, 끝면, 얇은 챔퍼는 detail=0. 재질 결/음영은 유지. 현재 전체 출력 면 중 524면은 이 경로이며 숨겨진 면도 포함한 수치. 아그로나 중앙 후방 판은 실제 호스와 원본 호스 실루엣 중복을 피하려고 추가로 detail=0 처리.
- 출력: 127요소 그대로. 지오메트리 SHA-256 동일 확인. T20, 최종 아틀라스 1024×512, PNG 273,287바이트.
- 가까이 보이는 총몸·조준부의 원본 릴리프와 재질 결을 T20으로 유지하면 고유 UV 섬이 늘어 512²에 손실 없이 들어가지 않음. 리샘플링 없이 1024×512로 패킹했으며 빈 면적과 텍스처 메모리를 별도 고려.
- 재현: kit build 후 `art/weapons/w325/lost_and_found/identity_pack.py <id>` 실행. 재배치는 면별 RGBA 그대로 유지. `material_review.py`로 비교 이미지 재생성.
- 확인: ADS OK, 같은 방향 공면 겹침 0, 파트/기하 불변, 출력 해시, west/east/top/q/front 오프라인 렌더. 실제 Minecraft·팩 로드·파지·장전·FPS는 미실행.

## Material R2 (2026-11-05)

하부 리시버·개머리 하부·트러스·가드를 금속, 후방/전방 리시버와 소음기를 보랏빛 금속으로 분리. 상부 외피는 보라 도장 유지.

수작업 모티프: 후방 리시버의 1텍셀 냉각 슬롯과 밝은 윗모서리. 폴리머/고무 기본 명도 차이 32.22.

형상 해시 불변, 아틀라스 [1024, 512], 겹침 0, ADS OK, 출력 해시 확인. kit.py 수정 없음. Blender 5시점 렌더 확인용이며 Minecraft 검수 아님.
