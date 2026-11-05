# Psi Cirrus II (W325, rare, Rapid-Fire pulse) over claws_of_the_wolf

- Identity kept: white/olive camo Veist-style bullpup, three side canisters (crossed boxes read as discs), white C-frame
  lower handguard with recessed panel, top shroud with the white carry bracket (real hole), front sight post, slotted
  muzzle rod + collar, enclosed hand loop (real hole between the diagonal loop bar and the grip), skeleton stock with
  thumbhole and camo flap over the magazine well, square reflex box.
- Elements: body 56 + magazine 2 = 58. Atlas 512x512, T 16.
- Map: uniform 25.76 px/m (rip 0.986 m long), width x1.1; whole model shifted -0.6 px in z so the rip grip/trigger
  land on the base grip (rip hand sits ~0.8 px behind claws_of_the_wolf's). Muzzle -8.95, butt 16.0 (base -8.61/16.8).
- Contract fit: grip top z 7.6-9.1 / trigger z 6.35-6.5 (base grip 7.0-8.9, trigger ~6.2); magazine z 9.95-12.15
  (base 9.7-12.9), bottom y 5.2 (base 6.4).
- Sight: the rip reflex box sat over the canisters (z 6.3-8.9, too close to the eye); moved 1.8 px forward
  (part transform) to z 3.9-6.5, hollow square box aperture 0.76 centred x 8 / y 12.48. W148 overlay dot kept.
- Known: the hand loop is a straight bar (rip loop is curved); grip texture is dark/flat compared to the rip knurl.
- Not verified in game (first person, ADS, reload).

## W325 detail + style pass (2026-11-05)
- Elements: 58 -> body 137 + magazine 5 = 142 (atlas 512x512).
- Style: Dead Man Walking break-up (machined(): long slabs split into segments with engraved joint seams), chamfered
  silhouette edges (chbox), rails with teeth, ribs, vents, separate panels; kit STYLE 'pixel' palette bake + Painter
  flat colours where the projection smeared.
- ADS: kit.py adscheck OK. receiver/stock tops 11.70/11.66, canisters -0.13, stock strut lowered; reflex box (sight_*) inside the base optic window. PALETTE 14 / FLAT_TOL 34 to calm the camo.
- Contract (grip, trigger, magazine box/part ids, muzzle) unchanged from the first pass.
- Not verified in game after this pass (offline Blender renders only).

## W325 cleanup pass vs the Chattering Bone negative reference (2026-11-05)
- Elements now body 136 + magazine 5 = 141; adscheck OK.
- Fixed: loop web/rim ride the loop bar axis, grip panel/foot on the grip axis, nose slab that poked through the shroud chamfers removed; camo repainted as 0.5 px cells in 3 flat colours (white/olive/black) instead of noisy projection.
- All designs end with dezfight(): coplanar overlapping faces are pulled 0.012 px inward (no z-fight slivers).
- Remaining checker hits are deliberate proud side panels on the same axis and angled grip/magazine meeting the body.

## W325 identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST
- 상아색·올리브색 각진 위장 도색
- 측면의 3개 은색 원형 캡
- 은색 C자 전방 프레임과 낮은 대각 손 보호대
- 뒤쪽 스톡의 실제 삼각형/사각형 빈 공간
- 열린 박스 조준경
- 대각선 음각 탄창과 은색 끝 총열

- 입체 변경: 기존 세 캡·C 프레임·스톡 구멍·상부 브래킷·탄창 리브 유지. 캡의 원형 링은 면 UV로 명료화.
- 페인트: 모든 노출 면을 `special()`로 직접 칠함. 부품별 단색, 실제 1텍셀 상단 하이라이트/하단 이음선, 원본 기반 패널선·핀·손잡이 스티플·상기 고유 표식. 투영 얼룩/무작위 노이즈 없음.
- 밀도/아틀라스: T20. kit build의 1024×512 작업 아틀라스를 `art/weapons/w325/lost_and_found/identity_pack.py <id>`로 손실 없이 512×512로 재배치. 중복 UV 섬만 공유하고 모든 면 RGBA를 정확히 비교함. 재빌드 후 반드시 이 재배치 단계를 실행.
- `identity_geometry.py`: 서로 다른 피벗/회전까지 월드 평면에서 비교하고 겹친 작은 면을 0.009px 안쪽으로 정리. 같은 방향 공면 겹침 0건(평면 1e-5, 투영 면적 0.0002 기준). 반대 방향으로 맞닿는 정상 접합면은 제외.
- 검토: kit build, ADS profile OK, west/east/top/q/front 오프라인 Blender 렌더. `review/identity_checks.json`, `review/*_compare.png`에 근거 보관.
- 미검증: 실제 Minecraft 1/3인칭, ADS 화면, 분리 장전, 10~20개 표시 및 FPS. 원본 PBR·마모는 Minecraft에 맞는 제한된 색과 선으로 해석했으며 원본과 정밀 동등하다고 주장하지 않음.
- 최종 출력: 141 → 141요소 (본체 136 + 탄창 5), PNG 14,591바이트.

## W325 MATERIAL pass (2026-11-05) — 이전 flat-paint 외관 대체

- W123 Gnawing Hunger / Beloved의 재질 및 페인트 코드, 제공된 인게임/아틀라스 이미지를 비교. 아래 재질은 원본 외관 기반의 RGBA 재해석이며 원본 PBR을 복구한 결과는 아님.
- `STYLE=material`; 전체 면을 채우던 flat special()은 최종 경로에서 제거. 각 부품을 도장·브러시드 금속·폴리머·고무 등으로 명시 분리.
- 재질 매핑 (RGB):
  - `ivory_enamel` → `paint` / `(186, 192, 173)`
  - `olive_enamel` → `paint` / `(69, 84, 43)`
  - `green_polymer` → `polymer` / `(40, 48, 41)`
  - `gunmetal` → `metal` / `(62, 69, 60)`
  - `steel` → `steel` / `(160, 176, 160)`
  - `rubber` → `rubber` / `(27, 32, 27)`
  - `recess` → `dark` / `(18, 25, 20)`
  - `optic_rim` → `lens` / `(55, 105, 77)`
- special(): 원본 투영에서 확인되는 올리브 위장 부분, 3개 캡의 링/십자 표식, 총구 안쪽만 유지. 이전의 반복 사각 위장 패턴 제거.
- 투영: 5×5 지점의 원본 유효 coverage가 60% 미만인 면, 끝면, 얇은 챔퍼는 detail=0. 재질 결/음영은 유지. 현재 전체 출력 면 중 543면은 이 경로이며 숨겨진 면도 포함한 수치. 아그로나 중앙 후방 판은 실제 호스와 원본 호스 실루엣 중복을 피하려고 추가로 detail=0 처리.
- 출력: 141요소 그대로. 지오메트리 SHA-256 동일 확인. T20, 최종 아틀라스 1024×512, PNG 347,029바이트.
- 가까이 보이는 총몸·조준부의 원본 릴리프와 재질 결을 T20으로 유지하면 고유 UV 섬이 늘어 512²에 손실 없이 들어가지 않음. 리샘플링 없이 1024×512로 패킹했으며 빈 면적과 텍스처 메모리를 별도 고려.
- 재현: kit build 후 `art/weapons/w325/lost_and_found/identity_pack.py <id>` 실행. 재배치는 면별 RGBA 그대로 유지. `material_review.py`로 비교 이미지 재생성.
- 확인: ADS OK, 같은 방향 공면 겹침 0, 파트/기하 불변, 출력 해시, west/east/top/q/front 오프라인 렌더. 실제 Minecraft·팩 로드·파지·장전·FPS는 미실행.

## Material R2 (2026-11-05)

하부 리시버·컨트롤 패널·레일·띠를 금속으로 전환. 은색 총열·브래킷·캐니스터 몸체 유지, 캡은 올리브 도장.

수작업 모티프: 캐니스터 동심원·십자와 상단 교정 눈금; 흰색/올리브 큰 위장 블록. 폴리머/고무 기본 명도 차이 34.12.

형상 해시 불변, 아틀라스 [1024, 512], 겹침 0, ADS OK, 출력 해시 확인. kit.py 수정 없음. Blender 5시점 렌더 확인용이며 Minecraft 검수 아님.
