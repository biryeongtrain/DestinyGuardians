#!/usr/bin/env python3
"""Compare preserved legacy and PROFILE view packs; no pack/source modification."""
import argparse,collections,hashlib,json,re,zipfile
from pathlib import Path

def inventory(path):
    raw=Path(path).read_bytes(); groups=collections.defaultdict(lambda:dict(files=0,raw=0,compressed=0))
    with zipfile.ZipFile(path) as z:
        for i in z.infolist():
            if i.is_dir():continue
            n=i.filename
            group=('legacy-arms' if any(x in n for x in ('/weapon_hands_w201/','/skin_arm_w204/')) else
                   'profile-view' if any(x in n for x in ('/profile_view/','/profile_arm.')) else
                   'weapon-poses' if '/first_person_framing_w205/' in n else
                   'sounds' if '/sounds/' in n else 'other')
            g=groups[group];g['files']+=1;g['raw']+=i.file_size;g['compressed']+=i.compress_size
        return dict(path=str(Path(path).resolve()),bytes=len(raw),sha1=hashlib.sha1(raw).hexdigest(),files=len(z.infolist()),rawBytes=sum(i.file_size for i in z.infolist()),groups=dict(groups))
def compare(old,new):
    a,b=inventory(old),inventory(new)
    return dict(legacy=a,profile=b,zipSavedBytes=a['bytes']-b['bytes'],zipReductionPercent=100*(a['bytes']-b['bytes'])/a['bytes'],rawSavedBytes=a['rawBytes']-b['rawBytes'])
def log_times(path):
    text=Path(path).read_text(errors='replace');p={}
    for key,pattern in [('startupSeconds',r'Game took ([\d.]+) seconds to start'),('menuToWorldSeconds',r'Time from main menu to in-game was ([\d.]+) seconds'),('totalSeconds',r'Total time to load game and open world was ([\d.]+) seconds')]:
        matches=re.findall(pattern,text)
        if matches:p[key]=float(matches[-1])
    p['oom']='OutOfMemoryError' in text
    p['shaderCompileOrLinkFailure']=bool(re.search(r'Shader compilation failed|Failed to compile.*shader|Failed to link.*shader',text,re.I))
    return p

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--legacy',required=True);p.add_argument('--profile',required=True);p.add_argument('--old-log');p.add_argument('--new-log');p.add_argument('--out',required=True);a=p.parse_args()
    result=compare(a.legacy,a.profile)
    if a.old_log and a.new_log:
        result['legacyLoad']=log_times(a.old_log);result['profileLoad']=log_times(a.new_log)
        result['timingScope']='ModernFix log timestamps; same QA profile/heap/mods; single sample unless separately stated; not a benchmark percentile'
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
