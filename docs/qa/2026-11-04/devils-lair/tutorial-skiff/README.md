# Tutorial skiff reuse — 2026-11-04

User requested the original tutorial transport instead of the ripped skiff. The strike now uses unchanged `rg_skiff` (54 elements, 1024 atlas), tutorial full brightness, idle and drop clips. Shared transport owns bounded arrival/departure translation; tutorial arrive/depart skeletal clips are deliberately not played because they travel outside the checked corridor. The hull includes idle sway and opening clamps.

The retired bundled model and atlas routes are removed. An unchanged managed installed copy is archived outside the BetterModel scan directory; user edits and symlinks are preserved. Actual isolated startup archived the old managed model successfully.

## Verification

- Actual Fabric NBT route gate passed for RY/BL/SP with the tutorial hull; see nbt-routes.xml.
- Real Gradle JAR produced. Full JUnit run: 2587 tests, 16 identical baseline failures, no new failures. See regression.json. This is not a green whole-project gate.
- Actual Minecraft framebuffer sequence: arrival, delivery beam, departure, and empty sky afterward. RY live admission reached 24/24. Screenshots are from a command-positioned resistant observer at RY.C2, not proof of native traversal or difficulty acceptance.
- Distributed pack: 187755174 bytes (187.8 MB); no dl_skiff entries. See pack.json.
- No native input lease acquired. Session leave and resistance cleanup issued; owned client/server stopped afterward. Master bounded awake assertion retained for subsequent work.

Full-strike route, wipe/reconnect acceptance and human difficulty testing remain separate pending work. This batch accepts the requested model replacement only.
