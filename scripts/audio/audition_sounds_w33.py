#!/usr/bin/env python3
"""Build a local W33 audition bundle from SHA256-pinned candidate metadata."""
import array
import html
import json
import subprocess
from import_sounds_w33 import ROOT, QA, RATE, download, decode, stats, ffmpeg_path, dump

def main():
    data = json.loads((QA / 'super-candidates.json').read_text())
    ffmpeg = ffmpeg_path(None)
    cards = []
    for row in data['candidates']:
        source = download(row, False)
        samples = decode(ffmpeg, source)
        measure = stats(samples)
        gain = min(12, -21-measure['rms_dbfs'], -6-measure['sample_peak_dbfs'])
        scale = 10**(gain/20)
        normalized = array.array('f', (x*scale for x in samples))
        relative = 'audition/' + row['element'] + '/' + row['original_name'] + '.ogg'
        path = QA / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([ffmpeg,'-v','error','-y','-f','f32le','-ar',str(RATE),'-ac','1','-i','pipe:0','-c:a','libvorbis','-q:a','4','-fflags','+bitexact','-flags:a','+bitexact',str(path)],input=normalized.tobytes(),check=True)
        row['audition_path'] = relative
        row['audition_gain_db'] = round(gain,4)
        hop = max(1,len(samples)//160)
        peaks = [max(map(abs,samples[i:i+hop])) for i in range(0,len(samples),hop)][:160]
        largest = max(peaks)
        bars = ''.join(f'<rect x="{i*3}" y="{40-v/largest*36:.1f}" width="2" height="{max(1,v/largest*72):.1f}"/>' for i,v in enumerate(peaks))
        cards.append(f'<article><h3>{html.escape(row["element"])} / {html.escape(row["original_name"])}</h3><p>{row["duration_seconds"]:.3f}s · {html.escape(row["hypothesis"])}</p><svg viewBox="0 0 480 80" aria-label="Peak envelope">{bars}</svg><audio controls preload="none" src="{relative}"></audio><details><summary>Source evidence</summary><p>Action: unverified. Folder: {row["source_folder_id"]}</p><p><a href="https://drive.google.com/file/d/{row["drive_id"]}/view">{row["drive_id"]}</a></p><code>{row["source_sha256"]}</code></details></article>')
    document = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>W33 Super audition</title><style>body{font:16px system-ui;background:#111820;color:#e8edf2;max-width:1080px;margin:36px auto;padding:0 24px}h1{font-size:30px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:16px}article{background:#1c2936;border:1px solid #354658;border-radius:10px;padding:18px}h3{font-size:16px;margin:0}p{line-height:1.5;color:#bdcbd8}svg{width:100%;height:70px;fill:#67ced2}audio{width:100%}a{color:#9fd6ff}code{overflow-wrap:anywhere;font-size:11px}</style><h1>W33 Super audition</h1><p>Folder identity is known; action labels are provisional hypotheses. Full source durations retained in mono 32 kHz previews, gain normalized with at least 6 dB sample-peak headroom. No listening verification claimed. Production provisional mappings are documented separately in w33.json.</p><p>Arc Staff: 1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV · Golden Gun: 1OOf4gcCUUHm1PG9n8zeU7x0BmknqqHCz</p><main>' + ''.join(cards) + '</main><script>document.addEventListener("play",e=>{document.querySelectorAll("audio").forEach(a=>{if(a!==e.target)a.pause()})},true)</script></html>'
    (QA / 'audition.html').write_text(document)
    dump(QA / 'super-candidates.json',data)
    print('Built',len(cards),'audition previews')

if __name__ == '__main__':
    main()
