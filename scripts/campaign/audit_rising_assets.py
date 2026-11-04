#!/usr/bin/env python3
"""Read-only verification of the supplied campaign archive; never edits originals."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(root):
    root = root.resolve()
    manifest = json.loads((root / 'FILE-HASHES.json').read_text())
    failures = []
    total = 0
    for relative, expected in manifest.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            failures.append({'file': relative, 'reason': 'missing or outside archive'})
            continue
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            while block := stream.read(1024 * 1024):
                total += len(block)
                digest.update(block)
        if digest.hexdigest().lower() != expected.lower():
            failures.append({'file': relative, 'reason': 'hash mismatch'})
    return {'source': str(root), 'files': len(manifest), 'bytes_read': total,
            'failures': failures, 'passed': not failures,
            'scope': 'File integrity only; no rendering, animation or audio acceptance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    result = audit(args.source)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'failures'}))
    raise SystemExit(0 if result['passed'] else 1)
