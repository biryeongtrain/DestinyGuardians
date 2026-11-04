#!/usr/bin/env python3
"""W118 R5 source drum contour regressions; strict .02/.35 readiness is unchanged.
No native rendering or aesthetic acceptance is implied by a passing core suite.
"""
import base64,hashlib,io,itertools,json,math,subprocess,sys,unittest,zlib,functools
from pathlib import Path
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'art/weapons/w115/hammerhead'
ASSET=ROOT/'src/main/resources/assets/destiny'
PARTS=('body','magazine','cover')
D=json.loads((ART/'design.json').read_bytes())
SOURCE=json.loads(zlib.decompress(base64.b64decode(D['source_reference_zlib_base64'])))
MODELS={p:json.loads((ASSET/f'models/weapon_surface_w115/hammerhead_{p}.json').read_bytes()) for p in PARTS}
ALL=[e for m in MODELS.values() for e in m['elements']]
BYNAME={e['name']:e for e in ALL}
SPECS={s['name']:s for ss in D['parts'].values() for s in ss}
MAN=json.loads((ART/'manifest.json').read_bytes())
TEXTURE=ASSET/'textures/item/weapon/w115/hammerhead.png'
TEX=np.asarray(Image.open(TEXTURE).convert('RGBA'))
FACES=((3,2,0,1),(6,7,5,4),(2,6,4,0),(7,3,1,5),(2,3,7,6),(4,5,1,0))
def sha(data):return hashlib.sha256(data).hexdigest()
def rotate(p,r):
    # Direct successive Rx -> Ry -> Rz, independent of generator matrix code.
    x,y,z=np.asarray(p)-r['origin'];a,b,c=map(math.radians,[r[k] for k in 'xyz'])
    y,z=y*math.cos(a)-z*math.sin(a),y*math.sin(a)+z*math.cos(a)
    x,z=x*math.cos(b)+z*math.sin(b),-x*math.sin(b)+z*math.cos(b)
    x,y=x*math.cos(c)-y*math.sin(c),x*math.sin(c)+y*math.cos(c)
    return np.array([x,y,z])+r['origin']
def corners(e):
    return np.array([rotate([e['to' if mask>>a&1 else 'from'][a] for a in range(3)],e['rotation']) for mask in range(8)])
def surface_points(s):
    return np.array(s['triangle_vertices']) if s['kind']=='triangle_plane' else corners(BYNAME[s['name']])
def surface_triangles(s):
    if s['kind']=='triangle_plane':return [s['triangle_vertices']]
    e=BYNAME[s['name']];v=corners(e);return [v[list(f)][list(ix)] for name,f in zip(('north','south','west','east','up','down'),FACES) if name in e['faces'] for ix in ((0,1,2),(0,2,3))]
def uv_pixels(f):
    u,v,s,t=f['uv'];x0,x1=sorted([round(u*64),round(s*64)]);y0,y1=round(v*64),round(t*64)
    return x0,y0,x1,y1

def independent_distance(points,triangles):
    # Independent plane projection + oriented-edge inclusion + clamped segments.
    t=np.asarray(triangles);a,b,c=t[:,0],t[:,1],t[:,2];n=np.cross(b-a,c-a);nn=(n*n).sum(1)
    result=[]
    for p in points:
        q=p-((p-a)*n).sum(1)[:,None]*n/np.maximum(nn[:,None],1e-30)
        inside=nn>1e-20
        for u,v in ((a,b),(b,c),(c,a)):
            inside &= (np.cross(v-u,q-u)*n).sum(1)>=-1e-12
        dist=np.where(inside,((q-p)**2).sum(1),np.inf)
        for u,v in ((a,b),(b,c),(c,a)):
            edge=v-u;h=np.clip(((p-u)*edge).sum(1)/np.maximum((edge*edge).sum(1),1e-30),0,1)
            dist=np.minimum(dist,((u+h[:,None]*edge-p)**2).sum(1))
        result.append(math.sqrt(float(dist.min())))
    return np.array(result)

def opaque_palette_size(tex):
    return len(np.unique(tex[:,:,:3][tex[:,:,3]==255],axis=0))

@functools.lru_cache(maxsize=None)
def independent_component_distances(cid):
    raw=np.array([SOURCE[i]['points'] for i in D['components'][cid]['source_indices']]);out=np.array([t for s in SPECS.values() if s['component']==cid for t in surface_triangles(s)])
    return independent_distance(raw.reshape(-1,3),out)

class HammerheadR5Tests(unittest.TestCase):
    def test_01_original_and_frozen_input_pins(self):
        self.assertEqual(len(D['input_sha256']),17);self.assertEqual(len(D['r2_input_sha256']),6)
        for p,h in {**D['input_sha256'],**D['r2_input_sha256']}.items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
        self.assertEqual(len(D['raw_input_sha256']),2)
        for p,h in D['raw_input_sha256'].items():self.assertEqual(sha(Path(p).read_bytes()),h,p)
        self.assertEqual(sha((ASSET/'models/weapon/machine_gun/hammerhead.json').read_bytes()),'7890eb2e60dc2a6547c7af7278a079b9e28575fd186683769c41f3c725c990bb')
        self.assertEqual(len(json.loads((ASSET/'models/weapon/machine_gun/hammerhead.json').read_bytes())['elements']),223)
    def test_02_native_schema_no_raw_mesh(self):
        self.assertEqual(D['revision'],'r5');self.assertEqual(MAN['revision'],'r5')
        for m in MODELS.values():
            self.assertEqual(set(m),{'credit','textures','elements'})
            self.assertEqual(m['textures'],{'0':'destiny:item/weapon/w115/hammerhead','particle':'destiny:item/weapon/w115/hammerhead'});self.assertTrue(m['elements'])
        for e in ALL:
            self.assertEqual(set(e),{'name','from','to','rotation','faces'});self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
            self.assertTrue(np.isfinite([*e['from'],*e['to'],*e['rotation']['origin'],*[e['rotation'][k] for k in 'xyz']]).all())
            self.assertTrue(all(-16<=v<=32 for v in e['from']+e['to']))
    def test_03_named_complete_disjoint_parts(self):
        self.assertEqual(len(BYNAME),len(ALL));self.assertEqual(set(BYNAME),set(SPECS))
        self.assertEqual({s['component'] for s in SPECS.values()},set(range(272)))
        for p in PARTS:
            self.assertEqual({e['name'] for e in MODELS[p]['elements']},{s['name'] for s in D['parts'][p]})
            for s in D['parts'][p]:self.assertEqual(D['components'][s['component']]['part'],p)
    def test_04_original_component_triangle_ledger(self):
        self.assertEqual(len(SOURCE),25499);self.assertEqual(len(D['components']),272)
        indices=[i for c in D['components'] for i in c['source_indices']]
        self.assertEqual(len(indices),len(set(indices)));self.assertEqual(set(indices),set(range(25499)))
        for c in D['components']:
            self.assertTrue(c['source_indices'])
            for i in c['source_indices']:
                t=SOURCE[i];self.assertEqual([t['mesh'],t['component'],t['bone']],c['key']);self.assertEqual(t['part'],c['part'])
        # Ledger retention is NOT a claim of exact geometric coverage.
    def test_05_original_coordinate_frame_and_pivots(self):
        ps=np.array([p for t in SOURCE for p in t['points']]);bounds=np.array([ps.min(0),ps.max(0)])
        np.testing.assert_allclose(bounds,D['expected_bounds'],atol=1e-10)
        np.testing.assert_allclose(bounds,[[4.6067723388,7.0003479322,-11.8837227988],[12.9274243878,14.6254133012,15.1162772012]],atol=1e-9)
        audit=json.loads((ROOT/'art/weapons/w114/hammerhead/original-model-audit.json').read_bytes())
        self.assertEqual(D['cover_pivot'],audit['coverHinge']['modelPivot']);self.assertEqual(MAN['cover_pivot'],D['cover_pivot'])
        self.assertEqual(D['body_pivot'],[8,8,8]);self.assertEqual(D['magazine_pivot'],[8,8,8])
    def test_06_independent_euler_triangle_corners(self):
        for s in SPECS.values():
            if s['kind']!='triangle_plane':continue
            e=BYNAME[s['name']];lo,hi=np.array(e['from']),np.array(e['to']);self.assertEqual(lo[2],hi[2])
            pts=[rotate([lo[0],lo[1],lo[2]],e['rotation']),rotate([hi[0],lo[1],lo[2]],e['rotation']),rotate([lo[0],hi[1],lo[2]],e['rotation'])]
            np.testing.assert_allclose(pts,s['triangle_vertices'],atol=1e-8)
            self.assertEqual(set(e['faces']),{'south','north'})
    def test_07_source_fitted_segmented_broad_panels(self):
        for tag,count in [('receiver_lower',33),('vented_shroud',45),('hinged_cover_shell',21),('pistol_grip',21),('stock_open_strut',19)]:
            specs=[s for s in SPECS.values() if s['name'].startswith(tag) and s['kind']=='source_panel'];self.assertEqual(len(specs),count)
            for s in specs:
                self.assertTrue(s['source_indices']);self.assertTrue(set(s['source_indices'])<=set(D['components'][s['component']]['source_indices']))
        panels=[s for s in D['parts']['body'] if s['kind']=='source_panel'];self.assertEqual(len(panels),478)
        self.assertGreater(sum(np.prod(sorted(np.array(s['geometry']['to'])-s['geometry']['from'])[-2:])>.5 for s in panels),20)
        self.assertTrue(any(any(abs(s['geometry']['rotation'][a]%90)>1e-3 for a in 'xyz') for s in panels))
        self.assertFalse(set(BYNAME)&{'shroud_planar_flank','receiver_left_wall','box_front_panel'})
    def test_08_broad_faces_opaque_and_only_curved_magazine_cards(self):
        curved={34,35};seen=set()
        for p,ss in D['parts'].items():
            for s in ss:
                e=BYNAME[s['name']]
                if s['kind']=='triangle_plane':self.assertEqual(p,'magazine');seen.add(s['component'])
                else:
                    self.assertEqual(set(e['faces']),{'south','north'} if s['kind']=='source_drum_shell' else {'north','south','west','east','up','down'})
                    for f in e['faces'].values():
                        x,y,x1,y1=uv_pixels(f);self.assertTrue((TEX[y:y1,x:x1,3]==255).all(),s['name'])
        self.assertEqual(seen,curved);self.assertEqual(MAN['body_cover_triangle_planes'],0)
        self.assertTrue(any(np.array(e['to'])[2]==e['from'][2] for e in D['frozen_r2']['models']['body']['elements']))
    def test_09_reload_anatomy_boundaries(self):
        for c in D['components']:
            bone=c['key'][2];expected='magazine' if bone=='Magazine' or bone.startswith('Bullet') else 'cover' if bone=='Cover' else 'body'
            self.assertEqual(c['part'],expected,c['name'])
        self.assertEqual({t['bone'] for t in SOURCE if t['part']=='magazine'},set(['Magazine']+[f'Bullet{i}' for i in range(1,9)]))
        self.assertTrue(all(t['part']=='cover' for t in SOURCE if t['mesh']=='Hammerhead.02.000'))
    def test_10_reviewed_counts_not_engine_performance_claim(self):
        self.assertEqual({p:len(m['elements']) for p,m in MODELS.items()},{'body':624,'magazine':562,'cover':143})
        self.assertEqual(len(ALL),1329);self.assertLessEqual(len(ALL),2048)
        cards=sum(s['kind']=='triangle_plane' for s in SPECS.values());self.assertEqual(cards,250);self.assertEqual(len(ALL)-cards,1079)
        self.assertEqual(sum(len(e['faces']) for e in ALL),6110);self.assertLessEqual(sum(len(e['faces']) for e in ALL),6144)
        self.assertEqual(MAN['review_budget']['faces'],6144)
        for e in ALL:
            dims=np.array(e['to'])-e['from'];self.assertTrue((dims>=0).all());self.assertGreater(np.prod(sorted(dims)[-2:]),1e-9)
    def test_11_valid_uv_shared_material_islands(self):
        self.assertEqual(TEX.shape,(1024,1024,4));self.assertEqual(set(np.unique(TEX[:,:,3])),{0,255})
        used={}
        for e in ALL:
            s=SPECS[e['name']];kind='triangle' if s['kind']=='triangle_plane' else 'grip' if s['material']=='rubber' else 'solid'
            for f in e['faces'].values():
                self.assertEqual(f['texture'],'#0');self.assertTrue(all(0<=v<=16 for v in f['uv']))
                x,y,x1,y1=uv_pixels(f);self.assertEqual((x1-x,y1-y),(128,128))
                used.setdefault((s['material'],kind),set()).add((x,y,x1,y1))
        self.assertTrue(all(len(rects)==1 for rects in used.values()))
        rects=[next(iter(v)) for v in used.values()]
        for a,b in itertools.combinations(rects,2):self.assertTrue(a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1])
    def test_12_four_pixel_extruded_gutters(self):
        self.assertEqual(D['atlas']['gutter'],4);g=4
        rects={uv_pixels(f) for e in ALL for f in e['faces'].values()}
        for x,y,x1,y1 in rects:
            tile=TEX[y:y1,x:x1];expected=np.pad(tile,((g,g),(g,g),(0,0)),mode='edge')
            np.testing.assert_array_equal(TEX[y-g:y1+g,x-g:x1+g],expected)
    def test_13_clean_palette_rejects_r2_fragment_noise(self):
        self.assertLessEqual(opaque_palette_size(TEX),20)
        r2=np.asarray(Image.open(io.BytesIO(base64.b64decode(D['frozen_r2']['texture_png']))).convert('RGBA'))
        self.assertGreater(opaque_palette_size(r2),1000) # Concrete negative control, not a relaxed R2 gate.
        self.assertEqual(len(D['palette']),8)
        self.assertTrue({'red','graphite','steel','silver','rubber','inset','link','brass'}<=set(D['palette']))
        self.assertEqual(MAN['palette'],D['palette'])
    def test_14_triangle_mask_and_doubleface_mirroring(self):
        for s in SPECS.values():
            if s['kind']!='triangle_plane':continue
            e=BYNAME[s['name']];south=e['faces']['south'];north=e['faces']['north'];u,v,u1,v1=south['uv']
            self.assertEqual(north['uv'],[u1,v,u,v1]);x,y,x1,y1=uv_pixels(south)
            uu,vv=np.meshgrid((np.arange(128)+.5)/128,(np.arange(128)+.5)/128)
            np.testing.assert_array_equal(TEX[y:y1,x:x1,3],np.where(uu<=vv,255,0))
            self.assertEqual(len(np.unique(TEX[y:y1,x:x1,:3].reshape(-1,3),axis=0)),1)
    def test_15_editable_embedded_inspection(self):
        bb=json.loads((ART/'inspection.bbmodel').read_bytes());self.assertEqual(bb['meta']['model_format'],'java_block');self.assertEqual(bb['name'],'Hammerhead W118 R5 source-fitted panels')
        self.assertEqual(bb['resolution'],{'width':1024,'height':1024});self.assertEqual({g['name'] for g in bb['outliner']},set(PARTS));self.assertEqual(len(bb['elements']),1329)
        ids=[e['uuid'] for e in bb['elements']];self.assertEqual(len(ids),len(set(ids)));self.assertCountEqual(ids,[c for g in bb['outliner'] for c in g['children']])
        self.assertEqual(next(g for g in bb['outliner'] if g['name']=='cover')['origin'],D['cover_pivot'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',',1)[1]),TEXTURE.read_bytes())
        for e in bb['elements']:
            self.assertEqual(set(e['faces']),{'north','south','east','west','up','down'})
            for name,f in e['faces'].items():
                native=BYNAME[e['name']]['faces'].get(name)
                if native is None:self.assertIsNone(f['texture']);self.assertEqual(f['uv'],[0,0,0,0])
                else:self.assertEqual(f['texture'],0);np.testing.assert_allclose(f['uv'],np.array(native['uv'])*64)
    def test_16_actual_six_revision_eight_view_comparison(self):
        im=Image.open(ART/'comparison.png');self.assertEqual(im.size,(4560,2500));pixels=np.asarray(im)
        for row in range(8):
            for col in range(6):
                if row>=6 and col in (1,2):continue # Old R1/R2 have no matching per-component names.
                tile=pixels[90+300*row:335+300*row,col*760+20:col*760+740]
                self.assertGreater(np.count_nonzero(tile.max(2)-tile.min(2)>15),100)
        self.assertEqual(sum(len(m['elements']) for m in D['rejected_r1']['models'].values()),86)
        self.assertEqual(sum(len(m['elements']) for m in D['frozen_r2']['models'].values()),1635)
    def test_17_top_ads_profile_black_patch_negative_controls(self):
        self.assertEqual(len(MAN['fidelity_iou']),6)
        for row in MAN['fidelity_iou'].values():
            self.assertGreater(row['source_pixels'],10000);self.assertGreater(row['r3_iou'],row['r2_iou'],row['view']);self.assertGreater(row['r4_iou'],row['r2_iou'],row['view']);self.assertGreater(row['r4_iou'],.92);self.assertGreater(row['r5_iou'],row['r2_iou'],row['view']);self.assertGreater(row['r5_iou'],.92);self.assertEqual(row['r5_opaque_black_mismatch_pixels'],0)
            self.assertGreater(row['r4_missing_source_pixels'],0);self.assertEqual(row['r4_opaque_black_mismatch_pixels'],0)
            self.assertGreater(row['r2_opaque_black_mismatch_pixels'],0)
        self.assertIn('TOP',MAN['fidelity_iou']['3']['view']);self.assertIn('ADS',MAN['fidelity_iou']['4']['view'])
        # Profile coverage worsens despite improved IoU: keep this limitation visible.
        self.assertGreater(MAN['fidelity_iou']['0']['r3_missing_source_pixels'],MAN['fidelity_iou']['0']['r2_missing_source_pixels'])
        self.assertFalse(MAN['native_accepted']);self.assertFalse(MAN['aesthetic_final'])
    def test_18_actual_bounds_diagnostic_not_false_exactness(self):
        points=np.concatenate([surface_points(s) for s in SPECS.values()]);actual=np.array([points.min(0),points.max(0)])
        np.testing.assert_allclose(actual,MAN['actual_surface_bounds'],atol=1e-9)
        np.testing.assert_allclose(actual,D['expected_bounds'],atol=.02,rtol=0)
        self.assertGreater(D['frozen_r3']['actual_surface_bounds'][1][1],D['expected_bounds'][1][1]+.1)
    def test_19_independent_per_component_envelope_diagnostics(self):
        self.assertEqual(set(MAN['spatial_deviation']),{str(i) for i in range(272)})
        for cid,c in enumerate(D['components']):
            points=np.concatenate([surface_points(s) for s in SPECS.values() if s['component']==cid]);bounds=np.array(c['bounds'])
            over=max(0,float(np.maximum(bounds[0]-points,points-bounds[1]).max()))
            self.assertAlmostEqual(over,MAN['spatial_deviation'][str(cid)]['source_envelope_protrusion'],places=8)
    def test_20_independent_distance_all_source_components(self):
        for cid in range(272):
            distances=independent_component_distances(cid)
            self.assertAlmostEqual(float(distances.max()),MAN['spatial_deviation'][str(cid)]['source_to_output_max'],places=7)
            self.assertAlmostEqual(float(np.quantile(distances,.95)),MAN['spatial_deviation'][str(cid)]['source_to_output_p95'],places=7)
            self.assertLessEqual(float(np.quantile(distances,.95)),.35,D['components'][cid]['name'])
    def test_21_exact_owned_manifest_hashes(self):
        batch=json.loads((ROOT/'docs/qa/2026-10-25/w118/batch.json').read_bytes())
        owned=next(f['owned_paths'] for f in batch['features'] if f['name']=='w118-hammerhead')
        self.assertEqual(set(MAN['changed_paths']),set(owned));self.assertEqual(len(owned),12)
        self.assertEqual(set(MAN['output_sha256']),set(owned)-{'art/weapons/w115/hammerhead/manifest.json'})
        for p,h in MAN['output_sha256'].items():self.assertEqual(sha((ROOT/p).read_bytes()),h,p)
    def test_22_deterministic_read_only_verify_twice(self):
        before={p:((ROOT/p).read_bytes(),(ROOT/p).stat().st_mtime_ns) for p in MAN['changed_paths']}
        for _ in range(2):
            run=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/generate_surface_w115_hammerhead.py'),'--verify'],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        for p,(data,mtime) in before.items():self.assertEqual((ROOT/p).read_bytes(),data,p);self.assertEqual((ROOT/p).stat().st_mtime_ns,mtime,p)
    def test_23_source_and_common_compiler_provenance(self):
        self.assertEqual(len(D['source_albedo_png_base64']),3)
        for v in D['source_albedo_png_base64'].values():self.assertGreaterEqual(min(Image.open(io.BytesIO(base64.b64decode(v))).size),512)
        ref=D['compiler_reference'];self.assertEqual(ref['path'],'scripts/mesh/native_triangle_elements_w115.py');self.assertFalse(ref['shipped_in_worker'])
        self.assertEqual(sha((ROOT/ref['path']).read_bytes()),ref['sha256']);self.assertNotIn(ref['path'],MAN['changed_paths'])
    def test_24_selected_real_aperture_samples_remain_open(self):
        # Finite samples, not a whole-mesh topology proof. Muzzle bore not certified.
        for point in ([8,14.1,3.38],[8,9.8,11.5],[8,9.93,6.1]):
            for s in SPECS.values():
                if s['kind']=='triangle_plane':continue
                e=BYNAME[s['name']];o=np.array(e['rotation']['origin']);basis=np.array([rotate(o+np.eye(3)[i],e['rotation'])-o for i in range(3)])
                local=(np.array(point)-o)@basis.T+o
                self.assertFalse(np.all(local>np.array(e['from'])+1e-7) and np.all(local<np.array(e['to'])-1e-7),s['name'])

    def test_25_frozen_r3_negative_controls_still_rejected(self):
        prior=D['frozen_r3'];old=prior['spatial_deviation']
        self.assertEqual(sum(v['source_envelope_protrusion']>.02 for v in old.values()),69)
        self.assertEqual({int(k) for k,v in old.items() if v['source_to_output_p95']>.35},{39,44,50,99,100,133})
        self.assertGreater(prior['actual_surface_bounds'][1][1]-D['expected_bounds'][1][1],.129)
        for part,model in prior['models'].items():
            data=(json.dumps(model,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
            self.assertEqual(sha(data),prior['model_sha256'][part])
        # Re-evaluate two old failing geometries independently, not only stored old metrics.
        historical_specs={**{s['name']:s for s in D['r5_previous_cap_specs']},**SPECS}
        for cid in (39,133):
            tris=[]
            for m in prior['models'].values():
                for e in m['elements']:
                    if historical_specs[e['name']]['component']!=cid:continue
                    v=corners(e)
                    tris.extend(v[list(f)][list(ix)] for f in FACES for ix in ((0,1,2),(0,2,3)))
            raw=np.array([SOURCE[i]['points'] for i in D['components'][cid]['source_indices']])
            self.assertGreater(float(np.quantile(independent_distance(raw.reshape(-1,3),np.array(tris)),.95)),.35)
    def test_26_source_patch_repair_not_replaced_anatomy(self):
        restored=[s for s in SPECS.values() if '_r4_restore_' in s['name']]
        self.assertEqual(len(restored),16)
        self.assertEqual({s['component'] for s in restored},{39,42,44,50,99,100,133,157})
        for s in restored:
            self.assertEqual(s['kind'],'source_panel');self.assertTrue(s['source_indices'])
            self.assertTrue(set(s['source_indices'])<=set(D['components'][s['component']]['source_indices']))
            self.assertGreater(s['r4_refit']['source_patch_area'],.002)
        oldnames={e['name'] for m in D['frozen_r3']['models'].values() for e in m['elements']}
        self.assertTrue(oldnames<=set(SPECS)|{s['name'] for s in D['r5_previous_cap_specs']})
    def test_27_original_right_belt_extension_not_an_invented_spike(self):
        cids={i for i,c in enumerate(D['components']) if c['key'][2].startswith('Bullet')}
        source=np.array([p for i in cids for idx in D['components'][i]['source_indices'] for p in SOURCE[idx]['points']])
        output=np.concatenate([surface_points(s) for s in SPECS.values() if s['component'] in cids])
        np.testing.assert_allclose([output.min(0),output.max(0)],[source.min(0),source.max(0)],atol=.02,rtol=0)
        self.assertGreater(source[:,0].max(),12.92)

    def test_28_drum_rings_are_original_vertices_not_idealized_circles(self):
        for cid in (45,46,47,48):
            evidence=D['r5_drum_refinement'][str(cid)]
            raw=np.array([SOURCE[i]['points'] for i in D['components'][cid]['source_indices']]).reshape(-1,3)
            for key in ('front_ring','outer_ring'):
                ring=np.array(evidence[key]);self.assertEqual(ring.shape,(36,3))
                nearest=np.linalg.norm(ring[:,None,:]-raw[None,:,:],axis=2).min(1)
                self.assertLess(nearest.max(),1e-6)
            specs=[s for s in SPECS.values() if s['component']==cid]
            self.assertEqual(len(specs),54)
            self.assertEqual({key:sum(s['r5_region']==key for s in specs) for key in ('cap','bevel','rim')},{'cap':18,'bevel':18,'rim':18})
            for s in specs:
                self.assertEqual(s['kind'],'source_drum_shell');self.assertEqual(s['material'],'steel')
                self.assertEqual(s['source_indices'],D['components'][cid]['source_indices'])
                self.assertEqual(set(BYNAME[s['name']]['faces']),{'north','south'})
                self.assertAlmostEqual(s['geometry']['to'][2]-s['geometry']['from'][2],.002)

    def test_29_cap_center_has_no_alpha_or_geometric_radial_tears(self):
        for cid in (45,46,47,48):
            caps=[s for s in SPECS.values() if s['component']==cid and s.get('r5_region')=='cap']
            ring=np.array(D['r5_drum_refinement'][str(cid)]['front_ring']);center=ring.mean(0)
            # Dense interior rays, not only corner/bounds agreement. No texture transparency allowed.
            points=np.array([center+np.array([r*math.cos(a),r*math.sin(a),0]) for r in np.linspace(0,1.1,13) for a in np.linspace(0,2*math.pi,181)])
            covered=np.zeros(len(points),dtype=bool)
            for s in caps:
                e=BYNAME[s['name']];o=np.array(e['rotation']['origin']);basis=np.array([rotate(o+np.eye(3)[i],e['rotation'])-o for i in range(3)])
                local=(points-o)@basis.T+o
                covered |= np.all((local[:,:2]>=np.array(e['from'])[:2]-1e-7)&(local[:,:2]<=np.array(e['to'])[:2]+1e-7),axis=1)
                for f in e['faces'].values():
                    x,y,x1,y1=uv_pixels(f);self.assertTrue((TEX[y:y1,x:x1,3]==255).all())
            self.assertTrue(covered.all(),f'cap {cid}: {int((~covered).sum())} interior rays missed')

    def test_30_actual_cap_projection_rejects_frozen_r4_octagons_and_seams(self):
        for row in MAN['drum_detail_comparison'].values():
            self.assertGreater(row['r5_iou'],row['r4_iou']+.04,row['view'])
            self.assertGreater(row['r5_iou'],.97,row['view'])
            self.assertLess(row['r5_interior_missing_pixels'],20,row['view'])
            self.assertGreater(row['r4_interior_missing_pixels'],2000,row['view'])
            self.assertEqual(row['r5_opaque_black_mismatch_pixels'],0)
        self.assertGreater(MAN['fidelity_iou']['4']['r5_iou'],MAN['fidelity_iou']['4']['r4_iou'])

    def test_31_frozen_r4_and_untouched_anatomy_byte_identity(self):
        prior=D['frozen_r4']
        for p,m in prior['models'].items():
            self.assertEqual(sha((json.dumps(m,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()),prior['model_sha256'][p])
        for p in ('body','cover'):self.assertEqual(MODELS[p]['elements'],prior['models'][p]['elements'])
        old={e['name']:e for e in prior['models']['magazine']['elements']}
        old_caps={s['name'] for s in D['r5_previous_cap_specs']}
        unchanged={e['name']:e for e in MODELS['magazine']['elements'] if SPECS[e['name']]['component'] not in (45,46,47,48)}
        self.assertEqual(unchanged,{name:e for name,e in old.items() if name not in old_caps})
        # Texture also unchanged: no source-alias resampling to disguise geometric defects.
        self.assertEqual(base64.b64decode(prior['texture_png']),TEXTURE.read_bytes())

class SpatialReadinessTests(unittest.TestCase):
    """Deliberately strict original-envelope criteria; failures are NOT waived by core tests."""
    def test_01_actual_source_bounds_and_sight(self):
        points=np.concatenate([surface_points(s) for s in SPECS.values()]);actual=np.array([points.min(0),points.max(0)])
        np.testing.assert_allclose(actual,D['expected_bounds'],atol=.02,rtol=0,err_msg='Original bounds/sight readiness not achieved; native review required.')
    def test_02_no_component_protrusions(self):
        bad={}
        for cid,c in enumerate(D['components']):
            points=np.concatenate([surface_points(s) for s in SPECS.values() if s['component']==cid]);bounds=np.array(c['bounds'])
            over=max(0,float(np.maximum(bounds[0]-points,points-bounds[1]).max()))
            if over>.02:bad[str(cid)]=round(over,6)
        self.assertFalse(bad,'Local source-envelope protrusions >.02: '+json.dumps(bad))
    def test_03_source_coverage(self):
        bad={str(cid):float(np.quantile(independent_component_distances(cid),.95)) for cid in range(272) if np.quantile(independent_component_distances(cid),.95)>.35}
        self.assertFalse(bad,'Source-to-output surface p95 >.35: '+json.dumps(bad))
if __name__=='__main__':
    readiness='--readiness' in sys.argv
    if readiness:sys.argv.remove('--readiness')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SpatialReadinessTests if readiness else HammerheadR5Tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(0 if result.wasSuccessful() else 1)
