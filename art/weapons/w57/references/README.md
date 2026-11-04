# W57 Marksman's Dodge: primary-source sidecar

Bounded source research captured on 2026-10-24 UTC. This is evidence for the local
all-equipped reload and 15m ammo pickup design; no runtime, test, animation or perk
implementation was inspected. This is not an exhaustive patch audit or a live
Destiny 2 playtest.

## Findings

- [Bungie Update 9.1.5](https://www.bungie.net/7/en/News/Article/destiny_update_9_1_5),
  published 2025-10-07: activating Marksman's Dodge collects nearby ammunition and
  reloads all weapons. The all-weapons wording supports including stowed equipped
  weapons; it does not specify a reserve transfer algorithm.
- [Bungie Update 9.5.0](https://www.bungie.net/7/en/News/Article/destiny_update_9_5_0),
  published 2025-12-02: ammo pickup radius increases from 10m to 15m.
- Official inventory definition **426473316** corroborates nearby ammo collection
  and all-weapon reload. Its description does not give a numeric radius.
- The live Manifest metadata retrieved at 2026-10-24T02:54:37Z advertises the same
  version and English inventory path pinned by W51. The existing **199,128,691-byte**
  cache matches W51's SHA-256. The inventory was not downloaded again: metadata
  agreement is not a fresh measurement of inventory bytes.

## Evidence files and boundaries

[sources.json](sources.json) contains dates, canonical URLs, exact CMS request URLs,
article UIDs, paraphrases and short evidence substrings (16 and 12 words including
the respective ability heading). [official-manifest.json](official-manifest.json)
connects W51's cache pin, captured current metadata and the complete selected
definition; its description evidence is 10 words. No source exceeds 25 quoted
words in these extracted reference records. This README paraphrases the findings.

Full CMS responses, complete article entries, page shells, official Settings and
Manifest responses, retrieval metadata, and the selected complete definition are
kept under ignored `run/private-sources/w57/`. Article HTML is only parsed as data.
The canonical article URLs returned HTTP 200 JavaScript shells; the body evidence
comes from Bungie.net's official live ContentStack delivery service, using the
pattern already recorded by W51. No community source is used. Optional historical
2.0 context is omitted; no weapon-perk implementation is claimed.

Unproven gameplay: through-wall magnet behavior; exact pickup/reload order; real
animation duration/frame timing; weapon-perk proc implementation; and air/ground
or other dodge restrictions. Personal ammo ownership, teammate interaction,
eligibility and brick consumption are local implementation policy rather than
independent findings from these sources. A 15m radius alone does not establish
collision shape, line-of-sight rules, or the exact inclusion boundary.

## Reproduce acquisition

Use the fixed `requestUrl` values in `sources.json`: two exact `url.hosted_url`
queries, `environment=live`, `locale=en-us`, `limit=2`, `include_count=true`.
Each captured query returned exactly one article. Use HTTP GET with a 30-second
timeout and a 5 MiB response cap. Read CMS `ApiKey` and `{environment}{deliveryToken}`
from `https://www.bungie.net/Platform/Settings/` at
`Response.systems.ContentStack.parameters`, then supply `api_key` and `access_token`
request headers in memory. Do not publish those values. Save raw response bytes
and retrieval metadata before extracting the one full entry. Preserve any new
capture in a separate private directory; do not replace this evidence snapshot.
Fetch only `/Platform/Destiny2/Manifest/` to compare version and the
`jsonWorldComponentContentPaths.en.DestinyInventoryItemDefinition` path with W51.
Read the existing pinned inventory cache to select the complete `426473316` entry.
No broad article search or full inventory download is needed. Later live edits
may change hashes; they require a separate snapshot, not regenerated old pins.

## Offline verification

From the repository root (Python 3 standard library only):

```sh
rtk proxy python3 -B scripts/qa/verify_marksman_sources_w57.py --out docs/qa/2026-10-24/w57/source-evidence/verification-local.json
```

The output path must be new and its parent must exist. The verifier makes no
network requests, writes only the requested new result, and never rewrites inputs
or regenerates pins. Exit codes: 0 passed, 1 evidence failure (with JSON result),
2 invalid/unwritable output. Private evidence and the original W51-pinned cache
are required; `--cache /path/to/identical-cache.json` supports a relocated cache
with the same SHA-256. `--root` supports an offline relocated evidence tree.
An absent or changed source fails; there is no download fallback.

[provenance-pins.json](../../../../docs/qa/2026-10-24/w57/source-evidence/provenance-pins.json)
pins inputs, extracted references, READMEs and the verifier. It is the reviewable
integrity baseline, not a signed authenticity certificate. The verifier checks
raw/entry equality, source identity/dates, evidence near the named ability heading,
quote budgets, W51/full-cache linkage, selected-definition equality and canonical
hashes. Its current-metadata check concerns the **captured retrieval time**, not the
time at which offline verification runs. Prior W51 files are read only.

See [the QA note](../../../../docs/qa/2026-10-24/w57/source-evidence/README.md)
and [the verification result](../../../../docs/qa/2026-10-24/w57/source-evidence/verification.json).
