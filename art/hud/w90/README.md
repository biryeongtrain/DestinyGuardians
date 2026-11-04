# W90 critical wash candidate — offline only

Two concrete, independently named item asset banks address the inner ellipse in
[W89 hp-1-0](../../../docs/qa/2026-10-25/w89/native/frames/hp-1-0.png).
These files are inactive prototypes; the parent owns selection, integration and Vision.

- `prototypes/local2x/assets/destiny/`: eight 1024×576 RGBA textures, their mean-mip metadata, two-sided plane models and CMD-tint item descriptors. Names: `incoming_w90_local2_0..7`.
- `prototypes/local4x/assets/destiny/`: equivalent 2048×1152 bank, names `incoming_w90_local4_0..7`.
- `generate_softness.py`: deterministic generator with source-preservation, peak, centre, monotonicity and filter-survival checks; writes only within this directory.
- `manifest.json`: source evidence hashes and all generated output hashes; no production pin edits.
- `offline/metrics.json`: all eight frames at both scales, coverage and discontinuity, 144 filter-stress cases.
- `offline/overview.png`: bright/dark schematic comparison; cutoff before final panel shrinking.
- `offline/sampling-1708.png`: nearest/bilinear raw-alpha sampling before cutoff at 1708×960.
- `offline/filter-stress.png`: resolved-coverage benefit beside mean-minification failure.
- `offline/alpha-profiles.png`: top-centre band profiles and loss of softness after minification.
- `research/collect_evidence.py`: exact cached26.3 ZIP and `javap` evidence collector; writes `research/` only.
- `research/evidence-manifest.json`, `research/javap-*.txt`, `research/vanilla-*.fsh.txt`, `research/library-paths.txt`: version/hash and source evidence.

Every preview is **OFFLINE / NOT NATIVE PROOF**. The generator uses synthetic
backgrounds, never paints over the already-washed native screenshot.

Reproduction, from the repository root, using the existing Pillow13 environment:

```sh
rtk proxy /tmp/destiny-hud-venv/bin/python art/hud/w90/generate_softness.py
rtk proxy /tmp/destiny-hud-venv/bin/python art/hud/w90/generate_softness.py --verify
rtk proxy python3 art/hud/w90/research/collect_evidence.py
```

The texture method preserves nearest-upscaled W89 alpha pointwise, including
values below26 in dot holes. Fixed per-source-cell reflected/rotated Bayer ranks
promote selected tail samples to32; original26..31 samples are promoted to32.
The coverage probability below26 is `a/26`. Above31 the original alpha is exact.
The centre and all original zero-alpha pixels stay clear. The eight peaks stay
77,88,101,112,125,136,149,160. There is no temporal randomization.

4× gives the smoother resolved macro ramp; 2× is a lower-memory comparison with
more visible quantization bands. Neither is certified for production. Filtering
can restore a hard contour, and fragment-scale dither jumps are32 rather than
the old26 minimum jump. Both deliberately add opacity in the former clipped
tail and slightly brighten the shoulder; this is not an opacity reduction.

The exact feasibility findings, measurements, limits and bounded native review
matrix are in [hud-softness-notes.md](../../../docs/qa/2026-10-25/w90/hud-softness-notes.md).
