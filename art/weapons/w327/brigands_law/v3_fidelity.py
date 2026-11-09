"""Source exterior fidelity pass: original palm swell, hooked backstrap, curved guard and swept receiver."""
import math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'scripts/art/w327'))
from closed_sections import shell,solid_loft

def refine(E,p):
 drop=('barrel/','breech/','muzzle/ivory_outer','muzzle/bore_back','receiver/steel_bedding','bow/','rear/upper_tail','rear/raised_tail_point','rear/cap','rear/dark_breech_slot','rear/breech_slot_roof','rear/breech_slot_sill','receiver/front_lower_cheek','receiver/belly_','receiver/rising_rear_cheek','receiver/grip_bridge','receiver/rear_scroll','receiver/front_lower_chamfer','receiver/rear_lower_chamfer','grip/internal_spine','grip/upper_raked_cheek','grip/palm_swell','grip/heel','grip/backstrap','grip/frontstrap','guard/')
 E=[e for e in E if not e['name'].startswith(drop)];C=[]
 def poly(name,outline,width,role,xc=8):C.append(dict(name=name,vertices=[p(u,v,xc-width/2) for u,v in outline],extrude=[width,0,0],role=role))
 def stroke(name,path,thick,width,role):
  normals=[]
  for (u,v),(U,V) in zip(path,path[1:]):
   L=math.hypot(U-u,V-v);normals.append((-(V-v)/L,(U-u)/L))
  offsets=[]
  for i,pt in enumerate(path):
   n=normals[0] if i==0 else normals[-1] if i==len(path)-1 else tuple(normals[i-1][j]+normals[i][j] for j in range(2));L=math.hypot(*n);n=tuple(x/L for x in n);den=1 if i in (0,len(path)-1) else max(.5,sum(n[j]*normals[i][j] for j in range(2)));offsets.append(tuple(x*thick/2/den for x in n))
  outline=[(a[0]+b[0],a[1]+b[1]) for a,b in zip(path,offsets)]+[(a[0]-b[0],a[1]-b[1]) for a,b in reversed(list(zip(path,offsets)))];poly(name,outline,width,role)
 # Source transverse sections show the receiver is round above a narrower rounded keel.
 q=36.5/1400
 def circle(u,v,rx,ry,N=12):return [p(u,v+ry*math.sin(j*2*math.pi/N),8+rx*math.cos(j*2*math.pi/N)) for j in range(N)]
 C.append(solid_loft('receiver/round_main_shell',[circle(u,v,r*q,r,12) for u,v,r in [(43,66,32),(75,66,30),(145,67,27),(225,67,28),(275,66,26)]],'ivory'))
 # The underbody is a round-bottom narrow keel, continuous from the lower mouth to the grip shoulder.
 sections=[]
 for u,top,bottom,rx in [(65,88,113,.42),(145,92,133,.57),(225,91,139,.61),(300,83,131,.59),(380,79,137,.57),(440,80,123,.54),(470,83,103,.32)]:
  vv=[p(u,top,8-rx),p(u,top,8+rx),p(u,bottom-10,8+rx),p(u,bottom-3,8+rx*.65),p(u,bottom,8),p(u,bottom-3,8-rx*.65),p(u,bottom-10,8-rx)]
  sections.append(vv)
 C.append(solid_loft('receiver/rounded_lower_keel',sections,'ivory'))
 # Trumpet flare is a real annular shell with an open bore and a curved transverse upper bow.
 sections=[]
 for u,r in [(33,37),(44,33),(71,30)]:
  outer=circle(u,66,r*q,r,12);inner=circle(u,66,(r-3)*q,r-3,12);outer.append(outer[0]);inner.append(inner[0]);sections.append((outer,inner))
 C.append(shell('muzzle/trumpet_flare',sections,p,'ivory_edge'))
 C.append(solid_loft('breech/exposed_neck',[circle(u,55,r*q,r,12) for u,r in [(275,15),(330,15)]],'steel'))
 C.append(solid_loft('breech/rear_tapered_collar',[circle(u,62,r*q,r,12) for u,r in [(330,25),(355,27),(395,37)]],'ivory'))
 C.append(solid_loft('rear/flared_tail',[circle(u,63,r*q,r,12) for u,r in [(396,23),(463,23),(480,27),(495,34)]],'ivory'))
 stroke('bow/narrow_upper_sweep',[(139,32),(208,18),(267,20),(333,33),(395,30)],3,.09,'ivory_edge')

 # The back edge swells to x499 at the palm and hooks inward again at the heel.
 poly('grip/source_palm_contour',[(366,137),(374,160),(383,196),(393,230),(404,271),(403,295),(398,303),(488,303),(489,294),(496,282),(499,273),(495,257),(482,235),(466,205),(449,170),(443,140),(425,133),(393,132)],1.92,'grip')
 poly('grip/hooked_backstrap',[(438,139),(447,139),(453,170),(470,204),(486,235),(499,256),(503,273),(498,285),(491,297),(485,302),(477,300),(487,287),(492,275),(488,261),(475,239),(459,208),(443,174)],1.67,'ivory_edge')
 stroke('grip/frontstrap_curve',[(371,151),(380,194),(391,232),(403,273),(401,298)],6,1.54,'ivory_dark')
 stroke('guard/source_front_sweep',[(185,197),(194,183),(212,169),(231,154),(249,148),(262,135)],6,.38,'ivory')
 stroke('guard/source_floor_sweep',[(184,197),(220,194),(273,191),(320,188),(366,183),(376,167)],6.5,.40,'ivory')
 return E,C
