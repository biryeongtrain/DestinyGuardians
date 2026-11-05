# Trax Dynia (rare scout rifle, Lightweight) — base patron_of_lost_causes

- Identity kept: tan/olive bullpup shell, through window in the front upper and through slot in the rear upper, hooded holo
  sight with tan cap, thumb hole above the raked grip, big trigger-guard loop, tan triangular mag-well cover, vertical box
  magazine behind the grip, slab butt pad on a rod, long thin barrel with a ported brake (bore painted on the brake face).
- Elements: body 64 + magazine 4 = 68 (no triangle adapter). Atlas 512x512, T 16.
- Placement: uniform 23.8 px/m, rip muzzle -> z -8.93, rip bore z 0.119 -> y 10.52. At this placement grip (z 7.4..10.4),
  trigger (z 6.7..6.9), magazine (z 10.4..13.1, y 5.15..9.0, vertical; base is z 10.6..13.4 tilted -8 deg) and butt (15.86)
  already match the base contract; no per-part moves.
- Sight: holo window x 7.63..8.37, y 12.3..13.1 open front/back; base W153 aim tip (y 12.68, z 6.1) is kept (overlay on) and
  a ray check from z 20 to the tip at x 8+-0.15 / y 12.68+-0.15 hits no element. Window inner faces painted dark.
- Bore of the barrel itself is 0.48 px (centre y 10.35, 0.17 px under the base bore 10.52) — muzzle flash origin unchanged.
- Not verified: in-game first-person, ADS alignment and reload magazine motion (master Vision pass).

## Detail + W30 pixel-style pass (2026-11-05)
- Elements now (body magazine total): 129 7 136. STYLE pixel (master kit), flat material palette per part via MAT/RULES in
  design.py (projection only where DECAL is set; none kept except Trax Dynia's side readout, repainted as flat texels).
- Big slabs split DMW-style: cblock() = core + side chamfer strips, segmented with seam gaps; long barrels/shrouds split
  with collars; corner fillets on holes; rails/ribs/vents as cubes; accents (bores, slots, logos, stripes) painted flat.
- ADS: see final report (kit adscheck); eye ray to the base aim tip clear at +-0.15 px.
- Not verified in game: first-person, ADS, reload motion; pixel style judged on offline renders only.


## Chattering Bone 반례 정리 (W325 pass 3)
- 모든 design.py에 declash(): 무회전 동평면 겹침 시 작은 쪽을 0.012 후퇴. zfight 검사 0건.
- guard_bottom 축 정렬·guard_toe 접합, 탄창 우물 덮개를 cover_hyp/left/top/fill로 재구성, butt_toe 무회전·butt_heel 삭제, 구멍 fillet 내삽. 135(128+7).
- 오프라인 Blender 렌더만 확인. 인게임 미검증.


## Identity pass — Ace / Izanagi 기준 (2026-11-05, 최신 결과)

### IDENTITY LIST
- 황갈색 긴 상부와 올리브색 하부 프레임
- 은색 테두리 안의 빨강·파랑 표시등, 선택기, 셀, 청록색 표시창
- 황갈색 띠가 있는 검정 홀로 조준경과 주황색 발광부
- 큰 방아쇠 울과 불펍 탄창 앞의 황갈색 삼각 커버
- 은색 볼트 패널과 검정 세로 리브 탄창
- 긴 노출 총열과 분할 총구 제동기

- 출력 요소: 135 → 147 (body 140 + magazine 7). 모든 mag_ 분할 및 기존 파지·탄창 위치 유지.
- 텍스처: T=20, 1024×512; 주 볼륨의 모든 노출 면을 special()로 직접 도색. 1 texel 밝은 모서리/어두운 seam, 판넬 윤곽, 근거 있는 체결부, 그립 점무늬, 고유 표식을 적용. 투영 fallback 없음.
- 512 atlas는 T20에서 overflow. 근접 1P의 고유 표식·조준경·그립을 보존하기 위해 1024 폭 사용; 높이는 kit가 사용 행에 맞춰 절삭.
- 입체: 4개 림과 안쪽 후벽으로 실제 깊이의 총구 개구부. 기존 열린 프레임·스톡 창·레일 톱니·리브 유지.
- 추가 입체: 표시 패널을 넓히고, 교차하던 삼각 커버의 회전 판 4개를 서로 맞닿는 계단 12개로 정리.
- 회전 부품의 측면/끝면도 포함한 동일 방향 평면 다각형 교차 검사: 0건. 기존 axis-only declash가 놓친 겹침은 0.03px 미만의 면 후퇴로 제거.
- ADS: kit adscheck OK
- 검토: read-only .blend 알베도 사선 렌더 source_q.png, rip 측면, west/east/top/q/front 오프라인 렌더와 compare.png를 직접 확인.
- 잔여: 실제 게임의 파지·ADS·장전·다수 표시·팩 로드는 master 통합 QA에서 확인해야 한다.


## Material pass — W123 충신 / 영원한 갈증의 허기 (2026-11-05, 최신)

- 앞선 평면 채색을 대체. STYLE=material, 모든 부품/면에 명시적 재질 배정. 원본 nx/px/q의 부품별 RGB 샘플과 실제 재질 역할로 색상을 정함.
- brushed steel/metal의 방향성 결, paint의 미세 입자, polymer의 점 질감, rubber의 교차 질감을 구분. 원본에 없는 금·천·목재는 추가하지 않음.
- special(): 표시 패널 테두리·빨강/파랑 표시등·선택기·상태 셀·청록색 창, 발광부의 작은 하이라이트. 나머지는 None으로 반환하여 재질 베이크를 사용. 이전의 전체 면 flat/가짜 패널 반복 도색은 호출하지 않음.
- 원본 relief는 측면의 패널·조각·홈에 사용. north/south 끝면과 새 sight 프레임, 새 cover_step/sup_band는 detail=0.
- upper_main은 원본 진단 패널이 중복 투영되어 detail=0으로 정리. 별도 진단 패널의 발색·금속 바탕을 유지.
- 재질 이름 → kind / RGB:
  - `dark_metal` → metal / (42, 47, 48)
  - `silver_steel` → steel / (135, 140, 140)
  - `bore_dark` → dark / (12, 15, 17)
  - `black_recess` → dark / (23, 26, 29)
  - `olive_shadow` → paint / (44, 52, 45)
  - `tan_paint` → paint / (129, 103, 79)
  - `tan_shadow` → paint / (102, 80, 60)
  - `readout_steel` → steel / (74, 81, 77)
  - `olive_paint` → paint / (59, 68, 60)
  - `grip_rubber` → rubber / (37, 41, 39)
  - `rubber_pad` → rubber / (25, 28, 29)
  - `amber_emitter` → glow / (216, 116, 46)
- Geometry SHA-256 이전 패스와 동일: `76b41f2171035c66962ba4264259e37d706ef3ca7c3f9e6cb7a80f8ffb44f221`. 요소 147개, mag_ 분할·ADS·동평면 검사 결과 유지. T20, atlas 1024×512.
- ADS: OK. 5방향 렌더·원본 비교·실제 출력 atlas 확대 확인.
- 정적 RGBA의 재질 표현이며 런타임 PBR/반사 복원은 아님. 인게임 파지·장전·ADS·팩 로드는 미검증.


## Material R2 — 노출 금속·재질 대비·모티프 (2026-11-05)

- 황갈색 외피만 paint로 유지하고 lower/rear 리시버·탄창 웰·그립 프레임은 olive_frame_metal, 방아쇠 울·트리거·충전부는 guard_steel로 변경. 금속 본체 78/87/80 대 고무 23/27/26로 분리. 모티프는 은색 볼트 슬라이드의 1texel 평행 가공 홈과 탄창 리브 윗선.
- elements 변경 없음. T20/atlas 크기 유지. 원본 좌표가 맞지 않아 detail=0인 면은 wear도 False로 하여 억지 마모를 추가하지 않음.

- R2 검증: 형상 SHA-256 기준선 동일, 모든 부품/면 재질 연결, atlas 크기 유지, build 및 5방향 오프라인 render 완료. ADS: kit OK. 실게임 팩 로드·파지·장전·ADS 미검증.
