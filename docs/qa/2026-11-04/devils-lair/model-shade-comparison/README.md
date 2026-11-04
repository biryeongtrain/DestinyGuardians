# Native Thrall shade comparison — 2026-11-04

Isolated QA only. 17 generated vanilla bone models, 1,954 elements: changed only `shade:false`. Geometry, UVs, textures and production assets unchanged. AutoHost additional local resource pack was loaded after the normal pack, confirmed by the client ResourceManager log and downloaded SHA1. All 17 item routes and original model hashes matched after regeneration.

Actual framebuffers were inspected at the same player position (1004.5,100,1005), yaw 0/pitch 10, with time set to noon. `qa_static` does not yield an identical frozen pose: the default pose visibly varies, so this is a qualitative comparison, not a pixel-matched experiment. Clouds also differ.

Result: severe stippling and horizontal surface artifacts remain with directional face shade disabled. This does not isolate the underlying geometry/atlas cause, nor rule out a minor shade contribution. No production change accepted. Screenshots show the actual native render, not an offline preview.

Cleanup: exact isolated AutoHost config restored from backup; owned client/server and local HTTP server stopped. Bounded master sleep-prevention assertion is retained for subsequent QA. No other profiles or user files changed.
