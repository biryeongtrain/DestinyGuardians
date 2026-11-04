# W91 N1 — Izanagi presentation candidate

Status: implementation candidate; central compilation/JUnit/GameTest/native gates unrun.

## Ownership and delegation

L1 owns exactly:

- `src/main/java/kim/biryeong/destiny/weapon/WeaponIzanagiPresentation.java`
- `src/test/java/kim/biryeong/destiny/weapon/IzanagiPresentationW91Test.java`
- `src/gametest/java/kim/biryeong/destiny/test/WeaponIzanagiPresentationW91GameTests.java`
- `art/weapons/w91-izanagi/lead-notes.md`
- `art/weapons/w91-izanagi/native-scenarios.json`

Native child tools are not exposed to this L1. An exact-scope broker request was
reported early. Topmaster created actual native child Turing,
`01a16f6c-0581-7bb1-854d-9a16eba61b7f`: `logicalParent=W91-N1-L1`,
`spawnedBy=topmaster`, one native child. This L1 did not directly spawn it and
did not create an app task. Review: accepted after completion relay and writes
released. Close: requested from topmaster; this L1 cannot perform native close
and does not claim the child is closed until the parent confirms it.

Child owns only `scripts/generate_izanagi_presentation_w91.py`,
`src/main/resources/assets/destiny/items/weapon_izanagi_w91/**`,
`src/main/resources/assets/destiny/models/item/weapon_izanagi_w91/**`, optional
new `src/main/resources/assets/destiny/textures/item/weapon_izanagi_w91/**`, and
`art/weapons/w91-izanagi/asset-*`. Child cannot edit these lead notes or native
scenarios. Require baseline/dirty hash readback, a deterministic generator and
non-mutating audit, original79-cube/baseUV preservation, distinct locally authored
motions and a completed-charge barrel cue. Original three texture files and
`art/weapons/w84/model/source/izanagi.bbmodel` remain read-only.

Shared runtime/item router/WeaponHandling/WeaponSwapCycle/fabric.mod.json,
WeaponIzanagi and all shared README/index/journal/QA paths are topmaster-owned.
This lane changes none of them. No builds, commits, server/client launches or
user-app operations were performed by this L1.

## Runtime and item definition contract

Public API:

```java
public static final int SELECTOR_INDEX = 6;
public enum Mode { IDLE, RELOAD, HONED }
public static boolean supports(WeaponCatalog.Entry entry);
public static void update(ServerPlayer owner, ItemStack stack, Mode mode, float progress);
public static boolean active(ItemStack stack);
public static Identifier model(ItemStack stack);
public static void clear(ServerPlayer owner, ItemStack stack);
public static void cleanup(ServerPlayer owner);
public static void clearAll();
```

`supports` requires the canonical W84 exotic identity. `model` requires an active
binding and returns `destiny:weapon_izanagi_w91/izanagis_burden`; inactive callers
must follow the existing original item/ADS/scope router. Getters never bind or
mutate stacks. No saved cosmetic field or ammunition/deadline changes are added.

Topmaster provides pure public `WeaponIzanagi.honing(ServerPlayer)`: actual
Pending owner object, current level and exact current ItemStack, with normal
eligibility, and **no `now < until` shortcut**. This getter was inspected after
the parent added it. Parent calls update after accepted starts, after actual
normal/Honed commit each tick, immediately after the real charged shot, and
clears from cancellation/cleanup/server-stop. Runtime.cleanup calls `cleanup(owner)`
to retire an old held stack even if an idle cue was created without a combat State.
Mode is HONED iff actual cycle is
reloading and `honing`; RELOAD for ordinary reloading; IDLE otherwise. The helper
also checks real `WeaponRuntime.reloading`/`honing` before exposing reload modes.
IDLE binds only for `WeaponIzanagi.charge(stack) >= 2`, never for persisted slot6.

Float6 encoding, shared with asset child:

| Meaning | Written selector | Dispatch buckets |
| --- | --- | --- |
| Ordinary | `floor(clamp(progress)*20)/20 + offset` | thresholds `0,.05,...,1`; fallback at1.01 |
| Honed pending | `2 + floor(clamp(progress)*20)/20 + offset` | thresholds `2,2.05,...,3`; fallback at3.01 |
| Funded completed cue | `4 + offset` | `[4,4.01)`; fallback at4.01 |
| Inactive | Original selector restored, or absent | Never route the wrapper without a live binding |

Non-finite progress becomes0. Offset is one of0/.00025/.0005, chosen to avoid the
original slot and retired donor sample. It remains within each .05 bucket and
makes binding changes observable to packet/item caches. Child must not use an
exact equality test for4. Non-first-person reload contexts use the exact original
item definition; charged cue adds cosmetic geometry in all contexts with the
original transforms. Original pose string0 (especially inspect/scope), grip flag0, and
charged ADS float3 are preserved. Charged main geometry must follow the existing
W70 ADS path and explicit original scope pose; the barrel cue must align with
that same transform. Izanagi retains its original 3D lens fallback, not a new W45
opaque/fullscreen scope. Other original scoped snipers remain unsupported by N1.
Parent router priority is Swap > Insert > Izanagi > ordinary reload > existing
ADS/scope. No original presentation helpers are changed.

Each binding owns a single float6 snapshot (value or absence), exact
owner/level/stack identities, current mode and last written value.
No entire old float vector is restored. A foreign-owner/late donor clear is a
no-op; an externally replaced slot6 is not overwritten. If slot6 was absent and
new higher slots now exist, restoration uses inactive -1 at6 while retaining
their indices. Otherwise only slot6 is removed. Lower zero padding is retained
because another renderer may own even an unchanged zero. Flags, strings, colors, unrelated lower
and higher floats always come from the current component.

## Tests and central acceptance

`IzanagiPresentationW91Test` checks canonical identity, independent W84 source and
three atlas hashes, the actual26.3 item codec/cuboid parser, resolved model
inheritance and preservation of all79 cubes/UVs/rotations/material references,
distinct moving normal/Honed poses, charged ADS/scope/grip sight lines and exact
original rendering routes in other contexts. These tests require the child bank
and remain unrun until central integration is complete.

Seven W90-isolated GameTests use real production reload packet/runtime pathways,
real61-tick deadlines, real funded commits and an actual paid downward hitscan.
All timed callbacks are registered during initialization. `TestCleanup.register`
is installed before fixture mutation; no global cleanup, gamerule changes,
external targets, or simulated clocks. Coverage:

- normal/Honed separation, no early cue, full61-tick commit and paid-shot removal;
- skill/stow/copy/level/death cancellation and retired-generation deadlines;
- foreign-owner clear, concurrent selector/metadata changes and exact float6 restoration;
- actual exact-stack owner transfer, fresh recipient deadline, late donor cleanup;
- absent float6 with later higher slots and an external slot6 replacement;
- completed charge surviving stow and real charged ADS serialization.
- no-combat-state idle binding cleared by owner cleanup after held-stack replacement.

Topmaster must register the new GameTest class in the shared gametest
`fabric.mod.json`, execute the JUnit/asset audit and GameTests centrally, and pin
the final stopped-writer candidate before one integrated Vision batch. No test
pass, framebuffer quality, native Q/slot input, hand IK, exact Destiny animation,
new source timing, audio listening or new charge VFX equivalence is claimed.

## Reference observations

First asset review accepted all238 outputs:221 models, one item definition,
one new texture and15 asset sidecars. Independent read-only SHA checks matched
237 pinned output files and67 pinned original inputs plus the generator SHA;
the output manifest excludes its own hash. Direct element comparisons confirmed
the exact79-cube/474-UV geometry in the78+1 split and the first79 elements of the
95-cube charged model. Reviewed generator KEYFRAMES (ordinary7/Honed8 contacts),
all42 sample descriptors,50 charged model remaps, guard thresholds, two-hand
compensation code, lens/texture preservation and the three offline contact sheets.
Child reports64,512 routing cases in its validation
sidecar; this L1 did not rerun that generator audit. Parent separately reported
read-only `--verify` passing238 outputs. No required child correction remains.
Offline sheets show distinct magazine/body movement and retained detailed art;
native sight-line/brightness/clipping and codec/bake validation remain central.

Child's handoff says clear slot6 to-1 in idle. Integration interpretation:
the router never selects this wrapper for inactive bindings, so preserving an
original saved slot6 or restoring absence is correct. An inactive persistent
selector has no routing authority. Lower padding is intentionally retained.
Child guard thresholds accept every helper offset0/.00025/.0005, including
endpoint4+.0005. There is no helper requirement to overwrite unrelated float3.

L1 source review also corrected the new codec test imports to the repository's
actual26.3 packages (`client.resources.model.cuboid.CuboidModel` and
`client.color.item.ItemTintSources`). Five JUnit methods and seven GameTests are
prepared but **unrun**. Native manifest schema/required fields were inspected;
all five scenarios have planned_unrun status and null candidatePin/result.
The parent owns final immutable candidate pins and all execution results.

L1 writes released after this note. Central gate may begin after topmaster
confirms every writer is stopped and performs the brokered child close.

Read design105, W84 design99, W58 design73, W84 transaction GameTests,
WeaponReloadPresentation/WeaponAimPresentation/WeaponInsertPresentation,
WeaponCombatItem, WeaponRuntime, W90 TestCleanup and TestPlayers. No `.codegraph`
directory is present according to the supplied repository contract; CodeGraph
was skipped. Every shell was invoked through `rtk`.

Original source SHA256:
`9ae28369f80ff0f81bb7e1344ee50b618b9a2de62dcafc631287084dbe3c8f31`.
Original native base model SHA256:
`68b997c775671994621b01630b3b2d07d0423b57ab16eabb07abfc615427d342`.
Original item definition SHA256:
`aacf7db971fb5172cea6e515a105dc1f467ccf370f603504ca2ae14cd153dc4d`.
Existing reload helper SHA256:
`91c34cb12c51b8b4895c1f94fd6655a3665079ae6f3781782e6b28e39053149b`.
Existing aim helper SHA256:
`40aff10c8dfdc8bcde0bc7d2380318339d3ce47085e7f84b15bc05158e66c2cf`.
