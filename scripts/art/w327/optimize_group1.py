"""Owned W327 output optimization. Read immutable per-weapon baseline JSONs.

Replace overlapping six-box beveled sections with three touching step blocks.
Hand cannon planes are merged only within the same material and moving part,
with less than .001 canonical model-pixel coplanarity error. Shared exporters
are loaded without changing their files.
"""
from pathlib import Path
import ast, copy, hashlib, importlib.util, json, math
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'art/weapons/w327/optimization_rifles'
IDS=['eyasluna','igneous_hammer','nation_of_beasts','submission','hung_jury_sr4']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def save(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,separators=(',',':'))+'\n')
def crop(e,f,lo,hi):
    """Crop face UV in the original local box coordinates."""
    axes={'north':(0,1,True,True),'south':(0,1,False,True),'west':(2,1,False,True),'east':(2,1,True,True),'up':(0,2,False,False),'down':(0,2,False,True)}
    a,b,ra,rb=axes[f];uv=e['faces'][f]['uv'];orig=e['from'];size=[e['to'][i]-orig[i] for i in range(3)]
    def interval(axis,rev):
        p=(lo[axis]-orig[axis])/size[axis];q=(hi[axis]-orig[axis])/size[axis]
        return (1-q,1-p) if rev else (p,q)
    u0,u1=interval(a,ra);v0,v1=interval(b,rb)
    return [uv[0]+(uv[2]-uv[0])*u0,uv[1]+(uv[3]-uv[1])*v0,uv[0]+(uv[2]-uv[0])*u1,uv[1]+(uv[3]-uv[1])*v1]
def step_sections(skin):
    changes=[]
    for part,es in skin['parts'].items():
        by={e['name']:e for e in es};groups=[n[:-4] for n in by if n.endswith('/web') and n[:-4]+'/face' in by]
        remove=set();add=[]
        for n in groups:
            members=[e for e in es if e['name'].startswith(n+'/corner')]
            if len(members)!=4: continue
            web=by[n+'/web'];face=by[n+'/face'];rotation=web.get('rotation');ang=math.radians((rotation or {}).get('x',0))
            # web and face share a center even in pitched grip assemblies.
            c=[(a+b)/2 for a,b in zip(web['from'],web['to'])]
            for side in [-1,1]:
                lo=web['from'].copy();hi=web['to'].copy()
                if side<0:hi[1]=face['from'][1]
                else:lo[1]=face['to'][1]
                q=copy.deepcopy(web);q['name']=n+('/step_lower' if side<0 else '/step_upper')
                q['from']=lo;q['to']=hi
                for f in q['faces']:q['faces'][f]['uv']=crop(web,f,lo,hi)
                if rotation:
                    # Keep original common pivot; no re-anchoring of moving parts.
                    q['rotation']=copy.deepcopy(rotation)
                # Contact faces are inside the touching assembly.
                q['faces'].pop('up' if side<0 else 'down',None)
                add.append(q)
            # Center top/bottom retain the exposed narrow ledges beside the caps.
            q=copy.deepcopy(face);q['name']=n+'/step_center';add.append(q)
            remove.update([web['name'],face['name']]+[e['name'] for e in members]);changes.append(n)
        skin['parts'][part]=[e for e in es if e['name'] not in remove]+add
    return changes
def merge_planes(w):
    path=ROOT/'scripts/art/w327/native_export_v4.py'
    # Invoke the established exporter in a separate output directory and reuse
    # the existing source-coordinate material cache. No source or shared code edit.
    code=path.read_text().replace("/'v4'","/'optimized'").replace("cache=out/'source_bake'","cache=ROOT/'art/weapons/w327'/w/'v4/source_bake'")
    mod={'__file__':str(path),'__name__':'owned_optimized_export'};exec(compile(code,str(path),'exec'),mod)
    rows=load(ROOT/f'art/weapons/w327/{w}/v4/native_planes.json');buckets={};merged=[];maxerr=0
    for r in rows:
        vv=np.array(sum(r['polygons'],[]),dtype=float);a=vv[0];_,_,v=np.linalg.svd(vv-a);n=v[-1]
        if next(x for x in n if abs(x)>1e-6)<0:n=-n
        key=(('/mag_' in r['name']),mod['color_for'](w,r['name']),*(round(float(x),4) for x in n),round(float(n@a),5))
        match=None
        for g in buckets.get(key,[]):
            allv=np.concatenate([g['_vertices'],vv]);_,_,basis=np.linalg.svd(allv-allv[0]);err=float(np.max(np.abs((allv-allv[0])@basis[-1])))
            # Also validate the exporter's actual longest-edge plane, not only SVD.
            trial={'name':g['name'],'polygons':g['polygons']+r['polygons']}
            if err*35<.0008:
                try:p=mod['plane'](trial)
                except AssertionError:continue
                original=mod['plane'](r)
                # Distant disconnected panels can share a plane but waste atlas
                # space when enclosed in one giant rectangle. Only compact unions.
                if p and p['projection_error']<.0008 and p['w']*p['h']<=g['_area']+original['w']*original['h']:
                    match=g;maxerr=max(maxerr,p['projection_error']);break
        if match is None:
            match=copy.deepcopy(r);match['_vertices']=vv;original=mod['plane'](r);match['_area']=original['w']*original['h'];buckets.setdefault(key,[]).append(match);merged.append(match)
        else:
            match['polygons']+=r['polygons'];match['_vertices']=np.concatenate([match['_vertices'],vv]);match['_area']+=original['w']*original['h']
    out=ROOT/f'art/weapons/w327/{w}/optimized';out.mkdir(exist_ok=True)
    save(out/'native_planes.json',[{k:v for k,v in g.items() if not k.startswith('_')} for g in merged]);mod['build'](w)
    skin=load(out/'native_skin.json');save(ROOT/f'src/main/resources/destiny/weapon_skins/{w}.json',skin)
    (ROOT/f'src/main/resources/assets/destiny/textures/item/weapon/w327/{w}.png').write_bytes((out/'native_atlas.png').read_bytes())
    return {'plane_groups_before':len(rows),'plane_groups_after':len(merged),'merge_projection_error_model_px':maxerr}
def main():
    report={}
    for w in IDS:
        base=load(OUT/f'{w}_before.json');before=sum(map(len,base['parts'].values()));faces_before=sum(len(e['faces']) for es in base['parts'].values() for e in es)
        if w in IDS[:3]:change=merge_planes(w)
        else:
            change={'stepped_sections':step_sections(base),'step_corner_extent_max_model_px':.18};save(ROOT/f'src/main/resources/destiny/weapon_skins/{w}.json',base)
        skinpath=ROOT/f'src/main/resources/destiny/weapon_skins/{w}.json';skin=load(skinpath);es=sum(skin['parts'].values(),[])
        assert len(es)<=1000
        assert all(all(math.isfinite(x) and 0<=x<=16 for x in f['uv']) for e in es for f in e['faces'].values())
        assert all(all(a<=b for a,b in zip(e['from'],e['to'])) for e in es)
        info={'before':before,'after':len(es),'faces_before':faces_before,'faces_after':sum(len(e['faces']) for e in es),'parts':{k:len(v) for k,v in skin['parts'].items()},'parse':True,'uv_in_range':True,'native_qa':'pending master',**change};report[w]=info
        art=ROOT/f'art/weapons/w327/{w}';manifest=load(art/'manifest.json');manifest.update(element_total=len(es),elements=info['parts'],optimization=info,optimization_generator='scripts/art/w327/optimize_group1.py')
        for p in [skinpath,ROOT/f'src/main/resources/assets/destiny/textures/item/weapon/w327/{w}.png']:
            manifest['outputs_sha256'][str(p.relative_to(ROOT))]=sha(p)
        save(art/'manifest.json',manifest);save(art/'optimization.json',info)
        validation=load(art/'validation.json');validation.update(total=len(es),elements=info['parts'],uv_in_range=True,atlas=skin['texture_size'],optimization=info,native_qa='pending master; historical ADS profile is not a fresh check')
        save(art/'validation.json',validation)
        if w not in IDS[:3]:
            design=art/'design.py';text=design.read_text();tree=ast.parse(text)
            assignments={n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
            roles=ast.literal_eval(assignments['ROLES'].value);newroles={}
            for e in es:
                name=e['name'];oldname=name
                if '/step_' in name:oldname=name.split('/step_')[0]+('/face' if name.endswith('/step_center') else '/web')
                newroles[name]=roles.get(oldname,roles.get(name.split('/step_')[0]+'/step_center','shell'))
            lines=text.splitlines(keepends=True)
            for key,value in sorted([('ELEMENTS',[{k:v for k,v in e.items() if k!='faces'} for e in es]),('ROLES',newroles)],key=lambda kv:assignments[kv[0]].lineno,reverse=True):
                node=assignments[key];lines[node.lineno-1:node.end_lineno]=[key+'='+repr(value)+'\n']
            design.write_text(''.join(lines))
        print(w,before,'->',len(es),'faces',faces_before,'->',info['faces_after'],flush=True)
    save(OUT/'report.json',report)
if __name__=='__main__':main()
