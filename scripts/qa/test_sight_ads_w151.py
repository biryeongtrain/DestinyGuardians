import copy
import json
import math
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G = runpy.run_path(str(ROOT/'scripts/generate_sight_ads_w151.py'))
read = lambda p: json.loads(p.read_bytes())

def local_point(point, e):
    """Inverse element rotation; source elements here use 26.3 x/y/z rotations."""
    rot=e.get('rotation',{})
    origin=rot.get('origin',[0,0,0])
    v=[p-o for p,o in zip(point,origin)]
    for axis in ('z','y','x'):
        angle=-math.radians(rot.get(axis,rot.get('angle',0) if rot.get('axis')==axis else 0))
        c,s=math.cos(angle),math.sin(angle)
        x,y,z=v
        v=([c*x-s*y,s*x+c*y,z] if axis=='z' else
           [c*x+s*z,y,-s*x+c*z] if axis=='y' else [x,c*y-s*z,s*y+c*z])
    return [p+o for p,o in zip(v,origin)]

def intersects_ray(e, x, y, start, end):
    a,b=local_point([x,y,start],e),local_point([x,y,end],e)
    lo,hi=0.,1.
    for i in range(3):
        d=b[i]-a[i]
        if abs(d)<1e-10:
            if not e['from'][i]+1e-7<a[i]<e['to'][i]-1e-7:return False
        else:
            u,v=sorted(((e['from'][i]-a[i])/d,(e['to'][i]-a[i])/d))
            lo,hi=max(lo,u),min(hi,v)
            if lo>=hi:return False
    return True

class W151SightAds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=read(ROOT/'art/weapons/w151/ads-manifest.json')

    def test_twenty_endpoints_align_actual_sight_and_eye_distance(self):
        self.assertEqual(len(self.manifest['weapons']),20)
        for row in self.manifest['weapons']:
            x,y,z=row['sight']['sightCenter'];s=row['scale']
            for hand,sign in [('righthand',1),('lefthand',-1)]:
                d=row['ads']['firstperson_'+hand];a,b,c=d['translation']
                self.assertEqual(d['rotation'],[0,0,0])
                self.assertAlmostEqual(sign*(.56+a/16+s*(x-8)/16),0,places=6)
                self.assertAlmostEqual(-.52+b/16+s*(y-8)/16,0,places=6)
                self.assertAlmostEqual(-.72+c/16+s*(z-8)/16,-row['eyeToSightMeters'],places=6)

    def test_hip_thirdperson_and_all_old_wrapper_branches_preserved(self):
        for row in self.manifest['weapons']:
            id=row['id'];mapping={}
            for f in range(21):
                for style in ('native','twohand'):
                    key=f'{G["KEY"]}/{id}_{f:02}_{style}'
                    model=read(G['A']/f'models/{key}.json')
                    self.assertEqual(model['parent'],'destiny:'+ (f'weapon/{row["family"]}/{id}' if f==0 else row['body']))
                    d=model['display']
                    baseline=read(G['A']/f'models/weapon_aim_w70/{id}_{f:02}_{style}.json')['display']
                    for context in baseline:
                        if context not in G['FP']:self.assertEqual(d[context],baseline[context],(id,context))
                    if f==0:self.assertEqual(d,baseline)
                    mapping[f'destiny:weapon_aim_w70/{id}_{f:02}_{style}']='destiny:'+key
            old=read(G['A']/f'items/weapon_aim_w70/{id}.json')
            self.assertEqual(read(G['A']/f'items/{G["KEY"]}/{id}.json'),G['remap'](old,mapping))

    def test_rocket_original_surfaces_preserved_except_recorded_opaque_optics(self):
        for row in read(ROOT/'art/weapons/w151/rockets-sights.json')['weapons']:
            source=read(ROOT/row['source']);body=read(G['A']/f'models/{row["body"]}.json')
            old=[e for e in source['elements'] if e['name'] not in row['removedSightNames']]
            self.assertEqual(body['elements'][:len(old)],old)
            self.assertEqual({k:v for k,v in body['textures'].items() if k!='sight'},source['textures'])
            self.assertEqual(len(body['elements']),row['elementCount'])
            self.assertLessEqual(len(body['elements']),1000)

    def test_split_ammit_keeps_seated_magazine_once_during_ads(self):
        row=next(r for r in self.manifest['weapons'] if r['id']=='ammit_ar2')
        sight=row['sight']
        body=read(G['A']/f'models/{sight["body"]}.json')
        magazine=read(ROOT/sight['companionModel'])
        assembled=read(G['A']/f'models/{row["body"]}.json')
        self.assertEqual(assembled['elements'],body['elements']+magazine['elements'])
        self.assertEqual(len(assembled['elements']),128)

    def test_rocket_center_and_near_aperture_rays_clear_rotated_walls(self):
        for row in read(ROOT/'art/weapons/w151/rockets-sights.json')['weapons']:
            body=read(G['A']/f'models/{row["body"]}.json')
            x,y,z=row['sightCenter'];start=z+row['eyeToSightMeters']*16/row['scale']
            end=min(e['from'][2] for e in body['elements'])-2
            for dx,dy in ((0,0),(.04,.04),(-.04,.04)):
                hits=[e['name'] for e in body['elements'] if intersects_ray(e,x+dx,y+dy,start,end)]
                self.assertEqual(hits,[],(row['id'],dx,dy,hits))

    def test_rotated_wall_test_detects_crossing_and_distinguishes_empty_bore(self):
        e={'from':[0,1,-2],'to':[1,2,2], 'rotation':{'origin':[0,0,0],'z':90}}
        self.assertTrue(intersects_ray(e,-1.5,.5,5,-5))
        self.assertFalse(intersects_ray(e,.5,.5,5,-5))

    def test_input_output_hashes_and_determinism(self):
        for p,h in self.manifest['inputSha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        for p,b in G['generate']().items():self.assertEqual(p.read_bytes(),b,p)

    def test_generated_models_and_textures_resolve(self):
        def visit(v):
            if isinstance(v,dict):
                if v.get('type')=='minecraft:model':
                    self.assertTrue((G['A']/('models/'+v['model'].removeprefix('destiny:')+'.json')).is_file(),v)
                for x in v.values():visit(x)
            elif isinstance(v,list):
                for x in v:visit(x)
        for row in self.manifest['weapons']:
            visit(read(G['A']/f'items/{G["KEY"]}/{row["id"]}.json'))
            for slot,value in read(G['A']/f'models/{row["body"]}.json')['textures'].items():
                if not value.startswith('#'):self.assertTrue((G['A']/('textures/'+value.removeprefix('destiny:')+'.png')).is_file(),value)

if __name__=='__main__':unittest.main(verbosity=2)
