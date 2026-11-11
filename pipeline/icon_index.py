"""Search index of the icon library (docs/ASSET_PACKS_PLAN.md step 2).

  assets/library/icons/index.json      one row per icon: id, set, name, words, category, licence, has_colour, char
  assets/library/icons/embeddings.npy  one all-MiniLM-L6-v2 sentence vector per row (float16, unit length)

Words come from the icon's name plus, for emoji, the emoji's Unicode name (unicode-emoji-json, MIT) and keywords
(emojilib, MIT). Both files are rebuilt automatically when the imported packs change (ensure()); nothing is in git.
The model is pinned to one revision and runs on the CPU, and scores are rounded, so the same words always find the
same icons.
"""

import hashlib
import json
import re
from functools import lru_cache

from . import config as C
from . import icon_library as L
from .util import PipelineError

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REV = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"       # Apache-2.0; pinned so every machine embeds the same
MODEL_FILES = ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json", "vocab.txt",
               "special_tokens_map.json"]
VERSION = 3                                                   # bump when the row format or the texts change
NODE = C.BASE_DIR / "node_modules"


# ---------------------------------------------------------------- the model
def model_dir(download: bool = True) -> str:
    from huggingface_hub import snapshot_download
    try:
        return snapshot_download(MODEL, revision=MODEL_REV, allow_patterns=MODEL_FILES, local_files_only=True)
    except Exception:  # noqa: BLE001  (not downloaded yet)
        if not download:
            raise PipelineError("the icon search model isn't downloaded yet. Run once in the project folder: "
                                "bin/python tools/build_icon_index.py")
        return snapshot_download(MODEL, revision=MODEL_REV, allow_patterns=MODEL_FILES)


@lru_cache(maxsize=1)
def _model():
    import torch
    from transformers import AutoModel, AutoTokenizer
    from transformers.utils import logging as tlog
    tlog.set_verbosity_error()
    tlog.disable_progress_bar()
    d = model_dir()
    tok = AutoTokenizer.from_pretrained(d)
    net = AutoModel.from_pretrained(d).to("cpu").eval()
    return torch, tok, net


def embed(texts: list):
    """Unit-length sentence vectors (float32 numpy, one row per text): mean pooling, as the model card does."""
    import numpy as np
    torch, tok, net = _model()
    out = []
    for i in range(0, len(texts), 128):
        enc = tok(texts[i:i + 128], padding=True, truncation=True, max_length=48, return_tensors="pt")
        with torch.no_grad():
            hid = net(**enc).last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).float()
        vec = (hid * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        out.append(torch.nn.functional.normalize(vec, dim=1).numpy())
    return np.concatenate(out) if out else np.zeros((0, 384), dtype="float32")


# ---------------------------------------------------------------- building
def _emoji_data():
    kw = json.loads((NODE / "emojilib" / "dist" / "emoji-en-US.json").read_text(encoding="utf-8"))
    uni = json.loads((NODE / "unicode-emoji-json" / "data-by-emoji.json").read_text(encoding="utf-8"))
    strip = lambda s: s.replace("️", "")                  # noqa: E731
    return {strip(k): v for k, v in kw.items()}, {strip(k): v for k, v in uni.items()}


def _chars(npm: str) -> dict:
    """icon name -> emoji character, from the package's chars.json (code points -> name)."""
    p = L.NPM_DIR / npm / "chars.json"
    if not p.exists():
        return {}
    out = {}
    for code, name in json.loads(p.read_text(encoding="utf-8")).items():
        try:
            ch = "".join(chr(int(c, 16)) for c in code.split("-"))
        except ValueError:
            continue
        out.setdefault(name, ch.replace("️", ""))
    return out


def _words(*parts) -> list:
    seen, out = set(), []
    for part in parts:
        for w in re.findall(r"[a-z0-9]+", str(part).lower().replace("_", " ")):
            if w not in seen and len(w) > 1 or w.isdigit() and w not in seen:
                seen.add(w)
                out.append(w)
    return out


def _countries() -> dict:
    """ISO 3166 two-letter code -> country name, from the flag emoji names."""
    _, uni = _emoji_data()
    out = {}
    for ch, row in uni.items():
        if row.get("group") == "Flags" and len(ch) == 2 and all(0x1F1E6 <= ord(c) <= 0x1F1FF for c in ch):
            out["".join(chr(ord(c) - 0x1F1E6 + 97) for c in ch)] = row["name"].replace("flag ", "")
    return out


def rows() -> list:
    kw, uni = _emoji_data()
    countries = _countries()
    out = []
    for set_id in L.installed():
        pack = L.load(set_id)
        spec = L.PACKS[set_id]
        chars = _chars(spec["npm"]) if spec.get("emoji") else {}
        for name in sorted(pack["icons"]):
            ic = pack["icons"][name]
            row = {"id": f"{set_id}:{name}", "set": set_id, "name": name, "licence": pack["licence"],
                   "has_colour": "currentColor" not in ic["b"], "char": "", "category": spec["role"]}
            if spec.get("emoji"):
                ch = chars.get(name, "")
                u = uni.get(ch, {})
                row["char"] = ch
                row["category"] = u.get("group", "Emoji")
                row["words"] = _words(name, u.get("name", ""), " ".join(kw.get(ch, [])))
                row["text"] = f"{name.replace('-', ' ')}: " + ", ".join(kw.get(ch, []) or [u.get("name", name)])
            elif set_id == "flags":
                code = name[:-4]
                country = countries.get(code, code)
                row["category"] = "Flags"
                row["words"] = _words(country, code, "flag")
                row["text"] = f"flag of {country}"
            elif set_id == "natural_earth":
                row["category"] = "Map"
                row["words"] = _words(ic["name"], ic.get("iso", ""), "map country")
                row["text"] = f"map of {ic['name']}"
            else:
                base = re.sub(r"-(fill|duotone|filled)$", "", name)
                row["category"] = "Icon"
                row["words"] = _words(base)
                row["text"] = base.replace("-", " ")
            out.append(row)
    return out


def signature() -> str:
    parts = [f"v{VERSION}", MODEL_REV]
    for set_id in L.installed():
        p = L.ICONS_DIR / set_id / "icons.json"
        parts.append(f"{set_id}:{p.stat().st_size}:{p.open(encoding='utf-8').read(300)}")
    return hashlib.sha1("|".join(parts).encode()).hexdigest()


def build(log=print) -> dict:
    import numpy as np
    if not L.installed():
        raise PipelineError("no icon packs are imported. Run once in the project folder: npm ci && "
                            "bin/python tools/import_icon_packs.py")
    data = rows()
    texts = sorted({r["text"] for r in data})
    log(f"icon index: {len(data):,} icons, {len(texts):,} different descriptions to embed")
    vecs = embed(texts)
    at = {t: i for i, t in enumerate(texts)}
    emb = np.stack([vecs[at[r["text"]]] for r in data]).astype("float16")
    np.save(L.EMBED, emb)
    for r in data:
        del r["text"]
    L.INDEX.write_text(json.dumps({"signature": signature(), "model": MODEL, "revision": MODEL_REV, "count": len(data),
                                   "icons": data}, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    load.cache_clear()
    return {"count": len(data), "sets": sorted({r["set"] for r in data})}


def is_current() -> bool:
    if not (L.INDEX.exists() and L.EMBED.exists()):
        return False
    return L.INDEX.open(encoding="utf-8").read(80).find(signature()) >= 0


def ensure(log=print) -> None:
    """Rebuilds the index when it is missing or the imported packs changed."""
    if not is_current():
        log("icon index: packs changed, rebuilding (about a minute)")
        build(log)


@lru_cache(maxsize=1)
def load():
    """(rows, embeddings float32, position by id)."""
    import numpy as np
    ensure(lambda *_: None)
    data = json.loads(L.INDEX.read_text(encoding="utf-8"))["icons"]
    emb = np.load(L.EMBED).astype("float32")
    if len(data) != len(emb):
        raise PipelineError("the icon index is damaged. Run: bin/python tools/build_icon_index.py --force")
    return data, emb, {r["id"]: i for i, r in enumerate(data)}


def scores(queries: list):
    """Cosine similarity of every query to every icon, rounded to 4 places (rows = queries)."""
    _, emb, _ = load()
    return (embed(queries) @ emb.T).round(4)


def search(query: str, sets=None, k: int = 10) -> list:
    """The k best icons for some words: [{id, score, words}], best first (ties by id)."""
    data, _, _ = load()
    sc = scores([query])[0]
    keep = [i for i, r in enumerate(data) if not sets or r["set"] in sets]
    keep.sort(key=lambda i: (-float(sc[i]), data[i]["id"]))
    return [{"id": data[i]["id"], "score": float(sc[i]), "words": data[i]["words"][:8]} for i in keep[:k]]
