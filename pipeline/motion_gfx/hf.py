"""Runs the pinned HyperFrames CLI (package.json -> node_modules/.bin/hyperframes) for the motion renderer, with
telemetry, update checks and skill installs switched off. Only local commands are used: check, snapshot, render."""

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from .. import config as C
from ..util import PipelineError

PINNED = json.loads((C.BASE_DIR / "package.json").read_text(encoding="utf-8"))["dependencies"]["hyperframes"]
BIN = C.BASE_DIR / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes")
GSAP_JS = C.BASE_DIR / "node_modules" / "gsap" / "dist" / "gsap.min.js"
MOTIONPATH_JS = C.BASE_DIR / "node_modules" / "gsap" / "dist" / "MotionPathPlugin.min.js"

ENV = {"HYPERFRAMES_NO_TELEMETRY": "1", "DO_NOT_TRACK": "1", "HYPERFRAMES_NO_UPDATE_CHECK": "1",
       "HYPERFRAMES_SKIP_SKILLS": "1", "NO_UPDATE_NOTIFIER": "1", "npm_config_update_notifier": "false"}


def _env():
    env = dict(os.environ, **ENV)
    if C.env("HYPERFRAMES_BROWSER_PATH"):
        env["HYPERFRAMES_BROWSER_PATH"] = C.env("HYPERFRAMES_BROWSER_PATH")
    return env


def check_installed() -> dict:
    """Node 22+, the pinned HyperFrames and GSAP in node_modules, FFmpeg. Raises PipelineError with the fix."""
    node = shutil.which("node")
    if not node:
        raise PipelineError("Node.js isn't installed. Install it once: brew install node  (needs 22 or newer)")
    v = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    m = re.match(r"v(\d+)", v)
    if not m or int(m.group(1)) < 22:
        raise PipelineError(f"Node.js {v} is too old; HyperFrames needs 22 or newer: brew upgrade node")
    if not BIN.exists() or not GSAP_JS.exists():
        raise PipelineError("HyperFrames isn't installed in this project. Run once in Terminal: "
                            "cd ~/youtube-pipeline && npm ci   (setup.sh does this too)")
    got = subprocess.run([str(BIN), "--version"], capture_output=True, text=True, env=_env()).stdout.strip()
    if got != PINNED:
        raise PipelineError(f"HyperFrames {got} is installed but this project is tested with {PINNED}: "
                            f"cd ~/youtube-pipeline && npm ci")
    if not shutil.which("ffmpeg"):
        raise PipelineError("FFmpeg isn't installed (brew install ffmpeg)")
    return {"node": v, "hyperframes": got}


def run(args, project: Path, log, what: str, timeout=1800):
    """Run `hyperframes <args>` inside the project folder. Returns (returncode, stdout, stderr)."""
    t0 = time.time()
    p = subprocess.run([str(BIN), *[str(a) for a in args]], cwd=str(project), capture_output=True, text=True,
                       env=_env(), timeout=timeout)
    log(f"    hyperframes {args[0]}: exit {p.returncode} in {time.time() - t0:.1f} s")
    (project / "logs").mkdir(exist_ok=True)
    with open(project / "logs" / f"hyperframes_{args[0]}.log", "a", encoding="utf-8") as f:
        f.write(f"\n=== {time.strftime('%H:%M:%S')} {what}: hyperframes {' '.join(map(str, args))}\n"
                f"{p.stdout[-20000:]}\n--- stderr\n{p.stderr[-20000:]}\n")
    return p.returncode, p.stdout, p.stderr


def json_out(stdout: str):
    """The JSON object a --json command printed (ignores any lines before it)."""
    i = stdout.find("{")
    if i < 0:
        return None
    try:
        return json.loads(stdout[i:])
    except ValueError:
        return None
