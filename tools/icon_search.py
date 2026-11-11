"""
icon_search.py  -  try the icon search:  bin/python tools/icon_search.py "battery dies"

    --set fluent_flat      only that pack (repeat for more); default = every imported pack
    -n 20                  how many results (default 10)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import icon_index as X  # noqa: E402
from pipeline.util import PipelineError  # noqa: E402

args, sets, n, words = sys.argv[1:], [], 10, []
while args:
    a = args.pop(0)
    if a == "--set" and args:
        sets.append(args.pop(0))
    elif a == "-n" and args:
        n = int(args.pop(0))
    else:
        words.append(a)
if not words:
    print(__doc__)
    sys.exit(1)
try:
    for i, r in enumerate(X.search(" ".join(words), sets or None, n), 1):
        print(f"{i:>2}  {r['score']:.4f}  {r['id']:<44} {' '.join(r['words'])}")
except PipelineError as e:
    print(f"ERROR {e}")
    sys.exit(1)
