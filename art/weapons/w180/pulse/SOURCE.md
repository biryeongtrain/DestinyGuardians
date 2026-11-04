# W180 pulse readability

## Original reference and observed behavior

Original gameplay reference: thatguyHoody, *Destiny 2 All SUPER Sounds - MEGA SHOWCASE including NEW SUPERS + PRISMATIC* (2024-06-11), [Shadowshot - Deadfall, 17:25–17:44](https://www.youtube.com/watch?v=O0uvtZMID9E&t=1045s).
The existing W34 cached contact sheets were re-inspected for W180 on 2026-10-27; the video was not re-fetched. `run/private-sources/w34/contact-action.jpg` labels 1046.8–1047.3 seconds (17:26.8–17:27.3): the caster silhouette and nearby environment brighten violet during cast/draw. At 1047.4–1047.7, bow/arrow energy brightens at release and the caster outline subsides. At 1048.1–1048.3 the first-person environment is largely unobstructed again. The wider `contact-source.jpg` shows another violet cast/bright local bow at 1057–1058.5 (17:37–17:38.5). Action-sheet sampling is about 0.1s; labels are approximate observations, not exact event timing.

These frames combine world VFX, actor lighting and camera changes. They do not identify an original screen-space corona implementation, establish an impact waveform, or measure Arc/Solar timing. The prior W34 audio's provisional impact assignment is not promoted to visual impact evidence. Cached reference hashes and copies are retained in the private W180 report, not redistributed as new product artwork.

The local problem is separately observable in `docs/qa/2026-10-27/w179/native/shader-review.jpg`: the three sustained grades are apparent, while six activation/impact pairs are hard to distinguish. W179's maintained command fixtures establish application/removal, not natural 10/4-tick timing.

## Authored local adaptation

W180 authors a broad elliptical screen shoulder and soft corona rim in the existing one-sample shader. It borrows the reference's readable peripheral energy and quick return to clear view; it does not reproduce or extract Bungie's renderer or original flash/camera behavior. Solar orange-gold, Arc cyan and Void violet are locally selected tints. The identical activation/impact shape makes impact pointwise weaker at two-thirds amplitude, rather than moving a weaker peak onto previously quiet pixels.

Only the existing `PulseConfig` fields are used: `vec4 Tint`, then `vec4 Shape`. Both kinds use Shape `[0.80, 0.12, 0.55, 0.45]`. Activation Tint.a is 0.12; impact is 0.08. Solar RGB `[1,0.60,0.16]`, Arc `[0.30,0.80,1]`, Void `[0.70,0.36,1]`. The edge ramp is radius 0.52–0.98; the broad shoulder extends to 2.5 width units from the corona radius and mixes 25% Gaussian rim. A square-root spatial response uses more of the existing light budget while preserving exact zero.

The shader computes `scene + (1-clamp(scene,0,1))*Tint.rgb*strength`, clamps strength to 0.12, preserves scene alpha, and never darkens normalized RGB. Added light per channel is at most 0.12; white has no headroom and receives zero light. The normalized central disk radius <=0.30 is exactly neutral. The screen is deliberately elliptical on wide viewports, retaining the existing normalized-screen contract.

Sampled CPU dominant-channel strengths across radius 0.70–0.98 are >=8.4249% activation and >=5.6166% impact (black-input light coefficients; actual pixel change decreases with scene headroom). Sampled peaks are 11.0663% / 7.3775%, below the 12% cap. About 66.94% / 67.06% of a 160x90 screen sample receives coefficients >=6.5% / >=4.3%. W179 covered 6.92% / 0% at those respective thresholds. This deliberate contiguous band is a product regression floor, not a claim of native perceptual acceptance.

Server lifecycle remains the existing 10-tick activation and 4-tick impact. There are no time uniforms, temporal strobes, history buffers, blur, distortion, full-screen flash, client injection, dependencies, dummy end_of_frame assets, or log filtering. No model is emitted: assembled model output count 0 (1,000 cap not applicable).

## Comparison and verification boundary

[comparison.png](comparison.png) is an **offline same-image CPU study**, clearly labeled in the image. All six rows reuse the same W179 native OFF PNG (`shader-solar-activation_pulse-off.png`, SHA256 `de322092f362bffc5d34fa2368066abf4a76741e4c39cd5bf4becef4bc43e6c9`). The original 1708x960 RGB image is resized once to 480x270, then both shaders' scalar assignments are evaluated at pixel-center UV. W179 uses preserved baseline constants; W180 uses current constants. There is no exposure change or amplified difference. Stored-image RGB simulation does not model GPU color-space details, resource loading, the active-grade stack, camera changes, or native event timing. Neither simulated column is a native PNG after capture.

Current targeted verification: **5 JUnit tests in 2 classes**, failures/errors/skips 0; **8 Python CPU tests**, failures/errors/skips 0; **1 glslang fragment syntax check**, exit 0; **7 JAR assets byte-identical** to source. The existing 2-test asset suite retains its original radius/width/light constraints and now also rejects additional sampler/block inputs. Three W180 JUnit tests use actual Minecraft 26.3 PostChainConfig CODEC (six chains plus invalid uniform-type rejection) and check the impact hierarchy. Python evaluates the shader's scalar assignments, checks the output data flow, bounded light/white headroom/neutral center, pointwise hierarchy and broad coverage. Two deliberate W179 negative controls fail the new visibility floors and are preserved. No GameTests or native GPU session were run by this worker.

Build failures retained privately: initial composite GCB identity mismatch; next invocation placed test filters after `jar` and was rejected before task execution. A private init script supplies the isolated GCB build identity; the corrected targeted test/JAR build succeeds with Java25 and the required isolated GCB path. No dependency source or shared build file was edited.

Private evidence and master native checklist: `/private/tmp/w180-pulse-report/`. Native GPU compilation, actual 10/4-tick readability, active-grade composition, HUD/ADS and camera acceptance remain pending the master's isolated session.
