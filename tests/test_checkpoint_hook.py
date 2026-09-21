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

SESSION = "session-1"
OTHER_SESSION = "session-2"


def checkpoint_content(
    *,
    status: str = "implementing",
    workspace: str | None = None,
    session: str | None = None,
) -> str:
    """生成结构合法的 checkpoint，固定 Hook 的判定输入。"""

    frontmatter = ["---", f"status: {status}", "updated: 2026-09-21T10:00:00Z"]
    if workspace:
        frontmatter.append(f"workspace: {workspace}")
    if session:
        frontmatter.append(f"session: {session}")
    frontmatter.append("---")
    body = [
        "",
        "# Goal",
        "Keep one recovery checkpoint.",
        "",
        "## Confirmed scope",
        "Update the Skill and optional hooks.",
        "",
        "## Non-goals",
        "Do not parse transcripts.",
        "",
        "## Current state",
        "Implementation started.",
        "",
        "## Next action",
        "Run tests.",
        "",
        "## Acceptance checks",
        "Hook tests pass.",
        "",
        "## Unresolved",
        "None.",
        "",
    ]
    return "\n".join(frontmatter + body)


class CheckpointHookTests(unittest.TestCase):
    def make_root(self) -> Path:
        """创建临时项目根目录，并在测试结束后清理。"""

        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        return Path(temporary_directory.name)

    def write_checkpoint(self, root: Path, content: str) -> Path:
        """写入 checkpoint 文件。"""

        checkpoint = root / ".codeaccord" / "checkpoint.md"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(content, encoding="utf-8")
        return checkpoint

    def session_start(self, cwd: Path, session_id: str | None = SESSION) -> dict | None:
        """触发 SessionStart 并返回 Hook 输出。"""

        payload: dict = {"cwd": str(cwd), "hook_event_name": "SessionStart", "source": "compact"}
        if session_id:
            payload["session_id"] = session_id
        return checkpoint_hook.handle_event(payload)

    def session_context(self, cwd: Path, session_id: str | None = SESSION) -> str:
        """取出 SessionStart 注入的上下文。"""

        output = self.session_start(cwd, session_id)
        self.assertIsNotNone(output)
        assert output is not None
        return output["hookSpecificOutput"]["additionalContext"]

    def test_valid_checkpoint_allows_manual_compaction(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, checkpoint_content(workspace=str(root), session=SESSION))

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNone(output)

    def test_invalid_checkpoint_blocks_manual_compaction(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, "status: implementing\n")

        output = checkpoint_hook.handle_event(
            {"cwd": str(root), "hook_event_name": "PreCompact", "trigger": "manual"},
            platform="claude",
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertEqual(output["decision"], "block")

    def test_invalid_checkpoint_blocks_codex_manual_compaction(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, "status: implementing\n")

        output = checkpoint_hook.handle_event(
            {"cwd": str(root), "hook_event_name": "PreCompact", "trigger": "manual"},
            platform="codex",
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])

    def test_invalid_checkpoint_does_not_block_automatic_compaction(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, "status: implementing\n")

        output = checkpoint_hook.handle_event(
            {"cwd": str(root), "hook_event_name": "PreCompact", "trigger": "auto"}
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertTrue(output["continue"])

    def test_owned_checkpoint_is_injected_from_parent_directory(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, checkpoint_content(workspace=str(root), session=SESSION))
        nested = root / "src" / "feature"
        nested.mkdir(parents=True)

        context = self.session_context(nested)

        self.assertIn("latest confirmed product boundary", context)
        self.assertIn("Keep one recovery checkpoint.", context)
        self.assertIn(f"CodeAccord session id: {SESSION}", context)
        self.assertNotIn("Ownership warning", context)

    def test_session_start_reports_session_id_without_checkpoint(self) -> None:
        root = self.make_root()

        context = self.session_context(root)

        self.assertIn(f"CodeAccord session id: {SESSION}", context)
        self.assertNotIn("latest confirmed product boundary", context)

    def test_verifying_checkpoint_is_valid_recovery_state(self) -> None:
        root = self.make_root()
        self.write_checkpoint(
            root,
            checkpoint_content(status="verifying", workspace=str(root), session=SESSION),
        )

        context = self.session_context(root)

        self.assertNotIn("checkpoint structure is incomplete", context)
        self.assertIn("status: verifying", context)

    def test_another_session_does_not_receive_checkpoint_contents(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, checkpoint_content(workspace=str(root), session=SESSION))

        context = self.session_context(root, OTHER_SESSION)

        self.assertIn("belongs to another session", context)
        self.assertIn(OTHER_SESSION, context)
        self.assertNotIn("latest confirmed product boundary", context)
        self.assertNotIn("Keep one recovery checkpoint.", context)

    def test_unknown_owner_is_injected_with_a_warning(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, checkpoint_content(workspace=str(root)))

        context = self.session_context(root)

        self.assertIn("latest confirmed product boundary", context)
        self.assertIn("Ownership warning", context)
        self.assertIn("owner is unknown", context)

    def test_workspace_mismatch_is_injected_with_a_warning(self) -> None:
        root = self.make_root()
        self.write_checkpoint(
            root, checkpoint_content(workspace="/somewhere/else", session=SESSION)
        )

        context = self.session_context(root)

        self.assertIn("latest confirmed product boundary", context)
        self.assertIn("records workspace /somewhere/else", context)

    def test_precompact_warns_for_another_session_without_blocking(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, checkpoint_content(workspace=str(root), session=SESSION))

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": OTHER_SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertTrue(output["continue"])
        self.assertNotIn("decision", output)
        self.assertIn(SESSION, output["systemMessage"])

    def test_hook_never_modifies_the_checkpoint(self) -> None:
        root = self.make_root()
        checkpoint = self.write_checkpoint(
            root, checkpoint_content(workspace=str(root), session=SESSION)
        )
        before = checkpoint.read_bytes()

        self.session_start(root)
        checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertEqual(checkpoint.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
