# W227 display equipment HUD delta

Root: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-seventh_seraph_officer_revolver`

The initial three-file delivery was integrated by master. The current delta.json contains only the sequential HUD follow-up described below; layout and tests remain unchanged. No commits, pushes, builds, test execution, client/server runs, Vision access, shared dependency edits, assets, models, animations, or controller/input edits.

## Sequential HUD-only follow-up

- Original integrated/main HUD SHA-256 (required preimage): `ebb512cc23d5714e1daf4b14ed9372e9171fec984321e55af833971dc1c4167b`.
- Replacement HUD SHA-256: `7e74344b09bd2ae1a0db8f2355d557b5b6a75530d9dc49a8ef4bd796d53c932e`.
- Current delta.json contains only `src/main/java/kim/biryeong/destiny/inventory/WeaponScreenHud.java`, with `baseSha256` recording the exact integration precondition. Do not replace a main HUD whose current hash differs.
- Removed the unconditional ` + " FRAME"` suffix: the existing Card.frame projection already contains the complete source_frame_label (for example, Adaptive Frame), now rendered once as ADAPTIVE FRAME.
- Added modest muted **BASE STATS** label at reference centre **(1440,590)**, 10px glyph size. Frame remains y548, divider y576, first stat row y609, leaving separate vertical bands without moving stat rows or any interactive layout.
- No changes to WeaponScreenLayout.java or WeaponScreenLayoutW227Test.java; original hashes below were rechecked unchanged.
- Source verification: baseline preimage matched exactly, inspected minimal diff, checked one base-stats label, confirmed unchanged frame/rule/stat-row coordinates, checked unchanged layout/test hashes and trailing whitespace. No worker compile/test/native runs.
- Master reports initial targeted source/build and 10 UI pure tests passed. This follow-up still awaits master's compilation/native verification; no new runtime/visual pass claimed.

## Implementation

- `WeaponScreenHud.render(ServerPlayer, WeaponScreenView)` and `remove(ServerPlayer)` use only personal ids beginning `destiny:equipment_w227_`.
- Dark slate full-screen underlay, player identity, CHARACTER/EQUIPMENT header, three equipped category squares, selected-category connector, adjacent 3x3 spare carried grid, purple/gold rarity, actual existing weapon GUI models, inspected details, frame, five real stat values/bars, elemental/ammo labels, live rounds/capacity, optional RPM, page buttons/count, close control, empty cells/categories/details, focused target frame, circular/cross pointer and footer.
- Exact footer controls: Mouse look pointer / WASD navigate / LMB or SPACE equip / RMB or Q close. Open hint: `/destiny inventory` or sneak+Q. No client mod or OS pointer requirement; GCB is not required by this renderer.
- Equipped cards are matched by WeaponSlot, allowing missing categories; choices are treated as the caller's current page of spare carried cards. Grid Card.equipped is supported if supplied. Renderer does not filter, reorder, equip, or modify inventory.
- Weapon previews are disposable `WeaponModels.create(WeaponCatalog.find(id))` stacks with `ItemDisplayContext.GUI`. Geometry uses the existing tintable `destiny:gui/hud/solid` item. No assets added.
- All geometry, previews, text, focus and pointer nodes call `setAboveHand(true)`. Only the full-screen underlay is UNALIGNED for viewport coverage; all interactive content is CENTER-aligned on the reference canvas.
- Typed immutable per-node state lives on the existing DisplayHud node. Identical state skips setters/packets; changed nodes update metadata in a batch, retaining entity identity. Moving pointer geometry retains its item stack. No per-tick respawns. End-of-render cleanup removes previously registered prefix nodes no longer painted, including old preview/empty/detail/message/stat fill nodes. remove() affects only this prefix. No separate UUID/session map.
- Text sizes are reference glyph pixels, converted to display scale using the 0.025 font-unit factor. Labels use centered text, transparent backgrounds, no shadow, and one explicit blank spacer row through the existing public backing-display API. This avoids the library's width-spaces spacer wrapping into several blank rows. Native readability/vertical alignment remains for master visual verification.
- Stat keys accept named projection keys and actual WeaponCharacteristics stat hashes (impact 4043523819, range 1240592695, stability 155624089, handling 943549884, reload speed 4188031367, RPM 4284893193). Missing values show an em dash; bar fill clamps to 0..100 but the label preserves the real value. Magazine uses Card.rounds/capacity directly, including zero and overflow.

## Controller/native cursor geometry

Coordinates are reference pixels on the CENTER-aligned 1920x1080 canvas: screen centre is (960,540), +X right, +Y down. Box.x/y are rectangle CENTRES. No signed-origin conversion is required by the controller. Node 0 initial cursor is **(240,360)**.

Rendering card/button bases, inset edge frames and focused frames all use `WeaponScreenLayout.bounds(node)`; hit testing uses the same immutable Box instances. All edges/corners inclusive, with gaps between distinct controls. Nonfinite input and background/outside points return -1. Invalid bounds throws IllegalArgumentException; navigate sanitizes invalid focus before accessing its source array. Directional nearest neighbour scores forward² + 8*perpendicular², resolves ties by node order, and clamps when no node is in the directional half-plane. Diagonals use dominant axis, horizontal on ties. Empty grid cells and disabled page controls remain navigable; controller handles their no-op activation.

| Node | Control | Center X | Center Y | Width | Height |
| --- | --- | --- | --- | --- | --- |
| 0 | Equipped kinetic | 240 | 360 | 156 | 156 |
| 1 | Equipped energy | 240 | 540 | 156 | 156 |
| 2 | Equipped power | 240 | 720 | 156 | 156 |
| 3 | Carried row 1, column 1 | 540 | 360 | 156 | 156 |
| 4 | Carried row 1, column 2 | 720 | 360 | 156 | 156 |
| 5 | Carried row 1, column 3 | 900 | 360 | 156 | 156 |
| 6 | Carried row 2, column 1 | 540 | 540 | 156 | 156 |
| 7 | Carried row 2, column 2 | 720 | 540 | 156 | 156 |
| 8 | Carried row 2, column 3 | 900 | 540 | 156 | 156 |
| 9 | Carried row 3, column 1 | 540 | 720 | 156 | 156 |
| 10 | Carried row 3, column 2 | 720 | 720 | 156 | 156 |
| 11 | Carried row 3, column 3 | 900 | 720 | 156 | 156 |
| 12 | Previous page | 540 | 860 | 156 | 48 |
| 13 | Next page | 900 | 860 | 156 | 48 |
| 14 | Close | 1740 | 112 | 152 | 52 |

## Source/API verification performed

- Read slot AGENTS.md, /Users/qf/.codex/RTK.md, baseline WeaponScreenView/Card, WeaponCatalog, WeaponModels, WeaponSlot and WeaponCharacteristics, local DisplayHud/ItemDisplayHud/TextDisplayHud API implementations, displayhud shader coordinate/depth rules, tintable solid item/model, and an authored weapon GUI transform. No .codegraph directory exists in this slot.
- Checked every invoked hud method name against the local displayhud source declarations; none missing. Verified GUI factory path, both above-hand paths, shared bounds calls, prefix-only cleanup, absence of respawn/runtime/inventory mutation calls, final newlines and no trailing whitespace.
- Seven JUnit pure layout tests authored: exact native centers and square dimensions; inclusive edges/corners and immediately-outside misses; background/outside/nonfinite hits; grid row-major movement and equipped/grid transitions; all-15-node reachability from every start; deterministic navigation, endpoints, invalid focus and extreme directional values; invalid geometry rejection.
- **Compilation, JUnit execution, centralized gates, client/server and native/Vision visual QA were intentionally NOT RUN. Master owns these checks.** No claim of visual acceptance or runtime pass.

## Hashes

- `src/main/java/kim/biryeong/destiny/inventory/WeaponScreenHud.java` (replacement): `7e74344b09bd2ae1a0db8f2355d557b5b6a75530d9dc49a8ef4bd796d53c932e`
- `src/main/java/kim/biryeong/destiny/inventory/WeaponScreenLayout.java`: `8c445819d076dcf012b1d253d25a946a805fb79fac032d767481340930698101`
- `src/test/java/kim/biryeong/destiny/inventory/WeaponScreenLayoutW227Test.java`: `1b1f7b8337597eb77778257ac319233709f02829d23a0e4b980e483699cadb92`
