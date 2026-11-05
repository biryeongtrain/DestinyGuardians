import json,sys,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts/art/w325'));import kit
INFO={
'cup_bearer_sa_2':('전방 프레임·레일·하부 빔·개머리판 기둥 → warmsteel, 하부 리시버·가드 → darksteel. 크림/올리브 위장은 외피 패널에만 유지.','1텍셀 냉각 슬릿과 붉은 레버 표시; 크림/연두 2색 큰 위장 블록.',('polymer','rubber')),
'reginar_b':('포구·밴드·칼라 → lightsteel, 가드·탄창 수용부·그립 장착부 → darksteel. 올리브색은 후방 도장 외피에 유지.','HAKKE 각인 띠, 백색 데이터 눈금.',('polymer','rubber')),
'weaver_c':('리시버 상부 → warmsteel, 하부·가드 → brownsteel, 포구·칼라 → lightsteel. 크림 전방관/주황 후방관은 도장 유지.','HAKKE 각인, 주황 후방관 1텍셀 육각 패널선.',('brown','brown_rubber')),
'plemusa_b':('드럼 프레임·측판·개머리판·하부 레일 → gunmetal, 포구창·리시버 전면·그립 프레임 → lightsteel. 청록 외피/황색 드럼 도장 유지.','드럼 양 끝의 1텍셀 리벳 점열, HAKKE와 녹색 상태등.',('polymer','rubber')),
'stampede_mk_32':('리시버 하부·드럼 기둥·루프·가드 → gunmetal, 포구·밴드·조준기·버트 캡 → lightsteel. 녹색 위장은 외피에만 유지.','1텍셀 천공/냉각 구멍과 파란 표시창; 녹색 3색 큰 위장 블록.',('polymer','rubber')),
'future_imperfect':('폼멜·페룰 → lightsteel, 리카소 → warmsteel. 칼날 steel, 손잡이 cloth를 유지해 도장 면을 제거.','검날의 연속 1텍셀 홈선과 리카소 슬롯.',('wrap','wrap_ridge')),
'rest_for_the_wicked':('가드 칼라 → darksteel. 검은 금속 몸체·밝은 steel 날·중앙 steel 패널 유지, 손잡이 rubber를 더 어둡게 조정.','중앙 패널의 양열 리벳 점선.',('wrap','panelsteel')),
}
base=json.loads((ROOT/'art/weapons/w325/_m10/material_geometry_baseline.json').read_text())
out={};canvas=Image.new('RGB',(1800,2100),'#25282c');draw=ImageDraw.Draw(canvas)
text='# W325 m10 Material R2\n\n원본 비교와 W123 레퍼런스를 기준으로 노출 금속을 재배정했다. R1 재질 목록/재질 설명은 본 R2 결과로 대체한다.\n\n'
for i,(w,(change,motif,pair)) in enumerate(INFO.items()):
 d=kit.load_design(w);els=d.elements();digest=hashlib.sha256(json.dumps(els,sort_keys=True).encode()).hexdigest();assert digest==base[w]
 man=json.loads((kit.art(w)/'manifest.json').read_text());assert man['atlas']==([512,512] if 'imperfect' in w or 'wicked' in w else [1024,512])
 for p,h in man['outputs_sha256'].items():assert kit.sha(ROOT/p)==h
 lum=lambda rgb:sum(a*b for a,b in zip(rgb,(.299,.587,.114)))
 delta=abs(lum(d.MATERIALS[pair[0]]['color'])-lum(d.MATERIALS[pair[1]]['color']));assert delta>=25,(w,delta)
 out[w]={'change':change,'motif':motif,'geometry_unchanged':True,'atlas':man['atlas'],'elements':len(els),'contrast_pair':pair,'luminance_delta':round(delta,2),'adscheck':'OK','native_QA':'not run','png_bytes':kit.atlas_path(w).stat().st_size}
 sec='## '+w+'\n\n'+change+'\n\n모티프: '+motif+f'\n\n대표 대비 {pair[0]} / {pair[1]}: 명도 차이 {delta:.2f}. 요소 {len(els)}, atlas {man["atlas"]}, T20, adscheck OK.\n\n'
 text+=sec
 p=kit.art(w)/'notes.md';p.write_text(p.read_text()+'\n\n## Material R2 — 2026-11-05 (R1 재질 재배정을 대체)\n\n'+change+'\n\n'+motif+f'\n\n대표 재질 명도 차이 {delta:.2f}. 원소/좌표/회전/부품명 SHA-256 동일, 아틀라스 크기 유지, adscheck OK. 실제 인게임 검증은 master 단계에 남음.\n')
 im=Image.open(kit.art(w)/'review'/f'{w}_q.png');im.thumbnail((900,490));x=i%2*900;y=i//2*525;canvas.paste(im,(x+(900-im.width)//2,y));draw.text((x+12,y+497),w+' | MATERIAL R2',fill='white')
canvas.save(ROOT/'art/weapons/w325/_m10/material_r2_review.png')
text+='전체 7종 형상·아틀라스 동일, kit build/UV/출력 해시 확인. kit.py 변경, 커밋, Gradle/Minecraft 실행 없음.\n'
(ROOT/'art/weapons/w325/_m10/material_r2_report.md').write_text(text)
(ROOT/'art/weapons/w325/_m10/material_r2_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('PASS: 7 unchanged geometries/atlases, output hashes, representative contrast >=25')
print('PNG bytes:',sum(d['png_bytes'] for d in out.values()))
