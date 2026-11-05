# Trax Lysis II (rare scout rifle, High-Impact) — base frontier_justice

- Identity kept: cream/olive compact bullpup — cream front band with ribbed grey handguard and bored front cap, "VI"
  cream nose, cream sight base with a through window and dark hump, big thumb hole, small trigger opening with lug,
  tapered grip, cream stock frame with window and dark cheek, boxy cream scope, pancake drum magazine.
- Elements: body 45 + magazine 3 = 48. Atlas 512x512, T 22 (compact gun, more texels per px).
- Placement: uniform 23.8 px/m (same as the other W325 Trax rifles) — the gun is z -2.0..14.55, i.e. ~8 px shorter than the
  base (-7.9..17.1); front cap/bore at z -2.0 (bore y 10.82, base muzzle -7.9 / bore 11.43). Trigger z 6.15..6.5 (base
  6.0..6.5), grip z 7.0..9.4 (base 6.6..9.8). Whole gun 0.5 px below a bore match to fit grip and scope.
- Scope moved -0.3 y (SCOPE_DY): hollow box tube, window x 7.72..8.28 y 12.92..13.45; W151 aim tip (y 13.12..13.28,
  z -4.24) kept; eye ray from z 20 to the tip clear at +-0.15 px. The tip floats ~2.2 px ahead of the short muzzle.
- Drum magazine moved +2.75 z / +0.55 y onto the base moving magazine (centre z 12.45 y 7.45), squared to the base axis
  (rip drum tilted 12.4 deg; texture sampled through the inverse tilt). Feed neck reaches the stock floor.
- Simplified: holes are rectangular; grip is a core + two raked edge beams.
- Not verified: in-game first-person, ADS sight picture, reload motion; short length vs base hand pose.

## Detail + W30 pixel-style pass (2026-11-05)
- Elements now (body magazine total): 88 5 93. STYLE pixel (master kit), flat material palette per part via MAT/RULES in
  design.py (projection only where DECAL is set; none kept except Trax Dynia's side readout, repainted as flat texels).
- Big slabs split DMW-style: cblock() = core + side chamfer strips, segmented with seam gaps; long barrels/shrouds split
  with collars; corner fillets on holes; rails/ribs/vents as cubes; accents (bores, slots, logos, stripes) painted flat.
- ADS: see final report (kit adscheck); eye ray to the base aim tip clear at +-0.15 px.
- Not verified in game: first-person, ADS, reload motion; pixel style judged on offline renders only.


## Chattering Bone 반례 정리 (W325 pass 3)
- 모든 design.py에 declash(): 무회전 동평면 겹침 시 작은 쪽을 0.012 후퇴. zfight 검사 0건.
- stock_bottom -10° 경사판을 축정렬 cblock으로, hg_nose 경사 탭을 계단 블록으로, 구멍 fillet 측면 내삽. 95(90+5). ADS 초과는 승인된 sight_* 열린 프레임(z 5.19..7.94)만.
- 오프라인 Blender 렌더만 확인. 인게임 미검증.


## Identity pass — Ace / Izanagi 기준 (2026-11-05, 최신 결과)

### IDENTITY LIST
- 밝은 크림 노랑 외장과 검정·녹회색 불펍 몸체
- 전방 외장의 두 사선과 윤곽 삼각 표식
- 흰색 총구판, 어두운 측면 방열 핀
- 검정 링과 원형 조절 표식이 있는 노란 조준경
- 노란 테두리의 열린 개머리판 창
- 검정 삽입창과 띠가 있는 아이보리 드럼 탄창

- 출력 요소: 95 → 99 (body 94 + magazine 5). 모든 mag_ 분할 및 기존 파지·탄창 위치 유지.
- 텍스처: T=20, 1024×512; 주 볼륨의 모든 노출 면을 special()로 직접 도색. 1 texel 밝은 모서리/어두운 seam, 판넬 윤곽, 근거 있는 체결부, 그립 점무늬, 고유 표식을 적용. 투영 fallback 없음.
- 512 atlas는 T20에서 overflow. 근접 1P의 고유 표식·조준경·그립을 보존하기 위해 1024 폭 사용; 높이는 kit가 사용 행에 맞춰 절삭.
- 입체: 4개 림과 안쪽 후벽으로 실제 깊이의 총구 개구부. 기존 열린 프레임·스톡 창·레일 톱니·리브 유지.
- 회전 부품의 측면/끝면도 포함한 동일 방향 평면 다각형 교차 검사: 0건. 기존 axis-only declash가 놓친 겹침은 0.03px 미만의 면 후퇴로 제거.
- ADS: kit adscheck ABOVE BASE: sight_*의 열린 프레임. y=13.2, x=8±0.15의 9개 평행 광선은 차폐 0개.
- 검토: read-only .blend 알베도 사선 렌더 source_q.png, rip 측면, west/east/top/q/front 오프라인 렌더와 compare.png를 직접 확인.
- 잔여: 실제 게임의 파지·ADS·장전·다수 표시·팩 로드는 master 통합 QA에서 확인해야 한다.


## Material pass — W123 충신 / 영원한 갈증의 허기 (2026-11-05, 최신)

- 앞선 평면 채색을 대체. STYLE=material, 모든 부품/면에 명시적 재질 배정. 원본 nx/px/q의 부품별 RGB 샘플과 실제 재질 역할로 색상을 정함.
- brushed steel/metal의 방향성 결, paint의 미세 입자, polymer의 점 질감, rubber의 교차 질감을 구분. 원본에 없는 금·천·목재는 추가하지 않음.
- special(): 전방 삼각 표식, 조준경 조절 링, 드럼 검정 띠·삽입창. 나머지는 None으로 반환하여 재질 베이크를 사용. 이전의 전체 면 flat/가짜 패널 반복 도색은 호출하지 않음.
- 원본 relief는 측면의 패널·조각·홈에 사용. north/south 끝면과 새 sight 프레임, 새 cover_step/sup_band는 detail=0.
- front_cap/mag_drum/top_band_rib의 형태 변경·이동으로 늘어진 투영을 발견하여 detail=0으로 제거.
- 재질 이름 → kind / RGB:
  - `ivory_paint` → paint / (201, 198, 184)
  - `bore_dark` → dark / (12, 15, 17)
  - `violet_metal` → metal / (68, 67, 75)
  - `yellow_paint` → paint / (205, 199, 137)
  - `dark_metal` → metal / (46, 48, 53)
  - `green_paint` → paint / (46, 57, 52)
  - `black_recess` → dark / (23, 26, 29)
  - `grip_rubber` → rubber / (32, 37, 39)
  - `body_polymer` → polymer / (35, 40, 43)
  - `rubber_pad` → rubber / (25, 28, 29)
  - `optic_inner` → dark / (20, 24, 27)
  - `silver_steel` → steel / (135, 140, 140)
- Geometry SHA-256 이전 패스와 동일: `3d8a1efb87aaf994c4c57d19c47df2a0298ff29d90ea178f5b853e1d43d0ee75`. 요소 99개, mag_ 분할·ADS·동평면 검사 결과 유지. T20, atlas 1024×512.
- ADS: ABOVE BASE: open sight frame; centre 9 rays clear. 5방향 렌더·원본 비교·실제 출력 atlas 확대 확인.
- 정적 RGBA의 재질 표현이며 런타임 PBR/반사 복원은 아님. 인게임 파지·장전·ADS·팩 로드는 미검증.


## Material R2 — 노출 금속·재질 대비·모티프 (2026-11-05)

- 녹색 리시버 측판·후방 프레임·가드·스톡 상부를 green_frame_metal로, 트리거·스코프 마운트·탄창 목·상부 밴드 리브를 rail_steel로 재배정. body polymer 53/58/61 대 grip rubber 22/27/29로 구분. 모티프는 전방 방열 핀의 1texel 십자 가공 슬롯.
- elements 변경 없음. T20/atlas 크기 유지. 원본 좌표가 맞지 않아 detail=0인 면은 wear도 False로 하여 억지 마모를 추가하지 않음.

- R2 검증: 형상 SHA-256 기준선 동일, 모든 부품/면 재질 연결, atlas 크기 유지, build 및 5방향 오프라인 render 완료. ADS: kit ABOVE BASE 경고 유지(열린 sight 프레임). 이전 중심 9개 평행 광선 무차폐 검사와 별개이며 네이티브 ADS 검증은 아님. 실게임 팩 로드·파지·장전·ADS 미검증.
