#!/usr/bin/env python3
"""Read local exact26.3 JAR via ZIP+javap, never run Minecraft or build.

Writes research/ only. Override --jar for another cached26.3 client JAR.
All shell invocations should start rtk, e.g. rtk proxy python3 <this file>.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CLASSES=(
    'net.minecraft.client.renderer.RenderPipelines',
    'net.minecraft.client.renderer.item.CuboidItemModelWrapper$Unbaked',
    'net.minecraft.client.resources.model.sprite.Material',
    'net.minecraft.client.resources.model.sprite.TextureSlots',
    'net.minecraft.client.resources.model.cuboid.FaceBakery',
    'net.minecraft.client.resources.model.geometry.BakedQuad$MaterialInfo',
    'net.minecraft.client.resources.model.geometry.ItemQuads',
    'net.minecraft.client.color.item.Constant',
    'net.minecraft.client.color.item.CustomModelDataSource',
)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jar',type=Path,default=Path.home()/'.gradle/caches/fabric-loom/26.3/minecraft-client.jar')
    a=p.parse_args()
    outputs={}
    with zipfile.ZipFile(a.jar) as jar:
        version=json.loads(jar.read('version.json'))
        assert version['id']=='26.3',version['id']
        for name in ('item','text'):
            outputs[f'vanilla-{name}.fsh.txt']=jar.read(f'assets/minecraft/shaders/core/{name}.fsh')
    pipeline=None
    for cls in CLASSES:
        text=subprocess.check_output(['rtk','proxy','javap','-p','-c','-classpath',str(a.jar),cls],text=True)
        if cls.endswith('RenderPipelines'):
            pipeline=text
            lines=text.splitlines()
            ranges=[]
            for i,line in enumerate(lines):
                if any(s in line for s in ('String pipeline/item_cutout','String pipeline/item_translucent')):
                    ranges.append((max(0,i-4),min(len(lines),i+18)))
                if 'putstatic' in line and any(s in line for s in ('Field ITEM_SNIPPET:', 'Field OIT_ITEM_SNIPPET:')):
                    ranges.append((max(0,i-33),i+1))
            indices=sorted({i for l,h in ranges for i in range(l,h)})
            text='Exact26.3 javap excerpts; original bytecode offsets preserved.\n'+'\n'.join(lines[i] for i in indices)+'\n'
        outputs['javap-'+cls.rsplit('.',1)[1]+'.txt']=text.encode()
    assert 'float 0.1f' in pipeline
    sourcefiles=(
        'libs/minigame-lib/src/main/resources/assets/minecraft/shaders/core/item.vsh',
        'libs/minigame-lib/src/main/resources/assets/minecraft/shaders/core/text.vsh',
        'libs/minigame-lib/src/main/resources/shaders/text.fsh',
        'libs/minigame-lib/src/main/java/kim/biryeong/minigamelib/shaderfx/api/ShaderEffects.java',
        'libs/minigame-lib/src/main/java/kim/biryeong/minigamelib/shaderfx/impl/RPHandler.java',
    )
    snippets=[]
    for source in sourcefiles:
        lines=(ROOT/source).read_text().splitlines()
        hits=set()
        for i,line in enumerate(lines):
            if any(s in line for s in ('displayhud_is_hud','vertexColor = Color','effectId != 0',
                'color.a < 0.1','VIGNETTE =','//%CASES%','text.fsh','register(')):
                hits.update(range(max(0,i-2),min(len(lines),i+4)))
        snippets.append(source+'\n'+'\n'.join(f'{i+1}: {lines[i]}' for i in sorted(hits)))
    outputs['library-paths.txt']=('\n\n'.join(snippets)+'\n').encode()
    manifest=dict(jar=str(a.jar),jarSha256=hashlib.sha256(a.jar.read_bytes()).hexdigest(),
        minecraftVersion=version,method='ZIP reads and rtk proxy javap -p -c only; no client VM/build/native input',
        libraryInputHashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sourcefiles},
        outputSha256={s:hashlib.sha256(v).hexdigest() for s,v in outputs.items()},
        nativeVerified=False,childDelegation='No subagent API exposed; app project listing did not include this repo. Lead collected evidence.')
    outputs['evidence-manifest.json']=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    for name,raw in outputs.items():
        (HERE/name).write_bytes(raw)
    print(json.dumps(dict(files=len(outputs),minecraftVersion=version['id'],nativeVerified=False)))


if __name__=='__main__':main()
