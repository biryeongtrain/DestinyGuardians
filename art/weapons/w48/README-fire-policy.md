# W48 intrinsic fire policy — research/data only

## Result / integration API

`WeaponFirePolicy.supportsAutomatic(WeaponCatalog.Entry)` is pure and returns a
boolean. It accepts canonical selected catalog values (including equal copies);
null, unknown IDs and mismatched catalog metadata fail closed. It does not load
the developer-only `art/` directory at runtime and does not mutate profiles,
stacks, ammo, timers, input, HUD or reload state. The JUnit artifact parity tests
keep the small code allow-list synchronized with the 63-row data table.

**15 / 63 automatic:** retain 12 selected AR/SMG/trace/MG weapons under the
existing family policy, and add only these 3 textually evidenced intrinsics:

| Selected ID | Official intrinsic plug hash | Verbatim official description |
|---|---:|---|
| `aishas_embrace` | 3920852688 | Fires full auto with deeper ammo reserves. Faster reload when weapon is empty. |
| `dead_man_walking_xx7463` | 806997698 | Full auto. Deeper ammo reserves. Slightly faster reload when magazine is empty. |
| `ikelos_sg_v1_0_1` | 996573084 | Fires full auto with deeper ammo reserves. Faster reload when weapon is empty. |

The remaining 48 are `TRIGGER_PER_CYCLE` in this deliberately narrow policy.
That is **not** a claim that perks or accessibility settings can never make them
automatic in Destiny. No global Full Auto accessibility feature is implemented.

## Actual socket/plug evidence, not a frame-name heuristic

Every selected W30 `bungie_hash` was checked against W40 metadata and the exact
official full inventory cache. Traverse each item's `sockets.socketEntries`,
resolve `singleInitialItemHash` into the same inventory definitions, and select
only a plug with both `itemTypeDisplayName == "Intrinsic"` and
`plug.plugCategoryIdentifier == "intrinsics"`. Require exactly one per selected
weapon. The evidence stores the actual socket index/entry, plug category/hash,
verbatim name/description, and canonical full-item/full-plug definition SHAs.
All current selected intrinsics happen to occupy socket 0, but selection did
not assume that position. No RPM stat or catalog `rapid_fire` string enables auto.

- `claws_of_the_wolf` (pulse), `null_composure` (fusion), and `apostate` (sniper)
  share intrinsic **878286503** with the rapid-fire AR/MG. Its description is:
  **“Deeper ammo reserves. Slightly faster reload when magazine is empty.”**
  There is no full-auto grant. AR/MG remain auto by the preserved family policy,
  not because this generic plug hash globally grants automatic fire.
- Rapid-fire heavy GL `canis_major` uses **2353477480**, likewise no full-auto
  wording. Fusion bursts, sidearm/pulse bursts, and LFR bursts are not themselves
  evidence of automatic repeated trigger cycles.
- Four selected item definitions actually initialize a **non-intrinsic Trait**
  plug **4267945040**, Full Auto Trigger System: `bygones`, `chattering_bone`,
  `claws_of_the_wolf`, `high_albedo`. Its full-auto text is recorded in
  `excludedNonIntrinsicFullAutoSockets`, but **does not** become intrinsic policy.
  Default/random roll traits, reusable/randomized alternatives and mods are
  outside scope. In particular, scanning every socket's text would be wrong.

The existing AR/SMG/trace/MG family baseline is an explicit retained architecture
decision. Their generic frame descriptions do not individually prove full-auto;
the evidence labels that distinction rather than inventing an official flag.

## Provenance and deterministic offline audit

Official manifest version: `245114.26.10.13.2000-1-bnet.66137`.
Source: W40's exact `DestinyInventoryItemDefinition-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json`.
Original cache: `/tmp/destiny-weapons-w30/bungie-items.json`, SHA-256
`b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c`.
No current-network, inferred roll, legacy RPM, or external community source is
needed. Both tables pin the W30 source/runtime catalogs and W40 definitions /
provenance byte SHAs. Evidence also pins `fire-policy.json` itself. Full definition
SHAs use UTF-8 canonical JSON with sorted keys, compact separators, no newline.
Artifact JSON uses deterministic UTF-8 two-space indentation and one final newline.

This read-only audit verifies every cached full definition and selected policy;
it does not write files or require Gradle/Minecraft:

```sh
rtk proxy python3 - <<'PY'
import hashlib, json
from pathlib import Path
sha = lambda b: hashlib.sha256(b).hexdigest()
canon = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True,
    separators=(',', ':'), allow_nan=False).encode()
art = Path('art/weapons/w48')
ev = json.loads((art/'fire-policy-evidence.json').read_bytes())
pol = json.loads((art/'fire-policy.json').read_bytes())
raw = Path('/tmp/destiny-weapons-w30/bungie-items.json').read_bytes()
assert sha(raw) == ev['inventorySha256']
assert sha((art/'fire-policy.json').read_bytes()) == ev['firePolicySha256']
for path, expected in ev['sourceHashes'].items():
    assert sha(Path(path).read_bytes()) == expected, path
full = json.loads(raw)
rows = {r['id']: r for r in pol['entries']}
base = set(pol['baseAutomaticFamilies'])
assert len(rows) == len(ev['entries']) == 63
for row in ev['entries']:
    item = full[str(row['bungieHash'])]
    assert sha(canon(item)) == row['itemDefinitionCanonicalSha256']
    socket = item['sockets']['socketEntries'][row['socketIndex']]
    assert socket == row['socketEntry']
    plug = full[str(socket['singleInitialItemHash'])]
    saved = row['intrinsicPlug']
    assert sha(canon(plug)) == saved['definitionCanonicalSha256']
    assert plug['itemTypeDisplayName'] == 'Intrinsic'
    assert plug['plug']['plugCategoryIdentifier'] == 'intrinsics'
    assert plug['displayProperties']['name'] == saved['name']
    assert plug['displayProperties']['description'] == saved['description']
    explicit = 'full auto' in saved['description'].lower()
    assert row['explicitFullAutoText'] == explicit
    assert rows[row['id']]['supportsAutomatic'] == (row['family'] in base or explicit)
    for excluded in row['excludedNonIntrinsicFullAutoSockets']:
        initial = item['sockets']['socketEntries'][excluded['socketIndex']]
        other = full[str(initial['singleInitialItemHash'])]
        assert sha(canon(other)) == excluded['initialPlug']['definitionCanonicalSha256']
        assert other['itemTypeDisplayName'] != 'Intrinsic'
assert sum(r['supportsAutomatic'] for r in rows.values()) == 15
for name in ('fire-policy.json', 'fire-policy-evidence.json'):
    raw = (art/name).read_bytes()
    assert raw == (json.dumps(json.loads(raw), ensure_ascii=False,
        indent=2, allow_nan=False)+'\n').encode()
print('Verified 63 exact official socket/plug policies; 15 automatic, 48 trigger-per-cycle')
PY
```

JUnit tests are authored for the main coordination gate; this sidecar does not
run Gradle or runtimes, and does not edit gameplay/integration files.
