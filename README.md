# CodeAccord

**Agree on the change, then build it.**

CodeAccord is a lightweight, portable Agent Skill for specification-driven software changes. It gives coding agents one continuous workflow for product requirements, bug fixes, refactors, configuration changes, and other repository work:

```text
Explore [Inspect <-> Challenge] -> Accord -> Build -> Verify
```

The agent repeatedly inspects the real project and challenges assumptions without editing product files. Once the evidence and decisions converge, it presents one fixed, scannable Accord — or a brief description for a small quick-path change — waits for one explicit agreement, and then implements and verifies that scope.

[简体中文](README.zh-CN.md)

## Why CodeAccord

Coding agents often fail in two opposite ways: they start editing before the problem is understood, or they introduce a heavy planning process for routine work. CodeAccord keeps the useful boundaries of specification-driven development while staying small:

- one Skill;
- one agreement gate;
- a quick path that skips the checkpoint and the full Accord for a small self-contained change;
- no CLI or runtime dependency for the core workflow;
- the conversation remains the primary working surface;
- at most one temporary recovery checkpoint;
- no accumulating change records, sync process, or archive lifecycle.

The user owns the desired outcome. The agent still evaluates diagnoses and proposed implementations against source code, tests, logs, contracts, and project constraints.

## Workflow

| Stage | Purpose |
| --- | --- |
| Explore | Loop between inspection and challenge, answer questions, and converge on evidence and a recommendation without editing product files. |
| Accord | Define the scope and acceptance checks — or, for a small quick-path change, describe it briefly — then receive one explicit confirmation. |
| Build | Implement the approved code, tests, and necessary documentation. |
| Verify | Check the result against the accord and report evidence. |

CodeAccord distinguishes product changes, bug fixes, and mixed changes inside the same workflow. It does not require the user to repeatedly say “analyze first” or “do not edit yet.”

## Fixed Accord

Explore uses short findings and recommendations while the direction is still being discussed. It does not end automatically when the agent thinks the evidence is sufficient. After the user accepts the direction or asks to finalize it, CodeAccord emits the full structure once: implementation readiness, change type, goal, current facts, implementation, change scope, compatibility and risks, acceptance checks, and open decisions. Within the full path a small scope keeps the headings but may use one sentence per section.

`Ready after confirmation` means the user can approve and implementation can start immediately. `Pre-authorized` means the user already requested direct implementation. `Blocked by decisions` names the remaining choices and cannot be approved as a complete implementation scope.

After the first Accord, changed decisions use an `Accord delta` containing only the previous and new decision, scope impact, acceptance changes, and open decisions. Unchanged sections are not repeated. Confirmed deltas merge into the recovery checkpoint; proposed deltas remain unresolved. A full restatement is generated only when the user asks for one or the prior baseline cannot be recovered.

## Quick path for small changes

A change uses the quick path only when every one of these holds: the goal is unambiguous, no product or compatibility decision is open, the edit touches one file or one call site and at most two files, it alters no public interface, configuration format, schema, persisted format, concurrency behavior, or deployment behavior, it is reversible, and it can be verified in the current context. A bug fix also needs an established root cause rather than an open investigation.

On the quick path the agent writes no checkpoint and emits no Accord. It states in one to three sentences which file and location changes, what the behavior becomes, and how it will be verified, then waits for a single confirmation. After that it edits and runs the most relevant focused check. Everything else — including several small edits that share one decision, any behavior another component depends on, or verification this context cannot perform — uses the full path.

## Installation

### Send to your AI

Copy and send the following to your coding agent, and it will handle the installation:

> Please install the CodeAccord skill from https://github.com/6xdax/CodeAccord into `.agents/skills/` of this project.

### Install with npx

The [`skills`](https://github.com/vercel-labs/skills) CLI installs CodeAccord into the skill directory of each coding agent it detects, and records the source in a lock file:

```bash
npx skills add 6xdax/CodeAccord      # this project
npx skills add -g 6xdax/CodeAccord   # every project for this user
```

```bash
npx skills update                    # update project skills
npx skills update -g                 # update global skills
```

`npx skills update` refreshes installed skills from the repository they came from, so a new CodeAccord revision reaches an existing installation without a manual copy. Add `-y` to skip the scope prompt, or name the skill with `npx skills update codeaccord` to update only this one.

### Install by copying

Copy the Skill directory into a Skill location supported by your coding agent.

Personal Codex installation:

```bash
cp -R skills/codeaccord ~/.codex/skills/codeaccord
```

Project-local installation:

```bash
mkdir -p /path/to/project/.agents/skills
cp -R skills/codeaccord /path/to/project/.agents/skills/codeaccord
```

For another Agent Skills-compatible tool, copy `skills/codeaccord` into that tool's supported Skill directory.

## Usage

Invoke it explicitly:

```text
$codeaccord Add support for splitting videos longer than 30 seconds.
```

```text
$codeaccord The save endpoint reports success, but the configuration disappears after restart.
```

Tools that support implicit Skill selection may activate CodeAccord automatically based on the `description` in `SKILL.md`.

### Direct implementation

CodeAccord normally stops once at the accord. A user can explicitly skip that separate gate:

```text
$codeaccord Investigate and fix this directly without a separate review step.
```

The agent still completes the read-only Explore loop and states one full `Pre-authorized` Accord before editing, but it may continue without waiting for another reply. A small change that meets the quick-path conditions states the brief description instead.

## Recovery checkpoint

The conversation remains the main interface. For work that may cross a context or session boundary, CodeAccord keeps one short recovery cache:

```text
.codeaccord/checkpoint.md
```

The agent updates it after agreement, after material changes or milestones, before long operations, and before expected context compaction. On the full path, a confirmed Accord or delta is a persistence barrier: the checkpoint write must succeed before product files are edited. The quick path creates no checkpoint; when one already exists for the session, it is refreshed afterwards rather than left stale. `Current state` records only the conclusions needed to resume inspection, implementation, or verification; it is not an activity log. After compaction or resume, the agent reads it, reconciles it with Git HEAD/status and current source, and refreshes stale state before editing. Completed checkpoints are removed instead of archived.

Each checkpoint records `workspace`, `session`, response language, Accord revision, Git HEAD, a worktree fingerprint, and the reason for its latest refresh. The fingerprint covers staged changes, unstaged tracked changes, and untracked contents without storing the diff itself. A checkpoint belonging to another session is surfaced as an ownership notice instead of being loaded as the current task, and it is not overwritten without the user's confirmation. There is one checkpoint per workspace, so two concurrent tasks in the same workspace should use separate worktrees.

CodeAccord 0.2 no longer creates `.codeaccord/changes/*.md`. Existing files are left untouched and are not loaded automatically.

## Optional compaction hooks

The core workflow does not require hooks. Optional examples under `integrations/` validate checkpoint structure, ownership, and Git freshness before compaction, and inject it after compaction or session resume on Codex and Claude Code.

These hooks do not summarize transcripts. Command hooks cannot reliably infer decisions that the active agent failed to save, and transcript formats are not stable contracts. The Skill therefore requires proactive semantic updates; hooks provide a recovery guard, a reload path, an ownership check, and stale-worktree detection. A stale checkpoint blocks manual compaction; automatic compaction continues with a warning and a mandatory recovery barrier. The hooks never write the checkpoint.

The examples assume a project-local installation at `.agents/skills/codeaccord`. See [integration instructions](integrations/README.md).

## Repository layout

```text
skills/codeaccord/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── checkpoint_hook.py

integrations/
├── README.md
├── claude-code/
│   └── settings.json.example
└── codex/
    └── hooks.json.example

tests/
└── test_checkpoint_hook.py
```

`SKILL.md` is the portable workflow. `agents/openai.yaml` is optional OpenAI/Codex interface metadata; tools that do not use it can ignore it. The script and hook examples are optional.

## License

[MIT](LICENSE)
