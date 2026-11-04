"""Isolated surface experiment: exact texel-centre triangle rasterization."""
import numpy as np
from PIL import Image

def extract(self, baker, cache, meta):
    T = self.to_px(self.V)
    rgba = np.asarray(Image.open(cache/'combined.png').convert('RGBA'))
    emit = np.asarray(Image.open(cache/'emit.png').convert('RGB'))
    h,w = rgba.shape[:2]
    pure = set(meta.get('pure_emission_materials', []))
    records=[]
    for bone in sorted(set(self.tri_bone)):
        ids=np.flatnonzero(self.tri_bone==bone)
        pitch,spacing=self.pitch_of(bone)
        for face in baker.FACES:
            da,near,(ua,va),us,vs=baker.FACE_DEF[face]
            bounds=T[ids][:,:,[ua,va]].reshape(-1,2)/pitch
            lo=np.floor(bounds.min(0)).astype(int);hi=np.floor(bounds.max(0)).astype(int)
            shape=hi-lo+1
            z=np.full(tuple(shape),np.inf);color=np.zeros((*shape,3),dtype=np.uint8)
            sign=1 if near=='min' else -1
            for ti in ids:
                tri=T[ti];q=tri[:,[ua,va]]/pitch
                e1=q[1]-q[0];e2=q[2]-q[0];det=e1[0]*e2[1]-e1[1]*e2[0]
                if abs(det)<1e-10:continue
                a=np.maximum(lo,np.ceil(q.min(0)-.5).astype(int));b=np.minimum(hi,np.floor(q.max(0)-.5).astype(int))
                if np.any(a>b):continue
                ii,jj=np.meshgrid(np.arange(a[0],b[0]+1),np.arange(a[1],b[1]+1),indexing='ij')
                dx=ii+.5-q[0,0];dy=jj+.5-q[0,1]
                u=(dx*e2[1]-dy*e2[0])/det;v=(e1[0]*dy-e1[1]*dx)/det
                valid=(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)
                if not valid.any():continue
                i=ii[valid]-lo[0];j=jj[valid]-lo[1];u=u[valid];v=v[valid]
                depth=(tri[0,da]+u*(tri[1,da]-tri[0,da])+v*(tri[2,da]-tri[0,da]))*sign
                front=depth<z[i,j]
                if not front.any():continue
                i=i[front];j=j[front];u=u[front];v=v[front];depth=depth[front]
                tex=self.UV[ti];uv=tex[0]+u[:,None]*(tex[1]-tex[0])+v[:,None]*(tex[2]-tex[0])
                x=(np.mod(uv[:,0],1)*w).astype(int)%w;y=((1-np.mod(uv[:,1],1))*h).astype(int)%h
                em=emit[y,x];glow=em.max(1)>16
                keep=glow if self.mats[self.MAT[ti]] in pure else (rgba[y,x,3]>=128)|glow
                i=i[keep];j=j[keep];z[i,j]=depth[keep]
                color[i,j]=np.maximum(rgba[y,x,:3],np.where(glow[:,None],em,0))[keep]
            i,j=np.nonzero(np.isfinite(z))
            if not len(i):continue
            records.append(dict(bone=bone,face=face,pitch=pitch,spacing=spacing,gi=i+lo[0],gj=j+lo[1],L=np.round(sign*z[i,j]/spacing).astype(np.int64),rgb=color[i,j],win=np.zeros(len(i),dtype=np.int64)))
    self.recs=records
    self.stats['surface_sampling']='exact triangle intersection at texel centres; source RGBA/emission'
