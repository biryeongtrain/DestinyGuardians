# Fare-Thee-Well (uncommon scout rifle, Lightweight) — base patron_of_lost_causes

- Identity kept: maroon receiver with top rail and recessed ejection port, ribbed grey handguard with open slots, offset
  gas tube with angled riser, long suppressor (bore painted), thumbhole bullpup stock with second (rear) window, cheek
  riser, raked curved magazine behind the grip, small rear sight fin.
- Elements: body 51 + magazine 2 = 53. Atlas 512x512, T 16.
- Placement: uniform 23.8 px/m; rip trigger (y -0.057) -> z 7.3 (whole gun 0.5 px behind the read frame so the raked grip,
  z 8.0..9.75, sits on the base grip z 8.3..9.4), bore -> y 10.52. Suppressor reaches z -9.45 (base muzzle -8.93),
  butt 16.42 (base 16.1).
- Magazine: shape kept (22 deg rake, 2.25 px thick) but moved +0.8 z / +0.3 y (part transform in model2world) so its centre
  sits ~0.3 px from the base moving magazine (base centre z 12.1, y 7.0); mag top buried in the stock belly.
- Sight: no optic on this rip. Rear fin kept and given two ears (x 7.7..7.86 / 8.14..8.3, top 12.82) so the base W153 aim
  tip (y 12.68, z 6.1) is framed in a notch; centre ray clear (ears touch only at +-0.15 px).
- Simplified: thumbhole and rear window are rectangular (rip is rounded), grip finger ribs are UV only.
- Not verified: in-game first-person, ADS, reload magazine motion.

## Detail + W30 pixel-style pass (2026-11-05)
- Elements now (body magazine total): 129 5 134. STYLE pixel (master kit), flat material palette per part via MAT/RULES in
  design.py (projection only where DECAL is set; none kept except Trax Dynia's side readout, repainted as flat texels).
- Big slabs split DMW-style: cblock() = core + side chamfer strips, segmented with seam gaps; long barrels/shrouds split
  with collars; corner fillets on holes; rails/ribs/vents as cubes; accents (bores, slots, logos, stripes) painted flat.
- ADS: see final report (kit adscheck); eye ray to the base aim tip clear at +-0.15 px.
- Not verified in game: first-person, ADS, reload motion; pixel style judged on offline renders only.


## Chattering Bone 반례 정리 (W325 pass 3)
- 모든 design.py에 declash(): 무회전 동평면 겹침 시 작은 쪽을 0.012 후퇴. zfight 검사 0건.
- bev 다이아몬드(모서리 돌출)를 cham()으로 교체: cblock 계단 모서리를 45° 스트립이 정확히 메움(front_plate, hg_upper, hg_belly, rec_upper, stock_top, cheek_riser). hg_belly 4° 경사판을 축정렬 블록으로, hg_lower를 receiver 하부와 겹치지 않게 분할(hg_lower_tail). stock_belly·butt_toe·grip_sweep 경사판 삭제→ well_front/stock_lower 계단, cheek 41° 끝판을 계단 블록으로, fillet 측면 0.015 내삽. 155(150+5).
- 오프라인 Blender 렌더만 확인. 인게임 미검증.


## Identity pass — Ace / Izanagi 기준 (2026-11-05, 최신 결과)

### IDENTITY LIST
- 검붉은 긴 리시버와 검정 상부 레일, 은색 노출 볼트
- 검정 소음기와 은색 링·널링 칼라
- 회색 핸드가드의 실제 슬롯·리브와 분리 가스관
- 두 개의 빈 창이 있는 검정 불펍 스톡
- 스톡 측면의 이중 은색 삼각 배지
- 은색 세로 테두리를 가진 경사진 검정 탄창

- 출력 요소: 155 → 159 (body 154 + magazine 5). 모든 mag_ 분할 및 기존 파지·탄창 위치 유지.
- 텍스처: T=20, 512×512; 주 볼륨의 모든 노출 면을 special()로 직접 도색. 1 texel 밝은 모서리/어두운 seam, 판넬 윤곽, 근거 있는 체결부, 그립 점무늬, 고유 표식을 적용. 투영 fallback 없음.
- 입체: 4개 림과 안쪽 후벽으로 실제 깊이의 총구 개구부. 기존 열린 프레임·스톡 창·레일 톱니·리브 유지.
- 회전 부품의 측면/끝면도 포함한 동일 방향 평면 다각형 교차 검사: 0건. 기존 axis-only declash가 놓친 겹침은 0.03px 미만의 면 후퇴로 제거.
- ADS: kit adscheck OK
- 검토: read-only .blend 알베도 사선 렌더 source_q.png, rip 측면, west/east/top/q/front 오프라인 렌더와 compare.png를 직접 확인.
- 잔여: 실제 게임의 파지·ADS·장전·다수 표시·팩 로드는 master 통합 QA에서 확인해야 한다.


## Material pass — W123 충신 / 영원한 갈증의 허기 (2026-11-05, 최신)

- 앞선 평면 채색을 대체. STYLE=material, 모든 부품/면에 명시적 재질 배정. 원본 nx/px/q의 부품별 RGB 샘플과 실제 재질 역할로 색상을 정함.
- brushed steel/metal의 방향성 결, paint의 미세 입자, polymer의 점 질감, rubber의 교차 질감을 구분. 원본에 없는 금·천·목재는 추가하지 않음.
- special(): 스톡의 이중 은색 삼각 배지 윤곽만. 나머지는 None으로 반환하여 재질 베이크를 사용. 이전의 전체 면 flat/가짜 패널 반복 도색은 호출하지 않음.
- 원본 relief는 측면의 패널·조각·홈에 사용. north/south 끝면과 새 sight 프레임, 새 cover_step/sup_band는 detail=0.
- 재질 이름 → kind / RGB:
  - `black_anodized` → metal / (41, 44, 47)
  - `bore_dark` → dark / (12, 15, 17)
  - `silver_steel` → steel / (135, 140, 140)
  - `dark_steel` → metal / (65, 69, 71)
  - `grey_polymer` → polymer / (73, 74, 73)
  - `maroon_paint` → paint / (83, 57, 59)
  - `black_recess` → dark / (23, 26, 29)
  - `maroon_shadow` → paint / (65, 44, 47)
  - `grip_rubber` → rubber / (66, 67, 66)
  - `stock_polymer` → polymer / (43, 46, 48)
  - `rubber_pad` → rubber / (25, 28, 29)
- Geometry SHA-256 이전 패스와 동일: `b80ac267a8bee68cdf9069a52f2abe418ff90bc0e5ae9aeaf4c02d210709612c`. 요소 159개, mag_ 분할·ADS·동평면 검사 결과 유지. T20, atlas 512×512.
- ADS: OK. 5방향 렌더·원본 비교·실제 출력 atlas 확대 확인.
- 정적 RGBA의 재질 표현이며 런타임 PBR/반사 복원은 아님. 인게임 파지·장전·ADS·팩 로드는 미검증.


## Material R2 — 노출 금속·재질 대비·모티프 (2026-11-05)

- 레일·방아쇠 울·트리거·핸드가드 리브·전방판·리시버 하부를 machined_frame metal로, 볼트·핀·충전 손잡이를 steel로 재배정. stock polymer 57/61/63 대 grip rubber 24/27/29로 명도 분리. 모티프는 탄창의 3개 세로 리브와 소음기 칼라의 1texel 홈.
- elements 변경 없음. T20/atlas 크기 유지. 원본 좌표가 맞지 않아 detail=0인 면은 wear도 False로 하여 억지 마모를 추가하지 않음.

- R2 검증: 형상 SHA-256 기준선 동일, 모든 부품/면 재질 연결, atlas 크기 유지, build 및 5방향 오프라인 render 완료. ADS: kit OK. 실게임 팩 로드·파지·장전·ADS 미검증.
