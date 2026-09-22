"""验证 CodeAccord checkpoint 快照助手的只读行为。"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "codeaccord"
    / "scripts"
    / "checkpoint_snapshot.py"
)
SPEC = importlib.util.spec_from_file_location("checkpoint_snapshot", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
checkpoint_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint_snapshot)


class CheckpointSnapshotTests(unittest.TestCase):
    def make_root(self) -> Path:
        """创建临时项目根目录，并在测试结束后清理。"""

        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        return Path(temporary_directory.name)

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

    def test_snapshot_returns_head_and_fingerprint(self) -> None:
        root = self.make_git_root()

        snapshot = checkpoint_snapshot.workspace_snapshot(root)

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(snapshot["git_head"], self.git(root, "rev-parse", "HEAD"))
        self.assertEqual(len(snapshot["worktree_fingerprint"]), 64)

    def test_snapshot_does_not_modify_git_state(self) -> None:
        root = self.make_git_root()
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        (root / "notes.txt").write_text("untracked\n", encoding="utf-8")
        before = self.git(root, "status", "--short")

        snapshot = checkpoint_snapshot.workspace_snapshot(root)

        self.assertIsNotNone(snapshot)
        self.assertEqual(self.git(root, "status", "--short"), before)

    def test_fingerprint_excludes_codeaccord(self) -> None:
        root = self.make_git_root()
        baseline = checkpoint_snapshot.workspace_snapshot(root)
        assert baseline is not None

        checkpoint = root / ".codeaccord" / "checkpoint.md"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text("status: implementing\n", encoding="utf-8")

        after = checkpoint_snapshot.workspace_snapshot(root)

        assert after is not None
        self.assertEqual(
            after["worktree_fingerprint"], baseline["worktree_fingerprint"]
        )

    def test_fingerprint_changes_with_worktree_changes(self) -> None:
        root = self.make_git_root()
        baseline = checkpoint_snapshot.workspace_snapshot(root)
        assert baseline is not None

        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        (root / "untracked.txt").write_text("new file\n", encoding="utf-8")

        changed = checkpoint_snapshot.workspace_snapshot(root)

        assert changed is not None
        self.assertEqual(changed["git_head"], baseline["git_head"])
        self.assertNotEqual(
            changed["worktree_fingerprint"], baseline["worktree_fingerprint"]
        )

    def test_snapshot_returns_none_without_git(self) -> None:
        root = self.make_root()

        self.assertIsNone(checkpoint_snapshot.workspace_snapshot(root))

    def test_cli_prints_json_and_fails_without_git(self) -> None:
        root = self.make_root()

        result = subprocess.run(
            ["python3", str(SCRIPT_PATH), str(root)],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("Unable to calculate", result.stderr)

        git_root = self.make_git_root()
        ok = subprocess.run(
            ["python3", str(SCRIPT_PATH), str(git_root)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(ok.returncode, 0)
        payload = json.loads(ok.stdout)
        self.assertIn("git_head", payload)
        self.assertIn("worktree_fingerprint", payload)


if __name__ == "__main__":
    unittest.main()
