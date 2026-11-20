"""Check the per-style script kits (pipeline/config.py SCRIPT_KITS): every picture style has a prompt and a sample,
the files exist, each prompt's header template names its own rendering_method, and every sample passes Check with
0 errors as that style, both as a full video and behind "Make Short" (type: short added like the UI does).
Prints "script kits: clean" or the problems. Run from the repo root: bin/python tools/check_script_kits.py"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C           # noqa: E402
from pipeline import script_parser as P    # noqa: E402


def as_short(text):
    # same as ui/index.html withType(): a script behind "Make Short" gets type: short unless the header has a type
    if not re.match(r"---\r?\n", text):
        return text
    end = text.find("\n---", 3)
    head = text[:end] if end > 0 else text
    return text if re.search(r"^type\s*:", head, re.M) else re.sub(r"^---\r?\n", "---\ntype: short\n", text, count=1)


def main():
    problems = []
    missing = set(C.RENDERING_METHODS) - set(C.SCRIPT_KITS)
    if missing:
        problems.append(f"no script kit for: {', '.join(sorted(missing))}")
    for method in C.SCRIPT_KITS:
        for kind in ("full", "short"):
            kit = C.script_kit(method, kind)
            if not kit["prompts"]:
                problems.append(f"{method}/{kind}: no prompt")
            for p in kit["prompts"]:
                f = C.SCRIPT_PROMPTS_DIR / f"{p['id']}.md"
                if not f.is_file():
                    problems.append(f"{method}/{kind}: prompt file missing: {f.relative_to(C.BASE_DIR)}")
                elif not re.search(rf"^rendering_method: {method}$", f.read_text(encoding="utf-8"), re.M):
                    problems.append(f"{f.relative_to(C.BASE_DIR)}: header template has no 'rendering_method: {method}'")
            f = C.BASE_DIR / "docs" / kit["sample"]
            if not f.is_file():
                problems.append(f"{method}/{kind}: sample missing: docs/{kit['sample']}")
                continue
            text = f.read_text(encoding="utf-8")
            r = P.parse(as_short(text) if kind == "short" else text)
            got = r["stats"].get("rendering_method")
            if got != method:
                problems.append(f"docs/{kit['sample']} ({kind}): Check gives rendering_method {got}, not {method}")
            for e in r["errors"]:
                problems.append(f"docs/{kit['sample']} ({kind}) line {e['line']}: {e['msg']}")
            warns = len(r["warnings"])
            print(f"{method:12} {kind:5} docs/{kit['sample']}: ok, {warns} warning{'s' * (warns != 1)}, "
                  f"~{r['stats'].get('est_seconds', 0):.0f} s, prompts: {', '.join(p['id'] for p in kit['prompts'])}")
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("script kits: clean")


if __name__ == "__main__":
    main()
