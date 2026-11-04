"""Package an explicitly curated return folder. Standard library only; no game/tool invocation."""
import argparse, hashlib, json, zipfile
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('root',type=Path); p.add_argument('--output',required=True,type=Path)
a=p.parse_args(); root=a.root.resolve(); target=a.output.resolve()
if not root.is_dir(): p.error('return root must exist')
if target==root or root in target.parents: p.error('ZIP must be outside return root')
if target.exists() or Path(str(target)+'.sha256').exists(): p.error('output already exists; choose a new filename')
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
if manifest.get('template') is not False: p.error('fill manifest; template must be false')
if not (root/'REPORT.md').is_file(): p.error('REPORT.md is required')
complete={'raw_extracted','decoded_unverified','verified_in_blender'}
for c in manifest.get('clips',[]):
    for role,path in c.get('files',{}).items():
        if path is None: continue
        f=(root/path).resolve()
        if root not in f.parents or not f.is_file(): p.error(f'invalid referenced file: {path}')
    if c.get('status') in complete:
        for role in ('clip','skeleton','runtimeRig'):
            path=c.get('files',{}).get(role)
            if not path or not (root/path).stat().st_size: p.error(f'{c.get("id")}: missing/empty {role}')
    if c.get('status')=='verified_in_blender':
        if not c.get('verification',{}).get('blenderPlayback') or not c.get('files',{}).get('preview'):
            p.error('verified_in_blender needs recorded playback and preview path')
denied={'.pkg','.dll','.exe','.pdb','.vdf','.acf','.key','.pem'}
allowed={'.json','.md','.txt','.log','.csv','.bin','.fbx','.gltf','.glb','.blend','.png','.jpg','.jpeg','.mp4','.webm','.diff','.patch','.py','.ps1','.yml','.yaml'}
files=[]
for f in sorted(root.rglob('*')):
    if f.is_symlink(): p.error(f'symlinks are not allowed: {f.name}')
    if not f.is_file(): continue
    rel=f.relative_to(root)
    if any(x.lower() in {'.git','.env','config','config.json','ssfn','credentials','loginusers.vdf'} or x.lower().startswith('ssfn') for x in rel.parts): p.error(f'possible credential/cache path: {rel}')
    if f.suffix.lower() in denied or f.suffix.lower() not in allowed: p.error(f'not a curated return artifact: {rel}')
    if f.stat().st_size>1024**3: p.error(f'file over 1GiB: {rel}; inspect and split intentionally')
    files.append((f,rel.as_posix()))
if not files: p.error('no return files')
hashes=[]
for f,rel in files:
    h=hashlib.sha256()
    with f.open('rb') as s:
        for b in iter(lambda:s.read(1024*1024),b''): h.update(b)
    hashes.append({'path':rel,'bytes':f.stat().st_size,'sha256':h.hexdigest()})
target.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as z:
    for f,rel in files: z.write(f,'destiny-animation-return/'+rel)
    z.writestr('destiny-animation-return/FILE_HASHES.json',json.dumps(hashes,indent=2))
h=hashlib.sha256()
with target.open('rb') as s:
    for b in iter(lambda:s.read(1024*1024),b''): h.update(b)
Path(str(target)+'.sha256').write_text(h.hexdigest()+'  '+target.name+'\n',encoding='utf-8')
print(f'{target}\n{len(files)} files; {target.stat().st_size} ZIP bytes\nSHA256 {h.hexdigest()}')
print('Packaging only: manually inspect logs for secrets and verify decoded motion separately.')
