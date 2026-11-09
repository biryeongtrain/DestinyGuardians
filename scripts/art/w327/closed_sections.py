"""Semantic closed section lofts: shared edges, two skins, closed end/side walls."""
import math

def shell(name,sections,point,role):
 # A section is [outer arc, inner arc], corresponding profile vertices at each station.
 vertices=[];faces=[];N=len(sections[0][0]);stride=N*2
 for outer,inner in sections:vertices.extend(outer+inner)
 for k in range(len(sections)-1):
  a=k*stride;b=a+stride
  for j in range(N-1):faces.extend([(a+j,a+j+1,b+j+1,b+j),(a+N+j,b+N+j,b+N+j+1,a+N+j+1)])
  faces.extend([(a,b,b+N,a+N),(a+N-1,a+2*N-1,b+2*N-1,b+N-1)])
 for base in [0,(len(sections)-1)*stride]:
  for j in range(N-1):faces.append((base+j,base+N+j,base+N+j+1,base+j+1))
 # Structural topology check: every undirected edge occurs twice in the closed surface.
 edges={}
 for f in faces:
  for i,j in zip(f,f[1:]+f[:1]):key=tuple(sorted((i,j)));edges[key]=edges.get(key,0)+1
 assert set(edges.values())=={2}
 return dict(name=name,vertices=vertices,mesh_faces=faces,role=role)

def oval_arc(p,u,rx,top,bottom,angles,wall=.09,q=.0234,xc=8):
 # Source-referenced oval arc about top; lower arcs positive sine, upper negative.
 outer=[];inner=[]
 for a in angles:
  aa=math.radians(a);outer.append(p(u,top+(bottom-top)*math.sin(aa),xc+rx*math.cos(aa)))
  inner.append(p(u,top+(bottom-top-wall/q)*math.sin(aa),xc+(rx-wall)*math.cos(aa)))
 return outer,inner

def solid_loft(name,sections,role):
 N=len(sections[0]);vertices=sum(sections,[]);faces=[]
 for k in range(len(sections)-1):
  for j in range(N):a=k*N+j;b=k*N+(j+1)%N;faces.append((a,b,b+N,a+N))
 faces.append(tuple(reversed(range(N))));faces.append(tuple((len(sections)-1)*N+j for j in range(N)))
 return dict(name=name,vertices=vertices,mesh_faces=faces,role=role)
