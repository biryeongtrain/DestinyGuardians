# Stampede Mk.32 (W325, rare grenade launcher, Rapid-Fire; no exact frame row) — base salvager_s_salvo

- Identity kept: green-camo shroud with white top band and muzzle cap, trapezoid front grip loop, dark drum cage
  (wide front post, drum box with the visible round, side lug), green upper receiver with the blue display, white rear
  sight block, raked grip + trigger, thumbhole stock with the twin square cut-outs (painted), white/black butt pad.
- Elements: body 17 + magazine(moving front group) 12 = 29 (cap 1000). Atlas 512x512 (T=14).
- Uniform 27.7 px/m proper rotation anchored on the base W201 hands: grip middle -> (z 8.24, y 8.18); slanted front
  loop post ~z -2.1 (base -2.14). Muzzle z -6.5 (base -7.83), butt z 16.4 (base 17.17).
- Added a small front ring sight on a 1.1 px tower framing the base iron sight centre (8, 14.30, -2.1).
- LEAF SPLIT (needs master): parts.magazine = moving front group (brl_*) for the base `_barrel` leaf; parts.body for
  `_body`; `_round` should keep base shell art (same as Plemusa-B).
- Simplifications: thumbhole and guard opening are rectangular; drum internals are UV only.
- Not verified: in-game reload motion, ADS ring framing, hand contact.

## W325 detail + pixel-style pass (2026-11-05)
- Elements now: 89 body + 31 magazine = 120. Atlas 512, kit STYLE=pixel, FLAT_TOL 34, PALETTE 16;
  identity repainted as flat colour blocks in special() (no projection grime), chamfered (45 deg strips) edges via cbox/rc,
  long slabs split into segments with recessed grooves; no shallow rotated slabs (Chattering Bone rule).
- kit adscheck: OK. Offline ADS view sim (/tmp/m10/adsview.py, camera 13 px behind the base sight) shows the centre clear.
- parts.magazine (brl_*, 31 elements) = moving front group for `_barrel`. Camo = 3-tone painted blobs.


## W325 Identity pass — 2026-11-05

### IDENTITY LIST
- 녹색 3색 위장
- 크림색 상부 띠와 포구 캡
- 검정 드럼 케이지
- 파란 상태 표시창
- 천공된 전방 통풍구
- 엄지 구멍과 삼각 앞손잡이

전방 통풍구 리브 5개 추가; 기존 brl_ 분리에 포함. 작은 천공, 파란 상태창, 위장 블록, 패널선 직접 페인트.

모든 보이는 면은 `special()` 직접 도색으로 지정했다. 면 크기에 맞춘 1텍셀 밝은 윗모서리/어두운 아랫선, 패널 홈, 작은 고정나사와 재질 대비를 사용한다. 기존 photographic projection은 새 표면 페인트의 fallback으로 사용하지 않는다.

요소 120 → 125, T20, 아틀라스 [1024, 512]. 런처 5종은 512에서 T20 overflow가 확인되어 1024×512로 배치했으며 가까운 면의 1텍셀 글리프/슬릿 보존을 위한 선택이다. 검 2종은 512×512.

검증: kit build/JSON·UV 생성, west/east/top/q/front 렌더 및 rip 비교, kit adscheck OK. adscheck는 높이 프로파일 검사라 실제 시야 점유율을 보증하지 않는다. master의 새 client ADS/1P/3P/장전/10–20개 표시는 아직 미검증. 기존 cbox/tube8의 교차 내부 면까지 전수 coplanar 무결성을 보증하지 않는다; 새 이빨/리브는 기존 면에 끝이 맞닿도록 설계했다.

참조: SKILL.md + ace-izanagi-study.md, main의 Ace(87)/Izanagi(79) JSON 및 /tmp/w325-ref-ace-izanagi.png, 각 proj_cache 원본 측면/사선, W30/Dead Man Walking 원칙. 검의 노란 화면은 master 확인상 3인칭 플레이어로서 스킨 버그가 아니므로 parts 키는 변경하지 않았다.


## Material pass — 2026-11-05 (Identity pass의 평면 도색 설명을 대체)

| 이름 | 종류 | RGB |
|---|---|---|
| ivory | paint | (210, 207, 191) |
| olive | paint | (66, 88, 45) |
| gunmetal | metal | (54, 57, 49) |
| dark | dark | (15, 19, 19) |
| polymer | polymer | (39, 43, 36) |
| blue_glass | lens | (28, 80, 120) |
| rubber | rubber | (25, 28, 27) |

`special()` 잔존 범위: 원본 위치의 진녹색/연두색 위장 스텐실, 파란 상태창·밝은 표시점, 통풍구 천공, 보어 암부. 나머지 면은 재질 베이크가 처리한다.

T20, atlas [1024, 512], PNG 342,074 bytes. 모든 요소/면의 재질이 명시되어 auto fallback은 없다. 5×5 면 표본에서 special 비율 1.605% (면적 가중 수치가 아님).

후방관 ADS 압축을 역변환한 뒤 원본 relief를 샘플링한다. 위치를 바꾼 조준기, 장전 탄체, 추가 리브, 회전 부품, 얇은 검 측면 이외 면은 detail=0. Cup의 변형된 하부/프레임과 Weaver의 압축 총몸/케이지는 늘어지는 투영을 끄고 재질 결만 남겼다.

검증: 직전 geometry SHA-256 동일, 파트/UV/출력 해시, material 전체 매핑·희소 special 검사 통과. kit build, adscheck OK, 5방향 렌더와 rip 비교 확인. 새 Gradle/Minecraft 실행·실화면 QA·전체 배포 ZIP 측정은 하지 않았다. geometry를 바꾸지 않아 이전 coplanar 검증 한계도 유지된다.


## Material R2 — 2026-11-05 (R1 재질 재배정을 대체)

리시버 하부·드럼 기둥·루프·가드 → gunmetal, 포구·밴드·조준기·버트 캡 → lightsteel. 녹색 위장은 외피에만 유지.

1텍셀 천공/냉각 구멍과 파란 표시창; 녹색 3색 큰 위장 블록.

대표 재질 명도 차이 36.90. 원소/좌표/회전/부품명 SHA-256 동일, 아틀라스 크기 유지, adscheck OK. 실제 인게임 검증은 master 단계에 남음.
