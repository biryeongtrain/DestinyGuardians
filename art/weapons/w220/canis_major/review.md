# Canis Major W220 — ready candidate, FIRST review pending

This is the new Canis route, using original class action `80A8A104` from
`heavy_grenade_launcher_796e9ebf`. Master evaluated the original Blender in a
separate read-only Blender 5.4 Alpha session, sampling frames 1..142 at61 poses.
Worker read `source-review.json`, `source-handling-evidence.json` and
`source-selection-review.json` in `/private/tmp/destiny-w220-source`, and opened
the actual `sheets/heavy_grenade_launcher_796e9ebf-80A8A104-upper-chain.png`.
This is not an independent worker Blender evaluation. The evidence has only an
armature, no Canis weapon mesh, camera or finger IK. Action104 provides original
carrier and arm motion; the following mechanism is authored calibration.

## Own geometry and mechanism

The W123/W149 Canis design has101 elements. Preserve every element, rotation,
texture reference, face UV and detail. No shaft, round, mesh adapter, replacement
texture or borrowed Edge geometry is introduced. Preserve the violet covers,
long silver etched tubes, offset lobed black drum, Greek-key belt, gold rims,
two hanging grips, trigger opening and irons. The Ace/Izanagi study informs
semantic solids and UV preservation, rather than a new element-count target.

| Part | Canonical indices | Elements | Treatment |
| --- | --- | ---: | --- |
| body | complement of the three moving groups | 66 | Exact canonical display; fixed bosses65/67, rear tubes72..75, grips82/84 and latch root100 remain here |
| magazine | 36..63 | 28 | Whole drum: core4, lobes8, etched belt8, rear gold belt8 |
| cradle | 64,66,68..71 | 6 | Both side arms and their lower crossbar move as one assembly |
| latch | 99 | 1 | Blade only; its root remains fixed |

The drum axis/anchor `[8.84,10.15,1.815]` comes from drum_core36. The two gold
fixed bosses65/67 give the X hinge line at `y=9.42,z=-1.34`, midpoint
`[8.84,9.42,-1.34]`. Root100 supplies latch pivot `[8,13.68,13.53]`.
Pistol grip82 has origin `[8,8.66,7.8]`; existing W201 right/left palm contacts
remain exactly `[8,8.65,7.8]` and `[8,8.6,-3.25]`. Existing left drum contact
`[5.45,10.05,1.8]` and its rotation also remain exact.

Blade99 opens32 degrees about root100 by .06. The cradle folds down85 degrees
by .16 and holds until .66; this clears its rear crossbar from the lateral
exchange path. Authored drum first drops2.9 units by .19, then moves rearward
.9 by .23 to pass behind the fixed front bosses. It travels8 units to its own
left for the exchange, holding .30..40, aligns laterally by .58, moves forward
by .60 and seats by .62. Cradle closes .66..75; latch closes .79..84; all parts
then hold their exact rest transform. No authored body tilt/translation is
added: master replays the original source weapon bone once.

The own-geometry opening calculation puts cradle Z bounds at
`[-2.308,-1.100]` when open85 degrees. Fixed bosses end at `z=-1.005`; the
authored drum front at rearward offset .9 is `z=-.85`, leaving .155 units
behind those bosses before lateral travel. Lowered drum top is `y=10.47`,
below receiver rail80 at `y=10.69`. These are bounded authored-path checks,
not a native collision or full source-attached clearance certificate.

## Hand and source integration

Use left handling, `partHint=magazine`, `policy=magazine`, action104 and window
`[.20,.25,.50,.58]`: blend on during .20..25, hold to .50, release by .58.
Only the whole detached drum receives source-palm translation attachment.
The gun-attached cradle and latch stay on their authored pivots. Release
precedes .62 seat so subsequent recovery cannot pull a seated drum away.

The source left wrist has substantial excursions: master measured maximum
32.6398 model units relative to weapon; right wrist is effectively fixed.
Consequently integrated drum translation during attachment follows that
source wrist, superseding the authored fallback exchange translation. Do not
damp or retime the chain, stretch arms, hide support or add camera offsets to
mask discrepancies. FIRST must assess pickup, possible cradle/body crossing,
drum contact through the source excursion, release/seating, latch readability
and recovery. Existing framing effective profile is identity placement with
rightWristRoll15; retain it with sourceFullChain/keepMeshSupport true and
hideSupportAtRest false. Shared W220 loader/routing integration belongs to
master and is not modified by this worker.

## Lightweight verification

Pure stdlib generator returns494 absolute-path byte values in its exclusive
namespace: four part models,488 display children, one item and one manifest.
Import/generate do not write; scratch rig override reads the fresh61 source
samples. The assembled candidate has101 weapon elements; four112-element arm
reserves give549. Parent-resolved current canonical alternatives have a maximum
231 elements, so the conservative maximum with that same reserve is679/1000.
Alternatives are counted independently. Final materialized arms/routes remain
master's measurement; `assembledBudgetVerified` stays false.

Checked deterministic generate, complete exclusive output mapping, JSON
finiteness, exact101-element/UV partition and all61 progress thresholds encoded
as exact float32(i/60). Checked both native/twohand grips and both FP contexts,
unchanged nonFP displays, exact endpoint displays/routes, canonical inactive/
overshoot fallback, and ADS/inspect precedence. Checked authored key values,
bounded PCHIP channels, C1 join derivatives, fixed cradle pivot, hold phases,
seat/rest and invalid progress rejection. No whole hands generation, Gradle,
game, live DCC or native rendering was run by worker.

61 discrete poses do not prove native continuous60fps interpolation. Sound,
ammo, gameplay and duration inputs are read-only and unchanged. Native
visibility/contact success is unclaimed. Await master's FIRST images and
feedback; same worker corrects or explains a justified no-change, then master
performs SECOND before final acceptance.
