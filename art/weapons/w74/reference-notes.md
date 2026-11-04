# W74 — normal-bow perfect-window clock

## Established source vs. implementation policy

- [Bungie Update 6.2.0](https://www.bungie.net/7/en/News/article/51707), 2022-08-23: lightweight perfect-draw endpoints became 0.50s at low stability and 0.80s at high stability. This is historical official corroboration, not a new measurement of the current engine or either selected roll.
- [Oracle `calc_perfect_draw`](https://github.com/d2foundry/oracle_engine/blob/dcd0c7d302b056ffbb532edcb711d724a17ca8c1/src/weapons/stat_calc.rs): pinned community-calculator linear interpolation. The local W46 source and [`build.rs`](https://github.com/d2foundry/oracle_engine/blob/dcd0c7d302b056ffbb532edcb711d724a17ca8c1/build.rs) map **905 lightweight**, **906 precision**. Oracle is primary evidence of its own calculation, not official Bungie engine code.
- Base stability uses exact existing W40/W46 official item hashes and stat `155624089` (`Stability`). No inferred exotic/Oathkeeper perk or unsupported random-roll stat bonus is granted.

| Selected exact item | Frame | Stability | Community formula | Raw window | Server window |
|---|---|---:|---|---:|---:|
| Biting Winds 1621657423 | Precision |43|0.3 + S/400 seconds|407,500µs|9 ticks|
| Whispering Slab 211938782 | Lightweight |53|0.5 + 3S/1000 seconds|659,000µs|14 ticks|

The offline [generator](../../../scripts/extract_bow_window_w74.py) checks existing source formula/frame strings and official stat agreement, then emits the [server data](../../../src/main/resources/destiny/weapons/w74-bow-window.json) and [source pins](references/perfect-window.json). It does not contact a live service. Existing Oracle licenses stay bundled. Integer microseconds avoid floating ceil errors; ceiling to 20TPS adds 42.5ms and 41ms respectively. The half-open interval starts at the **accepted** full-draw tick: `0 <= age < windowTicks`. Tick rounding and accepted-draw snapshot are explicit server policies.

## Feedback only, not completed fatigue mechanics

Runtime exposes IDLE / DRAWING / PERFECT / LATE from the owned native use session without writing state or NBT. The same W73 accepted duration drives projectile power, string pose, and this clock. Base 14/12-tick draws and the eligible 9-tick Tempo draw do not get separate drifting timers. Tempo changes draw duration, not this base-stability window. Buffered input ages only after actual nocking finishes and a draw is accepted.

Reticle outer frame shrinks up to35%, turns gold during the window, then returns to rested size with a muted amber warning. This is **authored informational feedback**, not extracted Destiny reticle art/animation or a measurement of its accuracy cone. The central dot stays fixed and white. Both existing cached HUD entities are reused; no new client assets/audio/models.

**LATE does not apply a new damage/accuracy penalty, automatically fire, spend ammunition or alter nock timing.** Existing full-draw arrow profile still applies after the window. Do not report full perfect-draw/fatigue simulation complete. The [bounded independent fatigue investigation](fatigue-notes.md) found no sufficiently grounded selected-roll max-hold or late-decay curve. Historical four-second reports are retained as leads, not implementation values.

Main's private successful fullarticle capture is `run/private-sources/w74/perfect-window-web-capture.json`; another retrieval timed out. The independent fatigue worker did not see the main's fullarticle passage and correctly limits its own retrieval claim. These are different captures, not contradictory source verification.

## Evidence limits

Actual server use/clock/HUD-object tests are not native-client input, framebuffer, sound listening or FPS evidence. No further native Minecraft launch was performed after the approved isolated W62 SDL diagnostic. Normal QA deployment/options/profiles/player files and user Blockbench/Blender projects remain untouched. [W74 QA](../../../docs/qa/2026-10-24/w74/README.md) and [design89](../../../docs/design/89_W74_활_최적_발사창_HUD.md) track the remaining work.
