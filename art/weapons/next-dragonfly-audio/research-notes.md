# N3 Dragonfly audio source research

Research handoff: **no defensible dedicated Dragonfly source candidate found** for solar, arc or void in the inspected evidence. Dedicated identities remain **unknown**. Keep the existing fallback. This completes the scoped source investigation, not N3 implementation or acceptance.

## Evidence and classification

The supplied archive is the D2 Master SFX Drive root `1kWVlvhqvFkf_If5Q9Zd0mMIM1haa6u4l`. Cached parent/file IDs and actual local source bytes were checked, rather than relying on filenames as identity proof. Exact absolute paths, full SHA-256 values, IDs, saved-listing coverage and read-time source hashes are in [source-manifest.json](source-manifest.json).

| Element | Existing original in read-only W33 cache | Supported finding | Dedicated Dragonfly identity |
| --- | --- | --- | --- |
| Solar | Hunter_Golden_Gun / 0215-000016A1.mp3; ID 1mz99LrYNXnW7sowJmw0BstrPBAQE3bCe | Original and existing Ogg hashes match W33 pins; uploader super-folder provenance, provisional discharge surrogate | Unknown |
| Arc | Hunter_Poledancer / 0215-0000163A.mp3; ID 1efALRAZftatncdG9GrQEacOhG6TuVKPw | Original and existing Ogg hashes match W33 pins; uploader super-folder provenance, provisional transient surrogate | Unknown |
| Void | Grenades - VOID / Exp_VOID_Vortex_Grenade_1.mp3; ID 1-Tu72ia6VjwEoOdYZx3US8SHIlRcWLeM | Original and existing Ogg hashes match W33 pins; uploader grenade label | Unknown |

“Confirmed” describes byte/provenance facts only. There are zero confirmed Dragonfly recordings and zero dedicated candidates supported by the inspected evidence. The existing solar/arc clips are already surrogates at the grenade layer; moving their labels to Dragonfly would not improve source identity. W33 audio measurements are prior recorded measurements, not fresh decoding or listening here.

The completed bounded local metadata scan and its exact hashed file inventory are in the manifest. It found no Dragonfly/Firefly text in the selected metadata. It excludes tools, large files and unrelated user archives and is not an exhaustive export of the collection. Two earlier broad regex scans were interrupted; the completed literal inventory supersedes them.

The cached root links to __Supers & Abilities (1SfxXaG5l4YaBAy2j3Uj2vysaIcwkc0Hs), whose saved HTML and full JSON identify Perk Related (1L1oOztNV7NaMQcKHDIbfMcAE7NPS8dsb). One targeted public metadata GET, capped at 2 MiB, returned four visible Woven_Mail_1..4.wav rows. The response hash, timestamp, exact IDs and parsed rows are preserved. These are rejected as unsupported Dragonfly candidates. No source audio was fetched. The raw remote HTML was held only in memory; the manifest preserves the parsed snapshot, not a full raw response. This observation is limited to visible rows.

The saved Legacy Sounds [2014-2019]/Explosions listing contains numeric 02FA files. Their exact visible file IDs are retained as **unknown inventory**, without invented element or event assignments. A listing hash is not an audio source hash; audio hashes remain null for unacquired originals. D1 Firefly, Woven Mail, super transients and grenade labels do not establish D2 Dragonfly identity.

## Next feature handoff

The smallest useful next input is a bounded clip/cue or event mapping from the supplied collection tying the precision-kill explosion to its solar/arc/void element. No massive archive download is needed. A candidate needs the exact source path/file ID, original SHA-256 and independent event/reference evidence; numeric names or envelope similarity cannot supply event identity.

Conceptual keys weapon.dragonfly.solar.detonate, weapon.dragonfly.arc.detonate and weapon.dragonfly.void.detonate are proposals only. Their source/output hashes remain null. No Ogg was generated, no event registered and no runtime patch supplied. After identity acceptance, a separate scoped implementation can record processing hashes and let topmaster integrate shared calls/registry. VFX remains a separate feature.

## Native and central validation plan

[native-scenarios.json](native-scenarios.json) supplies all mandatory operating-document fields for three independent planned scenarios: taskId, candidatePin, capability, fixtureId, setup, inputSteps, serverOracle, framePlan, audioClaim, cleanup and result. candidatePin/result are null; status is planned_unrun, with not_run_source_unknown and not_integrated gates.

Representative weapons are verified from W40 characteristics and W77 eligibility: solar distant_relation, arc long_arm, void brass_attacks; all use the confirmed base Dragonfly socket 4 / perk hash 2848615171. No new fixtures, tests or source changes were made.

Topmaster runs the central serial gates after source acceptance and integration. The plan covers native paid precision kills and body/no-perk/nonlethal controls, exact victims/ammo, open/covered/outside neighbors, a single event and actual recipients, and no recursive secondary dispatch. Server fixture setup remains preparation rather than native input proof. Native capabilities must be inspected before input; unsupported slot selection or Q/Ctrl+Q remains not_run_capability.

The single central batch must capture fresh before/impact/restored PNGs and separately document actual audio capture/listening when available. Packet/dispatch/OpenAL/PNG evidence cannot establish listening. Every sequence has lease/finally-release and neutral-state confirmation, owned-object teardown on success/failure/timeout/cancel, and restoration before the next scenario. No native session or listening occurred here.

## Hierarchy, scope and review

- Task N3; parent topmaster; lead L1-dragonfly-audio; depth 1.
- Lead thread ID: 01a16f5f-327b-7523-af27-01b43da1a02c.
- Native spawn/wait/send/close-agent tools are unavailable. Child count 0, child thread ID null; no app create_thread fallback.
- Child acceptance/review/closure and slot return: not applicable; no child or slot was acquired. Lead evidence review completed; research files ready for topmaster review; integration not_integrated.
- Exact ownership: only this new research-notes.md, source-manifest.json and native-scenarios.json. Writing scope is released at handoff.
- Local static checks only: JSON/contracts, eligible representatives, six original/Ogg SHA comparisons, listing parent/file relations and owned-file diff. Builds/tests/servers/clients/apps/commits: zero. Source audio remained read-only.
- Shared queue, journal, README, runtime, assets, sounds.json and tests are outside this lead's writes. Existing checkout changes belong to other work; read-time hashes are not a frozen integration candidate.

The operating document changed externally during final static review. Both initial and current hashes are preserved in source-manifest.json; the current document was reread. Its revised delegation guidance permits source leaf work with no artificial child. Runtime/sound/eligibility evidence pins still match. No frozen integration candidate is claimed.
