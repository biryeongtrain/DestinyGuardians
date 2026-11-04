#!/usr/bin/env python3
"""Verify the delivered bank; render its segments with wwiser/vgmstream, never file-order playlists.
Requires soundfile/numpy, vgmstream-cli and a wwiser checkout. Source is read-only.
"""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import soundfile as sf

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--wwiser',type=Path,required=True)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    a=ap.parse_args(); source=a.source.resolve(); cache=a.cache.resolve(); cache.mkdir(parents=True,exist_ok=True)
    def read(name): return json.loads((source/name).read_text(encoding='utf-8-sig'))
    hashes=read('FILE-HASHES.json')
    for name,digest in hashes.items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest: raise ValueError('Checksum: '+name)
    subprocess.run([sys.executable,str(a.wwiser),str(source/'wwise/80D52522.bnk'),'-d','none','-g','-gu','-gd','-gv','1','-go',str(cache),'-gw',str(source/'wwise/wem'),'-gf','CAkMusicSegment','-gxni'],check=True)
    resources=a.root/'src/main/resources'; out=resources/'assets/destiny_music/sounds/devils';out.mkdir(parents=True,exist_ok=True)
    segments={str(x['segment_id']):dict(x) for x in read('wwise/segments.json') if x['bank_tag']=='80D52522'}
    for node in ET.parse(source/'wwise/banks.xml').iter('object'):
        if node.get('name')!='CAkMusicSegment': continue
        fields={x.get('name'):x.get('value') for x in node.iter('field')}
        sid=fields.get('ulID')
        if sid in segments:
            segments[sid].update(beats_per_bar=int(fields['uTimeSigNumBeatsBar']),beat_value=int(fields['uTimeSigBeatValue']),grid_offset_ms=float(fields['fGridOffset']))
    sounds_path=resources/'assets/destiny_music/sounds.json';sounds=json.loads(sounds_path.read_text())
    report=[]
    for txtp in sorted(cache.glob('*.txtp')):
        if 'INACTIVE' in txtp.name: continue # Runtime engagement trigger is not established; active mix only.
        match=re.search(r'musicsegment-(\d+)',txtp.name)
        if not match: continue
        sid=match[1];wav=cache/(sid+'.wav');ogg=out/(sid+'.ogg')
        subprocess.run(['vgmstream-cli','-W','4','-i','-o',str(wav),str(txtp)],check=True,stdout=subprocess.DEVNULL)
        peak=0.; frames=0
        with sf.SoundFile(wav) as f:
            rate=f.samplerate
            for block in f.blocks(blocksize=65536,dtype='float32'):
                if not np.isfinite(block).all(): raise ValueError('Non-finite PCM '+sid)
                peak=max(peak,float(np.max(np.abs(block))));frames+=len(block)
        # Fixed global headroom, not per-song normalization; preserves relative bank gains.
        if peak*.3>0.98: raise ValueError('Headroom exceeded '+sid)
        with sf.SoundFile(wav) as inp, sf.SoundFile(ogg, 'w', samplerate=rate, channels=inp.channels, format='OGG', subtype='VORBIS') as encoded:
            for block in inp.blocks(blocksize=65536,dtype='float32'): encoded.write(block*.3)
        event='devils_segment_'+sid
        sounds[event]={'sounds':[{'name':'destiny_music:devils/'+sid,'stream':True}]}
        segments[sid].update(event=event,seconds=frames/rate,peak=peak)
        report.append(dict(segment=sid,frames=frames,rate=rate,sourcePeak=peak,sha256=hashlib.sha256(ogg.read_bytes()).hexdigest(),txtpSha256=hashlib.sha256(txtp.read_bytes()).hexdigest()))
        wav.unlink()
        print('Rendered',sid,round(frames/rate,3),flush=True)
    if any('event' not in x for x in segments.values()): raise ValueError('Missing segment')
    catalogue={'sections':read('music-state-to-combat.json'),'playlists':read('wwise/playlists.json'),'segments':segments,
      'transitions':[{k:v for k,v in x.items() if k!='raw'} for x in read('wwise/transitions.json') if x['owner_id']==706655015]}
    (resources/'destiny/devils_lair/music.json').write_text(json.dumps(catalogue,indent=2)+'\n')
    sounds_path.write_text(json.dumps(sounds,indent=2)+'\n')
    evidence=a.root/'docs/qa/2026-11-04/devils-lair/music-linkage'; evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'import.json').write_text(json.dumps({'source':str(source),'verifiedFiles':len(hashes),'sourceHashes':hashes,'segments':report,'gain':.3,'tools':'wwiser v20260808; vgmstream r2168; libsndfile Vorbis','limits':'Missing global Wwise bus; active engagement mix. Native crossfade and sample-accurate scheduling require separate acceptance.'},indent=2)+'\n')
    for name in ['media-id-to-wem.json','music-state-to-combat.json','state-to-media.json','transition-to-media.json']:
        (evidence/name).write_bytes((source/name).read_bytes())
if __name__=='__main__': main()
