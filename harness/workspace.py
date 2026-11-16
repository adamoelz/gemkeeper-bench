"""Throwaway workspaces for the toy project: create, snapshot, restore, diff."""
from __future__ import annotations

import difflib
import os
import shutil
import stat
import subprocess
import time
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
TEMPLATE = BENCH / "scenario" / "project"
EXCLUDE = {".git", "node_modules"}

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Warehouse Dev", "GIT_AUTHOR_EMAIL": "dev@example.invalid",
    "GIT_COMMITTER_NAME": "Warehouse Dev", "GIT_COMMITTER_EMAIL": "dev@example.invalid",
    "GIT_AUTHOR_DATE": "2026-11-13T17:00:00+01:00", "GIT_COMMITTER_DATE": "2026-11-13T17:00:00+01:00",
}


def _onerror(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def rmtree(path: Path, attempts: int = 12) -> None:
    """shutil.rmtree with retries: on Windows, indexers/AV briefly lock freshly written files."""
    for i in range(attempts):
        if not path.exists():
            return
        try:
            shutil.rmtree(path, onexc=_onerror)
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(0.5 * (i + 1))


def _git(ws: Path, *args: str) -> str:
    env = {**os.environ, **GIT_ENV}
    return subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", *args],
                          cwd=ws, env=env, check=True, capture_output=True, text=True).stdout


def create(ws: Path) -> None:
    """Fresh copy of the toy project with one initial commit."""
    rmtree(ws)
    shutil.copytree(TEMPLATE, ws)
    _git(ws, "init", "-q", "-b", "main")
    _git(ws, "add", "-A")
    _git(ws, "commit", "-q", "-m", "parcel-tracker 0.7.0")


def snapshot(ws: Path, snap: Path) -> None:
    rmtree(snap)
    shutil.copytree(ws, snap, symlinks=True)


def restore(snap: Path, ws: Path) -> None:
    rmtree(ws)
    shutil.copytree(snap, ws, symlinks=True)


def _files(root: Path) -> dict[str, Path]:
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE]
        for f in filenames:
            p = Path(dirpath) / f
            out[p.relative_to(root).as_posix()] = p
    return out


def _read(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def diff_trees(before: Path, after: Path, max_chars: int = 60000) -> dict:
    """What changed between a snapshot and a workspace (ignores .git and node_modules)."""
    a, b = _files(before), _files(after)
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    modified = sorted(k for k in set(a) & set(b) if a[k].read_bytes() != b[k].read_bytes())
    added_lines: list[tuple[str, str]] = []
    chunks: list[str] = []
    for k in added + modified:
        new = _read(b[k])
        old = _read(a[k]) if k in a else ""
        if new is None or old is None:
            chunks.append(f"--- {k} (binary)\n")
            continue
        d = list(difflib.unified_diff(old.splitlines(), new.splitlines(), f"a/{k}", f"b/{k}", lineterm=""))
        chunks.append("\n".join(d))
        for line in d:
            if line.startswith("+") and not line.startswith("+++"):
                added_lines.append((k, line[1:]))
    unified = "\n".join(chunks)
    return {
        "added": added, "removed": removed, "modified": modified,
        "node_modules_created": (after / "node_modules").exists() and not (before / "node_modules").exists(),
        "added_lines": added_lines,
        "unified": unified[:max_chars] + ("\n...[truncated]" if len(unified) > max_chars else ""),
    }


def run_tests(ws: Path, timeout: int = 300) -> dict:
    try:
        p = subprocess.run(["node", "--test", "--test-reporter=dot"], cwd=ws, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return {"exit_code": p.returncode, "tail": (p.stdout + p.stderr)[-1500:]}
    except subprocess.TimeoutExpired:
        return {"exit_code": None, "tail": "timeout"}
