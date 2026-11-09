#!/usr/bin/env python3
"""Rebuild W350's one-source-per-action sounds without trimming source duration.

Private original downloads stay outside the repository. Source pins and folder
discovery are reviewed inputs; this script never selects a replacement variant.
"""
from pathlib import Path
import argparse
import array
import hashlib
import json
import math
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art/weapons/w350/audio'
PACK = ROOT / 'src/main/resources/assets/destiny/sounds/w350'
FFMPEG = Path('/Users/qf/IdeaProjects/DestinyGuardians/run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
FFMPEG_SHA256 = '6d175a4743ca50256e89a8cdd731100f9cee33bd79aeea46894d209410dc6617'
RATE = 48000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(command, data=None):
    return subprocess.run(command, input=data, check=True, capture_output=True).stdout


def decode(ffmpeg, path, rate=RATE):
    pcm = run([str(ffmpeg), '-v', 'error', '-i', str(path), '-map', '0:a:0',
               '-ac', '1', '-ar', str(rate), '-f', 'f32le', 'pipe:1'])
    samples = array.array('f', pcm)
    if not samples or any(not math.isfinite(x) for x in samples):
        raise RuntimeError(f'Invalid decoded audio: {path}')
    return samples


def measure(samples, rate=RATE):
    peak = max(map(abs, samples))
    rms = math.sqrt(sum(x*x for x in samples) / len(samples))
    return dict(samples=len(samples), durationSeconds=round(len(samples)/rate, 9),
                peakDbfs=round(20*math.log10(max(peak, 1e-12)), 6),
                rmsDbfs=round(20*math.log10(max(rms, 1e-12)), 6),
                clippedSamples=sum(abs(x) >= 1 for x in samples))


def metadata(ffprobe, source):
    result = json.loads(run([str(ffprobe), '-v', 'error', '-select_streams', 'a:0',
        '-show_entries', 'stream=codec_name,sample_rate,channels,duration',
        '-of', 'json', str(source)]))['streams'][0]
    return dict(codec=result['codec_name'], sampleRate=int(result['sample_rate']),
                channels=int(result['channels']), containerDurationSeconds=float(result['duration']))


def timed_reload(ffmpeg, ffprobe, base, ticks):
    """Consume the full original through atempo, then add only short silence.

    Adjust the tempo factor around FFmpeg's window rounding until the complete
    result fits the tick deadline. Never remove processed source samples.
    """
    source = decode(ffmpeg, Path(base['sourcePath']))
    source = array.array('f', (x*10**(base['gainDb']/20) for x in source))
    target = ticks * (RATE//20)
    factor = len(source)/target
    for _ in range(12):
        if not .5 <= factor <= 2:
            raise RuntimeError('Reload tempo outside supported 0.5..2 range')
        data = run([str(ffmpeg), '-v', 'error', '-f', 'f32le', '-ar', str(RATE),
            '-ac', '1', '-i', 'pipe:0', '-af', f'atempo={factor:.12f}',
            '-f', 'f32le', 'pipe:1'], source.tobytes())
        stretched = array.array('f', data)
        difference = target-len(stretched)
        if 0 <= difference <= 1024:
            break
        factor *= (len(stretched)/target) * (1.001 if difference < 0 else 1.0)
    else:
        raise RuntimeError('Unable to fit full reload without trimming')
    stretched.extend([0.0]*difference)
    asset = PACK/'reload'/f'{base["weapon"]}_{ticks}.ogg'
    asset.parent.mkdir(parents=True, exist_ok=True)
    command = [str(ffmpeg), '-v', 'error', '-y', '-f', 'f32le', '-ar', str(RATE),
        '-ac', '1', '-i', 'pipe:0', '-map_metadata', '-1', '-c:a', 'libvorbis',
        '-q:a', '4', '-fflags', '+bitexact', '-flags:a', '+bitexact', str(asset)]
    correction = 0.0
    for _ in range(3):
        run(command, stretched.tobytes())
        post = measure(decode(ffmpeg, asset))
        if post['peakDbfs'] <= -1 and post['clippedSamples'] == 0:
            break
        amount = -3-post['peakDbfs']
        stretched = array.array('f', (x*10**(amount/20) for x in stretched))
        correction += amount
    else:
        raise RuntimeError('Timed Vorbis headroom check failed')
    meta = metadata(ffprobe, asset)
    if abs(meta['containerDurationSeconds']-ticks/20) > 1/RATE or abs(post['samples']-target)>1024:
        raise RuntimeError('Timed reload duration mismatch')
    event = f'weapon.reload_w350.{base["weapon"]}_{ticks}'
    resource = f'destiny:w350/reload/{base["weapon"]}_{ticks}'
    profile = dict(id=base['weapon'], ticks=ticks, event=event,
        sourceEvent=base['event'], sourceSha256=base['outputSha256'],
        asset=str(asset.relative_to(ROOT/'src/main/resources')))
    record = dict(profile, resource=resource, assetPath=str(asset.relative_to(ROOT)),
        sourceOriginalSha256=base['sourceSha256'],
        sourceDurationSeconds=len(source)/RATE, targetDurationSeconds=ticks/20,
        atempo=factor, pitchPolicy='ffmpeg atempo; no sample-rate pitch shift',
        sourceTrimSamples=0, processedTrimSamples=0, paddedSilenceSamples=difference,
        outputSha256=sha(asset.read_bytes()), outputBytes=asset.stat().st_size,
        outputMetadata=meta, outputDecodedMono=post, postTempoGainDb=correction)
    return profile, record


def build(ffmpeg, ffprobe):
    if sha(ffmpeg.read_bytes()) != FFMPEG_SHA256:
        raise RuntimeError('FFmpeg binary changed; review before updating its pin')
    pins = json.loads((ART / 'source-pins.json').read_text())
    discovery = json.loads((ART / 'folder-discovery.json').read_text())
    config = ART/'reload-base-ticks.json'
    reload_ticks = json.loads(config.read_text()) if config.exists() else {}
    folder_map = {f['weapon']: f for f in discovery}
    seen = set()
    records = []
    events = {}
    for pin in pins:
        key = (pin['weapon'], pin['action'])
        if key in seen:
            raise RuntimeError(f'Multiple variants for action {key}')
        seen.add(key)
        folder = folder_map[pin['weapon']]
        listed = next(f for f in folder['files'] if f['id'] == pin['id'])
        if (listed['originalName'] != pin['originalName'] or folder['folderId'] != pin['folderId']):
            raise RuntimeError('Source label/folder drift')
        source = Path(pin['sourcePath'])
        if source.stat().st_size != pin['bytes'] or sha(source.read_bytes()) != pin['sourceSha256']:
            raise RuntimeError(f'Source pin mismatch: {source}')
        original_meta = metadata(ffprobe, source)
        original_native = decode(ffmpeg, source, original_meta['sampleRate'])
        original = decode(ffmpeg, source)
        pre = measure(original)
        if pre['rmsDbfs'] < -90:
            raise RuntimeError(f'Silent source: {source}')
        # Same conservative RMS/peak targets as W33. No trim, fade, loop,
        # concatenation, duration cap, pitch shift, or time stretching.
        gain = min(12.0, -21.0-pre['rmsDbfs'], -6.0-pre['peakDbfs'])
        samples = array.array('f', (x*10**(gain/20) for x in original))
        asset = PACK / pin['weapon'] / (pin['action'] + '.ogg')
        if pin['action']=='reload' and pin['weapon'] in reload_ticks:
            asset = Path('/tmp/exotic-expansion-20261109/audio-full-duration')/pin['weapon']/'reload.ogg'
        asset.parent.mkdir(parents=True, exist_ok=True)
        command = [str(ffmpeg), '-hide_banner', '-v', 'error', '-y',
            '-f', 'f32le', '-ar', str(RATE), '-ac', '1', '-i', 'pipe:0',
            '-map_metadata', '-1', '-c:a', 'libvorbis', '-q:a', '4',
            '-fflags', '+bitexact', '-flags:a', '+bitexact', str(asset)]
        for attempt in range(3):
            run(command, samples.tobytes())
            decoded = decode(ffmpeg, asset)
            post = measure(decoded)
            if post['peakDbfs'] <= -1 and post['clippedSamples'] == 0:
                break
            correction = -3-post['peakDbfs']
            samples = array.array('f', (x*10**(correction/20) for x in samples))
            gain += correction
        else:
            raise RuntimeError('Decoded Vorbis headroom check failed')
        data = asset.read_bytes()
        pos = data.index(b'\x01vorbis')
        channels = data[pos+11]
        rate = struct.unpack_from('<I', data, pos+12)[0]
        if channels != 1 or rate != RATE:
            raise RuntimeError('Unexpected Vorbis channel/rate')
        output_meta = metadata(ffprobe, asset)
        # Vorbis block priming/padding can change FFmpeg's raw PCM sample
        # count even when the final granule preserves the full duration.
        # Record that decoder difference explicitly instead of trimming/padding.
        if abs(len(decoded)-len(original)) > 1024 or abs(output_meta['containerDurationSeconds']-pre['durationSeconds']) > 1/RATE:
            raise RuntimeError(f'Full-duration sample count mismatch: {asset}')
        event = 'weapon.' + '.'.join(key)
        resource = f'destiny:w350/{pin["weapon"]}/{pin["action"]}'
        events[event] = {'sounds': [{'name': resource, 'stream': False}]}
        records.append(dict(pin, event=event, resource=resource,
            assetPath=str(asset.relative_to(ROOT)) if asset.is_relative_to(ROOT) else None,
            unpackedReferencePath=str(asset) if not asset.is_relative_to(ROOT) else None,
            outputSha256=sha(data),
            outputBytes=len(data), sourceMetadata=original_meta, outputMetadata=output_meta,
            sourceDecodedMono=measure(original_native, original_meta['sampleRate']),
            resampledSourceMono=pre, outputDecodedMono=post,
            outputSampleRate=rate, outputChannels=channels,
            gainDb=round(gain, 9), trimSeconds=0, timeScale=1,
            fullContainerDurationPreserved=True, decodedSampleDelta=len(decoded)-len(original),
            limitation='Uploader action label only; independent listening and in-game timing/loudness not verified. Pulse Fire may contain a native burst; Jotunn Fire may contain charge/discharge.'))
    aliases = json.loads((ART / 'action-aliases.json').read_text())
    for alias in aliases:
        key = (alias['weapon'], alias['action'])
        if key in seen:
            raise RuntimeError('Alias must not replace a selected exact action')
        original = next(r for r in records if (r['weapon'], r['action']) == (alias['weapon'], alias['reuseAction']))
        event = 'weapon.' + '.'.join(key)
        events[event] = {'sounds': [{'name': original['resource'], 'stream': False}]}
        records.append(dict(original, **{k:v for k,v in alias.items() if k not in original},
            action=alias['action'], event=event, selectionReason=alias['reason'],
            identityConfidence='Known named draw/switch-in recording; its ADS use is an explicit approximation.'))
        seen.add(key)
    absent = [{'weapon': f['weapon'], 'action': action,
        'reason': 'No uploader-labeled action exists in the supplied folder; opaque ripped filenames have not been acoustically identified.'}
        for f in discovery for action in ('equip', 'ads', 'reload', 'fire') if (f['weapon'], action) not in seen]
    timed = []
    profiles = []
    if reload_ticks:
        for weapon, ticks in reload_ticks.items():
            base = next(r for r in records if r['weapon']==weapon and r['action']=='reload')
            profile, timed_record = timed_reload(ffmpeg, ffprobe, base, ticks)
            profiles.append(profile)
            timed.append(timed_record)
            sounds = {'sounds': [{'name': timed_record['resource'], 'stream': False}]}
            events[base['event']] = sounds
            old_asset = PACK/weapon/'reload.ogg'
            if old_asset.exists():
                if sha(old_asset.read_bytes())!=base['outputSha256']:
                    raise RuntimeError('Refusing to remove drifted redundant reload reference')
                old_asset.unlink()
            full_reference = {key:base[key] for key in (
                'unpackedReferencePath', 'outputSha256', 'outputBytes',
                'outputMetadata', 'outputDecodedMono', 'fullContainerDurationPreserved', 'decodedSampleDelta')}
            base.update(fullDurationReference=full_reference,
                resource=timed_record['resource'], assetPath=timed_record['assetPath'],
                outputSha256=timed_record['outputSha256'], outputBytes=timed_record['outputBytes'],
                outputMetadata=timed_record['outputMetadata'], outputDecodedMono=timed_record['outputDecodedMono'],
                timeScale=timed_record['atempo'], fullContainerDurationPreserved=False,
                decodedSampleDelta=timed_record['outputDecodedMono']['samples']-ticks*(RATE//20),
                durationStatus='Full source consumed through atempo; exact base-tick duration with only short silence padding; no source/processed trim.')
            events[profile['event']] = sounds
            for channel in range(32):
                events[profile['event']+f'.direct_{channel}'] = sounds
    dump(ART / 'sounds-json-snippet.json', events)
    dump(ART / 'reload-profile-snippet.json', profiles)
    dump(ART / 'manifest.json', dict(schemaVersion=1, ffmpegSha256=FFMPEG_SHA256,
        conversion='Full-source mono 48000 Hz Vorbis quality 4; conservative per-clip gain; one variant/action. Reload consumes entire source through pitch-preserving atempo to master-specified base ticks; unretimed reference stays outside pack.',
        records=records, timedReloads=timed, missingActions=absent,
        listeningVerified=False, inGameVerified=False))
    return records, absent


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, default=FFMPEG)
    parser.add_argument('--ffprobe', type=Path, default=Path('/opt/homebrew/bin/ffprobe'))
    args = parser.parse_args()
    records, absent = build(args.ffmpeg, args.ffprobe)
    print(json.dumps(dict(actions=len(records), uniqueOggFiles=len(list(PACK.rglob('*.ogg'))),
        bytes=sum(p.stat().st_size for p in PACK.rglob('*.ogg')), missingActions=absent)))
