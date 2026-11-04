"""W300 Guardian Rises audio + subtitle build (presentation lane).

Voice: the extracted Korean Ghost lines (read-only source) -> mono 48 kHz Vorbis with the
W280 loudnorm chain, untrimmed. Shaw Han and Shaw-dependent Ghost lines are excluded by the
adaptation (no Shaw Han ending); 80B75F68/80B75F6D are 1-byte invalid in the source.

SFX: no SFX banks were present in the extraction (audio_banks/ and music-banks.json are empty),
so every SFX below is ORIGINAL work synthesized here from oscillators/noise (deterministic seed).

sounds.json: only guardian_rises.* entries are appended at the end; every other byte is kept.
Run from anywhere: python3 scripts/campaign/rising_audio.py
"""
import array, csv, hashlib, json, math, random, subprocess, sys, tempfile, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/Users/qf/Downloads/Rising-Guardian-2026-11-01")
FFMPEG = Path("/Users/qf/IdeaProjects/DestinyGuardians/run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1")
ASSETS = ROOT / "src/main/resources/assets/destiny"
SOUNDS_JSON = ASSETS / "sounds.json"
SUBTITLES = ROOT / "src/main/resources/destiny/guardian_rises/subtitles_ko.json"
SR = 48000
# Not used by this adaptation (user-confirmed: no Shaw Han ending).
EXCLUDED = {
    "80b75f70": "Shaw Han radio — Shaw Han ending removed",
    "80b75f73": "Shaw Han radio — Shaw Han ending removed",
    "80b75f6c": "Ghost reacts to Shaw's Vanguard radio — ending removed",
    "80b75f6a": "Ghost calls Shaw — ending removed",
    "80b75f69": "Ghost locks Shaw's location — ending removed",
}
# Original authored subtitle-only lines (NOT in the extraction; no voice exists or is faked).
AUTHORED = {
    "rg.opening.found": "…찾았어요. 드디어.",
    "rg.opening.scan": "움직이지 마세요. 당신의 빛을 되돌려 놓을게요.",
    "rg.arrival.tower": "도착했어요, 수호자. 여기가 탑이에요.",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(src, dst, loudnorm):
    dst.parent.mkdir(parents=True, exist_ok=True)
    af = ["-af", "loudnorm=I=-19:TP=-2:LRA=7"] if loudnorm else []
    subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", str(SR), *af,
                    "-c:a", "libvorbis", "-q:a", "4", "-map_metadata", "-1", "-fflags", "+bitexact",
                    "-flags:a", "+bitexact", str(dst)], check=True)
    subprocess.run([str(FFMPEG), "-v", "error", "-i", str(dst), "-f", "null", "-"], check=True)


def ogg_seconds(path):
    out = subprocess.run([str(FFMPEG), "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return len(out) / 2 / SR


# ---------------------------------------------------------------- synthesis (original SFX)
rng = random.Random(0x5EED_0300)


def zeros(sec):
    return [0.0] * int(sec * SR)


def add(buf, sig, start=0.0, gain=1.0):
    o = int(start * SR)
    for i, v in enumerate(sig):
        j = o + i
        if 0 <= j < len(buf):
            buf[j] += v * gain


def env(n, attack, release, shape=1.0):
    a, r = max(1, int(attack * SR)), max(1, int(release * SR))
    out = []
    for i in range(n):
        g = min(1.0, i / a, (n - i) / r)
        out.append(g ** shape)
    return out


def osc(freq_fn, sec, wave_fn=math.sin):
    n, ph, out = int(sec * SR), 0.0, []
    for i in range(n):
        out.append(wave_fn(ph))
        ph += 2 * math.pi * freq_fn(i / SR) / SR
    return out


def saw(ph):
    x = (ph / (2 * math.pi)) % 1.0
    return 2 * x - 1


def noise(sec):
    return [rng.uniform(-1, 1) for _ in range(int(sec * SR))]


def svf(sig, cutoff_fn, q=0.7, mode="lp"):
    """Chamberlin state-variable filter with time-varying cutoff."""
    low = band = 0.0
    out = []
    damp = 1.0 / q
    for i, x in enumerate(sig):
        fc = min(cutoff_fn(i / SR), SR / 6.5)
        f = 2 * math.sin(math.pi * fc / SR)
        high = x - low - damp * band
        band += f * high
        low += f * band
        out.append(low if mode == "lp" else band if mode == "bp" else high)
    return out


def mul(sig, g):
    return [a * b for a, b in zip(sig, g)]


def normalize(buf, peak=0.70):
    m = max(1e-9, max(abs(v) for v in buf))
    return [v * peak / m for v in buf]


def exp_ramp(a, b, t, total):
    return a * (b / a) ** min(1.0, max(0.0, t / total))


def sfx_scan_loop():
    sec = 4.0
    buf = zeros(sec)
    trem = lambda t: 0.55 + 0.45 * math.sin(2 * math.pi * 14 * t)
    for f, g in ((1760, .10), (2637, .07), (3520, .035)):
        s = osc(lambda t, f=f: f * (1 + 0.004 * math.sin(2 * math.pi * 5 * t)), sec)
        add(buf, [v * trem(i / SR) for i, v in enumerate(s)], 0, g)
    # Two band-pass noise sweeps rising head-to-toe in pitch, 2 s each.
    sweep = svf(noise(sec), lambda t: exp_ramp(500, 3600, t % 2.0, 2.0), q=6, mode="bp")
    add(buf, sweep, 0, .55)
    add(buf, osc(lambda t: 110, sec), 0, .07)
    t = 0.0
    while t < sec - .05:  # digital data ticks
        blip = osc(lambda _: 4200 + rng.choice((0, 600, 1200)), .004)
        add(buf, mul(blip, env(len(blip), .0005, .003)), t, .22 if rng.random() < .3 else .11)
        t += .125
    return mul(normalize(buf, .6), env(len(buf), .15, .45))


def sfx_revive():
    sec = 3.2
    buf = zeros(sec)
    swell = svf(noise(1.9), lambda t: exp_ramp(250, 9000, t, 1.9), q=.8)
    add(buf, [v * (i / len(swell)) ** 2.4 for i, v in enumerate(swell)], 0, .9)
    chord = zeros(1.4)
    for f in (440.0, 554.37, 659.26, 987.77, 1318.5):
        for d in (-1.5, 1.5):
            add(chord, osc(lambda t, f=f, d=d: f + d, 1.4), 0, .09)
    decay = [math.exp(-i / SR * 2.6) for i in range(len(chord))]
    add(buf, mul(chord, decay), 1.8, 1.0)
    thump = osc(lambda t: 55 * (1 - .4 * t), .5)
    add(buf, mul(thump, [math.exp(-i / SR * 9) for i in range(len(thump))]), 1.8, .8)
    return mul(normalize(buf, .7), env(len(buf), .01, .35))


def sfx_ship_power():
    sec = 4.6
    buf = zeros(sec)
    core = osc(lambda t: exp_ramp(38, 175, t, 4.0), sec, saw)
    add(buf, svf(core, lambda t: exp_ramp(180, 2600, t, 4.2), q=1.4), 0, .55)
    add(buf, osc(lambda t: exp_ramp(700, 3300, t, 4.4), sec), 0, .05)
    clunk = svf(noise(.25), lambda t: 420, q=.9)
    add(buf, mul(clunk, [math.exp(-i / SR * 18) for i in range(len(clunk))]), 0, 1.0)
    t = .3
    while t < sec - .2:  # electrical crackle, thinning out as the system stabilises
        burst = svf(noise(.012), lambda _: 5200, q=2, mode="bp")
        add(buf, burst, t, .25 * (1 - t / sec))
        t += rng.uniform(.05, .22)
    return mul(normalize(buf, .7), env(len(buf), .02, .6))


def sfx_ship_takeoff():
    sec = 6.6
    buf = zeros(sec)
    brown, acc = [], 0.0
    for v in noise(sec):
        acc = acc * .995 + v * .1
        brown.append(acc)
    roar = svf(brown, lambda t: 380 + 1300 * math.sin(math.pi * min(1, t / 4.2)), q=.9)
    shape = [min(1, (i / SR) / 1.6) ** 1.5 * math.exp(-max(0, i / SR - 2.2) * .9) for i in range(len(roar))]
    add(buf, mul(roar, shape), 0, 1.0)
    tone = osc(lambda t: 95 - 35 * min(1, max(0, t - 1.6) / 4), sec, saw)
    add(buf, mul(svf(tone, lambda t: 700, q=1), shape), 0, .35)
    whine = osc(lambda t: 1250 - 520 * min(1, max(0, t - 1.6) / 4), sec)
    add(buf, mul(whine, shape), 0, .05)
    return mul(normalize(buf, .75), env(len(buf), .05, 1.2))


def sfx_transmat():
    sec = 1.7
    buf = zeros(sec)
    gl = osc(lambda t: exp_ramp(2600, 520, t, 1.3) * (1 + .02 * math.sin(2 * math.pi * 9 * t)), 1.4)
    add(buf, mul(gl, env(len(gl), .02, .5)), 0, .18)
    for _ in range(70):
        t0 = rng.random() ** 1.6 * 1.2
        f = rng.uniform(3000, 7200)
        s = osc(lambda _t, f=f: f, .09)
        add(buf, mul(s, [math.exp(-i / SR * 45) for i in range(len(s))]), t0, .09)
    zap = svf(noise(.18), lambda t: 2500, q=1, mode="hp")
    add(buf, mul(zap, [math.exp(-i / SR * 25) for i in range(len(zap))]), 1.3, .5)
    return mul(normalize(buf, .65), env(len(buf), .005, .3))


def sfx_ambient():
    loop, fade = 24.0, 2.0
    sec = loop + fade
    src = noise(sec)
    # LFOs complete whole cycles inside the loop, so the crossfaded seam is continuous.
    cut = lambda t: 260 + 170 * math.sin(2 * math.pi * 2 * t / loop) + 90 * math.sin(2 * math.pi * 5 * t / loop + 1.3)
    wind = svf(src, cut, q=1.8, mode="bp")
    gust = [0.55 + 0.45 * math.sin(2 * math.pi * 3 * (i / SR) / loop) ** 2 for i in range(len(wind))]
    buf = mul(wind, gust)
    for t0, f in ((3.1, 182), (11.7, 141), (17.4, 207)):  # distant metal creaks
        c = osc(lambda t, f=f: f * (1 + .03 * math.sin(2 * math.pi * 6 * t)), 1.6, saw)
        c = svf(c, lambda _: 900, q=3, mode="bp")
        add(buf, mul(c, env(len(c), .5, .9)), t0, .05)
    n, k = int(loop * SR), int(fade * SR)
    out = buf[:n]
    for i in range(k):
        a = i / k
        out[i] = out[i] * a + buf[n + i] * (1 - a)
    return normalize(out, .45)


SFX = {"scan_loop": sfx_scan_loop, "revive": sfx_revive, "ship_power": sfx_ship_power,
       "ship_takeoff": sfx_ship_takeoff, "transmat": sfx_transmat, "ambient_cosmodrome": sfx_ambient}


def write_wav(path, samples):
    data = array.array("h", (max(-32767, min(32767, int(v * 32767))) for v in samples))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


# ---------------------------------------------------------------- sounds.json (append-only)
def sound_entry(name, stream):
    return {"sounds": [{"name": f"destiny:{name}", "stream": stream}]}


def append_sounds(entries):
    text = SOUNDS_JSON.read_text(encoding="utf-8")
    marker = ',\n  "guardian_rises.'
    if marker in text:  # re-run: cut our previous block, the last original entry is kept verbatim
        base = text[:text.index(marker)]
    else:  # first run: drop only the root closing brace
        base = text.rstrip()
        if not base.endswith("}"):
            raise SystemExit("unexpected sounds.json tail")
        base = base[:-1].rstrip()
    body = ""
    for key, value in entries.items():
        inner = json.dumps(value, ensure_ascii=False, indent=2).replace("\n", "\n  ")
        body += f',\n  "{key}": {inner}'
    new = base + body + "\n}\n"
    before = json.loads(text)
    after = json.loads(new)
    keep = {k: v for k, v in after.items() if not k.startswith("guardian_rises.")}
    old = {k: v for k, v in before.items() if not k.startswith("guardian_rises.")}
    if keep != old or list(keep) != list(old):
        raise SystemExit("non-guardian sounds.json entries changed")
    SOUNDS_JSON.write_text(new, encoding="utf-8")


def main():
    rows = list(csv.DictReader((SOURCE / "dialogue-ko.csv").open(encoding="utf-8-sig")))
    lines, excluded, entries = {}, {}, {}
    for row in rows:
        tag = row["wem"].lower()
        if tag in EXCLUDED:
            excluded[tag] = {"speaker": row["narrator"], "korean": row["korean"], "reason": EXCLUDED[tag]}
            continue
        if row["status"] != "full_decode_non_silent":
            excluded[tag] = {"speaker": row["narrator"], "english": row["text"].strip(),
                             "reason": "source Korean audio missing/invalid (" + row["status"] + ")"}
            continue
        src = SOURCE / row["file"]
        if sha(src) != row["sha256"]:
            raise SystemExit("source hash mismatch " + str(src))
        dst = ASSETS / f"sounds/guardian_rises/voice/{tag}.ogg"
        encode(src, dst, loudnorm=True)
        with wave.open(str(src)) as w:
            seconds = w.getnframes() / w.getframerate()
        lines[tag] = {"speaker": "고스트", "text": row["korean"], "english": row["text"].strip(),
                      "ticks": math.ceil(seconds * 20), "duration_sec": round(seconds, 4), "voice": True,
                      "authored": False, "source": row["file"], "source_sha256": row["sha256"],
                      "output_sha256": sha(dst), "output_bytes": dst.stat().st_size}
        entries[f"guardian_rises.voice.{tag}"] = sound_entry(f"guardian_rises/voice/{tag}", True)
    for key, text in AUTHORED.items():
        # Reading-speed estimate: ~7 Hangul syllables per second plus a short hold.
        syllables = sum(1 for ch in text if not ch.isspace())
        lines[key] = {"speaker": "고스트", "text": text, "ticks": max(50, round(syllables / 7 * 20) + 24),
                      "voice": False, "authored": True,
                      "note": "Original W300 subtitle-only line. Not in the extraction; no voice recorded or substituted."}
    sfx_report = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name, fn in SFX.items():
            wav = Path(tmp) / f"{name}.wav"
            write_wav(wav, fn())
            dst = ASSETS / f"sounds/guardian_rises/sfx/{name}.ogg"
            encode(wav, dst, loudnorm=False)
            seconds = ogg_seconds(dst)
            sfx_report[name] = {"ticks": math.ceil(seconds * 20), "duration_sec": round(seconds, 3),
                                "provenance": "original synthesized (scripts/campaign/rising_audio.py, seed 0x5EED0300)",
                                "output_sha256": sha(dst)}
            entries[f"guardian_rises.sfx.{name}"] = sound_entry(f"guardian_rises/sfx/{name}", name.startswith("ambient"))
    SUBTITLES.parent.mkdir(parents=True, exist_ok=True)
    SUBTITLES.write_text(json.dumps({
        "version": 1,
        "source": "Rising-Guardian-2026-11-01/dialogue-ko.csv (korean column, exact)",
        "lines": lines, "sfx": sfx_report, "excluded": excluded}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_sounds(entries)
    print("voice", sum(1 for v in lines.values() if v["voice"]), "authored", len(AUTHORED),
          "excluded", len(excluded), "sfx", len(sfx_report), "sound events", len(entries))


if __name__ == "__main__":
    sys.exit(main())
