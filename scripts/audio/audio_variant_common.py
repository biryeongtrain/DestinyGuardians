"""Shared full-duration positional mono conversion; original deliveries stay read-only."""
import hashlib
import json
import subprocess
import wave


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def mono_derivative(ffmpeg, wav, out):
    with wave.open(str(wav)) as stream:
        rate, frames, channels = stream.getframerate(), stream.getnframes(), stream.getnchannels()
    assert channels == 2
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
                    "-af", "pan=mono|c0=0.5*c0+0.5*c1", "-ar", str(rate),
                    "-map_metadata", "-1", "-threads", "1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                    "-c:a", "libvorbis", "-q:a", "5", str(out)], check=True)
    pcm = subprocess.check_output([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(out),
                                   "-f", "s16le", "-acodec", "pcm_s16le", "-"])
    decoded = len(pcm) // 2
    assert abs(decoded - frames) <= 256 and any(pcm), wav
    assert out.read_bytes()[39] == 1, "Vorbis identification must report mono"
    return rate, frames, decoded
