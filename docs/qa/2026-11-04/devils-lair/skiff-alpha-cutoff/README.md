# Skiff emission alpha cutoff — native review

Isolated Minecraft 26.3 observation; no production model promoted.

Both item and entity translucent pipelines use `ALPHA_CUTOUT=0.1` (see retained javap output). The previous straight-alpha conversion placed most low-energy emission samples below that cutoff. The candidate raises nonzero alpha to 26/255 and compensates RGB in linear light. Point-sample surviving support increases from 7,545 to 48,303 texels. Geometry, rig and hull stay unchanged; this does not guarantee survival through filtering or mipmapping.

Three targeted offline tests pass. `native-day-clear.png` and `native-night.png` are actual static-fixture framebuffer captures. `native-day.png` is the initial rainy capture. The beam is now visible, but remains faint and gray/brown in daylight and weak orange at night. Hull stippling, gaps and apparent detached fragments persist. **Visual fidelity is not accepted.** Straight-alpha compositing still attenuates the background and is not source additive shading.

The client loaded an owned local pack routing the two candidate sprites to the blocks atlas after shared item-atlas overflow. This proves only that QA workaround; production atlas routing, animated flight, collision/lifecycle integration and performance acceptance remain unimplemented or unverified.

Cleanup at approximately 03:55 KST: debug model cleared, temporary nine-block platform removed, time restored to noon; owned client and server stopped. Native logs archived here. The installed candidate was hash-checked against `/tmp/devils-skiff-cutoff-20261104/dl_skiff_candidate.bbmodel` before removal. Owned local atlas pack removed and `options.before-skiff-cutoff.txt` restored. The old baseline player destination had no supporting floor: the player subsequently fell and entered down state. Recover the QA account at a verified standable position on the next launch; do not reuse that destination blindly.

The bounded master awake coordinator (caffeinate PID 69688, expiration 2026-11-04 14:27 KST) remains active for subsequent QA and restart gaps. Its receipt now records stopped runtime handles.
