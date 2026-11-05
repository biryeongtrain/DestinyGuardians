"""W325 (worker m1) shared detail helpers, copied verbatim into each weapon folder (art/weapons/w325/<id>/detail.py).

chamfer(...)  : a z-running box with 45-degree chamfered long edges (core + narrowed strip + one 45-degree rotated
                square slab per chamfered edge; the slab's outer face is the bevel, the rest is buried).
Cleaner       : special() helper that paints a face flat (median of its own clean projection samples) when the rip
                projection behind it is mostly occluded/missing (coverage below a threshold) or when the face is listed
                explicitly; the kit then adds its 1px edge highlight/shadow.  Deterministic.
"""
import json, math, statistics
from pathlib import Path
import kit


def box(name, lo, hi, **kw):
    e = {'name': name, 'from': [round(v, 5) for v in lo], 'to': [round(v, 5) for v in hi]}; e.update(kw); return e


def rot(e, axis, ang, origin):
    e['rotation'] = {'origin': [round(v, 5) for v in origin], 'x': 0, 'y': 0, 'z': 0}; e['rotation'][axis] = round(ang, 4)
    return e


def chamfer(name, lo, hi, c, edges=('tl', 'tr')):
    """Box lo..hi running along z; chamfer size c on the listed long edges (tl/tr = top left/right, bl/br bottom)."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    c = min(c, (x1 - x0) / 2.01, (y1 - y0) / 2.01)
    top = [k for k in edges if k[0] == 't']; bot = [k for k in edges if k[0] == 'b']
    cy0 = y0 + (c if bot else 0); cy1 = y1 - (c if top else 0)
    out = [box(name, (x0, cy0, z0), (x1, cy1, z1))]
    if top:
        out.append(box(name + '_crown', (x0 + (c if 'tl' in edges else 0), cy1, z0), (x1 - (c if 'tr' in edges else 0), y1, z1)))
    if bot:
        out.append(box(name + '_keel', (x0 + (c if 'bl' in edges else 0), y0, z0), (x1 - (c if 'br' in edges else 0), cy0, z1)))
    h = c / math.sqrt(2)
    for k in edges:
        cx = x0 + c if k[1] == 'l' else x1 - c
        cy = y1 - c if k[0] == 't' else y0 + c
        out.append(rot(box(f'{name}_bevel_{k}', (cx - h, cy - h, z0), (cx + h, cy + h, z1)), 'z', 45, (cx, cy, (z0 + z1) / 2)))
    return out


class Cleaner:
    def __init__(self, design, cache_dir, threshold=0.6, flat=(), skip=()):
        self.D = design; cache = Path(cache_dir); man = json.loads((cache / 'manifest.json').read_text())
        self.views = {k: kit.View(cache, k, man) for k in man['views']}
        ext = max(man['hi'][i] - man['lo'][i] for i in range(3))
        self.occ = getattr(design, 'OCC_TOL', ext * 0.012)
        self.grade = getattr(design, 'grade', kit.default_grade)
        self.th = threshold; self.flat = flat; self.skip = skip; self.cache = {}; self.log = {}

    def listed(self, pats, n, fn):
        for p in pats:
            pn, _, pf = p.partition(':')
            if (n == pn or (pn.endswith('*') and n.startswith(pn[:-1]))) and (not pf or fn in pf.split('|')): return True
        return False

    def colour(self, e, fn):
        key = (e['name'], fn)
        if key in self.cache: return self.cache[key]
        n = e['name']; res = None
        if not self.listed(self.skip, n, fn):
            nm = kit.rotate_vec(kit.NORMALS[fn], kit.rot_of(e)); pc = kit.face_point(e, fn, .5, .5)
            a = self.D.model2world(n, pc); b = self.D.model2world(n, tuple(pc[i] + nm[i] * .25 for i in range(3)))
            wn = [b[i] - a[i] for i in range(3)]; i = max(range(3), key=lambda k: abs(wn[k]))
            v = self.views[('p' if wn[i] > 0 else 'n') + 'xyz'[i]]
            cols = []; N = 8
            for si in range(N):
                for ti in range(N):
                    w = self.D.model2world(n, kit.face_point(e, fn, (si + .5) / N, (ti + .5) / N))
                    x, y = v.project(w); d = v.depth_at(x, y)
                    if d is None or d > sum(w[k] * v.d[k] for k in range(3)) + self.occ: continue
                    c = v.sample(x, y)
                    if c: cols.append(self.grade(c))
            cov = len(cols) / (N * N)
            if cols and (cov < self.th or self.listed(self.flat, n, fn)):
                res = tuple(int(statistics.median(c[k] for c in cols)) for k in range(3)) + (255,)
            self.log[key] = round(cov, 2)
        self.cache[key] = res
        return res

    def __call__(self, e, fn, s, t):
        return self.colour(e, fn)


class Flat:
    """W30-style flat colour blocks (style update 2026-11-05): every face of an element gets one colour = the median
    of the rip projection over all of that element's faces (so a part reads as one material), unless MAT gives an exact
    colour for the element name (first matching prefix).  camo(e, fn, s, t) optional blob painter.  The kit's pixel
    style then quantises to the weapon palette and draws the 1-texel bevel lines."""

    def __init__(self, design, cache_dir, mat=(), keep=()):
        self.c = Cleaner(design, cache_dir, threshold=2.0)
        self.mat = mat; self.keep = keep; self.el = {}

    def element_colour(self, e):
        n = e['name']
        if n in self.el: return self.el[n]
        res = None
        for pre, col in self.mat:
            if n.startswith(pre) or self.c.listed((pre,), n, ''):
                res = tuple(col)[:3] + (255,); break
        if res is None:
            cols = []
            for fn in kit.FACE_AXES:
                c = self.c.colour(e, fn)
                if c: cols.append(c)
            res = tuple(int(statistics.median(c[k] for c in cols)) for k in range(3)) + (255,) if cols else None
        self.el[n] = res
        return res

    def __call__(self, e, fn, s, t):
        if self.c.listed(self.keep, e['name'], fn): return None      # projected decal faces
        col = self.element_colour(e)
        cuts = SEAMS.get(seam_base(e['name']))
        if col and cuts and fn not in ('north', 'south'):
            z = kit.face_point(e, fn, s, t)[2]
            if any(abs(z - c) < 0.034 for c in cuts): return kit.lighten(col, -.42) + (255,)
        return col


def blob(p, scale=1.4, seed=0):
    """deterministic smooth value noise in model px -> 0..1 (for 2-3 colour camo blobs)"""
    def h(i, j, k):
        v = math.sin(i * 127.1 + j * 311.7 + k * 74.7 + seed * 19.3) * 43758.5453
        return v - math.floor(v)
    x, y, z = (c / scale for c in p); xi, yi, zi = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - xi, y - yi, z - zi
    sm = lambda f: f * f * (3 - 2 * f); fx, fy, fz = sm(fx), sm(fy), sm(fz)
    acc = 0.0
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                w = (fx if a else 1 - fx) * (fy if b else 1 - fy) * (fz if c else 1 - fz)
                acc += w * h(xi + a, yi + b, zi + c)
    return acc


SEAMS = {}


def chamfer_seg(name, lo, hi, c, edges=('tl', 'tr'), cuts=(), inset=0.05):
    """Long chamfered slab that reads as machined segments (Dead Man Walking) WITHOUT misaligned pieces (Chattering
    Bone negative reference): one continuous chamfered section; the segment seams are recessed 1-texel grooves
    engraved at the cut z values by Flat (dark line on every face of the slab)."""
    SEAMS[name] = tuple(cuts)
    return chamfer(name, lo, hi, c, edges)


def seam_base(n):
    for suf in ('_bevel_', '_crown', '_keel'):
        if suf in n: n = n.split(suf)[0]
    return n


def engrave(p, lines, hw=0.033):
    """lines: (axis 0/1/2, value, lo, hi on another axis or None) -> True where p lies on an engraved 1-texel line"""
    for ln in lines:
        ax, v = ln[0], ln[1]
        if abs(p[ax] - v) <= hw:
            if len(ln) < 5 or ln[3] <= p[ln[2]] <= ln[4]: return True
    return False

# W325 identity pass: clean per-face paint; exact painted texels survive kit quantisation.
def ink(col, amount):
    return tuple(max(0,min(255,int(c+amount))) for c in col[:3])+(255,)

def face_pixels(e, fn, s, t, density):
    _, u, v = kit.face_frame(e, fn)
    w=max(1,round(math.sqrt(sum(a*a for a in u))*density)); h=max(1,round(math.sqrt(sum(a*a for a in v))*density))
    return min(w-1,int(s*w)),min(h-1,int(t*h)),w,h

def finish(e, fn, s, t, colour, density):
    # Authored single-texel upper bevel and dark lower seam, including front/rear/end faces.
    i,j,w,h=face_pixels(e,fn,s,t,density)
    if e['name'].startswith('reticle') or 'bore' in e['name']: return colour
    if w>3 and h>3:
        if j==0: return ink(colour,25)
        if j==h-1: return ink(colour,-25)
        if i==0: return ink(colour,12)
        if i==w-1: return ink(colour,-14)
    return tuple(colour[:3])+(255,)

def line2(z,y,pts,width=.035):
    for (a,b),(c,d) in zip(pts,pts[1:]):
        dz,dy=c-a,d-b; den=dz*dz+dy*dy
        q=max(0,min(1,((z-a)*dz+(y-b)*dy)/den)) if den else 0
        if (z-a-q*dz)**2+(y-b-q*dy)**2 < width*width: return True
    return False

def rim(z,y,z0,y0,z1,y1,width=.04):
    return line2(z,y,[(z0,y0),(z1,y0),(z1,y1),(z0,y1),(z0,y0)],width)

def fastener(z,y,centres,light=(176,180,176,255),dark=(26,28,28,255),r=.11):
    for a,b in centres:
        d=max(abs(z-a),abs(y-b))
        if d<r:
            if abs(y-b)<.024 and abs(z-a)<r*.58: return dark
            return dark if d>r*.72 else light
    return None

def stipple(e,fn,s,t,density,base):
    i,j,w,h=face_pixels(e,fn,s,t,density)
    # recessed diamond/checker grip; clean 2-tone material, no projection grime
    return ink(base,-14) if (i+j)%5==0 and i>2 and j>2 and i<w-3 and j<h-3 else base


def resolve_coplanar(E):
    """Deterministic micro-relief on coincident same-facing facets only.
    Inherited chamfer end caps and frame joints share partial planes. Recess the losing
    face by 0.0001*(element index+1) model px (<0.015 px, <0.3 texel at T20).
    This removes z-fighting without shifting parts, changing angles, or adding slabs.
    Opposing joined faces and every non-overlapping boundary remain untouched.
    """
    dot=lambda a,b:sum(x*y for x,y in zip(a,b))
    sub=lambda a,b:tuple(x-y for x,y in zip(a,b))
    cr=lambda a,b:a[0]*b[1]-a[1]*b[0]
    def overlap(p,q):
        if sum(cr(q[i],q[(i+1)%4]) for i in range(4))<0:q=q[::-1]
        for a,b in zip(q,q[1:]+q[:1]):
            out=[]
            for c,d in zip(p,p[1:]+p[:1]):
                dc=cr(sub(b,a),sub(c,a));dd=cr(sub(b,a),sub(d,a))
                if dc>=-1e-8:out.append(c)
                if (dc>=0)!=(dd>=0):
                    k=dc/(dc-dd);out.append(tuple(c[j]+k*(d[j]-c[j]) for j in range(2)))
            p=out
            if len(p)<3:return False
        return abs(sum(cr(p[i],p[(i+1)%len(p)]) for i in range(len(p))))>.00002
    F=[]
    for i,e in enumerate(E):
        for fn in kit.FACE_AXES:
            p=[kit.face_point(e,fn,s,t) for s,t in ((0,0),(1,0),(1,1),(0,1))]
            n=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e))
            F.append((i,fn,p,n,dot(p[0],n)))
    recess=set()
    for k,(i,fn,p,n,d) in enumerate(F):
        u=sub(p[1],p[0]);v=sub(p[3],p[0]);ul=math.sqrt(dot(u,u));vl=math.sqrt(dot(v,v))
        u=tuple(a/ul for a in u);v=tuple(a/vl for a in v)
        project=lambda q:(dot(sub(q,p[0]),u),dot(sub(q,p[0]),v))
        pp=[project(a) for a in p]
        for j,gn,q,m,f in F[k+1:]:
            if i==j or dot(n,m)<.999999 or abs(d-f)>.00004:continue
            if overlap(pp,[project(a) for a in q]):recess.add((i,fn))
    for i,fn in recess:
        ax,side,*_=kit.FACE_AXES[fn];key='to' if side else 'from'
        E[i][key][ax]=round(E[i][key][ax]+(-1 if side else 1)*.0001*(i+1),5)
    return E
