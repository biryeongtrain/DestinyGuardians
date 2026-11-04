#!/usr/bin/env python3
"""Prove W30 source -> JAR -> running classpath/Polymer pack -> client cache bytes.

Run AFTER building and connecting the owned isolated test client; never rebuilds
or changes a server/client. Framebuffer claims still require inspecting the PNGs.
"""
import argparse,collections,hashlib,json,pathlib,xml.etree.ElementTree as ET,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--client-run',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True)
    p.add_argument('--cache',type=pathlib.Path,help='Optional read-only raw archive cache for original-file preservation checks')
    p.add_argument('--profile',choices=('w30','w32'),default='w30')
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'art/weapons/w30/manifest.json').read_text())
    preserved=[]
    for m in manifest['models']:
        assert sha((ROOT/f"art/blockbench/weapons/w30/{m['id']}.bbmodel").read_bytes())==m['bbmodel_sha256']
        if args.cache:
            for name,expected_hash in m['source_files'].items():
                path=args.cache/'raw'/m['id']/'extracted'/name
                assert sha(path.read_bytes())==expected_hash,str(path)
                preserved.append(dict(id=m['id'],file=name,sha256=expected_hash))
    references=[]
    for entry in json.loads((ROOT/'art/weapons/w30/style-reference.json').read_text()):
        path=pathlib.Path.home()/'Downloads'/entry['file']
        if path.exists():
            assert sha(path.read_bytes())==entry['sha256'],str(path)
            references.append(entry)
    artifacts=[p for p in (ROOT/'build/libs').glob('*.jar') if 'sources' not in p.name]
    assert len(artifacts)==1,artifacts
    jar=artifacts[0];pack=ROOT/'run/server/polymer/resource_pack.zip'
    source_prefix='src/main/resources/'
    expected={k[len(source_prefix):]:v for k,v in manifest['runtime_sha256'].items()}
    asset_expected={k:v for k,v in expected.items() if k.startswith('assets/')}
    def check_archive(path,entries):
        with zipfile.ZipFile(path) as z:
            for k,v in entries.items():assert sha(z.read(k))==v,(str(path),k)
        return dict(path=str(path),sha256=sha(path.read_bytes()),matched_entries=len(entries))
    jarproof=check_archive(jar,expected);packproof=check_archive(pack,asset_expected)
    for k,v in expected.items():
        assert sha((ROOT/'src/main/resources'/k).read_bytes())==v,k
        assert sha((ROOT/'build/resources/main'/k).read_bytes())==v,k
    classes={}
    with zipfile.ZipFile(jar) as z:
        for f in (ROOT/'build/classes/java/main').rglob('*.class'):
            k=str(f.relative_to(ROOT/'build/classes/java/main'))
            assert z.read(k)==f.read_bytes(),k
            classes[k]=sha(f.read_bytes())
    matches=[]
    for f in args.client_run.rglob('*'):
        if f.is_file() and f.stat().st_size>100000 and zipfile.is_zipfile(f):
            try:matches.append(check_archive(f,asset_expected))
            except KeyError:pass
            except AssertionError:pass
    assert matches,'No client cached pack matching final W30 source'
    captures=json.loads((args.out/'frames/captures.json').read_text())['records']
    for r in captures:
        assert sha((args.out/'frames'/r['file']).read_bytes())==r['sha256']
        assert r['before']['inWorld'] and r['after']['inWorld'] and r['before']['screen'] is None
    counts=dict(collections.Counter(r['context'] for r in captures))
    required=dict(gui=63,hip=63,ads=20,inspect=20,third_front=63)
    if args.profile=='w32':
        required=dict(observer=63,optional_two_hand=9,hip=63,ads=20,inspect=20,third_front=63)
        required.update({'compare_'+grip+'_'+context:1 for grip in ('native','two_hand') for context in ('hip','ads','inspect','third_front')})
    assert counts==required,counts
    native=[]
    if args.profile=='w32':
        for scenario in ('use','attack','move'):
            path=args.out/'native'/scenario/'report.json';report=json.loads(path.read_text())
            assert not report.get('error') and not report.get('monitorError'),str(path)
            state=report['released']
            assert not state['leaseActive'] and not state['heldKeys'] and not state['pendingSteps'],str(path)
            assert not any(state['nativeInput'].values()),str(path)
            assert state['alive'] and state['onGround'] and state['health']==report['before']['health'],str(path)
            assert state['playerY']==report['before']['playerY'],str(path)
            if scenario=='move':
                assert abs(state['playerX']-report['before']['playerX'])+abs(state['playerZ']-report['before']['playerZ'])>1,str(path)
            else:assert state['clicksConsumed']>report['before']['clicksConsumed'],str(path)
            native.append(dict(scenario=scenario,report=str(path.relative_to(args.out)),sha256=sha(path.read_bytes()),released=True))
    tests=[ET.parse(f).getroot() for f in (ROOT/'build/test-results/test').glob('TEST-*.xml')]
    junit={key:sum(int(t.get(key,'0')) for t in tests) for key in ('tests','failures','errors','skipped')}
    connectivity=[]
    for m in manifest['models']:
        cubes=json.loads((ROOT/f"art/blockbench/weapons/w30/{m['id']}.bbmodel").read_text())['elements']
        seen=set();sizes=[]
        for i in range(len(cubes)):
            if i in seen:continue
            queue=[i];seen.add(i);size=0
            while queue:
                a=cubes[queue.pop()];size+=1
                for k,b in enumerate(cubes):
                    if k not in seen and all(a['from'][axis]<=b['to'][axis]+.00001 and b['from'][axis]<=a['to'][axis]+.00001 for axis in range(3)):
                        seen.add(k);queue.append(k)
            sizes.append(size)
        connectivity.append(dict(id=m['id'],cubes=len(cubes),components=sorted(sizes,reverse=True)))
    (args.out/'geometry-connectivity.json').write_text(json.dumps(connectivity,indent=2)+'\n')
    report=dict(scope='18 curated classic families, 63 frame representatives; visual prototypes, not weapon combat',
                jar=jarproof,server_pack=packproof,client_cached_packs=matches,source_and_running_resource_matches=len(expected),
                compiled_class_sha256=classes,junit=junit,frames=counts,
                original_source_files_unchanged=preserved,original_style_references_unchanged=references,
                hand_polished_model_quality_complete=False,
                disconnected_accessory_watchlist=[r for r in connectivity if len(r['components'])>1],
                input_tested=bool(native),native_input_reports=native,
                gui_context_is_world_item_display=args.profile=='w30',full_inventory_screen_tested=False,
                left_hand_live_tested=False,multiplayer_and_performance_tested=False)
    (args.out/'runtime-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(jar_sha256=jarproof['sha256'],source_assets=len(expected),pack_assets=len(asset_expected),matching_cache_packs=len(matches),frames=counts,junit=junit),indent=2))
if __name__=='__main__':main()
