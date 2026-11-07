#!/usr/bin/env python3
"""Export a validated server's completed cache for installation before an identical server starts."""
import argparse, hashlib, json, zipfile
from pathlib import Path


def digest(path, algorithm):
    h=hashlib.new(algorithm)
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--server-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    cache=args.server_root/'polymer/destiny-pack-cache'
    manifest=json.loads((cache/'manifest.json').read_text())
    assert manifest['schema']==1
    assert digest(cache/'pack.zip','sha1')==manifest['zipSha1']
    assert digest(cache/'pack.zip','sha256')==manifest['zipSha256']
    assert digest(cache/'profiles.bin.gz','sha256')==manifest['profilesSha256']
    with zipfile.ZipFile(cache/'pack.zip') as z:
        assert 'pack.mcmeta' in z.namelist() and z.testzip() is None
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temp=args.output.with_suffix('.tmp')
    try:
        with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_STORED) as out:
            for name in ['pack.zip','profiles.bin.gz','manifest.json']:
                out.write(cache/name,'polymer/destiny-pack-cache/'+name)
            out.writestr('README.txt',
                'Extract into the server root before startup. Keep all three cache files together.\n'
                'This is a server cache bundle; the client resource pack is the inner pack.zip.\n'
                'Only matching mod/config/resource inputs reuse it. Other environments generate once and save their own cache.\n'
                'The server validates both output hashes and input compatibility automatically.\n')
        temp.replace(args.output)
    finally:temp.unlink(missing_ok=True)
    print(json.dumps(dict(path=str(args.output.resolve()),bytes=args.output.stat().st_size,
        clientPackBytes=(cache/'pack.zip').stat().st_size,inputKey=manifest['inputs'],sha256=digest(args.output,'sha256')),indent=2))


if __name__=='__main__':main()
