# W179 Mindbender's Ambition (Adept) insert presentation

## Observed same-weapon gameplay

[PureChiLL — Destiny 2: God Roll Mindbenders Ambition + Mida Multi-Tool!](https://www.youtube.com/watch?v=w6nyc_h7h2A), uploaded 2019-04-13. Actual video format136, 1280×720, 30fps, was downloaded and decoded. The weapon page at **10.000s / frame300** explicitly reads **MINDBENDER'S AMBITION**, with the familiar long barrel, warm bone fore-end/stock and hooked bone grip. The name has **no Adept suffix**: this verifies the standard weapon, not an Adept roll, ornament or exact default dye. It provides the same-weapon motion comparison only. Local canonical Adept geometry/paint remains authoritative.

Inspected full source frames in `storyboard.png` pair actual pixels above with authored emitted-JSON reconstruction below. Individual full PNGs, unmodified video/metadata, scan sheets and extraction logs stay outside product at `/private/tmp/w179-mindbender-s-ambition-adept-report`. Exact source frame indices and PNG/video SHA-256 values are also in `manifest.json.reference`.

| Source time / zero-based frame | Observed |
| --- | --- |
| 10.000 / 300 | Weapon identity and recognizable bone/metal silhouette. |
| 93.200 / 2796 | Post-shot ready, before lift. |
| 93.300 / 2799 | Receiver lifts/cants; open support hand; HUD0. |
| 93.400 / 2802 | Muzzle-up held receiver, hand withdraws. |
| 93.600 / 2808 | Gun stays raised while the support hand drops below frame. |
| 93.800 / 2814 | Red/brass cartridge visible in rising support hand below receiver; HUD0. |
| 94.000 / 2820 | HUD1 after first insert; receiver stays held. |
| 94.100 / 2823 | Forearm passes under receiver, held cant persists. |
| 94.200 / 2826 | Camera turns, hand withdraws; not a return to HIP. |
| 94.500 / 2835 | Second hand approach under receiver; HUD1. |
| 94.700 / 2841 | HUD2; hand withdraws and transition begins. |
| 95.200 / 2856 | Native source has transitioned to iron-sight ADS. |

These are discrete observed frames, not measured bones, hand IK or complete chamber motion. Gunfire/elimination overlays, camera pan and source perks prevent reading official reload duration from these pairs. The source's glowing orange runes and red shell are not copied into the canonical matte Adept atlas.

## Authored asset and underside inspection

The 104-solid W147 effective canonical surface is copied **exactly** into the new body parent: same long open barrel, octagonal muzzle, thick bone fore-end/stock, hooked bone grip, open guard/sight notch, silver rune collars, authored relief/face UVs, textures and display endpoints. Original canonical models/items/texture/data/audio are untouched. A separate cartridge adds12 output cuboids; there are no triangles/adapters, so maximum simultaneous assembled count is **104+12=116**, below1,000. Alternative full/body representations are not double-counted.

W178 supplies the rigid matrix composition pattern and item schema only. Mindbender has its own grip pivot `(8,8.70,8.18)`, held rotation `(22,-11,-36)` and force/return curves. Initial establishes that cant once, then approaches with one cartridge. Loop starts and finishes at exactly the same held body pose with less than0.71° force deflection; it never repeats the initial HIP lift. The return is an authored six-tick neutral recovery, hidden cartridge throughout, not the source's ADS motion. It supplies no ammo and adds no gameplay block. Existing5mag /16tick one-paid-shell `WeaponCycle` inserts remain authoritative; no timing/audio/data changes.

Underside close-ups in `comparison.png` inspect the actual emitted JSON at approach/contact/seat. Canonical `loading_tray` occupies X7.59..8.41, Y10.49..10.69, Z3.795..7.045; `action_solid` occupies X7.415..8.585, Y10.68..12.30, Z1.60..9.00. New shell anchor `(8,10.04,4.45)` is forward of guard: its **long axis is Z**, crimp toward muzzle **-Z**, metal head/rim toward stock **+Z**. At contact its top is below the tray, not a vertical cartridge crossing the receiver sideways. Its authored occluded continuation translates up/forward to `(8,11.00,2.55)`, entirely inside the existing solid action and forward of tray/guard; only there does it disappear. Canonical closed tray is preserved: this does not claim a newly modeled open chamber or extracted internal tube path.

One cartridge is twelve intersecting, positive-volume cuboids forming connected octagonal case/head/rim sections. It uses existing clean graphite tray/silver collar atlas texels, not the source's red paint or a new texture. Visibility is full-sized during approach/contact; zero-sized only outside visibility windows and after seating. All phase seams, HIP endpoints, return, ADS/inspect and non-FP hide it. Both FP contexts and native/twohand grip carriers share the same source-local motion. Non-FP contexts and ADS/inspect dispatch to the exact canonical item graph. Body initial0/return1 retain exact accepted display dictionaries.

## Verification and handoff boundary

Focused Python tests cover canonical preservation/element budget, cartridge axis/contact/seat, held seams/visibility, both hand/grip transforms, graph selectors/fallbacks, evidence provenance and owned path/hash contract. Standalone Java25 uses actual Minecraft26.3 representative CuboidModel parsing (both parents and selected children), a malformed negative control, full item codec, exact canonical fallback checks and independent representative JOML transformed points. These are offline asset tests, with no assertion of master runtime admission or routing.

Master owns shared runtime/routing/registries, native client/server, real hands, audio listening, cancellation/death/disconnect and display/performance acceptance. **No native success, hand IK, extracted animation, new third-person reload or game-runtime execution is claimed here.**

Regenerate with Pillow/NumPy Python: `scripts/generate_insert_w179_mindbender_s_ambition_adept.py --reference-dir /private/tmp/w179-mindbender-s-ambition-adept-report`; add `--verify` for deterministic byte comparison. Reference-dir must contain `reference-frames.json` and the twelve hashed full frames. The only generated product evidence is this four-file art folder; raw evidence remains external.

Retained acquisition failures: web connector returned an empty error; the extra Adept search produced no entries; initial yt-dlp muxed-format selection was unavailable. A later two-format overlap used the same temporary destination; **neither that file nor its metadata is evidence**. A fresh sequential format136 download to distinct `source720.mp4` / `source720.info.json` is the sole source used above, hashed and decoded independently. All logs and failed/transient files remain in the report directory; no baseline cleanup was performed.
