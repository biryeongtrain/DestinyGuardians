# Kinetic first native Vision review and correction

Reviewed the master's actual first `hip-0`, `third`, `ads-end-0` and all five `reload-valid-0..4` PNGs for Crimson, Thorn and Outbreak Perfected. Per-weapon `native-review-first.json` records all eight input-image hashes. The 1K final-pack filter is master's output stage; this fix preserves every authored 2048 × 512 atlas byte.

The actual confirmed ADS endpoint placed every sight down/right of the screen center. Original x translation -5.6 leaves +0.21m at the camera, and original y -2.8 leaves roughly -0.4m at the front sight. The correction uses the accepted W327 camera basis and each owned sight anchor, rather than shifting geometry to mimic the wrong camera. Both first-person contexts and all 21 aim stages are regenerated together with their contact-bound W204 hand leaves.

| Weapon | Pitch | ADS translation | Eye-to-sight |
| --- | ---: | --- | ---: |
| Crimson | 2° | -8.96, 3.15752505, -4.10454469 | 1.75m |
| Thorn | 3° | -8.96, 2.96518665, -4.97917281 | 1.90m |
| Outbreak | 2° | -8.96, 2.76594974, -0.47341818 | 1.10m |

The small positive pitch keeps rear roofs beneath the aim ray. Thorn's existing green bead sat below the forward roof; it is lifted 0.51484674 model units above that roof without changing its UV. Outbreak's opaque narrow holographic slab blocked an aimed ray. It is replaced with four physical open-hood rails and a tiny reticle, sampling existing constant-color atlas islands. Outbreak now emits 766 weapon elements across 46 closed solids; Crimson remains 736 and Thorn 849. Prior R2 offline geometry PNGs and render-evidence hashes remain preserved as earlier evidence; they precede these local sight changes.

Outbreak's native third-person capture points nearly vertically while the player uses the two-hand stance. Its -Z-forward basis matches the accepted W327 Krait. Its third-person display therefore receives the accepted compensated rotation `[5.729578,-17.188734,0]`, translation `[0,-2,2]`, scale `.7`. The hand-cannon captures show the normal lowered single-hand stance, which is retained.

The valid reload set shows the support hand following the moving chamber/magazine and frames 3/4 returning to hip. The tutorial overlay obscures portions of the raised barrels; these captures do not prove complete source-motion fidelity or all finger contact. Source actions remain absent, so reload motion remains authored approximation. No speculative reload change was made.

Targeted checks pass: all current graphs and references, bounds/UVs, original source/atlas SHA, exact reload return endpoints, and sight projection to camera `(0,0,-distance)` within 1e-8m. Exclusive stale aim-hand leaves are removed. No shared HUD/registry or global runtime edits were made. Native second Vision remains required to confirm visible centering, a clear sightline, hand contact and corrected Outbreak third person.

Reproduction: after `kinetic_quality_r2.py`, run `kinetic_native_fix.py`, `kinetic_quality_finalize.py`, then `kinetic_native_check.py` in the Pillow environment. Do not run the older all-plane R2 checker as the final binding gate: Outbreak's new rails are native cuboids, and the preserved R2 offline proof intentionally names the earlier geometry.
