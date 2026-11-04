# W217 Null Composure — FIRST reviewed, SECOND pending

This candidate retains the W179 Null Composure body, battery geometry, face UVs,
texture references, eleven authored motion knots, pivot and battery anchor.
It replaces per-segment smoothstops with W216 C1 weighted-harmonic PCHIP and emits
61 poses over 60 intervals. There are no new geometry elements or whole-grip,
receiver or triggerguard moves.

The same-weapon reference remains Datto FdLSPBirfps: identity at20.00s and reload
at136.8..138.8s, as documented in W179 SOURCE.md/manifest. The upright silver
shroud, blue capacitors, gold crest, open optic and lower frame remain intact.
The hidden battery stroke and contact positions are authored interpretations;
the worker read existing provenance and did not reopen the video.

The worker read the fresh master Blender5.4.0 Alpha report and full-chain export
and viewed the actual 80A8ADD3 upper-chain PNG at
/private/tmp/destiny-w217-source/sheets/fusion_rifle_04669cdb-80A8ADD3-upper-chain.png.
The report identifies Armature|fp_80A8ADD3_reload_full|Base, OBSlot, source
frames1..100 at30fps,61 evaluated samples, unchanged inputs and prior matrix
error0. The original scene contains only an ARMATURE. This is a shared fusion
group containing Null Composure, not an invented weapon-exclusive animation.
There is no recovered weapon mesh, camera, hand mesh or finger IK. The worker
did not independently open/evaluate Blender.

The pure stdlib generator returns248 absolute Path->bytes outputs and writes
nothing on import or generate(root=ROOT). Master owns materialization and shared
loader/runtime/rig/arm binding. Fresh rig SHA256
747749cea16ee1bec34df57fbb7fb8b6c7bb32e6dd1dfef6188991a0d2e4d76a
and report SHA256
d8edb0d97be1b4cc1446363216ac271fb6bbb1a91f3b52f1fa0b3dc48388fd6a
must match the reviewed W217 bytes. Existing worker shared inputs remain old;
focused checks override only these input reads in memory.

Effective family framing remains translation[-.65,.6,0], rotation[-1,2,0],
scale.98, rightWristRoll28 and leftRotation[15,35,-35]. The profile sets
sourceFullChain=true, keepMeshSupport=true and hideSupportAtRest=false.
The master binds the original full shoulder->elbow->wrist chain to ordinary-length
fingerless skin arms. There is no arm-length, camera or source-motion compensation.

Explicit contacts.reload uses rigAction80A8ADD3, partHint=magazine,
policy=magazine and gripWindow[.05,.20,.56,.64]. The contact releases during the
last insertion and is fully released by the same-weapon authored seat at.64.
The battery offset stays zero from.64 through1, so the later upper-hand sweep
cannot drag a seated cell through a palm attachment. All original rest contacts
are retained. Any lower-cell/grip overlap must be assessed locally from FIRST;
it does not justify moving the whole grip, receiver or triggerguard.

All91 source elements occur once with exact fields and UVs:88 body and3 battery
(indices28/29/32:Battery_keel_solid, Battery_blue_spine, Battery_heel).
With448 reserved arm elements the reload estimate is539; canonical211+448=659.
These are candidate estimates. Master must measure all actually assembled routes,
including ADS/inspect, against1000. No triangle adapters or added weapon elements.

Focused pre-READY in-memory checks passed:248 deterministic JSON outputs;
absolute output paths; exact authored knots, battery hold and seated interval;
exact partition/UV preservation; both hands/grips and endpoints; canonical
endpoint/nonFP/inactive fallbacks and ADS/inspect precedence; float32(i/60)
thresholds; finite displays with constant scales; C1 one-sided derivatives and
shape preservation without interval overshoot. Maximum sampled Euler component
step was17.454645 degrees. The derivative finite-difference mismatch was.001786
at epsilon1e-7. Audit rejected file-write opens; zero generated files were written.
Legacy generator was read/AST-inspected, never imported or executed.

After explicit master READY (seed session66402 exit0; baseline167443 files,
SHA256341840b529c05f8c1a32d58cd881cd4686f2ab7046fd934734507ed17cfd54e6),
only the three assigned files were written. The same focused checks passed
against the actual worktree generator/profile with fresh rig/report read
overrides in memory. No shared source, generated model, manifest, build, Java,
QA or CU output was copied or written. Master integration must install the
fresh source bytes and register this profile/action/61-pose route.

Magazine6, reload41ticks, charge533ms, burst9, cadence14.333333333333, ammo
lifecycle and audio remain unchanged. Canonical geometry, texture, gameplay and
audio inputs are hash-checked; no Java/shared/runtime/build/QA/CU files are owned.

The initial handoff above was a pre-FIRST candidate. The same-worker FIRST
response below records the later native evidence review. Final native acceptance
remains pending SECOND; assembled route count, listening and continuous60fps
interpolation are not established by these selected screenshots.

## Same-worker FIRST response — justified no product change

Evidence root: /private/tmp/destiny-w217-pass1-native. Worker actually viewed
screenshots/null_composure-review.png and null_composure-reload.png, raw reload
samples06/07/08/09/11 and frames/w217-null_composure-after-reload.png, then
re-viewed the original 80A8ADD3 upper-chain sheet. Open ADS is centered in the
review sheet. Sample06 meets the dark battery;07 remains at the battery;
08/09 show the source handling hand rising toward the receiver;11 shows lowering
and hand recovery. After-reload shows the ready silhouette and two-hand support.
These selected views expose no hard defect requiring a changed contact, framing
or geometry. Source ARMATURE-only limitations still apply.

Read sequences/w217-null_composure-reload.json and
oracles/w217-null_composure-reload-timeline.json. Exact captured client tick
brackets and conservative surrounding server progress polls are:

| Raw sample | Client ticks before..after | Surrounding server polls | Progress bracket |
|---|---|---|---|
|06|1685..1687|2256..2262|.45...60|
|07|1688..1690|2256..2268|.45...75|
|08|1692..1694|2262..2274|.60...90|
|09|1695..1697|2268..2274|.75...90|
|11|1702..1704|2274..2280|.90..inactive(-1)|

The PNGs are not tick-synchronized to server progress. These are outer monitoring
brackets, not exact image pose labels. Sample08's monitoring span
1793147117.739..1793147117.905 straddles the .75 oracle poll at1793147117.9043489,
so claiming an exact .64 seat frame from08 would be unsupported. Sample09 is
wholly bracketed after release. All listed active captures have reload route
before and after; sample12 transitions reload->ready and was not used to label
an exact active pose. After-reload client ticks1767..1769 and server ticks
2337/2342 report inactive progress-1, reloading=false and ammo6/30.

Focused seat check passed without generating files: battery local offset and
attachment weight are exactly zero at.64 and all grid39..60 (.65..1), and body
and battery displays are equal for native/twohand and both FP contexts. At
grid38 (.6333333) the remaining attachment weight is.01967593 with battery
offset[-.00122042,-.01616414,-.00644847]; by.64 both reach zero. Read the current
shared build_first_person_hands_w201.py envelope and magazine displacement rule:
part_shift=(sourcePalm-reloadTarget)*reload_grip_weight. Thus source wrist
departure cannot pull the seated battery after.64. Original full-chain samples
39/45/54/60 retain their evaluated changing wrist matrices and source frames
65.35/75.25/90.1/100; no source attenuation or limb changes were introduced.

Selected evidence SHA256 at review time (batch sealing belongs to master):

- review sheet:58eb9d97e41807cf877bc5f0a889242bc5dd2e9c601d9c891e51b670169aa623
- reload sheet:716f860be0bfe6f9d19d5e036a945078b8fd52f358c3a895ee52fcdad32a84c2
- reload sequence:3991bf8a6c29d193c368463fc80fa1b6198358332b69f6d617c2778cb4ba3d36
- progress timeline:a9dbeb1fd1125cb11618fef87bac9b6039cb372f2e1d915ce7e89b12be4bf94f
- after-reload bracket:69b1b4de994daab1774a4a36140b81cfce188ad97adff075767ea1ee5aecb5db

Decision: retain generator/profile byte-for-byte; update only this review.
Generator SHA256 remains
bda21764d11ebf8b260f254c41182dea806d70a61f7f39d34f2b86976bf9bd24;
profile SHA256 remains
a757011578342a287f4df68a38f460f115088ff2198392d8c887fd65f3055499.
Rest/ADS, geometry/UV, authored timing and audio remain unchanged. No MAIN,
shared, generated, QA, build or CU writes. FIRST selected native two-hand
right-FP evidence supports proceeding to master SECOND. It does not establish
every frame's contact, exact hidden-cell seating pixels, left-FP/native-grip
coverage, lifecycle cases, all-route budget, audio listening or60fps continuity.
