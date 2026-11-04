# W113 first-person swap authoring

Ten new directional pairs among Austringer, Beloved, Ammit AR2 and The Recluse;
the original Austringer <-> Beloved graphs, children and reports stay byte-identical
in weapon_swap_w91. All ten additions live in weapon_swap_w113.

This is an explicitly authored approximation of swap motion, reusing W91's audited
pure smoothstep and matrix helpers via runpy. It is not extracted or measured
original-game animation, hand motion, bones, frame interpolation or invented IK.
The current detailed W30 parent models, face UVs, textures, editable bbmodels,
default display transforms and item graphs remain immutable inputs. Their source
catalog archive provenance and byte hashes are recorded in manifest.json.

Every child has only parent and display. STOW renders actual outgoing geometry;
READY renders incoming geometry. Each phase has 21 samples at .05 spacing.
STOW 0 and READY 1 exactly match the rendered weapon's native/twohand HIP display.
Only first-person contexts animate. Non-first-person child contexts preserve the
actual rendered source carrier variant; the item wrapper sends all GUI, ground,
fixed, head and third-person contexts directly to the exact incoming item graph,
including ADS/inspect/default fallbacks and original metadata.

Float slot 5 selects STOW 0..1 or READY 2..3. Thresholds are sorted and audited in
float32 with the existing positive sub-.001 binding offsets. Values below 0 use the
incoming graph; 1..2 holds STOW's final sample; above 3 holds READY's exact HIP.
Flag 0 is the CURRENT incoming wire carrier, not the outgoing weapon default grip.
Both hands and both carrier branches are audited using actual crossbow correction
(-.641864 translation and 10-degree yaw). Vanilla performs left-hand reflection;
no extra mirror or hand IK is introduced. Scale and source geometry stay intact.

Runtime support is exactly the twelve distinct permutations of these four IDs.
Old two routes use W91, new ten use W113. Binding admission, owner/stack/level
identity, float restoration, cleanup and cache offsets are unchanged. Handling
alone owns phase durations, zero-duration transitions, firing and ammunition.

Generate: rtk proxy python3 -B scripts/generate_swap_presentation_w113.py
Read-only audit: append --verify. The 858-path worker allowlist is exact; this
generator writes only 853 asset/report files within it. Unknown output files are
rejected without deletion. Verification reconstructs bytes and checks immutable
source hashes and all output bytes without creating directories or writing files.

asset-samples.json lists all 840 children, current carrier flags, selectors,
actual parents and both first-person displays. Central native scenarios: all ten
new directions plus both W91 controls, both hands and carriers; STOW 0/.55/1 and
READY 0/.8/1; GUI/third-person/ADS/inspect fallbacks; interruptions, death, world
change, disconnect, donor handoff, stack copies and optional grip changes. Check
framing, occlusion and exact HIP continuity. No native/app/framebuffer acceptance
is claimed here; the master owns centralized compilation, JUnit and game testing.
