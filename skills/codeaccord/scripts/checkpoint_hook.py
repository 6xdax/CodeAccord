#!/usr/bin/env python3
"""校验并恢复 CodeAccord 的单一上下文 checkpoint。

Hook 只读 checkpoint：归属与 Git 新鲜度字段由 Agent 维护。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

CHECKPOINT_RELATIVE_PATH = Path(".codeaccord/checkpoint.md")
CHECKPOINT_VERSION = "1"
FINGERPRINT_PATHSPECS = (".", ":(exclude).codeaccord")
VALID_STATUSES = {"exploring", "approved", "implementing", "verifying"}
VALID_CHECKPOINT_REASONS = {
    "accord_confirmed",
    "delta_confirmed",
    "milestone",
    "precompact",
}
VERSIONED_FIELDS = (
    "workspace",
    "session",
    "language",
    "accord_revision",
    "git_head",
    "worktree_fingerprint",
    "checkpoint_reason",
)
REQUIRED_HEADINGS = (
    "# Goal",
    "## Confirmed scope",
    "## Non-goals",
    "## Current state",
    "## Next action",
    "## Acceptance checks",
    "## Unresolved",
)


def find_checkpoint(cwd: Path) -> Path | None:
    """从当前目录向上查找项目 checkpoint。"""

    current = cwd.resolve()
    for directory in (current, *current.parents):
        candidate = directory / CHECKPOINT_RELATIVE_PATH
        if candidate.is_file():
            return candidate
    return None


def frontmatter_lines(content: str) -> list[str]:
    """返回 frontmatter 行；缺少闭合分隔符时返回空列表。"""

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index]
    return []


def frontmatter_field(content: str, field: str) -> str | None:
    """读取 frontmatter 字段值，空值按缺失处理。"""

    prefix = f"{field}:"
    for line in frontmatter_lines(content):
        if line.startswith(prefix):
            value = line.partition(":")[2].strip()
            return value or None
    return None


class Freshness(NamedTuple):
    """Checkpoint 与当前工作区的一致性判断。"""

    state: str
    notes: tuple[str, ...] = ()
    blocks_manual: bool = False


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


def validate_checkpoint(content: str) -> list[str]:
    """检查恢复所需的最小结构，不判断自然语言内容。"""

    problems: list[str] = []
    status = frontmatter_field(content, "status")
    if status not in VALID_STATUSES:
        problems.append(
            "frontmatter status must be exploring, approved, implementing, or verifying"
        )
    if frontmatter_field(content, "updated") is None:
        problems.append("frontmatter updated timestamp is missing")
    if frontmatter_field(content, "checkpoint_version") is not None:
        if frontmatter_field(content, "checkpoint_version") != CHECKPOINT_VERSION:
            problems.append(
                f"frontmatter checkpoint_version must be {CHECKPOINT_VERSION}"
            )
        for field in VERSIONED_FIELDS:
            if frontmatter_field(content, field) is None:
                problems.append(f"frontmatter {field} is missing")
        revision = frontmatter_field(content, "accord_revision")
        try:
            revision_number = int(revision) if revision is not None else None
        except ValueError:
            revision_number = None
        if revision_number is None or revision_number < 0:
            problems.append("frontmatter accord_revision must be a non-negative integer")
        elif status != "exploring" and revision_number == 0:
            problems.append(
                "frontmatter accord_revision must be positive after Explore"
            )
        reason = frontmatter_field(content, "checkpoint_reason")
        if reason is not None and reason not in VALID_CHECKPOINT_REASONS:
            allowed = ", ".join(sorted(VALID_CHECKPOINT_REASONS))
            problems.append(f"frontmatter checkpoint_reason must be one of: {allowed}")
    for heading in REQUIRED_HEADINGS:
        if heading not in content:
            problems.append(f"missing heading: {heading}")
    return problems


def inspect_freshness(content: str, checkpoint: Path) -> Freshness:
    """判断 checkpoint 是否与当前 Git 工作区一致。"""

    version = frontmatter_field(content, "checkpoint_version")
    if version is None:
        return Freshness(
            "unknown",
            (
                "legacy checkpoint has no checkpoint_version or workspace fingerprint; "
                "refresh it before relying on it",
            ),
            True,
        )
    if version != CHECKPOINT_VERSION:
        return Freshness(
            "unknown",
            (f"unsupported checkpoint_version {version}",),
            True,
        )

    snapshot = workspace_snapshot(checkpoint.parent.parent)
    if snapshot is None:
        return Freshness(
            "unknown",
            ("Git freshness is unavailable; reconcile the workspace manually",),
        )

    expected_head = frontmatter_field(content, "git_head")
    expected_fingerprint = frontmatter_field(content, "worktree_fingerprint")
    notes: list[str] = []
    if expected_head != snapshot["git_head"]:
        notes.append(
            f"checkpoint git_head {expected_head} does not match current HEAD "
            f"{snapshot['git_head']}"
        )
    if expected_fingerprint != snapshot["worktree_fingerprint"]:
        notes.append("the Git worktree changed after the checkpoint was refreshed")
    if notes:
        return Freshness("stale", tuple(notes), True)
    return Freshness("fresh")


def inspect_ownership(
    content: str, checkpoint: Path, session_id: str | None
) -> tuple[bool, list[str]]:
    """返回 (是否属于其他会话, 归属提示)。

    只有记录中的会话与当前会话明确不同才算其他会话；缺失归属按未知处理。
    """

    recorded_session = frontmatter_field(content, "session")
    recorded_workspace = frontmatter_field(content, "workspace")
    notes: list[str] = []
    foreign_session = bool(recorded_session and session_id and recorded_session != session_id)
    if foreign_session:
        notes.append(
            f"the checkpoint records session {recorded_session} "
            f"but the current session is {session_id}"
        )
    elif recorded_session is None:
        notes.append("the checkpoint records no session, so its owner is unknown")
    if recorded_workspace and recorded_workspace != str(checkpoint.parent.parent):
        notes.append(
            f"the checkpoint records workspace {recorded_workspace} "
            f"but lives in {checkpoint.parent.parent}"
        )
    return foreign_session, notes


def _session_line(session_id: str | None) -> str:
    if not session_id:
        return ""
    return (
        f"CodeAccord session id: {session_id}. Record it in the checkpoint `session` "
        "field when you create .codeaccord/checkpoint.md."
    )


def _manual_compaction_block(issues: list[str], platform: str) -> dict[str, Any]:
    reason = "CodeAccord checkpoint must be refreshed: " + "; ".join(issues)
    if platform == "claude":
        return {"decision": "block", "reason": reason}
    return {"continue": False, "stopReason": reason, "systemMessage": reason}


def _automatic_compaction_warning(issues: list[str]) -> dict[str, Any]:
    return {
        "continue": True,
        "systemMessage": (
            "CodeAccord checkpoint may be stale before automatic compaction: "
            + "; ".join(issues)
            + ". After compaction, read the checkpoint and reconcile it with Git status "
            "and current source before editing any product file."
        ),
    }


def _freshness_warning(freshness: Freshness) -> str:
    return (
        f"Checkpoint freshness is {freshness.state}: "
        + "; ".join(freshness.notes)
        + ". Before editing any product file, read the checkpoint, inspect Git status "
        "and current source, reconcile differences, and refresh the checkpoint."
    )


def _session_start_output(additional_context: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        }
    }


def _foreign_session_context(
    checkpoint: Path, session_id: str | None, notes: list[str]
) -> dict[str, Any]:
    return _session_start_output(
        "A CodeAccord checkpoint exists but belongs to another session. Do not adopt its "
        "scope and do not overwrite it without the user's explicit confirmation. If the user "
        "confirms they are continuing that task, read it first and then take ownership by "
        "updating its `workspace` and `session` fields.\n\n"
        + "\n".join(f"- {note}" for note in notes)
        + f"\n\nCheckpoint: {checkpoint}\nCurrent session: {session_id}"
    )


def _recovery_context(
    checkpoint: Path,
    content: str,
    problems: list[str],
    notes: list[str],
    session_id: str | None,
    freshness: Freshness,
) -> dict[str, Any]:
    parts: list[str] = []
    session_line = _session_line(session_id)
    if session_line:
        parts.append(session_line)
    parts.append(
        "An active CodeAccord recovery checkpoint exists. Read it as the latest confirmed "
        "product boundary, then inspect git status and current source before continuing. "
        "Do not expand scope from the generated compaction summary."
    )
    if problems:
        parts.append("The checkpoint structure is incomplete: " + "; ".join(problems) + ".")
    if freshness.state != "fresh":
        parts.append(_freshness_warning(freshness))
    if notes:
        parts.append(
            "Ownership warning: "
            + "; ".join(notes)
            + ". Confirm with the user before overwriting this checkpoint."
        )
    return _session_start_output(
        "\n\n".join(parts) + f"\n\nCheckpoint: {checkpoint}\n\n{content}"
    )


def handle_event(payload: dict[str, Any], platform: str = "codex") -> dict[str, Any] | None:
    """处理 Codex 与 Claude Code 共用的 Hook 输入。"""

    cwd_value = payload.get("cwd")
    if not isinstance(cwd_value, str) or not cwd_value:
        return None
    session_value = payload.get("session_id")
    session_id = session_value if isinstance(session_value, str) and session_value else None
    event_name = payload.get("hook_event_name")

    checkpoint = find_checkpoint(Path(cwd_value))
    if checkpoint is None:
        if event_name != "SessionStart":
            return None
        session_line = _session_line(session_id)
        return _session_start_output(session_line) if session_line else None

    try:
        content = checkpoint.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "continue": True,
            "systemMessage": f"Unable to read CodeAccord checkpoint: {exc}",
        }

    problems = validate_checkpoint(content)
    foreign_session, notes = inspect_ownership(content, checkpoint, session_id)

    if event_name == "PreCompact":
        if problems:
            if payload.get("trigger") == "manual":
                return _manual_compaction_block(problems, platform)
            return _automatic_compaction_warning(problems)
        if foreign_session:
            return {
                "continue": True,
                "systemMessage": "CodeAccord checkpoint ownership: " + "; ".join(notes) + ".",
            }
        freshness = inspect_freshness(content, checkpoint)
        if freshness.blocks_manual and payload.get("trigger") == "manual":
            return _manual_compaction_block(list(freshness.notes), platform)
        if freshness.state != "fresh":
            return {
                "continue": True,
                "systemMessage": _freshness_warning(freshness),
            }
        return None

    if event_name == "SessionStart":
        if foreign_session:
            return _foreign_session_context(checkpoint, session_id, notes)
        freshness = inspect_freshness(content, checkpoint)
        return _recovery_context(
            checkpoint, content, problems, notes, session_id, freshness
        )

    return None


def main() -> int:
    """读取标准输入并输出 Hook JSON。"""

    mode = sys.argv[1] if len(sys.argv) > 1 else "codex"
    if mode == "snapshot":
        workspace = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
        snapshot = workspace_snapshot(workspace)
        if snapshot is None:
            print("Unable to calculate a Git workspace snapshot", file=sys.stderr)
            return 1
        json.dump(snapshot, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    platform = mode
    if platform not in {"codex", "claude"}:
        print(
            "Usage: checkpoint_hook.py [codex|claude|snapshot [workspace]]",
            file=sys.stderr,
        )
        return 2

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Invalid hook input: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict):
        print("Invalid hook input: expected a JSON object", file=sys.stderr)
        return 1

    output = handle_event(payload, platform)
    if output is not None:
        json.dump(output, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
