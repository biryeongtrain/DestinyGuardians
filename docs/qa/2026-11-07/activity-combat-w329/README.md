# W329 activity, melee and source audio QA

Authoritative integration: `/Users/qf/IdeaProjects/DestinyGuardians`. Isolated native server/client: `/tmp/destiny-devils-qa-20261103`, server25610 / Vision8102 / DevilsQA. Workers changed independent worktrees; master ran native input and inspected actual PNGs. QA covers the current integrated working tree, including pre-existing W327 weapon/perk changes. Those unrelated changes remain outside this scoped W329 commit. User authorized isolated background input previously.

## Implemented behavior

- Common activity exit tickets bind player, connection and exact participation session. Gear provides continue/leave confirmation; personal leave preserves teammates. Down-state chat confirmation remains available.
- Shared swept melee hits multiple visible owners with bounded candidates, line of sight and multipart deduplication. Sword, Arc Staff and Spectral use finite five-frame motion leases rather than teleport corrections. Native movement validation remains enabled.
- Ground lunge budget2 blocks; air5. Spectral captures accepted attack airborne state so its delayed contact keeps the air budget even when the windup ends after landing. Its existing31tick light recovery remains.
- Restriction notice and persistent marker; full teamwipe presentation and checkpoint recovery. Menu visibility does not restart the restriction cue. Indicator is below the health bar.
- Accepted activity Play starts the full Director cue immediately, waits20ticks, shows5..1 through tick100, and launches once at120ticks. Cancellation stops only the owned sound event. Source tail is retained.

## Native evidence

Actual framebuffer screenshots, native input consumption and server state were checked separately. These checks do not establish human speaker/listening acceptance.

| Scenario | Result |
| --- | --- |
| Sword grounded / airborne |2 /5 horizontal blocks, actual body trace; no movement-check snapback in observed sequence |
| Sword cleave |Two side Husks100→90.16 each |
| Sword wall |StartX300.5, wallX302, body stopsX301.65; target behind wall unchanged |
| Arc Staff |2 ground /5 air; both side targets damaged |
| Spectral |After fix300.5→305.5 in jump attack; two side Husks100→67.528 each |
| Countdown |Native Play, actual5/3/1 PNG samples, server launch after120ticks; SoundEngine plays selected Director source |
| Restriction |Correct icon and text, marker below healthbar; hidden in Gear and restored without cue replay |
| Teamwipe |Correct full-screen texture, selected teamwipe SoundEngine event, same checkpoint revived with new generation |
| Exit |Native E opens Gear, native continue preserves activity, native confirm exits; world transition intentionally cancels input lease |

![Restriction](restriction.png)
![Wipe](wipe.png)
![Exit confirmation](exit-confirm.png)

Initial native validation found missing textures in the new namespace: PNGs existed but neither vanilla item nor block atlas scanned textures/gui. Fixed12 exact sprite sources in items atlas, verified merged ZIP and reloaded client; final PNGs above have no checkerboard. Initial Spectral delayed-contact ground classification was fixed and retested. User also manually confirmed behavior and explicitly reported the same missing-texture defect before the fix.

## Automated checks

- Real Gradle assemble succeeded; exact artifact hash in artifact.json.
- Initial targeted JUnit42/42, countdown/state followup11/11, atlas/countdown final targeted6/6 passed.
- Full JUnit baseline comparison:2749 total,19 historical failures; same failure identities as prior W328. No claim of a green full suite. GoldenGun historical snapshot failure message changes with the edited HunterSuper source hash.
- Central GameTest: all50 required tests passed, real Gradle runGameTest BUILD SUCCESSFUL. First run crashed on nested tick-driver registration; second completed50 with9 fixture failures. Followup fixtures fix player world/list membership, camera watchdog setup, enclosure boundaries and packet flush timing without reducing assertions.

## Provenance, size and cleanup

Exact user-selected source mappings: respawn restriction023D-0000110F; teamwipe023D-00001176; countdown Drive file131_ndTXUG-08ev6wuRdiNK7ecmOqUjMQ. Full original audio and source metadata retained in art/audio. UI artwork is an authored Destiny-inspired approximation, not extracted original UI art.

Final generated pack185847431bytes (<250000000);12 explicit new atlas sources verified. See pack-after-atlas.json. JAR size is distinct from deployable pack size.

Temporary melee targets/wall removed; resistance fixture cleared; original heavy weapon returned from system storage and QA player returned to Tower. Existing storage and manual user changes preserved. Last observed control state before shutdown had no lease/keys/queued steps. Final slot-restoration screenshot was interrupted by owned client shutdown; it is not counted as a successful capture. Only owned client/server sessions were stopped; normal profiles unchanged. Bounded awake coordinator remains owned for the user-requested statistics followup QA.

Raw first/final logs, all native traces and failed attempts remain under `/tmp/w329-activity-combat/qa`.
