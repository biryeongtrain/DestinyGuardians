"""Geometry-preserving surface reduction for the six owned W327 group-2 models.
Authored solids, source mapping, materials and body/magazine boundaries remain intact.
"""
import math
import native_contours as nc

IDS = {'brigands_law','deliverance','forbearance','palmyra_b','apex_predator','cataclysmic'}
FACE_CORNERS = {'north':(0,1,2,3),'south':(4,5,6,7),'west':(0,2,4,6),'east':(1,3,5,7),'down':(0,1,4,5),'up':(2,3,6,7)}
FACE_NORMALS = {'north':(0,0,-1),'south':(0,0,1),'west':(-1,0,0),'east':(1,0,0),'down':(0,-1,0),'up':(0,1,0)}

def surfaces(contours):
    out=[]; saved=0
    for solid in contours:
        old=nc.surfaces([solid])
        if 'mesh_faces' in solid:
            out.extend(old); continue
        front=[tuple(p) for p in solid['vertices']]
        back=[tuple(p) for p in solid.get('back_vertices',[])] or [nc.add(p,solid['extrude']) for p in front]
        for side,points in [('front',front),('back',back)]:
            cap=[s for s in old if s['name'].startswith(solid['name']+'/'+side)]
            planar=None
            for i in range(len(points)):
                ordered=points[i:]+points[:i]
                if nc.norm(nc.cross(nc.sub(ordered[1],ordered[0]),nc.sub(ordered[2],ordered[0])))>1e-9:
                    planar=nc.planar_polygon(ordered);break
            if planar:
                part,mask=planar
                out.append(dict(name=solid['name']+'/'+side+'_merged',part=part,triangle=False,polygon_mask=mask,role=solid['role'],source_points=points))
                saved+=len(cap)-1
            else:out.extend(cap)
        out.extend(s for s in old if s['name'].startswith(solid['name']+'/perimeter'))
    return out,saved

def rotation(e):
    r=e.get('rotation') or {};angles=[r.get('angle',0) if r.get('axis')==axis else r.get(axis,0) for axis in 'xyz']
    return tuple(angles),tuple(r.get('origin',(0,0,0)))

def inverse(p,angles):
    # R = Rz Ry Rx, so inverse applies -z, -y, -x.
    x,y,z=p
    a,b,c=[math.radians(-v) for v in angles]
    x,y=x*math.cos(c)-y*math.sin(c),x*math.sin(c)+y*math.cos(c)
    x,z=x*math.cos(b)+z*math.sin(b),-x*math.sin(b)+z*math.cos(b)
    y,z=y*math.cos(a)-z*math.sin(a),y*math.sin(a)+z*math.cos(a)
    return x,y,z

def visible_faces(elements,is_mag):
    """Cull only faces fully inside one convex opaque cuboid in the same moving part.
    Four corners prove whole-face containment; no sample grid or cross-part culling.
    A tiny outward offset handles touching joins while retaining exterior surfaces.
    """
    records=[]
    for e in elements:
        angles,origin=rotation(e)
        corners=[nc.add(nc.tri.rotate(nc.sub(tuple(e['to'][i] if mask>>i&1 else e['from'][i] for i in range(3)),origin),angles),origin) for mask in range(8)]
        bounds=([min(p[i] for p in corners) for i in range(3)],[max(p[i] for p in corners) for i in range(3)])
        records.append((e,angles,origin,corners,bounds,is_mag(e['name'])))
    result={};culled=0
    for ei,(e,angles,origin,corners,bounds,part) in enumerate(records):
        keep=[]
        for face,indices in FACE_CORNERS.items():
            normal=nc.tri.rotate(FACE_NORMALS[face],angles)
            points=[nc.add(corners[i],nc.mul(normal,1e-5)) for i in indices]
            covered=False
            for ji,(other,oa,oo,oc,ob,op) in enumerate(records):
                if ji==ei or op!=part:continue
                if any(any(p[i]<ob[0][i]-1e-7 or p[i]>ob[1][i]+1e-7 for i in range(3)) for p in points):continue
                local=[inverse(nc.sub(p,oo),oa) for p in points]
                if all(all(other['from'][i]-1e-7<=p[i]<=other['to'][i]+1e-7 for i in range(3)) for p in local):
                    covered=True;break
            if covered:culled+=1
            else:keep.append(face)
        result[e['name']]=keep
    return result,culled
