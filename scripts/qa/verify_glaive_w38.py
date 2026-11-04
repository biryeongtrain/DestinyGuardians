#!/usr/bin/env python3
"""Read-only W38 two-handed held-pose byte provenance; does not start, rebuild or mutate clients."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--client-run',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    manifest=json.loads((ROOT/'art/weapons/w30/manifest.json').read_text())
    expected={str(Path(k).relative_to('src/main/resources')):v for k,v in manifest['runtime_sha256'].items()}
    for k,v in expected.items():assert sha(ROOT/'src/main/resources'/k)==v,k
    for model in manifest['models']:
        assert sha(ROOT/('art/blockbench/weapons/w30/'+model['id']+'.bbmodel'))==model['bbmodel_sha256']
    downloads=args.client_run/'downloads';entry=json.loads((downloads/'log.json').read_text().splitlines()[-1])
    paths=dict(jar=ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar',server_pack=ROOT/'run/server/polymer/resource_pack.zip',client_pack=downloads/entry['file']['name'])
    report={}
    for label,path in paths.items():
        keys=expected if label=='jar' else {k:v for k,v in expected.items() if k.startswith('assets/')}
        with zipfile.ZipFile(path) as z:
            for k,v in keys.items():assert hashlib.sha256(z.read(k)).hexdigest()==v,(label,k)
        report[label]=dict(path=str(path),sha256=sha(path),matched_entries=len(keys))
    before=json.loads((ROOT/'art/weapons/w38/baseline-runtime-hashes.json').read_text())
    changed=[k for k,v in before.items() if sha(ROOT/k)!=v]
    assert len(changed)==3 and all(k.startswith('src/main/resources/assets/destiny/models/weapon/glaive/nezarec_s_whisper') and k.endswith('_twohand.json') for k in changed)
    report['changed_resources']=changed
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
