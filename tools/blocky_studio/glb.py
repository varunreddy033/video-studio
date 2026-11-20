"""Minimal dependency-free glTF 2.0 (.glb) writer + low-poly geometry builders.

Only numpy + Pillow are needed. Units are metres, +Y up, models face +Z
(glTF convention), feet / base at y = 0.
"""
import io
import json
import math
import struct

import numpy as np

# --------------------------------------------------------------------------- geometry
# A geometry is a dict: pos (N,3) float32, nrm (N,3), uv (N,2), idx (M,) uint32


def _geom(pos, nrm, uv, idx):
    return {
        "pos": np.asarray(pos, np.float32).reshape(-1, 3),
        "nrm": np.asarray(nrm, np.float32).reshape(-1, 3),
        "uv": np.asarray(uv, np.float32).reshape(-1, 2),
        "idx": np.asarray(idx, np.uint32).reshape(-1),
    }


_FACES = {  # name: (normal, u axis, v axis)
    "front": ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    "back": ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
    "right": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "left": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "top": ((0, 1, 0), (1, 0, 0), (0, 0, -1)),
    "bottom": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
}
ALL_FACES = tuple(_FACES)


def box(w, h, d, faces=ALL_FACES):
    """Axis-aligned box centred on the origin. Each face gets full 0..1 UVs."""
    half = np.array([w, h, d], np.float32) / 2
    pos, nrm, uv, idx = [], [], [], []
    for f in faces:
        n, u, v = (np.array(a, np.float32) for a in _FACES[f])
        c = n * half
        hu = np.abs(u) @ half
        hv = np.abs(v) @ half
        base = len(pos)
        for su, sv, tu, tv in ((-1, -1, 0, 0), (1, -1, 1, 0), (1, 1, 1, 1), (-1, 1, 0, 1)):
            pos.append(c + u * su * hu + v * sv * hv)
            nrm.append(n)
            uv.append((tu, 1 - tv))
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]
    return _geom(pos, nrm, uv, idx)


def quad(w, h):
    """Flat quad in the XY plane facing +Z (for decals / signs)."""
    return box(w, h, 0.0, faces=("front",))


def cylinder(r, h, seg=16, r_top=None, caps=True):
    """Vertical cylinder / cone frustum, base at y=-h/2, top at y=+h/2."""
    r_top = r if r_top is None else r_top
    pos, nrm, uv, idx = [], [], [], []
    slope = (r - r_top) / h if h else 0
    for i in range(seg + 1):
        a = 2 * math.pi * i / seg
        ca, sa = math.cos(a), math.sin(a)
        n = np.array([sa, slope, ca]); n /= np.linalg.norm(n)
        pos += [(sa * r, -h / 2, ca * r), (sa * r_top, h / 2, ca * r_top)]
        nrm += [n, n]
        uv += [(i / seg, 1), (i / seg, 0)]
    for i in range(seg):
        a = 2 * i
        idx += [a, a + 2, a + 1, a + 1, a + 2, a + 3]
    if caps:
        for y, rr, ny in ((h / 2, r_top, 1), (-h / 2, r, -1)):
            if rr <= 0:
                continue
            c = len(pos)
            pos.append((0, y, 0)); nrm.append((0, ny, 0)); uv.append((0.5, 0.5))
            for i in range(seg + 1):
                a = 2 * math.pi * i / seg
                pos.append((math.sin(a) * rr, y, math.cos(a) * rr))
                nrm.append((0, ny, 0))
                uv.append((0.5 + 0.5 * math.sin(a), 0.5 + 0.5 * math.cos(a)))
            for i in range(seg):
                if ny > 0:
                    idx += [c, c + 1 + i, c + 2 + i]
                else:
                    idx += [c, c + 2 + i, c + 1 + i]
    return _geom(pos, nrm, uv, idx)


def cone(r, h, seg=16):
    return cylinder(r, h, seg, r_top=0.0)


def sphere(r, seg=16, rings=10, squash=1.0):
    pos, nrm, uv, idx = [], [], [], []
    for j in range(rings + 1):
        t = math.pi * j / rings
        for i in range(seg + 1):
            p = 2 * math.pi * i / seg
            n = np.array([math.sin(t) * math.sin(p), math.cos(t), math.sin(t) * math.cos(p)])
            pos.append(n * r * np.array([1, squash, 1]))
            nrm.append(n)
            uv.append((i / seg, j / rings))
    for j in range(rings):
        for i in range(seg):
            a = j * (seg + 1) + i
            b = a + seg + 1
            idx += [a, b, a + 1, a + 1, b, b + 1]
    return _geom(pos, nrm, uv, idx)


def hemisphere(r, seg=16, rings=6, squash=1.0):
    """Upper half sphere, flat side at y=0 (mushroom caps, bushes, domes)."""
    pos, nrm, uv, idx = [], [], [], []
    for j in range(rings + 1):
        t = (math.pi / 2) * j / rings
        for i in range(seg + 1):
            p = 2 * math.pi * i / seg
            n = np.array([math.sin(t) * math.sin(p), math.cos(t), math.sin(t) * math.cos(p)])
            pos.append(n * r * np.array([1, squash, 1]))
            nrm.append(n)
            uv.append((i / seg, j / rings))
    for j in range(rings):
        for i in range(seg):
            a = j * (seg + 1) + i
            b = a + seg + 1
            idx += [a, b, a + 1, a + 1, b, b + 1]
    c = len(pos)  # flat underside disc
    pos.append((0, 0, 0)); nrm.append((0, -1, 0)); uv.append((0.5, 0.5))
    for i in range(seg + 1):
        p = 2 * math.pi * i / seg
        pos.append((math.sin(p) * r, 0, math.cos(p) * r)); nrm.append((0, -1, 0))
        uv.append((0.5 + 0.5 * math.sin(p), 0.5 + 0.5 * math.cos(p)))
    for i in range(seg):
        idx += [c, c + 2 + i, c + 1 + i]
    return _geom(pos, nrm, uv, idx)


def torus(R, r, seg=24, tube=8):
    pos, nrm, uv, idx = [], [], [], []
    for j in range(tube + 1):
        v = 2 * math.pi * j / tube
        for i in range(seg + 1):
            u = 2 * math.pi * i / seg
            c = np.array([math.cos(u) * R, 0, math.sin(u) * R])
            n = np.array([math.cos(u) * math.cos(v), math.sin(v), math.sin(u) * math.cos(v)])
            pos.append(c + n * r); nrm.append(n); uv.append((i / seg, j / tube))
    for j in range(tube):
        for i in range(seg):
            a = j * (seg + 1) + i
            b = a + seg + 1
            idx += [a, a + 1, b, a + 1, b + 1, b]
    return _geom(pos, nrm, uv, idx)


def _rot_matrix(rx=0.0, ry=0.0, rz=0.0):
    rx, ry, rz = (math.radians(a) for a in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def transform(g, t=(0, 0, 0), r=(0, 0, 0), s=(1, 1, 1)):
    """Scale, then rotate (degrees, XYZ), then translate. Returns a new geometry."""
    s = np.array(s, np.float32)
    R = _rot_matrix(*r).astype(np.float32)
    pos = (g["pos"] * s) @ R.T + np.array(t, np.float32)
    nrm = (g["nrm"] / np.where(s == 0, 1, s)) @ R.T
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = nrm / np.where(ln == 0, 1, ln)
    out = dict(g, pos=pos.astype(np.float32), nrm=nrm.astype(np.float32))
    if np.prod(np.sign(s)) < 0:  # mirrored: flip winding
        out["idx"] = g["idx"].reshape(-1, 3)[:, ::-1].reshape(-1).copy()
    return out


def merge(geoms):
    pos, nrm, uv, idx, off = [], [], [], [], 0
    for g in geoms:
        pos.append(g["pos"]); nrm.append(g["nrm"]); uv.append(g["uv"])
        idx.append(g["idx"] + off); off += len(g["pos"])
    return _geom(np.concatenate(pos), np.concatenate(nrm), np.concatenate(uv), np.concatenate(idx))


# --------------------------------------------------------------------------- materials


class Mat:
    """PBR material. color = hex '#rrggbb' or rgb tuple 0..1. tex = PIL image."""

    def __init__(self, name, color="#ffffff", tex=None, emissive=None, emissive_strength=1.0,
                 rough=0.8, metal=0.0, alpha=None, double=False, unlit=False):
        self.name, self.tex, self.rough, self.metal = name, tex, rough, metal
        self.color = hex_rgb(color)
        self.emissive = hex_rgb(emissive) if emissive else None
        self.emissive_strength = emissive_strength
        self.alpha, self.double, self.unlit = alpha, double, unlit


def hex_rgb(c):
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(c)


def srgb_to_linear(c):
    return tuple(((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c)


# --------------------------------------------------------------------------- scene graph


class Node:
    def __init__(self, name, t=(0, 0, 0), r=(0, 0, 0), s=(1, 1, 1)):
        self.name, self.t, self.r, self.s = name, t, r, s
        self.prims = {}  # mat name -> (Mat, [geoms])
        self.children = []
        self.extras = {}

    def add(self, geom, mat, t=(0, 0, 0), r=(0, 0, 0), s=(1, 1, 1)):
        g = transform(geom, t, r, s)
        self.prims.setdefault(mat.name, (mat, []))[1].append(g)
        return self

    def child(self, name, t=(0, 0, 0), r=(0, 0, 0), s=(1, 1, 1)):
        n = Node(name, t, r, s)
        self.children.append(n)
        return n

    def attach(self, node):
        self.children.append(node)
        return node

    def bounds(self, M=None):
        M = np.eye(4) if M is None else M
        L = np.eye(4)
        L[:3, :3] = _rot_matrix(*self.r) * np.array(self.s)
        L[:3, 3] = self.t
        W = M @ L
        pts = []
        for _, gs in self.prims.values():
            for g in gs:
                p = np.c_[g["pos"], np.ones(len(g["pos"]))] @ W.T
                pts.append(p[:, :3])
        for c in self.children:
            b = c.bounds(W)
            if b is not None:
                pts.append(np.array(b))
        if not pts:
            return None
        p = np.concatenate(pts)
        return [p.min(0).tolist(), p.max(0).tolist()]


def _quat(rx, ry, rz):
    R = _rot_matrix(rx, ry, rz)
    w = math.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    if w < 1e-6:
        # fallback via largest diagonal
        i = int(np.argmax(np.diag(R)))
        j, k = (i + 1) % 3, (i + 2) % 3
        q = [0, 0, 0, 0]
        s = math.sqrt(max(0.0, 1 + R[i, i] - R[j, j] - R[k, k])) * 2
        q[i] = s / 4
        q[j] = (R[j, i] + R[i, j]) / s
        q[k] = (R[k, i] + R[i, k]) / s
        q[3] = (R[k, j] - R[j, k]) / s
        return q
    x = (R[2, 1] - R[1, 2]) / (4 * w)
    y = (R[0, 2] - R[2, 0]) / (4 * w)
    z = (R[1, 0] - R[0, 1]) / (4 * w)
    return [x, y, z, w]


# --------------------------------------------------------------------------- writer


def write_glb(root, path, extras=None):
    gl = {"asset": {"version": "2.0", "generator": "blocky_assets/tools/glb.py"},
          "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [], "meshes": [], "materials": [],
          "accessors": [], "bufferViews": [], "buffers": []}
    if extras:
        gl["scenes"][0]["extras"] = extras
    blob = bytearray()
    mat_index, tex_index = {}, {}
    used_ext = set()

    def view(data, target=None):
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob.extend(data)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            bv["target"] = target
        gl["bufferViews"].append(bv)
        return len(gl["bufferViews"]) - 1

    def accessor(arr, comp, typ, target, minmax=False):
        a = {"bufferView": view(arr.tobytes(), target), "componentType": comp,
             "count": len(arr), "type": typ}
        if minmax:
            a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
        gl["accessors"].append(a)
        return len(gl["accessors"]) - 1

    def texture(img):
        key = id(img)
        if key in tex_index:
            return tex_index[key]
        buf = io.BytesIO(); img.save(buf, "PNG")
        gl.setdefault("images", []).append({"bufferView": view(buf.getvalue()), "mimeType": "image/png"})
        gl.setdefault("samplers", [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}])
        gl.setdefault("textures", []).append({"source": len(gl["images"]) - 1, "sampler": 0})
        tex_index[key] = len(gl["textures"]) - 1
        return tex_index[key]

    def material(m):
        if m.name in mat_index:
            return mat_index[m.name]
        pbr = {"baseColorFactor": list(srgb_to_linear(m.color)) + [1.0 if m.alpha is None else m.alpha],
               "metallicFactor": m.metal, "roughnessFactor": m.rough}
        md = {"name": m.name, "pbrMetallicRoughness": pbr}
        if m.tex is not None:
            pbr["baseColorTexture"] = {"index": texture(m.tex)}
            if m.tex.mode == "RGBA":
                md["alphaMode"] = "MASK"; md["alphaCutoff"] = 0.5
        if m.alpha is not None and m.alpha < 1:
            md["alphaMode"] = "BLEND"
        if m.emissive:
            md["emissiveFactor"] = list(srgb_to_linear(m.emissive))
            if m.tex is not None:
                md["emissiveTexture"] = {"index": texture(m.tex)}
            if m.emissive_strength != 1.0:
                md.setdefault("extensions", {})["KHR_materials_emissive_strength"] = {
                    "emissiveStrength": m.emissive_strength}
                used_ext.add("KHR_materials_emissive_strength")
        if m.double:
            md["doubleSided"] = True
        if m.unlit:
            md.setdefault("extensions", {})["KHR_materials_unlit"] = {}
            used_ext.add("KHR_materials_unlit")
        gl["materials"].append(md)
        mat_index[m.name] = len(gl["materials"]) - 1
        return mat_index[m.name]

    def emit(node):
        i = len(gl["nodes"])
        nd = {"name": node.name}
        gl["nodes"].append(nd)
        if any(v != 0 for v in node.t):
            nd["translation"] = [float(v) for v in node.t]
        if any(v != 0 for v in node.r):
            nd["rotation"] = [float(v) for v in _quat(*node.r)]
        if any(v != 1 for v in node.s):
            nd["scale"] = [float(v) for v in node.s]
        if node.extras:
            nd["extras"] = node.extras
        if node.prims:
            prims = []
            for mname, (m, geoms) in node.prims.items():
                g = merge(geoms)
                attrs = {"POSITION": accessor(g["pos"], 5126, "VEC3", 34962, True),
                         "NORMAL": accessor(g["nrm"], 5126, "VEC3", 34962),
                         "TEXCOORD_0": accessor(g["uv"], 5126, "VEC2", 34962)}
                prims.append({"attributes": attrs, "indices": accessor(g["idx"], 5125, "SCALAR", 34963),
                              "material": material(m)})
            gl["meshes"].append({"name": node.name, "primitives": prims})
            nd["mesh"] = len(gl["meshes"]) - 1
        kids = [emit(c) for c in node.children]
        if kids:
            nd["children"] = kids
        return i

    emit(root)
    if used_ext:
        gl["extensionsUsed"] = sorted(used_ext)
    while len(blob) % 4:
        blob.append(0)
    gl["buffers"].append({"byteLength": len(blob)})
    js = json.dumps(gl, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js
    out += struct.pack("<II", len(blob), 0x004E4942) + bytes(blob)
    with open(path, "wb") as f:
        f.write(out)
    return len(out)
