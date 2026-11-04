#!/usr/bin/env python3
"""Audit a copied Wwise XML dump against delivered music; never infer encounter names.

Generate XML with pinned wwiser on a COPY of audio_banks/80D52522.bnk.
Duration matches below are candidates, not a recovered Wwise media-ID mapping.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def fields(node):
    return {f.attrib['name']: f.attrib.get('value') for f in node.findall('field')}


def audit(source, dump):
    expected = {name.replace('\\', '/'): digest for digest, name in
                (line.split(None, 1) for line in (source/'SHA256SUMS.txt').read_text().splitlines())}
    def verify(name):
        data = (source/name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if expected.get(name) != digest:
            raise ValueError('Source drift: '+name)
        return data, digest
    _, bank_hash = verify('audio_banks/80D52522.bnk')
    validation, _ = verify('audio/voice-music-validation.json')
    inventory = [x for x in json.loads(validation) if x['file'].startswith('audio/music/')]
    for row in inventory:
        _, row['oggSha256'] = verify(row['file'])
        _, row['wemSha256'] = verify('audio_raw/music/'+row['wem']+'.wem')
    root = ET.parse(dump).getroot()
    if root.attrib.get('version') != '150' or root.attrib.get('filename') != '80D52522.bnk':
        raise ValueError('Unexpected bank dump')
    objects = root.findall('./object[@name="HircChunk"]/list/object')
    tracks, segments, switches, playlists = [], [], [], []
    media = {}
    for obj in objects:
        base = fields(obj)
        row = {'id': int(base['ulID']), 'index': int(obj.attrib['index'])}
        kind = obj.attrib['name']
        if kind == 'CAkMusicTrack':
            row['clips'] = []
            for node in obj.findall('.//object[@name="AkTrackSrcInfo"]'):
                clip = fields(node)
                sid = clip['sourceID']; duration = float(clip['fSrcDuration']) / 1000
                candidates = [x for x in inventory if abs(x['frames']/x['rate']-duration) <= 1/x['rate']+1e-6]
                media[sid] = {'durationSeconds': duration, 'durationCandidates': [x['wem'] for x in candidates],
                              'mappingConfirmed': False}
                row['clips'].append(clip)
            row['automation'] = [ET.tostring(n, encoding='unicode') for n in obj.findall('.//object[@name="AkClipAutomation"]')]
            tracks.append(row)
        elif kind == 'CAkMusicSegment':
            row['durationMs'] = float(obj.find('.//field[@name="fDuration"]').attrib['value'])
            row['tracks'] = [int(n.attrib['value']) for n in obj.findall('.//field[@name="ulChildID"]')]
            row['markers'] = [fields(n) for n in obj.findall('.//object[@name="AkMusicMarkerWwise"]')]
            segments.append(row)
        elif kind == 'CAkMusicSwitchCntr':
            row['groups'] = [fields(n) for n in obj.findall('.//object[@name="AkGameSync"]')]
            row['routes'] = [fields(n) for n in obj.findall('.//object[@name="Node"]') if n.find('field[@name="audioNodeId"]') is not None]
            switches.append(row)
        elif kind == 'CAkMusicRanSeqCntr':
            # Retain nested order and loop semantics; a flat child list loses sequence meaning.
            row['structureXml'] = ET.tostring(obj, encoding='unicode')
            playlists.append(row)
    if len(objects) != 133 or len(tracks) != 68 or len(segments) != 49 or len(media) != 40:
        raise ValueError('Bank structure changed; inspect before using the report')
    return {'bankSha256': bank_hash, 'xmlSha256': hashlib.sha256(dump.read_bytes()).hexdigest(),
            'wwiserCommit': '08e937b649bc7007c234bbd59e34a41d5eef3b38',
            'limitations': ['Dump must be generated from the checksum-verified bank copy.',
                           'No encounter labels recovered; state number order is not gameplay order.',
                           'Duration candidates do not prove media IDs, even if unique.',
                           'wwiser reports a missing bus and multitracks; generated TXTP is diagnostic only.',
                           'No listening, client playback or loop-seam acceptance.'],
            'tracks': tracks, 'segments': segments, 'switches': switches, 'playlists': playlists,
            'media': media, 'sourceInventory': inventory}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--xml', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    report = audit(a.source, a.xml)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'tracks': len(report['tracks']), 'segments': len(report['segments']),
                      'media': len(report['media']),
                      'uniqueDurationCandidates': sum(len(x['durationCandidates']) == 1 for x in report['media'].values())}))


if __name__ == '__main__':
    main()
