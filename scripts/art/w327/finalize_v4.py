"""Install only explicitly named V4 hand cannons into this checkout's owned resources."""
import json,sys,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def native(p):return [8-35*p[0],7.6+35*p[2],8+35*p[1]]
def build(w):
 assert w in ['eyasluna','igneous_hammer','nation_of_beasts']
 art=ROOT/'art/weapons/w327'/w;v4=art/'v4';source=json.loads((art/'source-evaluation.json').read_text());camera=json.loads((v4/'camera_contract.json').read_text())
 assert sha(Path(source['blend']))==source['sha256'],'Source blend changed'
 skin=json.loads((v4/'native_skin.json').read_text());count=sum(map(len,skin['parts'].values()));assert count<=1000
 paths=[ROOT/'src/main/resources/destiny/weapon_skins'/f'{w}.json',ROOT/'src/main/resources/assets/destiny/textures/item/weapon/w327'/f'{w}.png',ROOT/'src/main/resources/assets/destiny/textures/item/hud/w327'/f'ammo_{w}.png']
 shutil.copy2(v4/'native_skin.json',paths[0]);shutil.copy2(v4/'native_atlas.png',paths[1])
 # Side silhouette is rasterized from authored polygon geometry, never alpha rectangle bounds.
 objects=json.loads((v4/'authored_geometry.json').read_text());points=[p for o in objects for p in o['vertices']]
 ymin=min(p[1] for p in points);ymax=max(p[1] for p in points);zmin=min(p[2] for p in points);zmax=max(p[2] for p in points);s=min(152/(ymax-ymin),56/(zmax-zmin));cx=(ymin+ymax)/2;cz=(zmin+zmax)/2
 icon=Image.new('RGBA',(640,256));d=ImageDraw.Draw(icon)
 for o in objects:
  for face in o['faces']:d.polygon([((80+(o['vertices'][i][1]-cx)*s)*4,(32-(o['vertices'][i][2]-cz)*s)*4) for i in face],fill=(255,255,255,255))
 icon.resize((160,64),Image.Resampling.LANCZOS).save(paths[2])
 def landmark(px,py):return [0,camera['source_center'][1]+(px-700)*camera['orthographic_scale']/1400,camera['source_center'][2]+(450-py)*camera['orthographic_scale']/1400]
 grip=landmark(*{'eyasluna':(1155,560),'igneous_hammer':(1140,550),'nation_of_beasts':(1157,544)}[w]);sight=landmark(*{'eyasluna':(964,202),'igneous_hammer':(954,193),'nation_of_beasts':(850,173)}[w])
 bones={b['name']:b for a in source['armatures'] for b in a['bones']}
 cylinder=bones['Cylinder']['head'] if 'Cylinder' in bones else landmark(905.5,302)
 anchors={'source_to_native_matrix':[[-35,0,0,8],[0,0,35,7.6],[0,35,0,8],[0,0,0,1]],'uniform_scale':35,'source_axis_forward':[0,-1,0],'native_axis_forward':[0,0,-1],
  'grip_contact':{'source':grip,'native':native(grip),'basis':'source-aligned visual palm center; approximate, source has no hand rig'},
  'sight_line':{'source_point':sight,'native_point':native(sight),'source_direction':[0,-1,0],'native_direction':[0,0,-1],'basis':'authored physical iron-sight clearance above source crest; presentation anchor, not source animation'},
  'moving_cylinder':{'source_pivot':cylinder,'native_pivot':native(cylinder),'native_axis':[0,0,-1],'basis':'source Cylinder bone head' if 'Cylinder' in bones else 'geometric chamber center; source has no cylinder bone'},
  'source_mechanism_bones':{k:{'source':bones[k]['head'],'native':native(bones[k]['head'])} for k in ['CraneRotate','CraneExtend','Magazine','Trigger'] if k in bones},
  'motion':'Existing donor timing/presentation is approximate reuse; source actions and hand rig are absent. Adjust runtime display, grip and ADS to these anchors, not exterior shape.'}
 (v4/'anchors.json').write_text(json.dumps(anchors,indent=2)+'\n')
 m=json.loads((art/'manifest.json').read_text());m.update(revision=4,element_total=count,elements={k:len(v) for k,v in skin['parts'].items()},atlas=[1024,1024],generator='scripts/art/w327/handcannons_v4.py + native_prepare_v4.py + native_export_v4.py + finalize_v4.py',native_acceptance='pending master native Minecraft QA',source_blend_sha256=source['sha256'],motion=anchors['motion'],material_finish='source-coordinate albedo on authored solids; source red paint/steel/rubber, Trials gold/metal/wrap, or ivory alloy by weapon; no dynamic PBR claim',outputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths})
 (art/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 (v4/'DELIVERY.md').write_text('V4 source-fidelity hand cannon. Actual source blend evaluated headlessly and preserved by SHA256. Native assembly uses standard 26.3 rotated cuboid faces and polygon alpha masks; no raw source mesh is shipped.\n\nSource-aligned neutral proof was reviewed before materials. Single uniform source transform is in anchors.json. Small coupled near-planar adjustments and counts are in native_preparation.json. Native rotation bases and reconstructed vertices are checked in native_validation.json.\n\nBlender 5.4 EEVEE DITHERED transparency produced diagonal depth artifacts where transparent rectangles overlap opaque neighboring faces. Analytic ray/UV checks and Cycles on the same JSON/atlas show continuous coverage. Diagnostic EEVEE/Cycles images are preserved separately. The representative material image uses Cycles; this is offline evidence, not native Minecraft acceptance.\n\nUser requested reduced review scope: final checks are JSON parse, element cap, atlas and source/output hashes. Master owns native grip, ADS, reload and pack QA. No extra model deformation to donor anchors.\n')
 print(w,count,{k:len(v) for k,v in skin['parts'].items()},flush=True)
if __name__=='__main__':
 for w in sys.argv[1:]:build(w)
