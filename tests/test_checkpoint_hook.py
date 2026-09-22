"""验证 CodeAccord checkpoint Hook 的跨平台核心行为。"""

from __future__ import annotations

import importlib.util
import subprocess
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
    snapshot: dict[str, str] | None = None,
    versioned: bool = False,
) -> str:
    """生成结构合法的 checkpoint，固定 Hook 的判定输入。"""

    frontmatter = ["---", f"status: {status}", "updated: 2026-09-21T10:00:00Z"]
    if workspace:
        frontmatter.append(f"workspace: {workspace}")
    if session:
        frontmatter.append(f"session: {session}")
    if versioned:
        frontmatter.extend(
            [
                f"checkpoint_version: {checkpoint_hook.CHECKPOINT_VERSION}",
                "language: zh-CN",
                "accord_revision: 1",
                f"git_head: {(snapshot or {}).get('git_head', 'unavailable')}",
                "worktree_fingerprint: "
                f"{(snapshot or {}).get('worktree_fingerprint', 'unavailable')}",
                "checkpoint_reason: accord_confirmed",
            ]
        )
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

    def git(self, root: Path, *args: str) -> str:
        """运行测试仓库中的 Git 命令。"""

        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def make_git_root(self) -> Path:
        """创建带一个提交且忽略 checkpoint 的测试仓库。"""

        root = self.make_root()
        self.git(root, "init")
        self.git(root, "config", "user.name", "CodeAccord Tests")
        self.git(root, "config", "user.email", "codeaccord@example.invalid")
        (root / ".gitignore").write_text(".codeaccord/\n", encoding="utf-8")
        (root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        self.git(root, "add", ".gitignore", "tracked.txt")
        self.git(root, "commit", "-m", "baseline")
        return root

    def write_current_checkpoint(self, root: Path, *, session: str = SESSION) -> Path:
        """按当前 Git 状态写入带新鲜度元数据的 checkpoint。"""

        snapshot = checkpoint_hook.workspace_snapshot(root)
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        return self.write_checkpoint(
            root,
            checkpoint_content(
                workspace=str(root),
                session=session,
                snapshot=snapshot,
                versioned=True,
            ),
        )

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
        root = self.make_git_root()
        self.write_current_checkpoint(root)

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNone(output)

    def test_legacy_checkpoint_blocks_manual_compaction(self) -> None:
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

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])
        self.assertIn("legacy checkpoint", output["stopReason"])

    def test_legacy_checkpoint_allows_automatic_compaction_with_warning(self) -> None:
        root = self.make_root()
        self.write_checkpoint(root, checkpoint_content(workspace=str(root), session=SESSION))

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "auto",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertTrue(output["continue"])
        self.assertIn("legacy checkpoint", output["systemMessage"])

    def test_non_git_versioned_checkpoint_warns_without_blocking(self) -> None:
        root = self.make_root()
        self.write_checkpoint(
            root,
            checkpoint_content(
                workspace=str(root),
                session=SESSION,
                versioned=True,
            ),
        )

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertTrue(output["continue"])
        self.assertIn("freshness is unknown", output["systemMessage"])

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

    def test_unstaged_change_makes_checkpoint_stale(self) -> None:
        root = self.make_git_root()
        self.write_current_checkpoint(root)
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])
        self.assertIn("worktree changed", output["stopReason"])

    def test_staged_change_makes_checkpoint_stale(self) -> None:
        root = self.make_git_root()
        self.write_current_checkpoint(root)
        (root / "tracked.txt").write_text("staged\n", encoding="utf-8")
        self.git(root, "add", "tracked.txt")

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])

    def test_untracked_content_change_makes_checkpoint_stale(self) -> None:
        root = self.make_git_root()
        untracked = root / "notes.txt"
        untracked.write_text("first\n", encoding="utf-8")
        self.write_current_checkpoint(root)
        untracked.write_text("second\n", encoding="utf-8")

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])

    def test_head_change_makes_checkpoint_stale(self) -> None:
        root = self.make_git_root()
        self.write_current_checkpoint(root)
        (root / "tracked.txt").write_text("next commit\n", encoding="utf-8")
        self.git(root, "add", "tracked.txt")
        self.git(root, "commit", "-m", "next")

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])
        self.assertIn("does not match current HEAD", output["stopReason"])

    def test_stale_checkpoint_allows_automatic_compaction_with_recovery_barrier(self) -> None:
        root = self.make_git_root()
        self.write_current_checkpoint(root)
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "auto",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertTrue(output["continue"])
        self.assertIn("freshness is stale", output["systemMessage"])
        self.assertIn(
            "before editing any product file", output["systemMessage"].lower()
        )

    def test_refresh_after_change_restores_freshness(self) -> None:
        root = self.make_git_root()
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.write_current_checkpoint(root)

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNone(output)

    def test_session_start_marks_stale_checkpoint_and_preserves_language(self) -> None:
        root = self.make_git_root()
        self.write_current_checkpoint(root)
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")

        context = self.session_context(root)

        self.assertIn("Checkpoint freshness is stale", context)
        self.assertIn("Before editing any product file", context)
        self.assertIn("language: zh-CN", context)

    def test_versioned_checkpoint_requires_all_metadata_fields(self) -> None:
        root = self.make_root()
        content = checkpoint_content(workspace=str(root), session=SESSION)
        content = content.replace(
            "session: session-1\n",
            "session: session-1\ncheckpoint_version: 1\n",
        )
        self.write_checkpoint(root, content)

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])
        self.assertIn("frontmatter language is missing", output["stopReason"])

    def test_implementing_checkpoint_requires_positive_accord_revision(self) -> None:
        root = self.make_git_root()
        snapshot = checkpoint_hook.workspace_snapshot(root)
        self.assertIsNotNone(snapshot)
        content = checkpoint_content(
            workspace=str(root),
            session=SESSION,
            snapshot=snapshot,
            versioned=True,
        ).replace("accord_revision: 1", "accord_revision: 0")
        self.write_checkpoint(root, content)

        output = checkpoint_hook.handle_event(
            {
                "cwd": str(root),
                "session_id": SESSION,
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )

        self.assertIsNotNone(output)
        assert output is not None
        self.assertFalse(output["continue"])
        self.assertIn("must be positive after Explore", output["stopReason"])

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
        self.assertIn("legacy checkpoint", context)

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

    def test_workspace_snapshot_does_not_modify_git_state(self) -> None:
        root = self.make_git_root()
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        (root / "notes.txt").write_text("untracked\n", encoding="utf-8")
        before = self.git(root, "status", "--short")

        snapshot = checkpoint_hook.workspace_snapshot(root)

        self.assertIsNotNone(snapshot)
        self.assertEqual(self.git(root, "status", "--short"), before)


if __name__ == "__main__":
    unittest.main()
