#!/usr/bin/env python3
"""校验并恢复 CodeAccord 的单一上下文 checkpoint。"""

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


def validate_checkpoint(content: str) -> list[str]:
    """检查恢复所需的最小结构，不判断自然语言内容。"""

    problems: list[str] = []
    status = next(
        (
            line.partition(":")[2].strip()
            for line in content.splitlines()
            if line.startswith("status:")
        ),
        None,
    )
    if status not in VALID_STATUSES:
        problems.append(
            "frontmatter status must be exploring, approved, implementing, or verifying"
        )
    if not any(line.startswith("updated:") for line in content.splitlines()):
        problems.append("frontmatter updated timestamp is missing")

    for heading in REQUIRED_HEADINGS:
        if heading not in content:
            problems.append(f"missing heading: {heading}")
    return problems


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


def _recovery_context(path: Path, content: str, problems: list[str]) -> dict[str, Any]:
    warning = ""
    if problems:
        warning = "\nThe checkpoint structure is incomplete: " + "; ".join(problems) + "."
    additional_context = (
        "An active CodeAccord recovery checkpoint exists. Read it as the latest "
        "confirmed product boundary, then inspect git status and current source before "
        "continuing. Do not expand scope from the generated compaction summary."
        f"{warning}\n\nCheckpoint: {path}\n\n{content}"
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        }
    }


def handle_event(payload: dict[str, Any], platform: str = "codex") -> dict[str, Any] | None:
    """处理 Codex 与 Claude Code 共用的 Hook 输入。"""

    cwd_value = payload.get("cwd")
    if not isinstance(cwd_value, str) or not cwd_value:
        return None

    checkpoint = find_checkpoint(Path(cwd_value))
    if checkpoint is None:
        return None

    try:
        content = checkpoint.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "continue": True,
            "systemMessage": f"Unable to read CodeAccord checkpoint: {exc}",
        }

    problems = validate_checkpoint(content)
    event_name = payload.get("hook_event_name")

    if event_name == "PreCompact":
        if not problems:
            return None
        if payload.get("trigger") == "manual":
            return _manual_compaction_block(problems, platform)
        return _automatic_compaction_warning(problems)

    if event_name == "SessionStart":
        return _recovery_context(checkpoint, content, problems)

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
