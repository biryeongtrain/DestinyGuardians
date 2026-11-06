# Client model-memory optimization — 2026-11-06

The pack now shares unchanged cube geometry between display-only weapon poses instead of baking each pose independently. Animation frames, geometry, textures and sound assets are retained. Actual client checks accepted this memory change with the existing third-person limitation recorded below; this is not full-product QA acceptance.

## Measured result

Isolated Minecraft 26.3 / Java 25 / Apple Silicon QA, tower, same asset set.

| Measurement | Before | After |
| --- | ---: | ---: |
| Java heap limit | 4 GiB | 2 GiB |
| Live Java objects after GC | 3,676,400,600 bytes | 1,253,583,944 bytes |
| BakedQuad count | 39,222,744 | 5,420,653 |
| BakedQuad object bytes | 2,824,037,568 | 390,287,016 |
| Unique referenced model IDs | 98,587 | 9,003 |
| Generated full pack ZIP | 207,643,125 bytes | 177,878,835 bytes |
| macOS physical footprint snapshot | 8.2 GiB (repeat baseline) | 6.0 GiB |
| Peak footprint reported by vmmap | 8.4 GiB (repeat baseline) | 6.2 GiB |

Live heap fell approximately 66%, BakedQuad count 86%, and the pack about 29.8 MB. The optimized client loaded and played with a 2 GiB heap. Heap object bytes are not process memory: the full process still used about 6 GiB, including native/graphics allocations. These are separate-launch snapshots, not repeated steady-state or FPS benchmarks. The repeat baseline had 3,690,506,520 live Java bytes and the identical 39,222,744 BakedQuad count.

The item atlas remains 16384×16384. Texture audits found only about 1.9 million byte-duplicate pixels and 0.28 million exactly reducible repeated pixels; these cannot materially shrink the atlas. Large images contain roughly 51 million pixels outside their alpha bounding boxes, but cropping requires validated UV/animation remapping. No texture resampling or source-art changes were made.

## Implementation and offline validation

- Specialize nested selectors on original weapon items and first-person-hidden held wrappers, eliminating unreachable branches while preserving selected leaves and wrapper metadata.
- Share only parent/display/credit chains rooted at self-contained standard cube models. Each display context uses `inverse(baseDisplay) * poseDisplay * originalLocal`.
- Preserve tint sources, local transforms, all nine display contexts, same-level right-to-left fallback and the NONE fallback. Skip unknown/custom parent/material shapes, singular roots and ancestor matrices.
- Apply before model deduplication and pruning in both profile-arm and legacy generation paths.
- Minecraft 26.3 local bytecode confirms geometry is baked independently of the local item matrix and that rendering applies the model display transform before the local matrix.
- Targeted SharedWeaponGeometryTest, WeaponPackOptimizerTest and ProfileArmAssetsTest: 14 tests passed.
- Selector-only intermediate pack: 254,016 deterministic sampled route comparisons over 882 changed item files passed. This is not an exhaustive proof over every CMD combination.
- Full `./gradlew test build --no-daemon`: **FAILED**, 2,680 tests / 18 failures. Compilation and jar tasks completed. See `full-test-failures.json` for missing historical audio evidence, asset hash/expectation mismatches and WeaponUseTrace expectation. A clean historical baseline full gate was not rerun; the checkout is not certified fully green.

## Actual framebuffer and input review

Screenshots are original framebuffer PNGs, captured with HUD visible and reviewed directly. Native sequences completed and released their leases; controls were neutral afterward. Server commands prepared fixtures separately from native fire/aim input. No speaker/audio acceptance or FPS percentile claim is made.

| Scenario | Result and evidence |
| --- | --- |
| Tower gun, hands and HUD | Preserved in before/after inspection: baseline-tower.png, shared-tower.png |
| SMG ADS | Centered sight, visible geometry/textures: smg-aim-2.png |
| Empty-magazine reload | Removed magazine / return / ammo restored: smg-auto-reload-8.png, smg-auto-reload-19.png; server reload event recorded |
| Bow draw/release | Bow/string/arrow state renders during native draw and release: bow-draw-6.png |
| Sniper ADS | Scope frame and aiming view render: sniper-scope-3.png |
| Shotgun shell reload | Ammo 0 → 4 → 5, insert pose and return: shotgun-cycle-18.png, shotgun-cycle-22.png |
| Sixteen simultaneous item displays | All sixteen shotgun models render: multi16.png; short smoke check, not a performance certification |
| Gear UI | Icons and held preview retained: baseline-inventory.png, shared-inventory.png. Blue/pink offline QA skin exists in both. |
| Native third-person camera | **Existing defect reproduced:** foreground first-person hands/gun remain visible. baseline-shotgun-third.png and shotgun-third-settled.png show the same issue before and after. Not a third-person product-quality pass. |

For the third-person comparison, only the two pre-change pack Java classes were read from HEAD and compiled into a separate temporary class directory; the working source/build output was not reverted. The isolated server generated the original 207,643,125-byte pack again. Its SMG and shotgun both reproduced the foreground overlay. All 28 shader files in the original and optimized pack are byte-identical. This establishes the issue predates this optimization; camera-mode handling remains separate follow-up work.

## Provenance and cleanup

Measurements and exact PNG SHA-256 values are in `measurements.json`. Working pack ZIPs, raw histograms, vmmap reports, native sequence results and runtime logs remain under `/tmp/destiny-memory-qa-20261106/`. The deployable optimized generated pack for this run is `shared-pack.zip` there; the later baseline comparison pack must not be mistaken for the optimized output.

Fixture: `/tmp/destiny-devils-qa-20261103/`, server 25610 / Vision 8102. Original QA weapon and loadout mode were restored; test displays and backup stands removed. Owned client/server and the bounded awake coordinator were stopped. Optimized server launch arguments were restored for the next run. Other user profiles, worlds, worktrees and art tools were untouched. Existing loot work remains separate and uncommitted by this change.
