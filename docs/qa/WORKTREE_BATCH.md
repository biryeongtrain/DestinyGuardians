# Dirty snapshot worktree batches

`scripts/qa/worktree_batch.py` provides `create`, `inspect`, and `export` using
Python 3.10+, Git, and `rtk`. It copies current working inputs, including dirty,
untracked, and ignored files. It does not use a bare HEAD checkout as the working
baseline. It never commits, stashes, resets, pushes, applies changes to main, or
removes worktrees. All subprocess commands run through `rtk`.

## Existing W108 worktrees

The authoritative manual bootstrap record is
`/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-25/w108/worktree-batch.json`.
It records these existing CLI worktrees under
`/Users/qf/IdeaProjects/DestinyGuardians-worktrees`:

| Name | Owned files |
| --- | --- |
| `w108-coverage` | `src/gametest/java/kim/biryeong/destiny/test/FeedingFrenzyLifecycleW108GameTests.java`, `docs/qa/2026-10-25/w108/lifecycle-plan.md` |
| `w108-tooling` | `scripts/qa/worktree_batch.py`, `scripts/qa/test_worktree_batch.py`, `docs/qa/WORKTREE_BATCH.md` |
| `w108-docs` | `docs/design/123_먹이_쟁탈전_특성.md`, `docs/qa/2026-10-25/w108/README.md` |

The record reports 9,086 baseline inputs per worktree, SHA-256
`27c436a45052b5c755b7941a1b3a6a739d292efb0c9f7862f58e1e9df8f343f7`, and HEAD
`bfd4b4573fd8651bf1ea850bf829622ccce5c3c2`. They were manually seeded without
commits. The chat repository differs from the product repository, so Git CLI
worktrees were used; these are not app-managed attachments.

This tool does not adopt these existing directories or invent a per-file
baseline for them. Its own hash format is versioned and need not match the
manual bootstrap digest. `create` refuses all existing destinations, including
empty directories and missing directories still registered as worktrees.
`inspect`/`export` require metadata from a successful tool `create`.

## Create a future batch

Use a JSON manifest outside the source checkout. Ownership is a nonempty list
of **exact files**, including future files, with no globs or directories.
Scopes must be disjoint across features. For example (replace the future
destinations; do not reuse the existing W108 names):

```json
{
  "features": [
    {
      "name": "next-tooling",
      "destination": "/absolute/existing-parent/next-tooling",
      "owned_paths": [
        "scripts/qa/example.py",
        "docs/qa/EXAMPLE.md"
      ]
    },
    {
      "name": "next-tests",
      "destination": "/absolute/existing-parent/next-tests",
      "owned_paths": ["src/test/java/example/ExampleTest.java"]
    }
  ]
}
```

```sh
rtk proxy python3 -B scripts/qa/worktree_batch.py create \
  --source /Users/qf/IdeaProjects/DestinyGuardians \
  --manifest /absolute/batch.json \
  --minigame-lib /Users/qf/IdeaProjects/DestinyGuardians/libs/minigame-lib \
  --gcb-server /Users/qf/IdeaProjects/GCB-server
```

The dependency defaults are `SOURCE/libs/minigame-lib` and
`SOURCE/libs/gcb-server`. Both must exist with `build.gradle`; pass the GCB
sibling checkout explicitly when needed. Dependency inputs are copied into
each worker's `libs/minigame-lib` and `libs/gcb-server` as regular independent
files/directories. No symlinks, hardlinks, nested Git metadata, caches, or build
outputs are shared. Dependency source edits in a worker are outside feature
ownership and block export.

The product's `gradle.properties` currently defaults GCB to `../GCB-server`.
For any later, separately authorized build, explicitly select the worker's
local copy using `-Pgcb_server_dir=/absolute/worker/libs/gcb-server`, or set
`ORG_GRADLE_PROJECT_gcb_server_dir=/absolute/worker/libs/gcb-server`.
The create/inspect JSON includes this environment setting. This tool does not
run Gradle or alter `gradle.properties`; callers must use the setting themselves.

Creation reserves fresh destinations and creates detached linked worktrees at
the captured source HEAD with `--no-checkout`, then initializes only their
private indices with `read-tree HEAD`. Files come exclusively from the filtered
dirty snapshot. In particular, a tracked file deleted from the source stays
absent even if Git ignores it. Existing tracked ignored inputs and untracked
ignored inputs are copied unless explicitly excluded below. Source working
files, its index, and HEAD are not changed. Git necessarily writes linked
worktree registration/private metadata in the shared Git administrative area.

## Included inputs, exclusions, and disk use

The walker reads the filesystem rather than relying on `git status` or
`git ls-files --others`. It preserves code, assets, scripts, design documents,
configuration, and build inputs such as `gradle/wrapper/gradle-wrapper.jar`.
The same explicit filter applies to source, dependencies, and worker inspection:

- Directory/path components, case insensitive: `.git`, `.gradle`, `.cache`,
  `.codegraph`, `__pycache__`, `node_modules`, `.pytest_cache`, `.mypy_cache`,
  `.ruff_cache`, `build`, `out`, `target`, `run`, `runs`, `logs`, `cache`, `caches`.
- `.DS_Store`, `*.log`, and numbered rotations such as `*.log.1`.
- Under `docs/qa/`, archive/container/video suffixes `.zip`, `.tar`, `.gz`,
  `.tgz`, `.bz2`, `.xz`, `.7z`, `.rar`, `.jar`, `.zst`, `.mp4`, `.mov`, `.mkv`,
  `.webm`.
- Under `docs/qa/`, binary capture/output suffixes `.png`, `.jpg`, `.jpeg`,
  `.gif`, `.webp`, `.bmp`, `.tif`, `.tiff`, `.ico`, `.wav`, `.ogg`, `.mp3`,
  `.flac`, `.opus`, `.aac`, `.m4a`, `.aif`, `.aiff`, `.class`, `.bin`, `.dat`,
  `.nbt`, `.pdf`, `.avi`, `.exe`, `.dll`, `.so`, `.dylib`, `.glb`, `.blend`,
  `.npy`, `.npz`, **at every size**. Thousands of individually small captures
  must not accumulate into gigabytes of copied history. Extension matching is
  case insensitive. This restriction does not apply to `art` or `src` binaries.
- Other binary files larger than 8 MiB under `docs/qa/`. Binary classification
  uses the first 8 KiB (NUL or invalid UTF-8); large text reports remain inputs.

Historical QA text, JSON reports, and Java snapshots remain included for tests
that use them as working inputs. Small screenshots/audio are excluded even below
8 MiB. No historical product QA archives are copied by the unittest fixtures.

These are explicit exclusions even when tracked. Do not place required source
inputs or owned files in these locations. Generated output changes there are
intentionally ignored during inspection/export. Symlinks in excluded output
locations are skipped; included symlinks, special files, and symlink ancestors
are refused rather than followed. Scope paths reject absolute paths, traversal,
backslashes, ambiguous separators, and Git metadata.

Every included file's SHA-256, size, and executable bit form the baseline.
Copies are streamed with exclusive creation and checked against these hashes.
Full inventories are rechecked after **all** batch copies, including file
additions/deletions and dependency edits. Source inode/time/mode fingerprints
also detect rewrites even when bytes return to their earlier value. All copies
must match the baseline before a batch becomes ready. This is drift detection,
not a filesystem transaction: keep source editing paused during capture; an
edit after the final check belongs to a later snapshot.

There is no full snapshot staging directory: creation uses one file inventory
in memory and streams to each destination. It still needs space for every
worker's included inputs and independent dependencies. With only 7.9 GiB free
at the W108 handoff, do not create another full product batch without budgeting
its size. Failed copies, including disk-full failures, leave partial destinations
and an `incomplete` state when registration succeeded. They are never silently
deleted, adopted, or overwritten. Inspect/export refuse incomplete state. Review
and clean failed directories/registrations manually when authorized.

## Inspect and export

```sh
rtk proxy python3 -B scripts/qa/worktree_batch.py inspect \
  --worktree /absolute/worker
rtk proxy python3 -B scripts/qa/worktree_batch.py export \
  --worktree /absolute/worker --dry-run
rtk proxy python3 -B scripts/qa/worktree_batch.py export \
  --worktree /absolute/worker --output /absolute/new-export-directory
```

`inspect` reports owned add/modify/delete operations and out-of-scope changes
relative to the copied dirty baseline. Inherited dirt is unchanged baseline,
so it is not a feature delta. Metadata lives in the worker's private Git
directory as `worktree-batch.json`; it includes explicit ownership and a
checksum of the per-file baseline. A changed worker HEAD or corrupt/incomplete
metadata blocks use. Inspection reports scope violations in JSON; export
rejects them with a nonzero exit status.

Both dry-run and materialized export check **every owned path** in the original
source against the create-time baseline (including expected absence and the
executable bit). Concurrent source additions, edits, or deletions in that scope
block export. Unrelated main edits remain untouched. The worker inventory and
owned source fingerprints are checked again after export copying. Avoid editing
either side during export.

A successful export has `manifest.json` plus `files/<owned-path>` for changed
regular files only, with before/after hashes and operation records. It contains
no inherited dirt or unrelated source files. A failed materialized export keeps
an `INCOMPLETE` marker and has no usable completed bundle. Never consume a bundle
with that marker. A successful empty export contains only its manifest.

Owned deletions fail by default. `--allow-deletes` permits **deletion records in
the bundle only**; it never deletes source files. Source files inherited as
already deleted are baseline absence and produce no deletion operation.
Output directories must be fresh and outside all registered worktrees and
original dependency roots. Existing exports are never overwritten.

There is intentionally no automatic integration or cleanup command. Review the
bundle's exact file list, then recheck each `before` hash/absence against the
target immediately before any separately authorized integration. An export-time
conflict check cannot protect against later main edits. Never apply a blanket
`git diff HEAD`, copy the entire worker back, or reset main: those actions would
mix inherited dirt with feature changes. Ownership/baseline metadata is local
trusted state, not an authenticated artifact from an untrusted worker.

## Tests

```sh
rtk proxy python3 -B -m unittest discover \
  -s scripts/qa -p test_worktree_batch.py -v
```

Only this stdlib suite is needed. It uses tiny Git repositories and dependencies
in automatically cleaned `TemporaryDirectory` fixtures, including fixture-only
seed commits. It never reads or copies a product checkout, runs Gradle, starts a
live server, or uses Computer Use. Binary filtering is tested by lowering the
threshold rather than allocating large captures. Tests cover isolated outputs,
dirty and ignored inputs/deletions, scoped export/deletion records, ownership,
conflicts, drift, unsafe paths/symlinks, occupancy, and no overwrite.


## W109 product batch

The tool was used for two actual product worktrees, `w109-one-for-all` and
`w109-surrounded`, each owning cycle/profile/wrapper, two JUnit files, and its
worker handoff. Both were seeded from33,502 dirty/current inputs, baseline
`b77ecbc2a242556ce0862b2ba5ac17bda69984d487cae6b928936a698b8faa96`.
Workers returned21/26 isolated passing tests; master integrated only six exact
additions per export after before/after checks, then owned the shared integration,
832JUnit/900GameTest final gate, and one consolidated native QA server session.
See [W109 evidence](2026-10-25/w109/README.md).

Both worktrees remain frozen and their workers are closed. No auto-retirement is
performed. Disk budgeting limited this batch to two leaders. Each source/dependency
snapshot used about805MiB; do not estimate future copies solely from W108's558MiB.
Export destinations must use canonical nonsymlink ancestors: `/tmp` on macOS was
correctly rejected; `/private/tmp` was accepted without relaxing path safety.

## W110 product batch

Two new independent worktrees (`w110-swashbuckler`, `w110-grave-robber`) returned
cycle/profile/wrapper plus their own two tests and handoffs. Each passed20 pure
standalone tests, not real wrapper behavior; central874JUnit/915GameTest and
one combined Vision product-server session verified integration separately.
33,898 dirty/current inputs, baseline
`dd848c2b42f5444cba77801ba712f6fd8dfe96453287aa3079e97ccdbebc82fd`.
Both exact6-addition exports were checked before/after; no out-of-scope/main
conflicts. Each808MiB; frozen workers closed, children0, no automatic retirement.
See [W110 evidence](2026-10-25/w110/README.md).


## W111 automatic copy-on-write

`copy_file` now attempts Darwin `clonefile` with `CLONE_NOFOLLOW` before streaming.
A clone has its own inode; block sharing is copy-on-write, not a hardlink or a
shared writable dependency/build/run directory. Existing baseline schema, CLI,
full source/worker inventories, exact-file ownership, no-overwrite policy, and
main conflict checks remain in force. Both source and target content hashes,
source stability and separate regular-file identity are checked. Identity is
validated before changing destination permissions.

Unsupported platform/symbol/filesystem (`EXDEV`, `ENOTSUP`/`EOPNOTSUPP`,
`ENOSYS`) uses exclusive streaming instead. Permission, space, occupancy and
other errors propagate; an `ENOSPC` is not silently retried as a full copy.
Failed/partial destinations are retained for inspection as before.

Do not infer physical allocation or a speedup factor from logical file sizes,
`st_blocks`, or clone counts. CoW lets later independent edits allocate changed
blocks, so reserve space for worker edits, generated outputs and central tests.
The W111 bootstrap used two actual product worktrees with 34,169 current dirty
inputs and independent dependencies; its external bootstrap is distinguished
from final-helper fixture validation. See [W111 record](2026-10-25/w111/README.md).

### Throughput operating policy

For product work, delegate independent gameplay, model/animation and HUD changes
rather than splitting only docs or audits. Each leader owns implementation and
its targeted regression; master continues shared critical-path work and owns
integration, one final full regression gate, and one consolidated native QA
session. Additional code changes/failures require fresh verification. This is
not permission to omit cleanup, image inspection or uncertain-result reporting.
Keep exact scope manifests, bounded child-agent count and disk/memory budgets.
The W111 workflow-only change is not counted as new gameplay features.
