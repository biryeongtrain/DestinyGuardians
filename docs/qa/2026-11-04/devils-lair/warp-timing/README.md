# Sepiks warp timing — real server entity ticks

Two new GameTests run an attached Sepiks model/entity in a real Minecraft server, allowing its normal AI age to reach 200. The encounter director is advanced through prior encounters as fixture setup. No reflection or manual AI ticking is used.

- Clear destination: source position is retained during warning, the exact selected destination is passed to commit once, relocation precedes arrival sound.
- Destination blocked after warning: commit is still called once, relocation and arrival sound are both suppressed.
- Timing: commit occurs on the sixteenth AI step inclusive of the warning step (15 server-tick intervals after the begin sound), followed by recovery.
- All eight DevilsWalkerGameTests pass, including the two new cases and six existing actor/model, faction, audio-packet, and actual-damage cases.

The commit acceptance flag models a late obstruction. Authored NBT collision/occupancy validation is covered by the separate warp-pads suite; this test does not combine those maps with the live timing fixture. No client framebuffer, native input, speaker listening, or FPS acceptance is claimed. Computer Use preflight still reported the Mac locked and QA ports 8102/25610 had no listeners, so no native client was launched.

Production code/assets were not changed by this batch. Existing full-suite 16 failures remain unresolved; the entire suite was not rerun for these test-only additions.
