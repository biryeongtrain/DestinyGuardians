from pathlib import Path
import json, hashlib, shutil, sys
phase=sys.argv[1] if len(sys.argv)>1 else "pass2"
assert phase in ("pass1","pass2")

repo = Path('/Users/qf/IdeaProjects/DestinyGuardians')
source = Path('/private/tmp/destiny-w221-'+phase+'-native')
dest = repo/'docs/qa/2026-10-28/w221'/('vision1' if phase=='pass1' else 'vision2')
assert not dest.exists()
dest.mkdir()
for name in ('screenshots', 'frames', 'sequences', 'oracles', 'fixtures', 'brackets'):
    path = source/name
    if path.exists():
        shutil.copytree(path, dest/name)
for name in ('shotgun-validation.json', 'native-validation.json', 'preflight.json', 'postflight.json',
             'client-ready.json', 'final-neutral-before-stop.json', 'server.log',
             'coordinator-progress.json', 'batch.log', 'server-wrapper.log', 'client-wrapper.log',
             'client-w221-'+phase+'-default.log', 'commands.jsonl'):
    path = source/name
    if path.exists():
        shutil.copy2(path, dest/name)
reproduce = dest.parent/'reproduce'/phase
reproduce.mkdir(parents=True, exist_ok=True)
for path in source.glob('*.py'):
    shutil.copy2(path, reproduce/path.name)
for path in source.glob('*.gradle'):
    shutil.copy2(path, reproduce/path.name)
rows = {str(p.relative_to(dest)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in dest.rglob('*') if p.is_file()}
(dest/'evidence-sha256.json').write_text(json.dumps(rows, indent=2)+'\n')
print({'evidenceFiles': len(rows), 'destination': str(dest)})
