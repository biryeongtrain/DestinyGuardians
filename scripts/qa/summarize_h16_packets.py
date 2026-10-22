#!/usr/bin/env python3
"""Summarize timestamp-filtered Minecraft JFR packets for the client sample window.

Do not use the vanilla summary's durationMs as a denominator for restarted JFR:
some non-packet events span earlier recordings. This uses each packet event time
and the measured wall window. Payload bytes are not compressed TCP wire bytes.
"""
import argparse
import collections
import json
import subprocess
from datetime import datetime
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("jfr", type=Path)
    p.add_argument("client_sample", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--jfr-tool", default="/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home/bin/jfr")
    a = p.parse_args()
    sample = json.loads(a.client_sample.read_text())
    start = datetime.fromisoformat(sample["start_utc"]).timestamp()
    seconds = sample["duration_seconds"]
    data = json.loads(subprocess.check_output([a.jfr_tool, "print", "--json", "--events",
        "minecraft.PacketSent,minecraft.PacketReceived", str(a.jfr)]))
    directions = {"minecraft.PacketSent": "sent", "minecraft.PacketReceived": "received"}
    counts = {d: collections.Counter() for d in directions.values()}
    sizes = {d: collections.Counter() for d in directions.values()}
    addresses = {d: collections.Counter() for d in directions.values()}
    for event in data["recording"]["events"]:
        v = event["values"]
        # Python truncates sub-microsecond digits; sufficient for a 30-second rate window.
        when = datetime.fromisoformat(v["startTime"]).timestamp()
        if not start <= when < start + seconds:
            continue
        d = directions[event["type"]]
        key = v["protocolId"] + "/" + v["packetId"]
        counts[d][key] += 1
        sizes[d][key] += v["bytes"]
        addresses[d][v["remoteAddress"]] += 1
    out = {"jfr": a.jfr.name, "sample": a.client_sample.name,
           "window_start_utc": sample["start_utc"], "window_seconds": seconds,
           "bytes_semantics": "Minecraft JFR encoded packet payload; not compressed TCP wire bytes",
           "directions": {}}
    for d in directions.values():
        count, size = sum(counts[d].values()), sum(sizes[d].values())
        out["directions"][d] = {"packets": count, "payload_bytes": size,
            "packets_per_second": count / seconds, "payload_bytes_per_second": size / seconds,
            "remote_packet_counts": dict(addresses[d]),
            "by_packet": [{"packet": k, "count": n, "bytes": sizes[d][k]} for k, n in counts[d].most_common()]}
    a.output.write_text(json.dumps(out, indent=2) + "\n")
    print(a.output)


if __name__ == "__main__":
    main()
