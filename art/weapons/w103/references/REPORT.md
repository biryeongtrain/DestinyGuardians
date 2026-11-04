# W103 L1 final ready report

**FROZEN — SOURCE/EXTRACTOR READY.** Integration and Java/runtime verification belong to master.

## Deliverables

- `scripts/extract_demolitionist_w103.py` — offline finite-source extractor, no dependencies or network.
- `src/main/resources/destiny/weapons/w103-demolitionist.json` — 11 rows (10 randomized + 1 curated Salvo).
- `art/weapons/w103/references/CONTRACT.md` — exact API, complete socket matrix and test-lead handoff.
- `mechanics.json` — source-backed baseline10/20%, 60tick refill ICD, reserve semantics and uncertainty.
- `socket-pools.json` — full proofs and all63 exact selected weapon scans including negative wave/sword evidence.
- `provenance.json` — every consumed SHA pin, fixed official manifest version, tool/version/retrieval record.
- `verification.json` — disjoint byte-identical reproduction and five rejected mutation fixtures.

## Verification

```sh
rtk proxy python3 scripts/extract_demolitionist_w103.py --verify
```

PASS. Disjoint reproduction of all4 generated outputs is byte-identical. Five source/semantic mutations rejected: changed bytes; removed Salvo option; disabled bow rollability; changed curated proof mode; fake trace randomized pool. Repeated extraction left output mtimes unchanged. Initial evidence-date viewport failure is retained in verification.json; repair verifies the date from a separately pinned result of the same official URL, retaining the numeric/context assertion.

## Important scope/uncertainty

Baseline chunks only: 10%, or20% for ordinary sniper/shotgun/fusion/glaive exceptions. Trace/GL/linear fusion remain10%; no blanket special-ammo rule. All11 eligible selected IDs are retained. Salvo set253 is a fixed curated alternative, not initial selection. Current D2 ability-tier/stat scalars and exact ICD owner/instance scope are not proven by this delivery. Master’s flat authored Minecraft cooldown adaptation and per-owner60tick ICD are explicitly local policies. No enhanced trait support.

## Boundaries

Only owned NEW paths were written. Ignored source captures/reproduction/fixtures are under `run/private-sources/w103`. No legacy game/model/audio/HUD assets regenerated; no Java/shared docs/registries edited. No builds, servers, clients, CU, gameplay input, commits or pushes. No child-agent tool available and no descendants claimed. No direct sub-agent messaging tool available; master relay to test lead is required.
