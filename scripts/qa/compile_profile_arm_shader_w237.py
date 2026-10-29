#!/usr/bin/env python3
"""Compile/link experimental entity shader families against exact 26.3 native includes.
This does not certify native Vulkan rendering or the completeness of the pipeline inventory.
"""
import argparse,itertools,json,re,subprocess,zipfile
from pathlib import Path

def run(pack,client,out,validator):
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(pack) as custom,zipfile.ZipFile(client) as native:
        def source(path):
            try:return custom.read(path).decode()
            except KeyError:return native.read(path).decode()
        def expand(s):
            return re.sub(r"#include <([^>]+)>",lambda m:expand(source("assets/"+m[1].replace(":","/shaders/include/"))),s)
        sources={ext:source("assets/minecraft/shaders/core/entity."+ext) for ext in ("vsh","fsh")}
        assert all("destinyArmInfo" in s for s in sources.values()),"Not a W237 opt-in probe pack"
        families=[{}, {"ALPHA_CUTOUT":"0.1"}, {"ALPHA_CUTOUT":"0.5"}, {"NO_CARDINAL_LIGHTING":"1"}, {"EMISSIVE":"1"}, {"PER_FACE_LIGHTING":"1"}, {"GLINT":"1","APPLY_TEXTURE_MATRIX":"1"}, {"DISSOLVE":"1"}]
        # RenderPipelines.OIT_SNIPPET and LevelRenderer static initializer in 26.3:
        # rank 2, coefficient count powExact(2,3), attachment count coefficients/4.
        common={"OIT":"1","OIT_WAVELET_RANK":"2","OIT_COEFF_COUNT":"8","OIT_COEFF_ATTACHMENT_COUNT":"2"}
        phases=[{},common|{"OIT_ACCUMULATE":"1"},common|{"OIT_ALPHA_ONLY":"1","OIT_DEPTH_BOUNDS":"1"},common|{"OIT_ALPHA_ONLY":"1","OIT_TRANSMITTANCE":"1"},common|{"OIT_ACCUMULATE":"1","OIT_ADDITIVE":"1"}]
        results=[]
        for n,(family,phase,no_overlay) in enumerate(itertools.product(families,phases,(False,True))):
            defines=family|phase|({"NO_OVERLAY":"1"} if no_overlay else {})
            for backend in ("opengl","vulkan"):
                files=[]
                for ext,stage in (("vsh","vert"),("fsh","frag")):
                    s=sources[ext].replace("#version 330","#version 450" if backend=="vulkan" else "#version 330",1)
                    i=s.index("\n",s.index("#extension"))
                    s=s[:i+1]+"".join("#define "+k+" "+v+"\n" for k,v in defines.items())+s[i+1:]
                    f=out/(str(n)+"-"+backend+"."+stage);f.write_text(expand(s));files.append(str(f.resolve()))
                cmd=[validator]+(["--target-env","vulkan1.2","--amb","--aml"] if backend=="vulkan" else [])+["-l",*files]
                result=subprocess.run(cmd,capture_output=True,text=True,cwd=out)
                results.append(dict(defines=defines,backend=backend,ok=result.returncode==0,output=result.stdout+result.stderr if result.returncode else ""))
        (out/"result.json").write_text(json.dumps(results,indent=2)+"\n")
        failures=[r for r in results if not r["ok"]]
        print(json.dumps(dict(programs=len(results),passed=len(results)-len(failures),failures=failures)))
        return 1 if failures else 0
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--pack",required=True,type=Path);p.add_argument("--client",required=True,type=Path);p.add_argument("--out",required=True,type=Path);p.add_argument("--validator",default="/opt/homebrew/bin/glslangValidator");a=p.parse_args()
    raise SystemExit(run(a.pack,a.client,a.out,a.validator))
