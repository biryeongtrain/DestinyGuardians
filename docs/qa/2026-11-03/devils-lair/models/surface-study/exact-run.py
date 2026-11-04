"""Reproduce the isolated Marauder raster experiment; product files stay untouched.
Run with Python containing NumPy and Pillow. Input cache retains original shader files.
"""
import argparse, runpy
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--cache', type=Path, required=True)
parser.add_argument('--native-cache', type=Path, required=True)
parser.add_argument('--no-fill',action='store_true')
args=parser.parse_args()
source=args.repo/'scripts/strikes/build_devils_models.py'
code=source.read_text()
start=code.index('def drive_native_candidate(name):')
a,b=code[:start],code[start:]
needle='  def samples(self):'
assert needle in b
b=b.replace(needle,'  def extract(self):\n   exact_extract(self,b,P,source_meta)\n'+needle,1)
if args.no_fill:
    b=b.replace('  def image(self,p):','  def merge_small(self):pass\n  def image(self,p):\n   return super().image(p)\n  def unused_image(self,p):',1)
    b=b.replace("self._silhouettes={(r['bone'],r['face']):set(zip(r['gi'].tolist(),r['gj'].tolist())) for r in self.recs};super().planes()","self.o['walls']=0;self.o['dilate']=False;super().planes()",1)
ns={'__name__':'isolated_exact_experiment','__file__':str(source),'exact_extract':runpy.run_path(str(Path(__file__).with_name('exact-extract.py')))['extract']}
exec(compile(a+b,str(source),'exec'),ns)
ns.update(REPO=args.repo,CACHE=args.cache,NATIVE_CACHE=args.native_cache)
ns['drive_native_candidate']('marauder')
