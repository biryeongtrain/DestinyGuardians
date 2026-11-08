# Startup resource pack output reuse

The old startup always invoked Polymer generation after BetterModel loaded. This re-expanded and optimized weapon assets on every server restart. The cache now persists the completed client ZIP together with exact server-side arm selector JSON and 32-bit pose matrices. Reusing the ZIP alone would leave server-side hand rendering uninitialized.

Startup still initializes registries and BetterModel normally. After that, a worker computes a content key and validates the completed outputs. Matching outputs restore the server data and prepare a copy of the archive off-thread. Only the atomic archive rename and readiness publication run on the server thread. Cache reuse does not emit a false pack-build completion event. Explicit operator pack generation still uses Polymer's original implementation.

The input key covers loaded mod versions and content, development class/resource roots, config inputs, BetterModel's generated asset ZIP, registered asset source paths, Polymer source_assets and configured included ZIPs, datapacks, Destiny feature properties, main pack UUID, description and icon. Config caches and filesystem/ZIP timestamps are excluded. Unknown, changed, absent or damaged outputs cause ordinary generation. A pack whose inputs changed during generation is not cached.

Outputs live in `polymer/destiny-pack-cache/`:

- `pack.zip`: completed client archive.
- `profiles.bin.gz`: server-only selector/pose companion; never send it to clients as a pack.
- `manifest.json`: schema, input key, actual ZIP SHA1/SHA256 and companion SHA256. Published last.

To install a pre-generated matching cache, copy all three files into that directory before startup. A cache from a different mod/config/resource set is rejected and generated once for the current environment. Default caching is enabled. `-Ddestiny.packCache.enabled=false` disables reuse/storage; `-Ddestiny.packCache.forceBuild=true` forces startup generation while refreshing the cache. `/polymer generate-pack` remains the explicit rebuild path.

Validation results and startup timings are appended below. No native client rendering/FPS or speaker acceptance is implied by server boot tests.

## Validation results

- All78 compatibility/pack unit tests passed in a real Gradle run, including7 new output corruption/key/pose tests and26 existing startup ordering tests. Initial assemble passed; the final readiness-reset build and36 relevant targeted units also passed.
- Actual headless Fabric boots: cold save test1/1 passed; subsequent restore test1/1 passed.543 routes and66812 matrices were loaded, referenced hand poses resolved, the advertised SHA1 matched the archive, and warm outputs were byte-identical without entering generation. Development class/resource input verification took28.859s.
- Actual packed-JAR, production-mode dedicated server: isolated loopback port25630, fresh world/config clone, no normal client/profile. Final default-gameplay run (older cache rejected after the JAR changed): process to saved output110.525s; restarted process to the same ready output12.098s, including1.536s cache restore. The earlier production pair measured179.374s/12.077s and is retained separately. Warm logs contain no pack-generation invocation. Both servers stopped normally with exit0. These are one cold/warm pair on this machine, not a sustained performance certification.
- Production client ZIP188236924 bytes (below250000000). Both client ZIP and server companion hashes are in the production manifest.
- The exported bundle is generated from the tested packed-JAR runtime, not the headless test-mod environment. Unzip into the server root alongside the matching JAR/config/mod/resource set. Different input sets intentionally generate and save their own cache once.

- Final lifecycle cleanup also clears AutoHost readiness at server start/stop, so a sequential server lifecycle in one JVM cannot advertise the prior session's pack while its selectors are empty. After this small change, the36 cache/pose/startup-order targeted unit tests and assemble were repeated successfully; the final packed-JAR cold/warm pair regenerates an incompatible older cache instead of relabelling it.

## 2026-11-08 key narrowed to this mod's assets

Servers with other mods kept reporting `Resource pack cache MISS` because the key hashed every mod's full jar, the whole `config/` tree and the world `datapacks/` folder, so runtime-rewritten configs or unrelated code changes invalidated it. The key (schema `destiny-pack-cache-2`) now covers: the Destiny mod in full (code and assets), `config/destiny`, `config/bettermodel`, `config/polymer/resource-pack.json`, the BetterModel output ZIP, registered/source assets, included ZIPs, `destiny.*` properties and pack identity. Every other mod contributes its version plus only `assets/**` and `pack.mcmeta`. World datapacks and other mods' configs/classes are no longer inputs. Consequence: a same-version code-only change in a foreign mod that alters Polymer-generated assets at runtime will not rebuild the pack; use `-Ddestiny.packCache.forceBuild=true` or `/polymer generate-pack` then.

The manifest now stores a per-group digest, and a MISS (or "inputs changed during generation") logs which groups changed, e.g. `changed inputs: [mod/styledchat]`. The first start after this update misses once because the old manifest has no group record. Not verified: a real packed-JAR server boot on the production mod set.
