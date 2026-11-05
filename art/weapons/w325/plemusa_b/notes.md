# Plemusa-B (W325, rare grenade launcher, Adaptive; no exact frame row) — base salvager_s_salvo

- Identity kept: worn white/black front shroud with the open front O-window, D-loop checkered front grip with the
  dark foot block, dark front plate + yellow octagonal drum, black side sight plate (green dots), white receiver hump,
  green HAKKE upper/stock, raked checkered pistol grip, skeleton stock struts, tall dark butt pad.
- Elements: body 16 + magazine(moving front group) 15 = 31 (cap 1000). Atlas 512x512 (T=14).
- Uniform 26 px/m proper rotation anchored on the base W201 grip hand (z 8.24, y 8.18); front grip lands z ~-1.8,
  y ~8.6 (base -2.14 / 8.9); muzzle z -6.8 (base -7.83), butt z 15.2 (base 17.17).
- Added a front ring sight on a 2.4 px tower so the base iron sight centre (8, 14.30, -2.1) is framed (Plemusa's own
  top is y 11.9..12.65); ring textured from the rip's front O-frame.
- LEAF SPLIT (needs master): parts.magazine here is the moving FRONT group (prefix brl_) intended for the base
  `_barrel` leaf; parts.body for `_body`; `_round` should keep base shell art. Current WeaponSkinAssets has no
  `_magazine/_moving` file for salvager_s_salvo, so every leaf would get the whole gun.
- Not verified: in-game reload (barrel leaf motion with a drum design), ADS through the ring, hand contact.

## W325 detail + pixel-style pass (2026-11-05)
- Elements now: 95 body + 42 magazine = 137. Atlas 512, kit STYLE=pixel, FLAT_TOL 34, PALETTE 16;
  identity repainted as flat colour blocks in special() (no projection grime), chamfered (45 deg strips) edges via cbox/rc,
  long slabs split into segments with recessed grooves; no shallow rotated slabs (Chattering Bone rule).
- kit adscheck: OK. Offline ADS view sim (/tmp/m10/adsview.py, camera 13 px behind the base sight) shows the centre clear.
- parts.magazine (brl_*, 42 elements) is the moving front group for the base `_barrel` leaf (master rule: barrel falls
  back to magazine). Drum is a real octagon in 3 banded segments.


## W325 Identity pass — 2026-11-05

### IDENTITY LIST
- 크림색 전방 덮개와 열린 O 프레임
- 담황색 드럼/하부 레일
- 청록색 HAKKE 총몸
- 검은 측면 상태창과 녹색 표시
- 빈 공간이 있는 삼각형 개머리판
- 앞손잡이 D 루프

기존 깊이/구멍/분리 brl_ 구조 유지. 드럼 홈, HAKKE, 상태창과 파지 텍스처를 직접 페인트.

모든 보이는 면은 `special()` 직접 도색으로 지정했다. 면 크기에 맞춘 1텍셀 밝은 윗모서리/어두운 아랫선, 패널 홈, 작은 고정나사와 재질 대비를 사용한다. 기존 photographic projection은 새 표면 페인트의 fallback으로 사용하지 않는다.

요소 137 → 137, T20, 아틀라스 [1024, 512]. 런처 5종은 512에서 T20 overflow가 확인되어 1024×512로 배치했으며 가까운 면의 1텍셀 글리프/슬릿 보존을 위한 선택이다. 검 2종은 512×512.

검증: kit build/JSON·UV 생성, west/east/top/q/front 렌더 및 rip 비교, kit adscheck OK. adscheck는 높이 프로파일 검사라 실제 시야 점유율을 보증하지 않는다. master의 새 client ADS/1P/3P/장전/10–20개 표시는 아직 미검증. 기존 cbox/tube8의 교차 내부 면까지 전수 coplanar 무결성을 보증하지 않는다; 새 이빨/리브는 기존 면에 끝이 맞닿도록 설계했다.

참조: SKILL.md + ace-izanagi-study.md, main의 Ace(87)/Izanagi(79) JSON 및 /tmp/w325-ref-ace-izanagi.png, 각 proj_cache 원본 측면/사선, W30/Dead Man Walking 원칙. 검의 노란 화면은 master 확인상 3인칭 플레이어로서 스킨 버그가 아니므로 parts 키는 변경하지 않았다.


## Material pass — 2026-11-05 (Identity pass의 평면 도색 설명을 대체)

| 이름 | 종류 | RGB |
|---|---|---|
| ivory | paint | (218, 211, 192) |
| gunmetal | metal | (65, 69, 69) |
| polymer | polymer | (34, 44, 40) |
| yellow | paint | (188, 180, 100) |
| green_glass | lens | (44, 91, 48) |
| steel | steel | (151, 158, 156) |
| teal | paint | (48, 88, 77) |
| rubber | rubber | (25, 28, 27) |

`special()` 잔존 범위: HAKKE 픽셀 글자와 녹색 상태 표시. 나머지 면은 재질 베이크가 처리한다.

T20, atlas [1024, 512], PNG 355,908 bytes. 모든 요소/면의 재질이 명시되어 auto fallback은 없다. 5×5 면 표본에서 special 비율 0.019% (면적 가중 수치가 아님).

후방관 ADS 압축을 역변환한 뒤 원본 relief를 샘플링한다. 위치를 바꾼 조준기, 장전 탄체, 추가 리브, 회전 부품, 얇은 검 측면 이외 면은 detail=0. Cup의 변형된 하부/프레임과 Weaver의 압축 총몸/케이지는 늘어지는 투영을 끄고 재질 결만 남겼다.

검증: 직전 geometry SHA-256 동일, 파트/UV/출력 해시, material 전체 매핑·희소 special 검사 통과. kit build, adscheck OK, 5방향 렌더와 rip 비교 확인. 새 Gradle/Minecraft 실행·실화면 QA·전체 배포 ZIP 측정은 하지 않았다. geometry를 바꾸지 않아 이전 coplanar 검증 한계도 유지된다.


## Material R2 — 2026-11-05 (R1 재질 재배정을 대체)

드럼 프레임·측판·개머리판·하부 레일 → gunmetal, 포구창·리시버 전면·그립 프레임 → lightsteel. 청록 외피/황색 드럼 도장 유지.

드럼 양 끝의 1텍셀 리벳 점열, HAKKE와 녹색 상태등.

대표 재질 명도 차이 37.05. 원소/좌표/회전/부품명 SHA-256 동일, 아틀라스 크기 유지, adscheck OK. 실제 인게임 검증은 master 단계에 남음.
