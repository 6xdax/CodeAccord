"""验证 CodeAccord checkpoint Hook 的跨平台核心行为。"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "codeaccord"
    / "scripts"
    / "checkpoint_hook.py"
)
SPEC = importlib.util.spec_from_file_location("checkpoint_hook", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
checkpoint_hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint_hook)

VALID_CHECKPOINT = """---
status: implementing
updated: 2026-09-21T10:00:00Z
---

# Goal
Keep one recovery checkpoint.

## Confirmed scope
Update the Skill and optional hooks.

## Non-goals
Do not parse transcripts.

## Current state
Implementation started.

## Next action
Run tests.

## Acceptance checks
Hook tests pass.

## Unresolved
None.
"""


class CheckpointHookTests(unittest.TestCase):
    def make_checkpoint(self, content: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary_directory = tempfile.TemporaryDirectory()
        root = Path(temporary_directory.name)
        checkpoint = root / ".codeaccord" / "checkpoint.md"
        checkpoint.parent.mkdir()
        checkpoint.write_text(content, encoding="utf-8")
        return temporary_directory, root

    def test_valid_checkpoint_allows_manual_compaction(self) -> None:
        temporary_directory, root = self.make_checkpoint(VALID_CHECKPOINT)
        self.addCleanup(temporary_directory.cleanup)

        output = checkpoint_hook.handle_event(
            {"cwd": str(root), "hook_event_name": "PreCompact", "trigger": "manual"}
        )

        self.assertIsNone(output)

    def test_verifying_checkpoint_is_valid_recovery_state(self) -> None:
        temporary_directory, root = self.make_checkpoint(
            VALID_CHECKPOINT.replace("status: implementing", "status: verifying").replace(
                "Implementation started.", "Implementation complete; acceptance tests are running."
            )
        )
        self.addCleanup(temporary_directory.cleanup)

        output = checkpoint_hook.handle_event(
            {"cwd": str(root), "hook_event_name": "SessionStart", "source": "compact"}
        )

        self.assertIsNotNone(output)
        assert output is not None
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("checkpoint structure is incomplete", context)
        self.assertIn("status: verifying", context)

    def test_invalid_checkpoint_blocks_manual_compaction(self) -> None:
        temporary_directory, root = self.make_checkpoint("status: implementing\n")
        self.addCleanup(temporary_directory.cleanup)

        output = checkpoint_hook.handle_event(
            {"cwd": str(root), "hook_event_name": "PreCompact", "trigger": "manual"},
            platform="claude",
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertEqual(output["decision"], "block")

    def test_invalid_checkpoint_blocks_codex_manual_compaction(self) -> None:
        temporary_directory, root = self.make_checkpoint("status: implementing\n")
        self.addCleanup(temporary_directory.cleanup)

        output = checkpoint_hook.handle_event(
            {"cwd": str(root), "hook_event_name": "PreCompact", "trigger": "manual"},
            platform="codex",
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])

    def test_invalid_checkpoint_does_not_block_automatic_compaction(self) -> None:
        temporary_directory, root = self.make_checkpoint("status: implementing\n")
        self.addCleanup(temporary_directory.cleanup)

        output = checkpoint_hook.handle_event(
            {"cwd": str(root), "hook_event_name": "PreCompact", "trigger": "auto"}
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertTrue(output["continue"])

    def test_session_start_injects_checkpoint_from_parent_directory(self) -> None:
        temporary_directory, root = self.make_checkpoint(VALID_CHECKPOINT)
        self.addCleanup(temporary_directory.cleanup)
        nested = root / "src" / "feature"
        nested.mkdir(parents=True)

        output = checkpoint_hook.handle_event(
            {"cwd": str(nested), "hook_event_name": "SessionStart", "source": "compact"}
        )

        self.assertIsNotNone(output)
        assert output is not None
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("latest confirmed product boundary", context)
        self.assertIn("Keep one recovery checkpoint.", context)

    def test_missing_checkpoint_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = checkpoint_hook.handle_event(
                {
                    "cwd": temporary_directory,
                    "hook_event_name": "SessionStart",
                    "source": "compact",
                }
            )

        self.assertIsNone(output)


if __name__ == "__main__":
    unittest.main()
