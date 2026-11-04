# Cinematic audience and enemy-target clocks

## Defect

DevilsSession previously called `director.pause(paused || noTargets)` using `participants()`, which excludes every player hidden by the presentation input lock. During BRIEFING this freezes `DevilsDirector.tickSpeech()`. Normal voice callbacks can directly end the briefing, but an unavailable cue depends on the director's 60-tick fallback, so it could retain the camera/input lock indefinitely. Sepiks intro time also stopped advancing for its camera duration despite the presentation clock advancing.

## Correction

The session now computes readiness without presentation suppression for progress and still computes combat targets with suppression for actors. Both clocks remain suspended for reset placement; without a ready living audience, progress remains paused. The same base readiness predicate feeds allows(), preserving the lock's damage/input exclusion. Audience must also be in the activity world.

## Validation scope

81 scoped JUnit checks pass, including three new policy/director integration tests. The missing-voice briefing remains BRIEFING for 59 active ticks and reaches RY_APPROACH on tick 60 while the policy keeps enemy actors paused. 1,000 ticks without an audience do not consume its fallback; readiness then resumes it. Placement pause and ordinary combat policies are also checked.

These tests exercise the real pure director and the shared policy used by DevilsSession, not a running session with a native camera. The session wiring was inspected in session.patch. Computer Use still reports the Mac locked; actual framebuffer, input restoration and listening acceptance remain pending. No visual completion commit is claimed.

Full JUnit: 2549 tests / 16 failures / 0 errors. Failure identities match prior baseline: True. They remain unresolved. Gradle --continue completed the jar task, but the combined command failed due to tests. SHA256: `d18a974c00477543a5fe0074dbe11a467e5655315c81fa6ed2102afa43251b96`.
