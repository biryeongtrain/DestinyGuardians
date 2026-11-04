import copy
import json
import math
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G = runpy.run_path(str(ROOT/'scripts/generate_sight_ads_w153.py'))
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

class W153SightAds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=read(ROOT/'art/weapons/w153/ads-manifest.json')

    def test_eighteen_endpoints_align_actual_sight_and_eye_distance(self):
        self.assertEqual(len(self.manifest['weapons']),18)
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
            expected=G['remap'](old,mapping)
            if row['family']=='fusion_rifle':expected['swap_animation_scale']=0.0
            self.assertEqual(read(G['A']/f'items/{G["KEY"]}/{id}.json'),expected)

    def test_declared_assembled_body_budget_and_eye_contract(self):
        for row in self.manifest['weapons']:
            sight=row['sight'];body=read(G['A']/f'models/{row["body"]}.json')
            self.assertTrue(1 <= len(body['elements']) <= 1000)
            self.assertEqual(len(body['elements']), sight.get('assemblyElementCount',sight['elementCount']))
            self.assertEqual(sight['eyeSide'],'+Z')
            self.assertTrue(.1 <= row['eyeToSightMeters'] <= 1)

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
