# Optional compaction hooks

CodeAccord's core behavior lives in `SKILL.md`. These optional hooks add two mechanical safeguards:

1. validate an existing checkpoint before compaction, blocking manual compaction when its structure is incomplete;
2. inject the checkpoint into the agent context after compaction or session resume.

They intentionally do not parse transcripts or generate semantic summaries. The active agent must refresh `.codeaccord/checkpoint.md` before compaction, as required by the Skill. Automatic compaction is never blocked because doing so near a hard context limit can fail the active request.

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

- No checkpoint file means no active recoverable CodeAccord task, so the hook is silent.
- A valid checkpoint allows compaction.
- An incomplete checkpoint blocks manual compaction so it can be repaired first.
- An incomplete checkpoint does not block automatic compaction.
- `SessionStart` with `startup`, `resume`, `clear`, or `compact` injects the checkpoint contents as agent context.

The Hook checks structure only. It cannot prove that the checkpoint is semantically current; that remains the active agent's responsibility.
