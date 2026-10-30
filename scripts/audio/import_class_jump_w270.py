#!/usr/bin/env python3
"""W270 bounded, deterministic audio import. Python stdlib + FFmpeg/libvorbis.

Only writes the 11 selected OGGs, root sounds-fragment.json and audio-import.json.
Requires an explicit isolated output root; never edits a sounds.json registry.
BNK inspection is a deliberately partial v150 structural parser, not a Wwise player.
"""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys

SOURCE = Path('/Volumes/qf-ssd/Destiny-Class-Jump-Sounds-2026-10-30')
MAIN = Path('/Users/qf/IdeaProjects/DestinyGuardians')
AUDIO = Path('src/main/resources/assets/destiny/sounds/class_jump_w270')
REPORT = Path('docs/qa/2026-10-30/w270/audio-import.json')
RATE = 48000
CEILING = 10 ** (-3 / 20)
TARGET = 10 ** (-4 / 20)
# One explicitly bank-listed representative per classified event. No arbitrary
# randomization of WEM lists, no reconstructed layering, no inferred loop export.
SELECTION = [
    ('class.hunter.dodge.gambler', '80D4AD51', '80D66B88', 'Accepted gambler dodge activation; once at the motion start.'),
    ('class.hunter.dodge.marksman', '80D4AD57', '80D665BA', 'Accepted marksman dodge activation; once at the motion start.'),
    ('class.warlock.rift.precast', '80D4AD6C', '80D665A0', 'Accepted rift cast start; once, before field creation.'),
    ('class.warlock.rift.healing', '80D4AD6F', '80D665A3', 'Actual healing field creation; once at field position.'),
    ('class.warlock.rift.empowering', '80D4AD75', '80D66BAB', 'Actual empowering field creation; once at field position.'),
    ('class.warlock.rift.end', '80D495ED', '80D665A6', 'Actual field removal/expiry; once at field position, only if a field existed.'),
    ('jump.hunter', '80D4B2F8', '80D64F18', 'Each accepted airborne extra jump; not the grounded vanilla takeoff.'),
    ('jump.blink.out', '80D4B307', '80D64F24', 'Successful blink departure; once at the departure position.'),
    ('jump.blink.in', '80D4B30A', '80D64F27', 'Successful blink arrival; once at the arrival position.'),
    ('jump.warlock.glide', '80D4B296', '80D64D68', 'Glide inactive-to-active transition; entity-attached, finite once; stop owner slot on exit.'),
    ('jump.titan.lift', '80D4B4C1', '80D650F3', 'Lift inactive-to-active transition; entity-attached, finite once; stop owner slot on exit.'),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def u32(data, offset=0):
    return struct.unpack_from('<I', data, offset)[0]


def hx(value):
    return f'{value:08X}'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect_bank(data):
    """Parse chunk/object boundaries and validated RanSeq tails only.

    Footer layout checked against wwiser/parser/wparser.py v150 branches:
    CAkRanSeqCntr__SetInitialValues, SetPlaylistWithoutCheck and LoadSource.
    We do not byte-scan arbitrary IDs and call those matches resolved call paths.
    """
    chunks, objects, offset = {}, {}, 0
    while offset < len(data):
        require(offset + 8 <= len(data), 'Truncated BNK chunk')
        name, size = data[offset:offset + 4], u32(data, offset + 4)
        require(offset + 8 + size <= len(data), 'Invalid BNK chunk size')
        require(name not in chunks, 'Duplicate BNK chunk')
        chunks[name] = data[offset + 8:offset + 8 + size]
        offset += 8 + size
    require(u32(chunks[b'BKHD']) == 150, 'Only inspected Wwise v150 is supported')
    hirc, offset = chunks[b'HIRC'], 4
    for _ in range(u32(hirc)):
        kind, size = hirc[offset], u32(hirc, offset + 1)
        body = hirc[offset + 5:offset + 5 + size]
        require(len(body) == size and size >= 4, 'Truncated HIRC object')
        oid = u32(body)
        require(oid not in objects, 'Duplicate HIRC object ID')
        objects[oid] = (kind, body)
        offset += 5 + size
    require(offset == len(hirc), 'HIRC trailing bytes')
    nodes = []
    for oid, (kind, body) in objects.items():
        row = {'id': hx(oid), 'type': kind, 'bytes': len(body)}
        if kind == 2:
            require(u32(body, 4) == 0x00140001, 'Unexpected source plugin layout')
            row.update(source_id=hx(u32(body, 9)), stream_type=body[8],
                       in_memory_media_bytes=u32(body, 13))
        elif kind == 3:
            row.update(action_type=f'{struct.unpack_from("<H", body, 4)[0]:04X}',
                       target_id=hx(u32(body, 6)), raw_hex=body.hex())
        elif kind == 4:
            count = body[4]
            require(count < 128 and len(body) == 5 + 4 * count, 'Unsupported event action list')
            row['actions'] = [hx(u32(body, 5 + 4 * i)) for i in range(count)]
        elif kind == 5:
            candidates = []
            for p in range(24, len(body) - 5):
                count = u32(body, p)
                if not 0 < count < 64 or p + 6 + 12 * count != len(body):
                    continue
                children = [u32(body, p + 4 + 4 * i) for i in range(count)]
                q = p + 4 + 4 * count
                if any(child not in objects for child in children):
                    continue
                if struct.unpack_from('<H', body, q)[0] != count:
                    continue
                playlist = [(u32(body, q + 2 + 8 * i), u32(body, q + 6 + 8 * i)) for i in range(count)]
                if sorted(children) != sorted(x[0] for x in playlist):
                    continue
                loop, lo, hi, transition, tlo, thi, avoid, tm, rm, mode, bits = struct.unpack_from('<HHHfffHBBBB', body, p - 24)
                require(mode in (0, 1) and tm <= 5 and rm <= 1, 'Unsupported RanSeq footer')
                candidates.append(dict(loop_count=loop, loop_mod_min=lo, loop_mod_max=hi,
                    transition_time_ms=transition, transition_min_ms=tlo, transition_max_ms=thi,
                    avoid_repeat=avoid, transition_mode=tm, random_mode=rm,
                    mode='random' if mode == 0 else 'sequence', continuous=bool(bits & 8),
                    flags=bits, children=[hx(c) for c in children],
                    playlist=[{'id': hx(c), 'weight': w} for c, w in playlist]))
            require(len(candidates) == 1, f'Ambiguous RanSeq tail: {hx(oid)}')
            row.update(candidates[0])
        nodes.append(row)
    return {'version': 150, 'object_count': len(objects), 'nodes': nodes,
            'scope': 'Structural partial parse; switch/RTPC routing, source-ID-to-WEM-tag binding and gameplay synchronization unresolved.'}


def run_ffmpeg(ffmpeg, args, data=None):
    p = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin',
                        '-xerror', '-threads', '1', *args], input=data, capture_output=True)
    if p.returncode or p.stderr:
        raise RuntimeError(f'FFmpeg failed/warned ({p.returncode}): {p.stderr.decode(errors="replace")}')
    return p.stdout


def floats(data):
    values = array.array('f')
    values.frombytes(data)
    if sys.byteorder != 'little':
        values.byteswap()
    require(values and all(math.isfinite(x) for x in values), 'Empty/nonfinite decoded PCM')
    return values


def pcm_stats(data):
    values = floats(data)
    peak = max(abs(x) for x in values)
    audible = [i for i, x in enumerate(values) if abs(x) >= 0.001]  # -60 dBFS sample threshold, not perceptual onset
    return {'samples': len(values), 'duration_seconds': len(values) / RATE,
            'peak_linear': peak, 'peak_dbfs': 20 * math.log10(peak) if peak else None,
            'first_sample_above_minus60_dbfs_seconds': audible[0] / RATE if audible else None,
            'last_sample_above_minus60_dbfs_seconds': audible[-1] / RATE if audible else None}


def encode(ffmpeg, pcm, gain):
    return run_ffmpeg(ffmpeg, ['-fflags', '+bitexact', '-f', 'f32le', '-ar', str(RATE),
        '-ac', '1', '-i', 'pipe:0', '-map_metadata', '-1', '-af', f'volume={gain:.12f}',
        '-c:a', 'libvorbis', '-q:a', '4', '-flags:a', '+bitexact', '-fflags', '+bitexact',
        '-f', 'ogg', 'pipe:1'], pcm)


def output_path(root, relative):
    path = root / relative
    require(path.resolve().is_relative_to(root), f'Output symlink escapes root: {path}')
    return path


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=SOURCE)
    ap.add_argument('--output-root', type=Path, required=True)
    ap.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    args = ap.parse_args()
    require(args.ffmpeg, 'Pass --ffmpeg /path/to/ffmpeg (libvorbis required)')
    ffmpeg = str(Path(args.ffmpeg).resolve())
    source, root = args.source.resolve(), args.output_root.resolve()
    require(not root.is_relative_to(source) and not source.is_relative_to(root), 'Source/output roots must be disjoint')
    require(not root.is_relative_to(MAIN.resolve()), 'Refusing writes in main checkout')
    source_paths = sorted(p for p in source.rglob('*') if p.is_file())
    before = {p.relative_to(source).as_posix(): digest(p.read_bytes()) for p in source_paths}
    expected = read_json(source / 'FILE-HASHES.json')['files']
    for item in expected:
        require(before.get(item['path']) == item['sha256'], f'Source manifest mismatch: {item["path"]}')
    cues = {c['sound']: c for c in read_json(source / 'CUES.json')}
    conversion = {c['tag']: c for c in read_json(source / 'audio-conversion.json')}
    loops = {c['tag']: c for c in read_json(source / 'audio-loop-metadata.json')}
    fragment, assets, banks = {}, [], {}
    provenance_names = ['FILE-HASHES.json', 'CUES.json', 'audio-conversion.json',
        'audio-loop-metadata.json', 'audio-sequence-timing.json', 'audio-selected-banks.json',
        'provenance/toolchain.json', 'provenance/selected-source-path-bindings.json']
    for key, sound, tag, trigger in SELECTION:
        cue, original = cues[sound], conversion[tag]
        require(not cue['candidate'] and tag in cue['wems'], f'Unclassified source: {tag}')
        require(loops[tag]['error'] is None and not loops[tag]['loopLines'], f'Unexpected file loop/error: {tag}')
        ogg = source / original['file']
        raw_name = f'audio/raw/{tag}.wem'
        require(before[original['file']] == original['sha256'], 'OGG conversion provenance mismatch')
        require(before[raw_name] == original['rawSha256'], 'Raw WEM provenance mismatch')
        require(original['channels'] == 2 and original['sampleRate'] == RATE, 'Unexpected source format')
        pcm = run_ffmpeg(ffmpeg, ['-i', str(ogg), '-map', '0:a:0', '-af', 'pan=mono|c0=0.5*c0+0.5*c1',
                                  '-ar', str(RATE), '-f', 'f32le', 'pipe:1'])
        src_stats = pcm_stats(pcm)
        require(abs(src_stats['duration_seconds'] - original['duration']) < 0.02, 'Source duration drift')
        gain = min(1.0, TARGET / src_stats['peak_linear'])
        for _ in range(4):
            encoded = encode(ffmpeg, pcm, gain)
            decoded = run_ffmpeg(ffmpeg, ['-i', 'pipe:0', '-map', '0:a:0', '-f', 'f32le', 'pipe:1'], encoded)
            stats = pcm_stats(decoded)
            if stats['peak_linear'] <= CEILING:
                break
            gain *= TARGET / stats['peak_linear']
        require(stats['peak_linear'] <= CEILING, 'Vorbis decoded peak exceeds -3 dBFS')
        ident = encoded.find(b'\x01vorbis')
        require(ident >= 0 and encoded[ident + 11] == 1 and u32(encoded, ident + 12) == RATE, 'Output not mono 48 kHz Vorbis')
        require(abs(stats['samples'] - src_stats['samples']) <= 128, 'Encoded duration changed unexpectedly')
        require(encode(ffmpeg, pcm, gain) == encoded, 'Bitwise reproducibility failed')
        relative = AUDIO / (key.replace('.', '_') + '.ogg')
        destination = output_path(root, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encoded)
        require(digest(destination.read_bytes()) == digest(encoded), 'Output write mismatch')
        # Decode the persisted file all the way to EOF as well as the in-memory encode.
        persisted_pcm = run_ffmpeg(ffmpeg, ['-i', str(destination), '-map', '0:a:0', '-f', 'f32le', 'pipe:1'])
        require(persisted_pcm == decoded, 'Persisted output decode mismatch')
        resource = f'destiny:class_jump_w270/{relative.stem}'
        fragment[key] = {'replace': False, 'sounds': [{'name': resource, 'stream': False}]}
        bank_name, sound_name = f'audio/raw/{cue["bank"]}.bnk', f'audio/raw/{sound}.sound.bin'
        if cue['bank'] not in banks:
            banks[cue['bank']] = {'path': bank_name, 'sha256': before[bank_name], **inspect_bank((source / bank_name).read_bytes())}
        movement = key in ('jump.warlock.glide', 'jump.titan.lift')
        assets.append({'event': key, 'output': relative.relative_to('src/main/resources').as_posix(),
            'path': relative.as_posix(), 'resource': resource,
            'bytes': len(encoded), 'sha256': digest(encoded), 'codec': 'vorbis', 'channels': 1, 'sample_rate': RATE,
            'source_ogg': original['file'], 'source_ogg_sha256': before[original['file']],
            'source_wem': raw_name, 'source_wem_sha256': before[raw_name],
            'source_sound': sound_name, 'source_sound_sha256': before[sound_name],
            'source_bank': bank_name, 'source_bank_sha256': before[bank_name],
            'source_tag': tag, 'sequence_timings': cue['sequenceTimings'], 'name_evidence': cue['nameEvidence'],
            'source_pcm_after_downmix': src_stats, 'output_pcm': stats, 'gain': gain,
            'playback': {'trigger': trigger, 'repeat': False, 'loop': False, 'pitch': 1.0,
                         'offset_from_semantic_event_seconds': 0, 'offset_is_port_recommendation': True},
            'classification': 'bank-listed representative; name/sequence classified; not gameplay verified',
            'approximation': ('Start/end WEM phase unresolved; finite representative only; no sustain.' if movement else
                              'Single representative; original random/switch/layer selection not reconstructed.'),
            'checks': {'full_source_decode': True, 'full_output_decode': True, 'persisted_decode': True,
                       'bitwise_reencode': True, 'peak_bounded': True}})
    total = sum(a['bytes'] for a in assets)
    require(total < 1024 * 1024, 'Compact asset budget exceeded (1 MiB)')
    fragment_path = output_path(root, Path('sounds-fragment.json'))
    save_json(fragment_path, fragment)
    after = {p.relative_to(source).as_posix(): digest(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    require(before == after, 'Source changed during import')
    report = {'schema': 1, 'task': 'W270', 'source_root': str(source),
        'source_toolchain': read_json(source / 'provenance/toolchain.json'),
        'ffmpeg': {'version': subprocess.check_output([ffmpeg, '-version'], text=True).splitlines()[0],
                   'binary_sha256': digest(Path(ffmpeg).read_bytes())},
        'processing': {'downmix': '0.5*L + 0.5*R', 'sample_rate': RATE, 'vorbis_quality': 4,
            'peak_ceiling_dbfs': -3, 'target_dbfs': -4, 'never_boost': True, 'trim': False,
            'resample': False, 'limiter': False, 'reproducibility': 'Every output re-encoded byte-identically with recorded FFmpeg binary.'},
        'source_integrity': {'manifest_files_verified': len(expected), 'files_hashed_before_and_after': len(before),
                             'unchanged': True, 'metadata_hashes': {n: before[n] for n in provenance_names}},
        'fragment': {'path': 'sounds-fragment.json', 'sha256': digest(fragment_path.read_bytes()),
                     'keys': list(fragment), 'merge': 'Add keys under destiny namespace after collision check; do not replace registry.'},
        'summary': {'assets': len(assets), 'events': len(fragment), 'total_ogg_bytes': total,
                    'peak_max_dbfs': max(a['output_pcm']['peak_dbfs'] for a in assets)},
        'entries': assets, 'banks': banks,
        'excluded': ['uncertain barricade', 'thruster', 'Phoenix Dive', 'unused acrobat',
                     'candidate banks', 'unresolved sustain', 'owner-slot aliases'],
        'limits': ['No client/server/build/listening/gameplay validation.',
                   'Sequence start=0 is local; no exact input-to-event or FBX synchronization is established.',
                   'Source WEM is Opus; supplied canonical OGG is already a lossy conversion. Mono Vorbis is an additional encode.',
                   'Sample peak bound is measured after Vorbis decode; it is not a true-peak or loudness certification.',
                   'Partial BNK parser cannot bind media IDs to package WEM tags or reproduce switches/RTPC gains.']}
    save_json(output_path(root, REPORT), report)
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
