# Reginar-B (W325, rare rocket launcher, Precision) — base pyroclastic_flow

- Identity kept: square dark tube with white muzzle cap and band, front housing, long carry handle, under-rail with
  vertical foregrip, light receiver band over the dark lower receiver/magwell/trigger, raked pistol grip, white collar
  block and olive rear tube with white top/bottom rails and bands (HAKKE stamp from the rip).
- Elements: body 38 + magazine 6 = 44 (cap 1000). Atlas 512x512 at T=14.
- Uniform 24 px/m proper rotation, anchored on the base W201 hands: pistol-grip middle -> (z 14.53, y 7.7); foregrip
  lands z ~8.1 / y ~8.8 (base support hand 7.5 / 9.38). Tube axis y 11.71 (base 11.9).
- Deliberate deviation: the tube spans z 0.7..27.1 vs base -7.8..19.2 (Reginar's grips sit near its front); ~8 px less
  tube ahead of the hands and ~8 px more behind the shoulder. Master: please judge in first person / third person.
- Side optic mirrored to +X and moved onto the base ADS sight (10.132, 12.69, eye +z): open 0.76 px window, amber pin
  below centre, 2.6 px tunnel; it sits above the tube top (12.66) like the base optic.
- Magazine = base reload rocket envelope (z 10.7..17.5), olive with grey nose; it lies inside the tube section.
- Leaf split caveat: base reload bank also has `_cradle` and `_lever` leaves; current WeaponSkinAssets treats them as
  whole-gun leaves (would duplicate the full gun). Needs master decision (empty them or add parts keys).
- Not verified: in-game first/third-person framing with the rear-shifted tube, ADS aperture, reload path, hand contact.

## W325 detail + pixel-style pass (2026-11-05)
- Elements now: 118 body + 6 magazine = 124. Atlas 512, kit STYLE=pixel, FLAT_TOL 34, PALETTE 16;
  identity repainted as flat colour blocks in special() (no projection grime), chamfered (45 deg strips) edges via cbox/rc,
  long slabs split into segments with recessed grooves; no shallow rotated slabs (Chattering Bone rule).
- kit adscheck: OK. Offline ADS view sim (/tmp/m10/adsview.py, camera 13 px behind the base sight) shows the centre clear.
- ADS fix: rear tube compressed (rip behind the receiver at 0.18x; tube ends z ~18.8 instead of 27) so the big side
  slab no longer covers the left/bottom of the ADS view; tube length is now shorter than the rip (deliberate).
- No separate cradle/lever parts: base `_cradle`/`_lever` leaves stay empty under the master's new split rule.


## W325 Identity pass — 2026-11-05

### IDENTITY LIST
- 짙은 회색 총몸과 올리브 후방관
- 백색 링과 하부 레일
- HAKKE 표식과 데이터 스트립
- 손잡이형 운반 고리
- 리브가 있는 수직 앞손잡이
- 황색 핀의 측면 조준기

총몸 패널을 실제 홈으로 분할하고 레일 이빨 6개 추가. 후방 총몸은 z=12.3 뒤 28%, 장전 탄체는 50%로 압축: 방아쇠/그립/조준 좌표 유지, mag_ 이름과 분리는 유지. 단축된 관에서 탄체가 돌출되지 않도록 탄체 길이도 함께 줄임. 장전 애니메이션 경로는 미수정이며 재검수 필요.

모든 보이는 면은 `special()` 직접 도색으로 지정했다. 면 크기에 맞춘 1텍셀 밝은 윗모서리/어두운 아랫선, 패널 홈, 작은 고정나사와 재질 대비를 사용한다. 기존 photographic projection은 새 표면 페인트의 fallback으로 사용하지 않는다.

요소 124 → 134, T20, 아틀라스 [1024, 512]. 런처 5종은 512에서 T20 overflow가 확인되어 1024×512로 배치했으며 가까운 면의 1텍셀 글리프/슬릿 보존을 위한 선택이다. 검 2종은 512×512.

검증: kit build/JSON·UV 생성, west/east/top/q/front 렌더 및 rip 비교, kit adscheck OK. adscheck는 높이 프로파일 검사라 실제 시야 점유율을 보증하지 않는다. master의 새 client ADS/1P/3P/장전/10–20개 표시는 아직 미검증. 기존 cbox/tube8의 교차 내부 면까지 전수 coplanar 무결성을 보증하지 않는다; 새 이빨/리브는 기존 면에 끝이 맞닿도록 설계했다.

참조: SKILL.md + ace-izanagi-study.md, main의 Ace(87)/Izanagi(79) JSON 및 /tmp/w325-ref-ace-izanagi.png, 각 proj_cache 원본 측면/사선, W30/Dead Man Walking 원칙. 검의 노란 화면은 master 확인상 3인칭 플레이어로서 스킨 버그가 아니므로 parts 키는 변경하지 않았다.

마지막 silhouette 조정: 기존 PwMap 후방 계수는 0.18→0.50으로 복원하고 위 후처리를 적용하여 색상 정체성인 올리브/주황 후방관이 남도록 했다. 최종 후방관 끝 z=15.011; 장전 탄체 끝 z=14.9.


## Material pass — 2026-11-05 (Identity pass의 평면 도색 설명을 대체)

| 이름 | 종류 | RGB |
|---|---|---|
| ivory | paint | (205, 207, 199) |
| charcoal | metal | (69, 66, 61) |
| polymer | polymer | (34, 37, 35) |
| steel | steel | (155, 160, 158) |
| rubber | rubber | (25, 28, 27) |
| dark | dark | (15, 19, 19) |
| gunmetal | metal | (65, 69, 69) |
| amber | glow | (218, 145, 33) |
| olive | paint | (78, 89, 44) |

`special()` 잔존 범위: HAKKE 픽셀 글자, 전방 데이터 스트립, 탄체 띠, 보어 암부. 나머지 면은 재질 베이크가 처리한다.

T20, atlas [1024, 512], PNG 215,592 bytes. 모든 요소/면의 재질이 명시되어 auto fallback은 없다. 5×5 면 표본에서 special 비율 0.418% (면적 가중 수치가 아님).

후방관 ADS 압축을 역변환한 뒤 원본 relief를 샘플링한다. 위치를 바꾼 조준기, 장전 탄체, 추가 리브, 회전 부품, 얇은 검 측면 이외 면은 detail=0. Cup의 변형된 하부/프레임과 Weaver의 압축 총몸/케이지는 늘어지는 투영을 끄고 재질 결만 남겼다.

검증: 직전 geometry SHA-256 동일, 파트/UV/출력 해시, material 전체 매핑·희소 special 검사 통과. kit build, adscheck OK, 5방향 렌더와 rip 비교 확인. 새 Gradle/Minecraft 실행·실화면 QA·전체 배포 ZIP 측정은 하지 않았다. geometry를 바꾸지 않아 이전 coplanar 검증 한계도 유지된다.


## Material R2 — 2026-11-05 (R1 재질 재배정을 대체)

포구·밴드·칼라 → lightsteel, 가드·탄창 수용부·그립 장착부 → darksteel. 올리브색은 후방 도장 외피에 유지.

HAKKE 각인 띠, 백색 데이터 눈금.

대표 재질 명도 차이 27.89. 원소/좌표/회전/부품명 SHA-256 동일, 아틀라스 크기 유지, adscheck OK. 실제 인게임 검증은 master 단계에 남음.
