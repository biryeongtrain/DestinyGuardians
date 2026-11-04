#!/usr/bin/env python3
"""Corroborate Wwise media candidates with exact WEM packet-prefix lengths.

This recovers structural constraints, not encounter labels or an authenticated ID table.
Downloads inputs are read-only. Reuses the checksum-validating bank audit.
"""
import argparse, gzip, hashlib, json, struct, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from audit_devils_music_bank import audit


def wem_prefix(data, packets=20):
    if len(data)<12 or data[:4]!=b'RIFF' or data[8:12]!=b'WAVE':
        raise ValueError('Expected RIFF WAVE')
    if struct.unpack_from('<I',data,4)[0]+8!=len(data):
        raise ValueError('RIFF size mismatch')
    chunks={};pos=12
    while pos+8<=len(data):
        tag=data[pos:pos+4];size=struct.unpack_from('<I',data,pos+4)[0];start=pos+8
        if start+size>len(data) or tag in chunks:raise ValueError('Invalid or duplicate RIFF chunk')
        chunks[tag]=(start,size);pos=start+size+(size&1)
    if pos not in (len(data),len(data)+1):raise ValueError('Trailing partial RIFF chunk')
    fmt,fmt_size=chunks[b'fmt '];seek,seek_size=chunks[b'seek'];payload,payload_size=chunks[b'data']
    if fmt_size<2 or struct.unpack_from('<H',data,fmt)[0]!=0x3041:
        raise ValueError('Expected Wwise Opus WEM codec 0x3041')
    if seek_size%2:raise ValueError('Odd-sized Opus packet table')
    sizes=struct.unpack_from('<'+'H'*(seek_size//2),data,seek)
    if len(sizes)<packets or sum(sizes)!=payload_size:
        raise ValueError('Opus packet table does not cover the data chunk')
    prefix=payload+sum(sizes[:packets])
    return dict(dataOffset=payload,packetCount=len(sizes),packetPrefixCount=packets,
                packetPrefixBytes=prefix,packetPrefixSha256=hashlib.sha256(data[:prefix]).hexdigest())


def build(source,xml_bytes,previous):
    if hashlib.sha256(xml_bytes).hexdigest()!=previous['xmlSha256']:
        raise ValueError('XML differs from the recorded bank audit')
    with tempfile.TemporaryDirectory(prefix='devils-bank-audit-') as tmp:
        path=Path(tmp)/'bank.xml';path.write_bytes(xml_bytes);report=audit(source,path)
    root=ET.fromstring(xml_bytes);sizes={}
    for obj in root.findall('.//object[@name="AkMediaInformation"]'):
        values={n.get('name'):n.get('value') for n in obj.findall('field')}
        sid=values['sourceID'];size=int(values['uInMemoryMediaSize'])
        if sid in sizes and sizes[sid]!=size:raise ValueError('Inconsistent media prefetch size')
        sizes[sid]=size
    inventory={}
    for row in report['sourceInventory']:
        name=row['wem'];inventory[name]=wem_prefix((source/'audio_raw/music'/(name+'.wem')).read_bytes())
    media={}
    for sid,row in report['media'].items():
        candidates=[name for name in row['durationCandidates'] if inventory[name]['packetPrefixBytes']==sizes[sid]]
        if not candidates:raise ValueError('No duration/20-packet match for '+sid)
        media[sid]=dict(durationSeconds=row['durationSeconds'],bankInMemoryBytes=sizes[sid],
                       durationCandidates=row['durationCandidates'],structuralCandidates=candidates,
                       uniqueStructuralCandidate=len(candidates)==1,mappingAuthenticated=False)
    return dict(bankSha256=report['bankSha256'],xmlSha256=report['xmlSha256'],
                method='duration within one sample AND WEM header plus first 20 packet sizes equals uInMemoryMediaSize',
                packetCountRule='20 is an observed invariant across all 40 media references, not an independently supplied ID table',
                uniqueStructuralCandidates=sum(r['uniqueStructuralCandidate'] for r in media.values()),
                unresolvedMediaIds=[sid for sid,r in media.items() if not r['uniqueStructuralCandidate']],
                media=media,wemPackets=inventory,
                limitations=['Prefix byte COUNT is corroboration, not a media-ID table or hash supplied by the bank.',
                             'Encounter/state names remain unknown. No runtime cue assignment is made.',
                             'Equal candidates remain unresolved; never choose by filename order.',
                             'No listening, loop-seam or native playback acceptance.'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--xml-gz',type=Path,required=True);ap.add_argument('--bank-report',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    report=build(args.source,gzip.decompress(args.xml_gz.read_bytes()),json.loads(args.bank_report.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['uniqueStructuralCandidates','unresolvedMediaIds']}))


if __name__=='__main__':main()
