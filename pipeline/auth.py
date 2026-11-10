"""
auth.py  -  logins for Video Studio when it is reachable from the internet.

  data/users.json     {"users": {"name": {"hash": "<scrypt>", "admin": true, "created": 0}}}
  data/secret_key     random key that signs the login cookie (stays on this Mac)
  data/setup_code     one-time code for creating the first account (deleted once used)

Passwords are stored only as scrypt hashes. Failed logins are rate limited per address and per username.
"""

import json
import os
import re
import secrets
import threading
import time
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from . import config as C

DATA = C.BASE_DIR / "data"
DATA.mkdir(exist_ok=True)
os.chmod(DATA, 0o700)
USERS = DATA / "users.json"
SECRET = DATA / "secret_key"
SETUP = DATA / "setup_code"
NAME_RE = re.compile(r"[a-z0-9][a-z0-9._-]{2,31}")
MIN_PASSWORD = 10
MAX_FAILS, WINDOW, LOCK = 5, 15 * 60, 15 * 60   # 5 wrong tries in 15 min -> locked for 15 min

_lock = threading.Lock()
_fails: dict = {}      # key -> [timestamps]
_locked: dict = {}     # key -> unlock time


def _private_write(path: Path, text: str):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def secret_key() -> bytes:
    if not SECRET.exists():
        _private_write(SECRET, secrets.token_hex(32))
    return SECRET.read_text(encoding="utf-8").strip().encode()


def _load() -> dict:
    if not USERS.exists():
        return {"users": {}}
    return json.loads(USERS.read_text(encoding="utf-8"))


def _save(d: dict):
    _private_write(USERS, json.dumps(d, indent=1))


def has_users() -> bool:
    return bool(_load()["users"])


def users():
    return [{"name": n, "admin": u.get("admin", False), "created": u.get("created")} for n, u in _load()["users"].items()]


def is_admin(name: str) -> bool:
    return bool(_load()["users"].get(name, {}).get("admin"))


def exists(name: str) -> bool:
    return name in _load()["users"]


def check_new(name: str, password: str):
    if not NAME_RE.fullmatch(name or ""):
        return "username: 3-32 characters, lowercase letters, numbers, dot, dash or underscore"
    if len(password or "") < MIN_PASSWORD:
        return f"password must be at least {MIN_PASSWORD} characters"
    if password.lower() in (name, "password12", "1234567890", "qwertyuiop"):
        return "choose a less guessable password"
    return None


def create(name: str, password: str, admin: bool = False):
    err = check_new(name, password)
    if err:
        raise ValueError(err)
    with _lock:
        d = _load()
        if name in d["users"]:
            raise ValueError("that username already exists")
        d["users"][name] = {"hash": generate_password_hash(password, method="scrypt"), "admin": admin,
                            "created": time.time()}
        _save(d)


def delete(name: str):
    with _lock:
        d = _load()
        if name not in d["users"]:
            raise ValueError("no such user")
        if d["users"][name].get("admin") and sum(1 for u in d["users"].values() if u.get("admin")) == 1:
            raise ValueError("can't delete the last admin")
        del d["users"][name]
        _save(d)


def set_password(name: str, password: str):
    err = check_new(name, password)
    if err:
        raise ValueError(err)
    with _lock:
        d = _load()
        d["users"][name]["hash"] = generate_password_hash(password, method="scrypt")
        _save(d)


def _blocked(key: str) -> float:
    until = _locked.get(key, 0)
    return max(0.0, until - time.time())


LOCAL = {"127.0.0.1", "::1", "?", ""}   # the tunnel hides real visitor addresses; don't lump everyone together


def _ip_key(ip: str):
    return None if ip in LOCAL else "ip:" + ip


def locked_for(ip: str, name: str) -> float:
    with _lock:
        k = _ip_key(ip)
        return max(_blocked(k) if k else 0.0, _blocked("user:" + (name or "")))


def _fail(key: str):
    now = time.time()
    hist = [t for t in _fails.get(key, []) if now - t < WINDOW] + [now]
    _fails[key] = hist
    if len(hist) >= MAX_FAILS:
        _locked[key] = now + LOCK
        _fails[key] = []


def verify(ip: str, name: str, password: str) -> bool:
    """True if the password is right. Wrong tries count towards a lockout (checked by the caller)."""
    u = _load()["users"].get(name or "")
    # always run one hash check so a wrong username takes as long as a wrong password
    ok = check_password_hash(u["hash"] if u else _DUMMY, password or "")
    k = _ip_key(ip)
    if ok and u:
        with _lock:
            if k:
                _fails.pop(k, None)
            _fails.pop("user:" + name, None)
        return True
    with _lock:
        if k:
            _fail(k)
        _fail("user:" + (name or ""))
    return False


_DUMMY = generate_password_hash(secrets.token_hex(8), method="scrypt")


def setup_code() -> str:
    """One-time code needed to create the first account (shown in the server log on this Mac)."""
    if has_users():
        SETUP.unlink(missing_ok=True)
        return ""
    if not SETUP.exists():
        _private_write(SETUP, secrets.token_urlsafe(18))
    return SETUP.read_text(encoding="utf-8").strip()


def use_setup_code(code: str) -> bool:
    real = setup_code()
    return bool(real) and secrets.compare_digest(real, code or "")


def finish_setup():
    SETUP.unlink(missing_ok=True)
