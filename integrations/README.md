# Optional compaction hooks

CodeAccord's core behavior lives in `SKILL.md`. These optional hooks add four mechanical safeguards:

1. validate an existing checkpoint before compaction, blocking manual compaction when its structure is incomplete or its Git snapshot is stale;
2. inject the checkpoint into the agent context after compaction or session resume;
3. report checkpoint ownership so a session never adopts or overwrites another session's task;
4. warn that the recovery barrier must reconcile stale or legacy state with Git before product edits continue.

They intentionally do not parse transcripts or generate semantic summaries. The active agent must refresh `.codeaccord/checkpoint.md` before compaction, as required by the Skill. Automatic compaction is never blocked because doing so near a hard context limit can fail the active request.

The hooks never write the checkpoint. Ownership and freshness metadata are recorded in the frontmatter by the agent, and the hook only compares them with the running session and current Git workspace.

After refreshing the semantic content, the agent obtains the current Git metadata from the same read-only script and copies it into the checkpoint frontmatter:

```bash
python3 .agents/skills/codeaccord/scripts/checkpoint_hook.py snapshot "$(git rev-parse --show-toplevel)"
```

The command outputs only `git_head` and `worktree_fingerprint`; it does not write the checkpoint or expose diff contents.
The examples allow 15 seconds because freshness calculation may inspect a large worktree.

The examples assume the Skill is installed in the project at:

```text
.agents/skills/codeaccord
```

If you use a personal installation, replace the script command with its absolute path.

## Codex

Merge [`codex/hooks.json.example`](codex/hooks.json.example) into `.codex/hooks.json`. Do not overwrite existing hooks. Codex requires project-local hooks to be reviewed and trusted; inspect them with `/hooks`.

## Claude Code

Merge [`claude-code/settings.json.example`](claude-code/settings.json.example) into `.claude/settings.json`. Do not overwrite existing settings or hooks. Inspect the loaded hooks with `/hooks`.

## Behavior

- `SessionStart` always reports the current session id so the agent can record it as the checkpoint owner.
- A checkpoint recorded for the current session is injected as agent context.
- A checkpoint recorded for another session produces an ownership notice instead of its contents, so an unrelated session cannot adopt that task or silently overwrite it.
- A checkpoint with no recorded owner, or a recorded workspace that does not match its location, is still injected with an ownership warning. Missing ownership should not block recovery of the user's own task.
- A structurally valid checkpoint whose Git snapshot matches the workspace allows compaction.
- An incomplete checkpoint blocks manual compaction so it can be repaired first.
- A stale or legacy checkpoint blocks manual compaction so the agent can reconcile and refresh it first.
- An incomplete checkpoint does not block automatic compaction.
- A stale or legacy checkpoint does not block automatic compaction; the hook emits a recovery-barrier warning instead.
- A non-Git workspace falls back to structure and ownership checks and reports freshness as unknown.
- On Codex, `PreCompact` warns when the checkpoint belongs to another session.

The Hook checks structure, recorded ownership, and whether the recorded Git snapshot still matches. It still cannot prove that the natural-language decisions are semantically correct; that remains the active agent's responsibility.
