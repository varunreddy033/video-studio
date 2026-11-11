"""
build_icon_index.py  -  the search index of the icon library (docs/ASSET_PACKS_PLAN.md step 2)

    bin/python tools/build_icon_index.py           build if the imported packs changed (also downloads the model)
    bin/python tools/build_icon_index.py --force   build anyway

Writes assets/library/icons/index.json and embeddings.npy (not in git). The render rebuilds them by itself when the
packs change; setup.sh runs this once so the first video doesn't wait for it. Model: all-MiniLM-L6-v2 (Apache-2.0),
pinned revision, ~90 MB in ~/.cache/huggingface.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import icon_index as X  # noqa: E402
from pipeline.util import PipelineError  # noqa: E402

try:
    if "--force" not in sys.argv and X.is_current():
        print("icon index: up to date")
    else:
        t = time.time()
        r = X.build()
        print(f"icon index: {r['count']:,} icons from {', '.join(r['sets'])} in {time.time() - t:.0f} s")
except PipelineError as e:
    print(f"ERROR {e}")
    sys.exit(1)
