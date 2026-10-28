from pathlib import Path
import subprocess, hashlib, json
r = Path('/Users/qf/IdeaProjects/DestinyGuardians')
q = r/'docs/qa/2026-10-28/w223'
def git(*args):
    return subprocess.check_output(['rtk','proxy','git',*args],cwd=r)
plan = json.loads((q/'commit-plan.json').read_text())
expected = {x['path']: x for x in plan['files']}
staged = {p.decode() for p in git('diff','--cached','--no-renames','--name-only','-z').split(b'\0') if p}
assert staged == set(expected), 'Staged scope differs from deliberate plan'
assert git('rev-parse','--show-object-format').strip() == b'sha1'
index = {}
for row in git('ls-files','--stage','-z').split(b'\0'):
    if not row: continue
    fields, path = row.split(b'\t',1)
    mode, oid, stage = fields.split()
    if path.decode() in expected:
        assert mode == b'100644' and stage == b'0'
        index[path.decode()] = oid.decode()
for rel, entry in expected.items():
    if entry.get('deleted'):
        assert not (r/rel).exists() and rel not in index, rel
        continue
    raw = (r/rel).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry['sha256'], rel
    blob = b'blob '+str(len(raw)).encode()+b'\0'+raw
    assert hashlib.sha1(blob).hexdigest() == index[rel], rel
before = {key:git(*args) for key,args in [('unstaged',('diff','--name-only','-z')),('untracked',('ls-files','--others','--exclude-standard','-z'))]}
out = Path('/private/tmp/destiny-w223-source/commit-output.log')
with out.open('wb') as f:
    result = subprocess.run(['rtk','proxy','git','commit','-q','-m','feat: fix glaive arm registration and add confirmed hit HUD (W223)'],cwd=r,stdout=f,stderr=subprocess.STDOUT)
assert result.returncode == 0, out.read_text()[-6000:]
assert not git('diff','--cached','--name-only').strip()
after = {key:git(*args) for key,args in [('unstaged',('diff','--name-only','-z')),('untracked',('ls-files','--others','--exclude-standard','-z'))]}
assert before == after, 'Unexpected remaining-work path drift during commit'
receipt = {'commit':git('rev-parse','HEAD').decode().strip(), 'files':len(staged), 'bytes':plan['bytes'], 'indexEmpty':True, 'remainingDirtyPathsPreserved':True, 'remaining':{k:len([p for p in v.split(b'\0') if p]) for k,v in after.items()}, 'cleanCheckoutBuildCertified':False, 'pushed':False}
Path('/private/tmp/destiny-w223-source/commit-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
