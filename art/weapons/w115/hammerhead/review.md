# Hammerhead W118 / R5 source drum contour and seams

## Narrow product change

R4 is frozen inside `design.json` and remains a historical comparison, not rewritten QA. Native W117 `hh-twohand-hip.png`, `hh-native-sample-14.png`, and `hh-ads-sample-08.png` were inspected read-only. Their coarse drum endcaps motivated this change. R5 replaces only the192 sparse alpha triangle cards of original cap components45/46/47/48 with216 explicit, named, source-fitted opaque rotated shell cuboids. Each cap has18 crossing flat-face strips,18 bevel panels and18 outer-rim panels. Shapes use the actual irregular original36-point rings, pairing circumference edges for rim/bevel panels, not an invented ideal circle. The flat cap strips retain18 opposing source-edge pairs. Steel material comes from the existing clean source-derived palette; it is not nearest-point ripped-albedo projection.

All863 existing R4 cuboids remain geometrically identical. Body and cover element arrays, all non-cap magazine elements, component34/35 shoulder cards, belt links, source bones, source272-component /25,499-triangle ledger, original frame and W114 cover hinge are independently retained. No body simplification, giant-box burial, hidden-face culling of old anatomy, source deletion, registry/animation change or triangle-only broad-panel regression was used. The rightward ADS belt extension is original Bullet1..8 anatomy and remains rigid.

## Counts and native representation

| Part | Cuboids | Alpha right-triangle cards | Elements | Emitted faces |
|---|---:|---:|---:|---:|
| body |624|0|624|3744|
| magazine |312|250|562|1508|
| cover |143|0|143|858|
| total |**1079**|**250**|**1329**|**6110**|

Review caps remain2048 elements /6144 faces:34 face slots remain. Face counts are authored/emitted faces, not measured on-screen visibility, draw calls or performance acceptance. The216 new shells have positive .002 inward depth with opaque north/south faces only; unused lateral sides are internal shell edges. Their two material faces preserve source visibility from both sides without triangular alpha. Existing body/cover/hardware cuboids still emit all6 faces. Native geometry uses only supported cuboids and Rz*Ry*Rx Euler rotations; no raw mesh schema. BB keeps all6 editor face slots including disabled `texture:null` slots and embedded texture, with W118 R5 name/groups/pivots.

The1024 atlas is byte-identical to R4:8 source-derived materials,128px islands,4px extruded gutters. Source triangle cards remain only in curved shoulder components34/35. Texture is unchanged, not reblurred to disguise geometry.

## Unrelaxed readiness and limitations

Strict readiness **3/3 PASS**: global bounds/sight within.02, every original component envelope within.02, and independently evaluated all272 source-component vertex-to-emitted-surface p95 within.35. Actual global extrema equal the original frame; maximumY remains14.625413301170328. Maximum component protrusion is **.005390083** at47; no component exceeds.02. Maximum coverage p95 remains **.291418783** at curved feed34. New cap p95 values45/46/47/48 are **.030543/.030544/.030165/.030165**; their maximum output-to-source sample deviation is.027815. This is a bounded approximation, not exact topology or continuous area-weighted coverage. Old feed35 output-to-source maximum.496893 remains disclosed in manifest. No thresholds were relaxed or distance checks removed.

Frozen R3's69 envelope failures,6 coverage failures and excess sight height remain negative controls, with independent distance rechecks. Both historical comparisons `r3_iou > r2_iou` and `r4_iou > r2_iou` remain for every whole-model view, alongside `r5_iou > r2_iou`. R4-vs-R3 profile/ADS missing-pixel regressions remain historical evidence:3200->3221 and511->524. They are not erased by R5 improvement.

## Actual offline image review

Worker personally viewed the final generated4560x2500 `comparison.png` and enlarged R4/R5 cap crops. Six revisions raw/R1/R2/R3/R4/R5 have6 matched whole-weapon views, including HIGH/TOP, ADS and open-cover/feed-removed. Two additional cap-only rows compare source/R3/R4/R5 axial and oblique surfaces. R1/R2 cap-only cells explicitly say component identifiers differ; their whole-model images remain above. No copied QA screenshot is presented as R5 evidence.

The final disks are substantially rounder and cap/rim surfaces continuous rather than the old coarse octagons. Receiver/stock/cover remain identical geometrically. Cap-only IoU improves **.917370->.973896 axial** and **.927889->.984708 oblique**. Eroded-source interior missing pixels improve **4664->15** and **2320->16**. These remaining pixels and18-facet bevel shading mean **not seamless/exact/final**. Whole-model IoU improves in all6 views: **.926645/.966409/.968944/.962099/.958628/.954486**; source missing pixels decrease in each. ADS missing pixels524->343. Clean palette flatness and shoulder faceting remain apparent; no aesthetic-final claim.

An initial one-sided36-facet shell draft failed the oblique check (IoU.549172, interior missing27517). Enabling cap back faces alone left the oblique IoU.926079. Those drafts were rejected, not exported. Final18-facet double-faced opaque rim/bevel shells resolve that exposed-back omission while staying below the unchanged budget. No speculative further geometry expansion followed final visual review.

## Regression and handoff

Core suite:31 tests, including original pins, independent Euler mapping, all272 component distances/envelopes, ledger and part disjointness, cap ring provenance, dense cap-center rays, opaque UV/gutter tests, frozen R4/R3/R2 negative controls, BB editor slots and historical comparative assertions. Core runs two complete read-only deterministic `--verify` calls and checks unchanged bytes/mtimes. Final documentation/hash refresh receives one further read-only deterministic verification. Exact run results are in the W118 worker note and handoff.

Normal export: `/private/tmp/destiny-w118-hammerhead-export`. `manifest.json` lists the exact12 owned paths and11 non-self hashes; external export inventory holds baseline/after hashes including manifest self hash. Unchanged atlas is intentionally omitted from the changed-file bundle because main already has its pinned bytes. No main or sealed QA write, GUI/native/Gradle/DCC run, shared compiler/converter/Java edit, child process delegation, Git history mutation or large source copy.

Native R5 art/performance acceptance is **unverified and master-owned**: actual cap filtering/overlap/shading, HIP/ADS roundness and hand alignment, reload/cover/rigid belt readability, vents/bore/aperture topology, Blockbench reopening and performance. Same-material coplanar cap strips overlap;18-facet bevel/rim approximations and small residual seams require the single shared native review. This scoped contour improvement is not animation completion or default-promotion approval.

Final targeted results: **31/31 core PASS (52.497s),3/3 strict PASS (6.472s)**, including2 read-only deterministic regenerations. First core historical-cap lookup error is retained in worker note; correction preserves independent frozenR3 negative checks. Final doc/hash-only refresh receives standalone --verify before normal scoped export.
