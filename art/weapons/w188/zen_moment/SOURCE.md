# W188 base Zen Moment — source and policy boundary

Base hash **2387244414**, enhanced hash **1748774930** (excluded). Scope is the existing 65 selected catalog identities, not every Destiny weapon. The generator emits exactly 10 base official socket rows.

## Official identity and roll evidence

Pinned Bungie manifest `245114.26.10.13.2000-1-bnet.66137`. Official inventory and plugsets use component suffix `-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json`. Local cached raw files: `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/bungie-plugsets.json`, `/tmp/destiny-weapons-w60/manifest.json`. Component paths are checked against the manifest, hashes against source pins. This is cached official evidence, not a newly downloaded inventory snapshot.

A row qualifies only when its weapon is exact legendary tier 5, the socket belongs to trait category 4241085061, the reference is **randomizedPlugSetHash**, the pool is nonfake, and an exact base plug entry has **currentlyCanRoll: true**. Reusable/fake pools, enhanced plugs, nontrait sockets, nonrolling entries and exotics cannot add support. `official-sockets.json` records all 65 scans, every referenced randomized/reusable pool and matching entry, accepted full pool proofs, and rejected matches. Names locate the two official definitions only; names never qualify a weapon pool.

Eligible selected weapons: Duke Mk. 44, Austringer, Gnawing Hunger, Cold Denial, Blast Furnace, Distant Relation, Bug-Out Bag, Lonesome, Dead Man Walking XX7463, Retrofit Escapade. Source rows carry exact weapon hash, socket and plugset hash.

## Independent current mechanics review (2026-10-27 UTC)

* Clarity: https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/live/descriptions/clarity.json — live fetch SHA256 `881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384`, agrees with W187 cached entry. Base entry says weapon hits, one second, **5?** maximum, **?%** flinch resist, 15% visual weapon shake/reticle bounce per stack; HC/scout **2?**, pulse/sidearm 1.5, others 1. Entry lastUpload 1719594243302 is older than retrieval.
* Destiny Data Compendium: https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278 — independently fetched live; Zen row 250 still says **5?** cap, **?%** flinch and **15?%** visual effects. States 2x HC/scout and 1.5x pulse/sidearm. Explicitly **has no effect on actual recoil/camera movement**. Its gold up-arrow +5 stability is enhanced-only; base supplies no stability stat. Whole HTML SHA256 `a1cc8780ec2dbed7e89c05bd260085eebba2732994d72cdc379d8aa5f19da6f9` (sheet assets may vary across fetches). Saved exact base entry and DDC row are in `clarity-source.json`.

Agreement between community sources is corroboration, not proof from original game instrumentation. Independent attempts to obtain extra sources (D2Foundry 503, light.gg 403, search challenge, empty Bungie route) supplied no additional accepted numeric evidence. Current DDC resolves the family-weight policy but **does not resolve original cap or numeric flinch resistance**. These unresolved points are not reported as original measurements.

## Explicit authored port policies

* Half-stack integer units: 2 units = one stack; HC/scout +4 units, pulse/sidearm +3, others +2 for each confirmed positive direct weapon transaction.
* Tentative five-stack cap becomes authored bounded cap 10 units. All stacks expire together 20 server ticks after the last accepted hit; refresh at cap is allowed. Original independent-stack versus refresh-all timing is unproven.
* **AUTHORED** flinch mapping: `1 - 0.05 * stackUnits`, reaching 0.5 scalar at cap. This is linear 10% flinch resistance per whole stack. Neither source provides that percentage; it is an explicit local balancing mapping. Master composes this with existing incoming flinch, before its angular budget.
* Zen never changes stability stat, accuracy, actual recoil, aim displacement or `WeaponAiming.shot` camera kick. Visual weapon shake/reticle bounce have no separate present renderer and remain unimplemented; do not simulate them by lowering shot camera kick. Therefore this port has exact official **base eligibility**, but is not a claim of complete exact visual/numeric parity.
* No evidence establishes a visible original Zen proc row. Keep gameplay state hidden and expose queries to debug only. No permanent HUD countdown/stack row is added.
* Conservative held-only lifetime: slot change, source copy/replacement, world/owner/context/loadout/data/runtime/class changes, successful trait edit and cleanup revoke source tokens. Late projectiles cannot grant a newly held gun any credit. This strict source protection is authored port lifecycle policy.
* Real hits against the same enemy repeatedly count. A lethal confirmed hit counts even after target death. Miss, immunity, blocking, ability, secondary perk splash and nonfinite/nonpositive damage do not count. Token capture is only a trusted paid-emission boundary; the method alone does not prove payment or damage attribution.

## Reproduction and validation

Run `rtk proxy python3 scripts/build_zen_moment_w188.py` from the assigned worktree; add `--verify` for read-only byte verification or `--output-root /private/tmp/w188-zen-report/reproduce` for isolated output. Arguments accept explicit pinned inventory/plugsets/manifest/Clarity/DDC files. Strict source SHA checks, official predicates and exact value types reject drift. Java profile also pins generated resource bytes and exact canonical catalog entries; no WeaponPerks static initialization recursion.

Worker tests cover pure production cycle, profile, ownership lease and source boundaries. They do not instantiate an actual ServerPlayer. Master owns registry/shared hooks, actual FabricGT and native flinch/visual verification. Local execution reports remain outside product scope in `/private/tmp/w188-zen-report`.
