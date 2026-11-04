"""Create an offline Dreg-Light candidate from the audited skiff shader bake.

Preserves the full source rig and its hover origin. No runtime registration or animation claims.
python project_skiff_drive.py BAKE_DIR OUTPUT_DIR
"""
import hashlib
import argparse
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('cache',type=Path)
parser.add_argument('output',type=Path)
parser.add_argument('--atlas',type=int,choices=(2048,4096),default=2048)
parser.add_argument('--max-quads',type=int,default=6000)
parser.add_argument('--translucent-fx',action='store_true',help='Experimental separate straight-alpha source emission atlas')
parser.add_argument('--rasterized',action='store_true',help='Experimental exact source triangle intersections at texel centers')
parser.add_argument('--preserve-subtexel',action='store_true',help='Keep source-sampled cells missed by center rays; requires --rasterized')
parser.add_argument('--density',type=float,default=.18,help='Initial atlas fitting density')
args=parser.parse_args()
if args.max_quads<1:parser.error('--max-quads must be positive')
if not np.isfinite(args.density) or not 0<args.density<=1:parser.error('--density must be in (0, 1]')
if args.preserve_subtexel and not args.rasterized:parser.error('--preserve-subtexel requires --rasterized')
cache=args.cache.resolve();output=args.output;output.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('dreglight',repo/'scripts/campaign/bake_dreglight.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
metadata=json.loads((cache/'shader-bake.json').read_text())
coverage_file=cache/metadata['coverage_file']
if hashlib.sha256(coverage_file.read_bytes()).hexdigest()!=metadata['coverage_sha256']:
    raise ValueError('Skiff shader coverage hash mismatch')
coverage=np.load(coverage_file)['coverage']
rgb=np.asarray(Image.open(cache/'combined.png').convert('RGB'))
emission=np.asarray(Image.open(cache/'emit.png').convert('RGB'))
if coverage.shape!=rgb.shape[:2] or emission.shape!=rgb.shape or not np.isfinite(coverage).all():
    raise ValueError('Incompatible skiff shader atlases')
d=dict(np.load(cache/'shader_mesh.npz'))
d['mat_tex']=np.array([str(cache/'combined.png')]*len(d['mats']))
key='dl_skiff_candidate'
np.savez_compressed('/tmp/r7_dump_'+key+'.npz',**d)
safe=lambda name:str(name).lower().replace(' ','_').replace('.','_')
names=list(map(str,d['names']))
if len(set(map(safe,names)))!=len(names):raise ValueError('Skiff bone-name collision')
b.SPECS[key]=dict(kind='native',src=metadata['source_blend'],bones={safe(n):n for n in names},
                 parents={safe(n):safe(p) if str(p) else None for n,p in zip(names,d['parents'])},
                 root=safe(names[0]),roles={},k=16.,y0=0.,fine=(),glow_fine=False,
                 density=args.density,spacing_scale=1.,walls=3,max_quads=args.max_quads,split=True)
emission_materials=set(metadata['emission_materials'])
pure_emission=set(metadata['pure_emission_materials'])


class SkiffBake(b.Bake):
    def _bones(self):
        super()._bones()
        for index,material in enumerate(self.mats):
            if material not in emission_materials:continue
            mask=self.MAT==index
            for parent in set(self.tri_bone[mask]):
                child=parent+'_glow'
                selected=mask&(self.tri_bone==parent)
                self.tri_bone[selected]=child;self.parent[child]=parent;self.origin[child]=self.origin[parent]

    def samples(self):
        super().samples()
        tri=self.S['tri'];t=self.to_px(self.V)[tri];q=self.S['P']-t[:,0]
        v0=t[:,1]-t[:,0];v1=t[:,2]-t[:,0]
        a=np.einsum('ij,ij->i',v0,v0);ab=np.einsum('ij,ij->i',v0,v1);c=np.einsum('ij,ij->i',v1,v1)
        vq=np.einsum('ij,ij->i',q,v0);wq=np.einsum('ij,ij->i',q,v1);den=a*c-ab*ab
        u=np.divide(c*vq-ab*wq,den,out=np.zeros_like(den),where=abs(den)>1e-12)
        v=np.divide(a*wq-ab*vq,den,out=np.zeros_like(den),where=abs(den)>1e-12)
        uv=self.UV[tri,0]+u[:,None]*(self.UV[tri,1]-self.UV[tri,0])+v[:,None]*(self.UV[tri,2]-self.UV[tri,0])
        h,w=coverage.shape;xx=(np.mod(uv[:,0],1)*w).astype(int)%w;yy=((1-np.mod(uv[:,1],1))*h).astype(int)%h
        emit=emission[yy,xx];emitting=emit.max(1)>16
        pure=np.array([self.mats[mi] in pure_emission for mi in self.MAT[tri]])
        keep=np.where(pure,emitting,(coverage[yy,xx]>=.5)|emitting)
        self.S['rgb'][emitting]=np.maximum(self.S['rgb'][emitting],emit[emitting])
        if args.translucent_fx:
            # Pure additive cards must not carry the dark combined-radiance background.
            self.S['rgb'][pure]=emit[pure]
        self.stats.update(coverage_source='independent shader coverage',transparent_source_samples_removed=int((~keep).sum()),
                          source_emission_samples=int(emitting.sum()))
        self.S={k:value[keep] for k,value in self.S.items()};self.stats['samples']=int(keep.sum())

    def recolour(self):
        for record in self.recs:record['col']=record['rgb'].copy()

    def extract(self):
        if not args.rasterized:
            return super().extract()
        from slice_raster import raster_face,uncovered_cells
        fallback={}
        if args.preserve_subtexel:
            super().extract()
            fallback={(r['bone'],r['face']):r for r in self.recs}
        retained=0
        triangles=self.to_px(self.V)
        records=[]
        for bone in sorted(set(self.tri_bone)):
            selected=np.nonzero(self.tri_bone==bone)[0]
            pitch,spacing=self.pitch_of(bone)
            def sample(index,uv):
                h,w=coverage.shape
                xx=(np.mod(uv[:,0],1)*w).astype(int)%w
                yy=((1-np.mod(uv[:,1],1))*h).astype(int)%h
                emit=emission[yy,xx];emitting=emit.max(1)>16
                pure=self.mats[self.MAT[selected[index]]] in pure_emission
                keep=emitting if pure else (coverage[yy,xx]>=.5)|emitting
                color=rgb[yy,xx].copy()
                color[emitting]=np.maximum(color[emitting],emit[emitting])
                if pure and args.translucent_fx:color=emit
                return color,keep
            for face in b.FACES:
                r=raster_face(triangles[selected],self.UV[selected],pitch,b.FACE_DEF[face],sample)
                previous=fallback.get((bone,face))
                if r is None:
                    if previous is not None:
                        records.append(previous);retained+=len(previous['L'])
                    continue
                record=dict(bone=bone,face=face,pitch=pitch,spacing=spacing,gi=r['gi'],gj=r['gj'],
                            L=np.round(r['depth']/spacing).astype(np.int64),rgb=r['rgb'])
                if previous is not None:
                    missing=uncovered_cells(previous['gi'],previous['gj'],r['gi'],r['gj'])
                    retained+=int(missing.sum())
                    for field in ('gi','gj','L','rgb'):
                        record[field]=np.concatenate([record[field],previous[field][missing]])
                records.append(record)
        self.recs=records
        self.stats['surface_sampling']='exact orthographic triangle intersection at texel centers'
        self.stats['subtexel_source_cells_retained']=retained

    def build(self):
        """Keep the best *packed* surface while narrowing the failed density interval.

        The generic mob fitter jumps back to its first coarse fit after one overshoot.
        A large hollow craft needs a bounded search instead; no spacing/budget relaxation.
        """
        import time
        started=time.monotonic()
        if not args.rasterized or args.preserve_subtexel:self.samples()
        low,high=0.,self.o['density']
        density=high;best=None;attempts=[]
        for attempt in range(10):
            self.o['density']=density
            self.extract();self.merge_small();self.recolour();self.planes()
            area=sum((p['img'].shape[0]+1)*(p['img'].shape[1]+1) for p in self.plist)
            fraction=area/self.o['atlas']**2
            fits=(len(self.plist)<=self.spec['max_quads'] and fraction<.97
                  and all(max(p['img'].shape[:2])<=self.o['atlas'] for p in self.plist)
                  and self.pack())
            attempts.append(dict(density=density,quads=len(self.plist),area_fraction=fraction,fits=bool(fits)))
            print('SKIFF_FIT',attempts[-1],'seconds',round(time.monotonic()-started,1),flush=True)
            if fits:
                low=density;self.stats['rect_area_frac']=fraction
                best=(self.plist,dict(self.stats),density)
                if density==high:break
            else:high=density
            if best and high-low<max(.001,low*.04):break
            density=(low+high)/2
        if best is None:raise RuntimeError('No skiff projection fits the requested atlas and quad budget')
        self.plist,self.stats,self.o['density']=best
        if not self.pack():raise RuntimeError('Previously packed skiff candidate no longer fits')
        self.stats.update(density=self.o['density'],spacing_scale=self.o['spacing_scale'],fit_attempts=attempts)
        return self

    def authored_animations(self,groups):return []


x=SkiffBake(key,opts={'atlas':args.atlas}).build()
x.stats.update(atlas_size=args.atlas,quad_budget=args.max_quads)
model=x.model(dict(sourceBlend=metadata['source_blend'],sourceSha256=metadata['source_sha256'],
                   technique='Dreg-Light with separate shader coverage/emission',status='offline static candidate',
                   scale='16 pixels per normalized source unit; hover origin preserved',
                   limits=['No runtime animation or flight route yet','Baked PBR under authored neutral lighting',
                           'Binary cutout at coverage 0.5 and emission threshold 16','Native visual/performance acceptance pending']))
model['devils_lair']=model.pop('w300')
if args.rasterized:
    model['devils_lair']['surfaceSampling']=dict(
        method='exact texel-center triangle intersections before depth quantization',
        preserveSubtexel=args.preserve_subtexel,
        retainedSourceCells=x.stats['subtexel_source_cells_retained'])
if args.translucent_fx:
    from skiff_fx import split_fx
    model,fx_report=split_fx(model)
    model['devils_lair']['effects']=fx_report
    model['devils_lair']['limits']=[
        'No runtime animation or flight route yet','Baked PBR under authored neutral lighting',
        'Hull coverage cutout 0.5; source emission support threshold 16 remains',
        'Straight alpha approximates additive radiance but attenuates backgrounds',
        'BetterModel texture export and native visual/performance acceptance pending']
    x.stats['effects']=fx_report
path=output/(key+'.bbmodel');path.write_text(json.dumps(model,separators=(',',':')))
Image.fromarray(x.atlas).save(output/'atlas.png')
(output/'stats.json').write_text(json.dumps(x.stats,indent=2)+'\n')
print('SKIFF_CANDIDATE',len(model['elements']),'quads',x.stats['mean_luma'],'mean luma',flush=True)
