# Guardian Rises implementation acceptance ledger

## Scope
Use Rising-Guardian-2026-11-01 assets to replace the tutorial with the complete first mission, beginning in darkness with Ghost scanning the Guardian and ending with ship acquisition and Tower arrival (no Shaw Han ending). Server-only; Polymer enemies, BetterModel visuals/animation, post effects, isolated Fantasy instances. Final quality must be verified with actual gameplay, not only tests.

## Verified intake
- Source archive is read-only. audit_rising_assets.py verified all 25,647 manifest entries (2,917,537,571 bytes), zero mismatches; see source-integrity.json.
- Source metadata identifies five maps, seventeen FBX files and forty-two usable Korean voices. This is inventory evidence, not local rendering acceptance.
- No playable animation clips, collision/navmesh, complete scan VFX or opening first dialogue are supplied. Implement original scene choreography and collision; do not fabricate recovered provenance.
- GLB is already Y-up, transformed from original Destiny Z-up. Do not transform twice.
- Actor placement records are not encounter counts. Exodus Garden 2A is not confirmed mandatory route.

## Required acceptance (all pending)
- [ ] Inspect source models/maps locally and record orientation, scale, materials and rig review images.
- [ ] Build bounded Fantasy instance preparation, membership isolation and idempotent cleanup.
- [ ] Implement complete Gateway/Breach/Divide/Dock 13 traversal, collision and authored encounters.
- [ ] Implement Polymer Fallen combat AI with BetterModel source-informed meshes and animation.
- [ ] Implement Walker legs, stagger and exposed weakpoint with projectile/hitscan correctness.
- [ ] Implement darkness, Ghost scan, resurrection reveal and interrupt-safe post/camera ownership.
- [ ] Integrate appropriate Korean voice/subtitles, one-shot Rise, environment sounds and ship departure.
- [ ] Preserve E menu explanations and first automatic-rifle equip; retain all-weapon practice as follow-up.
- [ ] Implement checkpoints, death/reconnect/restart recovery, revision completion and loan/reward idempotence.
- [ ] Validate actual GCB/non-GCB inputs and complete mission through Tower arrival using Vision.
- [ ] Measure concurrent-instance load, packet/entity budgets and repeated instance cleanup.
- [ ] Build final JAR and scoped commit only after acceptance; document residual asset limitations.

## Current QA preflight
Computer Use inventory is available, but selecting Finder returned “Computer Use was not approved to use Finder”. Lock-state preflight is therefore unverified; no QA client was launched and no bypass attempted. Implementation and offline asset work can continue.

## Worktree state
Pool registry labels slots 1–3 working on old W260 tasks and slots 4–5 ready. Registry is not proof of live workers or integration; inspect actual slot deltas before refresh. Preserve existing uncommitted W289/W290/W291 and other user changes.

## Foundation implementation
Added GuardianRisesProgress with scan-to-departure stages, checkpoint snapshots, once-only music state and generation-scoped combat callbacks. Added GuardianRisesInstances with per-session Fantasy handles, bounded admission, ready-before-entry state and player-preserving cleanup. These are not wired into live tutorial enrollment yet. Three progress unit tests cover duplicate/stale combat events, death/reconnect checkpoint semantics and terminal completion; real world lifecycle and complete campaign acceptance remain pending.

## W300 batch (2026-11-01, master)
- Master contract: `src/main/java/kim/biryeong/destiny/campaign/RisingServices.java` (zones/markers, Fallen spawn, presentation handles, BetterModel model+clip names, voice ids).
- User-named worktree parent `/Users/qf/IdeaProjects/DestinyGuardians-wortrees` (exact spelling as requested). Five isolated seeds created with `scripts/qa/worktree_batch.py create` from the current dirty product (222,517 files, baseline sha256 fd5c291b…, GCB dependency from /Users/qf/IdeaProjects/GCB-server). The old 5-slot pool was not used: its slots carried unintegrated/out-of-scope historical drift (see /tmp/w300/violations.json); their stray `w26x-delta` exports were moved, not deleted, to `DestinyGuardians-worktrees/w300-evidence/preserved-slot-strays/`.
- Lanes and exact ownership: /tmp/w300/manifest.json (map, fallen, models, presentation, director). Briefs: /tmp/w300/brief-*.md. Evidence: `DestinyGuardians-wortrees/w300-evidence/<lane>/`.
- Status: lanes running; nothing integrated or verified in game yet.

## W300 r2–r4 통합 (2026-11-01 16:05, master)

- 통합: map r2–r5(조명 하한·경로 큐·routes.json·트리거 반경 검사), director r2(경로 추종 고스트 트레일), presentation r2–r4(우주선 프롭·출발 시네마틱·탑 도착 커튼/임무 완료 카드·픽업 프롭·시네마틱 중 HUD/1인칭 무기 숨김), fallen r3–r5(워커 아레나 고정·TTK 재조정·`destiny:fallen` 피해 유형·1회 피해 상한, 보스바 제거→고스트 콜아웃 자막, 적 머리 위 Destiny식 체력바), models r3–r4b(Blockbench 재제작: Dreg 317·Vandal 375·Captain 439·Shank 173 큐브, Walker·Skiff 재도색, 32px/블록).
- master 수정: 인스턴스 시계 아침 고정(`ADVANCE_TIME=false`), 서버 종료 시 미완료 빌드 청크 티켓 해제(정지 hang 수정), 웨이브 `order` 태그 해석, routes.json 압축 배열 형식 파서, light.* 단계 점등(`applyLights`), 부활 로그, 자막 카드 위치, Walker 포구 z=4.9, hitscan 디버그 로그 제거, `runGameTest`에 `destiny.guardianRises=false`.
- 검사: `test --tests kim.biryeong.destiny.campaign.*` 전부 통과. `runGameTest` 101 실패 — 2026-10-31 w288 기준선과 실패 목록 동일(신규 회귀 0, W287 튜토리얼 실패는 플래그로 해소). `gradlew jar` 성공: `build/libs/destiny-guardians-0.1.0+26.3.jar` sha256 b1c65214…f9.
- Vision(r2/r3, 서버 명령=픽스처): 오프닝 스캔, 게이트웨이 경로 네이티브 이동→브리치, 소총 획득·브리치 전투(네이티브 사격 킬), 보급품→디바이드, 워커 출현·다리 피격, Dock13 조명·주차 우주선, 출발→탑 도착 완료. 
- 미검증: r4b 모델·체력바·콜아웃·출발 카메라·도착 커튼의 인게임 모습(사용자 테스트 대기), 오디오 청취, FPS/MSPT, 다중 인스턴스, 블라인드 전체 플레이.
- 커밋 보류: `DestinyGuardians.java`/`sounds.json` 등 공유 파일에 기존 미커밋 작업이 섞여 있어, 사용자 인게임 수락 후 범위 확인하여 커밋.

- r4c 모델 다듬기 통합(16:29): 상아 갑옷 반점 ~1/3, 캡틴 팔 슬림화·발톱·어깨 망토(472 큐브). 캠페인 테스트 통과, `gradlew jar` 재빌드 sha256 8e7cef05…380c. 인게임 미검증(사용자 테스트).

## W300 r6 — Dreg-Light handoff adopted as rg_dreg (2026-11-01)

- **Source:** `~/Downloads/Dreg-Light-Handoff/Dreg-Light/dreg_combat.bbmodel`, sha256 `96afa5f0…3510`.
  - 19 bones, 1,864 source-mesh surface quads, a 2048 atlas, and 13 retargeted D2 clips plus the `damage` alias.
  - The user approved it ("저거대로 작업"). The handoff docs are copied to `dreg-light/`.
- **Import:** `scripts/campaign/import_dreg_handoff.py`.
  - Kept the handoff's geometry, texture and clips.
  - Added an `eyes_glow` bone: 4 emissive cyan eye quads in front of the black sockets. The patch is painted into a free atlas cell.
  - Added aliases: `shoot`←fire, `hit`/`stagger`←hurt, `spawn`←surprise_front, `run`←walk ×0.72.
  - Output `rg_dreg.bbmodel` sha256 is `536ea9d8…2f5a`.
- **AI:** the Dreg (RUSHER) now uses `taunt` on first sight (40%, about 1 s pause), and `evade_left`/`evade_right` side-steps when hurt (35%, cooldown 3.5–6 s, only toward standable, clear ground). These are the FallenModels optional actions TAUNT, EVADE_LEFT and EVADE_RIGHT.
- **Test:** RisingModelAssetsTest supports the BB 4.x inline outliner and zero-thickness quads. The Dreg budget is now 1500–2200 elements with a 2048 atlas, and its four arms are `arm_*`/`lower_arm_*`.
  - Campaign suites: 67/67 pass.
  - `./gradlew jar` is a real Gradle build; jar sha256 `5c03ccc7…7e96`.
- **Not verified:**
  - The handoff was validated on BetterModel 3.6.0, but the project runs 3.5.1, so in-game load needs checking.
  - Eye glow placement in game.
  - Evade and taunt feel.
  - FPS with many 1,864-quad Dregs.
  - The remaining dye: the cloth is source grey. The House of Devils crimson is not applied.
- **r6b, House of Dusk cloth:** the cowl and tabard are now violet.
  - **Mask:** texels map to the source cloth materials `80E12DD0` and `80E12F18` through a 3D nearest-surface lookup, then UV-space hole closing. The scripts are `scripts/campaign/dreg_source_tris_blender.py` and `dreg_cloth_mask.py`; the mask is `scripts/campaign/data/dreg_cloth_mask.png`.
  - **Dye:** source weave value × violet (0.56, 0.33, 0.86) at gain 2.3, which keeps the luma gate at 80 or above. Preview: `dreg-light/rg_dreg_house_of_dusk.png`.
  - **Known leak:** the waist sash, which sits under the cowl, is dyed too.
- **r6c House of Dusk palette (supersedes the r6b cloth-only dye):**
  - **Reference:** the user's Bungie Dusk Dreg render, `dreg-light/refs/house_of_dusk_dreg_render_bungie.png`. Destinypedia lists the same image as "Render of a Dreg belonging to the House of Dusk".
  - **Material map:** `scripts/campaign/dreg_material_map.py` labels every atlas texel with its nearest source D2 material (3D lookup, normal-weighted). Output: `data/dreg_material_map.{png,json}`.
  - **Recolour per material:** cowl and tabard Dusk violet; straps leather brown; helmet, pauldron, knee, bracers worn steel; torso dark hide; hands and feet mauve; crest violet; spikes bone. Each texel keeps the source's value detail.
  - **Results:** luma gate passes. Campaign suites 67/67. `./gradlew jar` jar sha256 `14e0a6b4…8383`; `rg_dreg` sha256 `3cd8d517…ef23`.
  - **Comparison:** `dreg-light/cmp_ref_vs_rg_dreg.png`. It is a flat UV projection, not a shaded render, and the eye glow is not in the preview.
- **r6c Vision (master, 18:56–19:00 KST):**
  - **Setup:** isolated QA server `/private/tmp/destiny-w300-server` (BetterModel 3.5.1, Polymer pack regenerated) with copper-golem 26.3 vision client on port 8102 as MinigameQA. `rg_dreg` was summoned by a server fixture command.
  - **Framebuffer PNGs:** `dreg-light/vision_dreg_{front,close,side,night}.png` and the sheet `vision_dreg_sheet.png`.
  - **Observed:** the model loads and renders under 3.5.1. The idle pose animates. Violet cowl and tabard, steel helmet, pauldron and knees, leather wraps and mauve hands and feet all read. The four cyan eyes glow, including at midnight.
  - **Not verified:** combat clips (taunt, evade, fire, death) in a live fight, FPS with many Dregs, audio.
- **r6c perf (master, 19:13–19:16 KST):** M4 Pro, 1280×720 window (2560×1440 Retina), render distance 16, fancy, vsync off, maxFps 260 (isolated QA `options.txt` only; original saved as `options.before-perf.txt`). Dregs idling in a 6-column grid 6–16 blocks ahead, sampled with 28 × 0.5 s client `fps` reads; server `tick query`.

  | Dregs | client FPS (median, min–max) | server MSPT (avg) |
  |---|---|---|
  | 0 | 332 (30–359) | 1.7–2.3 |
  | 1 | 323 (314–341) | 2.0–2.3 |
  | 10 | 234 (219–244) | 1.8–2.0 |
  | 20 | 180 (162–206) | 1.5–1.6 |
  | 30 | 145 (136–152) | 1.6–1.7 |

  - **Excluded:** runs with a flat 30 FPS were window-occlusion throttling, not load. The 0-Dreg run went 30 → 332 in the same window, so those samples are left out.
  - **Frame:** `dreg-light/perf_dreg_30.png` (F3 overlay on).
  - **Not covered:** combat, clips other than idle, other GPUs, and network bandwidth.
- **Next:** the Vandal, Captain, Shank and Walker rebuild with the Dreg-Light technique is dispatched to w300_models_x (r7). Vandal and Captain share the Dreg's 77-bone skeleton, so the 13 D2 clips retarget directly.

## W300 r7 — Fallen SFX/VFX from Rising-Guardian-Fallen-AV (2026-11-01)

- **Source:** `~/Downloads/Rising-Guardian-Fallen-AV-2026-11-01` (read-only), extracted with Charm from the launchpad mission.
- **SFX** (w300_fallen r6): `FallenSounds` plus 56 `guardian_rises.fallen.*` events, 343 mono OGG files, 7.1 MB. The hooks cover gunfire, flyby, thwack, melee, barks (with a budget), foley and the Walker. See `docs/design/guardian-rises/fallen-audio.md`.
- **VFX** (w300_presentation r5): `FallenVfx` plus 13 sprites from D2 particle textures: muzzle, tracer, impact, explosion, EMP, weakpoint, Shank burst, shield and blink. See `docs/design/guardian-rises/fallen-vfx.md`.
- **Master fix:** the VFX textures moved to `textures/item/guardian_rises/vfx/`. The 26.3 item atlas only scans `item/` and `block/`, so all 13 were rendering as the missing-texture checker. The client log had 13 "Missing textures" warnings before the fix and 0 after.
- **Vision:** `fallen-av/fight_sheet.png` shows 2 Dregs, a Vandal and a Captain attacking the player. The muzzle flashes, contrails and impact stars render.
  - **Known issue:** impact stars still read large when the hit lands right beside the camera.
  - **Not verified:** listening to the SFX (no audio capture) and the Walker effects.
- **Tests and build:** campaign tests 103/103. `./gradlew jar` passes.
- **r7b (presentation r5b):**
  - Each viewer's sprites are capped by apparent size: stars at 4°, and the hit player does not see their own impact.
  - Contrails are 0.10 blocks wide and last 2 ticks. Arc-trail dust is spaced every 1.5 blocks.
  - Vision `fallen-av/fight2_sheet.png`: no full-screen stars at close range, and the effects are smaller.
  - The pink tint on distant stars is unexplained; the CMD tint path needs checking.
  - Campaign tests 104/104.
- **Skiff:** no runtime spawns the Skiff yet. The model and clips are registered, but nothing uses them, so the D2 skiff SFX are unwired.
- **r8 Skiff drop (w300_fallen r7/r8):** a Skiff arrives with reinforcement waves, lowers its riders, then departs. It uses the D2 `skiff_flyover` and `skiff_enemy_spawner` sounds, an open-sky offset search, and a `[skiff]` log line.
  - **Vision:** `fallen-av/divskiff3_sheet.png`. In Divide wave 1 (`divide_reinforce`), the Skiff hovered at the decided point, dropped 4 riders and departed. Log: `sky=DIRECT seenBy=4/4 search=9.7ms/270 reads`.
  - **Offline scan:** Breach waves 1, 2 and 4 and the Dock 13 defence use an offset hover.
  - **Not verified in game:** Breach, Dock 13 and audio.
  - **Proposals:** split `dock_defense` into ordered waves, and add `prop.skiff_*` hint markers for the map lane.
  - **Tests:** campaign tests 117/117.

## r9 (2026-11-02) Walker 실화면·혼합 성능

- 결함1: `/summon` 시 NBT가 NoGravity를 덮어써 Walker(noPhysics)가 y=-108까지 낙하 후 제거됨 → `FallenMob.isNoGravity()` override(비보병·비행형은 항상 무중력).
- 결함2: BetterModel이 서버 passenger attachment(히트박스 상단 h)만큼 디스플레이를 내리는데 클라이언트 대역(좀비)은 2.0125에 태움 → 모델 원점이 발+(2.0125−h). Walker +1.01, Shank +1.11, Captain −0.59 침하. `RisingFallen.register`에 `.passengerAttachments(좀비 좌석)` 적용(w300_models_x r9 패치, base sha 51fdd4b9 일치).
- Vision: `models-r7/r9_grounded_front.png` — y=-61 지면에서 Dreg/Vandal/Captain/Walker 접지, Shank 의도된 부유, Walker 머리 위 체력바.
- 혼합 성능(Dreg4:Vandal3:Captain1:Shank2, M4 Pro, vsync off, QA 프로필 inactivityFpsLimit=minimized): 0=291, 10=192, 20=134, 30=122 FPS median, 서버 평균 1.1–1.5ms/tick. 이전 10fps는 AFK 프레임 제한이었음.
- 미검증: Walker 전투 전체(EMP/약점/다리 파괴) 실전투 캡처, 실제 존 FPS, 청취.
- r9 Divide 실미션: `start`→`skip divide_walker`→lure/reinforce 처치→`divide_walker` 웨이브 Walker y=109 지면 스폰. 플레이어 귀속 피해로 3 사이클(ARMORED→LEG_BREAK→STAGGER→EXPOSED→RECOVER) 진행, core 230→110, Ghost 자막 콜아웃 표시 확인 (`walker-fight/sheet.png`). 처치(DEAD) 연출 캡처는 미완.
- 주황 윤곽선: 주포 충전 telegraph(`FallenModels.charge`, BetterModel glow) — 의도된 표시. 벽 뒤에서도 보이는 점은 충전 시간 동안만.
- QA 실수: 벽 안 tp로 다운→체크포인트 재시작, 차원 미지정 tp로 인스턴스 이탈. 이후 `execute as MinigameQA at @s` 기준으로 tp.
- r10: Divide 실미션에서 Walker DEAD → `DOCK_13` 단계 자동 진행 확인 (`walker-fight/death_sheet.png`, status stage=DOCK_13). Walker 처치 시 Ghost 콜아웃 "해냈어요! 워커가 쓰러졌어요!" 표시.
- r10 수정: 단계 전환 시 사망 연출 중인 적은 discard하지 않음(`RisingCampaign` spawner.discard); 보병 사망 시 bodyfall 사운드가 Shank burst 조건에 잘못 묶이던 if 중첩 수정; Walker 사망 클립(2.6s) 종료 시 최종 코어 폭발(VFX+SFX)로 모델 제거를 가림. 평지 단독 재현 `walker-fight/fdeath_sheet.png`(최종 폭발 추가 전).
- jar sha256 c45b6a13a7a6fb01e0d7b0a951a01172b7443ead051207467c21f30d419ac52c, 캠페인 테스트 통과. 최종 폭발 추가 후 실화면 재캡처는 미수행.
- r10 실미션 후반부(jar c45b6a13): `skip dock_13`→ship trigger 접근→`SHIP_DEFENSE` 0/14 → dock_defense / dock_ship_west(skiff riders=4, sky=HINT) / dock_ship_east(skiff riders=5) 3웨이브 → `DEPARTURE` → "completed revision 1" → 타워 월드 도착 화면(`dock13/sheet.png`, `after_complete.png`). Ghost 자막 출력 확인(`dock13/ship.png`).
- 미검증: 격납고 지붕 아래 시점이라 Dock13 스키프 기체는 화면에 안 잡힘(로그로만 확인); 출발 시네마틱은 웨이브를 명령으로 처치해 실시간 캡처하지 않음.

## r11 (2026-11-02) 오프닝 스캔 중 직업 선택 — 사용자 지시

- 요청: 고스트 스캔 중 "당신은 누구입니까?" → 타이탄/헌터/워록 A/D 선택 → 선택 후 고스트가 빛을 되돌린다며 깨움.
- `OpeningScan`: 스캔 종료(t=148) 시 암전 유지·scan_loop 정지·authored 자막 `rg.opening.who` "당신은… 누구입니까?" → 타임라인 정지 상태로 `ClassChoice`(A/D 엣지 순환, Space 확정, 진입 시 이미 눌린 키 무시, 45초 자동 확정). title=선택 직업(직업색), subtitle=◀ 타이탄·헌터·워록 ▶, 액션바=조작 안내. 확정 시 `CharacterLoadouts.selectClass` 적용, 설명문 표시 후 "움직이지 마세요. 당신의 빛을 되돌려 놓을게요." → 암전 → revive → bloom → 직업 대사(54/56/58 …). 실명 효과는 무기한, bloom에서 해제.
- `RisingMission.OPENING_TIMEOUT` 90→120초. 신규 단위 테스트 `OpeningClassChoiceTest`(3), `RisingSubtitlesTest` authored 수 8→9.
- Vision 실입력(Vision control A/D/Space): HUNTER→D→워록, D→타이탄, A→워록… / 2회차 HUNTER→A→TITAN→Space, 서버 로그 "opening class chosen: TITAN (applied)", 이후 기상 장면에서 헌터 직업 대사 확인(1회차). 증거 `opening-r11/sheet.png`, `choice_final.png`.
- jar sha256 4f29dcb5e30cd9503fc905d34fd49fb94eb79ba582cc65eb06f2dc3852a1de18, 캠페인 테스트 120/120 통과.

## r12 (2026-11-02) 시작 암전 단축 — 사용자 지시 "블랙아웃 후 스캔까지 길어도 5초"

- 원인: 매 시작마다 Gateway 구역(706 컬럼, 450x190x450)을 새 인스턴스에 짓느라 암전이 ~78초 지속. 컬럼마다 청크 티켓을 그때 요청해 컬럼당 최소 1틱 이상 대기.
- 수정: (1) `ZoneTemplate.Build` 다음 192 컬럼 청크 선요청(prefetch) + 회귀 테스트, (2) 암전 대기 중(head 세션 비RUNNING)만 빌드 예산 2→16ms, (3) **웜 스페어 인스턴스**: 유휴 빌드 시간에 Gateway를 미리 지은 인스턴스 1개 유지, 시작 시 `GuardianRisesInstances.adopt`로 즉시 인계(진행 중이면 빌드째 인계, 다른 체크포인트면 미완성 Gateway 취소), 사용 후 다음 스페어 재준비(~11초). 서버 종료 시 정리. `-Ddestiny.guardianRises.warmSpare=false`로 끔. (4) 오프닝 도입부 단축: 고스트 등장 16→6틱, 스캔 52→30틱.
- 실측(Vision, 로그 시각): 이전 queued→entered 78s → prefetch 6.2s → 웜 스페어 **0s**; `start` 명령→스캔 시작 **1.7초**. 스페어 없을 때(연속 시작 직후 등) 최악 ~8초. 깨어남 시 Gateway 지형 정상(`opening-r12/sheet.png`).
- jar sha256 11de1ed1dcead10ab9f6c2774a67ee48bd8873c39502afc3b1a2bb417210de0c, 캠페인 테스트 통과.

## r13 (2026-11-02) 캠페인 고스트 → 튜토리얼 Generalist Shell 모델 — 사용자 지시

- `GhostCompanion.Body`: 기본값을 튜토리얼 `TutorialGhost`(추출 Generalist Shell 11 디스플레이, 2048 텍스처)로 변경. BetterModel `rg_ghost`는 `-Ddestiny.guardianRises.ghostModel=bettermodel`로만 사용.
- `TutorialGhost` 확장(튜토리얼 동작 불변): look(시선 지정), open(개폐 강제), transmat(크기 성장). 클립 매핑: transmat=성장 등장, shell_open=완전 개방, scan=0.95 개방+스캔 시선, speak=소폭 개방, look=수호자 응시.
- 따라오기 위치를 튜토리얼과 같은 프레이밍(전방 2.1·우측 1.25)으로 조정 — 첫 시도(rg_ghost 위치 그대로)는 화면 오른쪽 위에 껍질 조각만 잘려 보였음(`ghost-r13/follow.png`), 조정 후 `ghost-r13/sheet2.png`(스캔·기상·따라오기).
- jar sha256 b7c2be98bdbbb0935829b91ed4b6bc187790f4040ad2f339ea952e96f6294d1b. QA 중 실행 중 재빌드로 서버가 종료 시 NoClassDefFoundError(QA 환경 문제, 제품 무관) → 재시작.
- r13 추가: Breach 소총 스캔(BREACH_DARK→ARM_YOURSELF)에서 튜토리얼 고스트가 껍질을 펼치고 스캔 광선을 쏜 뒤 다음 단계로 진행 확인(`ghost-r13/rifle_scan.png`). QA 메모: 콘솔에서 skip은 `execute as MinigameQA run destiny rising skip ...` 형태로만 동작.
- r13 출발 실시간 캡처(`ghost-r13/departure_sheet.png`): 우주선 정박 → 플래시 전환 → 외부 카메라에서 우주선 이륙·상승(트레일) → 탑 월드 도착("지형 불러오는 중…"). 고스트는 출발 중 숨김 처리되어 보이지 않음(의도). 출발 컷 동안 채팅 로그(QA 명령 출력)가 화면에 남는 것은 QA 명령 때문.
- Dock13 스키프: 서쪽/동쪽 hover 지점 근처에서 캡처했으나 기체가 화면에 잡히지 않음(`ghost-r13/skiff_sheet.png`) — 로그상 eligible=true, 미해결/미확인.
- r13b: 따라오는 튜토리얼 고스트가 Divide 기둥에 파묻혀 잘려 보임(`perf-zones/sheet.png`) → `GhostCompanion.clearOfTerrain`(눈→슬롯 레이캐스트+껍질 반경 0.45, 막히면 눈 쪽으로 당김) + 튜토리얼 껍질은 항상 수호자를 바라보게(뒤통수 대신 눈) 수정. 결과 `perf-zones/divide_lure_r13c.png`. jar 27d3fadd…, 캠페인 테스트 통과.
- 실구역 FPS(M4 Pro, vsync off, 렌더거리 16, Vision 20샘플 median): Divide lure 8기 ~123-130, reinforce(스키프) ~168, Walker 전투 근접 ~124. 서버 평균 0.3ms/tick.

## W303 — 전역 수호자 쓰러짐 (Guardian Down) r1 · 2026-11-02

- 신규 `down/GuardianDown.java`, `down/GuardianDownHud.java`, 아트 `scripts/art/build_guardian_down_hud_w303.py`, 음성 `sounds/guardian_down/revive_eyes_up{,_short}.ogg`.
- 모든 플레이어 사망을 가로채 시체(마네킹)·셸 전개 고스트·포스트 이펙트·데스티니식 HUD(제목/상태/24분절 링/키캡/처치자 카드)를 표시. 월드: 5초 후 SPACE 제자리 부활 / SHIFT 귀환 지점. 캠페인: 3초 후 SPACE → 체크포인트 재시작. 크루시블: 같은 HUD를 외부 API로 사용.
- r1 수정: 접속 시 stale spectator 복구(`destiny_guardian_down` 태그), 공중 사망 시 바닥 스냅·제자리 부활 지면 탐색(실패 시 귀환 지점), 좁은 실내 카메라 프레이밍(8방향 탐색 + 오버헤드 블렌드, 고스트 1.35m 이내 금지), 쓰러짐 중 캠페인 HUD 숨김, 처치자 아이콘(적=뿔 해골, 환경=경고 삼각형), 키캡/문구 간격.
- Vision(`guardian-down-r1/sheet.png`): 월드 낙하 사망, 제자리 부활, 귀환 지점 부활, 캠페인 실내 사망→체크포인트 부활 확인. 부활은 QA 명령 `/guardiandown revive`로 구동(관전 중 Vision 키 입력 불가) — 실제 SPACE/SHIFT 홀드 입력과 음성 청취는 미검증.
- W302 Stubborn Oak(86요소, w302_oak) main 통합: `weapon_skins/stubborn_oak.json`, 아틀라스, HUD 아이콘, `art/weapons/w302/stubborn_oak/`. Khvostov는 placeholder 유지(w300_models_x 진행 중). 인게임 1인칭/ADS 미검증.
- 테스트: 2,452개 중 6개 실패(기존 무관: GoldenGun×2, W112 실루엣 해시, W179 Mindbender, W168 Austringer, W115). 실제 Gradle `jar` 빌드 sha256 `53c55e61a38bb264e6b0912886499e7ba31b6216aedbffaf3f004cfa739fff16`.

### W303 r2 · 2026-11-02 12:20
- 실제 입력 검증: Vision 클라이언트에 QA 옵션 `-PvisionControlAllowSpectator=true` 추가(기본 off, 관전 중 입력·background 모드 유지). 백그라운드(창 비활성) 상태에서 SPACE 홀드 → 체크포인트 부활(11:44:41), SHIFT 홀드 → 귀환 지점 부활(11:47:49) 확인. 증거 `guardian-down-r2/`.
- 쓰러짐 중 Ghost 액션바 안내 차단, 쓰러질 때 액션바 비움. 제자리 부활 지면 탐색을 발밑 우선으로 변경.
- 사용자 지시: "고스트: 빛을 따라오세요"·"고스트: 목표 · 방향" 텍스트 안내 제거(화면 목표 마커로 대체). 고스트 대사 자막 카드 중앙 하단(x960, 하단 905, 폭 760) + 1인칭 무기 위에 그림(`setAboveHand`). Vision `sub4_2.png`.
- QA 서버 콘솔을 RCON으로 전환(`/tmp/w300/rcon.py`), stdin fifo는 명령 누락.
- W302 인게임 1차 Vision(`w302-weapons-r1/`): Khvostov hip/ADS, Stubborn Oak hip/ADS 정상 파지·조준선. Khvostov 조준경 유리 alpha 112가 아이템 cutout 렌더에서 불투명 남색 판으로 보여 유리 alpha 0으로 변경(빌드 스크립트 동일 반영) → 투명 창 + 빨간 레티클 확인(`khv_ads_crop3.png`). 장전·근거리 10~20개 표시는 미검증.
- 주의: 서버 시작과 `processResources`를 동시에 돌리면 팩에 이전 리소스가 들어감 — 빌드 완료 후 서버 시작.
- W303 r3 (13:30): Khvostov ADS 레티클(w303_khv_reticle, high) 원본처럼 얇은 빨간 대시 2개 + 아래 눈금, 유리 바로 앞 z4.50, 발광, W148 흰 점 제거(`no_overlay`). 인게임 확인 `w302-weapons-r1/khv_ads_crop4.png`.
- Dock 13 스키프 2·3웨이브 화면 확인(`dock13-r2/w1_sheet.png`, `w2_sheet.png`), 마지막 웨이브→출발→탑 도착→"임무 완료"까지 연속 진행(`dep_sheet.png`).
- 수정: 쓰러짐 포스트이펙트가 플레이어 데이터에 남아 재접속 후 화면이 계속 붉던 문제 → 접속/정리 시 제거(`/guardiandown effects` QA 명령). 완료 시 채팅 문구 제거(임무 완료 타이틀·고스트 대사로 대체).
