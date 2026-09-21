# Optional compaction hooks

CodeAccord's core behavior lives in `SKILL.md`. These optional hooks add three mechanical safeguards:

1. validate an existing checkpoint before compaction, blocking manual compaction when its structure is incomplete;
2. inject the checkpoint into the agent context after compaction or session resume;
3. report checkpoint ownership so a session never adopts or overwrites another session's task.

They intentionally do not parse transcripts or generate semantic summaries. The active agent must refresh `.codeaccord/checkpoint.md` before compaction, as required by the Skill. Automatic compaction is never blocked because doing so near a hard context limit can fail the active request.

The hooks never write the checkpoint. Ownership is recorded in the frontmatter by the agent, and the hook only compares it with the running session.

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
- A valid checkpoint allows compaction.
- An incomplete checkpoint blocks manual compaction so it can be repaired first.
- An incomplete checkpoint does not block automatic compaction.
- On Codex, `PreCompact` warns when the checkpoint belongs to another session.

The Hook checks structure and recorded ownership only. It cannot prove that the checkpoint is semantically current; that remains the active agent's responsibility.
