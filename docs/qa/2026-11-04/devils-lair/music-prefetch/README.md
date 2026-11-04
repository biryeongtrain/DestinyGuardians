# Music media corroboration by WEM prefetch size

New evidence: all 40 music-bank media references have `uInMemoryMediaSize` equal to the matching WEM's data-chunk offset plus the lengths of its first 20 Opus packets. Combining this exact byte-count condition with source duration reduces the ambiguous set from 17 media IDs to 5, yielding 35 unique structural candidates. This is stronger than duration alone, but is not an authenticated source-ID table: the bank provides a prefix size, not a hash of those bytes.

`audit_devils_music_prefetch.py` verifies the archived XML hash, reuses the source checksum audit (bank, validation metadata and all 41 delivered music WEM/OGG files including descent), validates RIFF sizes, codec 0x3041 and complete packet-table coverage, then compares the exact 20-packet prefix. It does not rank or resolve ties by file order. The 20-packet rule is an observed invariant, not independently named source metadata.

Unresolved groups:
- IDs 161660846 / 877932565 / 945741618: tags 80D62742 / 80D62743 / 80D62744.
- IDs 342137398 / 249567261: tags 80D715E7 / 80D715E9.

`routes.json` relates these uncertainties to the previously generated diagnostic TXTP references. States 1156398953 and 1156398957 still reference ambiguous groups. Other available diagnostic routes have unique structural candidates, but none has an authenticated encounter label. The existing diagnostic set does not contain state 1156398956, so it is not full-route coverage. Automatic TXTP mix/bus limitations from the earlier bank review still apply.

Parser checks: the valid source yields prefix size 3932; truncation, wrong codec and an inconsistent packet-size table are rejected. See `parser-checks.json`. No source asset was modified, no BGM cue was installed, and no listening, loop seam or native playback acceptance occurred.

The user has been asked asynchronously for additional media-ID/WEM and music-state/encounter mapping data. Runtime combat music remains outstanding; this report is evidence toward recovery, not BGM implementation completion.

Reproduce from the repository root:

```sh
rtk proxy python3 scripts/strikes/audit_devils_music_prefetch.py --source /Users/qf/Downloads/Devils-Lair-Strike-KO-2026-11-02 --xml-gz docs/qa/2026-11-03/devils-lair/music/bank.xml.gz --bank-report docs/qa/2026-11-03/devils-lair/music/bank-structure.json --output docs/qa/2026-11-04/devils-lair/music-prefetch/report.json
```
