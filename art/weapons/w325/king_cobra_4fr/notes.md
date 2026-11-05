# King Cobra-4fr (rare linear fusion rifle, Precision) — base line_in_the_sand

- Identity kept: white vented shroud (octagon) on a long grey lower frame with the forward fin, dark coil in an open window,
  purple-camo receiver/stock with green "VEIST" logo (UV), white striped bracket + cap, hook rear sight, grey support leg
  with spike, raked grip with trigger curl, short stock with curved butt, flat bottom plate (rip battery).
- Elements: body 58 + magazine 6 = 64 (first build 24 + 2). Atlas 512x512, T 15.
- Placement: uniform 23.8 px/m, rip trigger -> z 5.73 (base trigger 5.5..5.9), rip z 0.071 -> y 8.95. Shroud muzzle z -10.05
  (base -9.9), bore y 10.04 (base LFR rails y 7.7..11.0, no single bore). Grip z 5.6..8.0 (base 6.7..9.25). Butt 12.62
  (base 15.15; rip stock is short).
- Magazine = bottom plate (mag_*), z 3.7..8.2 y 4.95..6.2 on the base moving battery (z 3.7..9.9, y 4.9..6.2).
- ADS: adscheck OK (front upper lowered to 10.9). Base uses W45 scope route / W150 sight route; skin adds no reticle and keeps
  overlay elements (none in the base surface leaf). Hook sight top 12.68 at z 4.6..5.0.
- Flat-painted (smeared projection) caps/undersides of frame, leg, grip, stock, plate, white bracket.
- Not verified: in-game first-person, the W45 scoped first-person (the scope route hides the gun), reload plate motion.

## Detail + W30 pixel-style pass (2026-11-05)
- Elements now (body magazine total): 78 10 88. STYLE pixel (master kit), flat material palette per part via MAT/RULES in
  design.py (projection only where DECAL is set; none kept except Trax Dynia's side readout, repainted as flat texels).
- Big slabs split DMW-style: cblock() = core + side chamfer strips, segmented with seam gaps; long barrels/shrouds split
  with collars; corner fillets on holes; rails/ribs/vents as cubes; accents (bores, slots, logos, stripes) painted flat.
- ADS: see final report (kit adscheck); eye ray to the base aim tip clear at +-0.15 px.
- Not verified in game: first-person, ADS, reload motion; pixel style judged on offline renders only.


## Chattering Bone 반례 정리 (W325 pass 3)
- 모든 design.py에 declash(): 무회전 동평면 겹침 시 작은 쪽을 0.012 후퇴. zfight 검사 0건.
- bevels 다이아몬드를 cham()으로(upper_flat, rec_top), stock_top과 cap 동평면 상면을 0.2 내려 분리, stock_belly 2°·butt_toe 8.5°·butt_back 6.5°·mag_belly 5°를 축정렬로, 평행한 white_strut 삭제. 93(81+12).
- 오프라인 Blender 렌더만 확인. 인게임 미검증.


## Identity pass — Ace / Izanagi 기준 (2026-11-05, 최신 결과)

### IDENTITY LIST
- 보라 회색의 세 가지 명도로 나눈 각진 위장 무늬
- 녹색 VEIST 문자 배지
- 세 개의 어두운 사선 띠를 가진 흰색 상부 브래킷
- 흰색 긴 총열 덮개와 환기 슬롯·상부 레일
- 몸체 창 안에 노출된 짙은 녹색 코일
- 올리브색 큰 그립 프레임과 하부 배터리·검정 삽입창

- 출력 요소: 93 → 97 (body 85 + magazine 12). 모든 mag_ 분할 및 기존 파지·탄창 위치 유지.
- 텍스처: T=20, 1024×1024; 주 볼륨의 모든 노출 면을 special()로 직접 도색. 1 texel 밝은 모서리/어두운 seam, 판넬 윤곽, 근거 있는 체결부, 그립 점무늬, 고유 표식을 적용. 투영 fallback 없음.
- 512 atlas는 T20에서 overflow. 근접 1P의 고유 표식·조준경·그립을 보존하기 위해 1024 폭 사용; 높이는 kit가 사용 행에 맞춰 절삭.
- 입체: 4개 림과 안쪽 후벽으로 실제 깊이의 총구 개구부. 기존 열린 프레임·스톡 창·레일 톱니·리브 유지.
- 추가 입체: 가려져 있던 흰 브래킷을 외장 면에 노출하고 같은 경사면에 맞춰 돌출 교차 제거.
- 회전 부품의 측면/끝면도 포함한 동일 방향 평면 다각형 교차 검사: 0건. 기존 axis-only declash가 놓친 겹침은 0.03px 미만의 면 후퇴로 제거.
- ADS: kit adscheck OK
- 검토: read-only .blend 알베도 사선 렌더 source_q.png, rip 측면, west/east/top/q/front 오프라인 렌더와 compare.png를 직접 확인.
- 잔여: 실제 게임의 파지·ADS·장전·다수 표시·팩 로드는 master 통합 QA에서 확인해야 한다. 임의 y=12.38 탐색선은 기존 hook 철제 조준부와 만나므로 네이티브 카메라 검증을 대체하지 않는다.


## Material pass — W123 충신 / 영원한 갈증의 허기 (2026-11-05, 최신)

- 앞선 평면 채색을 대체. STYLE=material, 모든 부품/면에 명시적 재질 배정. 원본 nx/px/q의 부품별 RGB 샘플과 실제 재질 역할로 색상을 정함.
- brushed steel/metal의 방향성 결, paint의 미세 입자, polymer의 점 질감, rubber의 교차 질감을 구분. 원본에 없는 금·천·목재는 추가하지 않음.
- special(): 양면 VEIST 문자, 국소 위장 도장 패치, 흰 브래킷의 검정 사선 띠. 나머지는 None으로 반환하여 재질 베이크를 사용. 이전의 전체 면 flat/가짜 패널 반복 도색은 호출하지 않음.
- 원본 relief는 측면의 패널·조각·홈에 사용. north/south 끝면과 새 sight 프레임, 새 cover_step/sup_band는 detail=0.
- 재질 이름 → kind / RGB:
  - `barrel_steel` → steel / (181, 182, 184)
  - `black_recess` → dark / (23, 26, 29)
  - `collar_steel` → steel / (143, 148, 147)
  - `bore_dark` → dark / (12, 15, 17)
  - `silver_steel` → steel / (135, 140, 140)
  - `coil_metal` → metal / (33, 42, 34)
  - `frame_polymer` → polymer / (66, 63, 54)
  - `camo_paint` → paint / (65, 60, 68)
  - `logo_metal` → metal / (34, 35, 40)
  - `white_paint` → paint / (206, 205, 199)
  - `grip_rubber` → rubber / (52, 49, 42)
  - `rubber_pad` → rubber / (25, 28, 29)
- Geometry SHA-256 이전 패스와 동일: `b81532b6a481309c3133901fe0bd546866399c1cb54d73da00972005420f1188`. 요소 97개, mag_ 분할·ADS·동평면 검사 결과 유지. T20, atlas 1024×1024.
- ADS: OK. 5방향 렌더·원본 비교·실제 출력 atlas 확대 확인.
- 정적 RGBA의 재질 표현이며 런타임 PBR/반사 복원은 아님. 인게임 파지·장전·ADS·팩 로드는 미검증.


## Material R2 — 노출 금속·재질 대비·모티프 (2026-11-05)

- camouflage는 상부/스톡 외피에만 유지하고 rec_body/rec_mid/rec_top은 receiver_metal로 변경. 프레임 가장자리·전방 핀·트리거·측면 레버는 frame_steel. 하부 polymer 77/75/65 대 grip rubber 27/29/24로 구분. 모티프는 흰 금속 총열의 2열 1texel 냉각 슬릿이며 기존 VEIST/사선 띠는 보존.
- elements 변경 없음. T20/atlas 크기 유지. 원본 좌표가 맞지 않아 detail=0인 면은 wear도 False로 하여 억지 마모를 추가하지 않음.

- R2 검증: 형상 SHA-256 기준선 동일, 모든 부품/면 재질 연결, atlas 크기 유지, build 및 5방향 오프라인 render 완료. ADS: kit OK. 실게임 팩 로드·파지·장전·ADS 미검증.
