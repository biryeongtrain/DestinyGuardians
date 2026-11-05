# Cup-Bearer SA/2 (W325, rare rocket launcher, Adaptive) — base bellowing_giant

- Identity kept: long olive rear launch tube with end cap/band, open front cage (twin rails + end frame), cream/green camo
  upper receiver with sloped tail and red levers, top bracket, thumbhole stock with dark raked grip and trigger loop,
  checkered angled foregrip, +X side optic.
- Elements: body 42 + magazine 7 = 49 (cap 1000). Atlas 512x512 at T=14 texel/px.
- Rip mapped uniformly at 22.7 px/m as a proper rotation (model X = -rip x; decals not mirrored). Trigger z 6.48 (base 6.6), grip 7.4..8.8 raked
  (base 7.35..8.4), foregrip hinge z ~2.2 (base 1.8..2.5), tube axis y 12.04 (base 11.9), muzzle cage front z -2.6
  (base -5.55), rear tube end z 24.35 (base 21.45; extends 2.9 further behind the shoulder).
- Deviations: rip side optic (rip +x -> model -X) mirrored onto +X and moved onto the base ADS sight line (aperture centre 9.55,12.10, red pin below centre, open
  0.84 px window, 2.5 px deep tunnel); foregrip rake reduced 45->15 deg and moved +0.3 z.
- Magazine = base reload rocket envelope (z -2.4..3.2), hand painted olive/cream/red; tail fins sit just inside the
  open front cage (cage front -2.6).
- Not verified: in-game first-person/ADS framing through the side optic tunnel, reload rocket path vs the cage rails,
  hand contact on the shifted foregrip.

## W325 detail + pixel-style pass (2026-11-05)
- Elements now: 118 body + 7 magazine = 125. Atlas 512, kit STYLE=pixel, FLAT_TOL 34, PALETTE 16;
  identity repainted as flat colour blocks in special() (no projection grime), chamfered (45 deg strips) edges via cbox/rc,
  long slabs split into segments with recessed grooves; no shallow rotated slabs (Chattering Bone rule).
- kit adscheck: OK. Offline ADS view sim (/tmp/m10/adsview.py, camera 13 px behind the base sight) shows the centre clear.
- ADS fixes: receiver behind z 3.4 lowered to y 13.2 (squashed rip receiver), side optic tunnel shortened to z 4.0..5.6,
  rear launch tube compressed (rip behind y 0.10 at 0.40x; tube now ends z ~16.6 instead of 24.4) so it no longer
  fills the left half of the ADS view. Camo painted as two large cream/green blobs.


## W325 Identity pass — 2026-11-05

### IDENTITY LIST
- 크림색 프레임과 연두색 위장 패널
- 올리브색 후방 발사관의 링
- 열린 직사각형 포구 케이지
- 붉은 측면 레버
- 엄지 구멍이 뚫린 개머리판
- 오른쪽 개방형 보조 조준기

측면 벤트 리브 4개 추가, 후방 발사관을 z=10 이후 30%로 압축. 방아쇠/그립/탄체는 유지.

모든 보이는 면은 `special()` 직접 도색으로 지정했다. 면 크기에 맞춘 1텍셀 밝은 윗모서리/어두운 아랫선, 패널 홈, 작은 고정나사와 재질 대비를 사용한다. 기존 photographic projection은 새 표면 페인트의 fallback으로 사용하지 않는다.

요소 125 → 129, T20, 아틀라스 [1024, 512]. 런처 5종은 512에서 T20 overflow가 확인되어 1024×512로 배치했으며 가까운 면의 1텍셀 글리프/슬릿 보존을 위한 선택이다. 검 2종은 512×512.

검증: kit build/JSON·UV 생성, west/east/top/q/front 렌더 및 rip 비교, kit adscheck OK. adscheck는 높이 프로파일 검사라 실제 시야 점유율을 보증하지 않는다. master의 새 client ADS/1P/3P/장전/10–20개 표시는 아직 미검증. 기존 cbox/tube8의 교차 내부 면까지 전수 coplanar 무결성을 보증하지 않는다; 새 이빨/리브는 기존 면에 끝이 맞닿도록 설계했다.

참조: SKILL.md + ace-izanagi-study.md, main의 Ace(87)/Izanagi(79) JSON 및 /tmp/w325-ref-ace-izanagi.png, 각 proj_cache 원본 측면/사선, W30/Dead Man Walking 원칙. 검의 노란 화면은 master 확인상 3인칭 플레이어로서 스킨 버그가 아니므로 parts 키는 변경하지 않았다.


## Material pass — 2026-11-05 (Identity pass의 평면 도색 설명을 대체)

| 이름 | 종류 | RGB |
|---|---|---|
| olive | metal | (103, 108, 80) |
| gunmetal | metal | (65, 69, 69) |
| ivory | paint | (211, 201, 186) |
| red | paint | (151, 39, 30) |
| steel | steel | (157, 158, 143) |
| dark | dark | (15, 19, 19) |
| polymer | polymer | (49, 49, 39) |
| rubber | rubber | (25, 28, 27) |

`special()` 잔존 범위: 원본 위치의 녹색 위장 스텐실, 붉은 레버의 밝은 표시, 측면 벤트, 탄체 띠, 보어 암부. 나머지 면은 재질 베이크가 처리한다.

T20, atlas [1024, 512], PNG 243,688 bytes. 모든 요소/면의 재질이 명시되어 auto fallback은 없다. 5×5 면 표본에서 special 비율 9.84% (면적 가중 수치가 아님).

후방관 ADS 압축을 역변환한 뒤 원본 relief를 샘플링한다. 위치를 바꾼 조준기, 장전 탄체, 추가 리브, 회전 부품, 얇은 검 측면 이외 면은 detail=0. Cup의 변형된 하부/프레임과 Weaver의 압축 총몸/케이지는 늘어지는 투영을 끄고 재질 결만 남겼다.

검증: 직전 geometry SHA-256 동일, 파트/UV/출력 해시, material 전체 매핑·희소 special 검사 통과. kit build, adscheck OK, 5방향 렌더와 rip 비교 확인. 새 Gradle/Minecraft 실행·실화면 QA·전체 배포 ZIP 측정은 하지 않았다. geometry를 바꾸지 않아 이전 coplanar 검증 한계도 유지된다.


## Material R2 — 2026-11-05 (R1 재질 재배정을 대체)

전방 프레임·레일·하부 빔·개머리판 기둥 → warmsteel, 하부 리시버·가드 → darksteel. 크림/올리브 위장은 외피 패널에만 유지.

1텍셀 냉각 슬릿과 붉은 레버 표시; 크림/연두 2색 큰 위장 블록.

대표 재질 명도 차이 28.87. 원소/좌표/회전/부품명 SHA-256 동일, 아틀라스 크기 유지, adscheck OK. 실제 인게임 검증은 master 단계에 남음.
