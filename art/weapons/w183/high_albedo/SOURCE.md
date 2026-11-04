# W183 High Albedo reload source and authorship

Original gameplay: [Is The High Albedo Good?  (Destiny 2: Beyond Light)](https://www.youtube.com/watch?v=vBiSPlhfkMI), DrDestiny, 2020-11-22.
Retained full video: `/private/tmp/w183-albedo-report/review.mp4`, format298, 1280x720, **60/1fps**, video timebase **1/15360**, start0. Source PNGs are extracted with ffmpeg frame select and `-fps_mode vfr`, no frame interpolation. Frame index is zero-based; timestamp = n/60. Clip/metadata/each actual PNG SHA256 and exact extraction argv are in report and manifest.

Same-weapon identity: inventory at frame240 /4.000000s explicitly says HIGH ALBEDO and shows its orange muzzle brace, red open barrel cage, blue receiver/top bridge, orange reservoir and lower knurled silver cylinder. All persist in the following first-person reload. These match canonical W143 art. No API item hash, bone data or exact roll was recovered from pixels. The alternate Ibetonme clip downloaded during scouting has a different shader; its sight/paint are not used for product output.

## Actual sequence inspected before implementation

| Source frame | Time(s) | Nearest authored p | Observed evidence |
|---|---|---|---|
| 240 | 4.000000 | 0.00 | Inventory explicitly HIGH ALBEDO; orange muzzle brace, open red cage, blue receiver, orange reservoir and lower silver cylinder match canonical base appearance. |
| 1956 | 32.600000 | 0.00 | Before reload: one remaining round in HUD; exact phase boundary is authored at32.6667s. |
| 1968 | 32.800000 | 0.10 | Muzzle lift begins while right hand keeps pistol grip. Under-barrel cylinder and carry bridge remain attached. |
| 1980 | 33.000000 | 0.20 | Strong diagonal muzzle-up presentation; support forearm reaches toward pistol grip base. |
| 1986 | 33.100000 | 0.30 | Support hand covers grip-base release; no separate cylinder opening or barrel break. |
| 1992 | 33.200000 | 0.35 | Support hand drops below grip; outgoing path partly hand/screen occluded. |
| 1998 | 33.300000 | 0.40 | Incoming long rectangular magazine is visible below grip in support hand. Canonical asset lacks this shaft and contains only magazine_base. |
| 2004 | 33.400000 | 0.50 | Magazine insertion toward grip; tip/seat boundary occluded behind fingers. Carrier remains canted up. |
| 2016 | 33.600000 | 0.60 | Support hand has left grip; canted receiver held briefly. No moving bolt visible. |
| 2028 | 33.800000 | 0.75 | Carrier rolls/lowers inward; HUD now30. Source capacity/perk is not a gameplay input. |
| 2040 | 34.000000 | 0.85 | Support hand sweeps across upper/rear receiver, obscuring exact manipulation. No individually resolved bolt travel is animated. |
| 2052 | 34.200000 | 1.00 | Weapon returns to aiming presentation. Canonical hip endpoint authored to local product transform; source continues aiming. |

Reload action bounds are approximately frame1960..2052, **32.666667..34.200000s** (1.533333s). This observation is mapped to local normalized progress; local reload remains **36ticks**, magazine27, RPM491, burst3, cadence7.333333333333ticks, burst spacing1.333333333333ticks, original sounds and ammo transfer. Source HUD30 is not an input to capacity/timing. Source enters aiming; p0/p1 use exact canonical hip transforms.

## Canonical split and authorized reload-only whole magazine (revision2)

Canonical `models/weapon_surface_w123/high_albedo.json` stays unchanged: **100 cuboids**, no triangles. **Body:99**, zero-based indices0..90 and92..99. Original magazine index91 `magazine_base`: bounds[7.325,5.81,7.89]..[8.675,6.13,9.45], origin[8,5.97,8.67], X=-17deg. Grip core/heel, backstrap, cylinder, cage, sight and selector remain fixed. All100 original elements/faces/UV/default dye reconstruct exactly in original order; no canonical file or atlas is edited.

**Revision1 was rejected:** the source frame1998 /33.300000s clearly exposes a long magazine shaft, while canonical index91 is only a baseplate. The initial baseplate-only attempt was not a completed whole-magazine reload. Its export, reports, tests and screenshots are retained in `/private/tmp/w183-albedo-report/superseded-baseplate-only/`. Master then explicitly authorized source-backed **reload-only** shaft geometry, without canonical edits.

Revision2 adds **11 reload-only cuboids** to the magazine parent: one dark rectangular shaft core and ten shallow reinforcing ribs (three longitudinal plus two cross ribs on each broad face). Source frame1998 shows the long dark rectangular body with that rib structure; hand covers its lower/near section. The symmetric hidden broad face, exact dimensions and rib thickness are authored interpretations, not extracted original mesh. Core bounds before rotation are[7.50,6.08,8.09]..[8.50,10.12,9.25] (**1.00 x4.04 x1.16**, broad-side aspect3.483). These dimensions fit the existing grip and baseplate and give an exposed long shaft, without pretending source projection measures its exact length.

The shaft and ribs rotate around the **same [8,5.97,8.67], X=-17deg anchor** as original magazine_base, sharing one parent and one rigid display transform. Mag parent: **12 elements** (original baseplate+11 shaft/ribs); active assembly **99+12=111**, below1000. All added corners are enclosed in the canonical grip/heel/baseplate solids at seated offset0. No independent casing/bullet/bolt/hand geometry, scale fade or duplicate magazines.

Core faces reuse canonical magazine_base upper-face UV[10.140625,4.203125,10.65625,4.796875]. Ribs reuse an interior existing steel-barrel atlas patch[.3125,.25,.4375,.375]; no texture/paint/default sight file changes. The dark broad core and restrained steel ribs correspond to the visible source magazine rather than borrowing the alternate-video shader.

**Endpoint guard:** range samples0 and20 return a deep copy of the exact canonical full item graph. Thus exact p0/p1 (and p>=1) draw the untouched **100-element canonical geometry**, not the added shaft. Display children0/20 still retain exact canonical transforms for all hands/grips, but their shaft parents are unreachable through the item graph at endpoints. Negative, ADS/inspect and nonFP also remain canonical. Intermediate insertion hides the shaft inside the existing grip.

## Authored numeric motion

Pivot[8,8.65,7.85] is canonical grip_core origin; magazine anchor[8,5.97,8.67] is canonical baseplate origin. Release follows the -17deg grip axis [0,-0.956304756,0.292371705] before the small authored lateral exchange clearance. Pose keys below are authored interpretations; these are not extracted camera transforms, animation or bones. `p / carrier RxRyRz(deg) / display shift(model units) / magazine local offset(model units)`:

```
0.00   0,0,0       0,0,0         0,0,0
0.08  18,2,-3      .12,-.12,0    0,0,0
0.20  42,10,-16    .35,.18,.12   0,0,0
0.30  46,16,-29    .45,.25,.15   0,-2.8,.856
0.40  44,17,-31    .45,.25,.15   -.50,-5.2,1.590
0.50  43,17,-30    .45,.23,.15   -.16,-2.3,.703
0.60  41,18,-27    .45,.20,.15   0,0,0
0.70  33,22,-33    .38,.10,.10   0,0,0
0.80  22,25,-40    .30,0,.10     0,0,0
0.86  26,16,-24    .22,.06,.05   0,0,0
0.92   9,5,-7      .10,-.02,0    0,0,0
1.00   0,0,0       0,0,0         0,0,0
```

Cubic smoothstep interpolation sampled21 times at i/20. Observed diagonal lift/cant, grip-base release, low incoming magazine, insertion and inward roll/rear-hand sweep determine order. Exact hand-occluded release/seat, clearance, pivot and phases are authored. The upper/rear support-hand sweep hides the mechanism; **no separately resolved bolt travel is animated**. Carrier accent reflects the visible weapon response only. This trajectory was authored from the High Albedo sequence; W182 IKELOS infrastructure was reused only for matrices, display children, guards, CPU textured renderer and test patterns.

## Integration and verification limits

Item model `destiny:weapon_reload_w183_high_albedo/high_albedo`: floats[1] normalized0..1, boolean[0] existing grip. Both firstperson hands; string[0] ADS/inspect, negative progress and every nonFP context fall back to exact canonical graph. Exact0/1 canonical full graph plus endpoint transforms and scales. 2 geometry parents +84 display-only children +1 guarded item =87 pack files. Master owns shared registry/routing/admission/runtime/HUD.

comparison.png: offline textured canonical side/obliques, representative progression, grip detail, both hands/grips. storyboard.png: actual retained frames above independent offline poses; different camera/FOV, **not** native screenshots or hand-contact evidence. No native success, handIK, new third-person reload, listening or performance result claimed. Whole represented magazine now includes the source-backed shaft under explicit authorization; exact original mesh fidelity is not claimed. Native pack/hand contact/lifecycle/audio/stability remain pending master.
