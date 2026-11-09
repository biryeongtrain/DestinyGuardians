"""Source-first closed contour solids. Built from hand-authored profile landmarks, never ripped mesh conversion."""
import math

def refine(d,poly,cross):
 r=d.rect;b=d.beam
 if d.w=='deliverance':
  prefixes=('muzzle/','chamber/','junction/crown','crown','front_handle/','frame/inner_grip','frame/grip_edge','frame/rear_vertical','frame/rear_inward','frame/rear_return','frame/lower_return','frame/lower_belly','frame/lower_front')
  d.E=[e for e in d.E if not e['name'].startswith(prefixes)]
  # Narrow diamond muzzle in a rectangular solid block; four closed volumes form the real bore.
  cy=121;q=d.q;outer=[(-.88,74),(.88,74),(.88,166),(-.88,166)];diamond=[(0,107),(.23,121),(0,135),(-.23,121)]
  sections=[[(0,74),(.88,74),(.88,121),(.23,121),(0,107)],[(.88,121),(.88,166),(0,166),(0,135),(.23,121)],[(0,166),(-.88,166),(-.88,121),(-.23,121),(0,135)],[(-.88,121),(-.88,74),(0,74),(0,107),(-.23,121)]]
  for i,section in enumerate(sections):
   cross(d,f'muzzle/diamond_frame{i}',section,10,54,'shell')
   inner=[(x*.78,121+(v-121)*.78) for x,v in section];cross(d,f'muzzle/recessed_bezel{i}',inner,8,18,'edge')
  r('muzzle/upper_recess',10,69,53,75,1.65,'edge');r('muzzle/top_slot_floor',13,74,48,81,.65,'black')
  for s in [-1,1]:r(f'muzzle/top_rail{s}',12,66,51,74,.16,'shell',8+s*.74)
  # Long tapered side plate is one true wedge with a continuous lower contour.
  poly(d,'chamber/tapered_lower',[(53,122),(292,122),(292,210),(230,202),(149,191),(53,174)],1.60,'shell')
  r('chamber/fin_bedding',53,115,294,126,1.68,'black')
  # Twisted tapered lamellae. The cross-section rotates sinusoidally along the actual shroud.
  for j in range(23):
   u=54+j*10.4;theta=26*math.sin((j-2)*.41)
   profile=[(-.85,122),(-.18,69),(.18,69),(.85,122)]
   cross(d,f'chamber/twisted_lamella{j}',profile,u,u+8.1,'shell',theta)
  # Crown has its actual concave front notch, not a protruding decorative disc.
  poly(d,'junction/notched_crown',[(292,18),(416,18),(416,72),(291,72),(299,61),(304,48),(303,36),(299,27)],1.70,'shell')
  r('junction/crown_top_rail',291,15,420,21,.33,'edge',7.38);r('junction/crown_top_rail2',291,15,420,21,.33,'edge',8.62)
  for s in [-1,1]:
   path=[(322,27),(326,45),(340,57),(356,61),(372,57),(386,45),(390,27)]
   for j,(a,c) in enumerate(zip(path,path[1:])):b(f'crown{s}/engraved_arc{j}',a,c,1.6,.06,'black',8+s*.87)
  # Massive rounded forward quadrant and crescent return carry the silhouette.
  poly(d,'frame/forward_cast_quadrant',[(294,122),(415,122),(415,273),(433,274),(433,302),(462,315),(461,335),(326,335),(316,314),(307,286),(301,255),(296,220)],1.54,'shell')
  poly(d,'frame/continuous_crescent',[(327,274),(435,274),(435,296),(471,301),(526,296),(573,283),(606,262),(632,231),(650,191),(655,168),(679,168),(675,213),(662,250),(643,278),(615,301),(580,319),(541,331),(493,337),(459,337),(327,335)],1.48,'shell')
  poly(d,'frame/rear_cheek',[(673,165),(731,165),(731,267),(670,267),(650,252),(663,219)],1.20,'shell')
  poly(d,'frame/diagonal_handhold',[(490,174),(550,174),(594,271),(535,271)],1.10,'shell')
  for side in [-1,1]:
   x=8+side*.80;r(f'forward{side}/latch_socket',326,215,364,240,.08,'black',x);r(f'forward{side}/latch',334,217,355,238,.11,'edge',x+side*.03)
  r('frame/front_vertical_ornament',294,126,322,211,1.70,'shell')
  d.E=[e for e in d.E if not e['name'].startswith('junction/orange_quadrant')]
  poly(d,'junction/curved_shoulder',[(292,122),(303,108),(320,95),(342,85),(368,76),(391,72),(416,72),(416,122)],1.84,'accent')
  poly(d,'junction/rear_shoulder_sweep',[(416,72),(439,84),(467,95),(497,102),(497,124),(416,124)],1.22,'shell')
  for side in [-1,1]:
   poly(d,f'lever{side}/raised_crescent',[(343,124),(382,124),(388,143),(385,155),(376,167),(364,174),(345,174),(353,160),(357,144)],.20,'shell',8+side*.88)
   r(f'lever{side}/under_recess',343,174,385,184,.10,'black',8+side*.81)

 elif d.w=='forbearance':
  prefixes=('mag_barrel/','breech/orange_quadrant','receiver/upper_rail','receiver/lower_core','receiver/recess','stock/top_shell','stock/lower_cheek','stock/front_swept_face','stock/heel_sweep')
  d.E=[e for e in d.E if not e['name'].startswith(prefixes)]
  # Source cylindrical chamber is exposed between the angular nose fins and broad swept breech shoulders.
  d.ring('mag_barrel/round_chamber',300.5,132,36,227,4,'black',16);d.ring('mag_barrel/narrow_fin_core',126,132,23,122,3,'black',12)
  # Rectangular nose with a circular bore and real depth.
  N=12;outer=[];inner=[]
  for j in range(N):
   a=2*math.pi*j/N;x=math.sin(a);y=math.cos(a);t=min(1.21/(abs(x) or 1e-9),1.34/(abs(y) or 1e-9));outer.append((x*t,132-y*t/d.q));inner.append((x*22*d.q,132-y*22))
  aa=1.21;bb=1.34;outer_xy=[(0,bb),(aa,bb),(aa,bb/2),(aa,0),(aa,-bb),(aa/2,-bb),(0,-bb),(-aa,-bb),(-aa,-bb/2),(-aa,0),(-aa,bb),(-aa/2,bb)];outer=[(x,132-y/d.q) for x,y in outer_xy]
  for j in range(N):k=(j+1)%N;cross(d,f'mag_barrel/rect_nose_segment{j}',[outer[j],outer[k],inner[k],inner[j]],30,67,'shell')
  for side in [-1,1]:
   def mirror(pro):return [(side*x,v) for x,v in pro][::side]
   cross(d,f'mag_barrel/front_outer_post{side}',mirror([(1.08,90),(1.24,90),(1.24,173),(1.08,173)]),10,31,'shell')
   cross(d,f'mag_barrel/upper_lobed_lip{side}',mirror([(.23,90),(1.16,90),(1.16,95),(.87,95),(.65,96),(.45,100),(.30,106),(.23,112)]),10,31,'shell')
   cross(d,f'mag_barrel/lower_lobed_lip{side}',mirror([(1.17,146),(1.17,173),(.61,173),(.64,164),(.72,156),(.89,149)]),10,31,'shell')
  cross(d,'mag_barrel/front_central_stem',[(-.23,90),(.23,90),(.23,112),(-.23,112)],10,31,'shell')
  cross(d,'mag_barrel/front_lower_field',[(-.48,153),(.48,153),(.48,173),(-.48,173)],10,31,'shell')
  d.ring('mag_barrel/bore_lip',11,132,23,6,2,'steel',12);d.ring('mag_barrel/deep_bore',45,132,22,60,2,'black',12)
  # Two staggered arrays of angular helical fins, each a closed tapered solid.
  for j in range(7):
   for side in [-1,1]:
    u=70+j*16+(5 if side>0 else 0);profile=[(side*.10,91),(side*.45,84),(side*1.20,137),(side*.72,163)]
    if side<0:profile.reverse()
    cross(d,f'mag_barrel/interleaved_fin{side}_{j}',profile,u,u+10,'shell',[-28,12,39,-16,31,-35,8][j] + side*18)
  r('mag_barrel/lower_rail',69,164,190,174,1.55,'steel')
  # Broad swept outer cheek follows the actual quarter-circle outline; it is proud of the barrel.
  outline=[(316,173),(320,153),(329,133),(342,117),(359,104),(378,96),(396,92),(414,92),(414,174)]
  poly(d,'breech/swept_left_shoulder',outline,.23,'accent',6.82);poly(d,'breech/swept_right_shoulder',outline,.23,'accent',9.18)
  r('breech/shoulder_bridge',401,93,416,174,2.44,'accent')
  # Long open receiver channel and internal sliding mechanism.
  for side in [-1,1]:r(f'receiver/side_wall{side}',416,92,598,161,.24,'shell',8+side*.94)
  r('receiver/channel_floor',420,126,598,139,1.65,'black');r('receiver/lower_keel',426,146,598,162,1.67,'shell')
  for u in [431,466,519]:r(f'receiver/channel_bridge{u}',u,104,u+7,119,1.75,'steel')
  d.ring('receiver/internal_cylinder',474,116,9,85,3,'steel',8)
  r('receiver/slide_rod',431,112,525,118,.22,'black',7.50)
  for side in [-1,1]:r(f'receiver/channel_rail{side}',421,92,535,98,.15,'edge',8+side*.72)
  # Rear shoulder tapers around its cutout and long top recess.

  for side in [-1,1]:poly(d,f'stock/sculpted_cheek{side}',[(598,94),(776,94),(776,130),(759,137),(748,155),(742,170),(641,170),(626,151),(613,126)],.20,'shell',8+side*.65)
  poly(d,'stock/lower_core',[(606,115),(776,115),(776,130),(759,137),(748,155),(742,170),(641,170),(626,151),(613,126)],1.13,'shell')
  r('stock/top_channel_floor',626,101,767,113,.84,'black')
  for side in [-1,1]:r(f'stock/top_channel_rail{side}',622,90,773,100,.20,'shell',8+side*.63)
  # Re-cut the top cavity by narrowing the side support beneath its open rails.
  d.E=[e for e in d.E if e['name']!='stock/sculpted_cheek']
 elif d.w=='apex_predator':
  d.E=[e for e in d.E if not e['name'].startswith(('bone/','grip/','tube/navy','muzzle/','exhaust/','sight/'))]
  d.ring('tube/continuous_front',312,75,36.5,424,3.5,'accent',16);d.ring('tube/continuous_rear',836,75,36.5,630,3.5,'accent',16)
  d.ring('muzzle/deep_inner_bore',100,75,25,28,2,'black',12);d.ring('exhaust/open_lip',1149,75,38,15,4,'steel',16)
  # Actual source transverse probes show two open oval skins around the tube, not planar side wings.
  from closed_sections import shell,oval_arc
  lower=[(25,.10,128,130),(91,.72,106,132),(150,1.02,75,136),(310,1.05,81,149),(420,1.05,81,144),(548,1.03,81,174),(617,.73,104,143)]
  sections=[oval_arc(d.p,u,rx,top,bottom,[0,36,72,108,144,180],wall=min(.085,rx*.4),q=d.q) for u,rx,top,bottom in lower]
  d.C.append(shell('bone/continuous_oval_lower_skin',sections,d.p,'shell'))
  # The upper bowed crown is an arched transverse strip; its underside retains the long source opening.
  stations=[(128,.15,76,74),(174,.64,61,47),(226,.82,58,29),(306,.92,43,21),(422,.68,30,17),(508,.47,24,14),(552,.13,16,11)]
  sections=[]
  for u,rx,edge,crest in stations:
   outer=[];inner=[]
   for t in [-1,-.33,.33,1]:
    v=crest+(edge-crest)*t*t;outer.append(d.p(u,v,8+rx*t));inner.append(d.p(u,v+3.2,8+rx*t))
   sections.append((outer,inner))
  d.C.append(shell('bone/arched_upper_skin',sections,d.p,'shell'))
  sections=[]
  for u,rx,edge,crest in [(10,.40,45,38),(50,.72,56,38),(100,.85,75,38)]:
   outer=[];inner=[]
   for t in [-1,-.5,0,.5,1]:
    v=crest+(edge-crest)*t*t;outer.append(d.p(u,v,8+rx*t));inner.append(d.p(u,v+5,8+rx*t))
   sections.append((outer,inner))
  d.C.append(shell('muzzle/open_scalloped_hood',sections,d.p,'accent'))

  # Actual palm opening and hooked backstrap, not a polygonal ladder of intersecting bars.
  handle=[(312,142),(345,149),(358,175),(368,221),(382,263),(402,292),(431,301),(544,283),(616,272),(626,258),(614,227),(600,195),(593,168),(611,151),(624,193),(647,233),(668,247),(701,240),(663,270),(620,294),(543,306),(429,320),(405,317),(388,305),(374,280),(362,245),(350,195),(338,163)]
  poly(d,'grip/closed_sculpted_frame',handle,1.13,'shell')
  # Navy lower-edge marking is a material region on the continuous frame, not a second overlapping shell.
  poly(d,'grip/navy_heel_hook',[(526,299),(585,319),(614,287),(620,294),(589,329),(574,329),(520,307)],.86,'accent')
  poly(d,'bone/rear_window_outer',[(507,42),(551,38),(591,44),(650,64),(711,94),(717,105),(704,114),(620,143),(604,142),(668,116),(694,101),(645,78),(590,59),(550,51)],1.10,'shell')
  poly(d,'bone/rear_window_strut',[(587,67),(650,88),(678,108),(672,117),(638,96),(588,80)],1.07,'edge')
  d.ring('sight/offset_cylinder',526,75,22,55,4,'black',12,9.755);d.ring('sight/offset_front_lip',499,75,23,7,3,'edge',12,9.755);r('sight/connecting_mount',508,76,532,97,1.05,'black',9.16)
 elif d.w=='cataclysmic':
  drop=('fork/top_body','fork/lower_body','fork/front_bridge','sight/','fork/top_inset','fork/flute','fork/under_swept_keel','fork/lower_root','frame/orange_','frame/front_dark_inset','frame/rear_curve','frame/rear_return','frame/lower_bed','grip/diagonal_core','grip/rear_bevel','grip/heel')
  d.E=[e for e in d.E if not e['name'].startswith(drop)]
  # Measured source transverse sections: open, asymmetric front channels; twisting SQUARE blocks above the bedding.
  for side in [-1,1]:
   pro=[(.88,65),(.88,111),(.43,111),(.43,106),(.29,100),(.27,85),(.30,80),(.42,80),(.65,76),(.79,70),(.80,65)]
   if side<0:pro=[(-x,v) for x,v in reversed(pro)]
   cross(d,f'fork/front_upper_channel{side}',pro,10,125,'shell',center_v=85)
   pro=[(.88,146),(.88,190),(.30,190),(.30,174),(.29,161),(.43,155),(.49,151),(.49,146)]
   if side<0:pro=[(-x,v) for x,v in reversed(pro)]
   cross(d,f'fork/lower_channel{side}',pro,10,445,'shell',center_v=166)
  r('fork/upper_channel_floor',28,105,386,111,1.65,'shell')
  r('fork/lower_channel_floor',10,174,445,190,1.15,'shell')
  cross(d,'fork/front_diagonal_cut',[(-.30,174),(.30,174),(.30,185),(.17,190),(-.30,190)],10,32,'edge',center_v=180)
  r('fork/rib_bedding',127,104,386,112,1.76,'black')
  for j in range(17):
   u=130+j*15.1;theta=42*math.cos((u-150)*2*math.pi/105)
   profile=[(-.61,57),(.61,57),(.61,109),(-.61,109)]
   cross(d,f'fork/rotating_square_block{j}',profile,u,u+11.5,'shell',theta,83)
  # Open arched iron sight in the actual transverse plane, not an opaque crossbar.
  pts=[(-.68,48),(-.68,35),(-.64,23),(-.54,14),(-.39,9),(-.17,8),(.17,8),(.39,9),(.54,14),(.64,23),(.68,35),(.68,48)]
  for j,((x,v),(X,V)) in enumerate(zip(pts,pts[1:])):
   a=d.p(590,v,8+x);bb=d.p(590,V,8+X);cc=[(a[k]+bb[k])/2 for k in range(3)];L=math.dist(a,bb);ang=math.degrees(math.atan2(bb[1]-a[1],bb[0]-a[0]))
   d.add(f'sight/open_arch{j}',[cc[0]-L/2,cc[1]-.025,cc[2]-.025],[cc[0]+L/2,cc[1]+.025,cc[2]+.025],'ivory',dict(origin=cc,x=0,y=0,z=ang))
  r('sight/arch_floor',588,47,592,49,1.40,'ivory')
  for side in [-1,1]:r(f'sight/open_leg{side}',588,49,592,67,.05,'ivory',8+side*.60)
  r('sight/central_bead',588,42,592,51,.06,'ivory')
  b('sight/long_wire',(592,64),(687,64),3,.07,'ivory');b('sight/rear_branch',(620,86),(643,64),3,.07,'ivory')
  poly(d,'fork/sculpted_front_keel',[(11,191),(55,191),(55,262),(42,253),(28,236),(18,216)],1.40,'shell')
  poly(d,'fork/sculpted_root',[(353,147),(446,147),(446,258),(437,258),(429,235),(410,214),(384,199),(353,191)],1.68,'shell')
  poly(d,'frame/orange_curved_arch',[(446,143),(462,151),(475,167),(487,189),(496,217),(502,249),(501,279),(495,308),(482,335),(473,349),(446,349),(446,330),(459,317),(469,291),(475,263),(474,232),(468,204),(457,182),(446,176)],1.62,'accent')
  poly(d,'frame/front_inset',[(456,194),(474,183),(485,211),(491,239),(491,274),(483,305),(474,333),(457,324)],1.70,'shell')
  poly(d,'frame/continuous_lower_return',[(480,303),(735,303),(753,278),(766,249),(775,217),(778,176),(808,176),(807,223),(796,268),(780,303),(758,330),(735,345),(480,345)],1.38,'shell')
  poly(d,'grip/actual_raked_palm',[(646,181),(697,181),(753,297),(699,297)],1.20,'shell')
  # Beveled exposed cell-stack bracket and actual upper receiver inset band.
  for side in [-1,1]:r(f'rear/upper_rail{side}',826,83,1047,91,.17,'shell',8+side*.66)
  r('rear/top_channel_floor',830,92,1040,97,1.13,'black')
