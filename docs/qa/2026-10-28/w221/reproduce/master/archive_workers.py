from pathlib import Path
import json, hashlib, zipfile

repo = Path('/Users/qf/IdeaProjects/DestinyGuardians')
qa = repo/'docs/qa/2026-10-28/w221'
assert json.loads((qa/'visual-review.json').read_text())['accepted']
# User steering: archive owned delta but retain these five worktrees as reusable slots.
features = json.loads((qa/'worktrees.json').read_text())['features']
integrated = {x['path']: x['after'] for x in json.loads((qa/'integration-pass2.json').read_text())}
out = qa/'worker-recovery.zip'
assert not out.exists()
with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for feature in features:
        work = Path(feature['destination'])
        metadata = repo/'.git/worktrees'/work.name/'worktree-batch.json'
        assert work.parent == repo.parent/'DestinyGuardians-worktrees'
        archive.write(metadata, feature['name']+'/worktree-batch.json')
        for rel in feature['owned_paths']:
            raw = (work/rel).read_bytes()
            assert raw == (repo/rel).read_bytes(), rel
            assert hashlib.sha256(raw).hexdigest() == integrated[rel], rel
            archive.writestr(feature['name']+'/files/'+rel, raw)
    archive.writestr('acceptance.json', (qa/'visual-review.json').read_bytes())
with zipfile.ZipFile(out) as archive:
    assert archive.testzip() is None
print({'archive': str(out), 'bytes': out.stat().st_size, 'workers': len(features)})
