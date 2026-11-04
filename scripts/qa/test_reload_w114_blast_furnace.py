#!/usr/bin/env python3
"""Isolated W114 regression. No Gradle, game, DCC, network or source mutations.

Bundled Python supplies numpy/Pillow. Optional --junit writes XML outside worktree.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import struct
import sys
import unittest
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w114_blast_furnace.py'))
A=G['ASSETS'];ART=G['ART'];KEY='weapon_reload_w114_blast_furnace/blast_furnace'
MAG=[54,110,112,113,116,118,120,124,132,139,143,149]
SOURCE_SHA='f3922a28cc58de8c7a7f965ba3464aeb5841d1a53bde72bf74d58e48aca39706'
TEX_SHA='0f252ca03244d8b2d7d5c63e9d67c90dc87e6bbac3faeb402572aacb7df4cd91'

def read(p):return json.loads(Path(p).read_bytes())
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def matrix(pose,left=False):
    r=np.radians(pose['rotation']);s=-1 if left else 1
    a,b,c=r[0],r[1]*s,r[2]*s
    rx=np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]])
    ry=np.array([[np.cos(b),0,np.sin(b)],[0,1,0],[-np.sin(b),0,np.cos(b)]])
    rz=np.array([[np.cos(c),-np.sin(c),0],[np.sin(c),np.cos(c),0],[0,0,1]])
    m=np.eye(4);m[:3,:3]=rx@ry@rz@np.diag(pose['scale']);m[:3,3]=np.array(pose['translation'])*[s,1,1]/16
    return m

class Reload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=G['generate']();cls.source=read(G['BASE']);cls.item=read(A/'items/weapon/blast_furnace.json')
        cls.audit=json.loads(cls.outputs[ART/'partition-audit.json'])
    def pose(self,frame,part,grip='native'):
        return json.loads(self.outputs[A/f'models/{KEY}_{frame:02d}_{part}_{grip}.json'])
    def test_01_deterministic_check_all_93_files(self):
        self.assertEqual(93,len(self.outputs));G['write_outputs'](self.outputs,True)
    def test_02_exact_owned_asset_inventory(self):
        paths={p for p in self.outputs if p.is_relative_to(A)}
        self.assertEqual(87,len(paths));self.assertTrue(all(str(p.relative_to(ROOT)) in G['owned_paths']() for p in self.outputs))
        actual=set((A/'models/weapon_reload_w114_blast_furnace').glob('*.json'))|set((A/'items/weapon_reload_w114_blast_furnace').glob('*.json'))
        self.assertEqual(paths,actual);self.assertFalse(any('cover' in p.name for p in paths))
    def test_03_independent_original_pins(self):
        self.assertEqual(SOURCE_SHA,G['sha'](G['BASE'].read_bytes()))
        self.assertEqual(TEX_SHA,G['sha']((A/'textures/item/weapon/w30/blast_furnace.png').read_bytes()))
        for path,pin in G['PINS'].items():self.assertEqual(pin,G['sha']((ROOT/path).read_bytes()),path)
    def test_04_whole_elements_uv_texture_conservation(self):
        restored={}
        self.assertEqual(MAG,self.audit['parts']['magazine'])
        for part,count in [('body',237),('magazine',12)]:
            geo=json.loads(self.outputs[A/f'models/{KEY}_{part}.json']);self.assertEqual(count,len(geo['elements']))
            self.assertEqual({k:v for k,v in self.source.items() if k not in ('elements','display')},{k:v for k,v in geo.items() if k!='elements'})
            for i,e in zip(self.audit['parts'][part],geo['elements'],strict=True):
                self.assertNotIn(i,restored);restored[i]=e
        self.assertEqual(self.source['elements'],[restored[i] for i in range(249)])
        self.assertLessEqual(len(restored),256)
    def test_05_semantic_source_components_and_material(self):
        self.assertEqual(29124,self.audit['sourceTriangles']);self.assertEqual(681,self.audit['magazineTriangles'])
        comps=[c for c in self.audit['sourceComponents'] if c['magazineTriangles']]
        self.assertEqual([18,46,49,60,63,95,109],[c['component'] for c in comps])
        self.assertTrue(all(c['triangleCount']==c['magazineTriangles'] and c['material']=='Frame' and c['mesh']=='Blast-Furnace.00.003' for c in comps))
        weights=self.audit['sourceMeshes'][0]['boneWeights']['Magazine']
        self.assertEqual(dict(vertexCount=575,minWeight=1.0,maxWeight=1.0),weights)
        self.assertEqual(270,len(self.audit['sourceComponents']))
    def test_06_clipped_area_membership_not_bbox(self):
        for row in self.audit['cubes']:
            self.assertGreater(row['clippedArea'],0)
            self.assertEqual(row['index'] in MAG,row['magazineAreaShare']>.5)
            self.assertAlmostEqual(row['clippedArea'],sum(v['area'] for v in row['sourceSurfaces']),places=9)
            self.assertEqual(G['sha'](G['encode'](self.source['elements'][row['index']])),row['originalElementSha256'])
        ap=self.audit['approximation'];self.assertEqual([57,59,61],ap['distanceDisagreements'])
        self.assertTrue(.58<ap['capturedClippedMagazineFraction']<.59)
        self.assertTrue(.53<ap['capturedRawMagazineFraction']<.54)
        self.assertEqual([54,110,112,113,124,132,143,149],ap['mixedSelected'])
        self.assertFalse(ap['perfectMagazineExtraction'])
        region=ap['upperWellResidual'];self.assertEqual([49,50,57,59,61,196],region['retainedIndices'])
        self.assertTrue(.9982<region['retainedAboveUpperMergeFraction']<.9983)
        self.assertTrue(.9982<region['lowerRegionCapturedFraction']<.9983)
        self.assertAlmostEqual(17.85397843414108,region['retainedClippedMagazineArea'],places=8)
        self.assertAlmostEqual(3.6236109117125466,region['rawAreaOutsideOriginalCubes'],places=8)
    def test_07_surface_distance_analytic_oracle(self):
        tri=np.array([[[0,0,0],[1,0,0],[0,1,0]]],dtype=float)
        actual=G['point_triangle_distances']([[.25,.25,2],[2,0,0],[-1,-1,0],[.5,.5,0]],tri)
        np.testing.assert_allclose(actual,[2,1,math.sqrt(2),0],atol=1e-10)
        # Degenerate source triangles still use their finite segments.
        deg=np.array([[[0,0,0],[1,0,0],[1,0,0]]],dtype=float)
        np.testing.assert_allclose(G['point_triangle_distances']([[.5,2,0]],deg),[2])
    def test_08_seven_distance_samples_per_cube(self):
        for row in self.audit['cubes']:
            sd=row['surfaceDistance'];self.assertEqual(7,len(sd['samplePoints']))
            self.assertEqual(7,len(sd['body']));self.assertEqual(7,len(sd['magazine']))
            self.assertTrue(all(math.isfinite(v) and v>=0 for p in ('body','magazine') for v in sd[p]))
            self.assertEqual(sum(x<y for x,y in zip(sd['magazine'],sd['body'])),sd['magazineVotes'])
    def test_09_full_graph_fallback_metadata(self):
        item=json.loads(self.outputs[A/f'items/{KEY}.json']);node=item['model']
        self.assertEqual(self.item['model'],node['fallback']);self.assertEqual(self.item['model'],node['cases'][0]['model']['fallback'])
        item['model']=self.item['model'];self.assertEqual(self.item,item)
        self.assertEqual(list(G['FP']),node['cases'][0]['when']);self.assertEqual('minecraft:display_context',node['property'])
    def test_10_graph_21_samples_and_carrier_branches(self):
        item=json.loads(self.outputs[A/f'items/{KEY}.json']);rd=item['model']['cases'][0]['model']
        self.assertEqual(1,rd['index']);self.assertEqual(21,len(rd['entries']))
        refs=set()
        for i,e in enumerate(rd['entries']):
            self.assertEqual(i/20,e['threshold']);c=e['model'];self.assertEqual(0,c['index'])
            for branch,grip in [('on_false','native'),('on_true','twohand')]:
                self.assertEqual('minecraft:composite',c[branch]['type'])
                self.assertEqual(2,len(c[branch]['models']))
                for part,leaf in zip(('body','magazine'),c[branch]['models']):
                    key=f'destiny:{KEY}_{i:02d}_{part}_{grip}';self.assertEqual(key,leaf['model']);refs.add(key)
        self.assertEqual(84,len(refs))
    def test_11_float32_boundaries_offsets_and_negative_fallback(self):
        thresholds=[f32(i/20) for i in range(21)]
        select=lambda p:max((i for i,t in enumerate(thresholds) if t<=f32(p)),default=-1)
        for p in (-1,-.001):self.assertEqual(-1,select(p))
        for i in range(21):
            for offset in (0,.0001,.000999,.001):self.assertEqual(i,select(f32(f32(i/20)+offset)))
            if i>0:self.assertEqual(i-1,select(f32(thresholds[i]-.00001)))
        self.assertEqual(20,select(1.001))
    def test_12_exact_endpoints_every_hand_and_part(self):
        for grip in ('native','twohand'):
            base=read(G['BASE'] if grip=='native' else G['BASE'].parent/'blast_furnace_twohand.json')['display']
            for frame in (0,20):
                for part in G['PARTS']:self.assertEqual(base,self.pose(frame,part,grip)['display'])
    def test_13_finite_transforms_nonfp_unchanged(self):
        for i in range(21):
            for part in G['PARTS']:
                for grip in ('native','twohand'):
                    pose=self.pose(i,part,grip);self.assertEqual({'parent','display'},set(pose))
                    self.assertEqual(f'destiny:{KEY}_{part}',pose['parent'])
                    base=read(G['BASE'] if grip=='native' else G['BASE'].parent/'blast_furnace_twohand.json')['display']
                    for context,transform in pose['display'].items():
                        if context not in G['FP']:self.assertEqual(base[context],transform)
                        for field,vs in transform.items():
                            self.assertEqual(3,len(vs));self.assertTrue(all(math.isfinite(v) for v in vs))
                            if field=='translation':self.assertTrue(all(abs(v)<=80 for v in vs))
                            if field=='scale':self.assertTrue(all(0<v<=4 for v in vs))
    def test_14_both_hand_crossbow_carrier_matrix_inverse(self):
        for i in range(21):
            for part in G['PARTS']:
                n=self.pose(i,part)['display'];t=self.pose(i,part,'twohand')['display']
                for left,context in enumerate(G['FP']):
                    sign=-1 if left else 1;angle=math.radians(10)*sign
                    carrier=np.array([[math.cos(angle),0,math.sin(angle),-.641864*sign],[0,1,0,0],[-math.sin(angle),0,math.cos(angle),0],[0,0,0,1]])
                    np.testing.assert_allclose(matrix(n[context],left),carrier@matrix(t[context],left),atol=3e-6,rtol=0)
    def test_15_visible_body_and_local_magazine_departure(self):
        n=self.pose(8,'body')['display'];m=self.pose(8,'magazine')['display']
        self.assertGreater(n[G['FP'][0]]['rotation'][0],60)
        for context in G['FP']:
            self.assertEqual(n[context]['rotation'],m[context]['rotation']);self.assertEqual(n[context]['scale'],m[context]['scale'])
            local=np.linalg.solve(matrix(n[context])[:3,:3],(np.array(m[context]['translation'])-n[context]['translation']))
            np.testing.assert_allclose(local,[.2,-5.8,.35],atol=2e-6)
        self.assertEqual(self.pose(15,'body')['display'],self.pose(15,'magazine')['display'])
        for bad in (-.01,1.01,float('nan'),float('inf')):
            with self.assertRaises(ValueError):G['sample'](bad)
    def test_16_gameplay_provenance_hashes_actual_range(self):
        p=read(ART/'gameplay-provenance.json');self.assertEqual(16,len(p['frames']))
        self.assertEqual(38.7,p['frames'][0]['seekSeconds']);self.assertEqual(40.95,p['frames'][-1]['seekSeconds'])
        self.assertEqual(75,p['clip']['endSeconds']);self.assertLess(p['clip']['bytes'],70*1024*1024)
        for f in p['frames']:
            path=ROOT/f['path'];self.assertEqual(f['sha256'],G['sha'](path.read_bytes()))
            with Image.open(path) as im:self.assertEqual((1280,720),im.size)
        notes=(ART/'reference-notes.md').read_text();self.assertIn('BRAVE',notes);self.assertIn('41 seconds',notes)
        for p in (ART/'gameplay-contact.png',ART/'partition-contact.png',ART/'preview-contact.png'):
            with Image.open(p) as im:im.verify()
    def test_17_inspection_preserves_original_bb_cubes_uv_textures(self):
        src=read(G['BB']);bb=json.loads(self.outputs[ART/'inspection.bbmodel'])
        for field in ('elements','textures','resolution'):self.assertEqual(src[field],bb[field])
        self.assertEqual(['body','magazine'],[g['name'] for g in bb['outliner']])
        children=[v for g in bb['outliner'] for v in g['children']]
        self.assertEqual(249,len(children));self.assertEqual({e['uuid'] for e in src['elements']},set(children))

class XmlResult(unittest.TextTestResult):
    def startTest(self,test):
        super().startTest(test);self.node=ET.SubElement(self.xml,'testcase',classname=type(test).__name__,name=test._testMethodName)
    def addFailure(self,test,err):
        super().addFailure(test,err);ET.SubElement(self.node,'failure').text=self._exc_info_to_string(err,test)
    def addError(self,test,err):
        super().addError(test,err);ET.SubElement(self.node,'error').text=self._exc_info_to_string(err,test)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.xml=ET.Element('testsuite',name='BlastFurnaceReloadW114Python')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--junit',type=Path);args=ap.parse_args()
    result=unittest.TextTestRunner(verbosity=2,resultclass=XmlResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(Reload))
    if args.junit:
        assert not args.junit.resolve().is_relative_to(ROOT),'JUnit XML must go to private temp, outside exact worktree ownership'
        result.xml.set('tests',str(result.testsRun));result.xml.set('failures',str(len(result.failures)));result.xml.set('errors',str(len(result.errors)))
        args.junit.parent.mkdir(parents=True,exist_ok=True);ET.ElementTree(result.xml).write(args.junit,encoding='utf-8',xml_declaration=True)
    sys.exit(not result.wasSuccessful())
