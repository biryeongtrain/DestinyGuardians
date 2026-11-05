# Rest for the Wicked (W325, rare sword, Adaptive) — base abide_the_return

- Identity kept: dark cleaver blade with the open slot between the riveted grey centre panel and the black spine bar
  (bridged near the guard like the rip), clipped point with the white bevelled slant edge, black guard block, grey
  ribbed grip with screw, pommel.
- Elements: body 16, no magazine (sword). Atlas 512x256 (T=16).
- Uniform 21.6 px/m proper rotation; grip centre on the base grip (Y 6.07, Z 7.7); point side -> -Z like the base
  cutting margin. Pommel Y 3.3 (base 2.5), tip Y 31.3 (base 31.5). Blade Z 6.8..9.4: the wide blade reaches 0.8 px
  further toward +Z than the base back rail (base is a slim curved sword).
- Thickness 0.48 px (rip 0.022 m), real see-through slot.
- Not verified: first-person swing/guard pose readability of the wide blade, hand wrap on the grip.

## W325 detail + pixel-style pass (2026-11-05)
- Elements now: 49 body + 0 magazine = 49. Atlas 512, kit STYLE=pixel, FLAT_TOL 34, PALETTE 16;
  identity repainted as flat colour blocks in special() (no projection grime), chamfered (45 deg strips) edges via cbox/rc,
  long slabs split into segments with recessed grooves; no shallow rotated slabs (Chattering Bone rule).
- kit adscheck: OK. Offline ADS view sim (/tmp/m10/adsview.py, camera 13 px behind the base sight) shows the centre clear.
- ADS fix: point lowered (rip z 1.19 -> 1.15) and tip built as 5 axis-aligned steps under one 45-ish slant strip.


## W325 Identity pass — 2026-11-05

### IDENTITY LIST
- 검은 넓은 도끼형 날
- 회색 중앙 리벳 패널
- 밝은 사선 칼끝
- 날 뒤쪽의 길게 열린 슬롯
- 중간의 짧은 연결 다리
- 검은 가드와 회색 리브 손잡이

기존 실제 관통 슬롯과 연결 다리 보존. 중앙 패널 경계/양열 리벳, 날 경계, 손잡이 패턴을 직접 페인트. 원본에 없는 장식을 추가해 요소 수를 채우지 않음.

모든 보이는 면은 `special()` 직접 도색으로 지정했다. 면 크기에 맞춘 1텍셀 밝은 윗모서리/어두운 아랫선, 패널 홈, 작은 고정나사와 재질 대비를 사용한다. 기존 photographic projection은 새 표면 페인트의 fallback으로 사용하지 않는다.

요소 49 → 49, T20, 아틀라스 [512, 512]. 런처 5종은 512에서 T20 overflow가 확인되어 1024×512로 배치했으며 가까운 면의 1텍셀 글리프/슬릿 보존을 위한 선택이다. 검 2종은 512×512.

검증: kit build/JSON·UV 생성, west/east/top/q/front 렌더 및 rip 비교, kit adscheck OK. adscheck는 높이 프로파일 검사라 실제 시야 점유율을 보증하지 않는다. master의 새 client ADS/1P/3P/장전/10–20개 표시는 아직 미검증. 기존 cbox/tube8의 교차 내부 면까지 전수 coplanar 무결성을 보증하지 않는다; 새 이빨/리브는 기존 면에 끝이 맞닿도록 설계했다.

참조: SKILL.md + ace-izanagi-study.md, main의 Ace(87)/Izanagi(79) JSON 및 /tmp/w325-ref-ace-izanagi.png, 각 proj_cache 원본 측면/사선, W30/Dead Man Walking 원칙. 검의 노란 화면은 master 확인상 3인칭 플레이어로서 스킨 버그가 아니므로 parts 키는 변경하지 않았다.


## Material pass — 2026-11-05 (Identity pass의 평면 도색 설명을 대체)

| 이름 | 종류 | RGB |
|---|---|---|
| panelsteel | steel | (117, 125, 121) |
| wrap | rubber | (114, 122, 115) |
| steel | steel | (151, 158, 156) |
| blacksteel | metal | (37, 43, 45) |
| edge | steel | (209, 217, 212) |

`special()` 잔존 범위: 중앙 패널의 양열 리벳. 나머지 면은 재질 베이크가 처리한다.

T20, atlas [512, 512], PNG 73,889 bytes. 모든 요소/면의 재질이 명시되어 auto fallback은 없다. 5×5 면 표본에서 special 비율 0.0% (면적 가중 수치가 아님).

후방관 ADS 압축을 역변환한 뒤 원본 relief를 샘플링한다. 위치를 바꾼 조준기, 장전 탄체, 추가 리브, 회전 부품, 얇은 검 측면 이외 면은 detail=0. Cup의 변형된 하부/프레임과 Weaver의 압축 총몸/케이지는 늘어지는 투영을 끄고 재질 결만 남겼다.

검증: 직전 geometry SHA-256 동일, 파트/UV/출력 해시, material 전체 매핑·희소 special 검사 통과. kit build, adscheck OK, 5방향 렌더와 rip 비교 확인. 새 Gradle/Minecraft 실행·실화면 QA·전체 배포 ZIP 측정은 하지 않았다. geometry를 바꾸지 않아 이전 coplanar 검증 한계도 유지된다.


## Material R2 — 2026-11-05 (R1 재질 재배정을 대체)

가드 칼라 → darksteel. 검은 금속 몸체·밝은 steel 날·중앙 steel 패널 유지, 손잡이 rubber를 더 어둡게 조정.

중앙 패널의 양열 리벳 점선.

대표 재질 명도 차이 37.63. 원소/좌표/회전/부품명 SHA-256 동일, 아틀라스 크기 유지, adscheck OK. 실제 인게임 검증은 master 단계에 남음.
