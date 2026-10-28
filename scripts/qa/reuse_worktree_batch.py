#!/usr/bin/env python3
"""Refresh completed private worktree slots from the current dirty integration checkout.

Never pulls a remote or changes main. Close slot workers before calling. Unmerged
owned changes or any out-of-scope drift block the whole batch before writes.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import zipfile
import worktree_batch as b


def refresh(source, manifest, recovery):
    source=b.repo_root(source)
    features=manifest.get('features', [])
    if not features:raise b.BatchError('Nonempty features required')
    recovery=b.clean_absolute(recovery)
    protected=b.registered_worktrees(source)
    if any(recovery==p or p in recovery.parents or recovery in p.parents for p in protected):
        raise b.BatchError('Recovery must be outside every worktree')
    if recovery.exists() or not recovery.parent.is_dir():raise b.BatchError('New recovery directory required')
    head=b.git(source,'rev-parse','HEAD')
    base=b.scan(source,skip_dependencies=True)
    workers=[];scope=[];destinations=set();dependency_sources=None
    # Validate all slots first. A completed owned delta must already equal main.
    for feature in features:
        if set(feature)!={'name','destination','owned_paths'}:raise b.BatchError('Invalid feature fields')
        work,old=b.load(feature['destination'])
        if work in destinations:raise b.BatchError('Duplicate slot')
        destinations.add(work)
        if b.clean_absolute(old['source'])!=source:raise b.BatchError('Different source checkout')
        if b.git(work,'rev-parse','--symbolic-full-name','HEAD')!='HEAD':raise b.BatchError('Slot must be detached')
        if b.git(work,'write-tree')!=b.git(work,'rev-parse',old['head']+'^{tree}'):
            raise b.BatchError('Staged slot changes need integration first')
        owned=b.owned_paths(feature['owned_paths']);b.owned_paths(scope+owned);scope+=owned
        for rel in owned:
            if (source/rel).is_dir():raise b.BatchError('Scope must name files')
        deps=tuple(old['dependency_sources'])
        if len(deps)!=len(b.DEPENDENCIES):raise b.BatchError('Invalid dependency roots')
        if any(recovery==b.clean_absolute(p) or b.clean_absolute(p) in recovery.parents or recovery in b.clean_absolute(p).parents for p in deps):
            raise b.BatchError('Recovery must be outside dependencies')
        if dependency_sources is not None and deps!=dependency_sources:raise b.BatchError('Different dependency roots')
        dependency_sources=deps
        current=b.scan(work)
        workers.append((work,old,feature,current))
    deps={prefix:b.clean_absolute(path) for prefix,path in zip(b.DEPENDENCIES,dependency_sources)}
    dep_snaps={prefix:b.scan(path) for prefix,path in deps.items()}
    baseline=dict(base[0])
    for prefix,snap in dep_snaps.items():baseline.update({prefix+'/'+rel:v for rel,v in snap[0].items()})
    plans=[]
    for work,old,feature,current in workers:
        for rel in old['baseline'].keys()|current[0].keys():
            if current[0].get(rel)!=old['baseline'].get(rel):
                if rel not in old['owned_paths'] or current[0].get(rel)!=baseline.get(rel):
                    raise b.BatchError('Unintegrated or out-of-scope slot change: '+str(work/rel))
        delta=sorted(rel for rel in current[0].keys()|baseline.keys() if current[0].get(rel)!=baseline.get(rel))
        plans.append((work,old,feature,current,delta))
    def source_stable():
        if b.git(source,'rev-parse','HEAD')!=head or b.scan(source,True)!=base:
            raise b.BatchError('Source drift; do not run workers against incomplete refresh')
        for prefix,path in deps.items():
            if b.scan(path)!=dep_snaps[prefix]:raise b.BatchError('Dependency drift')
    source_stable()
    recovery.mkdir()
    rows=[]
    # Preserve overwritten/deleted bytes and old state before any product writes.
    with zipfile.ZipFile(recovery/'before.zip','x',compression=zipfile.ZIP_DEFLATED) as archive:
        for i,(work,old,feature,current,delta) in enumerate(plans):
            archive.writestr(str(i)+'/state.json',json.dumps(old))
            for rel in delta:
                if rel in current[0]:archive.write(work/rel,str(i)+'/files/'+rel)
    for work,old,feature,current,delta in plans:
        if b.scan(work)!=current:raise b.BatchError('Worker drift before refresh')
        b.write_json(b.state_path(work),{**old,'status':'refresh-incomplete','recovery':str(recovery)},'w')
        for rel in delta:
            target=b.joined(work,rel)
            actual=b.read_file(target)[0] if target.exists() else None
            if actual!=current[0].get(rel):raise b.BatchError('Slot drift: '+rel)
            if rel not in baseline:
                target.unlink()
                continue
            prefix=next((p for p in b.DEPENDENCIES if rel.startswith(p+'/')),None)
            origin=deps[prefix]/rel[len(prefix)+1:] if prefix else source/rel
            temporary=target.with_name(target.name+'.refresh-tmp')
            b.copy_file(origin,temporary,baseline[rel])
            os.replace(temporary,target)
        if b.scan(work)[0]!=baseline:raise b.BatchError('Refreshed snapshot mismatch')
        rows.append({'slot':str(work),'task':feature['name'],'changedFiles':len(delta),'baselineFiles':len(baseline)})
    source_stable()
    for work,old,feature,current,delta in plans:
        if head!=old['head']:
            b.git(work,'update-ref','--no-deref','HEAD',head,old['head'])
            b.git(work,'read-tree',head)
        b.write_json(b.state_path(work),{**old,'name':feature['name'],'head':head,'status':'ready',
            'owned_paths':feature['owned_paths'],'baseline':baseline,'baseline_sha256':b.fingerprint(baseline),
            'previous_recovery':str(recovery)},'w')
    report={'source':str(source),'head':head,'slots':rows,'recovery':str(recovery/'before.zip'),
            'mainModified':False,'recreatedWorktrees':False,'dirtyAndUntrackedInputsIncluded':True}
    b.write_json(recovery/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--recovery',required=True)
    args=p.parse_args()
    try:
        print(json.dumps(refresh(args.source,json.loads(Path(args.manifest).read_text()),args.recovery),indent=2))
    except (b.BatchError,OSError,ValueError) as error:
        print('worktree-refresh: '+str(error),file=sys.stderr);return 1
    return 0

if __name__=='__main__':sys.exit(main())
