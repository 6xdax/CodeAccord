# CodeAccord

**Define a verifiable outcome first; build clear requests directly.**

CodeAccord is a lightweight, conversation-first specification-driven development (SDD) Agent Skill for new features, bug fixes, refactors, configuration changes, and other repository work:

```text
Explore [Inspect <-> Challenge] -> [Accord if needed] -> Build -> Verify
```

The agent inspects the real project and challenges assumptions, using the user's request or confirmed Accord to define expected behavior and how to verify it. When the outcome is clear and no user decision remains, it implements and verifies directly. When behavior or boundaries need discussion, it compares meaningful options and presents a concise recommendation for confirmation.

[简体中文](README.zh-CN.md)

## Why CodeAccord

Coding agents may edit before understanding a problem or burden clear requests with unnecessary plans. CodeAccord keeps the useful judgment while reducing that overhead:

- clear requests serve as a minimal specification and proceed without a proposal or extra confirmation;
- consequential user decisions are discussed and confirmed once;
- a proposal starts with one complete summary sentence, then gives only the evidence needed to decide;
- the conversation remains primary, with one temporary checkpoint for confirmed agreements or recovery when needed;
- the core workflow needs no CLI or runtime dependency and creates no change archive.

The user owns the desired result. The agent still checks diagnoses and implementations against source code, tests, logs, and contracts.

## Workflow

| Stage | Purpose |
| --- | --- |
| Explore | Inspect actual behavior and challenge assumptions; this can be brief for a clear request. |
| Accord (when needed) | Summarize a consequential behavior or scope decision and confirm it once. |
| Build | Implement the authorized code, tests, and necessary documentation. |
| Verify | Check the result against the request or confirmed direction and report evidence. |

## Agreements only when needed

Discuss an Accord only when a material product, compatibility, data, deployment, or similar decision remains, or when the user asks to discuss first. **Its first sentence should state the cause or goal, recommended action, main affected area, and expected result.** The rest should include only evidence, scope, risks, and acceptance checks that help the user decide, without an investigation log.

For a bug, a useful order is cause and evidence, repair, affected code, and verification. For a new requirement, describe real tradeoffs when relevant, recommended implementation, affected components, and acceptance. Choose headings, order, and length for the task and use the user's language. Do not invent alternatives to fill a template or present an unverified root cause as fact.

Keep discussing while a user-owned decision remains unresolved. If the user has already authorized the concrete direction, proceed; otherwise request one confirmation. For later material scope changes, describe only the changed decision and its impact.

## Direct work on clear requests

When the user asks for a change, the outcome is clear, and no consequential user decision is open, first identify observable expected behavior and how to check it from the request and project contracts. For a bug, distinguish current behavior from expected behavior. Ask only when a material expectation cannot be derived. Then inspect enough to act safely, implement, and verify against that expectation. Do not require a separate proposal, specification file, or confirmation. Touching several files does not itself trigger an Accord. A bug's root cause can be established during investigation.

When behavior or compatibility boundaries need a user decision, investigate read-only and discuss them first. The agent makes ordinary engineering choices. Committing, pushing, deploying, publishing, and deleting durable data retain their own authorization requirements.

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

A clear request can proceed directly, for example:

```text
$codeaccord Investigate and fix the configuration disappearing after restart.
```

The user can also ask to discuss the approach first; the agent then keeps product files read-only until the direction and authorization are clear.

## Recovery checkpoint

The conversation remains the main interface. For work that may cross a context or session boundary, CodeAccord keeps one short recovery cache:

```text
.codeaccord/checkpoint.md
```

Direct work needs no extra confirmation; its checkpoint use depends on recovery risk. When a task may span context or long operations, record the user's authorized scope. For a decision-path Accord, write and verify the checkpoint after confirmation and before editing product files. Refresh it after milestones, before long operations, and before expected compaction. `Current state` records only the conclusions needed to resume inspection, implementation, or verification; it is not an activity log. After compaction or resume, the agent reads it, reconciles it with Git HEAD/status and current source, and refreshes stale state before editing. Completed checkpoints are removed instead of archived.

Each checkpoint records `workspace`, `session`, response language, Accord revision, Git HEAD, a worktree fingerprint, and the reason for its latest refresh. The fingerprint covers staged changes, unstaged tracked changes, and untracked contents without storing the diff itself. A checkpoint recorded for another session is treated as foreign: the agent confirms with the user before adopting or overwriting it. There is one checkpoint per workspace, so two concurrent tasks in the same workspace should use separate worktrees.

CodeAccord 0.2 no longer creates `.codeaccord/changes/*.md`. Existing files are left untouched and are not loaded automatically.

## Repository layout

```text
skills/codeaccord/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── checkpoint_snapshot.py

tests/
└── test_checkpoint_snapshot.py
```

`SKILL.md` is the portable workflow. `agents/openai.yaml` is optional OpenAI/Codex interface metadata; tools that do not use it can ignore it. The snapshot script is optional.

## License

[MIT](LICENSE)
