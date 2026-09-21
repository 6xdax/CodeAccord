#!/usr/bin/env python3
"""校验并恢复 CodeAccord 的单一上下文 checkpoint。

Hook 只读 checkpoint：归属字段由 Agent 维护，避免多个会话互相覆盖。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CHECKPOINT_RELATIVE_PATH = Path(".codeaccord/checkpoint.md")
VALID_STATUSES = {"exploring", "approved", "implementing", "verifying"}
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
    for heading in REQUIRED_HEADINGS:
        if heading not in content:
            problems.append(f"missing heading: {heading}")
    return problems


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


def _manual_compaction_block(problems: list[str], platform: str) -> dict[str, Any]:
    reason = "CodeAccord checkpoint is incomplete: " + "; ".join(problems)
    if platform == "claude":
        return {"decision": "block", "reason": reason}
    return {"continue": False, "stopReason": reason, "systemMessage": reason}


def _automatic_compaction_warning(problems: list[str]) -> dict[str, Any]:
    return {
        "continue": True,
        "systemMessage": (
            "CodeAccord checkpoint is incomplete before automatic compaction: "
            + "; ".join(problems)
        ),
    }


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
        return None

    if event_name == "SessionStart":
        if foreign_session:
            return _foreign_session_context(checkpoint, session_id, notes)
        return _recovery_context(checkpoint, content, problems, notes, session_id)

    return None


def main() -> int:
    """读取标准输入并输出 Hook JSON。"""

    platform = sys.argv[1] if len(sys.argv) > 1 else "codex"
    if platform not in {"codex", "claude"}:
        print("Usage: checkpoint_hook.py [codex|claude]", file=sys.stderr)
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
