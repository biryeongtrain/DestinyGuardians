# Trax Arda II (uncommon scout rifle, High-Impact) — base frontier_justice

- Identity kept: teal/gunmetal bullpup — long teal suppressor with perforated rear band (UV) and painted bore, teal
  handguard with dark rail channel and ribbed rail (UV), front sight block, teal rise to a hollow tube scope with flared
  eyepiece and turret, trigger lug + grip, thumb hole, ribbed stock with slots (UV), teal butt block, slanted box magazine.
- Elements: body 44 + magazine 2 = 46. Atlas 512x512, T 18.
- Placement: uniform 23.8 px/m, rip trigger -> z 6.2 (base trigger 6.0..6.5), rip scope axis -> y 13.2 = W151 eye line
  (aim tip y 13.12..13.28, z -4.24, kept); centre-line x offset 0.08 px removed. Scope window x 7.72..8.28 y 12.95..13.45,
  eye ray from z 20 to the tip clear at +-0.15 px. Suppressor muzzle z -8.95 (base -7.9), bore y 11.15 (base 11.43).
  Butt z 14.85 (base 17.1): the gun is ~2 px shorter at the rear.
- Grip z 6.6..9.0 (base 6.6..9.8). Magazine moved +1.5 z / +0.55 y toward the base moving magazine (rip tilt kept), centre
  ~0.8 px ahead of the base magazine centre; a full match would hang it behind the short butt.
- Not verified: in-game first-person, ADS, reload motion.

## Detail + W30 pixel-style pass (2026-11-05)
- Elements now (body magazine total): 94 2 96. STYLE pixel (master kit), flat material palette per part via MAT/RULES in
  design.py (projection only where DECAL is set; none kept except Trax Dynia's side readout, repainted as flat texels).
- Big slabs split DMW-style: cblock() = core + side chamfer strips, segmented with seam gaps; long barrels/shrouds split
  with collars; corner fillets on holes; rails/ribs/vents as cubes; accents (bores, slots, logos, stripes) painted flat.
- ADS: see final report (kit adscheck); eye ray to the base aim tip clear at +-0.15 px.
- Not verified in game: first-person, ADS, reload motion; pixel style judged on offline renders only.


## Chattering Bone 반례 정리 (W325 pass 3)
- 모든 design.py에 declash(): 무회전 동평면 겹침 시 작은 쪽을 0.012 후퇴. zfight 검사 0건.
- hg_belly 2.3°·upper_rise 8.4°·guard_lug_toe 5.7°·stock_belly 19° 경사판을 축정렬 블록/계단으로 교체, fillet 내삽. 102(100+2). ADS 초과는 승인된 sight_* 구간만.
- 오프라인 Blender 렌더만 확인. 인게임 미검증.


## Identity pass — Ace / Izanagi 기준 (2026-11-05, 최신 결과)

### IDENTITY LIST
- 청록색 소음기·상부 외장과 짙은 회색 하부 프레임
- 소음기 뒤 은색 다공성 열 차폐 밴드
- 긴 측면 홈 안의 분리된 레일 톱니
- 청록색 개머리판 끝의 검정 사각 삽입부
- 금속 조절부를 가진 청록색 망원 조준경
- 세 개의 밝은 테두리 패널이 있는 경사진 탄창

- 출력 요소: 102 → 112 (body 110 + magazine 2). 모든 mag_ 분할 및 기존 파지·탄창 위치 유지.
- 텍스처: T=20, 1024×512; 주 볼륨의 모든 노출 면을 special()로 직접 도색. 1 texel 밝은 모서리/어두운 seam, 판넬 윤곽, 근거 있는 체결부, 그립 점무늬, 고유 표식을 적용. 투영 fallback 없음.
- 512 atlas는 T20에서 overflow. 근접 1P의 고유 표식·조준경·그립을 보존하기 위해 1024 폭 사용; 높이는 kit가 사용 행에 맞춰 절삭.
- 입체: 4개 림과 안쪽 후벽으로 실제 깊이의 총구 개구부. 기존 열린 프레임·스톡 창·레일 톱니·리브 유지.
- 추가 입체: 소음기 열 차폐 밴드를 2열의 실제 슬롯과 안쪽 코어로 재구성.
- 회전 부품의 측면/끝면도 포함한 동일 방향 평면 다각형 교차 검사: 0건. 기존 axis-only declash가 놓친 겹침은 0.03px 미만의 면 후퇴로 제거.
- ADS: kit adscheck ABOVE BASE: sight_*의 열린 프레임. y=13.2, x=8±0.15의 9개 평행 광선은 차폐 0개.
- 검토: read-only .blend 알베도 사선 렌더 source_q.png, rip 측면, west/east/top/q/front 오프라인 렌더와 compare.png를 직접 확인.
- 잔여: 실제 게임의 파지·ADS·장전·다수 표시·팩 로드는 master 통합 QA에서 확인해야 한다.


## Material pass — W123 충신 / 영원한 갈증의 허기 (2026-11-05, 최신)

- 앞선 평면 채색을 대체. STYLE=material, 모든 부품/면에 명시적 재질 배정. 원본 nx/px/q의 부품별 RGB 샘플과 실제 재질 역할로 색상을 정함.
- brushed steel/metal의 방향성 결, paint의 미세 입자, polymer의 점 질감, rubber의 교차 질감을 구분. 원본에 없는 금·천·목재는 추가하지 않음.
- special(): 개머리판 끝의 검정 사각 삽입부만. 나머지는 None으로 반환하여 재질 베이크를 사용. 이전의 전체 면 flat/가짜 패널 반복 도색은 호출하지 않음.
- 원본 relief는 측면의 패널·조각·홈에 사용. north/south 끝면과 새 sight 프레임, 새 cover_step/sup_band는 detail=0.
- 재질 이름 → kind / RGB:
  - `teal_paint` → paint / (57, 79, 75)
  - `black_recess` → dark / (23, 26, 29)
  - `bore_dark` → dark / (12, 15, 17)
  - `dark_metal` → metal / (47, 53, 52)
  - `silver_steel` → steel / (135, 140, 140)
  - `teal_shadow` → paint / (44, 64, 60)
  - `receiver_metal` → metal / (70, 74, 73)
  - `grip_polymer` → polymer / (48, 52, 51)
  - `rubber_pad` → rubber / (25, 28, 29)
  - `optic_inner` → dark / (20, 24, 27)
  - `vent_steel` → steel / (127, 134, 132)
- Geometry SHA-256 이전 패스와 동일: `f6a5480080c74cc2829a29078832a5091197a07da50487867d96afbef4d568ba`. 요소 112개, mag_ 분할·ADS·동평면 검사 결과 유지. T20, atlas 1024×512.
- ADS: ABOVE BASE: open sight frame; centre 9 rays clear. 5방향 렌더·원본 비교·실제 출력 atlas 확대 확인.
- 정적 RGBA의 재질 표현이며 런타임 PBR/반사 복원은 아님. 인게임 파지·장전·ADS·팩 로드는 미검증.


## Material R2 — 노출 금속·재질 대비·모티프 (2026-11-05)

- 레일 톱니·전방 블록·스코프 마운트·방아쇠 울을 rail_steel로, 탄창을 magazine_metal로, 핸드가드 안쪽 코어를 노출 metal로 배정. receiver metal 87/94/94, grip polymer 54/59/58, butt rubber 23/27/26로 대비 분리. 모티프는 실제 탄창의 3개 프레스 패널을 1texel 윤곽으로 표현.
- elements 변경 없음. T20/atlas 크기 유지. 원본 좌표가 맞지 않아 detail=0인 면은 wear도 False로 하여 억지 마모를 추가하지 않음.

- R2 검증: 형상 SHA-256 기준선 동일, 모든 부품/면 재질 연결, atlas 크기 유지, build 및 5방향 오프라인 render 완료. ADS: kit ABOVE BASE 경고 유지(열린 sight 프레임). 이전 중심 9개 평행 광선 무차폐 검사와 별개이며 네이티브 ADS 검증은 아님. 실게임 팩 로드·파지·장전·ADS 미검증.
