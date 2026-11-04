#!/usr/bin/env python3
"""Prepare only the new W116 isolated profile; never edit an installed profile.

26.3's vanilla AFK limiter can cap an otherwise active native-input test at30fps.
Use the real minimized-only option for a controlled comparison, not a focus
override or disabled lock. This does not establish performance by itself.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/qa/2026-10-25/w115/native/isolated-client-options.txt'
DESTINATION = Path('/private/tmp/destiny-w116-native/client-run/options.txt')
VALUES = {'inactivityFpsLimit': '"minimized"', 'maxFps': '120', 'enableVsync': 'false'}


def controlled_options(text):
    if not isinstance(text,str) or '\0' in text:
        raise ValueError('Expected ordinary options text')
    found=set();out=[]
    for line in text.splitlines(keepends=True):
        key,sep,value=line.rstrip('\r\n').partition(':')
        if key not in VALUES:
            out.append(line);continue
        if not sep or key in found:
            raise ValueError('Duplicate or invalid controlled option: '+key)
        old=json.loads(value)
        valid=(old in ('afk','minimized') if key=='inactivityFpsLimit' else
               type(old) is bool if key=='enableVsync' else type(old) is int and old>0)
        if not valid:raise ValueError('Unexpected source value: '+key)
        found.add(key)
        ending=line[len(line.rstrip('\r\n')):]
        out.append(key+':'+VALUES[key]+ending)
    if found!=set(VALUES):raise ValueError('Missing controlled render option')
    return ''.join(out)


def prepare():
    if not SOURCE.is_file() or SOURCE.is_symlink():raise ValueError('Missing saved isolated source')
    manifest=json.loads((SOURCE.parent/'SHA256SUMS.json').read_text())
    raw=SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest[SOURCE.name]:raise ValueError('Source evidence drift')
    for parent in (DESTINATION.parent,*DESTINATION.parents):
        if parent.is_symlink():raise ValueError('Symlink in QA destination')
    marker=DESTINATION.parent.parent/'OWNER.json'
    if marker.is_symlink() or not marker.is_file() or json.loads(marker.read_text()).get('stage')!='W116':
        raise ValueError('Need a master-created W116 owned runtime first')
    data=controlled_options(raw.decode()).encode()
    with DESTINATION.open('xb') as f:f.write(data)
    return dict(source=str(SOURCE),sourceSha256=hashlib.sha256(raw).hexdigest(),
                destination=str(DESTINATION),sha256=hashlib.sha256(data).hexdigest(),
                controlled=VALUES,onlyIsolatedProfile=True)


if __name__=='__main__':print(json.dumps(prepare(),indent=2))
