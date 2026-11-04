# 악마의 소굴 구현 진행

## 현재 범위

- 사용자 확인(2026-11-03): 구현 계속. 보상 지급은 이번 범위에서 제외.
- 3인 고정 튜닝이며 인원별 스케일링 없음. 실제 3인 난이도/완주 시간 평가는 구현 이후 별도 수락.
- 자동 회귀, 격리 클라이언트 시각/동작 검증과 실제 3인 난이도 수락을 구분한다.

## 격리 작업

세 작업본은 scripts/qa/worktree_batch.py로 현재 dirty/untracked 소스와 독립 dependency를 복제했다. 167730개 파일의 공통 해시 기준선은 6224139b0bc45e69fbbea16f9e25defdda04cf1345ec46ac19f8907ab89af263. 기존 변경과 역사 QA 삭제는 보존했다.

## 현재 검사

- DevilsRosterTest 4개, DevilsWalkerStateTest 3개: 실제 Gradle targeted test 통과.
- 기본판 한국어 대사 12개: SHA256 전달본 일치, 전체 OGG 디코딩, finite/non-silent 검사. 15개 생성 파일 재현성 비교 통과. 원음 byte-identical.
- 게임 runtime에 아직 연결하지 않음. 인게임 화면/오디오/성능 검증은 미실시.
- 원본 GLB 조사 및 1차 voxel 변환은 진행 중이며 최종 화면으로 수락하지 않음.

## 남은 작업

공유 director, 실제 팀 lifecycle, 원본 기반 맵/모델 통합, 군체 및 보스 AI/공격 판정, HUD/대사/BGM, 체크포인트/부활/재접속, 자동 회귀와 빌드, 격리 Vision 검사. 보상 지급은 제외.

Master staging files are in the main checkout (DevilsRoster, DevilsWalkerState, DevilsInstances, DevilsVoiceCatalog, tests, and the audio importer/resources). Worker map/model results are not yet integrated.

- DevilsVoiceCatalogTest: 실제 Gradle test 1개 추가 통과. 12개 음성의 패키지 OGG 해시/이벤트 경로/전체 길이 타이밍과 변형 제외 확인. 전체 targeted 검사 합계8개(두 번의 관련 실행).
- DevilsInstances 컴파일 성공. DevilsSubtitles는 추가 후 compileJava 진행 중; 아직 화면 검증 전.

- DevilsSubtitles 추가 후 실제 Gradle compileJava 성공(4초). UI 화면 검수는 아직 미실시.

## 공유 director와 맵 통합

- Director 소유 delta4개 파일: export manifest의 before(null)/after SHA256 확인 후 통합. 소유 범위 밖 변경 없음. 31팩과10특수 actor, 예약/재시도/세대 및 교체 incarnation, 대사 gate,2회 보호막 구현.
- 맵 담당은 read-only 후보를 반환하여 master가10개 후보 파일을 직접 통합했다. 출력6종 해시,4GLB와77텍스처 해시, 공통 sampler와 generator 해시 일치 확인. 지도 보정 provenance는 bundled manifest에 보존했다. map-integration.json에 추가 파일의 원본/해시 기록.
- 실제 Gradle 통합 테스트32개 전부 통과(/tmp/devils-integration-tests.log). 기존 master8 + director18 + map6.
- DevilsWorldBuild 및 관련2개 테스트 추가, 실제 Gradle targeted test 통과(/tmp/devils-world-build-tests.log). 총34개의 서로 다른 테스트.
- DevilsVoicePlayback은 한 공유 대사 clock과 개인 sound/subtitle projection을 구현. 취소 시 완료 콜백 호출 없음. 실제 클라이언트 오디오는 미검증.
- 지도 source-vs-voxel 비교와 offline voxel camera를 검토했다. 실제 Minecraft 화면으로 인정하지 않는다.
- 아직 init/입장명령/실제 actor factory에 연결하지 않았으며 플레이 가능한 공격전으로 보고하지 않는다.

## 사용자 색상 수정 지시 및 후속 통합
- 현재 회색 모델 초안은 사용자에게 거절됨. 황혼의 가문 배색 및 군체 종별 갑각/피부/발광 색을 머티리얼 역할 기준으로 적용 후 재베이크/비교해야 함. 단순 전체 보라색 tint 금지.
- Recovery 2개 신규 파일의 manifest 해시 확인 후 main 통합. worker 17개 targeted test 통과; main 재검사 대기.
- Spatial 2개 신규 파일의 해시 확인 후 main 통합. worker 4개 테스트 통과. master가 서버 스레드 제한과 스폰당4개 경로 후보 탐색 상한 추가; 실제 월드 검증 대기.
- GuardianDown 소유 Options identity 기반 revive/cancel/body API, 선택적60틱 보호/공격 해제, 외부 부활 스케줄 옵션 추가. 기존6인자/8인자 호환. accepted weapon emission/공격 능력/피해 경로 연결.
- DevilsObjectives 어댑터 추가. 방어88기 실제 처치 진행, 실드별서비터3기 및 브리그/워커 목표.
- compileJava 및 compileGametestJava 성공 후 외부스케줄 옵션 등 추가 변경은 재검사 대기. DevilsRevivalGameTests는 작성/등록됐으나 아직 실행하지 않음.

## Admission correction — 1–3 players

User correction: solo/duo admission allowed; maximum three, fixed three-player encounter tuning. Updated roster, director, recovery, instance validation comments and design. Gradle targeted Roster/Director/Recovery tests passed, including equal 24-actor opening at 1/2/3 participants and zero/four/duplicate rejection. Session coordinator revision is pending integration; no live solo-start claim.

## Live adapter and health runtime verification

- Integrated verified session delta (DevilsLair/DevilsSession) with 1–3 admission and caller-only start command. Wired init, competing activity entry guards, weapon/ability/custom damage guards, and strike block protection. These are compiled by the current runtime test build, not yet accepted as a playable complete strike.
- Added GuardianDown.resumeOwned: no second death/rule callback, exact existing-owner identity, external scheduling only, finite position checks, remaining countdown from recovery state, failed-scene cleanup. Disconnect clears owned revival protection.
- Actual Minecraft26.3/Fabric GameTest max-health passed: finite Float.MAX_VALUE cap, default20/minimum1, armor cap unchanged, actual1600/2200/100000 health, attribute codec roundtrip, damage/heal above1024. Evidence runtime/max-health.xml and .log.
- First revival runtime attempt failed before assertions could validate gameplay: test players lacked native level registration, causing DistanceManager.removePlayer during setCamera. Failure evidence preserved as runtime/revival-failed-fixture.*. Test setup corrected to addNewPlayer with paired removal; rerun in progress.
- Remaining: model material reconstruction/review/installer, cinematic adapter, checkpoint supplies, Walker damage identity/hitboxes, SFX/BGM selection, complete actual client/session verification. Rewards are explicitly omitted by user instruction; actual3-player difficulty evaluation follows implementation.

- Revival rerun passed2/2 actual server GameTests after native player registration: owner isolation, cancellation vs success, externally scheduled reconnect without a second death, one normal completion callback, and attack-cancelled protection. Evidence runtime/revival.xml and .log. This is server/packet lifecycle evidence, not framebuffer or audio acceptance.

## NBT chunk generator — 2026-11-03

사용자 요청에 따라 Nucleoid map-templates 0.3.2+26.2를 include하고 steve-td TemplateChunkGenerator 구조를 26.3 buildTerrain에 맞췄다. DevilsTemplateGenerator가 섹션과 WG heightmap을 생성하고 DevilsChunkWarmup은 청크 티켓으로 준비를 기다린다. `.zone`은 오프라인 변환/회귀 oracle만 담당한다. 4개 압축 NBT와 SHA manifest는 data/destiny/map_template/devils_lair에 있다.

실서버 검사에서 확인해 수정한 문제: 26.3 BlockState codec은 Name/Properties가 아닌 id/properties 사용; Fantasy 빈 월드는 PREPARING에서 tickWhenEmpty=true가 필요하며 ready 후 false 전환. GameTest의 가속 틱이 비동기 준비 전에 소진되므로 fixture 대기만 50ms polling, 120초 상한으로 조절했다.

실제 runGameTest 성공: 네 맵 모든 voxel의 NBT/원본 grid/생성 월드 일치, 총 437455 nonair blocks, 구역별 월드 offset과 샘플 heightmap, 실제 Fantasy 월드 tick 진행 확인. 보고서 runtime/nbt.xml, 로그 runtime/nbt.log. 초기 실패 보고서도 보존했다. 이는 실제 서버 생성 검증이며 framebuffer/플레이 이동/조명 시각 수락은 아니다.

## Presentation / supply lifecycle integration

DevilsPresentation candidate hash 83554aa866858b67958a24292ca10037518cd4704559d5cb337e66609c23445b의 기준 해시를 확인한 뒤 통합했다. DevilsLair 초기화에 factory 등록, 기존 Rising/GuardianDown HUD·무기 suppression predicate와 OR 결합. Sepiks는 guard 전투 중 spawn animation 자동 재생을 금지하고 presentation의 원본 intro 정상 종료로 전투를 시작한다. Tracker sightTrace=false로 시선/occlusion에 따른 연출 중단 위험을 줄였다.

26.3 ServerPlayer.setCamera bytecode에서 body teleport 확인. 카메라 시작 직후 안전 entrance anchor로 body를 되돌리고, 소유 camera 정상 종료 시 같은 level/alive/non-down일 때 anchor 복원. 실제 framebuffer/카메라 패킷 동작은 미검증.

DevilsSupplies의 2개 신규 파일을 worker SHA 대조 후 통합. 세션 생성/zone entry/전멸/재접속/이탈/종료 lifecycle을 연결했다. offline 전멸 대상은 zone별 복구 부채를 보존해 재입장 후 해당 zone baseline만 복원한다. 보급함 위치·개인 상호작용·UI 연결은 아직 남았다. 보급 기능 전체 완료로 간주하지 않는다.

통합 후 실제 Gradle compileJava + 관련 JUnit 32개 통과. runtime/TEST-*.xml과 presentation-supplies-integration.log에 보존. 신규 인게임 검증이나 최종 배포 JAR 생성은 수행하지 않았다.

## 보급함 상호작용 — 2026-11-03

DevilsSupplyStations: 각 구역 IN 주변 반경4–7, 최대64 후보의 바닥 ray/지지/충돌/물/경계/3좌석 간격 검사 후 저작 철제 상자와 특탄 녹색·중탄 보라색 strip display를 생성한다. 바닐라 블록 텍스처 기반 저작 prop이며 추출 원작 상자로 표시하지 않는다. 지형·상자 인벤토리는 변경하지 않는다.

세션 입장 전에 네 구역 보급함 준비, 종료 시 소유 display만 제거. 3블록 범위, 시선 dot>=.94, 벽 ray 검사를 통과하고 새로운 sneak edge가 발생했을 때만 기존 개인 사용권 ledger에 전달한다. down/미준비/연출/재입장 대기 중에는 수락하지 않는다. 공급 근처에서는 발전기/부활 hold와 중복 처리하지 않는다. ObjectiveTracker에 개인별 사용 가능/사용 완료 표시.

NBT 전환 잔여 경로도 수정: DevilsSpatial.clear는 .zone decode 대신 markers dimensions를 사용한다.

실제 Gradle compile + supplies9/spatial4 tests 통과. 실제 Fabric GameTest에서 네 구역 안전 보급함 배치, prepare 두 번 후 정확히12 display(3parts×4) 확인 및 모든 맵 voxel 비교 통과. runtime/supply-stations.xml/log. native 입력/시각 수락, 실플레이 로드아웃으로 지급 검증은 아직 미수행. 초기26.3 API 컴파일 오류(displayClientMessage, coloured Blocks constants)는 direct actionbar packet/registry 조회로 수정했다.

## Walker retention — latest user decision

- User selected the existing Walker rather than either Drive replacement. Model worker acknowledged and stopped Walker replacement work.
- DevilsActors now resolves WALKER to existing rg_walker; DevilsActorModel maps the strike shoot event to its existing fire clip. No model, atlas, rig or animation keys were changed.
- Retained asset: src/main/resources/destiny/guardian_rises/models/rg_walker.bbmodel, SHA256 21e327f7911bb16e31ca9578605ed9ba172fd33b1f33226c61f9478589cdc1b6. Its exported display rig contains 23 groups; the earlier 50-bone comparison referred to the source animation rig. Asset metadata identifies authored r4b clips, not original Drive actions.
- Actual Gradle compileJava passed. New strike visual/animation acceptance and multipart damage runtime verification remain pending.

## Walker multipart damage — real server integration

- Added DevilsWalkerGameTests with a package-scoped actor fixture: drive the actual director from solo briefing through refinery/device/defense to BL, then spawn the real Walker through DevilsActors.spawn (including retained rg_walker BetterModel attachment).
- Real Combat.damage assertions passed: six legs plus one core; leg canonical owner is root; 40 damage reduces pooled leg health by40; proxy HP stays unchanged; leg break is not a kill; exposed core precision; lethal core hit reports one real boss kill; all proxies removed; stale proxy cannot report another kill or director death.
- Actual Gradle compileGametestJava and filtered runGameTest succeeded. Evidence runtime/walker-damage.xml and walker-damage.log. The fixture advances the pure walker phase machine synchronously between hits; it does not establish native input, animation timing, camera, audio, frame rate, or full strike visual acceptance.
- Remaining damage limitation: owner/direct/server-tick ShotKey still conflates distinct emissions from one player in the same server tick. This test does not cover or claim to fix that behavior. Attack-emission identity and multi-part splash dedup remain next work.
- Normal Hive Thrall shader comparison was visually reviewed and shown; remaining projection edge noise sent to model worker. No candidate accepted for final in-game quality or integrated in this batch.

## Positional combat audio integration

- Wired DevilsSession sound callbacks to DevilsCombatSounds: direct positional HOSTILE packets only to the owning session audience, loaded and in the same world/range. Impact sounds use collision positions; firing, teleport and Brig armor-break callbacks are connected. Generation cancellation/leave/disconnect stop only this strike namespace's event IDs.
- Added reproducible importer and explicit gameplay routes. Final catalog:38 named source events,313 full-length mono Vorbis variants. Source SHA256 verification, finite/non-silent decode, retained frame count/rate, output manifest hashes and regenerated sample equivalence pass. All routes/files resolve; source actor owner matching and unmatched approximations are recorded in the manifest and runtime/combat-audio-assets.json. Corrected Acolyte fire to its actor-linked arc_rifle_fire and Wizard charge to wizard_cast_ability after actor-index audit.
- Actual Gradle runGameTest passed2 tests: previous Walker multipart/death regression plus queued ClientboundSoundPacket verification (correct source event, HOSTILE category, positional coordinates, in-range owning listener only, scoped stop packets). Evidence runtime/combat-audio.xml/log. This server run preceded the Acolyte/Wizard catalog-only correction; final catalog importer verification passed afterward. No native audio engine, speaker, mix acceptance, or final pack download acceptance is claimed.
- Original banks are represented as randomized media variants, not reconstructed Wwise layering. Brig unnamed firing/vocal events, exact Shank and Sepiks firing attribution, additional hurt/foley, BGM selection and audible mix remain pending. Generic death explosion selections are explicit approximations. No claim of full original audio fidelity.

## Explicit weapon emission identity

- Combat carries a scoped firing/contact identity only during its matching synchronous hurt call. Nested scopes restore the previous identity on close; no static player/tick identity is used for scoped weapon emissions.
- WeaponRuntime scopes accepted instant emissions, sword contacts, projectile ticks and impacts. Separate projectiles remain distinct in one server tick. Payload splash has its own nested identity so a legitimate impact plus explosive payload is not suppressed by the same Walker multipart dedup key.
- DevilsMob consumes explicit identities when present. Unscoped vanilla/ability sources retain the previous owner/direct/tick fallback; separate same-tick ability casts/perk chains are NOT yet certified.
- Real filtered GameTest passed2 tests: Walker damage/death + positional sound. Extended Walker fixture executes multiple attacks in one real server tick: first40 damage credits once across leg/core, separate10 and nested5 credit independently, resumed outer20 is rejected. Actual pooled loss55; leg break and one real death assertions remain intact. Evidence runtime/emission.xml/log.
- Actual WeaponRuntime paid-shot payload regression also passes: one ammunition round, secondary damage once, no recursive explosion or delayed repeat. The first run failed because its old splash expectation lacked the already user-approved primary1.5/special2.5 tuning (998.0504 expected vs997.0756 actual HP, exactly1.5 damage). Updated the independent expected splash factors, not production damage or tolerance. Preserved failure in payload-old-balance-failure.xml/log; successful rerun payload-emission-regression.xml/log. Other legacy payload-test numeric expectations were not audited and no entire-suite pass is claimed. Initial filter spelling selected no tests; corrected to the verified method wildcard.
- Model comparisons reviewed: Hive source colours preserved, projection edge noise remains; Sepiks FX black cards unacceptable; Brig still needs Dusk adaptation and runtime armor/clip contracts. Worker continues; no static candidate model installed.

## Live client session — initial observation

- Owned isolated server at 127.0.0.1:25610 completed Polymer resource-pack generation. Client uses its own /tmp/destiny-devils-qa-20261103/client profile and Vision8102. Server coordinator is wrapped by keep_awake.py with a7200second bound; no persistent security setting changed.
- Actual Vision state/framebuffer shows AccessibilityOnboardingScreen, inWorld=false. This is Minecraft first-run onboarding, not evidence of a locked Mac. Computer Use app inventory does not expose the Java game window; asked user to press Continue. No game-view, traversal or audio acceptance claimed.
- Preserved initial state, actual PNG and retained Walker SHA in runtime/live-initial/. The retained Walker hash remains21e327f7911bb16e31ca9578605ed9ba172fd33b1f33226c61f9478589cdc1b6.

## First framebuffer and subtitle correction

- Resolved first-run onboarding by stopping the owned client and changing onboardAccessibility=false only in the isolated QA profile. The earlier manual Continue request is no longer needed. Added the case-sensitive offline DevilsQA UUID to this fixture whitelist; production settings unchanged.
- Actual pack reload completed and solo admission reached RUNNING/BRIEFING in the NBT world. Captured runtime/live-initial/strike-entry.png. Native move sequence was consumed and released, but body position did not change during the briefing lock; this does NOT prove traversal.
- User requested black caption backgrounds, white NotoSans text and background QA. Existing font provenance verifies extracted NotoSansKR-Medium/Bold. Increased subtitle body20→32 and speaker17→26 in1920 HUD coordinates; wrapping1280 and spacing42. compileJava and ObjectiveTypographyTest passed.
- Actual framebuffer exposed dark glyphs under TextDisplay background (runtime/subtitle-readable/framebuffer.png, preserved failure). Replaced the native text background with separate black solid HUD plates at depth25, text at30, shadow off. Second compileJava passed; new visual acceptance pending.
- Client launcher now explicitly uses visionControlBackground=true per user authorization. Observed backgroundMode/Active/Gameplay=true while still focused; unfocused input is not yet certified. New bounded master awake wrapper spans restarts, exec6397/caffeinate91154,7200second limit, ownership recorded in /tmp/destiny-devils-qa-20261103/master-awake.json.

- Separate plates visually pass at854x480: runtime/subtitle-plates/framebuffer-final.png shows white NotoSansKR glyphs on fitted black row backgrounds, including long Korean briefing. Native TextDisplay background had obscured glyphs; no global shader changes were made. Source paragraph remains full-clip text; sentence-aligned timing is not implemented.
- Server status reached RY_APPROACH/8 occupied, then returned to BRIEFING before the later move sequence; native body remained fixed and attribute speed was0 during renewed briefing. Pending model integration prevents full encounter acceptance. This is not a successful traversal test. User-enabled background mode is live, but current snapshots still show focused window; inactive-window proof remains pending.

- Correction after inspecting actual RY plan: F1/F3 use only existing rg Dreg/Vandal/Shank/Captain. Missing dl models are a later-zone integration limitation, NOT a proven cause of this first-zone reset. Next investigation must instrument/inspect spawn placement failures and source attachment in the real RY instance. No root-cause fix claimed.

### Enemy attack knockback — 2026-11-03

User requested no player knockback from enemies. Combat.suppressesKnockback now suppresses Mob-attributed impulses against ServerPlayer before the existing LivingEntity mixin changes velocity or synchronizes it. This covers DevilsMob melee, bolts, splash and hazards through their shared mobAttack source, as well as other mob-attributed attacks. Existing damage/down processing and voluntary movement remain untouched.

Actual Gradle compile and filtered GameTest passed: enemy_damage_preserves_guardian_motion (one test selected). Real hurtServer reduces health while preserving the pre-existing nonzero movement vector; explicit forced mob knockback is suppressed and generic-source impulse still works. Evidence runtime/enemy-knockback.xml and .log. The second requested legacy filter did not select a test; do not count it as passed. Live client combat observation after this change remains pending; this is server validation, not framebuffer acceptance.

### Falls and proximity revival — 2026-11-03

Boundary falls now enter activity-owned GuardianDown at the last validated supported position, falling back to a safe checkpoint seat. Ordinary damage immunity cannot prevent a boundary death. High class jumps are not killed by the map ceiling. The down records one death and preserves the externally scheduled revival callback. No-target encounters pause spawning/AI while recovery clocks continue, preventing downed teammates from causing repeated spawn failure resets. Actual GuardianDown GameTests: 3 passed, including safe fall body, exactly one death, external timer ownership, reconnect and revival protection. Evidence runtime/fall-revival.xml/log. Session-level boundary and real-client fall visuals still require live validation.

Latest user revival policy: proximity alone within3 blocks with clear LoS charges ally revival for60 continuous ticks; no sneak required and supply targeting no longer blocks rescue. RY self-revive unlocks at100 ticks and requires jump; RF/BL/SP at600 ticks. Normal RY no longer wipes an all-down team while they wait to request self revive. Restricted-zone wipe remains160 ticks per existing plan. Targeted recovery/director tests and compileJava passed; evidence runtime/*-proximity.xml and proximity-revival.log. Client/native multi-player proximity validation remains pending.

Model worker returned /tmp/devils-drive-native-final-delta/manifest.json (7 models + generator). Fallen comparison reviewed: improved material colours but close-range slice noise remains. Not integrated yet; Hive comparison, hashes, real runtime readability and performance still pending.

### Drive model candidate integration — 2026-11-03

Reviewed source/candidate Hive and Fallen comparisons and integrated exactly eight manifest files after confirming all destination baselines absent and candidate SHA256 values matching. Source shader/native receipts retained under models/drive-native. Existing rg_walker untouched. The Brig colours are authored Dusk adaptation; slice noise remains a real close-range limitation, not accepted as final commercial quality.

Added DevilsModelAssets startup installer for seven dl models, reusing the versioned Rising installer with a separate exact catalog and ownership markers. Existing edited server files are retained. Targeted model tests and actual Gradle jar succeeded; JAR content and hash recorded in runtime/drive-model-jar.json. Runtime startup installed all seven models. BetterModel resourcepack/client load and visual acceptance remain pending.

Background native movement verified in tower after the updated pack loaded: windowActive=false, backgroundActive=true, native sequence completed/released, player moved (70.5,75,-19.5) -> (72.654844,75,-9.575365), neutral native keys and no lease afterward. Actual after PNG inspected. Evidence runtime/background-tower-move. This proves background movement in the self-camera tower state, not combat or cinematic movement.

Live candidate pack downloaded and gameplay entry succeeded. Runtime/drive-model-live/combat.png inspected: first Fallen packs attacking, player remains (333.5,80,276.5), in bounds, self-camera, inactive window eligible. Temporary resistance255 was an observation fixture, not difficulty acceptance. Third RY pack ground route checks still fail (route probe budget4, collision/support rejections), despite no player fall. Thus earlier falling was not the sole cause of third-pack failure; map spawn connectivity requires correction. No claim that all seven new mobs rendered in combat yet. Ended observation by leaving strike and clearing only the temporary resistance effect. Current owned server exec99557/client95544 remain for continued QA; master awake still bounded.

### Left-flank admission diagnosis — 2026-11-03

Added a real NBT-world admission assertion for all8 third-pack slots against the actual RY entry seat, retaining full4-map voxel validation. It reproduces DREG placement failure without any combat/player fall. Offline source route IN-L includes a2-block downward step, so added2 visible polished-andesite blocks at local(69,14,29/30), with generator provenance and regenerated NBT. This alone does NOT fix runtime path admission; failure and before/after evidence retained. After step, one-block offline reverse route exists (62 cells;8543 reachable), but native navigation ends at local(72,16,25), next to source walls/bars. Diagnostic now compares path-node budget vs navigation range to distinguish collision disconnection from bounded search exhaustion. No route fix acceptance yet.

Native diagnostic isolation:4x maximum visited nodes at range64 still cannot reach the entry; default node budget with FOLLOW_RANGE128 reaches it. Updated actor navigation range128 while retaining explicit64-block target acquisition in DevilsMob. Full NBT/admission regression running; no final pass asserted before results.

Real filtered NBT GameTest PASSED after range128 change: all8 third-pack slots admitted with reservations against actual RY.IN.0, plus existing4-map voxel/origin/heightmap and12 supply display assertions. Evidence runtime/left-route-fixed.xml/log. This verifies spawn admission, not live chase animation/performance or all player positions; live third-pack combat and other zones still pending.

### Fallen–Hive hostility — 2026-11-03

DevilsActors now scopes combat targets to participant players and opposite-faction root actors in the same runtime/zone. Hive: Thrall, Acolyte, Knight, Wizard; remaining strike kinds are Fallen. Same-faction, self, dead, retired and foreign-session actors are excluded. DevilsMob acquires the nearest valid target within64 blocks and uses the same predicate for melee, bolt collision, splash/hazard damage and hostile damage reception. Player-only spawn/warp safety checks are retained. Actor deaths still notify the director once; enemy damage does not call player Combat kill rewards.

Actual Fabric GameTests passed3/3: mixed RF actor/model fixture verifies mutual AI melee, ranged bolt damage, friendly/self/foreign-session exclusion, lethal enemy damage advancing the director exactly once, dead-target removal, and no player super-energy reward despite a prior player tag. Existing real Walker multipart death and combat audio packet regressions also pass. Evidence runtime/faction-combat.xml/log. First filter used dot rather than underscore and selected zero tests; corrected class filter selected the3 reported cases. This is server-side AI/physics evidence, not native-client infighting visuals or difficulty acceptance. Full unit gate/JAR result follows.

User steering: player detection or player damage takes priority over faction opponents. Each AI step checks visible participants within64 blocks first; an alerted player is remembered for100 ticks (5s, local tuning), refreshed while visible. Direct player damage alerts immediately even beyond passive detection range and through cover, including Walker proxy hits forwarded to the root. Invalid/disconnected/downed/creative players lose priority. Switching to a player cancels old-target windup/burst/reservation; already-fired bolts remain physical projectiles. No change to party scaling or spawn admission. Updated runtime regression includes visible-player priority for both factions, unseen-player exclusion, damage through cover, memory expiry and distant-player alert.

Full unit gate (before priority steering):2535 tests,16 failures across weapon geometry/reload policy, silhouette/GoldenGun HUD assets and legacy/reviewed sound manifests; not claimed passing and not assumed baseline-equivalent. Exact run retained in runtime/faction-full-unit.log. JAR task was not reached in that failed combined invocation.

Final player-priority server regression PASSED3/3, including the beyond64-block direct attack alert case. Evidence runtime/player-priority.xml/log. Native-client infighting/player-alert visual acceptance remains pending; no accepted whole-strike release or commit is claimed.

Actual Gradle jar succeeded after final priority changes; artifact/hash receipt runtime/player-priority-jar.json. Full unit failures above remain unresolved.

### Marauder Drive source and missing model repair — 2026-11-03

The runtime routes MARAUDER to dl_marauder but the seven-model installer omitted it. Downloaded the user-provided Dusk folder's actual Marauder archive (Drive file1VbRIBpcGXOb64MVp5JZPaKtBef3O7uhT), preserved its source, and audited the440-bone edit rig. Body shader graphs retained; the source scene's launcher/single loose blade were hidden in an evaluated copy, and the provided native dual-blade meshes/UVs attached at the original upper hand sockets with Drive blade materials. Lower-hand arc effects are part of the source body and match the wiki reference. Fixed relative/nested texture lookup in generator; no source files modified.

Mapped70 used deform groups to the native combat rig, with explicit anatomical restoration of stretched upper/lower arms and thighs. Source input58 hashes match previous native extraction. Candidate:2106 quads,17 clips,432 sampled native FK checks, maximum0.000209px position residual. Source/bake comparison shown before integration. Model installed as eighth owned dl asset; retained rg_walker unchanged. Installation/preservation and required-clip unit tests passed12/12. Runtime catalog test initially hit fixture collision for tall Brig at y4 (not model absence); moved its attachment-only fixture to clear air at y20 and reran. Evidence models/marauder-drive and runtime/catalog-fixture-collision.*.

Not final visual acceptance: close-range slice noise remains, mean luma59.39 is below historical80 reference (source colour retained), actual client grounding/stealth/attack contacts/performance still pending. Source comparison row displays combined radiance only; emitted arc texture is merged separately into the game candidate.

Final runtime catalog regression PASSED4/4: all13 planned species attach their actual BetterModel models, plus prior faction/player priority, Walker multipart death and combat audio tests. Attachment-only fixture is clear air; this does not establish grounded spawn admission or visual acceptance.

Actual Gradle jar succeeded; bundled Marauder bytes equal the reviewed candidate. Receipt runtime/marauder-jar.json. Existing client/8102 and server/25610 were not live at preflight; no new client launched this batch. Previous owned caffeinate91154 still reported active; no security settings changed. Goal remains incomplete and active.

### Live RY admission and player targeting follow-up — 2026-11-03 21:18 KST

Current isolated client loaded the final Marauder pack and entered the strike. After briefing, actual framebuffer shows the objective HUD. Server status reports RUNNING / RY_APPROACH / 24/24: all three approach packs now admitted. Native movement completed from (333.5,80,276.5) to (335.654844,80,285.402024), with neutral keys and released lease afterward. Actual PNG shows Fallen firing toward the player. The idle QA player was subsequently downed by Captain; server recorded100-tick self-revive readiness. This is not difficulty acceptance. Vision control correctly rejects spectator state, so native self-revive was not tested; no control safety gate was bypassed. Left strike through the existing server command, returned to tower and verified neutral control state.

Evidence runtime/player-priority-live. Mixed-faction target-switch visuals remain unverified; current acceptance for hostility/player priority is the real server AI fixture in runtime/model-catalog.xml and player-priority.xml. Model slice noise remains visible in combat. Full strike acceptance and the previously recorded16 unit failures remain unresolved.

### Source-labelled descent music — 2026-11-03

Added DEVILS_DESCENT to the existing personal ActivityMusic path. Active strike briefing selects it; existing MusicService plays/stops on RECORDS, waits for client and pack readiness, and owns each listener. Generation cancellation and activity cleanup reset the one-shot immediately, including same-tick restart. No arbitrary combat playlist was assigned.

New scripts/strikes/import_devils_music.py verifies all41 delivered music OGGs and their original WEMs against SHA256SUMS plus bank/index/validation metadata. Imports the explicitly labelled cosmo_portal1_descent source80D715DA as unchanged OGG bytes (11.590104s stereo) with stream:true. Volume0.3 is provisional mix tuning. Other combat candidates remain unreviewed; silent80D63BFA excluded. Full-length links and provenance are in music/audition.md and source-inventory.json.

Actual targeted Gradle tests passed12/12 (music timeline + every scheduled event duration/stream resource). Live isolated server rebuilt its pack; live-pack.json confirms the imported OGG bytes and sound definition. Client entered briefing; actual briefing.png inspected. Server trace shows descent start21:23:17, natural stop21:23:29; second start21:23:53 and early-exit stop21:23:54 with tower music resuming. No client audio-engine capture or speaker listening was performed, so these prove server lifecycle/resource inclusion only. Verified neutral input and tower return before stopping owned server/client. Existing all-strike acceptance, combat cue selection/loops, model slice noise and16 full-unit failures remain open. Goal remains active; no accepted completion commit.

Actual Gradle jar succeeded after music integration; bundled descent bytes verified, receipt music/jar.json. An early ZIP inspection raced the in-progress jar writer and failed; inspection was repeated only after Gradle completed successfully.

### Surface quality experiments — 2026-11-03

Marauder source/current/four candidate comparisons saved under models/surface-study. Destination-colour dilation, twice-finer planes,4096 atlas and normal-axis filtering were evaluated in isolated output folders. None met the visual threshold for integration; all live model/source bytes preserved. Geometry/texture expansion alone is not an accepted quality fix. Corrected outward-winding/backface-masked offline rendering still shows defects. Next evidence needed is controlled near/mid-range actual-client rendering before shared projection changes. Goal remains active.
