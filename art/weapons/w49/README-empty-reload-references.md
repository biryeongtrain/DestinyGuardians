# W49 — empty reload / bow nocking references

Research only, reviewed 2026-10-24. **Direction is supported; exact Destiny timings and input transitions are not established.** Hashes, exact item text, source classifications and observed frames are in [empty-reload-references.json](empty-reload-references.json).

## Primary evidence and direct observation

- **Native automatic vs accessibility:** [Bungie, 2022-12-01](https://www.bungie.net/7/en/News/article/51999) announced the global Full Auto toggle. It is separate from a weapon's intrinsic automatic behavior; footage with unknown settings cannot classify native semi/auto behavior.
- **Charge must survive reload:** [Bungie Hotfix 6.3.0.7, 2023-01-31](https://www.bungie.net/7/en/News/article/hotfix_6_3_0_7) separately fixes held-trigger Full Auto stoppage and charge-based weapons bypassing charge delay after empty-mag auto loading. This supports preserving charge gates, **not** a guarantee that every weapon resumes on the same held press.
- **Nock and draw are distinct:** the pinned official inventory cache describes Compact Arrow Shaft (`16392701`) as improving nocking and reload speed. The selected Biting Winds and Whispering Slab resolve to Precision/Lightweight intrinsics (`715195141` / `2108556049`) whose text explicitly assigns Reload to cancelling a drawn shot. These definitions do not explicitly specify automatic nock initiation or durations. The old Bow Reloader (`2493794080`) is deprecated in this cache; its historical loader wording is not current evidence.
- **Actually viewed bow sequence:** [cassuttaja, “Rapid hit on bows reload speed test,” 2022-09-27](https://www.youtube.com/watch?v=54yvDaDwlJ4&t=7). Downloaded format 244, 854×480, 30 fps. Zero-based source frames 235 (PTS 7.833s) and 240 (8.000s) show post-shot recovery with HUD `0`; frame 255 (8.500s) shows a nocked, undrawn bow and HUD `1`; frame 300 (10.000s) remains idle with `1`. This verifies **shot → nock/recovery → loaded idle**, distinct from the next draw. **No input overlay:** it cannot prove that Reload or a second trigger press was absent. Automatic nocking is a direction inference, not directly verified physical input. Rapid Hit/modifiers are uncontrolled; neither the uploader's frame-count claims nor these locator timestamps calibrate base timing.

Full video, metadata and inspected frame/contact images stay under gitignored `run/private-sources/w49/`; no full media is copied into `art/`. Existing W48 Long Arm footage supports insert visuals only; it does not establish held input or automatic reload initiation.

## Early release, cancellation and evidence limits

[Bungie designer Greg Peng's 2018 interview](https://gameinformer.com/feature/2018/06/13/a-deep-dive-on-destiny-2-forsakens-new-bow) directly describes early release changing trajectory. Bungie [linked this developer feature](https://www.bungie.net/7/en/News/Article/46944). This is historical developer evidence, not a current damage curve; the embedded video returned 404 and was not viewed.

The [Destinypedia Gameplay section, revision 389637](https://www.destinypedia.com/index.php?title=Combat_Bow&oldid=389637#Gameplay) **is community secondary evidence**: it describes early/undrawn release with reduced damage and speed, greater arc, Reload letdown without firing, and eventual forced release when holding too long. Its qualitative account supports avoiding an all-or-nothing “discard every early release” model. It does not provide exact damage/velocity/arc interpolation, perfect-draw duration, hold/overdraw threshold or penalties. Those values remain unknown; ordinary bows, frame differences, exotics and perks must not be collapsed into a universal measured rule. The clip does not measure perfect draw or overdraw.

Official Reload-cancel text supports letdown. Mapping that action to **Q**, suppressing a projectile, and ensuring cancelled input cannot later emit a deferred arrow are project decisions. Nocking time must not count as active draw time; nock completion must not itself draw or shoot.

## Reports supporting direction, not universal guarantees

| Source | What it establishes / limitation |
| --- | --- |
| [Help 262342625](https://www.bungie.net/en/Forums/Post/262342625) | Player reproduction expects reload after emptying while holding fire/ADS; reports a bug. Not a Bungie specification. |
| [Help 262105717](https://www.bungie.net/en/Forums/Post/262105717) | Player expects continuous Full Auto when holding fire through reload; reports controller jams. Not evidence for native semi-auto. |
| [Help 264667841](https://www.bungie.net/en/Forums/Post/264667841) | BNGHelp8 acknowledges investigation of Barrow-Dyad/settings interaction. Exotic special case, not a blanket rule. |
| [Historical LFR report](https://www.reddit.com/r/DestinyTheGame/comments/10qjbsh/) | First-person report contrasts SMG/sniper held-input reload with an LFR release/repress requirement after a patch. Not a universal charged-weapon contract. |
| [Sprint/reload report](https://www.bungie.net/en/Forums/Post/243540461) | Community account says animation cancellation still leaves firing delay. Ammo HUD refill alone does not prove shoot readiness. Sprint cancellation, transfer boundary and restart timing remain unverified. |

## Authored implementation direction — not measured Destiny behavior

- Last successful shot queues empty reload **after any burst drains**, without another press. Keep existing eligibility/ammo gates. The initial delay bounded by the **next server tick** is authored, not a measured original-game delay.
- Resume only a supported **intrinsic automatic** profile with maintained real fire input, after reload and existing fire/cooldown gates. Do not treat stale input or repeated empty callbacks as a new press. Native semi-auto gets no queued extra shot. Fusion/LFR still require a fresh press under this scope; this is not asserted as universal Destiny behavior.
- A successful released bow shot schedules nocking without requiring another press to reload. Completion restores the arrow to ready/idle, without an extra shot. Start draw timing only when a loaded arrow actually begins drawing. Partial release may fire using explicitly **authored interpolation**; it is not an exact Destiny scalar. Q letdown cancels without an arrow.
- Sprint/cancel/swap/skill should invalidate pending work so it cannot later reload or shoot unexpectedly; retain transfers already committed by the existing policy. Exact Destiny cancellation, automatic restart, and ready-to-fire boundaries are unknown. Do not infer an early shot from the disappearance of an animation.

No main code, tests, other docs, logs, Gradle, runtime or commits were changed/run by this research task.
