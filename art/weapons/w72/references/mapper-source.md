# W72 BetterModel item-mapping source evidence

Read-only dependency and implementation review, 2026-10-24. No builds, tests,
applications, downloads, production edits, or test edits performed by this sidecar.
This note is the only file written.

## Exact cached dependencies

- `/Users/qf/.gradle/caches/modules-2/files-2.1/io.github.toxicity188/bettermodel-api/3.5.1/ef02c6643255cf4b8952def9daa63a128154b140/bettermodel-api-3.5.1.jar`
  - SHA-256: `384fd04f33231cde7274e205752bb54a8ea0744176160d96f709307f89a9ab95`
  - SHA-1: `ef02c6643255cf4b8952def9daa63a128154b140`
- `/Users/qf/.gradle/caches/modules-2/files-2.1/io.github.toxicity188/bettermodel-core/3.5.1/3a73407f005b55deb16687666fd2088cdafdf351/bettermodel-core-3.5.1.jar`
  - SHA-256: `6b2cbb1c2edd3beb3d711758ab9a529d979e527317e557bdcfc87eb1bb720b32`
  - SHA-1: `3a73407f005b55deb16687666fd2088cdafdf351`
- `/Users/qf/.gradle/caches/modules-2/files-2.1/io.github.toxicity188/bettermodel-fabric/3.5.1/3c3abf924f903a437da0250ba0415b67ee174e6a/bettermodel-fabric-3.5.1.jar`
  - SHA-256: `b2a8b0bbf5adfde32bba6624644431326e3ea23c66a362cc2a566a411c0d3eb6`
  - SHA-1: `3c3abf924f903a437da0250ba0415b67ee174e6a`

## Provenance and method

Used offline `javap -c -p -l` (and selected `-v`) on the above 3.5.1 JARs.
Local readable source root:
`/Users/qf/Documents/Codex/2026-10-20/notion-plugin-notion-openai-curated-remote/work/bm`.
That checkout is commit `7dc7eed` and declares `project_version=3.6.0`; it is NOT
claimed to be a complete 3.5.1 source tree. The following cited implementations
were cross-checked against the 3.5.1 bytecode and its source line tables.
Paths below are relative to that source root.

## Bytecode-backed calls and ordering

- `api/src/main/java/kr/toxicity/model/api/bone/BoneTags.java:64-74`:
  LEFT_ITEM (`pli`, `li`) uses `BoneItemMapper.entity(THIRDPERSON_LEFTHAND,
  BaseEntity::offHand)`; RIGHT_ITEM uses the right-hand transform and `mainHand`.
  The JAR bootstrap method explicitly references `BaseEntity.offHand`.
- `platform/fabric/src/main/kotlin/kr/toxicity/model/impl/fabric/entity/BaseFabricEntityImpl.kt:114-129`:
  hand mappers wrap current native LivingEntity hand items.
- `api/src/main/java/kr/toxicity/model/api/tracker/Tracker.java:737-774` and
  `tracker/TrackerUpdateAction.java:385-389,408-419` (same API package root):
  `update(itemMapping()) -> tryUpdate -> pipeline.matchTree -> ItemMapping.test
  -> RenderedBone.updateItem(predicate)`. `update` is synchronous on its caller;
  successful updates flag a later dirty-data send. ItemStack action writes one
  output and does not replace the mapper.
- `api/src/main/java/kr/toxicity/model/api/bone/RenderedBone.java:184-192,273-280`:
  `updateItem` evaluates `itemMapper.apply(renderContext,itemStack)` BEFORE calling
  `itemStack(predicate,result)`. In the 3.5.1 bytecode, apply is at offsets 14-18;
  the itemStack call is at 19. Inside itemStack, the reference and predicate
  checks occur before monitorenter at offset 24; assignment is at offset 39,
  followed by invisibility, tint-cache clear, and applyItem under the monitor.
  `itemLock` is a private final Object. `renderContext` and `itemStack` are volatile.
- `RenderedBone.java:430-439` (same bone directory) ->
  `platform/fabric/src/main/kotlin/kr/toxicity/model/impl/fabric/entity/ModelDisplayEntityImpl.kt:149-153`:
  applyItem calls ModelDisplay.item; Fabric takes its entity-data lock, clones the
  platform item, and calls native Display.ItemDisplay.setItemStack. This can
  change the native display immediately, before any packet send.
- `api/src/main/java/kr/toxicity/model/api/tracker/Tracker.java:155-157`:
  `completeContext().thenAccept(...) -> pipeline.matchTree(bone.updateItem(context))`
  remaps all bones; no tracker.task queue or fixed-bone filter is used.
  `api/src/main/java/kr/toxicity/model/api/data/renderer/RenderSource.java:286-290`
  obtains player context from the skin-completion future. Completion can be
  immediate or deferred; thenAccept itself supplies no main-thread ordering.
- `platform/fabric/src/main/kotlin/kr/toxicity/model/impl/fabric/entity/PlayerChannelHandlerImpl.kt:195-225`:
  carried-item/player-action packets can schedule a non-fixed-bone itemMapping
  refresh, gated by hide-equipment and cancel-inventory settings.
  `platform/fabric/src/main/kotlin/kr/toxicity/model/impl/fabric/scheduler/FabricModelSchedulerImpl.kt:46-49`
  implements asyncTaskLater(1) as 50 wall-clock milliseconds on its own executor.
- `api/src/main/java/kr/toxicity/model/api/tracker/Tracker.java:171-209,278-279`:
  stock start ticks inline then schedules 25 ms frames. Tasks drain on even frames
  before handlers and bundle sends. These are stock dependency semantics;
  Destiny's clock mixin changes owned-tracker frame scheduling, not the above
  future-completion or packet-scheduler calls.
- `api/src/main/java/kr/toxicity/model/api/bone/RenderedBone.java:92-97` exposes
  getItemMapper/setItemMapper (verified in the JAR). No commit-generation check
  exists in the inspected item update path. A persistent mapper fixes sequential
  remapping but cannot retract a result already evaluated before its policy changes.
- `api/src/main/java/kr/toxicity/model/api/tracker/EntityTrackerRegistry.java:275-277`:
  getOrCreate returns an existing tracker without invoking the creation supplier.
  `EntityTracker.java:93-94,161` invokes the pre-update consumer AFTER super(),
  whose constructor has already attached the context-completion callback.
- `api/src/main/java/kr/toxicity/model/api/bone/RenderedBone.java:241-242,418-439`:
  enchant builds a modified item then calls itemStack; tint uses the same itemLock
  and applies the currently stored item. An authoritative itemStack policy will
  intentionally replace direct item/enchant outputs on owned hands, even at NONE.

## Commit-hook review boundary

Taking the actual native itemLock around policy selection AND the original
itemStack call serializes policy binding and native assignment; monitor re-entry
is legal. Re-evaluating the default hand mapper under this lock rejects an old
prop argument after clear. Keep suppliers pure state reads, retain them for the
bone lifetime, and do not acquire tracker/registry/other-bone locks inside them.
Inspected display paths take entity-data lock below itemLock; no reverse path to
itemLock was found there. This is not a proof for arbitrary custom mappers,
predicates, other mixins, or direct ModelDisplay.item calls, which bypass the hook.

Selection publication alone is not simultaneous two-display mutation. Publish,
then synchronously refresh both owned hands to order final commits behind older
writers. Keep published stacks/vectors immutable by convention; TransformedItemStack
is shallowly immutable and its copy() clones vectors and the underlying item.

At review, PlayerAnimations binds only in the getOrCreate initializer. A live
pre-existing same-model tracker skips this binding, leaving the newly allocated
LimbEquipment detached. The foreign-tracker test closes its tracker before
activation, so it does not exercise that adoption path.

The fifth W72 test uses a real mapper evaluation held before commit, publishes a
new prop on the server thread, then releases the worker and inspects the native
display. Its second assertion supplies a stale prop after clear. These establish
specific deterministic overwrite schedules; they do NOT replay or identify the
unrecorded original W71 interleave. Historical one-off failure attribution remains
unproven. Main's reported green counts are not independently re-run by this sidecar.


## Foreign-tracker refusal follow-up

Inspected sixth test `preexistingForeignLimbIsNotSilentlyAdoptedOrClosed`.
Read-only verification of `docs/qa/2026-10-24/w72/red-foreign.log`: line 732
records its tick-0 refusal assertion failure; lines 744-746 report 570 completed
GameTests and exactly one required failure. This run was started by main.

Main proposes a creation-callback-completed flag and immediate false return when
that callback did not run. This correctly distinguishes the already-existing
branch without claiming its clock or inserting it into ACTIVE. Set the flag after
successful binding and guard before claimServerClock and all later mutations.
The guard was proposed, not yet present in the source snapshot inspected here.
The sixth test checks refusal, immediate open/not-ACTIVE state, and live mapping;
it does not directly inspect the clock-ownership bit or assert open after stop.
Stock getOrCreate is a get-then-create operation, so the flag alone is not an
atomic ownership protocol against concurrent external registry creators.
