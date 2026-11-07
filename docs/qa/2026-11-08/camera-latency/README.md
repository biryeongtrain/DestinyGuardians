# W345 camera / owner model separation

## Defect paths

- CameraViews sends a client-only PlayerPosition at the view position. A BetterModel limb riding that local player follows the view rather than the real stage actor. The old intro relay was created only during the later audience snapshot, after the initial tracker spawn/show could already be submitted.
- SuperCamera previously installed owner visibility after switching the camera and left limb displays attached to the local player/fake-player mount chain.
- BetterModel 3.5.1 schedules vanilla-body hiding from the outbound spawn-success callback. This is not a client-render acknowledgement and runs on Netty, outside CameraViews.sending's ThreadLocal. A separate later hide is not atomic with the initial model snapshot. Exact dependency bytecode was inspected locally. TCP packet reordering is not claimed.

## Change

A session-owned OwnerModelCarrier separates owner model passengers from the local player in both paths. Intro anchors stay fixed at the stage; super anchors follow authoritative body position with 2-tick native interpolation. The relay is installed from the tracker initializer or before the super camera switch. At the first model add/mount, the same outgoing bundle creates the anchor and hides the vanilla body before submitting the model. Later own flags retain invisibility while preserving other bits. World, real passenger graph and other viewers are unchanged. HUD/foreign riders remain on their original vehicle. Closing removes only this handler/anchor and submits actual current flags after handler removal.

## Evidence status

Targeted JUnit: 35 passing (6 new backlog/flags/equipment/respawn/cleanup tests, 8 existing passenger relay tests, 13 camera math tests, 8 presentation/facing tests). These inspect actual production packet rewrites, including an EmbeddedChannel whose writes are held until explicitly flushed; they do not establish native rendering by themselves.

Baseline native QA used an isolated loopback TCP proxy adding 50 ms per direction (100 ms added RTT), no GCB client, background input explicitly authorized in the conversation. Native super input completed and released. The reported misplaced-model symptom was not consistently reproduced in the baseline sample; the sampled active Arc model was visible at the body. This is therefore not claimed as an exact before/after reproduction of the user's original connection.

Full Gradle suite: 2,800 tests, 22 failures (see full-test-result.json). Failures include absent historical audio source files and historical motion/asset hash assertions. No full-suite pass is claimed. The owned packet tests passed in that run. A separate targeted test + jar Gradle invocation succeeded; the final targeted rerun includes the added armor regression.

Actual SuperCamera world tests: 12/12 passed. The initial attempt disabled AutoHost but left the profile-graph readiness gate enabled, so it waited before fixture allocation and was deliberately terminated (143). The rerun used destiny.weapon.legacyPixelArms=true only to bypass that unrelated 1P readiness gate. BetterModel limb models were still loaded. Synthetic players have no real BetterModel Netty channel; warnings were emitted and these results prove ownership/physics/release behavior, not native carrier rendering. Native QA below uses the normal full resource pack and no legacy-pixel-arm property.

Fixed client: the packaged candidate ran in the normal full-pack runtime, without GCB or legacy pixel arms. The isolated TCP proxy added 100 ms RTT for the first native Arc cast and 200 ms RTT for a second native cast, forward movement, left/right click input, the real Devils Lair briefing cast, normal intro completion, and activity leave. This is added transport delay, not a measured real Internet ping. In the 200 ms combat sample the client body moved from z=0.5 to z=12.3179 while the separate camera stayed behind it; the model remained at the body. During the intro the client local player was at the view position while the authored actor stayed at the stage, with no extra ordinary body seen there. The final perspective API check showed the ordinary player and Diamond Helmet again, cameraIsPlayer=true, vehicleId=-1. Inputs finished with leaseActive=false, heldKeys=[], pendingSteps=0 and neutral native input. The temporary helmet was removed and perspective reset before shutdown.

These are actual PNG and native client-input checks for the owner view. Other observers, GCB client prediction and all super variants were not individually verified. No speaker or Internet jitter/loss acceptance is claimed. The first move-only native sample occurred after the first cast expired and is not counted as super movement evidence; the combined 200 ms sequence provides that evidence. The world tests do not establish carrier rendering because their synthetic connections lack BetterModel's real Netty handler.

Native logs contain no model/carrier failure or unknown-entity warning. The offline development account emitted the usual Realms token warning; Realms was not used. The original high-ping failure was not consistently reproduced in the baseline, so this fixes the identified ordering/attachment paths without claiming an exact original-network reproduction.


## Distribution and production cache

The genuine Gradle jar contains the current compiled SuperCamera, PlayerAnimations and OwnerModelCarrier classes (checked byte-for-byte). The final targeted test run passed 35/35 and final camera world rerun passed 12/12. The full-suite result remains 22 failures and is preserved separately.

Normal production cold boot generated and saved the matching cache in 111.97 s. The warm boot restored in 1,537 ms, was ready in 14.13 s, did not regenerate the resource pack, retained the exact inner SHA-1, and exited 0. The exported server cache bundle is 203,719,427 bytes; its inner client pack is 191,661,837 bytes, under 250,000,000. JAR and bundle paths/hashes are in build.json and prebuilt-pack.json. Extract the companion bundle at the server root before startup. Compatibility mismatches intentionally regenerate once.
