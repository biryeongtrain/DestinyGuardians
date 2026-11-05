# Future Imperfect (W325, rare sword, Adaptive) — base abide_the_return

- Identity kept: straight white/worn single-edge blade, wider ricasso block with the dark vents and stamp, clipped
  point, white ferrule, wrapped grip with the diamond binding pattern, collar and white pommel cap.
- Elements: body 12, no magazine (sword). Atlas 512x512 (T=16).
- Uniform 21.6 px/m proper rotation; grip centre on the base grip (Y 6.07, Z 7.7); edge -> -Z like the base cutting
  margin. Pommel Y 2.0 (base 2.5), tip Y 31.0 (base 31.5). Straight blade Z 7.2..8.6 (base curved 6.0..8.6).
- Blade thickness 0.28 px (rip 0.013 m) so it stays visible edge-on.
- Not verified: first-person swing/guard readability, hand wrap on the grip.

## W325 detail + pixel-style pass (2026-11-05)
- Elements now: 36 body + 0 magazine = 36. Atlas 512, kit STYLE=pixel, FLAT_TOL 34, PALETTE 16;
  identity repainted as flat colour blocks in special() (no projection grime), chamfered (45 deg strips) edges via cbox/rc,
  long slabs split into segments with recessed grooves; no shallow rotated slabs (Chattering Bone rule).
- kit adscheck: OK. Offline ADS view sim (/tmp/m10/adsview.py, camera 13 px behind the base sight) shows the centre clear.
- ADS fix: clipped tip shortened (point rip z 1.20 -> 1.165) so the tip no longer rises above the base tip profile.


## W325 Identity pass — 2026-11-05

### IDENTITY LIST
- 길고 좁은 은백색 직선 날
- 짙은 회색 날 경계
- 사선으로 끝나는 검끝
- 밝은 리카소의 검정 통풍 슬릿
- 흑회색 감긴 손잡이
- 밝은 폼멜

리카소 양면의 얇은 실제 레일 2개 추가. 날은 원본의 긴 연속면을 유지하며 1텍셀 경계, 리카소 슬롯/단차, 그립 패턴 직접 페인트.

모든 보이는 면은 `special()` 직접 도색으로 지정했다. 면 크기에 맞춘 1텍셀 밝은 윗모서리/어두운 아랫선, 패널 홈, 작은 고정나사와 재질 대비를 사용한다. 기존 photographic projection은 새 표면 페인트의 fallback으로 사용하지 않는다.

요소 36 → 37, T20, 아틀라스 [512, 512]. 런처 5종은 512에서 T20 overflow가 확인되어 1024×512로 배치했으며 가까운 면의 1텍셀 글리프/슬릿 보존을 위한 선택이다. 검 2종은 512×512.

검증: kit build/JSON·UV 생성, west/east/top/q/front 렌더 및 rip 비교, kit adscheck OK. adscheck는 높이 프로파일 검사라 실제 시야 점유율을 보증하지 않는다. master의 새 client ADS/1P/3P/장전/10–20개 표시는 아직 미검증. 기존 cbox/tube8의 교차 내부 면까지 전수 coplanar 무결성을 보증하지 않는다; 새 이빨/리브는 기존 면에 끝이 맞닿도록 설계했다.

참조: SKILL.md + ace-izanagi-study.md, main의 Ace(87)/Izanagi(79) JSON 및 /tmp/w325-ref-ace-izanagi.png, 각 proj_cache 원본 측면/사선, W30/Dead Man Walking 원칙. 검의 노란 화면은 master 확인상 3인칭 플레이어로서 스킨 버그가 아니므로 parts 키는 변경하지 않았다.

검증 중 기존 tip_step0의 높이 0인 평면 요소를 제거했다.


## Material pass — 2026-11-05 (Identity pass의 평면 도색 설명을 대체)

| 이름 | 종류 | RGB |
|---|---|---|
| ivory | paint | (211, 211, 198) |
| edge | steel | (144, 152, 147) |
| wrap | cloth | (70, 73, 70) |
| wrap_ridge | cloth | (111, 115, 107) |
| blade | steel | (205, 209, 201) |
| steel | steel | (151, 158, 156) |

`special()` 잔존 범위: 리카소의 작은 검정 슬롯. 나머지 면은 재질 베이크가 처리한다.

T20, atlas [512, 512], PNG 73,658 bytes. 모든 요소/면의 재질이 명시되어 auto fallback은 없다. 5×5 면 표본에서 special 비율 0.0% (면적 가중 수치가 아님).

후방관 ADS 압축을 역변환한 뒤 원본 relief를 샘플링한다. 위치를 바꾼 조준기, 장전 탄체, 추가 리브, 회전 부품, 얇은 검 측면 이외 면은 detail=0. Cup의 변형된 하부/프레임과 Weaver의 압축 총몸/케이지는 늘어지는 투영을 끄고 재질 결만 남겼다.

검증: 직전 geometry SHA-256 동일, 파트/UV/출력 해시, material 전체 매핑·희소 special 검사 통과. kit build, adscheck OK, 5방향 렌더와 rip 비교 확인. 새 Gradle/Minecraft 실행·실화면 QA·전체 배포 ZIP 측정은 하지 않았다. geometry를 바꾸지 않아 이전 coplanar 검증 한계도 유지된다.


## Material R2 — 2026-11-05 (R1 재질 재배정을 대체)

폼멜·페룰 → lightsteel, 리카소 → warmsteel. 칼날 steel, 손잡이 cloth를 유지해 도장 면을 제거.

검날의 연속 1텍셀 홈선과 리카소 슬롯.

대표 재질 명도 차이 41.13. 원소/좌표/회전/부품명 SHA-256 동일, 아틀라스 크기 유지, adscheck OK. 실제 인게임 검증은 master 단계에 남음.
