#!/usr/bin/env python3
"""Sample genuine game's FPS counter at 1 Hz; screenshot cadence is not FPS.

Run without screenshot capture during measured windows. Keeps focus state and all
loaded entity IDs/types/positions so diagnostics and culling can be distinguished.
"""
import argparse
import concurrent.futures
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def read(port):
    before = time.monotonic()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/state", timeout=10) as r:
            state = json.loads(r.read())
        return {"port": port, "request_seconds": time.monotonic() - before, "state": state}
    except Exception as error:
        return {"port": port, "request_seconds": time.monotonic() - before, "error": repr(error)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    p.add_argument("--seconds", type=int, default=30)
    p.add_argument("--ports", type=int, nargs="+", default=[8102, 8103])
    a = p.parse_args()
    start = time.monotonic()
    rows = []
    utc = datetime.now(timezone.utc).isoformat()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(a.ports)) as pool:
        while time.monotonic() - start < a.seconds:
            row = {"elapsed_seconds": time.monotonic() - start,
                   "clients": list(pool.map(read, a.ports))}
            rows.append(row)
            # Retain partial evidence if interrupted or a client goes away.
            save(a.output, {"start_utc": utc, "duration_seconds": time.monotonic() - start,
                "complete": False, "samples": rows})
            time.sleep(max(0, len(rows) - (time.monotonic() - start)))
    save(a.output, {"start_utc": utc, "duration_seconds": time.monotonic() - start,
                                   "complete": True,
                                   "source": "Minecraft.getFps via isolated Vision /state; 1 Hz polling",
                                   "samples": rows})
    print(str(a.output))


if __name__ == "__main__":
    main()
