# W221 Parcel of Stardust (Fell to Earth) candidate

Status: transferred to the assigned READY worktree after verifying baseline hash `20d131fe19cf2c58851434a6948223e71292498af598146204c6cb39d66031d4`. Only the exact three owned files were written; main/dependency/generated files remain untouched. OriginalBlend -> Blender61 -> FIRST Vision -> same-worker review is now recorded below; master SECOND Vision and final acceptance remain pending. Retain this worktree as a reusable slot after W221 per latest user instruction.

## Exclusive delta

- `scripts/generate_insert_w221_parcel_of_stardust_fell_to_earth.py`
- `art/weapons/w221/parcel_of_stardust_fell_to_earth/profile.json`
- `art/weapons/w221/parcel_of_stardust_fell_to_earth/review.md`

Temporary draft staging root: `/private/tmp/destiny-w221-drafts/parcel_of_stardust_fell_to_earth/`. This scratch location is not durable provenance.
Assigned worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-parcel_of_stardust_fell_to_earth`.

## Original-source evidence actually reviewed

Reviewed the temporary staged copies of the source review, handling evidence, fresh rig and upper-chain sheet. Master retained the durable repository-relative provenance at:

- `docs/qa/2026-10-28/w221/source-review.json`
- `docs/qa/2026-10-28/w221/source-handling-evidence.json`
- `docs/qa/2026-10-28/w221/source-sheets/shotgun_2eb0529e-80A8A3F1-upper-chain.png`
- `art/weapons/w221/rigs/shotgun_2eb0529e.json`

These are the recorded archival destinations, now confirmed present in main; the temporary source staging paths are not durable references. Master owns their preservation and installation. The worker has not created those shared files. The sheet depicts both shoulder/elbow/wrist chains at normalized0/.2/.4/.6/.8/1, with a substantial mid-action excursion and return near the starting chain arrangement. It does not show the Parcel model, shell contact, camera, or gameplay.

Master, not this worker, opened the original `.blend` in its separate background Blender5.4Alpha and evaluated61 samples. Its reported prior-cache joint error is0 and inputs unchanged. Action `Armature|fp_80A8A3F1_reload_full|Base`, slot `OBSlot`, source frames1..101; left loading hand. The armature-only scene has no weapon mesh, camera or finger IK. Shared group membership is not proof of a recovered per-weapon selector. Profile sourceBlend/sourceMap/boneMap hashes are taken from that fresh cache.

Read the weapon-art skill and Ace/Izanagi study, Parcel canonical W123/W147 surface and geometry evidence, effective framing, W201 contacts, W208 shape/shell-phase API, FILO's rejected body-only-freeze history, and master-owned hands/rig/reload-hand modules. No live DCC or SSD source was modified.

## Mechanical choices

Retain all101 canonical body elements and their UVs, including wooden pump/stock, rigid tube magazine, loading elevator, open guard, barrel and clear rear sight. No detachable magazine, pump movement, texture edit, invented geometry reduction or scale-zero shell. Right grip `[8,9,9.18]` and left support `[7.8,9.1,-.8]` retain exact W201 contact records. Start from effective shotgun framing: translation `[-.65,.6,0]`, rotation `[-1,2,0]`, scale`.98`; retain wrist/support settings; enable sourceFullChain/keepMeshSupport, disable hideSupportAtRest, sourceViewRotation identity. No camera-depth/lift/lower or axis damping is introduced.

Parcel's own loading elevator spans `[7.44,10.08,2.48]` to `[8.56,10.48,4.10]`. Shell anchor `[8,9.78,4.18]` sits below its lower face, just behind its rear edge. The longitudinal shell points along canonical -Z; .44-diameter case, .46 head, .51 rim, total length1.54. Alignment stays below the elevator, then rises .62 and advances1.35 toward the fixed tube bore. This is authored loading geometry, not an extracted cartridge track. Twelve solids retain nonzero meaningful Parcel UV rectangles from `magazine_wall_0`, `ejection_bolt`, and `magazine_front_collar_0`; no FILO geometry/contact is copied.

INITIAL, LOOP, RETURN each contain61 poses/60 intervals (183 total); native/twohand, both first-person display contexts. Shell offsets use shape-preserving C1 PCHIP with zero endpoint/hold/extremum derivatives. Initial visibility .46<=p<.90, loop .12<=p<.84; pickup and seated holds bound ordinary-scale handling. Only the shell uses empty geometry outside these windows. Invisible recycling returns to identical HOME with zero velocity at initial-end/loop-start/loop-end/return-start, including continuous handling-hand target seams. Return has no shell geometry.

The generated body leaves retain accepted rigid displays; they contain no independent authored body sweep. **Master must compose source weapon motion AND the entire shoulder/elbow/wrist chain together.** This is not the rejected FILO body-only freeze. `sourceShellPoseHold=true` opts into the shared calibration: initial source_p=.35*smooth(p/.36); loop source_p=.35/frame36; return blend the same source pose to rest. `sourcePalmContactFit=true`, shell policy, shell partHint and rigAction80A8A3F1 keep the left loading palm coherent with the relative shell target. These are explicit calibrations, not a recovered shell loop or full-action replay.

## Pure checks completed

Ran `rtk proxy python3 -B` with an audit hook rejecting write/mutation operations during import and generation. Two generations are byte-identical. `generate(root=ROOT, *, rig_path=None, profile_path=None)` returns737 absolute Path->bytes entries:3 geometry parents,732 display children,1 item graph and1 manifest. It writes nothing; scratch rig/profile overrides work without installing source caches. Inputs remain root-relative by default; optional relative overrides resolve against root.

Passed exclusive namespace partition; all generated/existing model references resolve; canonical body/UV equality;12 positive-volume shell solids with nondegenerate UVs; ordinary unchanged positive scale and rotation in all732 display children; untouched non-FP displays;183 exact Java float32 division-before-addition thresholds; two next-float inactive-gap guards. Original item metadata and entire canonical graph are retained for non-FP, ADS, inspect, negative/inactive CMD4, initial0 and return60 (also values above5). Dense PCHIP samples remain within knot bounds; numerical one-sided C1 checks pass; hidden HOME body/shell displays and derivatives match at every held phase seam for both grips.

Budget:101 body +12 shell =113 weapon elements; conservative448 ordinary forearm/upper-arm reservation yields561 assembled elements, below1000. This is a reservation-based upper bound, not master's actual skin-materialized count. No full hands generation, Gradle, game, Vision, audio or continuous60fps claim was performed.

## Integration and remaining review

Master owns W221 cache/profile loading, exact ID parser/runtime routing on CMD4 with60-grid samples, shared shell hold/contact opt-in, hand materialization, actual assembled count and FIRST/SECOND Vision. Preserve existing per-shell insert duration/ammo events and W219 cancellable last-shell sound; this delta edits no gameplay/audio code. Framing must be applied once to the whole assembly.

FIRST review should cover native/twohand and both handed contexts: upper arms at initial lift, shell pickup/seat occlusion, left palm contact, repeated loop stability, hidden HOME continuity, early cancellation/partial reload, return and hip/ADS sight clearance. Send concrete images/phase intervals to this worker; respond with a correction or justified no-change before master's SECOND. No cosmetic revision should be manufactured. Native acceptance remains pending. User authorizes commits after the accepted batch; master owns all commits, workers do not commit. Retain the fixed worktree slot afterward.

Provenance-only draft normalization: generator manifest and profile now name the durable QA evidence above and root-relative fresh rig. Rechecked import/generate purity and determinism; all736 non-manifest generated assets remain byte-identical to the pre-normalization candidate. At provenance normalization, no worktree transfer had yet occurred.

READY transfer validation: imported the assigned-worktree generator and generated twice in memory against that worktree; audited import/generation rejected writes. Passed deterministic737 outputs, exclusive paths,183 Java float32 samples plus2 gap guards, graph fallback/endpoints, source body/UV equality, ordinary scale/non-FP displays, shell volume/UV, PCHIP monotonicity/C1 and hidden HOME seams, and reference resolution. Used the temporary originalBlend61 scratch rig override because shared W221 rig installation remains master-owned; recorded provenance stays repository-relative. No assets were materialized; FIRST feedback and SECOND Vision were pending at transfer. No full worktree scan, export or commit was performed.

## FIRST Vision feedback response: justified no-change

Reviewed the actual Parcel hip/ADS/reload sheet and reload sequence sheet, the Parcel panel of `first-post-reload-review.png`, and full-resolution raw reload captures03,04,13,14. Reopened the retained original-source upper-chain sheet and read the retained source action/handling evidence. No game, live DCC, generated pack or shared file was modified by this worker.

The pictured hip and post-reload views retain the wooden pump/stock and ordinary arm silhouette; pictured ADS has a clear center sight opening. The reload sheet retains a stable port pose and normal arm shape. Near-seat raw03 shows the loading palm raised beneath the receiver with ammo0; raw04 shows ammo1 and the next handling state at the same weapon pose. The capture03 client bracket is1769..1771, near recorded observation time1793159982856ms and the server timeline's initial CMD4=.85 at1793159982911ms. This is a near-seat bracket, not an exact synchronized CMD4 reading for the PNG. The cartridge is largely occluded by the palm/receiver there. Raw13 shows a small exposed shell surface at the top of the left loading palm; raw14 moves that palm toward the port, where the receiver obscures the cartridge. There is no pictured detached floating shell, raised upper-arm intrusion, or weapon jump. These snapshots do not prove a fully visible seat silhouette throughout the sequence.

Rechecked the owned pure curves: initial reaches SEATED `[0,.62,-1.35]` atp=.86 and stays seated until visibility ends atp=.90; loop reaches SEATED atp=.78 and stays seated until visibility ends atp=.84. Last visible grid samples are initial53/60 and loop50/60, both exactly SEATED at ordinary scale. Empty geometry starts after seating; hidden HOME recycling does not expose a returning cartridge. The visibility rule does not hide an unseated shell to mask a contact defect.

Confirmed the installed shared contact-fit implementation targets `left[ctx]['translation']` toward the shell's reload_target using the existing grip envelope. The profile selects handLEFT, shell policy, sourcePalmContactFit and sourceShellPoseHold. At full handling weight the left palm and the shell anchor share that exact composed target; the right grip is unaffected. Observed partial shell visibility at the left palm is consistent with that route. No alternate hand assignment is warranted.

Compared the installed originalBlend61 joint sampler against the authored curves: initial-end, loop-start, loop-end and return-start all select exactly the same full source sample atp=.35/frame36 of80A8A3F1. Body and shell display targets match at those four seams for native and twohand, both first-person contexts; HOME is hidden and its endpoint derivative is zero. Return ends at the original source rest joints. Raw03/04, the stable repeated pose on the reload sheet and the settled post-reload panel show no visible seam jump. Pure equality establishes the sampled seam contract; sparse PNGs cannot certify every intermediate rendered frame.

The retained source file remains armature-only with original shoulder/elbow/wrist chains,61 samples over frames1..101 and master-reported prior-cache error0. Its generic full reload contains no weapon mesh, camera, cartridge or per-shell selector/event track. The .35 whole-chain hold and contact fit remain explicit calibration; this review does not reinterpret them as recovered shell animation.

Read `vision1/native-validation.json`:18 total native sequences, neutralAfter=true; Parcel reload54 captures, ADS12 captures, finished ammo6/25. The Parcel interrupt record reports released=true, reloading=false, afterRounds1 and an authoritative runtime.paid event. These are retained master-run results, not a new worker execution or acoustic listening check.

Decision: no generator/profile correction. The available images, installed LEFT contact-fit route, seat-before-hide checks and identical held seams provide no concrete defect. Do not move the shell, palm, source axes or camera merely to expose an occluded cartridge. Visibility under the receiver/palm is the documented limit; retain current geometry, ordinary arm lengths, full chain, timing and audio. Only this review document changes in response to FIRST feedback.

Remaining: master SECOND Vision and final acceptance; sampled first-person views do not establish all opposite-hand/native/slim combinations, fully unobscured seat contact, continuous60fps or microphone/listening validation. Master retains commits and shared integration. Keep this fixed reusable worktree slot and this worker available until accepted.

FIRST image evidence actually viewed (paths relative to `docs/qa/2026-10-28/w221/`):

- `vision1/screenshots/parcel_of_stardust_fell_to_earth-review.png` SHA256 `880050008c283437ab7b39739d7a6c25b4846b61538cf77385f7be2a3bb59016`
- `vision1/screenshots/parcel_of_stardust_fell_to_earth-reload.png` SHA256 `a6ed91ebb486518d452d361845d08779d0d61803c9f594f1b0c3d97d174bfb48`
- `first-post-reload-review.png` SHA256 `77107b1e8a5e6a8567494282dfcdd760805e16de8e5ba327383128eee478f97f`
- `vision1/frames/w221-parcel_of_stardust_fell_to_earth-reload-sample-03.png` SHA256 `3ef1695d78e73b899f097d0304d005c42120f74d211532a84999c53339d42890`
- `vision1/frames/w221-parcel_of_stardust_fell_to_earth-reload-sample-04.png` SHA256 `6f7e945ccbf3ed2caaeed5db993e18756ccfbc61a7d0cea95f7e6ac876c60089`
- `vision1/frames/w221-parcel_of_stardust_fell_to_earth-reload-sample-13.png` SHA256 `f0cc1397864293d2a98c4e2323561aeb662dd1acecba6d4a95abb97efd84dfd9`
- `vision1/frames/w221-parcel_of_stardust_fell_to_earth-reload-sample-14.png` SHA256 `cde4221329d0a5b2840770f8467e193e30b3aa444c12961f1d6ae9a3d03a300f`
- `source-sheets/shotgun_2eb0529e-80A8A3F1-upper-chain.png` SHA256 `76a2e7f4e73a6bfb804e8eb0e3918289280976c7b3e6bff78dbdb7c706f01c41`
