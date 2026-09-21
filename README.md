# CodeAccord

**Agree on the change, then build it.**

CodeAccord is a lightweight, portable Agent Skill for evidence-based software changes. It gives coding agents one continuous workflow for product requirements, bug fixes, refactors, configuration changes, and other repository work:

```text
Inspect -> Challenge -> Accord -> Build -> Verify
```

The agent investigates the real project, challenges unsupported assumptions, presents one concrete change brief, waits for one explicit agreement, then implements and verifies the agreed scope.

[简体中文](README.zh-CN.md)

## Why CodeAccord

Coding agents often fail in two opposite ways: they start editing before the problem is understood, or they introduce a heavy planning process for routine work. CodeAccord keeps the useful boundaries of specification-driven development while staying small:

- one Skill;
- one agreement gate;
- no CLI or runtime dependency;
- no mandatory planning files;
- at most one durable change record when the work needs it;
- no automatic sync or archive lifecycle.

The user owns the desired outcome. The agent still evaluates diagnoses and proposed implementations against source code, tests, logs, contracts, and project constraints.

## Workflow

| Stage | Purpose |
| --- | --- |
| Inspect | Establish current behavior and evidence from the actual project. |
| Challenge | Test assumptions, identify risks, and recommend the strongest approach. |
| Accord | Present one reviewable scope and receive one explicit confirmation. |
| Build | Implement the approved code, tests, and necessary documentation. |
| Verify | Check the result against acceptance criteria and report evidence. |

CodeAccord distinguishes product changes, bug fixes, and mixed changes inside the same workflow. It does not require the user to repeatedly say “analyze first” or “do not edit yet.”

## Installation

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

The agent still investigates before editing.

## Durable change records

Simple work stays in the conversation. CodeAccord creates one durable record only when the change spans modules or sessions, affects contracts, data, deployment, or operations, contains several product decisions, or explicitly needs a saved plan.

Unless a project defines another compatible location, records are stored at:

```text
.codeaccord/changes/<change-name>.md
```

CodeAccord does not modify ignore rules, commit, sync, or archive these records automatically.

## Repository layout

```text
skills/codeaccord/
├── SKILL.md
└── agents/
    └── openai.yaml
```

`SKILL.md` is the portable workflow. `agents/openai.yaml` is optional OpenAI/Codex interface metadata; tools that do not use it can ignore it.

## License

[MIT](LICENSE)
