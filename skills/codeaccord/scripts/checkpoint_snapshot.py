#!/usr/bin/env python3
"""计算 CodeAccord checkpoint 的 Git 快照（git_head 与工作区指纹）。

只读命令行助手：不读取或写入 checkpoint，不保存 diff 内容。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

FINGERPRINT_PATHSPECS = (".", ":(exclude).codeaccord")


def _run_git(workspace: Path, *args: str) -> bytes | None:
    """运行不带外部 diff 的只读 Git 命令；非 Git 工作区返回 None。"""

    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def workspace_snapshot(workspace: Path) -> dict[str, str] | None:
    """计算 HEAD 与工作区指纹，不返回或保存实际 diff 内容。"""

    root_bytes = _run_git(workspace, "rev-parse", "--show-toplevel")
    head_bytes = _run_git(workspace, "rev-parse", "--verify", "HEAD")
    if root_bytes is None or head_bytes is None:
        return None

    root = Path(root_bytes.decode("utf-8", errors="surrogateescape").strip()).resolve()
    head = head_bytes.decode("ascii", errors="replace").strip()
    commands = (
        (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            *FINGERPRINT_PATHSPECS,
        ),
        (
            "diff",
            "--binary",
            "--no-ext-diff",
            "HEAD",
            "--",
            *FINGERPRINT_PATHSPECS,
        ),
        (
            "diff",
            "--cached",
            "--binary",
            "--no-ext-diff",
            "HEAD",
            "--",
            *FINGERPRINT_PATHSPECS,
        ),
    )
    digest = hashlib.sha256()
    digest.update(b"codeaccord-worktree-v1\0")
    digest.update(head.encode("ascii", errors="replace"))
    for command in commands:
        output = _run_git(root, *command)
        if output is None:
            return None
        digest.update(b"\0command\0")
        digest.update(" ".join(command).encode("utf-8"))
        digest.update(b"\0")
        digest.update(output)

    untracked = _run_git(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        *FINGERPRINT_PATHSPECS,
    )
    if untracked is None:
        return None
    for raw_path in sorted(path for path in untracked.split(b"\0") if path):
        digest.update(b"\0untracked\0")
        digest.update(raw_path)
        path = root / raw_path.decode("utf-8", errors="surrogateescape")
        try:
            if path.is_symlink():
                digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
                continue
            if not path.is_file():
                return None
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError:
            return None

    return {"git_head": head, "worktree_fingerprint": digest.hexdigest()}


def main() -> int:
    """输出工作区快照 JSON。"""

    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    snapshot = workspace_snapshot(workspace)
    if snapshot is None:
        print("Unable to calculate a Git workspace snapshot", file=sys.stderr)
        return 1
    json.dump(snapshot, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
