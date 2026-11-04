#!/usr/bin/env python3
"""Read-only W52 official quotes/video provenance; no live rule, input or audio certification."""
from pathlib import Path
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'art/weapons/w52/references'
checked = {}


def check(value, expected):
    path = Path(value)
    path = path if path.is_absolute() else ROOT / path
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == expected, value
    checked[str(path)] = actual


def pins(node):
    """Validate explicit path+SHA pairs, including clip/metadata prefixes."""
    if isinstance(node, dict):
        if 'path' in node and 'sha256' in node:
            check(node['path'], node['sha256'])
        for key, value in node.items():
            if key.endswith('Path') and key[:-4] + 'Sha256' in node:
                check(value, node[key[:-4] + 'Sha256'])
            pins(value)
    elif isinstance(node, list):
        for value in node:
            pins(value)


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from strings(value)


def normalized(value):
    return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', value)).split())


def main():
    audit = json.loads((ROOT / 'docs/qa/2026-10-24/w52/reference-audit.json').read_text())
    pins(audit)
    sources = json.loads((BASE / 'sources.json').read_text())
    videos = json.loads((BASE / 'videos.json').read_text())
    pins(sources)
    pins(videos)
    quotes = 0
    for source in sources['sources']:
        article = json.loads((ROOT / source['articlePath']).read_text())
        text = normalized(' '.join(strings(article)))
        for quote in source['checkedQuotes']:
            assert normalized(quote) in text, (source['id'], quote)
            quotes += 1
    # Check the exact five selected intrinsic definitions borrowed from W51,
    # not the historical W51 implementation source hashes changed in this stage.
    pins(json.loads((ROOT / 'art/weapons/w51/references/official-manifest.json').read_text()))
    report = dict(stage='W52', files=len(checked), sha256=checked,
                  officialArticles=len(sources['sources']), exactQuotes=quotes,
                  contactSheets=len(videos['contactSheets']), liveGameVerified=False,
                  nativeInputVerified=False, audioAuditionVerified=False)
    out = ROOT / 'docs/qa/2026-10-24/w52/source-verification.json'
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'sha256'}))


if __name__ == '__main__':
    main()
