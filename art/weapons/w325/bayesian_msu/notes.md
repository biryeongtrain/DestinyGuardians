# Bayesian MSu (W325, rare, Adaptive pulse) over bygones

- Identity kept: ivory/yellow-camo upper rail over a dark slotted handguard, under-barrel grip module with a real gap
  below the handguard, splayed two-leg bipod (two-axis rotated bars + feet), enclosed hand loop (real hole),
  long raked grip, yellow stock panel, rod + separate butt pad, screen sight block.
- Elements: body 32 + magazine 2 = 34. Atlas 512x512, T 16.
- Map: uniform 26.6 px/m, whole model shifted -0.3 z; grip + trigger moved a further 0.4 forward (part transform) and
  the loop bar re-aimed at the moved grip foot, because the rip grip sits ~1 px behind bygones' while its magazine
  already matches. Grip top z 7.2-9.1 / trigger 6.3-6.5 (bygones grip ~7.0-9.0); magazine z 10.55-12.95 (base 10.7-13.4).
- Sight: rip screen block (z 6.3-8.9) moved 1.8 forward and 0.09 up: hollow box z 4.2-6.8, aperture 0.76 centred
  x 8 / y 12.74 (bygones W151 pin tip 12.74); ends painted dark. W148 overlay dot kept.
- Muzzle -6.45 (base -8.54): the rip's short barrel kept; bipod feet reach z -8.4, y 5.5 (visible below the barrel in
  first person - intended identity, master to judge in game).
- Not verified in game; multi-axis element rotation (bipod) relies on native 26.3 x-then-y rotation as in kit.py.

## W325 detail + style pass (2026-11-05)
- Elements: 34 -> body 129 + magazine 5 = 134 (atlas 512x512).
- Style: Dead Man Walking break-up (machined(): long slabs split into segments with engraved joint seams), chamfered
  silhouette edges (chbox), rails with teeth, ribs, vents, separate panels; kit STYLE 'pixel' palette bake + Painter
  flat colours where the projection smeared.
- ADS: kit.py adscheck OK. screen sight shortened to 1.3 px and placed in bygones' optic window (z 5.2-6.5, sight_*); ivory/yellow/teal flat colour blocks.
- Contract (grip, trigger, magazine box/part ids, muzzle) unchanged from the first pass.
- Not verified in game after this pass (offline Blender renders only).

## W325 cleanup pass vs the Chattering Bone negative reference (2026-11-05)
- Elements now body 131 + magazine 5 = 136; adscheck OK.
- Fixed: loop and grip parts on shared axes, 18 deg module chin slab -> 3 axis-aligned steps, bipod feet axis-aligned blocks, slanted magazine base -> flat block.
- All designs end with dezfight(): coplanar overlapping faces are pulled 0.012 px inward (no z-fight slivers).
- Remaining checker hits are deliberate proud side panels on the same axis and angled grip/magazine meeting the body.

## W325 identity pass — Ace / Izanagi (2026-11-05)

### IDENTITY LIST
- 상아색·황색 위장 상부 레일
- 짙은 청록 총몸과 2열 손잡이 벤트
- 실제 간격이 있는 아래쪽 모듈
- 벌어진 양각대 2개 다리
- 노란 스톡 패널과 노출된 연결봉
- 상아색 조준경·총구와 밝은 총몸 제어판

- 입체 변경: 기존 양각대·하부 모듈의 빈 공간·상부 레일·탄창 리브를 유지. 원본의 밝은 제어판은 UV로 복원.
- 페인트: 모든 노출 면을 `special()`로 직접 칠함. 부품별 단색, 실제 1텍셀 상단 하이라이트/하단 이음선, 원본 기반 패널선·핀·손잡이 스티플·상기 고유 표식. 투영 얼룩/무작위 노이즈 없음.
- 밀도/아틀라스: T20. kit build의 1024×512 작업 아틀라스를 `art/weapons/w325/lost_and_found/identity_pack.py <id>`로 손실 없이 512×512로 재배치. 중복 UV 섬만 공유하고 모든 면 RGBA를 정확히 비교함. 재빌드 후 반드시 이 재배치 단계를 실행.
- `identity_geometry.py`: 서로 다른 피벗/회전까지 월드 평면에서 비교하고 겹친 작은 면을 0.009px 안쪽으로 정리. 같은 방향 공면 겹침 0건(평면 1e-5, 투영 면적 0.0002 기준). 반대 방향으로 맞닿는 정상 접합면은 제외.
- 검토: kit build, ADS profile OK, west/east/top/q/front 오프라인 Blender 렌더. `review/identity_checks.json`, `review/*_compare.png`에 근거 보관.
- 미검증: 실제 Minecraft 1/3인칭, ADS 화면, 분리 장전, 10~20개 표시 및 FPS. 원본 PBR·마모는 Minecraft에 맞는 제한된 색과 선으로 해석했으며 원본과 정밀 동등하다고 주장하지 않음.
- 최종 출력: 136 → 136요소 (본체 131 + 탄창 5), PNG 11,387바이트.

## W325 MATERIAL pass (2026-11-05) — 이전 flat-paint 외관 대체

- W123 Gnawing Hunger / Beloved의 재질 및 페인트 코드, 제공된 인게임/아틀라스 이미지를 비교. 아래 재질은 원본 외관 기반의 RGBA 재해석이며 원본 PBR을 복구한 결과는 아님.
- `STYLE=material`; 전체 면을 채우던 flat special()은 최종 경로에서 제거. 각 부품을 도장·브러시드 금속·폴리머·고무 등으로 명시 분리.
- 재질 매핑 (RGB):
  - `ivory_enamel` → `paint` / `(201, 200, 177)`
  - `yellow_enamel` → `paint` / `(179, 171, 88)`
  - `teal_enamel` → `paint` / `(35, 57, 55)`
  - `polymer` → `polymer` / `(30, 43, 39)`
  - `gunmetal` → `metal` / `(58, 68, 63)`
  - `steel` → `steel` / `(137, 151, 137)`
  - `rubber` → `rubber` / `(25, 30, 28)`
  - `recess` → `dark` / `(17, 26, 23)`
  - `lens` → `lens` / `(45, 90, 70)`
- special(): 원본에서 확인되는 황색 위장 부분과 총구 안쪽만 유지. 이전의 반복 사각 위장 패턴 제거.
- 투영: 5×5 지점의 원본 유효 coverage가 60% 미만인 면, 끝면, 얇은 챔퍼는 detail=0. 재질 결/음영은 유지. 현재 전체 출력 면 중 529면은 이 경로이며 숨겨진 면도 포함한 수치. 아그로나 중앙 후방 판은 실제 호스와 원본 호스 실루엣 중복을 피하려고 추가로 detail=0 처리.
- 출력: 136요소 그대로. 지오메트리 SHA-256 동일 확인. T20, 최종 아틀라스 1024×512, PNG 306,627바이트.
- 가까이 보이는 총몸·조준부의 원본 릴리프와 재질 결을 T20으로 유지하면 고유 UV 섬이 늘어 512²에 손실 없이 들어가지 않음. 리샘플링 없이 1024×512로 패킹했으며 빈 면적과 텍스처 메모리를 별도 고려.
- 재현: kit build 후 `art/weapons/w325/lost_and_found/identity_pack.py <id>` 실행. 재배치는 면별 RGBA 그대로 유지. `material_review.py`로 비교 이미지 재생성.
- 확인: ADS OK, 같은 방향 공면 겹침 0, 파트/기하 불변, 출력 해시, west/east/top/q/front 오프라인 렌더. 실제 Minecraft·팩 로드·파지·장전·FPS는 미실행.

## Material R2 (2026-11-05)

리시버·하부 모듈·개머리 구조·가드를 금속, 총구와 연결봉을 강철로 전환. 상부 아이보리/황색 외피 유지.

수작업 모티프: 탄창 모서리 리벳과 그림자 1텍셀; 아이보리/황색 큰 위장 블록. 폴리머/고무 기본 명도 차이 34.45.

형상 해시 불변, 아틀라스 [1024, 512], 겹침 0, ADS OK, 출력 해시 확인. kit.py 수정 없음. Blender 5시점 렌더 확인용이며 Minecraft 검수 아님.
