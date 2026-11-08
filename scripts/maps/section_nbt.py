"""Independent reader for Nucleoid section-NBT map artifacts (no game client)."""
import gzip, struct
import numpy as np


def load(path):
    raw=memoryview(gzip.decompress(path.read_bytes()));offset=0
    def take(n):
        nonlocal offset
        value=raw[offset:offset+n];offset+=n
        if len(value)!=n:raise ValueError('Truncated NBT')
        return value
    def num(fmt):return struct.unpack(fmt,take(struct.calcsize(fmt)))[0]
    def string():return bytes(take(num('>H'))).decode('utf-8')
    def payload(kind):
        if kind in (1,2,3,4,5,6):return num({1:'>b',2:'>h',3:'>i',4:'>q',5:'>f',6:'>d'}[kind])
        if kind==8:return string()
        if kind==9:
            element=num('>B');count=num('>i')
            if count<0:raise ValueError('Negative NBT list')
            return [payload(element)for _ in range(count)]
        if kind==10:
            value={}
            while True:
                sub=num('>B')
                if sub==0:return value
                key=string()
                if key in value:raise ValueError('Duplicate NBT key')
                value[key]=payload(sub)
        if kind in (7,11,12):
            count=num('>i')
            if count<0:raise ValueError('Negative NBT array')
            return np.frombuffer(take(count*{7:1,11:4,12:8}[kind]),dtype={7:'i1',11:'>i4',12:'>u8'}[kind])
        raise ValueError(f'Unsupported NBT type {kind}')
    if num('>B')!=10:raise ValueError('Expected compound root')
    string();root=payload(10)
    if offset!=len(raw):raise ValueError('Trailing NBT bytes')
    return root


def state_text(state):
    props=state.get('properties',{})
    return state['id']+('['+','.join(k+'='+v for k,v in props.items())+']'if props else '')


def sections(root):
    seen=set()
    for chunk in root['chunks']:
        pos=tuple(map(int,chunk['pos']))
        if pos in seen:raise ValueError(f'Duplicate section {pos}')
        seen.add(pos);bs=chunk['block_states'];palette=[state_text(s)for s in bs['palette']]
        if not palette:raise ValueError('Empty section palette')
        if len(palette)==1:indices=np.zeros(4096,np.int32)
        else:
            bits=max(4,(len(palette)-1).bit_length());per=64//bits
            words=bs['data'].astype(np.uint64);i=np.arange(4096,dtype=np.uint64)
            if len(words)!=(4096+per-1)//per:raise ValueError('Wrong packed section length')
            indices=((words[i//per]>>((i%per)*bits))&((1<<bits)-1)).astype(np.int32)
            if indices.max()>=len(palette):raise ValueError('Invalid section palette index')
        yield pos,palette,indices.reshape(16,16,16)
