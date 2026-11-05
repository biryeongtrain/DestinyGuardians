# Nanty Narker (W325, rare, Rapid-Fire pulse) over claws_of_the_wolf

- Same rip frame as Lost and Found (identical receiver/stock/handguard geometry, same uniform map 27.73 px/m, width x1.2).
- Identity kept: mint-white thumbhole bullpup stock with long dark cheek pad, dark slotted handguard, white barrel,
  dark angular gas block, slotted white muzzle brake (two real through ports, dark bore), short scope with ringed eyepiece.
- Elements: body 72 + magazine 2 = 74. Atlas 512x512, T 16.
- Contract fit: grip/trigger/magazine identical to Lost and Found (grip top z 6.7-8.4, trigger 5.9-6.05, magazine
  z 10.1-12.9). Muzzle -8.96 (base -8.61, +0.35 longer, rip proportion).
- Sight: scope lowered 0.15 px; objective ring z 2.8-4.5 (aperture 0.64) and eyepiece ring z 5.9-7.0 (aperture 0.86)
  centred x 8 / y 12.5 (base ADS line); mid tube has side walls + floor only (open top) so the eye line stays clear;
  turret sits at y >= 12.93 above the aperture. W148 overlay dot kept.
- Not verified: in-game first person / ADS tunnel look of the scope / reload alignment (offline renders only).

## W325 detail + style pass (2026-11-05)
- Elements: 74 -> body 149 + magazine 6 = 155 (atlas 512x512).
- Style: Dead Man Walking break-up (machined(): long slabs split into segments with engraved joint seams), chamfered
  silhouette edges (chbox), rails with teeth, ribs, vents, separate panels; kit STYLE 'pixel' palette bake + Painter
  flat colours where the projection smeared.
- ADS: kit.py adscheck OK. scope = objective ring + eyepiece ring + open-top mid tube (all sight_*), eye cup block removed; rear lowered/narrowed exactly like Lost and Found. Scope body painted flat mint, rings dark.
- Contract (grip, trigger, magazine box/part ids, muzzle) unchanged from the first pass.
- Not verified in game after this pass (offline Blender renders only).

## W325 cleanup pass vs the Chattering Bone negative reference (2026-11-05)
- Elements now body 151 + magazine 6 = 157; adscheck OK.
- Fixed: same grip/belly/magazine-plate fixes as Lost and Found.
- All designs end with dezfight(): coplanar overlapping faces are pulled 0.012 px inward (no z-fight slivers).
- Remaining checker hits are deliberate proud side panels on the same axis and angled grip/magazine meeting the body.

## W325 identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST
- 연한 민트색 총몸·흰색 총열/브레이크
- 검정 칙패드와 조임 밴드
- 앞뒤 개구부가 열린 짧은 민트 조준경
- 총구의 2개 실제 측면 포트
- 검은 전방 손잡이와 흰 가스관 슬롯
- 은색 스톡 레버와 불펍 리브 탄창

- 입체 변경: 가스관 두 끝의 소형 챔퍼와 하단 가스블록 챔퍼를 단순화하여 157→148. 총구 포트·조준경·파지/탄창 계약 유지.
- 페인트: 모든 노출 면을 `special()`로 직접 칠함. 부품별 단색, 실제 1텍셀 상단 하이라이트/하단 이음선, 원본 기반 패널선·핀·손잡이 스티플·상기 고유 표식. 투영 얼룩/무작위 노이즈 없음.
- 밀도/아틀라스: T20. kit build의 1024×512 작업 아틀라스를 `art/weapons/w325/lost_and_found/identity_pack.py <id>`로 손실 없이 512×512로 재배치. 중복 UV 섬만 공유하고 모든 면 RGBA를 정확히 비교함. 재빌드 후 반드시 이 재배치 단계를 실행.
- `identity_geometry.py`: 서로 다른 피벗/회전까지 월드 평면에서 비교하고 겹친 작은 면을 0.009px 안쪽으로 정리. 같은 방향 공면 겹침 0건(평면 1e-5, 투영 면적 0.0002 기준). 반대 방향으로 맞닿는 정상 접합면은 제외.
- 검토: kit build, ADS profile OK, west/east/top/q/front 오프라인 Blender 렌더. `review/identity_checks.json`, `review/*_compare.png`에 근거 보관.
- 미검증: 실제 Minecraft 1/3인칭, ADS 화면, 분리 장전, 10~20개 표시 및 FPS. 원본 PBR·마모는 Minecraft에 맞는 제한된 색과 선으로 해석했으며 원본과 정밀 동등하다고 주장하지 않음.
- 최종 출력: 157 → 148요소 (본체 142 + 탄창 6), PNG 12,235바이트.

## W325 MATERIAL pass (2026-11-05) — 이전 flat-paint 외관 대체

- W123 Gnawing Hunger / Beloved의 재질 및 페인트 코드, 제공된 인게임/아틀라스 이미지를 비교. 아래 재질은 원본 외관 기반의 RGBA 재해석이며 원본 PBR을 복구한 결과는 아님.
- `STYLE=material`; 전체 면을 채우던 flat special()은 최종 경로에서 제거. 각 부품을 도장·브러시드 금속·폴리머·고무 등으로 명시 분리.
- 재질 매핑 (RGB):
  - `mint_enamel` → `paint` / `(174, 195, 176)`
  - `white_enamel` → `paint` / `(210, 222, 213)`
  - `green_polymer` → `polymer` / `(28, 42, 33)`
  - `gunmetal` → `metal` / `(59, 68, 61)`
  - `steel` → `steel` / `(143, 161, 150)`
  - `rubber` → `rubber` / `(24, 31, 26)`
  - `recess` → `dark` / `(18, 26, 21)`
  - `optic_rim` → `lens` / `(54, 99, 84)`
- special(): 총구 안쪽 검정과 조준경 테두리의 작은 반사점만 유지.
- 투영: 5×5 지점의 원본 유효 coverage가 60% 미만인 면, 끝면, 얇은 챔퍼는 detail=0. 재질 결/음영은 유지. 현재 전체 출력 면 중 614면은 이 경로이며 숨겨진 면도 포함한 수치. 아그로나 중앙 후방 판은 실제 호스와 원본 호스 실루엣 중복을 피하려고 추가로 detail=0 처리.
- 출력: 148요소 그대로. 지오메트리 SHA-256 동일 확인. T20, 최종 아틀라스 512×512, PNG 197,595바이트.
- 재현: kit build 후 `art/weapons/w325/lost_and_found/identity_pack.py <id>` 실행. 재배치는 면별 RGBA 그대로 유지. `material_review.py`로 비교 이미지 재생성.
- 확인: ADS OK, 같은 방향 공면 겹침 0, 파트/기하 불변, 출력 해시, west/east/top/q/front 오프라인 렌더. 실제 Minecraft·팩 로드·파지·장전·FPS는 미실행.

## Material R2 (2026-11-05)

리시버 띠·레일·가드·가스부를 금속, 소염기·총열·슬리브를 강철로 전환. 민트 외피와 흰 가스 튜브 유지.

수작업 모티프: 조준경 전방 칼라의 1텍셀 눈금. 폴리머/고무 기본 명도 차이 36.05.

형상 해시 불변, 아틀라스 [512, 512], 겹침 0, ADS OK, 출력 해시 확인. kit.py 수정 없음. Blender 5시점 렌더 확인용이며 Minecraft 검수 아님.
