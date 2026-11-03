# Full RY → RF → BL → SP progression in the real runtime — 2026-11-04

Two consecutive isolated runs (`run-a`, `run-b`) reached `COMPLETE` through the real `DevilsSession`, director, actor spawning, transport, music, objectives and presentation, with **no checkpoint reset, session failure or exception**. Both runs took about 365 seconds and passed every planned phase in order: BRIEFING, RY_APPROACH, RY_CLEAR, RF_ENTRY, RF_DEVICE, RF_DEFENSE1–3 with both intermissions, RF_CLEAR, BL_BATTLE (Walker + two Brigs), BL_CLEAR, SP_GUARD, SP_INTRO, SP_DAMAGE1, SP_SHIELD1, SP_DAMAGE2, SP_SHIELD2, SP_DAMAGE3, COMPLETE. The session then returned the player to the tower after the 30 second completion window.

## What is real and what is a fixture

- Real: server, single Vision client (DevilsQA), resource pack, zone NBT maps, spawn search, reinforcement transport, director gating (shield phases rejected damage until three Servitors died; Sepiks guard/intro rejected damage), zone gathering at exit anchors, completion and return.
- Native client input: the RF device was activated by the client's own held sneak through the Vision control lease (device-*.json, lease released, keys neutral).
- Fixture: enemy kills are server `/damage ... by DevilsQA` commands every 3 s; zone exits use one command teleport per clear phase; the player is kept alive with Resistance V and Regeneration. This proves progression wiring, not combat difficulty, traversal, AI quality or fight length.

## Findings

- An earlier attempt ended correctly as "party left" because the fixture teleport lacked `at @s` and moved the player to the overworld. A second attempt's RF/BL/SP wipes came from the fixture repeating a teleport into the next zone outside its bounds and from expired protection. Both were fixture errors; the product reacted as designed (fall → down → wipe → checkpoint reset at the right zone).
- The Sepiks intro plays as a letterboxed camera on the boss for about 4 s (sepiks-intro-camera.png, run-b sheet frames 6–10). Frame 6 briefly shows unloaded black chunk faces at the camera position; they fill in within one frame. The server logs "moved too quickly" while the camera owns the view because the hidden body is held at its anchor; no rubber-band is visible in captured frames.

## Not covered

Native combat with three classes, human difficulty/fight length, disconnect/reconnect and wipe-at-every-encounter acceptance, tick p95 / client FPS measurement, and speaker listening remain open plan acceptance items.
