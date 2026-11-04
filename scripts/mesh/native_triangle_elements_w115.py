#!/usr/bin/env python3
"""26.3 vanilla triangle adapter: two rotated alpha-masked cuboid planes.

This is NOT a raw mesh JSON loader. CuboidModelElement accepts Euler x/y/z
rotations; CuboidRotation applies Rz(z)*Ry(y)*Rx(x). A longest-edge altitude
splits an arbitrary triangle into at most two right triangles. Each right
triangle is a single zero-depth cuboid with two faces and a triangular atlas
island (opaque iff u<=v). No entity, composite child or custom client is needed.
Caller must bake each atlas island from its returned 3D basis, including alpha;
plain opaque rectangles are NOT triangles. Bounds/alpha/native acceptance must
be checked by the consumer. Functions here only guarantee geometric mapping.
"""
import math

def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a):
 n=norm(a)
 if n<=1e-12:raise ValueError('Degenerate basis')
 return mul(a,1/n)

def euler_zyx(u,v,n):
 """Angles in degrees for matrix with columns u,v,n; native rotationZYX."""
 y=math.asin(max(-1.,min(1.,-u[2])))
 if abs(math.cos(y))>1e-8:x,z=math.atan2(v[2],n[2]),math.atan2(u[1],u[0])
 else:x,z=math.atan2(-n[1],v[1]),0.
 return tuple(math.degrees(t) for t in (x,y,z))

def rotate(p,angles):
 """Independent direct Rx then Ry then Rz, matching Minecraft bytecode."""
 x,y,z=p;a,b,c=map(math.radians,angles)
 y,z=y*math.cos(a)-z*math.sin(a),y*math.sin(a)+z*math.cos(a)
 x,z=x*math.cos(b)+z*math.sin(b),-x*math.sin(b)+z*math.cos(b)
 x,y=x*math.cos(c)-y*math.sin(c),x*math.sin(c)+y*math.cos(c)
 return x,y,z

def split_triangle(vertices):
 if len(vertices)!=3 or any(len(v)!=3 for v in vertices):raise ValueError('Expected three XYZ vertices')
 points=[tuple(float(x) for x in v) for v in vertices]
 if any(not math.isfinite(x) for v in points for x in v):raise ValueError('Nonfinite triangle')
 a,b,c=max(((points[i],points[(i+1)%3],points[(i+2)%3]) for i in range(3)),key=lambda t:norm(sub(t[1],t[0])))
 edge=sub(b,a);length=norm(edge)
 if length<=1e-10:raise ValueError('Degenerate triangle')
 along=mul(edge,1/length);offset=dot(sub(c,a),along);foot=add(a,mul(along,offset));height=norm(sub(c,foot))
 if height<=1e-10:raise ValueError('Degenerate triangle')
 vertical=unit(sub(c,foot));parts=[]
 for endpoint in (a,b):
  width=norm(sub(endpoint,foot))
  if width<=1e-10:continue
  u=unit(sub(endpoint,foot));n=unit(cross(u,vertical));angles=euler_zyx(u,vertical,n)
  parts.append(dict(origin=foot,u=u,v=vertical,width=width,height=height,rotation=angles,
                    vertices=(foot,endpoint,c)))
 return parts

def point_at(part,u,v):
 """Atlas normalized coordinates: top-left=(0,0), opaque when u<=v."""
 return add(part['origin'],add(mul(part['u'],u*part['width']),mul(part['v'],(1-v)*part['height'])))

def to_element(part,name,uv,texture='#0'):
 if len(uv)!=4 or any(not math.isfinite(x) or not 0<=x<=16 for x in uv):raise ValueError('Invalid atlas UV')
 if uv[2]<=uv[0] or uv[3]<=uv[1]:raise ValueError('Invalid atlas island')
 center=add(part['origin'],add(mul(part['u'],part['width']/2),mul(part['v'],part['height']/2)))
 origin=sub(center,(part['width']/2,part['height']/2,0.));end=add(center,(part['width']/2,part['height']/2,0.))
 if any(not -16<=x<=32 for p in (origin,end) for x in p):raise ValueError('Vanilla unrotated element bounds exceeded')
 # north is mirrored horizontally relative to south in FaceBakery.
 return dict(name=name,**{'from':list(origin),'to':list(end)},
  rotation=dict(origin=list(center),x=part['rotation'][0],y=part['rotation'][1],z=part['rotation'][2]),
  faces=dict(south=dict(uv=list(uv),texture=texture),north=dict(uv=[uv[2],uv[1],uv[0],uv[3]],texture=texture)))
