# W300 Guardian Rises — BetterModel 모델 (lane w300-models)

작성 2026-11-01 · 상태: 생성·오프라인 검사 완료 / **인게임 미검증** (BetterModel 실제 로드·표시·애니메이션·FPS는 master QA 대상)

## 결과물

| 모델 | 요소(큐브) | 본 | 회전 그룹(≈표시 엔티티) | 텍스처 | 크기 px (X,Y,Z) | 복셀 | 파일 |
|---|---|---|---|---|---|---|---|
| rg_dreg | 377 | 19 | ~18 | 512² | 23 × 39 × 21 | 1.0 px | 715 KiB |
| rg_vandal | 354 | 18 | ~17 | 512² | 23 × 37 × 29 | 1.1 px | 676 KiB |
| rg_captain | 349 | 19 | ~18 | 512² | 27 × 48 × 36 | 1.49 px | 649 KiB |
| rg_shank | 336 | 8 | ~7 | 512² | 31 × 22 × 26 | 1.1 px | 452 KiB |
| rg_walker | 766 | 22 | ~21 | 1024² | 130 × 65 × 124 | 2.95 px | 1497 KiB |
| rg_skiff | 563 | 7 | ~6 | 512² | 79 × 69 × 250 | 3.27 px | 601 KiB |
| rg_ghost | 33 | 13 | ~10 | 64² | 9 × 10 × 9 | 직접 제작 | 190 KiB |
| rg_ship | 58 | 13 | ~12 | 128² | 110 × 31 × 143 | 직접 제작 | 59 KiB |

예산: 보병 150–400, Walker ≤900, 텍스처 ≤512(Walker ≤1024) 모두 충족. 16 px = 1 블록, 모델 정면 = -Z(north, BetterModel steve 기준과 동일). 원본 1 m = 16 px (Fallen/Shank/Ghost 비율 유지; Ghost는 원본 0.12 m 셸을 90 px/m로 확대해 탐색 가독성 확보), Walker 0.55배(약 8 × 4 × 7.8 블록), Skiff 0.35배(길이 약 15.6 블록). 배율은 디렉터가 BetterModel scale로 추가 조정 가능.

설치: `RisingModelAssets.prepare()`가 `config/bettermodel/models/NAME.bbmodel`에 8개를 설치. 마지막 설치본의 SHA-256를 BetterModel 스캔 경로 밖 `config/destiny/guardian_rises/models/NAME.sha256`에 기록한다. 번들이 바뀌면 설치본이 우리 마지막 설치본과 동일할 때만 원자적으로 교체하고, 사용자가 수정한 파일·심볼릭 링크·다른 모델은 건드리지 않는다. **DestinyGuardians.onInitialize에서 다른 *ModelAssets.prepare()와 함께 호출하는 연결은 master 소유 파일이므로 아직 하지 않았다.**

재생성: `/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/campaign/rising_models.py -- [--only rg_dreg,...] [--evidence DIR] [--no-render]`. 결과는 결정적이다(같은 입력에서 8개 파일 SHA-256 동일 확인).

## 원본 매핑 (읽기 전용 /Users/qf/Downloads/Rising-Guardian-2026-11-01/models)

| 모델 | 원본 FBX | 사용한 엔티티/자식 | 비고 |
|---|---|---|---|
| rg_dreg | fallen_dreg__80E1AFCF | 본체 80E1AFCF, 무기 80A6DB7C(오른쪽 위 손), 칼 80A6DD0B(왼쪽 아래 손) | 배낭·방패 자식(80A6D859 등)은 원본에서 원점에 겹쳐 있어 제외 |
| rg_vandal | fallen_vandal__80E1AF6E | 본체, 저격형 소총 80A6DEFD | 망토 유지 |
| rg_captain | fallen_captain__80E15797 | 본체, 소총 80A6D809, 칼 80A6D802 | 뿔·모피 망토 유지 |
| rg_shank | Shank__80E29872 | 본체 | 80E1AF0C는 같은 모델(80E12FDC)·같은 재질 — 동일 결과라 하나로 공유 |
| rg_walker | Walker__80C60641 | 본체 80C60641, 포 80C3EA34, 포탑 80C3631C | 측면 장갑 80C3E9F7/80C3EA0E는 원점 정렬이 불확실해 제외 |
| rg_skiff | Skiff__80C3EE92 | 선체 80C3EE92, 클램프 80C3EEB3 | 해치 80C3EECA/80C3EEE0 제외 |
| rg_ghost | Ghost__80CFD3CB | 비율·색만 사용 | 8개 셸 본, 코어, 눈 메시 구조를 그대로 본으로 반영 |
| rg_ship | 없음 — **원작 추출물 아님** | — | 아래 참조 |

**rg_ship 판정:** mission_object 8종을 렌더해 확인한 결과 녹색 연료 캔(80CBE1C4), 보급 상자(80CBE2BD), 소총(80CFD2E5), 파이프/전선, 격자 문짝·벽판, 문틀, 깨진 벽판이며 우주선은 없다. 활동 데이터의 `sq_ship` 라벨은 `fallen_skiff`를 가리키고, Dock 13 배치에는 Fallen·Shank만 있다. 따라서 rg_ship은 **이번 작업에서 새로 디자인한 점프십**(흰 선체, 주황 줄무늬, 쌍발 엔진, 후퇴익, 랜딩기어, 발광 엔진/항법등)이다. 원작 모델이라고 표기하지 않는다. 증거: `w300-evidence/models/inspect/missions_all.png`.

## 제작 방식과 디자인 판단

- **Fallen/Shank/Walker/Skiff:** FBX 바인드 포즈를 평가해 원본 뼈 계층 → 소수 리그 본으로 매핑(가장 가까운 지정 조상). 각 삼각형을 원본 DDS 색으로 면적 샘플링 → 본별 복셀화(표면 근처만 점유 + 닫힘 + 외부 채움) → 탐욕 병합 큐브 → 예산을 넘으면 복셀을 자동 확대. 팔·다리처럼 기울어진 사지는 사지 축 프레임에서 복셀화하고 큐브에 같은 회전을 줘서 계단 현상을 줄였다(본당 회전 1종 → BetterModel이 본당 표시 1개로 처리).
- **텍스처:** 면마다 복셀당 2–4 텍셀을 굽는다(가까운 표본 6개 가중 평균, 볼록 모서리 어둡게). 원본은 염색(dye) 셰이더 데이터가 없어 회색 디테일 맵만 있으므로 Fallen 망토·가죽·장갑에 **임의 지정 팔레트**(House of Devils풍 적갈색 망토, 어두운 강철)를 곱했다. 색이 있는 고유 albedo(머리, 무기, Walker 파란 관절)는 그대로 샘플링.
- **4팔 유지:** Dreg/Vandal/Captain 모두 uarm/farm_{ul,ll,ur,lr} 네 팔이 독립 본.
- **Ghost:** 셸 꽃잎을 복셀화하면 사각뿔이 계단처럼 깨져서, 원본 비율(셸 8조각·코어·눈)과 albedo 색으로 회전 판재 33개를 직접 구성했다. 눈(eye 본)·코어 홍채는 light_emission 15.
- **추가 발광 부품(직접 제작):** Fallen 눈 4개, Shank 눈, Walker 약점(weakpoint)·덮개판(plate_l/r)·머리 눈, Skiff 엔진, 점프십 엔진·항법등. 원본 VFX가 아니다.
- **Walker 본:** leg_fl/fr/ml/mr/bl/br(+_low), claw_l/r, head, turret, weakpoint, plate_l/r. 계약의 leg_fl/leg_fr/leg_bl/leg_br/weakpoint 포함.

## 애니메이션 — 전부 직접 제작 (추출물에 클립 없음)

모든 클립 이름은 `RisingServices.Models`와 일치. 루프: idle/walk/run/fly(+Ghost scan/speak). 나머지는 once, 끝 포즈를 유지해야 하는 death·leg_break·weakpoint_open·shell_open·transmat·power_up·takeoff는 `hold`.

- 보병: 스타일별 수치(Dreg 짧은 주기·고개 떨림, Vandal 22° 숙인 자세·양손 소총, Captain 느리고 무거운 보폭). 사지는 목표 방향으로 조준(aim)해 포즈를 계산하고 Blockbench 회전 규약으로 변환했다. shoot 반동, melee 칼 휘두르기(몸통 비틀기), hit/stagger, 앞으로 쓰러지는 death, 착지 후 포효하는 spawn.
- Shank: 부유·날개 떨림, fly 전경사, shoot 반동·눈 확대, 회전 추락 death.
- Walker: 삼각 보행(3다리씩 교대) 무거운 상하 흔들림, fire 반동, leg_break(앞왼다리 꺾임 후 유지), weakpoint_open(덮개 개방·차체 하강·약점 확대 유지) → recover, death.
- Skiff: arrive(먼 상공에서 진입·감속), drop(클램프 개방), depart. Ghost: idle·scan(셸 회전+개방)·speak(눈 펄스)·shell_open/close·transmat(회전 수축)·look. 점프십: idle(엔진 미등), power_up(엔진 점화·진동·기어 압축), takeoff(상승·기어 수납·전방 가속).

## 검사 (오프라인)

- `./gradlew test --tests kim.biryeong.destiny.campaign.model.RisingModelAssetsTest -Pgcb_server_dir=<worktree>/libs/gcb-server` → 5/5 통과: 8개 모델 존재·예산, 텍스처 PNG 크기, 필수 클립·루프 모드, outliner/animator 무결성, UV 범위, Walker/Ghost/Fallen 계약 본, 설치(INSTALLED/CURRENT/UPDATED/KEPT_USER_COPY/SKIPPED_LINK, 무관 파일 보존).
- BetterModel `ModelData.loadBlueprint` 엄격 로드는 플랫폼 부트스트랩(BoneItemMapper)이 필요해 단위 테스트에서 실행 불가 — **인게임 확인 필요**.
- 검토 이미지(원본 vs 큐브, 전/3-4/측/후): `w300-evidence/models/review_rg_*.png`, 클립 5프레임 시트 `rg_*_clips.png`(행 순서는 `rg_*_clips.txt`), 전체 `overview_cubes.png`, 아틀라스 `rg_*_atlas.png`. 미리보기는 Blockbench 규약(회전 x/y 부호 반전, 위치 x 반전)으로 계산한 근사이며 BetterModel 실제 렌더가 아니다.

## 알려진 한계 / master 확인 항목

1. 인게임에서 8개 모델이 BetterModel 경고 없이 로드되는지, 사지 회전 큐브(비정수 각도)가 표시 분할 후 올바른 위치에 붙는지.
2. 회전 방향 규약(애니메이션 x/y 반전)이 Blockbench와 같다는 가정 — 걷기 다리 방향, Vandal 조준이 정면(-Z)을 향하는지, Walker 다리가 바깥으로 들리는지.
3. 표시 엔티티 수: 보병 1기당 약 18개, Walker 약 21개 — 10–20기 동시 FPS.
4. Skiff arrive/depart, 점프십 takeoff는 위치 이동이 수십 블록이다. 엔티티 원점이 시야 밖이면 컬링될 수 있으니 디렉터가 기반 엔티티를 함께 움직이는 방식도 고려.
5. 복셀 기반 큐브라 근거리에서 원본보다 거칠다(특히 Walker/Skiff). Fallen 망토·장갑 색은 염색 데이터 부재로 임의 팔레트.
6. 무기 장착 각도(rot)와 원점에 겹친 자식 배제는 직접 판단. 원본 자식 배치 의미는 미확정.

## r2 (2026-11-01) — master 1차 Vision 반영: 명도·발광 본

1차 Vision(`w300-evidence/vision-r1/models/gal.png`, `fallen/s_dreg.png`): 8개 모두 경고 없이 로드·재생, 그러나 정오 하늘빛에서 Fallen/Walker/Skiff/Ship이 거의 검은 실루엣.

- **명도 패스:** 아틀라스 평균 명도(0–255) r1 → r2: Dreg 65→124, Vandal 66→128, Captain 65→136, Shank 74→130, Walker 97→109, Skiff 96→110, Ghost 90→101, Ship 107→114. Fallen 팔레트(임의 지정): 망토 적갈 ~94, 가죽 ~114, 강철 장갑 ~165, 트림 하이라이트 ~195, 크레스트 ~99. 색 albedo(머리·무기·Walker 관절)는 텍스처별 8–92 백분위 명도를 목표 범위(Fallen 92–163, Walker 87–173, Skiff 97–179, Shank 92–168)로 재매핑하고 색상은 유지. 볼록 모서리 텍셀은 밝게(×1.24, 판재 테두리 하이라이트), 오목 주름은 어둡게(×0.80), 텍셀 최저 명도 ~61.
- **발광 본(`_glow` 접미사, light_emission 15 유지):** 발광 요소는 모두 `_glow` 본에만 있고 `_glow` 본에는 발광 요소만 있다(테스트로 고정). 기존 애니메이션 본(Walker `weakpoint`, Ghost `eye`)은 유지하고 발광 큐브만 자식 `_glow` 본으로 옮겼다.
  - rg_dreg: `eyes_glow`(head), `weapon_glow`(weapon), `blade_glow`(blade)
  - rg_vandal: `eyes_glow`, `weapon_glow`
  - rg_captain: `eyes_glow`, `weapon_glow`, `blade_glow`, `pack_glow`(torso 등 아크 코일)
  - rg_shank: `eye_glow` (body)
  - rg_walker: `eye_glow`(head), `weakpoint_glow`(weakpoint 하우징의 자식)
  - rg_skiff: `engines_glow` (hull)
  - rg_ghost: `eye_glow` (eye의 자식)
  - rg_ship: `engine_l_glow`, `engine_r_glow`, `lights_glow`
  아크/충격 부품(무기 셀·총구, 칼날, Captain 등 코일)은 직접 제작한 장식이며 원본 VFX가 아니다.
- **가독성:** Fallen 눈이 r1에서 머리 복셀 안에 묻혀 있었다 → 복셀 얼굴 표면에 배치하고 1.3배 확대, 청백색. 네 팔·망토·장갑의 명도 대비로 실루엣 분리.
- **주의:** r1 Ship 아틀라스는 이미 평균 107이었는데도 인게임에서 순흑이었다. 따라서 텍스처만이 원인이 아니며, 표시 엔티티가 받는 광원(엔티티 위치의 블록/하늘빛, 바닥에 묻힌 위치)이나 런타임 brightness 설정도 원인일 가능성이 높다. `_glow` 본 전체 밝기와 별개로 몸체 본의 최소 밝기(brightness override)도 인게임에서 확인할 것.

## r3 (2026-11-01) — Walker 재설계 (master Vision: 22 m 거리에서 갈색/회색 덩어리)

- **복셀 변환 폐기 → 직접 제작한 4다리 Walker 153요소, 텍스처 256².** 원본 Walker__80C60641의 돔형 선체·전방 머리 포·마디 다리를 참고하되, `WalkerBoss`에 다리 히트 영역이 4개뿐이므로 원본 6다리를 4다리로 줄였다(원작 형태와 다름, 의도적 각색). 6-다리 r2 복셀 모델은 `w300-evidence/models/r3/before_rg_walker.bbmodel`에 보존.
- **히트박스 정렬:** main `campaign/fallen/WalkerBoss.LAYOUT`(앵커 기준 블록, x 오른쪽·y 위·z 앞, 모델 px = 16x, 16y, −16z)에 맞췄다. 발판 중심 = LEG_* (±2.3, 0, ±2.0), 정강이는 0–4블록 높이에서 다리 상자 안을 지난다. 선체 = 폭 4.5블록, 높이 3.7–6.3블록(HULL 3.7–5.8 포함), 중심 z −0.2. weakpoint_glow 중심 = WEAKPOINT (0, 3.3, 1.6). 테스트 `walkerGeometryMatchesWalkerBossHitRegions`가 이 숫자를 고정한다(레이아웃이 바뀌면 함께 갱신).
- **포 끝 불일치(보고):** `WalkerBoss.muzzle()`은 (0, 4.3, 2.4)블록에서 발사하지만 모델 포구 끝은 (0, 4.31, 4.99)블록이다. 투사체가 머리 속에서 나오므로 muzzle z를 ~4.9로 옮기는 것을 제안(master 소유 파일).
- **팔레트(직접 지정):** 강철 판(명도 ~190/145/90 세 단계), 적갈 장갑(~84), 황토 트림(~165), 관절 검정(~54). `plate` 텍스처: 위·왼쪽 테두리 하이라이트, 아래·오른쪽 그림자, 큰 면의 패널 이음매, 모서리 리벳, 하단 오염, 결정적 노이즈.
- **발광 1.5배:** `eye_glow` 6×3.9(r2 4×2.6) + 중심 하이라이트; `weakpoint_glow` 코어 10.5³(r2 7³), 테두리 13.5×6×6(r2 9×4×4), 캡 4.5×4.5×1.5. ARMORED 상태에서도 좁은 셔터(`plate_l/r`) 사이로 주황 테두리가 보이도록 했다.
- **본:** root, body, head, eye_glow, weakpoint, weakpoint_glow, plate_l, plate_r, leg_{fl,fr,bl,br}, leg_{..}_low. r2의 leg_ml/mr, claw_*, turret은 제거(main 코드 참조 없음 확인).
- **애니메이션(직접 제작):** walk는 대각 쌍(fl+br / fr+bl) 무거운 착지(차체 하강). leg_break: 앞왼다리 충격 반동 → 무릎 꺾임 → 선체가 그 모서리로 쓰러지며 오버슈트 후 유지. 쓰러진 자세는 수치 풀이로 나머지 세 발이 지면(y≈0)에 남도록 계산(`WALKER_DOWNED`). stagger: 쓰러진 자세에서 좌우로 격하게 흔들리고 성한 다리가 허우적, 머리 요동, 눈 깜빡임. weakpoint_open: 셔터 개방·코어 1.45배 유지. recover: 일어서며 셔터 닫힘. death: 네 다리가 모두 벌어지며 선체 추락, 눈·코어 소멸.
- **증거:** `w300-evidence/models/r3/compare_20m.png`(이전/이후, 20블록, 눈높이 1.7, 정면·3/4), `review_after.png`, `after_front_zoom.png`, `rg_walker_clips.png`(행: idle, walk, fire, leg_break, stagger, weakpoint_open, recover, death), `rg_walker_atlas.png`. Blender 워크벤치 렌더라 발광·Minecraft 음영은 반영되지 않는다.
- **미검증:** 인게임 표시·밝기(몸체 본 최소 밝기는 런타임 FallenModels 소관), 회전 규약 실제 방향, leg_break가 실제로 앞왼다리(LEG_FL)에서 보이는지 — 런타임이 어떤 다리가 부서졌는지와 무관하게 이 클립은 항상 fl을 꺾는다. 다리별 파손 연출이 필요하면 `leg_break_fr/bl/br` 클립을 추가할 수 있다(계약 변경 필요).

## r4b (2026-11-01) — Blockbench 재제작: House of Devils 화풍, Sketchfab 품질 기준

사용자 요구: "Dreg 큐브가 너무 적다 — Sketchfab `minecraft-fallen-captain-destiny-2` (c91aec9f) 이상의 퀄리티", "Blockbench에서 작업". 참조 이미지는 품질 기준으로만 사용했다(다운로드 불가, 복제·추적 없음).

**작업 방식(실제 수행한 것만):** 실행 중인 Blockbench 5.1.4의 MCP 서버(1.10.1, `localhost:3000/bb-mcp`)를 HTTP로 직접 호출했다. 모델마다 새 프로젝트 탭을 열었다(사용자 탭 없음 확인, 작업 탭은 `w300_owned` 표시 후 종료). 저장은 Blockbench 프로젝트 코덱(`Codecs.project.compile`)으로 했다.
- 형상: `add_group`(본 피벗)과 `place_cube`(from/to/origin/rotation, 면별 UV)로 배치. 큐브 좌표는 증거 폴더의 저작 스크립트(`r4/bb/dreg.py`, `fallen.py`, `shank.py`)가 생성했다. 한 장면씩 수작업으로 클릭한 것은 아니다.
- 텍스처: 저작 규칙으로 만든 픽셀 레이어를 `create_texture`로 불러온다. 규칙은 재질별 8~10단 램프, 1px Bayer+노이즈 디더, 판 가장자리 1px 어둡게+칩, 회갈색 먼지 디더(아래로 갈수록 진함), 리벳, 패널 이음, 천 주름, 단 방향 40% 어둡게, 안쪽 면 어둡게, 알파 컷아웃 프린지로 이루어진다. 그 위에 `paint_with_brush` 스트로크 패스를 더했다(긁힘+밝은 아래 입술, 녹·피 흘림, 가죽 바늘땀, 망토 주름선, 메탈 글린트, 망토 등판의 Devils 문장).
  - 브러시로 픽셀을 하나씩 찍는 방식은 쓰지 않았다. Blockbench 5.1.4에서 `connect_strokes=false`가 좌표마다 undo를 하나씩 만들어 약 95 px/s밖에 나오지 않기 때문이다.
  - 마지막에 컷아웃 알파를 0/255로 정리했다.
- 애니메이션: `create_animation`으로 키를 넣고, 루프 클립은 catmullrom, `death`는 hold로 설정했다.
  - Blockbench free 포맷에서 측정한 결과 편집기 회전·위치 값은 물리 값과 같다(bedrock식 x/y 부호 반전 없음).
  - Walker·Skiff는 형상과 클립을 유지하고 텍스처만 재도색했다(`repaint.py`: 기존 bbmodel 로드 → 면별 UV 재패킹 → 픽셀 레이어 → 브러시 패스).

**밀도/예산(테스트로 고정):** 모든 재도색 모델은 2 texel/px(블록당 32px)이다. 테스트는 면적 비율 3.6 이상을 요구한다.

| 모델 | 요소 | 본 | 아틀라스 | 테스트 범위 | 비고 |
|---|---|---|---|---|---|
| rg_dreg | 317 | 22 | 256 | 250–450 | 1.9 b, 디지티그레이드 다리, 굽은 상체, 팔 2 + 붕대 감은 절단 하완(왼쪽), 오른쪽 하완 소켓 캡 |
| rg_vandal | 375 | 20 | 256 | 300–500 | ×1.21, 팔 4, 긴 망토, 뾰족 후드, 와이어 라이플(상완 두 손 거치) |
| rg_captain | 439 | 23 | 256 | 400–700 | ×1.37, 뿔 투구, 눈 6, 왼어깨 초승달 크레스트(뼈 14 마디 + 붉은 띠), 쌍검(`weapon`/`blade`), `pack_glow` 에테르 |
| rg_shank | 173 | 8 | 256 | 150–250 | 계단식 구체(층마다 22/45/68° 박스 3개), 붉은 띠, 파란 눈, 추진기 4, 쌍열 쇼크포 |
| rg_walker | 161 | 20 | 1024 | 150–250 | 형상 유지, sand 장갑에 판 격자·리벳·붉은 띠, 다크 관절 |
| rg_skiff | 54 | 7 | 1024 | 40–300 | 형상 유지, 회색 금속 판 격자와 붉은 배너 |

**팔레트 (refs/ 실측, `r4/palette_sheet.png`):**
- Fallen: ivory `#d7c3ab`(P25 `#bba58e`, P75 `#efdfcc`), rust `#622a1f`, red cloak `#904533`, undersuit `#554860`/`#665972`, dark `#382728`
- Captain: ivory `#bdb7ae`, red `#4b2024`
- Dreg 인게임 퍼플: `#67476d`
- Devil Walker: sand `#c5a386`(P25 `#af907c`, P75 `#d9b68e`), red `#a9454b`, joints `#252932`, orange `#eda13d`
- Walker 컨셉: `#a77b4d`
- 실제 램프는 `r4/bb/kit.py`의 `RAMPS`다. ivory·red·leather·suit·metal·rust·bandage·dirt·cyan·shock·orange·sand·stripe.

**참조 출처:** `r4/refs/provenance.txt`에 URL·sha256·작가 표기를 남겼다. Bungie 저작물이며 팔레트와 실루엣 참고에만 썼다.

**master 리뷰 반영 (같은 날 2차):**
- ivory 판에 1px 가장자리 어둡게+칩, 회갈색 먼지 디더, 이음 그림자를 넣었다. 하퇴·무릎 판은 shade 4(약 70%)로 낮췄다.
- 가죽·언더슈트에 밝음→그늘 그라데이션을 넣었다.
- 망토는 단 쪽으로 약 40%, 안쪽 면도 더 어둡게 했다.
- 다리를 길게 했다: 엉덩이 y 14→15.8, 무릎 앞, 발목 뒤로.
- 상체 숙임을 늘렸다: Dreg −33°, Vandal −28°, Captain −24°.
- 팔을 길게 했다: Dreg 상완 6.4, 전완 6.4. 4팔 Fallen 상완 7.2/6.8, 전완 6.3, 하완 5.2/4.8.

**계약 유지:**
- 본 이름, 클립 이름, `_glow` 본은 그대로다.
- Walker는 `leg_{fl,fr,bl,br}_glow`를 계속 가진다.
- Shank에 `spawn`을 추가했다(지지대 펼침 + 눈 부팅, `FallenModels` SPAWN → spawn).
- `_glow` 본 요소에는 저장 후 `light_emission: 15`를 다시 넣는다. Blockbench free 코덱이 이 값을 버리기 때문이다.
- `rotation`이 0이라 생략된 요소에는 `[0,0,0]`을 채운다.
- 빈 animator는 제거한다.

**테스트 변경 (`RisingModelAssetsTest`):**
- 위 예산과 아틀라스 상한(1024)을 반영했다.
- Shank `spawn`이 필수다.
- Walker 다리 발광 본을 반영했다.
- 신규 `repaintedModelsHaveThirtyTwoPixelsPerBlock`, `fallenClothIsAlphaCutout`: 알파 0/255만 허용하고, 사용 면 안에 투명 픽셀이 200개를 넘어야 한다.
- mid-tone 하한을 90→80으로 낮췄다. 웨더링으로 Dreg 평균 휘도가 89이기 때문이다.
- `./gradlew test --tests '...RisingModelAssetsTest'` 결과는 10/10 통과다.

**인게임 미검증 (master 확인 필요):**
1. BetterModel 3.5.1이 투명 픽셀을 컷아웃으로 그리는지 확인해야 한다. jar 문자열에서 cutout/translucent 처리를 찾지 못했다. 아이템 모델 기본 렌더링에 기대고 있다.
2. 다축 큐브 회전(26.3)이 BetterModel에서 그대로 보이는지.
3. 애니메이션 방향이 Blockbench 미리보기와 같은지 확인해야 한다. walk 0.2s에 왼다리가 앞, death는 앞으로 쓰러짐, melee는 위→아래 베기다.
4. Captain 뿔·크레스트는 히트박스(2.6 b)보다 위로 약 3.4 b까지 솟는다.
5. 두께 0.2px 망토 판이 원거리에서 깜빡이는지(z-fighting).
6. Fallen 텍스처 평균 휘도가 낮아져 어두운 실내에서 읽히는지.

`rising_models.py`의 `render_mc`는 알파 컷아웃을 지원하도록 바꿨다. 로더는 rotation/origin 생략을 허용한다. 이 렌더는 휴식 포즈만 쓴다. 기존 bedrock식 부호 가정은 free 포맷 클립에 맞지 않으므로 애니메이션 포즈 렌더에 쓰면 안 된다.

**재생성 주의:** `scripts/campaign/rising_models.py`의 생성기를 다시 돌리면 r4b Blockbench 결과물 6종(dreg·vandal·captain·shank·walker·skiff)이 r4 Python 판으로 덮어써진다. r4b 재생성은 Blockbench를 띄운 상태에서 `w300-evidence/models/r4/bb/`의 `make.py <dreg|vandal|captain|shank> ...`와 `repaint.py rg_walker|rg_skiff ...`로 한다. Ghost와 Ship은 r3 그대로다.

## r4c (2026-11-01) — 아이보리 장갑 정리, Captain 팔/망토

master 리뷰: Captain의 아이보리 장갑 전체에 갈색 점이 깔려 "점박이 소"처럼 보인다.

같은 Blockbench MCP 파이프라인을 썼다. Dreg·Vandal·Captain을 새 탭에서 재빌드하고 코덱으로 저장했다. 형상 변경은 Captain뿐이다.

**아이보리/뼈 재질 텍스처 (`r4/bb/kit.py`, Dreg·Vandal·Captain 공통):**
- 판 표면 디더 진폭을 줄이고 상하 명암 기울기를 약하게 했다. 표면은 기본 톤 주변 2~3단으로 거의 깨끗하다.
- 먼지는 아래 가장자리 띠(높이 20%), 이음선 ±1px, 좌우 테두리에만 둔다. 판 가운데는 0이다.
  - 아래 줄이 아닌 먼지는 진한 dirt 대신 반 단계 어두운 따뜻한 회갈색이다.
- 칩은 3배 적게 했다(면적/26 → 면적/140). 92%는 판 가장자리 픽셀에 붙는다.
- 1px 어두운 하단·측면 림과 가장자리 칩은 유지했다.
- 겹침(림+이음+그림)으로 기본 톤보다 4단 넘게 내려가지 않게 바닥을 두었다. 칩과 리벳은 예외다.
- 리벳은 아이보리 면 10×10px 이상에만 둔다. 가시·뿔 조각에는 리벳과 이음선이 없다.
- 브러시 패스의 아이보리 긁힘은 30%만 남기고, 녹·피 흘림 확률은 0.45 → 0.2로 낮췄다.

**측정 (`r4c/speck_metric.py`):** 아이보리 면에서 고립된 어두운 점의 수다. 8이웃 중앙값보다 22 이상 어둡고, 비슷하게 어두운 이웃이 1개 이하인 픽셀을 센다. 그래서 선이나 림은 세지 않는다. 단위는 100 내부 픽셀당 개수다.

| 모델 | r4b | r4c |
|---|---|---|
| Dreg | 9.42 | 3.17 |
| Vandal | 10.60 | 3.64 |
| Captain | 12.19 | 4.49 |

**Captain 형상 (`fallen.py`, 요소 439 → 472, 예산 400–700 안):**
- 상완 2개와 하완 2개의 전완을 가늘게 했다.
  - 슈트 1.5 → 1.05, 가죽 두 단(1.45/1.15)으로 손목 쪽이 좁아진다.
  - 아이보리 브레이서는 옆판 0.4, 뒤판 0.4의 얇은 판이다.
- 손은 1.1×0.95×0.75로 작아졌다.
- 갈고리 발톱은 3개에 각 4마디, 길이 3.0, 끝이 0.8씩 가늘어진다. 엄지 발톱은 3마디다.
- 망토 쪽에는 어깨 맨틀을 추가했다.
  - 등 윗부분 판(9.4×1.2W).
  - 좌우 어깨 덮개 박스, 바깥으로 늘어진 6.2×6.0 프린지 천.
  - 가슴 앞 덮개 천, 어깨 뒤 늘어진 천.
  - 등판과 견갑부가 천에 덮인다.

**변하지 않은 것:** 본·클립 이름, `_glow` 본, 예산, 아틀라스 256, 0/255 컷아웃 알파, 애니메이션 키.

`RisingModelAssetsTest`는 10/10 통과다.

**미검증:** 인게임 모습은 확인하지 않았다(앞 r4b 항목과 같다). 어깨 맨틀 천은 `cape` 본에 붙어 있으므로, 공격 시 상완 판과 겹치거나 뚫고 나오는지 master Vision에서 봐야 한다.
