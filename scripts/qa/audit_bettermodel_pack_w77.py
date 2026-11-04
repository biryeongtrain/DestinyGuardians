#!/usr/bin/env python3
"""Read-only comparison of current BetterModel item dependencies after a fresh QA install.
Numeric model/texture identifiers are resolved before comparison. Not framebuffer evidence.
"""
import argparse,hashlib,json,zipfile
from functools import lru_cache
from pathlib import Path

def canonicalizer(archive):
 names=set(archive.namelist())
 @lru_cache(None)
 def model(name):return normalize(json.loads(archive.read(name)),0)
 def normalize(value,depth):
  if depth>24:raise ValueError("Dependency depth exceeds24")
  if isinstance(value,list):return [normalize(x,depth+1) for x in value]
  if not isinstance(value,dict):return value
  result={}
  for key,v in value.items():
   if key in ("model","parent") and isinstance(v,str) and ":" in v:
    ns,path=v.split(":",1);name=f"assets/{ns}/models/{path}.json"
    result[key]=model(name) if name in names else v
   elif key=="textures" and isinstance(v,dict):
    textures={}
    for k,texture in v.items():
     name=None
     if ":" in texture:
      ns,path=texture.split(":",1);name=f"assets/{ns}/textures/{path}.png"
     textures[k]={"pngSha256":hashlib.sha256(archive.read(name)).hexdigest()} if name in names else texture
    result[key]=textures
   else:result[key]=normalize(v,depth+1)
  return result
 return model

def audit(old,new):
 with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
  na,nb=set(a.namelist()),set(b.namelist());ca,cb=canonicalizer(a),canonicalizer(b)
  items=sorted(n for n in nb if n.startswith("assets/bettermodel/items/") and n.endswith(".json"))
  different=[n for n in items if n not in na or ca(n)!=cb(n)]
  outside=[n for n in na&nb if not n.startswith("assets/bettermodel/") and a.read(n)!=b.read(n)]
  assert not different,different
  assert not outside,outside
  return dict(currentBetterModelItems=len(items),semanticDifferences=different,changedCommonOutsideBetterModel=outside,
   method="Resolve model/parent JSON and texture PNG content; preserve other parsed JSON including transforms/tints",
   removedEntries=len(na-nb),addedEntries=len(nb-na),changedEntries=sum(a.read(n)!=b.read(n) for n in na&nb),
   oldBytes=Path(old).stat().st_size,newBytes=Path(new).stat().st_size,
   note="Fresh QA server omits old BetterModel examples and obsolete H13 definitions. Numeric dependency reassignment is not byte equality. This does not verify animations or pixels.")
if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--old",type=Path,required=True);p.add_argument("--new",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();d=audit(a.old,a.new);a.out.write_text(json.dumps(d,indent=2)+"\n");print(json.dumps(d))
