"""Shared lossless DGZONE -> Nucleoid section-NBT converter (stdlib only)."""
import argparse, gzip, hashlib, json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def u16(n): return struct.pack(">H", n)
def i32(n): return struct.pack(">i", n)
def string(s):
    raw = s.encode("utf-8")
    return u16(len(raw)) + raw

def tag(kind, name, payload): return bytes([kind]) + string(name) + payload
def compound(entries): return b"".join(entries) + b"\0"
def ints(values): return i32(len(values)) + b"".join(i32(n) for n in values)
def items(kind, values): return bytes([kind]) + i32(len(values)) + b"".join(values)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def read_zone(path):
    raw = memoryview(gzip.decompress(path.read_bytes()))
    if bytes(raw[:8]) != b"DGZONE01": raise ValueError("Invalid authoring grid")
    sx, sy, sz = struct.unpack_from(">iii", raw, 8)
    n, = struct.unpack_from(">H", raw, 20); pos = 22; palette = []
    for _ in range(n):
        length, = struct.unpack_from(">H", raw, pos); pos += 2
        palette.append(bytes(raw[pos:pos+length]).decode()); pos += length
    runs, = struct.unpack_from(">i", raw, pos); pos += 4
    cells = bytearray()
    for _ in range(runs):
        pair = []
        for _ in range(2):
            value = shift = 0
            while True:
                b = raw[pos]; pos += 1; value |= (b & 127) << shift; shift += 7
                if not b & 128: break
                if shift > 35: raise ValueError("Invalid varint")
            pair.append(value)
        value, count = pair
        if value >= n or count < 1 or len(cells) + count > sx*sy*sz: raise ValueError("Invalid run")
        cells.extend(bytes([value]) * count)
    if len(cells) != sx*sy*sz or pos != len(raw): raise ValueError("Invalid grid length")
    return (sx, sy, sz), palette, cells

def block_state(text):
    name, _, properties = text.partition("[")
    entries = [tag(8, "id", string(name))]
    if properties:
        entries.append(tag(10, "properties", compound(tag(8, k, string(v))
            for k, v in (pair.split("=", 1) for pair in properties.rstrip("]").split(",")))))
    return compound(entries)

def export(source, target, origin, data_version):
    (sx, sy, sz), palette, cells = read_zone(source)
    chunks = []; count = 0
    for cy in range((sy+15)//16):
        for cz in range((sz+15)//16):
            for cx in range((sx+15)//16):
                section = bytearray(4096)
                for y in range(16):
                    for z in range(16):
                        yy, zz = cy*16+y, cz*16+z
                        if yy >= sy or zz >= sz: continue
                        width = min(16, sx-cx*16)
                        start = (yy*sz+zz)*sx+cx*16
                        section[y*256+z*16:y*256+z*16+width] = cells[start:start+width]
                used = sorted(set(section))
                if used == [0]: continue
                count += sum(v != 0 for v in section)
                remap = {value:i for i,value in enumerate(used)}
                entries = [tag(9, "palette", items(10, [block_state(palette[v]) for v in used]))]
                if len(used) > 1:
                    bits = max(4, (len(used)-1).bit_length()); per_long = 64//bits
                    words = []
                    for offset in range(0, 4096, per_long):
                        word = sum(remap[v] << (i*bits) for i,v in enumerate(section[offset:offset+per_long]))
                        words.append(struct.pack(">Q", word))
                    entries.append(tag(12, "data", i32(len(words))+b"".join(words)))
                chunks.append(compound([tag(11, "pos", ints([cx+origin[0]//16,cy+origin[1]//16,cz+origin[2]//16])),
                    tag(10, "block_states", compound(entries))]))
    bounds = compound([tag(11,"min",ints(origin)),tag(11,"max",ints([origin[0]+sx-1,origin[1]+sy-1,origin[2]+sz-1]))])
    root = compound([tag(3,"data_version",i32(data_version)), tag(9,"chunks",items(10,chunks)),
        tag(10,"bounds",bounds),tag(8,"biome",string("minecraft:the_void")),tag(9,"block_entities",items(10,[])),
        tag(9,"regions",items(10,[])),tag(10,"data",compound([tag(8,"authoring_sha256",string(sha(source)))]))])
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(gzip.compress(tag(10,"",root),compresslevel=9,mtime=0))
    return dict(source=str(source.relative_to(ROOT)),sourceSha256=sha(source),nbtSha256=sha(target),
                origin=origin,size=[sx,sy,sz],sections=len(chunks),blocks=count,bytes=target.stat().st_size)
