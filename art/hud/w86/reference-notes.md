# W86 — incoming-damage HUD references

Bounded research-only pass, 2026-10-24 UTC / 2026-10-25 KST. Owned writes: this file, `references/*`, `data/research.json`. Original W85/weapon reference bytes preserved. No production, assets/helper, QA, tests, builds, native game/apps or global MCP control changed/run. No reference images were synthesized or assets generated. Research stopped after the bounded source pass; limitations are retained rather than broadened into a video hunt.

## Shape verdict for the parent / asset worker

**Do not call the authored top-facing smooth curved arc, 320-square bank or bearing rotation D2-exact.** The best actual inspected still supports a **compact, solid red/orange tapered wedge near the central aim area**, with a **separate broad peripheral red warning**. It does not establish a long thin arc, full ring, screen-edge-only arrow or the exact source-bearing convention.

Open **`references/gameplay-yZnltegf48g-maxres3.jpg`** (1280×720, actual fetched numbered video still). The compact red/orange wedge is approximately x51% / y62% in this single image, below the central aim area. These are rough visual image coordinates, **not** engine angles or a fixed layout radius. A red **X** higher in the aim area is the outgoing hitmarker, not the directional damage marker. Enemy labels/bars, objective diamonds and radar sectors are also not the incoming indicator. The marker overlaps a target, so confidence in its exact isolated silhouette is limited; no clean alpha mask or controlled bearing sweep was obtained.

The authored rotating arc may be a defensible local approximation, but its smooth curvature, size, angular sector and top-facing convention remain local. This evidence does **not** prove that an edge-only replacement is correct either. Do not invent precise geometry from a still.

## Periphery and health/shield comparison

| Actual reference | Direct visual observation | What it does not prove |
|---|---|---|
| `gameplay-yZnltegf48g-maxres3.jpg` | Short **red** top-center remaining-bar segment; strong translucent **red/maroon** outer-screen wash with bright pink/white rippling distortion and dark irregular edge patches; central gameplay remains readable | Exact activation HP/percentage, timing, pulse curve, shield-only eligibility or contribution of every simultaneous effect |
| `gameplay-yZnltegf48g-maxres2.jpg` | Substantially filled **white** top-center bar; much milder dark/red peripheral tint | A controlled shield-only hit comparison, or that red effects are absent while shields remain |
| `gameplay-zXJvpfdmWS0-maxres2.jpg` | Historical depleted-looking bar and maroon/red edge/corner vignette; central gun and target readable | Current2026 exact look or numeric threshold |

The broad warning reads as a **soft peripheral vignette/wash**, not merely a hard red rectangle or a new icon beside the health bar. The severe still additionally contains large rippling/high-contrast distortion. A server-side resource-pack approximation need not reproduce all of that distortion, but omission/strength is a local art decision, not a measured match.

**Do not copy the pale rectangle behind the bar in maxres3 as native HUD styling:** it appears to be the creator's bar highlight/edit. The ordinary top-center bar is visible without that rectangle in maxres2.

The 2025 `health-stat-comparison-thumbnail-raw.jpg` is a **creator-edited montage**, not one continuous full-screen gameplay frame. It provides a clear white-versus-red bar-color comparison and dark/red tint context. Its “100 Health” through “200 Health” labels refer to **Health stat**, not remaining HP, and must not be converted into an activation threshold. It is not evidence for native placement of eleven bars.

**Shield-only versus critical is not fully isolated here.** The white-bar and short-red-bar moments support qualitatively different presentations, but these are different gameplay moments with combat underway. Do not claim a strict shield-break gate, absence of red tint on shield hits, a 30% Destiny threshold, or that every rippling effect is exclusively critical health.

## Actual footage and timestamps

- [CoolGuy — The Bizarre way Flinch works in Destiny 2](https://www.youtube.com/watch?v=zXJvpfdmWS0), published **2018-10-11**. W85 source page and M0/M1 storyboard JPEGs reused byte-identically. Numbered `hq2` / `maxres2` show actual historical gameplay; `hq1` is a character menu and `hq3` an end card, explicitly not gameplay evidence.
- [CoolGuy — Destiny 2: The new Flinch Resistance system is crazy and you NEED to do this!](https://www.youtube.com/watch?v=yZnltegf48g), published **2022-06-17**. W85 source page and M0/M1 reused; M2–M5 and numbered stills fetched within this pass. `maxres2` is the white-bar comparison; `maxres3` is the strongest red-periphery/short-red-bar reference. `hq1` is a sponsor card, not gameplay.
- [Oftly — Destiny 2: 100-200 Health Stat Comparison](https://www.youtube.com/watch?v=IeBlEb6HocY), published **2025-08-20**. Raw page plus edited maxres thumbnail retained. The page links the short [PvE compared to PvP](https://www.youtube.com/watch?v=x346OB_R96g), same date; its metadata is retained as context only, not an unseen-frame claim.

**Exact source-frame timestamps for numbered YouTube stills are unavailable and recorded as null.** Do not assume `maxres2` is exactly halfway through the video or claim a frame timestamp from its filename. Their actual retrieval URL, retrievedAt and SHA256 are pinned.

Timestamped sparse storyboard examples: direction video M1 tile1 ≈ **0:52**; resistance M4 tile7 ≈ **8:55**, M5 tile6 ≈ **10:55**, M5 tile13 ≈ **11:30**. Tile index is zero-based, row-major. Formula: `(sheetIndex * 25 + tileIndex) * interval`; interval2s for direction,5s for resistance. These samples were visually inspected and show damage/periphery context, but are **not** exact event timing or asserted exact matches for the numbered stills. `visual-observations.json` records all inspected images and qualifications. No complete video/audio stream was downloaded.

## Official-description search result

No specific first-party incoming-direction or critical-periphery specification was established in this bounded pass. The official old guide URL redirected to a New Player Guides index; one guessed old article resolved to Rewards Pass content; another article was introductory class content; some linked pages returned404/403. These raw responses are retained and excluded from HUD mechanics evidence. Search CAPTCHA, wiki404 and failed help API responses likewise do not establish absence of official documentation elsewhere. No threshold, shape or angle is attributed to Bungie prose without a source.

## Explicit local-policy boundaries

Unknown / **null**: exact damage bearing angles, orientation mapping, isolated silhouette, fixed marker radius/pixels, RGB values, fade lifetime, critical HP or fraction, shield-break-only gate, health/shield/absorption damage matrix, vignette onset/recovery/pulse, multi-source capacity and exact current2026 look.

Parent's **four origins**, **one-second life**, **30% HP critical threshold**, and authored rotating arc bank are **explicit local policy**, not Destiny facts. This research neither validates nor overrides those implementation choices. Keep direction cue and health warning conceptually separate: a hit/source cue is not itself proof of ongoing critical state, and a critical-looking vignette is not evidence of source bearing.

## Provenance / immutable reuse

`references/reuse-provenance.json` records every byte-identical W85 copy, source path, original source URL/retrievedAt where applicable, copiedAt, bytes and SHA256. `gameplay-evidence.json` is the unchanged **W85** metadata extraction; W86-specific findings are separately in `visual-observations.json` and `video-identities-extracted.json`.

`references/retrievals.json` records each new actual URL, retrievedAt, bytes and SHA256, plus origin URL for Jina-rendered responses. HTTP200 does not make an origin403/404, CAPTCHA, wrong-topic page or sponsor card gameplay evidence. Failed requests retain generated exception text, labelled as failure records rather than fabricated raw HTTP bodies. `references/provenance.json` inventories **only this sidecar's owned files**, not the separate worker's assets/helper. No original weapon reference was edited.
