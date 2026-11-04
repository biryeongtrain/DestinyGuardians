# W180 Halfdan-D whole-magazine reload

Canonical identity: long ivory/silver Häkke shroud and stock, orange receiver marking,
brown grip/lower frame, narrow channel magazine, real bore/guard/stock/sight apertures.
The accepted W129 model has 114 solids and 684 explicit face UV rectangles. Preserve
all element fields, face UV, original texture and dye, geometry axes and grip endpoints.

## Source chronology and actual visual evidence

1. W30/W31 supplied default appearance reference and original FBX/diffuse research,
   recorded by `art/weapons/w123/halfdan_d/review.md`. Neutral rip diffuse alone was
   not treated as finished dye. These are appearance sources, not reload animation.
2. W129 accepted clean canonical `models/weapon_surface_w123/halfdan_d.json` and
   `textures/item/weapon/w123/halfdan_d.png`: 114 meaningful solids, face UV atlas.
3. W179 supplied whole-part render graph and rigid Rx Ry Rz composition conventions,
   reviewed in `generate_reload_w179_null_composure.py`; no motion keys copied.
4. W180 searched local research first (W48/W49/W62/W69 and W123 Halfdan art).
   Existing Halfdan timing and appearance did not contain a same-weapon reload.
   Captured [CammyCakes Gaming, Halfdan-D | Review | Destiny 2](https://www.youtube.com/watch?v=JkSdcwO-MGM),
   published 2019-08-06, inspected actual 1280x720 60fps original gameplay frames.
   5.00s is the readable HALFDAN-D nameplate. The selected 77.10-78.60s sequence
   retains its long shroud, narrow box magazine and stock. Source blue-marked paint
   and optic differ from the local canonical finish/iron sights; only motion informed
   this adaptation. Neither blue paint nor source optic is transferred.

[Comparison](comparison.png) reconstructs emitted display JSON independently with
NumPy and the existing CPU raster: three oblique cameras at common framing for
start/withdrawn/end, three separate whole-mag views, and seating rock in all four
FP hand/grip combinations. [Storyboard](storyboard.png) embeds all 17 original
frames above nearest authored poses. These are offline renders without hands,
not native screenshots or claims of exact camera matching.

## Observed mechanics versus authored adaptation

Video-relative times use sequential decoded frame n/60. MPEG-TS start PTS .016667
is not added. Scout seeks were for locating the scene; final evidence came from
sequential frame selection from the complete source, with frame indices below.

- 77.10: leaves ADS following firing; 77.20-77.30: shallow muzzle-up presentation,
  support hand comes under magazine while receiver rolls to expose well.
- 77.40-77.50: support hand grips then withdraws long box magazine downward;
  77.60-77.90: visible empty-well pause, hand/magazine offscreen.
- 78.00: replacement magazine rises from lower left; 78.10: enters well, source
  counter changes 26 to 35. This is source-only perk/magazine behavior, not ours.
- 78.20: hand braces/slaps seated magazine while receiver kicks slightly higher;
  78.30: hand moves forward beneath handguard; 78.40-78.60: hip recovery.

No separately measurable charging-handle translation is established in these
frames. `Charging_handle` stays in the receiver; no invented bolt stroke or top
sweep. Hand occlusion and screen edge hide exact magazine travel. Local angles,
grip pivot [8,8.5,8.55], phase normalization and clearance stroke are authored:
6.2 model units down, .65 lateral and .65 forward at maximum. The whole magazine
moves rigidly, without scaling, disappearance or spinning. Shallow lift, empty-well
pause, upward insertion and positive seat rock distinguish this Halfdan adaptation
from W179's steep upright energy-cell sequence. No recovered rig/bones or hand IK.

Magazine_neck, Magazine_body, Magazine_floor and Magazine_heel are the four
adjacent overlapping solids forming the intact moving magazine. Well/strap,
charging handle, trigger guard, grip and all other elements remain receiver.
Every canonical element occurs once: 110 body + 4 magazine = 114 emitted cubes;
0 adapter triangles, 0 additions, assembled total 114 <=1000. Full versus split
are alternative representations and are not double-counted.

## Product graph and invariants

`destiny:weapon_reload_w180_halfdan_d/halfdan_d` has 21 samples per part/grip,
84 display-only children + two static geometry templates. Both
firstperson_righthand and firstperson_lefthand are supported for native/twohand
using rigid grip compensation and unchanged scale. Exact accepted displays at
samples 0 and 20. FP-only graph uses float1 progress and flag0 twohand; canonical
ADS/inspect mode cases precede reload. Negative progress and all nonFP contexts
use exact canonical graph. Existing hand_animation_on_swap=false preserved.

Existing 33-round magazine, reload44 ticks, 400rpm/cadence3 ticks, burst1, ammo,
reload/perk clocks, audio, ADS and inspect are untouched and pinned. Source
35-round counter is not a local behavior requirement. Only exact 94 owned paths
are returned. Master must admit graph in central routing; worker edits no shared
runtime/client/registry/docs or sealed QA and makes no new third-person claim.

## Reproduce and focused validation

Use the bundled Pillow/NumPy Python; set PYTHONDONTWRITEBYTECODE=1. The generator
requires external original frames/video/info at `--reference-dir` (default
`/private/tmp/w180-halfdan-d-report`), or an archived copy of the same inputs.
This leaves source media/logs outside the 94 exclusive product paths. Manifest
stores original hashes, chronology, observations and authored keys.

```
rtk proxy env PYTHONDONTWRITEBYTECODE=1 /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/generate_reload_w180_halfdan_d.py --verify
rtk proxy env PYTHONDONTWRITEBYTECODE=1 /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/qa/test_reload_w180_halfdan_d.py
rtk proxy python3 /private/tmp/w180-halfdan-d-report/run-java.py
```

Java uses JDK25 at `/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home`,
cached actual Minecraft 26.3 CuboidModel parser, ItemModels codec and ItemTransform/JOML
with representative samples, both grips and left mirror. Dependency path is isolated:
ORG_GRADLE_PROJECT_gcb_server_dir=<worktree>/libs/gcb-server. No full gate/build.
Current execution counts and failure history live in the private report.

## Master native scenario checklist (all pending)

- Admit the exact graph/catalog id `halfdan_d`, float1 progress/flag0 grip;
  exercise existing clock/ammo lifecycle through master-owned routing tests.
- Both FP hands x both grips: first/last hip match; muzzle-up framing; neck/body/
  floor/heel move together; visible clear well; approach/seat without guard/near-plane
  clipping; positive seating rock and forward recovery. No detached floor/duplicate mag.
- ADS and inspect during positive progress select canonical branches; negative
  inactive uses canonical. Check normal ADS sight picture and optic visibility.
- Completion, cancellation, swap/equip, death and disconnect restore canonical
  presentation; unchanged 33 rounds/44 reload ticks and perk behavior.
- Listen to reload audio in native session and check alignment with local existing
  timing. Offline captured source is video-only; no listening verification claimed.
- Representative third-person observer and GUI/ground/fixed/head use accepted
  presentation; no new third-person reload animation is claimed.
- Briefly observe 10-20 held displays for visible breakage/stutter. Native quality,
  actual sound, hand clearance and performance remain unverified until master runs.

## Preserved research/authoring failures and limitations

Web search did not locate a usable YouTube result; direct ytsearch found this source.
Initial scaffold failed before product writes because a guessed W153 Halfdan sight
path does not exist; corrected pins to actual canonical paths. Full traceback reason
retained in private failures.md. Downloader warned of no JS runtime and MPEG-TS in
MP4 container; format311 completed and ffmpeg decoded it sequentially. ffmpeg's
single-PNG filename warning did not prevent written images. No failed reference
format downloads were attempted. All commands/logs/research stay private; no CU,
Vision, live DCC or game process was used.

## Original reference hashes

| Seconds | Decoded frame n | Original PNG SHA256 |
|---|---|---|
| 5.00 | 300 | `8d44e4e08e507ec274baeaae38f81161a922f28d0d9ca8386b40b02ee7d14f1b` |
| 77.10 | 4626 | `95c68f6ec140171f9bb006989ded67b2155773434201f0536416cab29ed882c5` |
| 77.20 | 4632 | `be0ff600c7f513dabfab464b31945de3489cb346e06c6069362b29435b6da130` |
| 77.30 | 4638 | `637ce617023b79c34bce525202610c2ba6ce9465a517281a4c66486697969ab1` |
| 77.40 | 4644 | `b752107d218ecf0b17846528405ccc124d58d74e26d483decce241f218266b2a` |
| 77.50 | 4650 | `b9c34dee040d200460e4f7e7caf20f19e06a594c2afca976dbf622267bfeae22` |
| 77.60 | 4656 | `b4118a450afd9a82f8b1e4a6f5e050b8c863dddc49653c754345bfe27464bd5a` |
| 77.70 | 4662 | `f4d5b94cd1ab4bab6767a5a2a11fee5ab77bb5bdc2c31aadb25ced08b8f14b9e` |
| 77.80 | 4668 | `e906457c93aff358e52e6222464925149fba7bb599fa924d3a9f43d79cacff44` |
| 77.90 | 4674 | `27ee9639f59feddda5429b6997b48fc9cf10cecd2a8bf47fc3814ee92a6d0dad` |
| 78.00 | 4680 | `42152f603c950b433adbccd899a98ea97fe306a35c2d7d3bd68154f749b941e9` |
| 78.10 | 4686 | `70d36128b1013fb49bac0b56653851245734a93d3b5943b738db7f3e56c5e2f1` |
| 78.20 | 4692 | `31ab81e82005f88083bf791842e49b299d7fb5044e5eee17b509abef768637bd` |
| 78.30 | 4698 | `702c58958a47b1df9becbba08574a0c1df13f32d21be1c1a3635b78e85b94fbb` |
| 78.40 | 4704 | `11827b868754d9e2d62e7766564eea0af35e449b4f5ad583f51d42fa645c057e` |
| 78.50 | 4710 | `78bda6938258db6519ed8a855db88b04b24053a1f59fd55c6a9cdabe9d7865d7` |
| 78.60 | 4716 | `58ebbd0db196459100b0b156b400548202fcafb058e1bbe9db40b09fdab17fa7` |

halfdan-reference.mp4: SHA256 `e772e2bcbde5ae40c68b88dae41d2a775b998d4cde9298ff8113e12d197947b9`.

halfdan-reference.info.json: SHA256 `5179dfa611057b1053862e4ae9a92e013419c4ac427577be69cfb445e7e909a3`.
