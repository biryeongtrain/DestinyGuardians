# W332 구현 궁극기 원본·런타임 검토 목록

현재 장착 가능한 궁극기는 **19개: Hunter7 / Titan6 / Warlock6**다. `AbilityRegistry` 등록과 `CharacterLoadouts`의 직업·속성·SUPER 필터가 기준이다. Stasis/Strand/Twilight Arsenal/Song of Flame은 이 구현의 선택 가능한 목록이 아니다.

이 문서는 코드·리소스·기존 원본 평가 기록을 대조한 catalog다. **이번 작업에서 추가 `.blend`를 열거나 인게임 모션을 검증하지 않았다.** Arc/Spectral은 기존 W330/W331 직접 평가·native 기록을 참조한다. 나머지의 실제 외형·파지·프레임 연속성은 master가 아래 시나리오로 확인해야 한다.

사용자 요구의 **2틱은 display interpolation duration**이다. gameplay contact, cooldown, entry blend, clip 길이 변경으로 해석하지 않는다. GCB 지원 경로는 별도 구현 담당이 확인한다.

## 원본 가용성

- Light 전달본 `/Users/qf/Downloads/Destiny-Light-Abilities-2026-10-28/Destiny-Light-Abilities-2026-10-28`의 source.blend/CLIPS.md/inspection.json을 읽기 전용으로 목록화했다. 초 단위 길이는 원본30fps 액션 범위이며 실제 Destiny 재생 배속까지 검증한 수치는 아니다.
- 지정 WindowsReturn 두 `/Volumes/qf-ssd/...` 원본은 현재 마운트되어 있지 않다. Downloads 최상위에 Dark Abilities 전달본은 없었다. 없는 원본을 확인했다고 표시하지 않는다.
- W229 Daybreak slash1/2, sword-catch/glide는 기존 provenance에 해시가 남아 있으나 현재 Light 그룹에 모두 포함되어 있지는 않다. 기존 source evaluation과 이번 재평가를 구분한다.

## 우선순위와 전체 시나리오

| 우선순위 | Super ID / 직업·속성 | 현재 문제·판단 | native 입력 / 최소 캡처 |
|---|---|---|---|
| P1_retarget_retime | `destiny:hunter/shadowshot` / hunter·VOID | Source ground AD97/air AD8A are1.3s. W199 attack.9s retimes lower body and forces endpoint toward ready; upper body preserves authored bow/cheek/nock. Air source inspected but deferred; release stays fixed7ticks. This is a partial adaptation, not full original source motion. | Shift+F only; automatic draw/release; no click should duplicate it. Aim level/up/down; observe bow grip and recovery. Repeat while falling. / 5s |
| P1_source_attack_unused | `destiny:warlock/nova_warp` / warlock·VOID | Ground/air cast2.0333s exist. Product burst attack.6s and idle/move/air.8s are authored. Original charge-exit A99D1.2667s and single-frame charge-idle A99C are unused. Replacing visual must retain gameplay charge12/recovery6 and damage epoch semantics until explicitly revised. | Shift+F; wait2.3s; left click to charge/burst; wait1.2s; Shift+left click blink; walk; repeat falling activation/burst. Observe burst recovery + expiry. / 28s |
| P1_phase_gap | `destiny:hunter/storms_edge` / hunter·ARC | Original dagger cast1.6667s and blink-enter.0667s exist. No _attack clip: each extra charge explicitly reuses _start. Native blink-enter only covers2/30s, not an invented full spin. No end source, generic swing fallback. | Shift+F automatic first throw; wait2s; left click twice with2s gaps; aim at safe wall/owned enemy so each throw can collide and blink. Observe charges0 and exit. / 9s |
| P1_attack_source_gap | `destiny:titan/burning_maul` / titan·SOLAR | Only original ground/air casts1.3s are in Light group. Product light.65s/heavy.9s and idle/move/air.8s are authored adapters; no matching original attack extraction is present. Shift-heavy only accepted while supported. | Shift+F; wait1.5s; left click x2 with1s gaps; Shift+left click heavy; observe wave and full recovery; air activation + normal light; walk. / 28s |
| P1_authored_attack_source_gap | `destiny:titan/arc_super` / titan·ARC | Ground/air cast/landing source retained. Independent light _attack.5s and ready/move loops are authored; Light source group has casts/air idle but no verified light punch. Air primary selects air/landing pose; do not relabel a cast as original light attack. | Shift+F; wait1.7s; left click x2 at.9s gaps; jump and click to slam; land. Repeat air activation from platform; expire/cancel. / 28s |
| P2_air_source_unused | `destiny:titan/solar_super` / titan·SOLAR | Ground cast1.2667s and throw1.5667s are full source. Source air cast/air melee exist but no product _start_air or air-throw selector. Idle source hold; move includes authored lower gait. | Shift+F; wait1.5s; left click x2 at1.8s gaps; walk; repeat activation/throw falling. Observe hammer item recovery and expiry. / 24s |
| P2_air_source_unused | `destiny:titan/void_super` / titan·VOID | Ground cast1.4s + throw1.3333s + Sentinel sprint composition. Original air cast1.3333s/throw.8s and weak combos exist but product has only ground cast/throw contract; no claim of original melee combos. | Shift+F; wait1.6s; left click x2 at1.6s gaps; walk; repeat falling cast/throw. / 20s |
| P2_air_source_unused | `destiny:warlock/arc_super` / warlock·ARC | Ground cast1.2333/attack-enter.4667/attack-idle.5/end.3333s full source. Air cast1.2667 and blink source exist but not selected. Attack is repeated enter pulses rather than complete enter→hold→exit channel state machine. | Shift+F; wait1.5s; repeated left click for2s to sustain channel; release and observe end; move; repeat falling activation. / 19s |
| P2_air_source_unused | `destiny:warlock/solar_super` / warlock·SOLAR | Ground cast1.5667s + event-linked slash1.0333s are pinned source; source air cast exists but not installed/selected. Idle/move use generic sword-catch Replacement source, not confirmed Daybreak ready; air lower body uses generic glide. Slash2 source reviewed previously but not selected. | Shift+F; wait1.8s; left click x2 at1.3s gaps; walk; jump/glide and click; repeat air activation; observe sword/camera recovery. / 27s |
| P2_air_source_unused | `destiny:warlock/void_super` / warlock·VOID | Source ground cast1.3s occupies _attack, auto-selected on first tick; _start/_idle absent intentionally. Source air AD81 also1.3s but not installed/selected. Release15ticks (14+entry1); visual duration27ticks. Common end swing fallback. | Shift+F automatic Nova; no click; observe release and complete follow-through until projectile impact. Repeat falling. / 6s |
| P2_source_gap | `destiny:hunter/golden_gun` / hunter·SOLAR | No Golden Gun animation group exists in the supplied Light package. Current start.45/shot.35/end.35 and ready loop2s are authored H15 motion, not an original extraction. | Shift+F; wait.6s; left click x3 with.5s gaps; retain final dissolve/recovery. Repeat air activation once. / 12s |
| P2_native_pending | `destiny:hunter/blade_barrage` / hunter·SOLAR | Single complete cast1.9667s source; two automatic volleys at15/29ticks. No separate source attack/end identified in this supplied group. Common end path invokes vanilla WHACK when _end is missing. | Shift+F; no primary input required; observe both knife volleys and full recovery. Repeat falling. / 5s |
| P2_native_pending | `destiny:hunter/gathering_storm` / hunter·ARC | Complete cast1.6333s; automatic release5ticks is a provisional gameplay cue, not a decoded source event. Hand prop explicitly released; flight/field outlive cast. No independent end clip; generic end swing fallback. | Shift+F; no attack click; aim at owned target/wall; observe staff release and return, field remains. / 13s |
| P2_native_pending | `destiny:titan/thundercrash` / titan·ARC | Ground/air enter.8s, source single-frame flight extended to.2s hold, normal exit.8333s and wall exit.6667s. Source hold period is authored, not duration compression. Steering/impact are runtime, not clip translation. | Shift+F; steer camera into floor/owned enemy; second activation into vertical wall to cover end_wall; third air activation. No primary attack needed. / 8s |
| P2_native_pending | `destiny:titan/ward_of_dawn` / titan·VOID | Source ground1.4/air-enter.4333/air-loop.9/land1.1s exist. Field installs only on support; player cast/camera is released while independent field remains. No separate end action required. | Shift+F on floor; observe dome and weapon return. Repeat falling from platform; observe air-enter/loop/land then dome; no click. / 8s |
| P2_native_pending | `destiny:warlock/chaos_reach` / warlock·ARC | Complete source enter.7333/end.4; original loop is single frame and product hold.0667. Alternate source exit.8 exists but variant is not proven required. Runtime plays exit before end() cleanup, so do not misclassify the final stop as skipped exit. | Shift+F; aim beam at owned target; no click; observe channel and.4s exit; repeat air activation. / 6s |
| P2_native_pending | `destiny:warlock/well_of_radiance` / warlock·SOLAR | Complete source ground1.7667/air-enter.5667/land1.0667. Landed sword planted after full landing phase; independent Well remains600ticks, player returns to weapon immediately after planting. | Shift+F on floor; observe sword plant/weapon return. Repeat platform fall; observe air-enter, supported landing, sword plant. No attack click. / 8s |
| baseline_W330 | `destiny:hunter/spectral_blades` / hunter·VOID | Nine directly evaluated original actions + source final guard idle/air + mixed authored lower-body gait. Full duration, continuous quaternion metadata. Source contact beats explicitly provisional. Heavy uses Shift+left click; no invented light2-air clip. | Shift+F; wait1.8s; left click x3 at1.9s gaps; Shift+left click heavy; observe invisibility. Repeat cast/light/heavy in air; walk/run and blocked walk. / 25s |
| baseline_W330_W331 | `destiny:hunter/arc_staff` / hunter·ARC | Ground/air cast + 3 ground lights + air light + four source dodges. Existing ready/move/end are legacy authored poses; heavy/uppercut/slam source actions are available but not a registered runtime primary/heavy contract. | Shift+F; wait1.6s; left click x3 with1.6s gaps; direction + Shift twice for all four directions (modless DoubleSneak); GCB uses its separate dodge binding; jump then left click; idle and move; expiry. / 24s |

## 각 궁극기의 실제 클립과 원본 대응

숫자는 clip 본체의 길이다. entry/exit blend는 JSON의 별도 필드로 남겼다. W229는 timing-manifest가 출처이고, W330은 직접 Blender 평가 manifest가 출처다. 그 밖의 W230 tag는 **이름 의미 + 동일 길이로 좁힌 후보**이며, 별도의 per-clip provenance를 찾지 못한 경우 원본 대응 확정으로 표시하지 않았다. hold/composite의 반복 주기는 원본 움직임의 배속으로 비교하지 않는다.

### 아크 지팡이 — `destiny:hunter/arc_staff`

Runtime: `src/main/java/kim/biryeong/destiny/ability/hunter/HunterSuper.java`. 분류: **baseline_W330_W331**. 설정: `{"duration_ticks":400,"strike_interval_ticks":6,"reach":4.5,"arc_degrees":70,"damage":16}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| idle | 1.600000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| attack | 1.300000 | 80A8A937 / 1.3 | full source span matched; W330 direct Blender evaluation manifest |
| start | 1.433333 | 80A8A922 / 1.4333333333333333 | full source span matched; W330 direct Blender evaluation manifest |
| end | 0.350000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| move | 0.600000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| start_air | 1.300000 | 80A8A95C / 1.3 | full source span matched; W330 direct Blender evaluation manifest |
| attack_weak_2 | 1.400000 | 80A8A92A / 1.4 | full source span matched; W330 direct Blender evaluation manifest |
| attack_weak_3 | 1.233333 | 80A8A92B / 1.2333333333333334 | full source span matched; W330 direct Blender evaluation manifest |
| attack_air | 0.666667 | 80A8A92D / 0.6666666666666666 | full source span matched; W330 direct Blender evaluation manifest |
| dodge_forward | 1.033333 | 80A8A938 / 1.0333333333333334 | full source span matched; W331 direct Blender source review |
| dodge_backward | 1.033333 | 80A8A93C / 1.0333333333333334 | full source span matched; W331 direct Blender source review |
| dodge_left | 1.033333 | 80A8A93E / 1.0333333333333334 | full source span matched; W331 direct Blender source review |
| dodge_right | 1.033333 | 80A8A93F / 1.0333333333333334 | full source span matched; W331 direct Blender source review |

Ground/air cast + 3 ground lights + air light + four source dodges. Existing ready/move/end are legacy authored poses; heavy/uppercut/slam source actions are available but not a registered runtime primary/heavy contract.

미연결 원본 후보: 80A8A933 hunter_arcstrider_staff_melee_heavy_1 (1.366667s); 80A8A935 hunter_arcstrider_staff_melee_heavy_slam_air_enter (0.700000s); 80A8A934 hunter_arcstrider_staff_melee_weak_2_hold (0.333333s); 80A8A95F hunter_arcstrider_staff_melee_heavy_2 (1.800000s); 80A8A966 hunter_arcstrider_staff_melee_medium_1 (1.266667s); 80A8A972 hunter_arcstrider_staff_melee_medium_2 (1.233333s); 80A8A985 hunter_arcstrider_staff_melee_heavy_1_air (1.000000s); 80A8AAE4 hunter_arcstrider_staff_melee_heavy_uppercut (0.933333s)

Native: Shift+F; wait1.6s; left click x3 with1.6s gaps; direction + Shift twice for all four directions (modless DoubleSneak); GCB uses its separate dodge binding; jump then left click; idle and move; expiry. 조건: Ground + grounded dodge; raised launch pad for air cast/air attack. 최소 24s. 장착은 직업→속성→`/guardian equip destiny:hunter/arc_staff` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 황금 총 — `destiny:hunter/golden_gun`

Runtime: `src/main/java/kim/biryeong/destiny/ability/hunter/HunterSuper.java`. 분류: **P2_source_gap**. 설정: `{"duration_ticks":200,"shots":3,"shot_interval_ticks":8,"range":80,"damage":80}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| idle | 2.000000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| attack | 0.350000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| start | 0.450000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| end | 0.350000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |

No Golden Gun animation group exists in the supplied Light package. Current start.45/shot.35/end.35 and ready loop2s are authored H15 motion, not an original extraction.

미연결 원본 후보:

Native: Shift+F; wait.6s; left click x3 with.5s gaps; retain final dissolve/recovery. Repeat air activation once. 조건: Ground and falling from a low platform. 최소 12s. 장착은 직업→속성→`/guardian equip destiny:hunter/golden_gun` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 그림자 사격 — `destiny:hunter/shadowshot`

Runtime: `src/main/java/kim/biryeong/destiny/ability/hunter/HunterSuper.java`. 분류: **P1_retarget_retime**. 설정: `{"tether_radius":7,"tether_ticks":160,"damage":20}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| idle | 2.400000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| attack | 0.900000 | 80A8AD97 / 1.3 | length differs from source (retime/partial adaptation); W199 retarget PLAN + sealed source sample |

Source ground AD97/air AD8A are1.3s. W199 attack.9s retimes lower body and forces endpoint toward ready; upper body preserves authored bow/cheek/nock. Air source inspected but deferred; release stays fixed7ticks. This is a partial adaptation, not full original source motion.

미연결 원본 후보: 80A8AD8A bow_cast_air; hunter_nightstalker_bow_cast_air (1.300000s)

Native: Shift+F only; automatic draw/release; no click should duplicate it. Aim level/up/down; observe bow grip and recovery. Repeat while falling. 조건: Ground; falling cast above safe landing floor. 최소 5s. 장착은 직업→속성→`/guardian equip destiny:hunter/shadowshot` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 칼날 장전 — `destiny:hunter/blade_barrage`

Runtime: `src/main/java/kim/biryeong/destiny/ability/hunter/HunterExpandedSupers.java`. 분류: **P2_native_pending**. 설정: `{"cast_ticks":40,"knives_per_volley":7,"first_contact_ticks":15,"second_contact_ticks":29,"projectile_speed":1.5,"fan_spread":0.055,"detonation_delay_ticks":10,"impact_damage":1,"damage":8,"radius":2.2}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.966667 | 80A8AD86 / 1.9666666666666666 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |

Single complete cast1.9667s source; two automatic volleys at15/29ticks. No separate source attack/end identified in this supplied group. Common end path invokes vanilla WHACK when _end is missing.

미연결 원본 후보:

Native: Shift+F; no primary input required; observe both knife volleys and full recovery. Repeat falling. 조건: Ground and falling; clear forward target volume. 최소 5s. 장착은 직업→속성→`/guardian equip destiny:hunter/blade_barrage` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 폭풍결집 — `destiny:hunter/gathering_storm`

Runtime: `src/main/java/kim/biryeong/destiny/ability/hunter/HunterExpandedSupers.java`. 분류: **P2_native_pending**. 설정: `{"cast_ticks":33,"first_contact_ticks":5,"projectile_speed":1.65,"impact_damage":15,"lightning_damage":12,"lightning_delay_ticks":40,"field_delay_ticks":24,"field_duration_ticks":160,"pulse_ticks":14,"pulse_damage":5,"radius":4}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.633333 | 80A8ABF2 / 1.6333333333333333 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |

Complete cast1.6333s; automatic release5ticks is a provisional gameplay cue, not a decoded source event. Hand prop explicitly released; flight/field outlive cast. No independent end clip; generic end swing fallback.

미연결 원본 후보:

Native: Shift+F; no attack click; aim at owned target/wall; observe staff release and return, field remains. 조건: Ground + falling cast; target within projectile range. 최소 13s. 장착은 직업→속성→`/guardian equip destiny:hunter/gathering_storm` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 폭풍의 칼날 — `destiny:hunter/storms_edge`

Runtime: `src/main/java/kim/biryeong/destiny/ability/hunter/HunterExpandedSupers.java`. 분류: **P1_phase_gap**. 설정: `{"cast_ticks":34,"duration_ticks":400,"first_contact_ticks":19,"attack_contact_ticks":18,"projectile_speed":2,"blink_range":15,"radius":4,"damage":20}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.666667 | 80A8ACCE / 1.6666666666666667 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| blink | 0.066667 | 80A8ACF0 / 0.06666666666666667 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |

Original dagger cast1.6667s and blink-enter.0667s exist. No _attack clip: each extra charge explicitly reuses _start. Native blink-enter only covers2/30s, not an invented full spin. No end source, generic swing fallback.

미연결 원본 후보:

Native: Shift+F automatic first throw; wait2s; left click twice with2s gaps; aim at safe wall/owned enemy so each throw can collide and blink. Observe charges0 and exit. 조건: Ground and falling; safe blink destination required. 최소 9s. 장착은 직업→속성→`/guardian equip destiny:hunter/storms_edge` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 스펙트럼 칼날 — `destiny:hunter/spectral_blades`

Runtime: `src/main/java/kim/biryeong/destiny/ability/hunter/HunterExpandedSupers.java`. 분류: **baseline_W330**. 설정: `{"cast_ticks":32,"duration_ticks":470,"attack_interval_ticks":10,"attack_contact_ticks":6,"heavy_contact_ticks":3,"light_cost_ticks":10,"heavy_cost_ticks":35,"range":3.3,"heavy_range":4,"damage":11,"heavy_damage":18,"attack2_contact_ticks":4}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.566667 | 80A8AAC4 / 1.5666666666666667 | full source span matched; W330 direct Blender evaluation manifest |
| attack3 | 1.733333 | 80A8AAC5 / 1.7333333333333334 | full source span matched; W330 direct Blender evaluation manifest |
| attack2 | 1.466667 | 80A8AAC7 / 1.4666666666666666 | full source span matched; W330 direct Blender evaluation manifest |
| attack | 1.466667 | 80A8AAC8 / 1.4666666666666666 | full source span matched; W330 direct Blender evaluation manifest |
| start_air | 1.600000 | 80A8AAD0 / 1.6 | full source span matched; W330 direct Blender evaluation manifest |
| attack3_air | 0.966667 | 80A8AAE5 / 0.9666666666666667 | full source span matched; W330 direct Blender evaluation manifest |
| attack_air | 0.833333 | 80A8AAF8 / 0.8333333333333334 | full source span matched; W330 direct Blender evaluation manifest |
| idle | 0.800000 | 80A8AAC4 / 1.5666666666666667 | hold or composite; clip period is authored, not source playback speed; W330 direct Blender evaluation manifest |
| move | 0.800000 | 80A8AAC4 / 1.5666666666666667 | hold or composite; clip period is authored, not source playback speed; W330 direct Blender evaluation manifest |
| air | 0.800000 | 80A8AAD0 / 1.6 | hold or composite; clip period is authored, not source playback speed; W330 direct Blender evaluation manifest |
| heavy | 1.000000 | 80A8B4F5 / 1.0 | full source span matched; W330 direct Blender evaluation manifest |
| heavy_air | 0.900000 | 80A8B55A / 0.9 | full source span matched; W330 direct Blender evaluation manifest |

Nine directly evaluated original actions + source final guard idle/air + mixed authored lower-body gait. Full duration, continuous quaternion metadata. Source contact beats explicitly provisional. Heavy uses Shift+left click; no invented light2-air clip.

미연결 원본 후보: 80A8A7CC hunter_bladedancer_arc_blade_melee_weak_1 (1.466667s); 80A8A7D5 hunter_bladedancer_arc_blade_melee_weak_2 (1.466667s); 80A8A7CF hunter_bladedancer_arc_blade_melee_weak_3 (1.566667s); 80A8AAE8  (1.733333s)

Native: Shift+F; wait1.8s; left click x3 at1.9s gaps; Shift+left click heavy; observe invisibility. Repeat cast/light/heavy in air; walk/run and blocked walk. 조건: Ground; raised platform fall for air actions; long enough air hang for selection. 최소 25s. 장착은 직업→속성→`/guardian equip destiny:hunter/spectral_blades` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 대혼란의 주먹 — `destiny:titan/arc_super`

Runtime: `src/main/java/kim/biryeong/destiny/ability/titan/TitanSuper.java`. 분류: **P1_authored_attack_source_gap**. 설정: `{"duration_ticks":500,"deploy_ticks":31,"air_deploy_ticks":15,"land_ticks":19,"startup_contact_ticks":28,"attack_interval_ticks":12,"max_attacks":16,"damage":24,"radius":3.5,"attack_contact_ticks":4}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| idle | 0.800000 | unresolved / None | unresolved/no single motion source; pinned existing timing-manifest |
| move | 0.800000 | unresolved / None | unresolved/no single motion source; pinned existing timing-manifest |
| air | 1.500000 | 80A8A6AA / 1.5 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| start | 1.466667 | 80A8AD9A / 1.4666666666666666 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| start_air | 0.666667 | 80A8AD9B / 0.6666666666666666 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| land | 0.900000 | 80A8AD9C / 0.9 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| attack | 0.500000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |

Ground/air cast/landing source retained. Independent light _attack.5s and ready/move loops are authored; Light source group has casts/air idle but no verified light punch. Air primary selects air/landing pose; do not relabel a cast as original light attack.

미연결 원본 후보: 80A8AD9D titan_striker_fistsofhavoc_cast_enter_forward (1.466667s); 80A8AD93 titan_striker_fistsofhavoc_cast_enter_forward_long (1.600000s)

Native: Shift+F; wait1.7s; left click x2 at.9s gaps; jump and click to slam; land. Repeat air activation from platform; expire/cancel. 조건: Ground; platform fall with solid landing floor for _land. 최소 28s. 장착은 직업→속성→`/guardian equip destiny:titan/arc_super` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 태양의 망치 — `destiny:titan/solar_super`

Runtime: `src/main/java/kim/biryeong/destiny/ability/titan/TitanSuper.java`. 분류: **P2_air_source_unused**. 설정: `{"duration_ticks":420,"deploy_ticks":26,"attack_interval_ticks":32,"max_attacks":16,"damage":24,"radius":3,"projectile_speed":1.7,"attack_contact_ticks":6}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.266667 | 80A8A8FE / 1.2666666666666666 | full source span matched; pinned existing timing-manifest |
| attack | 1.566667 | 80A8A8AE / 1.5666666666666667 | full source span matched; pinned existing timing-manifest |
| idle | 0.500000 | 80A8A8AE / 1.5666666666666667 | hold or composite; clip period is authored, not source playback speed; pinned existing timing-manifest |
| move | 0.800000 | unresolved / None | unresolved/no single motion source; pinned existing timing-manifest |

Ground cast1.2667s and throw1.5667s are full source. Source air cast/air melee exist but no product _start_air or air-throw selector. Idle source hold; move includes authored lower gait.

미연결 원본 후보: 80A8A8B2 titan_sunbreaker_hammer_melee_lunge; hammer_melee_lunge (1.566667s); 80A8A8F1 hammer_cast_air; titan_sunbreaker_hammer_cast_air_enter (1.266667s); 80A8A8F0 hammer_charge (1.266667s); 80A8A8F2 hammer_charge_air (0.833333s); 80A8A8F3 titan_sunbreaker_hammer_melee_lunge_air; hammer_melee_lunge_air (0.833333s)

Native: Shift+F; wait1.5s; left click x2 at1.8s gaps; walk; repeat activation/throw falling. Observe hammer item recovery and expiry. 조건: Ground + falling; safe projectile target. 최소 24s. 장착은 직업→속성→`/guardian equip destiny:titan/solar_super` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 파수병 방패 — `destiny:titan/void_super`

Runtime: `src/main/java/kim/biryeong/destiny/ability/titan/TitanSuper.java`. 분류: **P2_air_source_unused**. 설정: `{"duration_ticks":340,"deploy_ticks":28,"attack_interval_ticks":27,"max_attacks":16,"damage":24,"radius":3,"projectile_speed":1.7,"attack_contact_ticks":6}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.400000 | 80A8A928 / 1.4 | full source span matched; pinned existing timing-manifest |
| attack | 1.333333 | 80A8A924 / 1.3333333333333333 | full source span matched; pinned existing timing-manifest |
| idle | 0.500000 | 80A8A928 / 1.4 | hold or composite; clip period is authored, not source playback speed; pinned existing timing-manifest |
| move | 0.500000 | unresolved / None | unresolved/no single motion source; pinned existing timing-manifest |

Ground cast1.4s + throw1.3333s + Sentinel sprint composition. Original air cast1.3333s/throw.8s and weak combos exist but product has only ground cast/throw contract; no claim of original melee combos.

미연결 원본 후보: 80A8A7D1 shield_melee_weak_1 (1.000000s); 80A8A7E6 shield_melee_weak_2 (1.033333s); 80A8A7D0 shield_melee_weak_3 (1.100000s); 80A8A7E7 shield_melee_weak_1_air; shield_melee_airborne_weak_1 (0.800000s); 80A8A7D2 shield_melee_airborne_heavy_1 (1.066667s); 80A8A81D shield_melee_heavy_slam_air_enter (0.800000s); 80A8A94F cast_air_crusader; titan_sentinel_shield_cast_air_enter (1.333333s); 80A8A967 titan_sentinel_shield_throw_air; shield_throw_air_crusader (0.800000s); 80A8A964 titan_sentinel_shield_charge (1.166667s); 80A8A983 titan_sentinel_shield_charge_air (1.033333s); 80A8A97D titan_sentinel_shield_charge_combo (1.166667s); 80A8A9AD titan_sentinel_shield_sprint (0.500000s)

Native: Shift+F; wait1.6s; left click x2 at1.6s gaps; walk; repeat falling cast/throw. 조건: Ground + falling; owned enemy + wall for shield flight. 최소 20s. 장착은 직업→속성→`/guardian equip destiny:titan/void_super` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 천둥충돌 — `destiny:titan/thundercrash`

Runtime: `src/main/java/kim/biryeong/destiny/ability/titan/TitanExpandedSupers.java`. 분류: **P2_native_pending**. 설정: `{"flight_ticks":90,"flight_speed":1.0,"max_distance":64,"damage":38,"radius":4.5,"aftershock_damage":6}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 0.800000 | 80A8AAD4 / 0.8 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| idle | 0.200000 | 80A8AAE6 / 0.0 | single original pose extended into hold; not a retimed motion; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| air | 0.200000 | 80A8AAE6 / 0.0 | single original pose extended into hold; not a retimed motion; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| start_air | 0.800000 | 80A8AAE7 / 0.8 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| end_wall | 0.666667 | 80A8AAED / 0.6666666666666666 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| end | 0.833333 | 80A8AAFC / 0.8333333333333334 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |

Ground/air enter.8s, source single-frame flight extended to.2s hold, normal exit.8333s and wall exit.6667s. Source hold period is authored, not duration compression. Steering/impact are runtime, not clip translation.

미연결 원본 후보:

Native: Shift+F; steer camera into floor/owned enemy; second activation into vertical wall to cover end_wall; third air activation. No primary attack needed. 조건: Ground/air start; safe floor and wall in bounded flight corridor. 최소 8s. 장착은 직업→속성→`/guardian equip destiny:titan/thundercrash` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 불타는 망치 — `destiny:titan/burning_maul`

Runtime: `src/main/java/kim/biryeong/destiny/ability/titan/TitanExpandedSupers.java`. 분류: **P1_attack_source_gap**. 설정: `{"duration_ticks":500,"light_cost":0.04,"heavy_cost":0.08,"light_contact_ticks":6,"heavy_contact_ticks":7,"spin_radius":3,"spin_damage":14,"wave_damage":28,"wave_distance":14}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.300000 | 80A8AAF7 / 1.3 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| start_air | 1.300000 | 80A8AB1A / 1.3 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| idle | 0.800000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| move | 0.800000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| air | 0.800000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| attack | 0.650000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| attack2 | 0.900000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |

Only original ground/air casts1.3s are in Light group. Product light.65s/heavy.9s and idle/move/air.8s are authored adapters; no matching original attack extraction is present. Shift-heavy only accepted while supported.

미연결 원본 후보:

Native: Shift+F; wait1.5s; left click x2 with1s gaps; Shift+left click heavy; observe wave and full recovery; air activation + normal light; walk. 조건: Ground for heavy; falling cast with safe landing for air variant. 최소 28s. 장착은 직업→속성→`/guardian equip destiny:titan/burning_maul` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 새벽의 수호물 — `destiny:titan/ward_of_dawn`

Runtime: `src/main/java/kim/biryeong/destiny/ability/titan/TitanExpandedSupers.java`. 분류: **P2_native_pending**. 설정: `{"field_ticks":600,"air_wait_ticks":80,"radius":4,"health":160}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| air | 0.900000 | 80A8AD95 / 0.9 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| start_air | 0.433333 | 80A8AD98 / 0.43333333333333335 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| start | 1.400000 | 80A8ADA0 / 1.4 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| land | 1.100000 | 80A8ADA2 / 1.1 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |

Source ground1.4/air-enter.4333/air-loop.9/land1.1s exist. Field installs only on support; player cast/camera is released while independent field remains. No separate end action required.

미연결 원본 후보:

Native: Shift+F on floor; observe dome and weapon return. Repeat falling from platform; observe air-enter/loop/land then dome; no click. 조건: Ground + falling; solid landing required; avoid floating-field fixture. 최소 8s. 장착은 직업→속성→`/guardian equip destiny:titan/ward_of_dawn` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 폭풍몰입 — `destiny:warlock/arc_super`

Runtime: `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockSuper.java`. 분류: **P2_air_source_unused**. 설정: `{"duration_ticks":320,"attack_interval_ticks":11,"range":10,"chain_range":4,"max_targets":3,"damage":5,"attack_contact_ticks":5,"cast_ticks":25,"attack_duration_ticks":10}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.233333 | 80A8A8B0 / 1.2333333333333334 | full source span matched; pinned existing timing-manifest |
| attack | 0.466667 | 80A8A8A8 / 0.4666666666666667 | full source span matched; pinned existing timing-manifest |
| idle | 0.500000 | 80A8A8AC / 0.5 | full source span matched; pinned existing timing-manifest |
| end | 0.333333 | 80A8A8AA / 0.3333333333333333 | full source span matched; pinned existing timing-manifest |

Ground cast1.2333/attack-enter.4667/attack-idle.5/end.3333s full source. Air cast1.2667 and blink source exist but not selected. Attack is repeated enter pulses rather than complete enter→hold→exit channel state machine.

미연결 원본 후보: 80A8A8B4 cast_blink; blink_cast; warlock_stormcaller_lightning_blink_cast (0.600000s); 80A8A8C6 lightning_enter_air; warlock_lightning_enter_air (1.266667s); 80A8A8DD warlock_lightning_cast_idle; lightning_cast_idle; warlock_stormcaller_lightning_attack_idle (0.166667s); 80A8A8D9 warlock_lightning_cast_exit; lightning_cast_exit; warlock_stormcaller_lightning_attack_exit (0.333333s); 80A8A8DC lightning_cast_enter; warlock_lightning_cast_enter; warlock_stormcaller_lightning_attack_enter (0.466667s)

Native: Shift+F; wait1.5s; repeated left click for2s to sustain channel; release and observe end; move; repeat falling activation. 조건: Ground and falling; owned target within10blocks. 최소 19s. 장착은 직업→속성→`/guardian equip destiny:warlock/arc_super` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 여명 — `destiny:warlock/solar_super`

Runtime: `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockSuper.java`. 분류: **P2_air_source_unused**. 설정: `{"duration_ticks":480,"attack_interval_ticks":22,"projectile_life_ticks":60,"projectile_speed":1.8,"radius":2.5,"damage":12,"attack_contact_ticks":8,"cast_ticks":32,"attack_duration_ticks":21}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.566667 | 80A8A921 / 1.5666666666666667 | full source span matched; pinned existing timing-manifest |
| attack | 1.033333 | 80A8A960 / 1.0333333333333334 | full source span matched; pinned existing timing-manifest |
| idle | 0.733333 | unresolved / None | unresolved/no single motion source; pinned existing timing-manifest |
| move | 0.733333 | unresolved / None | unresolved/no single motion source; pinned existing timing-manifest |
| air | 2.000000 | unresolved / None | unresolved/no single motion source; pinned existing timing-manifest |

Ground cast1.5667s + event-linked slash1.0333s are pinned source; source air cast exists but not installed/selected. Idle/move use generic sword-catch Replacement source, not confirmed Daybreak ready; air lower body uses generic glide. Slash2 source reviewed previously but not selected.

미연결 원본 후보: 80A8A96C warlock_dawnblade_dodge_back_air; dodge_back_air_warlock (0.500000s); 80A8A968 warlock_dawnblade_dodge_front_air; dodge_front_air_warlock (0.500000s); 80A8A96A dodge_left_air_warlock; warlock_dawnblade_dodge_left_air (0.500000s); 80A8A969 dodge_right_air_warlock; warlock_dawnblade_dodge_right_air (0.500000s); 80A8A973 warlock_archangel_cast_air; cast_archangel_air (1.566667s); 80A8A98D dodge_back_air_archangel (0.500000s); 80A8A990 dodge_front_air_archangel (0.500000s); 80A8A98F dodge_left_air_archangel (0.500000s); 80A8A991 dodge_right_air_archangel (0.500000s)

Native: Shift+F; wait1.8s; left click x2 at1.3s gaps; walk; jump/glide and click; repeat air activation; observe sword/camera recovery. 조건: Ground and falling/glide with safe floor. 최소 27s. 장착은 직업→속성→`/guardian equip destiny:warlock/solar_super` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 신성 폭탄 — `destiny:warlock/void_super`

Runtime: `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockSuper.java`. 분류: **P2_air_source_unused**. 설정: `{"projectile_life_ticks":60,"projectile_speed":0.9,"radius":4,"damage":24,"attack_duration_ticks":26,"attack_contact_ticks":14,"vortex_duration_ticks":200,"vortex_delay_ticks":9,"vortex_pulse_ticks":10,"vortex_damage":2}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| attack | 1.300000 | 80A8AD80 / 1.3 | full source span matched; pinned existing timing-manifest |

Source ground cast1.3s occupies _attack, auto-selected on first tick; _start/_idle absent intentionally. Source air AD81 also1.3s but not installed/selected. Release15ticks (14+entry1); visual duration27ticks. Common end swing fallback.

미연결 원본 후보: 80A8AD81 warlock_voidwalker_novabomb_cast_air; warlock_novabomb_air; novabomb_air (1.300000s); 80A8AD82 novabomb_spread; warlock_novabomb_spread (1.300000s); 80A8AD87 novabomb_spread_air; warlock_novabomb_spread_air (1.300000s)

Native: Shift+F automatic Nova; no click; observe release and complete follow-through until projectile impact. Repeat falling. 조건: Ground + falling; clear target within projectile lifetime. 최소 6s. 장착은 직업→속성→`/guardian equip destiny:warlock/void_super` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 빛의 샘 — `destiny:warlock/well_of_radiance`

Runtime: `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockExpandedSupers.java`. 분류: **P2_native_pending**. 설정: `{"duration_ticks":600,"radius":5,"height":2.5,"heal_interval_ticks":5,"heal":2,"weapon_multiplier":1.25,"air_timeout_ticks":160}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 1.766667 | 80A8AAC6 / 1.7666666666666666 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| start_air | 0.566667 | 80A8AACA / 0.5666666666666667 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| land | 1.066667 | 80A8AACB / 1.0666666666666667 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |

Complete source ground1.7667/air-enter.5667/land1.0667. Landed sword planted after full landing phase; independent Well remains600ticks, player returns to weapon immediately after planting.

미연결 원본 후보:

Native: Shift+F on floor; observe sword plant/weapon return. Repeat platform fall; observe air-enter, supported landing, sword plant. No attack click. 조건: Ground + falling with solid landing support; field cannot plant midair. 최소 8s. 장착은 직업→속성→`/guardian equip destiny:warlock/well_of_radiance` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 혼돈 범위 — `destiny:warlock/chaos_reach`

Runtime: `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockExpandedSupers.java`. 분류: **P2_native_pending**. 설정: `{"duration_ticks":80,"pulse_ticks":3,"range":24,"damage":3,"beam_width":1.8}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start | 0.733333 | 80A8AABC / 0.7333333333333333 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| idle | 0.066667 | 80A8AAD8 / 0.0 | single original pose extended into hold; not a retimed motion; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| end | 0.400000 | 80A8AADF / 0.4 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |

Complete source enter.7333/end.4; original loop is single frame and product hold.0667. Alternate source exit.8 exists but variant is not proven required. Runtime plays exit before end() cleanup, so do not misclassify the final stop as skipped exit.

미연결 원본 후보: 80A8AB48 warlock_stormcaller_arc_beam_cast_exit; warlock_arc_beam_exit (0.800000s)

Native: Shift+F; aim beam at owned target; no click; observe channel and.4s exit; repeat air activation. 조건: Ground + falling/air;24block beam lane. 최소 6s. 장착은 직업→속성→`/guardian equip destiny:warlock/chaos_reach` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

### 신성 차원 — `destiny:warlock/nova_warp`

Runtime: `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockExpandedSupers.java`. 분류: **P1_source_attack_unused**. 설정: `{"duration_ticks":490,"charge_ticks":12,"radius":4.4,"damage":16,"blink_range":4,"blink_interval_ticks":10,"burst_recovery_ticks":6}`.

| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |
|---|---:|---|---|
| start_air | 2.033333 | 80A8A9A2 / 2.033333333333333 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| start | 2.033333 | 80A8A9AE / 2.033333333333333 | full source span matched; semantic-name + exact-length candidate; per-clip W230 provenance not found |
| idle | 0.800000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| move | 0.800000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| air | 0.800000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |
| attack | 0.600000 | unresolved / None | unresolved/no single motion source; authored_or_unpinned |

Ground/air cast2.0333s exist. Product burst attack.6s and idle/move/air.8s are authored. Original charge-exit A99D1.2667s and single-frame charge-idle A99C are unused. Replacing visual must retain gameplay charge12/recovery6 and damage epoch semantics until explicitly revised.

미연결 원본 후보: 80A8A99C warlock_voidwalker_novapulse_charge_idle (0.000000s); 80A8A99D nova_pulse_charge_exit; warlock_nova_pulse_charge_exit; warlock_voidwalker_novapulse_charge_exit (1.266667s); 80A8AAF5 warlock_voidwalker_novapulse_cast_enter (2.033333s)

Native: Shift+F; wait2.3s; left click to charge/burst; wait1.2s; Shift+left click blink; walk; repeat falling activation/burst. Observe burst recovery + expiry. 조건: Ground + falling; safe unobstructed blink landing. 최소 28s. 장착은 직업→속성→`/guardian equip destiny:warlock/nova_warp` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다.

## 공용 fallback과 다음 수정 배정

- `w229_`/`w230_` missing clip은 Hunter/Steve 클립으로 대체되지 않는다. 다만 ClassAbilityEffects의 missing attack/end는 vanilla WHACK4tick이다. 별도 end가 없는 단발 cast를 원본 end 완료라고 기록하지 않는다.
- Hunter base의 current→legacy H15→Steve 탐색은 회복 경로이며 원본 fidelity의 근거가 아니다. Storm’s Edge 추가 throw는 missing attack 때문에 start를 다시 선택한다.
- Chaos Reach는 tickChaos에서 먼저 end를 재생하고 exit 길이만큼 기다린다. 최종 end()의 stop만 보고 exit 누락이라고 판단하면 잘못이다.
- Shadowshot 우선 제안: 새 named source overlay/generator + HunterSuper ground/air 선택 + HunterModelAssets 설치. 원본 표시1.3초와 기존7tick release를 분리하고 bow/nock 접촉을 native로 확인한다.
- Nova Warp 우선 제안: 새 charge-idle/charge-exit source overlay/generator + ClassSuperModelAssets 설치 + WarlockExpandedSupers 시각 phase mapping. source1.267초를 gameplay charge12/recovery6에 무조건 대입하지 않는다.
- Hammer/Sentinel/Daybreak/Stormtrance/NovaBomb air selector는 다음 배치 후보. 새로운 art clip과 정확한 phase/출처를 함께 반환한다.
- Golden Gun, Maul attack, Fists light는 이번 원본에서 확인되지 않은 범위다. 원본 확보 또는 명시적 approximation 승인으로 분리하며 임의 cast 재사용을 original attack으로 부르지 않는다.

## 검사 경계

19개 ID 중복 없음, 현재 source/resource JSON 파싱 및 클립 길이 대조, 입력 시나리오 생성만 수행했다. 새 native QA·Blender 평가·렌더·모션 수락은 수행하지 않았다. main/prod/asset 변경 없음. 전체 원본 tag·event·hash와 실제 clip 목록은 source-catalog.json에 보관했다.
