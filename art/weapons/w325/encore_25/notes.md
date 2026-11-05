# Encore-25 (W325, rare, Adaptive pulse) over bygones

- Identity kept: red top cover with hump, rail and rear ear, green/grey bullpup body with slots, perforated round
  barrel shroud, front hook post, full-length rectangular trigger guard (real hole), raked banded magazine with a
  top flange, beige side plate on the rear receiver, curved butt pad (stepped upper/lower lobes).
- Elements: body 23 + magazine 2 = 25 (lowest of the batch: the rip is a few large volumes). Atlas 512x512, T 16.
- Map: uniform 30 px/m, whole model shifted +0.4 z. Grip top z 7.0-8.7 / trigger 5.85-6.05 (bygones grip ~7.0-9.0);
  magazine top z 10.3-12.9 raked 15 deg (bygones moving magazine 10.7-13.4), flange to 14.0. Muzzle -7.25 (base -8.54).
- Sight: no optic; red cover top 12.42-12.72 under the bygones ADS line (W151 pin tip 12.74), front hook tip 12.1,
  rear ear thin plate (x 7.88-8.12, y 12.72-13.3) at z 9.25-9.6 - may be visible at the top of the ADS view; W148
  overlay dot kept as aim point.
- Known: perforations are texture only; butt pad curve approximated by three boxes. Not verified in game.

## W325 detail + style pass (2026-11-05)
- Elements: 25 -> body 97 + magazine 6 = 103 (atlas 512x512).
- Style: Dead Man Walking break-up (machined(): long slabs split into segments with engraved joint seams), chamfered
  silhouette edges (chbox), rails with teeth, ribs, vents, separate panels; kit STYLE 'pixel' palette bake + Painter
  flat colours where the projection smeared.
- ADS: kit.py adscheck OK. red cover lowered to bygones roof (12.0); tall rear ear replaced by an open two-post notch sight (sight_post_l/r, top 12.95) in the optic window; perforated shroud painted as a regular hole grid.
- Contract (grip, trigger, magazine box/part ids, muzzle) unchanged from the first pass.
- Not verified in game after this pass (offline Blender renders only).

## W325 cleanup pass vs the Chattering Bone negative reference (2026-11-05)
- Elements now body 95 + magazine 6 = 101; adscheck OK.
- Fixed: hump ramp sliver removed, grip panel/foot on the grip axis, guard heel removed, magazine bands/floor on the magazine axis.
- All designs end with dezfight(): coplanar overlapping faces are pulled 0.012 px inward (no z-fight slivers).
- Remaining checker hits are deliberate proud side panels on the same axis and angled grip/magazine meeting the body.

## W325 identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST
- 붉은 상부 덮개와 황갈색 가는 띠
- 올리브 녹색 측판과 짙은 회색 총몸
- 실제 천공 창을 갖춘 황갈색 총열 덮개
- 붉은 꼬리 및 탄창 바닥의 SUROS 표기
- 황갈색 테두리 후방 측판
- 긴 사각 방아쇠 울과 3개 황갈색 리브의 경사진 탄창

- 입체 변경: 총열 덮개를 상/하/중간 레일·6개 연결대·내부 총열로 재구성해 5개 천공 구간의 실제 깊이를 확보.
- 페인트: 모든 노출 면을 `special()`로 직접 칠함. 부품별 단색, 실제 1텍셀 상단 하이라이트/하단 이음선, 원본 기반 패널선·핀·손잡이 스티플·상기 고유 표식. 투영 얼룩/무작위 노이즈 없음.
- 밀도/아틀라스: T20. kit build의 1024×512 작업 아틀라스를 `art/weapons/w325/lost_and_found/identity_pack.py <id>`로 손실 없이 512×512로 재배치. 중복 UV 섬만 공유하고 모든 면 RGBA를 정확히 비교함. 재빌드 후 반드시 이 재배치 단계를 실행.
- `identity_geometry.py`: 서로 다른 피벗/회전까지 월드 평면에서 비교하고 겹친 작은 면을 0.009px 안쪽으로 정리. 같은 방향 공면 겹침 0건(평면 1e-5, 투영 면적 0.0002 기준). 반대 방향으로 맞닿는 정상 접합면은 제외.
- 검토: kit build, ADS profile OK, west/east/top/q/front 오프라인 Blender 렌더. `review/identity_checks.json`, `review/*_compare.png`에 근거 보관.
- 미검증: 실제 Minecraft 1/3인칭, ADS 화면, 분리 장전, 10~20개 표시 및 FPS. 원본 PBR·마모는 Minecraft에 맞는 제한된 색과 선으로 해석했으며 원본과 정밀 동등하다고 주장하지 않음.
- 최종 출력: 101 → 104요소 (본체 98 + 탄창 6), PNG 10,215바이트.

## W325 MATERIAL pass (2026-11-05) — 이전 flat-paint 외관 대체

- W123 Gnawing Hunger / Beloved의 재질 및 페인트 코드, 제공된 인게임/아틀라스 이미지를 비교. 아래 재질은 원본 외관 기반의 RGBA 재해석이며 원본 PBR을 복구한 결과는 아님.
- `STYLE=material`; 전체 면을 채우던 flat special()은 최종 경로에서 제거. 각 부품을 도장·브러시드 금속·폴리머·고무 등으로 명시 분리.
- 재질 매핑 (RGB):
  - `red_enamel` → `paint` / `(119, 57, 51)`
  - `green_enamel` → `paint` / `(73, 91, 76)`
  - `receiver_coating` → `paint` / `(45, 54, 49)`
  - `polymer` → `polymer` / `(33, 42, 36)`
  - `brass` → `gold` / `(151, 130, 83)`
  - `gunmetal` → `metal` / `(61, 67, 60)`
  - `steel` → `steel` / `(123, 133, 115)`
  - `rubber` → `rubber` / `(26, 31, 27)`
  - `recess` → `dark` / `(18, 24, 20)`
- special(): SUROS 글자, 후방 측판의 황동색 테두리, 붉은 덮개의 얇은 황갈색 띠만 유지.
- 투영: 5×5 지점의 원본 유효 coverage가 60% 미만인 면, 끝면, 얇은 챔퍼는 detail=0. 재질 결/음영은 유지. 현재 전체 출력 면 중 400면은 이 경로이며 숨겨진 면도 포함한 수치. 아그로나 중앙 후방 판은 실제 호스와 원본 호스 실루엣 중복을 피하려고 추가로 detail=0 처리.
- 출력: 104요소 그대로. 지오메트리 SHA-256 동일 확인. T20, 최종 아틀라스 512×512, PNG 212,492바이트.
- 재현: kit build 후 `art/weapons/w325/lost_and_found/identity_pack.py <id>` 실행. 재배치는 면별 RGBA 그대로 유지. `material_review.py`로 비교 이미지 재생성.
- 확인: ADS OK, 같은 방향 공면 겹침 0, 파트/기하 불변, 출력 해시, west/east/top/q/front 오프라인 렌더. 실제 Minecraft·팩 로드·파지·장전·FPS는 미실행.

## Material R2 (2026-11-05)

중앙·후방 리시버·측판·레일·가드·개머리 목을 금속으로 전환. 붉은 상부, 녹색 전방 외피, 황동 슈라우드 유지.

수작업 모티프: SUROS 각인, 황동 띠, 1텍셀 측판 테두리. 폴리머/고무 기본 명도 차이 33.52.

형상 해시 불변, 아틀라스 [512, 512], 겹침 0, ADS OK, 출력 해시 확인. kit.py 수정 없음. Blender 5시점 렌더 확인용이며 Minecraft 검수 아님.
