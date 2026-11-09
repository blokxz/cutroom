"""Read-only protection for a client's original material.

Every client lists the folders that hold its originals as `source_folders`. Those are machine-specific
absolute paths, so they belong in the git-ignored clients/<slug>/client.local.json (same keys as
client.json, merged over it); a `source_folders` key in client.json is still honoured:

    clients/<slug>/client.local.json:   {"source_folders": ["/home/me/Downloads/Hotel Sol photos"]}

Nothing in cutroom may write, move or delete inside those folders. Extra folders can be protected for a
process with CUTROOM_READONLY (os.pathsep-separated). Any tool that writes calls ensure_writable() first:

    from media.guard import ensure_writable
    ensure_writable(out_path)            # raises ReadOnlyPathError if out_path is protected

Entries are stripped of surrounding whitespace and must be absolute paths (after '~' expansion). A relative
`source_folders` entry is still protected, resolved against the client folder (and `brief.py check` reports
it as an error); a relative CUTROOM_READONLY entry raises GuardConfigError, so every write fails until the
variable is fixed. Paths are compared after resolving symlinks and '..' (os.path.realpath), and
case-insensitively on macOS and Windows, whose default file systems ignore case. A path that does not exist
yet is resolved through its existing parents, so a symlinked parent directory pointing into a source folder
is caught too.

CLI:  python3 tools/material.py guard <path>...   (prints PROTECTED / writable per path)
"""
import glob
import json
import os
import sys

ENV_READONLY = "CUTROOM_READONLY"
CLIENT_FILE = "client.json"
LOCAL_FILE = "client.local.json"


class ReadOnlyPathError(PermissionError):
    """Raised when a write would land inside a protected (read-only) folder."""


class GuardConfigError(ReadOnlyPathError):
    """The protection itself is misconfigured (e.g. a relative CUTROOM_READONLY entry): refuse every write."""


def _root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def clients_dir():
    return os.environ.get("CUTROOM_CLIENTS") or os.path.join(_root(), "clients")


def _case_insensitive():
    return sys.platform == "darwin" or sys.platform.startswith("win") or os.name == "nt"


def _norm(path):
    p = os.path.realpath(os.path.expanduser(str(path).strip()))
    return os.path.normcase(p).casefold() if _case_insensitive() else p


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def load_client(cdir):
    """client.json with client.local.json merged over it (top-level keys); {} when neither is readable."""
    data = dict(_read_json(os.path.join(cdir, CLIENT_FILE)) or {})
    data.update(_read_json(os.path.join(cdir, LOCAL_FILE)) or {})
    return data


def source_folder_entries(cdir):
    """[(entry, origin file)] of the non-empty `source_folders` strings in client.json and client.local.json."""
    out = []
    for name in (CLIENT_FILE, LOCAL_FILE):
        data = _read_json(os.path.join(cdir, name)) or {}
        folders = data.get("source_folders")
        if isinstance(folders, list):
            out += [(p.strip(), name) for p in folders if isinstance(p, str) and p.strip()]
    return out


def is_absolute(entry):
    return os.path.isabs(os.path.expanduser(entry.strip()))


def protected_folders(extra=()):
    """[(normalised real path, reason)] for every source folder of every client, CUTROOM_READONLY and `extra`."""
    out = []
    dirs = {os.path.dirname(p) for pat in (CLIENT_FILE, LOCAL_FILE)
            for p in glob.glob(os.path.join(clients_dir(), "*", pat))}
    for cdir in sorted(dirs):
        slug = os.path.basename(cdir)
        for p, origin in source_folder_entries(cdir):
            if not is_absolute(p):
                p = os.path.join(cdir, p)  # relative: protect it where it would resolve, never drop it
            out.append((_norm(p), f"source folder of client '{slug}' ({origin})"))
    for p in (os.environ.get(ENV_READONLY) or "").split(os.pathsep):
        if not p.strip():
            continue
        if not is_absolute(p):
            raise GuardConfigError(f"{ENV_READONLY} entries must be absolute paths, got {p.strip()!r}: "
                                   f"refusing every write until it is fixed")
        out.append((_norm(p), ENV_READONLY))
    for p in extra:
        if p and str(p).strip():
            out.append((_norm(p), "source of this run"))
    return out


def _inside(path, folder):
    return path == folder or path.startswith(folder.rstrip(os.sep) + os.sep)


def protecting_folder(path, extra=()):
    """(folder, reason) protecting `path`, or None if it is writable."""
    p = _norm(path)
    for folder, reason in protected_folders(extra):
        if _inside(p, folder):
            return folder, reason
    return None


def is_protected(path, extra=()):
    return protecting_folder(path, extra) is not None


def ensure_writable(path, extra=(), action="write"):
    """Return `path` unchanged, or raise ReadOnlyPathError if it resolves inside a protected folder."""
    hit = protecting_folder(path, extra)
    if hit:
        folder, reason = hit
        raise ReadOnlyPathError(
            f"refusing to {action} '{path}': it is inside '{folder}' ({reason}), which is read-only. "
            f"Write into the client folder (clients/<slug>/...) instead."
        )
    return path
