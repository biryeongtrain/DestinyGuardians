"""World-plane overlap check: includes rotated parts with distinct pivots."""
import math
import kit

def area(poly): return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2 if poly else 0

def intersect(a,b):
    winding=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(b,b[1:]+b[:1])); sign=1 if winding>0 else -1
    out=a
    for p,q in zip(b,b[1:]+b[:1]):
        before=out; out=[]
        if not before: break
        def val(v): return sign*((q[0]-p[0])*(v[1]-p[1])-(q[1]-p[1])*(v[0]-p[0]))
        for u,v in zip(before,before[1:]+before[:1]):
            du,dv=val(u),val(v); iu,iv=du>=-1e-9,dv>=-1e-9
            if iu: out.append(u)
            if iu!=iv:
                t=du/(du-dv); out.append((u[0]+t*(v[0]-u[0]),u[1]+t*(v[1]-u[1])))
    return out

def overlaps(els):
    groups={}
    for i,e in enumerate(els):
        for fn in kit.NORMALS:
            normal=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e))
            pts=[kit.face_point(e,fn,s,t) for s,t in [(0,0),(1,0),(1,1),(0,1)]]
            d=sum(normal[k]*pts[0][k] for k in range(3)); key=tuple(round(v,5) for v in normal)+(round(d,5),)
            omit=max(range(3),key=lambda k:abs(normal[k])); axes=[k for k in range(3) if k!=omit]
            poly=[tuple(p[k] for k in axes) for p in pts]
            groups.setdefault(key,[]).append((i,fn,poly))
    hits=[]
    for group in groups.values():
        for x,a in enumerate(group):
            for b in group[x+1:]:
                if a[0]==b[0]: continue
                overlap=area(intersect(a[2],b[2]))
                if overlap>0.0002: hits.append((a,b,overlap))
    return hits

def clean(els):
    els=[e for e in els if all(e["to"][k]-e["from"][k]>1e-6 for k in range(3))]
    for attempt in range(12):
        hits=overlaps(els)
        if not hits: return els
        changed=set()
        for a,b,_ in hits:
            q=a if area(a[2])<=area(b[2]) else b
            i,fn,_=q
            if (i,fn) in changed: continue
            axis,side,*_=kit.FACE_AXES[fn]; e=els[i]
            if e['to'][axis]-e['from'][axis]<.035: continue
            edge='to' if side else 'from'
            e[edge]=list(e[edge]); e[edge][axis]+= -.009 if side else .009
            changed.add((i,fn))
        if not changed: break
    if overlaps(els): raise ValueError('unresolved same-facing world-plane overlap')
    return els
