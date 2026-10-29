"""W245 material basecolor equations from the supplied 3Dmigoto HLSL.

No game lighting/normal/emission reconstruction. Inputs are PS TEXCOORD3.xy,
not automatically raw mesh UV0: callers own the VS/chunk UV transform. DDS
RGB is decoded to linear BEFORE filtering; alpha and Non-Color stay linear.
All equations and cbuffer colors operate in linear space. sample returns sRGB.

Default valid means supported, finite, and no missing basecolor inputs.
For explicitly accepted static/world/instance substitutes construct with
allow_representative=True. Such samples are usable, never exact; see recipes.
Without that opt-in the RGB estimate is still returned but valid is false.
bake alpha encodes this validity, NOT the game G-buffer o0.w/opacity.
"""
from __future__ import annotations
import argparse
from collections import OrderedDict
import io
import json
from pathlib import Path
import struct
import numpy as np
from PIL import Image


def srgb_to_linear(x):
    x = np.asarray(x, dtype=np.float32)
    return np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)


def linear_to_srgb(x):
    x = np.maximum(np.asarray(x, dtype=np.float32), 0)
    return np.where(x <= .0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - .055)


def sat(x):
    return np.clip(x, 0, 1)


def mix(a, b, w):
    return a + w * (b - a)


# Explicit shader allowlist: similar names or texture slots do not imply a match.
FAMILIES = {
    "mask_dye": ["8113C982", "80B4F9B4", "8113C946", "8113C8A4", "8113C916", "8113C9E4"],
    "layer_detail": ["8113C94B", "8113D1B6", "8113DD37"],
    "graded_albedo": ["80B4F7BB", "8113D448"],
    "palette_masks": ["80B4F7C0", "80B4F7C3"],
    "world_detail": ["8113C163"],
    "world_dye": ["8113CA88"],
    "world_tint": ["8113F230"],
    "uv_tint": ["8113F235"],
    "direct_albedo": ["8113D45D"],
    "instance_layers": ["8113D463"],
    "affine_dye": ["8113C8C5"],
    "affine_additive": ["80B4F8A3"],
    "normal_layers": ["8113F25A"],
    "complex_dye_layers": ["8113C992"],
    "projected_decal": ["8113EA2C"],
}
SHADERS = {s: f for f, shaders in FAMILIES.items() for s in shaders}
FORMULAS = {
    "mask_dye": "q=T1(uv*cb0.xy+cb0.zw); A=cb1+cb2*q.a; B=cb3+cb4*q.a; C=cb5+cb6*q.g; D=lerp(select(uv.x>0,A,B),C,select(uv.y>1,T0.r,1)); rgb=lerp(D,cb7,sat(cb8.x+cb8.y*T0.g)).rgb; C8A4 shifts color indices +3 and remaps T0.r; C9E4 uses T0.b to blend A/B, T0.r for C",
    "layer_detail": "noise=T4(uv*cb3.xy+cb3.zw); w=sat(sat(T0.g*(1-cb9.x)+cb9.x*(cb10.x+cb10.y*noise.g))+clamp(cb6.x+cb6.y*T2.g,cb7.x,cb8.x)); base=lerp(cb11+cb12*sat(T0.g),T0,remap(w)); detail=cb1+cb2*sat(T1.r); m=sat(cb4.x*sat(cb5.x+cb5.y*T3.r)+(1-cb4.x)*TEXCOORD8.w); rgb=lerp(base,detail,m)*noise; C94B/DD37 select remap and tint by uv.y>1; DD37 has third dye ramp",
    "graded_albedo": "x=T0.rgb; D448: x=lerp(x,x*cb8.rgb,x.b); x=clamp((x*gain)*contrast+offset,lo,hi); x=tint*x; x=dot(x,[.3,.59,.11])+saturation*(x-dot(x,[.3,.59,.11])); rgb=x*min(1,max(gain_or_cb14,0)^exponent)",
    "palette_masks": "m=T1(affine_uv).rgb; A=cbBase+cbDelta*sat(remap(m.g)); B=lerp(A,cbSecond,m.r); C=lerp(B,cbThird,m.b); rgb=C*sat(remap(T0(uv*cb5.xy+cb5.zw).g))",
    "world_detail": "rgb=T2(uv*cb5.xy+cb5.zw).rgb*sat((T0(worldAffine*cb2.xy+cb2.zw).rgb+cb0.rgb)*(T1(worldAffine*cb4.xy+cb4.zw).rgb+cb3.rgb)); worldAffine=world.xy*cb1.xy+cb1.zw; TFX can overwrite cb2/cb3/cb4",
    "world_dye": "d=T1(affine(uv,cb0,cb1)); w=sat(cb3.x+cb3.y*T1(world.xy*cb2.xy+cb2.zw).a); A=cb6+cb7*sat(w+cb5.x+cb5.y*d.a); B=cb8+cb9*sat(d.g); rgb=lerp(cb4,lerp(A,B,T0.r),sat(cb10.x+cb10.y*T0.g)).rgb",
    "world_tint": "rgb=cb1.rgb*T0(world.xy*cb0.xy+cb0.zw).rgb",
    "uv_tint": "rgb=cb5.rgb*T0(uv).rgb",
    "direct_albedo": "rgb=T0(uv).rgb",
    "instance_layers": "a=sat(remap(sat(T2(uv*cb3.xy+cb3.zw).r*cb4.x+TEXCOORD8.x*(1-cb4.x)),cb5)); b=sat(remap(sat(cb2.w*T1(uv*cb0.xy+cb0.zw).a*cb6.x+TEXCOORD8.w*(1-cb6.x)),cb7)); rgb=lerp(cb1*T0,cb2*T1,b)*lerp(cb1,T3,a)",
    "affine_dye": "m=sat(T2(affine(uv,cb3,cb4)).r); rgb=T0.rgb*lerp(cb0.rgb+cb1.rgb*m,cb2.rgb,T1.r)",
    "affine_additive": "qUV=affine(uv,cb4,cb5); red=T1(qUV,s2_clamp).r; green=T1(qUV,s1_wrap).g; rgb=(cb0.rgb+cb1.rgb*sat(red))*(cb2.x+cb2.y*green)+(cb3.x+cb3.y*T0.g)",
    "normal_layers": "w=sat(cb21.x*sat(remap(T6.r,cb18))*(cb20.x+cb20.y*dot(cb19.xyz,normal))); a=sat(cb4.x+cb4.y*TEXCOORD8.z); foreground=lerp(lerp(T0(affine(affine(uv,cb0,cb1),cb2,cb3)),T0(affine(uv,cb2,cb3)),a),cb5,cb6.x); background=cb15*T4(affine(uv,cb13,cb14)); rgb=lerp(background,foreground,w)",
    "complex_dye_layers": "n=T0.g; q=T1(detailUV).r; base=(cb2+cb3*sat(cb1.x+cb1.y*n))*T2(detailUV)+T3; dye=cb5+cb6*sat(cb4.x+cb4.y*n)+(cb8+cb9*sat(cb7.x+cb7.y*q))*cb10*n; w=sat(TEXCOORD8.w*cb23.x+cb23.y*lerp(sat(cb24.x+cb24.y*q),sat(cb25.x+cb25.y*n),cb26.x)); rgb=lerp(base,select(uv.y>1,dye,base),w)",
    "projected_decal": "n=T3(uv).g; q=triplanar T4(world,normal,cb1..11); weight=clamp(remap(clamp(remap(q,cb22),cb20,cb21)*clamp(remap(n,cb19),cb17,cb18),cb25),cb23,cb24); rgb=(cb15+cb16*sat(clamp(remap(q,cb14),cb12,cb13)))*weight*sat(cb30.y); no G-buffer normal/depth compositing",
}
# Basecolor texture dependencies only: normal/roughness slots intentionally excluded.
SLOTS = {
    "mask_dye": [0, 1], "layer_detail": [0, 1, 2, 3, 4],
    "graded_albedo": [0], "palette_masks": [0, 1],
    "world_detail": [0, 1, 2], "world_dye": [0, 1],
    "world_tint": [0], "uv_tint": [0], "direct_albedo": [0],
    "instance_layers": [0, 1, 2, 3], "affine_dye": [0, 1, 2],
    "affine_additive": [0, 1], "normal_layers": [0, 4, 6],
    "complex_dye_layers": [0, 1, 2, 3], "projected_decal": [3, 4],
}


def decode_dds(path):
    """Decode BC1/2/3/7 sRGB DDS using identical UNORM block codec in memory."""
    data = bytearray(Path(path).read_bytes())
    if data[:4] != b"DDS ":
        raise ValueError(f"Not DDS: {path}")
    if data[84:88] == b"DX10":
        fmt = struct.unpack_from("<I", data, 128)[0]
        # No decompression/color edits here. This only bypasses Pillow enum gaps.
        remap = {29: 28, 72: 71, 75: 74, 78: 77, 91: 87, 93: 88, 99: 98}
        if fmt in remap:
            struct.pack_into("<I", data, 128, remap[fmt])
    with Image.open(io.BytesIO(data)) as im:
        return np.asarray(im.convert("RGBA"), dtype=np.float32) / 255


COMMON_UV_VERTEX_SHADERS = {"8113C0FC", "8113C0E0", "80B4FB63", "8113C0F7", "8113D459", "8113D445"}


def raw_uv_to_texcoord3(raw_uv, chunk_uv=None, *, allow_representative=False):
    """VS equation: PS TEXCOORD3.xy = TEXCOORD0.xy * cb1[1].xx + cb1[1].yz.

    chunk_uv is cb1[1] as (scale, offset_u, offset_v[, unused_w]), or Nx3/4
    per-sample values. Materials Vertex.CBuffers are cb0, NOT this cb1.
    None returns identity representative UVs and false validity unless explicitly
    accepted. This helper does not decode packed integer UVs or infer cb1.
    """
    uv=np.asarray(raw_uv,dtype=np.float32)
    if uv.ndim!=2 or uv.shape[1]!=2: raise ValueError("raw_uv must be Nx2")
    valid=np.isfinite(uv).all(axis=1,keepdims=True)
    if chunk_uv is None:
        return uv.copy(),valid & bool(allow_representative)
    c=np.asarray(chunk_uv,dtype=np.float32)
    if c.shape not in {(3,),(4,),(len(uv),3),(len(uv),4)}:
        raise ValueError("chunk_uv must be cb1[1] as 3/4 or Nx3/4")
    c=np.broadcast_to(c,(len(uv),c.shape[-1]))
    out=uv*c[:,0:1]+c[:,1:3]
    return out,np.isfinite(out).all(axis=1,keepdims=True)&valid


def uv_from_charm_export(export_uv, *, terrain=False):
    """STATIC Charm 058e2ec VertexTexcoords0 -> (PS UV Nx2, valid Nx1).

    StaticPart.TransformUVs already applied scale/translation and stored
    (ps_u, 1-ps_v). Undo V flip only; do NOT call raw_uv_to_texcoord3 again.
    Caller must account for any additional downstream GLB UV conversion.
    terrain is a bool or length-N mask: terrain entries are returned unchanged
    and invalid until that export pipeline is independently verified.
    """
    uv=np.asarray(export_uv,dtype=np.float32)
    if uv.ndim!=2 or uv.shape[1]!=2: raise ValueError("export_uv must be Nx2")
    terrain_mask=np.asarray(terrain,dtype=bool)
    if terrain_mask.ndim==2 and terrain_mask.shape==(len(uv),1):
        terrain_mask=terrain_mask[:,0]
    terrain_mask=np.broadcast_to(terrain_mask,(len(uv),))
    out=uv.copy()
    out[~terrain_mask,1]=1-out[~terrain_mask,1]
    valid=np.isfinite(out).all(axis=1,keepdims=True)&(~terrain_mask[:,None])
    return out,valid


class MaterialBaker:
    def __init__(self, material_root, *, allow_representative=False, cache_mb=256):
        self.root = Path(material_root)
        self.allow_representative = bool(allow_representative)
        self.cache_limit = max(1, int(cache_mb)) * 1024**2
        self._cache = OrderedDict()
        self._cache_bytes = 0
        self.materials = {}
        self.recipes = {}
        self.last_errors = {}
        for path in sorted((self.root / "Materials").glob("*.json")):
            d = json.loads(path.read_text())
            p = d["Material"]["Pixel"]
            cb = np.array([[v[a] for a in "XYZW"] for v in p["CBuffers"]], dtype=np.float32)
            tag = d["Hash"].upper()
            self.materials[tag] = (d, p, cb)
            shader = p["Hash"]
            family = SHADERS.get(shader)
            required = []
            if family in {"world_detail", "world_dye", "world_tint"}:
                required.append("world_xy")
            if family == "layer_detail" and cb[4, 0] != 1:
                required.append("instance8")
            if family == "instance_layers" and (cb[4, 0] != 1 or cb[6, 0] != 1):
                required.append("instance8")
            if family == "normal_layers":
                required.extend(["normal", "instance8"])
            if family == "complex_dye_layers" and cb[23, 0] != 0:
                required.append("instance8")
            if family == "projected_decal":
                required.extend(["world_xyz", "normal"])
            dynamic = []
            bc = p.get("Bytecode", [])
            # Every potentially dynamic cbuffer output is disclosed. Only outputs
            # used by these equations affect validity (others are PBR/emission).
            dynamic_all = [int(x.split(":")[1]) for x in bc if x.startswith("PopOutput:")]
            if family == "world_detail":
                dynamic = sorted(set(dynamic_all) & {0, 1, 2, 3, 4, 5})
            warnings = ["PS TEXCOORD3.xy expected; mesh UV0 requires caller-verified VS/chunk transform", "LOD0 bilinear; derivatives, mip bias and anisotropy not reproduced", "basecolor only; no lighting, normal, emissive or engine compositing"]
            if family == "projected_decal":
                warnings.append("isolated decal color contribution; framebuffer normal/depth rejection unavailable; bake alpha is NOT physical decal opacity")
            if not family:
                warnings.append("shader unsupported; no slot0 fallback")
            vertex_shader=d["Material"]["Vertex"]["Hash"]
            uv_common=vertex_shader in COMMON_UV_VERTEX_SHADERS
            self.recipes[tag] = {
                "shader": shader, "vertex_shader": vertex_shader,
                "raw_uv_transform": {"supported_common_affine": uv_common, "formula": "PS TEXCOORD3.xy = rawUV0 * CHUNK_MODEL.cb1[1].x + CHUNK_MODEL.cb1[1].yz" if uv_common else "not analyzed", "required_engine_input": "CHUNK_MODEL.cb1[1]", "available_in_material_json": False, "missing_behavior": "identity representative approximation only", "evidence": f"Shaders/HLSL/VS_{vertex_shader}.hlsl"},
                "raw_vs_contract": {"input": "genuine uncooked normalized GPU TEXCOORD0", "requires_chunk_uv": True, "formula": "rawUV*cb1[1].x+cb1[1].yz", "helper": "uv_from_raw", "applies_to_current_static_export": False},
                "static_export_contract": {"input": "StaticPart.TransformUVs cooked VertexTexcoords0", "formula": "PS UV = (export_u,1-export_v)", "requires_chunk_uv": False, "helper": "uv_from_charm_export", "downstream_condition": "caller confirms STATIC path and accounts for extra GLB transforms", "terrain_verified": False},
                "family": family or "unsupported", "supported": bool(family),
                "quality": "representative_approximation" if required or dynamic else ("basecolor_equation_with_uv_contract" if family else "unsupported"),
                "exact_original_color": False, "required_inputs": required,
                "dynamic_cb_outputs": dynamic_all, "basecolor_dynamic_cb_outputs": dynamic,
                "representative_substitutes": {"world_xy": "PS UV used as world.xy", "world_xyz": "(u,v,0) used as world.xyz", "instance8": "(1,1,1,1); TEXCOORD8 is interpolated vertex Buffer t0 data, not a proven per-instance color", "normal": "(0,0,1) in Destiny Z-up coordinates", "dynamic_cb": "extracted static CBuffers, not evaluated TFX"},
                "basecolor_slots": SLOTS.get(family, []),
                "textures": p["Textures"], "formula": FORMULAS.get(family, "unsupported"),
                "pixel_cb_snapshot": cb.tolist() if family else None,
                "evidence": f"Shaders/HLSL/PS_{shader}.hlsl", "warnings": warnings,
                "valid_semantics": "all inputs present; allow_representative=True explicitly accepts disclosed substitutes",
                "colorspace": "DDS sRGB RGB -> linear before filtering; alpha/Non-Color unchanged; cbuffer linear; output sRGB clipped 0..1",
            }

    uv_from_charm_export = staticmethod(uv_from_charm_export)

    def uv_from_raw(self, tag, uv, chunk_uv=None):
        """Per-material common VS affine; returns PS UV Nx2 and validity Nx1."""
        tag=str(tag).upper()
        if tag not in self.recipes or not self.recipes[tag]["raw_uv_transform"]["supported_common_affine"]:
            a=np.asarray(uv,dtype=np.float32)
            return a.copy(),np.zeros((len(a),1),bool)
        return raw_uv_to_texcoord3(uv,chunk_uv,allow_representative=self.allow_representative)

    def _texture(self, spec):
        key = (spec["Hash"], spec["Colorspace"])
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        a = decode_dds(self.root / "Textures" / f"{spec['Hash']}.dds")
        if spec["Colorspace"].lower() == "srgb":
            a[..., :3] = srgb_to_linear(a[..., :3])
        while self._cache and self._cache_bytes + a.nbytes > self.cache_limit:
            _, old = self._cache.popitem(last=False)
            self._cache_bytes -= old.nbytes
        self._cache[key] = a
        self._cache_bytes += a.nbytes
        return a

    def _sample_texture(self, p, slot, uv, sampler=1):
        spec = p["Textures"][str(slot)]
        if spec.get("Dimension") != "2D":
            raise ValueError(f"basecolor texture {slot} is not 2D")
        a = self._texture(spec)
        h, w = a.shape[:2]
        state = p.get("Samplers", {}).get(str(sampler))
        if state is None:
            raise ValueError(f"sampler {sampler} unavailable")
        def address(idx, n, mode):
            if mode == "Wrap": return idx % n
            if mode == "Clamp": return np.clip(idx, 0, n-1)
            if mode == "Mirror":
                idx = idx % (2*n)
                return np.where(idx < n, idx, 2*n-1-idx)
            raise ValueError(f"unsupported address mode {mode}")
        x = uv[:, 0] * w - .5
        y = uv[:, 1] * h - .5  # DDS row zero = v zero; no hidden vertical flip.
        x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
        ax, ay = (x - x0)[:, None], (y - y0)[:, None]
        def fetch(ix, iy):
            return a[address(iy,h,state["AddressV"]), address(ix,w,state["AddressU"])]
        if state["Filter"] == "MinMagMipPoint":
            return fetch(np.floor(x+.5).astype(np.int64), np.floor(y+.5).astype(np.int64))
        if state["Filter"] not in {"MinMagMipLinear", "Anisotropic"}:
            raise ValueError(f"unsupported filter {state['Filter']}")
        return mix(mix(fetch(x0,y0),fetch(x0+1,y0),ax),mix(fetch(x0,y0+1),fetch(x0+1,y0+1),ax),ay).astype(np.float32)

    def _evaluate(self, tag, uv, inputs):
        d, p, c = self.materials[tag]
        recipe = self.recipes[tag]
        f, h = recipe["family"], p["Hash"]
        n = len(uv)
        missing = [k for k in recipe["required_inputs"] if k not in inputs]
        cb_missing = [k for k in recipe["basecolor_dynamic_cb_outputs"] if k not in inputs.get("cb_overrides", {})]
        if "cb_overrides" in inputs:
            c = c.copy()
            for k,v in inputs["cb_overrides"].items(): c[int(k)] = v
        def field(name, default, width):
            a = np.asarray(inputs.get(name, default), dtype=np.float32)
            return np.broadcast_to(a, (n,width))
        world = field("world_xy", uv, 2)
        ins = field("instance8", [1,1,1,1], 4)
        normal = field("normal", [0,0,1], 3)
        def t(slot, q=uv, sampler=1): return self._sample_texture(p, slot, q, sampler)
        def transform(q, i): return q*c[i,:2]+c[i,2:]
        def affine(q,i,j): return np.stack((q@c[i,:2]+c[i,2],q@c[j,:2]+c[j,2]),axis=1)
        def remap(x,i): return c[i,0]+c[i,1]*x
        def clampcb(x,lo,hi): return np.minimum(c[hi,0],np.maximum(c[lo,0],x))
        if f == "mask_dye":
            q = t(1,transform(uv,0)); base=t(0)
            shift = 3 if h == "8113C8A4" else 0
            a = c[1+shift,:3]+sat(q[:,3:4])*c[2+shift,:3]
            b = c[3+shift,:3]+sat(q[:,3:4])*c[4+shift,:3]
            z = c[5+shift,:3]+sat(q[:,1:2])*c[6+shift,:3]
            if h == "8113C9E4":
                color = mix(mix(a,b,base[:,2:3]),z,base[:,0:1])
            else:
                color = np.where(uv[:,0:1]>0,a,b)
                w = base[:,0:1]
                if shift: w=clampcb(remap(w,3),1,2)
                color = mix(color,z,np.where(uv[:,1:2]>1,w,1))
            rgb=mix(color,c[7+shift,:3],sat(remap(base[:,1:2],8+shift)))
        elif f == "layer_detail":
            noise=t(4,transform(uv,3))[:,:3]; base=t(0)[:,:3]; g=base[:,1:2]
            w=sat(sat(g*(1-c[9,0])+c[9,0]*remap(noise[:,1:2],10))+clampcb(remap(t(2)[:,1:2],6),7,8))
            tint=c[11,:3]+c[12,:3]*sat(g)
            if h == "8113D1B6":
                w=clampcb(remap(w,16),14,15)
                target=base
            else:
                above=uv[:,1:2]>1
                tint=np.where(above,c[13,:3]+c[14,:3]*sat(g),tint)
                i=18 if h=="8113C94B" else 20
                w=np.where(above,clampcb(remap(w,i+3),i+1,i+2),clampcb(remap(w,i),i-2,i-1))
                target=base if h=="8113C94B" else c[15,:3]+c[16,:3]*sat(g)
            color=mix(tint,target,w)
            q=transform(uv,0)
            detail=c[1,:3]+c[2,:3]*sat(t(1,q)[:,0:1])
            m=sat(c[4,0]*sat(remap(t(3,q)[:,0:1],5))+(1-c[4,0])*ins[:,3:4])
            rgb=mix(color,detail,m)*noise
        elif f == "graded_albedo":
            x=t(0)[:,:3]
            if h == "8113D448":
                x=mix(x,x*c[8,:3],x[:,2:3]); gain,contrast,lo,hi,tint,saturation,atten,exponent=9,10,11,12,8,13,14,15
            else:
                gain,contrast,lo,hi,tint,saturation,atten,exponent=5,6,7,8,4,9,5,10
            x=clampcb(x*c[gain,0]*c[contrast,0]+c[contrast,1],lo,hi)*c[tint,:3]
            luma=x@np.array([.300000012,.589999974,.109999999],dtype=np.float32)
            x=luma[:,None]+c[saturation,0]*(x-luma[:,None])
            rgb=x*min(1,float(max(0,c[atten,0]))**float(c[exponent,0]))
        elif f == "palette_masks":
            idx=10 if h=="80B4F7C0" else 11
            q=transform(uv,8) if h=="80B4F7C0" else affine(uv,8,9)
            m=t(1,q); a=c[idx,:3]+c[idx+1,:3]*sat(remap(m[:,1:2],idx-1))
            rgb=mix(mix(a,c[idx+2,:3],m[:,0:1]),c[idx+3,:3],m[:,2:3])*sat(remap(t(0,transform(uv,5))[:,1:2],7))
        elif f == "world_detail":
            q=transform(world,1)
            rgb=t(2,transform(uv,5))[:,:3]*sat((t(0,transform(q,2))[:,:3]+c[0,:3])*(t(1,transform(q,4))[:,:3]+c[3,:3]))
        elif f == "world_dye":
            q=t(1,affine(uv,0,1)); w=sat(remap(t(1,transform(world,2))[:,3:4],3))
            a=c[6,:3]+c[7,:3]*sat(w+remap(q[:,3:4],5)); b=c[8,:3]+c[9,:3]*sat(q[:,1:2]); m=t(0)
            rgb=mix(c[4,:3],mix(a,b,m[:,0:1]),sat(remap(m[:,1:2],10)))
        elif f == "world_tint": rgb=t(0,transform(world,0))[:,:3]*c[1,:3]
        elif f == "uv_tint": rgb=t(0)[:,:3]*c[5,:3]
        elif f == "direct_albedo": rgb=t(0)[:,:3]
        elif f == "instance_layers":
            a=sat(remap(sat(t(2,transform(uv,3))[:,0:1]*c[4,0]+ins[:,0:1]*(1-c[4,0])),5))
            q=t(1,transform(uv,0))
            b=sat(remap(sat(c[2,3]*q[:,3:4]*c[6,0]+ins[:,3:4]*(1-c[6,0])),7))
            rgb=mix(t(0)[:,:3]*c[1,:3],q[:,:3]*c[2,:3],b)*mix(c[1,:3],t(3)[:,:3],a)
        elif f == "affine_dye":
            q=sat(t(2,affine(uv,3,4))[:,0:1]); rgb=t(0)[:,:3]*mix(c[0,:3]+c[1,:3]*q,c[2,:3],t(1)[:,0:1])
        elif f == "affine_additive":
            q_uv=affine(uv,4,5); q=t(1,q_uv); red=t(1,q_uv,2)[:,0:1]
            rgb=(c[0,:3]+c[1,:3]*sat(red))*remap(q[:,1:2],2)+remap(t(0)[:,1:2],3)
        elif f == "normal_layers":
            w=sat(c[21,0]*sat(remap(t(6)[:,0:1],18))*remap((normal@c[19,:3])[:,None],20))
            a=sat(remap(ins[:,2:3],4)); q=affine(uv,2,3); q2=affine(affine(uv,0,1),2,3)
            fg=mix(mix(t(0,q2)[:,:3],t(0,q)[:,:3],a),c[5,:3],c[6,0])
            bg=c[15,:3]*t(4,affine(uv,13,14))[:,:3];rgb=mix(bg,fg,w)
        elif f == "complex_dye_layers":
            q=transform(uv,0); n0=t(0)[:,1:2]; detail=t(1,q)[:,0:1]
            base=(c[2,:3]+c[3,:3]*sat(remap(n0,1)))*t(2,q)[:,:3]+t(3)[:,:3]
            dye=c[5,:3]+c[6,:3]*sat(remap(n0,4))+(c[8,:3]+c[9,:3]*sat(remap(detail,7)))*c[10,:3]*n0
            w=sat(ins[:,3:4]*c[23,0]+c[23,1]*mix(sat(remap(detail,24)),sat(remap(n0,25)),c[26,0]))
            rgb=mix(base,np.where(uv[:,1:2]>1,dye,base),w)
        elif f == "projected_decal":
            xyz=field("world_xyz",np.column_stack((uv,np.zeros(n))),3)
            norm=normal/np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-12)
            a=t(4,transform(xyz[:,1:3],1),2)[:,1:2]; b=t(4,transform(xyz[:,[0,2]],2),2)[:,1:2]
            w=sat(clampcb((norm@c[3,:3])[:,None],4,5)+clampcb((norm@c[6,:3])[:,None],7,8))
            q=mix(a,b,w); top=t(4,transform(xyz[:,:2],9),2)[:,1:2]
            w=np.minimum(1,sat((norm@c[10,:3])[:,None])+sat((norm@c[11,:3])[:,None]))
            q=mix(q,top,w)
            w=clampcb(remap(clampcb(remap(q,22),20,21)*clampcb(remap(t(3)[:,1:2],19),17,18),25),23,24)
            rgb=(c[15,:3]+c[16,:3]*sat(clampcb(remap(q,14),12,13)))*np.where(w>0,w,0)*sat(c[30,1])
            # This is only the isolated color contribution. Engine scene normal
            # t2.Load and depth/background compositing are outside basecolor.
        else:
            return np.zeros((n,3),np.float32),np.zeros((n,1),bool)
        valid=np.isfinite(rgb).all(axis=1,keepdims=True)
        if (missing or cb_missing) and not self.allow_representative: valid[:]=False
        return rgb.astype(np.float32),valid

    def sample(self, tag, uv, *, inputs=None):
        """Return (sRGB float32 Nx3, valid bool Nx1); inputs optionally supply
        world_xy/world_xyz Nx2/Nx3, normal Nx3, instance8 Nx4 (interpolated per-vertex TEXCOORD8; legacy API name), cb_overrides dict.
        NaN/inf UV and unknown/unsupported materials are invalid, no fallback.
        """
        tag=str(tag).upper()
        inputs=dict(inputs or {})
        if "world_xyz" in inputs and "world_xy" not in inputs:
            inputs["world_xy"]=np.asarray(inputs["world_xyz"],dtype=np.float32)[...,:2]
        uv=np.asarray(uv,dtype=np.float32)
        if uv.ndim!=2 or uv.shape[1]!=2: raise ValueError("uv must be Nx2")
        out=np.zeros((len(uv),3),np.float32); valid=np.zeros((len(uv),1),bool)
        if tag not in self.materials or not self.recipes[tag]["supported"]: return out,valid
        finite=np.isfinite(uv).all(axis=1)
        if not finite.any(): return out,valid
        selected={}
        for k,v in (inputs or {}).items():
            a=np.asarray(v) if k!="cb_overrides" else None
            selected[k]=a[finite] if a is not None and a.ndim==2 and len(a)==len(uv) else v
        try:
            self.last_errors.pop(tag,None)
            rgb,ok=self._evaluate(tag,uv[finite],selected)
            out[finite]=sat(linear_to_srgb(np.nan_to_num(rgb,nan=0,posinf=1,neginf=0)))
            valid[finite]=ok
        except (OSError,ValueError,KeyError,IndexError,NotImplementedError) as exc:
            self.last_errors[tag]=f"{type(exc).__name__}: {exc}"
        return out,valid

    def bake(self, tag, size=256, *, inputs=None, uv_bounds=(0,0,1,1)):
        """RGBA uint8 HxWx4. Alpha = sample validity; NOT source opacity.
        Repeat/unit swatch only. Some shaders encode dye selection in UV outside
        [0,1], so a unit tile cannot be assumed to repeat; sample geometry UVs.
        """
        size=int(size)
        if size<1: raise ValueError("size must be positive")
        x=(np.arange(size,dtype=np.float32)+.5)/size
        u,v=np.meshgrid(x,x)
        uv=np.stack((uv_bounds[0]+u.ravel()*(uv_bounds[2]-uv_bounds[0]),uv_bounds[1]+v.ravel()*(uv_bounds[3]-uv_bounds[1])),axis=1)
        rgb,valid=self.sample(tag,uv,inputs=inputs)
        return np.concatenate((np.rint(rgb*255).astype(np.uint8),valid.astype(np.uint8)*255),axis=1).reshape(size,size,4)


if __name__ == "__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("material_root");cli.add_argument("tag");cli.add_argument("output")
    cli.add_argument("--size",type=int,default=256);cli.add_argument("--representative",action="store_true")
    args=cli.parse_args();baker=MaterialBaker(args.material_root,allow_representative=args.representative)
    Image.fromarray(baker.bake(args.tag,args.size)).save(args.output)
    print(json.dumps(baker.recipes.get(args.tag.upper(),{}),ensure_ascii=False,indent=2))
    if baker.last_errors: raise SystemExit(json.dumps(baker.last_errors))
