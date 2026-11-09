"""Author Nucleoid regions and patch metadata without re-encoding any block sections."""
import gzip
import struct
from pathlib import Path
import zone_nbt as nbt


def region_payload(definitions, origin):
    regions = []
    for region in definitions:
        low = [v + o for v, o in zip(region['min'], origin)]
        high = [v + o for v, o in zip(region['max'], origin)]
        if len(low) != 3 or len(high) != 3 or any(a > b for a, b in zip(low, high)):
            raise ValueError('Invalid region bounds: ' + region['id'])
        regions.append(nbt.compound([
            nbt.tag(8, 'marker', nbt.string(region['marker'])),
            nbt.tag(11, 'min', nbt.ints(low)), nbt.tag(11, 'max', nbt.ints(high)),
            nbt.tag(10, 'data', nbt.compound([nbt.tag(8, 'id', nbt.string(region['id']))]))]))
    return nbt.items(10, regions)


def patch_regions(path, definitions, origin):
    """Replace only the root regions tag; retain every other uncompressed byte."""
    path = Path(path)
    raw = gzip.decompress(path.read_bytes())
    offset = 0

    def take(n):
        nonlocal offset
        value = raw[offset:offset+n]
        offset += n
        if len(value) != n:
            raise ValueError('Truncated NBT')
        return value

    def number(fmt):
        return struct.unpack(fmt, take(struct.calcsize(fmt)))[0]

    def string():
        return take(number('>H')).decode('utf-8')

    def skip(kind):
        if kind in (1, 2, 3, 4, 5, 6):
            take({1:1, 2:2, 3:4, 4:8, 5:4, 6:8}[kind])
        elif kind == 8:
            string()
        elif kind == 9:
            sub, count = number('>B'), number('>i')
            if count < 0: raise ValueError('Negative list length')
            for _ in range(count): skip(sub)
        elif kind == 10:
            while True:
                sub = number('>B')
                if sub == 0: break
                string(); skip(sub)
        elif kind in (7, 11, 12):
            count = number('>i')
            if count < 0: raise ValueError('Negative array length')
            take(count * {7:1, 11:4, 12:8}[kind])
        else:
            raise ValueError('Unknown NBT kind ' + str(kind))

    if number('>B') != 10: raise ValueError('Expected compound root')
    string()
    replacement = nbt.tag(9, 'regions', region_payload(definitions, origin))
    found = False
    while True:
        start = offset
        kind = number('>B')
        if kind == 0: break
        name = string(); skip(kind)
        if name == 'regions':
            if found: raise ValueError('Duplicate regions tag')
            found = True
            changed = raw[:start] + replacement + raw[offset:]
    if offset != len(raw): raise ValueError('Trailing NBT bytes')
    if not found: changed = raw[:-1] + replacement + raw[-1:]
    path.write_bytes(gzip.compress(changed, compresslevel=9, mtime=0))
