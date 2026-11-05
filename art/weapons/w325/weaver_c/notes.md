# Weaver-C (W325, rare rocket launcher, Precision) — base pyroclastic_flow

- Identity kept: cream front tube with dark top shroud, white muzzle cap, side rail cages (zig-zag braces painted from
  the rip), under-rail + vertical foregrip, cream receiver with dark side window, orange top fin, light band over the
  rust-brown lower receiver, raked checkered grip, orange rear tube with the panel pattern and HAKKE stamp, rear hoop.
- Elements: body 42 + magazine 6 = 48 (cap 1000). Atlas 512x512 at T=14.
- Same fit as Reginar-B (shared HAKKE frame): uniform 24 px/m proper rotation anchored on the base W201 grip hand
  (z 14.53, y 7.7), foregrip z ~8.1; tube z 0.4..27.0 vs base -7.8..19.2 (deliberate, hands first).
- Side optic mirrored to +X, open aperture on the base ADS sight (10.132, 12.69), amber pin; from the -X side the
  optic box hides most of the orange top fin.
- Magazine = base reload rocket envelope (z 10.7..17.5) painted orange with cream nose.
- Same `_cradle`/`_lever` leaf caveat as Reginar-B.
- Not verified: in-game framing, ADS aperture, reload path, hand contact.

## W325 detail + pixel-style pass (2026-11-05)
- Elements now: 105 body + 6 magazine = 111. Atlas 512, kit STYLE=pixel, FLAT_TOL 34, PALETTE 16;
  identity repainted as flat colour blocks in special() (no projection grime), chamfered (45 deg strips) edges via cbox/rc,
  long slabs split into segments with recessed grooves; no shallow rotated slabs (Chattering Bone rule).
- kit adscheck: OK. Offline ADS view sim (/tmp/m10/adsview.py, camera 13 px behind the base sight) shows the centre clear.
- ADS fix: rear tube compressed (rip behind the receiver at 0.18x; tube ends z ~18.8 instead of 27) so the big side
  slab no longer covers the left/bottom of the ADS view; tube length is now shorter than the rip (deliberate).
- No separate cradle/lever parts: base `_cradle`/`_lever` leaves stay empty under the master's new split rule.


## W325 Identity pass — 2026-11-05

### IDENTITY LIST
- 크림색 전방관
- 주황색 후방관과 육각 패널선
- 은색 측면 케이지와 지그재그 브레이스
- 주황색 상부 핀
- 갈색 총몸 하부와 앞손잡이
- HAKKE 표식

총몸/전방관을 실제 홈으로 분할하고 레일 이빨 6개 추가. 후방 총몸은 z=12.3 뒤 28%, 장전 탄체는 50%로 압축. mag_ 이름/분리 유지, 탄체 길이 변경과 장전 접촉은 master QA 필요.

모든 보이는 면은 `special()` 직접 도색으로 지정했다. 면 크기에 맞춘 1텍셀 밝은 윗모서리/어두운 아랫선, 패널 홈, 작은 고정나사와 재질 대비를 사용한다. 기존 photographic projection은 새 표면 페인트의 fallback으로 사용하지 않는다.

요소 111 → 121, T20, 아틀라스 [1024, 512]. 런처 5종은 512에서 T20 overflow가 확인되어 1024×512로 배치했으며 가까운 면의 1텍셀 글리프/슬릿 보존을 위한 선택이다. 검 2종은 512×512.

검증: kit build/JSON·UV 생성, west/east/top/q/front 렌더 및 rip 비교, kit adscheck OK. adscheck는 높이 프로파일 검사라 실제 시야 점유율을 보증하지 않는다. master의 새 client ADS/1P/3P/장전/10–20개 표시는 아직 미검증. 기존 cbox/tube8의 교차 내부 면까지 전수 coplanar 무결성을 보증하지 않는다; 새 이빨/리브는 기존 면에 끝이 맞닿도록 설계했다.

참조: SKILL.md + ace-izanagi-study.md, main의 Ace(87)/Izanagi(79) JSON 및 /tmp/w325-ref-ace-izanagi.png, 각 proj_cache 원본 측면/사선, W30/Dead Man Walking 원칙. 검의 노란 화면은 master 확인상 3인칭 플레이어로서 스킨 버그가 아니므로 parts 키는 변경하지 않았다.

마지막 silhouette 조정: 기존 PwMap 후방 계수는 0.18→0.50으로 복원하고 위 후처리를 적용하여 색상 정체성인 올리브/주황 후방관이 남도록 했다. 최종 후방관 끝 z=14.9337; 장전 탄체 끝 z=14.9.


## Material pass — 2026-11-05 (Identity pass의 평면 도색 설명을 대체)

| 이름 | 종류 | RGB |
|---|---|---|
| ivory | paint | (215, 214, 201) |
| cream | paint | (204, 200, 173) |
| steel | steel | (151, 158, 156) |
| polymer | polymer | (34, 37, 35) |
| brown | polymer | (58, 43, 34) |
| brown_rubber | rubber | (41, 31, 25) |
| orange | paint | (197, 85, 47) |
| gunmetal | metal | (65, 69, 69) |
| dark | dark | (15, 19, 19) |
| amber | glow | (218, 145, 33) |

`special()` 잔존 범위: HAKKE 픽셀 글자, 탄체 띠, 보어 암부. 나머지 면은 재질 베이크가 처리한다.

T20, atlas [1024, 512], PNG 227,826 bytes. 모든 요소/면의 재질이 명시되어 auto fallback은 없다. 5×5 면 표본에서 special 비율 0.727% (면적 가중 수치가 아님).

후방관 ADS 압축을 역변환한 뒤 원본 relief를 샘플링한다. 위치를 바꾼 조준기, 장전 탄체, 추가 리브, 회전 부품, 얇은 검 측면 이외 면은 detail=0. Cup의 변형된 하부/프레임과 Weaver의 압축 총몸/케이지는 늘어지는 투영을 끄고 재질 결만 남겼다.

검증: 직전 geometry SHA-256 동일, 파트/UV/출력 해시, material 전체 매핑·희소 special 검사 통과. kit build, adscheck OK, 5방향 렌더와 rip 비교 확인. 새 Gradle/Minecraft 실행·실화면 QA·전체 배포 ZIP 측정은 하지 않았다. geometry를 바꾸지 않아 이전 coplanar 검증 한계도 유지된다.


## Material R2 — 2026-11-05 (R1 재질 재배정을 대체)

리시버 상부 → warmsteel, 하부·가드 → brownsteel, 포구·칼라 → lightsteel. 크림 전방관/주황 후방관은 도장 유지.

HAKKE 각인, 주황 후방관 1텍셀 육각 패널선.

대표 재질 명도 차이 28.12. 원소/좌표/회전/부품명 SHA-256 동일, 아틀라스 크기 유지, adscheck OK. 실제 인게임 검증은 master 단계에 남음.
