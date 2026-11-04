# W220 Edge Transit ready candidate — FIRST review pending

Owned changes only:

- `scripts/generate_reload_w220_edge_transit.py`
- `art/weapons/w220/edge_transit/profile.json`
- `art/weapons/w220/edge_transit/review.md`

## Source evidence and authorship

Read `/private/tmp/destiny-w220-source/worker-common.md`, worktree `AGENTS.md`, the referenced global `RTK.md`, minecraft-weapon-art-design skill and Ace/Izanagi study. No `.codegraph/` exists in this worktree. Read master `source-review.json`, `source-handling-evidence.json`, `source-selection-review.json`, fresh heavy rig, W180 generator/manifest/SOURCE.md, current framing/contact API, `reload_hand_w218.py`, `rig_arms_w205.py` and relevant `build_first_person_hands_w201.py` paths. Viewed actual heavy104 upper-chain sheet and retained W180 actual-footage storyboard with the image tool.

Master evaluated the original read-only Blender source in Blender5.4.0 Alpha before implementation. Worker did not independently open or evaluate Blender. Selected group `heavy_grenade_launcher_796e9ebf`, action `80A8A104`, `Armature|fp_80A8A104_reload_full|Base`, OBSlot, original frames1..142 at30fps,61 evaluated samples. Source contains ARMATURE only; no weapon mesh, camera or finger IK. Weapon-local wrist excursion32 is LEFT32.63977327179959 versus RIGHT0.0004504622613956923. LEFT handles; RIGHT carries. No per-weapon selector recovery is claimed. Profile records source hashes and reviewed evidence hashes.

W180 storyboard shows raise, whole drum departure, empty rectangular frame, replacement return, seating, final hand action and recovery. Historical dark-shader footage establishes action order; canonical green/seafoam UV/paint stays intact. Numerical keys, hidden exchange path, cradle38deg, lug stroke, contacts and normalized phase mapping remain authored adaptations. The sheet shows bone motion and cannot establish mesh contact or native visibility.

## Geometry and mechanics

Preserve canonical96 solids and face UVs, exact12 W180 authored keys, hold phases, and matrix algebra. `GRIP=(8,8.8,8.5)`, `DRUM_ANCHOR=(8.53,10.22,3.11)`, `HINGE=(8.53,9.67,.85)` remain exact. No new geometry, textures or triangle adapters. The complete28-solid drum consists of4 cores,8 bays and16 front/rear rim segments, canonical indices28..55, names `drum_core_`, `drum_bay_`, `drum_front_rim_`, `drum_rear_rim_`. All28 share one rigid magazine transform; it is never reduced to a plate.

Body68 includes the four original `drum_latch_±1`/`drum_cradle_±1` solids, articulated around the retained hinge, and original `charging_lug` index95. Brackets open38deg by.20 and hold through.74; empty-frame hold.42..52 remains exact; drum seats.74; cradle closes.81; existing lug reaches.85 local Z travel at.89 and returns.94. No extra magazine copy, scale fading, body-mounted barrel attachment or shell invention.

Interpolation is stdlib C1 weighted harmonic PCHIP with zero endpoint/hold/extremum tangents across vector and scalar channels. All12 keys remain exactly evaluable even where they fall between the61 uniform poses. Outputs use exact float32(i/60) thresholds for60 intervals. Native/twohand and both FP contexts remain. The exact current canonical item graph handles nonFP, endpoints, negative inactive progress, overshoot, ADS and inspect.

The authored W180 carrier algebra is retained. Current shared `source_weapon_display` replaces that carrier with source weapon motion, preserving relative drum displacement and body articulation. The worker adds no second source-body transform. Master owns source-chain replay without retiming, attenuation, stretching or hiding.

## Contacts and attachment

Effective `first_person_framing_w205.load/profile` for this heavy family currently resolves to default translation[0,0,0], rotation[0,0,0], scale1, rightWristRoll15. Preserve these values and set sourceFullChain=true, keepMeshSupport=true, hideSupportAtRest=false. No additional camera offset.

Preserve W201 idle contacts: right[8,8.4,8.73]/[-28,0,0], left[8,7.95,-2.35]/[-21,0,0]. Preserve reload flank contact[5.8,10.1,3.1]/[0,0,-80]. Explicit hand=left, rigAction=80A8A104, partHint=magazine, policy=magazine applies to all28 drum solids. Grip window[.12,.20,.64,.72] ramps before extraction and fades during reseating, fully zero before.74 seat. Seated recovery, cradle closure and lug action remain independent of the source palm. The authored path resumes during release; FIRST must check contact and clearance during that blend.

## Targeted verification performed

Ran pure Python with `-B`, fresh scratch rig override `/private/tmp/destiny-w220-source/heavy_grenade_launcher_796e9ebf.json`, no resource materialization. Generator compiled, profile parsed. Repeated generate calls returned byte-identical mappings with Path write methods/mkdir and builtins.open blocked. All248 absolute Path/bytes outputs match the exclusive expected namespace:2 static parts +244 display children +1 item +1 manifest (247 pack files).

Compared all12 key poses against W180 functions extracted via AST without importing Pillow/NumPy: sample channels, both grip/part displays and articulated body elements match exactly. Checked exact.42..52 hold, seated recovery, cradle/lug phase values, interval bounds across51 positions per authored segment, and finite C1 convergence around every interior key (maximum numerical left/right slope difference.002326610015757069 at epsilon1e-7). No component overshoot. Generated native and twohand right-FP display Euler component step maximum9.617547214deg; this is an offline sampling check, not a claim about native smoothness or all possible source-chain transforms.

Verified body68 +drum28, full payload indices28..55, unchanged element dimensions and face/UV records across61 poses/both grips. Only four cradle/latch names and charging_lug change body geometry. Both endpoint records match accepted displays exactly; nonFP displays remain exact. Canonical graph guard/fallback checks cover nonFP, ADS/inspect cases, endpoints0/1, negative and overshoot; all61 threshold floats match float32(i/60). Attachment weight is1 at.20/.64 and0 at.72/.74/.81/.89/.94/1; shared attachment shift returns zero at release and recovery.

Active weapon96 +448 classic arm reserve =544. Parent-resolved current canonical alternatives have maximum236 elements; maximum with reserve is684, below1000. Full and split alternatives are not summed. Manifest records this bound as an estimate; master must count final materialized arm routes before claiming assembledBudgetVerified. All generated outputs stay in memory.

## Integration and remaining work

Pure API: `generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[absolute Path, bytes]`. Default rig `art/weapons/w220/rigs/heavy_grenade_launcher_796e9ebf.json`; default profile `art/weapons/w220/edge_transit/profile.json`. Master must install/register W220 rig/profile and materialize the returned mapping in the integrated checkout. No shared loader/runtime/registry, resources, QA, dependencies, SSD sources, live DCC, client or server changed. No children spawned; no commit/reset/stash/clean/push.

Ready candidate only. FIRST contact/clearance/framing/ADS/recovery PNG review pending. Worker remains available for the same-worker correction or justified no-change after master's FIRST feedback, then master SECOND. No native success, continuous native60fps interpolation, audio/gameplay verification, or final acceptance claimed. Whole hands generation, Gradle and game were deliberately left to master under the assigned scope.
