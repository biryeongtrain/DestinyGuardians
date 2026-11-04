#!/usr/bin/env python3
"""Import selected named combat events; retain full duration and hash source provenance."""
import argparse, csv, hashlib, io, json
from pathlib import Path
import numpy as np
import soundfile as sf

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def generate(source, routes_file):
    routes = json.loads(routes_file.read_text())
    wanted = {n for events in routes['routes'].values() for n in events.values()}
    table = source / 'combat/sound-events.csv'
    names = {}
    for row in csv.DictReader(table.open(encoding='utf-8-sig', newline='')):
        for name in json.loads(row['nameCandidates']):
            if name in wanted:
                if name in names:
                    raise ValueError('Ambiguous named event: ' + name)
                names[name] = row
    if wanted != names.keys():
        raise ValueError('Missing named events: ' + str(wanted - names.keys()))
    hashes = {}
    for line in (source / 'SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines():
        if line.strip():
            sha, name = line.split(maxsplit=1)
            hashes[name.lstrip('*').replace('\\', '/')] = sha.lower()
    output, evidence, sounds = {}, {}, {}
    for name, row in sorted(names.items()):
        variants = []
        for relative in json.loads(row['ogg']):
            if Path(relative).is_absolute() or '..' in Path(relative).parts:
                raise ValueError('Unsafe source path')
            raw = (source / relative).read_bytes()
            if digest(raw) != hashes.get(relative):
                raise ValueError('Source hash mismatch: ' + relative)
            key = Path(relative).stem.lower()
            if key not in evidence:
                samples, rate = sf.read(io.BytesIO(raw), dtype='float32', always_2d=True)
                if not samples.size or not np.isfinite(samples).all():
                    raise ValueError('Invalid decoded samples: ' + relative)
                mono = samples.mean(axis=1)
                if np.max(np.abs(mono)) < .0001:
                    raise ValueError('Silent or phase-cancelled event: ' + relative)
                encoded = io.BytesIO()
                sf.write(encoded, mono, rate, format='OGG', subtype='VORBIS')
                result = encoded.getvalue()
                decoded, decoded_rate = sf.read(io.BytesIO(result))
                if len(decoded) != len(mono) or decoded_rate != rate or decoded.ndim != 1:
                    raise ValueError('Mono duration changed: ' + relative)
                output['assets/destiny_devils_sfx/sounds/' + key + '.ogg'] = result
                evidence[key] = dict(source=relative, sourceSha256=digest(raw), sha256=digest(result),
                                     frames=len(mono), rate=rate, originalChannels=samples.shape[1], channels=1)
            variants.append({'name':'destiny_devils_sfx:' + key, 'attenuation_distance':64})
        if not variants:
            raise ValueError('Empty event: ' + name)
        sounds[name] = {'sounds':variants}
    encode = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
    output['assets/destiny_devils_sfx/sounds.json'] = encode(sounds)
    output['destiny/devils_lair/combat-sound-routes.json'] = encode(routes)
    output['destiny/devils_lair/combat-audio-manifest.json'] = encode(dict(
        source=str(source), tableSha256=digest(table.read_bytes()), events=names, files=evidence,
        routeAudit={kind:{event:dict(sourceEvent=name,
                    sourceOwnerMatch=bool(set(routes['actorSources'][kind]) & set(json.loads(names[name]['owners']))),
                    approximate=not bool(set(routes['actorSources'][kind]) & set(json.loads(names[name]['owners']))))
                    for event,name in events.items()} for kind,events in routes['routes'].items()},
        conversion='full-length channel mean to mono Vorbis for positional playback; no gain or trim',
        audibleAcceptance=False))
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--resources', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    source, resources = args.source.resolve(), args.resources.resolve()
    if source == resources or source in resources.parents:
        raise ValueError('Output may not be inside read-only source')
    outputs = generate(source, Path(__file__).with_name('devils_combat_sound_routes.json'))
    stale = []
    previous = resources / 'destiny/devils_lair/combat-audio-manifest.json'
    if previous.exists():
        for key, evidence in json.loads(previous.read_text())['files'].items():
            relative = 'assets/destiny_devils_sfx/sounds/' + key + '.ogg'
            if relative not in outputs:
                path = resources / relative
                if path.exists() and digest(path.read_bytes()) != evidence['sha256']:
                    raise ValueError('Refusing to remove modified generated audio: '+relative)
                if path.exists(): stale.append(path)
    for relative, raw in outputs.items():
        path = resources / relative
        if args.verify:
            # Ogg encoder stream serials differ; compare decoded audio, not container randomness.
            if path.suffix == '.ogg':
                a, ar = sf.read(path); b, br = sf.read(io.BytesIO(raw))
                if ar != br or not np.array_equal(a,b): raise ValueError('Audio differs: '+relative)
            elif path.name == 'combat-audio-manifest.json':
                actual, expected = json.loads(path.read_bytes()), json.loads(raw)
                for key, evidence in actual['files'].items():
                    audio = resources / ('assets/destiny_devils_sfx/sounds/' + key + '.ogg')
                    if digest(audio.read_bytes()) != evidence['sha256']:
                        raise ValueError('Manifest output hash mismatch: '+key)
                    evidence.pop('sha256')
                for evidence in expected['files'].values(): evidence.pop('sha256')
                if actual != expected: raise ValueError('Manifest differs')
            elif path.read_bytes() != raw:
                raise ValueError('Metadata differs: '+relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    if stale and args.verify: raise ValueError('Obsolete generated audio remains')
    for path in stale: path.unlink()
    print(json.dumps({'files':len(outputs), 'verify':args.verify}))
