---
name: codeaccord
description: Explore, agree, implement, and verify software changes with a read-only inspect-and-challenge loop, one explicit agreement gate, and one compact recovery checkpoint. Use for product requirements, bug fixes, refactors, configuration changes, and other codebase work where the agent should establish evidence and scope before editing instead of blindly accepting assumptions or immediately changing code.
license: MIT
metadata:
  author: CodeAccord contributors
  version: "0.4.1"
---

# CodeAccord

Turn a software change request into an evidence-based agreement, then carry that agreement through implementation and verification.

The user's desired outcome and explicit constraints are authoritative. Their diagnosis, proposed files, and preferred implementation are hypotheses to evaluate. Agree when the evidence supports them. Disagree plainly when they are incomplete, incorrect, risky, or less effective than an available alternative.

Use the user's language unless project instructions require another language.

## Lifecycle

Use one continuous lifecycle:

```text
Explore [Inspect <-> Challenge] -> Accord -> Build -> Verify
```

- **Explore:** Repeat Inspect and Challenge until the evidence, proposed behavior, scope, and acceptance checks are sufficient for a decision. This phase may include answering the user's questions and comparing approaches, but does not edit product files.
- **Accord:** Define what will change, how far it will go, and what proves completion; obtain one explicit confirmation.
- **Build:** Complete the agreed implementation, tests, and necessary documentation.
- **Verify:** Check the delivered behavior against the accord and report evidence.

Do not split this lifecycle across separate planning and implementation skills. Infer the current stage from the conversation and continue from the latest confirmed accord.

The Accord stage has two depths. A non-trivial change produces a full Accord; a small self-contained change that meets every quick-path condition uses a brief confirmed description instead. See **Choose the response path**.

## Explore loop

Explore is a loop, not two one-time steps. Move between **Inspect** and **Challenge** whenever new evidence changes the diagnosis, exposes a missing case, or invalidates a proposed solution.

During Explore:

- read code, configuration, logs, tests, history, documentation, schemas, and runtime evidence;
- run non-destructive diagnostics or reproductions that do not intentionally change tracked files or business data;
- discuss alternatives, answer the user's questions, and record decisions as they become clear;
- distinguish confirmed facts, supported inferences, user decisions, and unresolved questions;
- do not edit implementation files, tests, configuration, or product documentation.

An interim Explore response may answer a question, report findings, reject a premise, or explain what evidence is still missing. Keep it brief and proportional: state the new conclusion, current recommendation, and any decision still needed. Do not use the full Accord structure during Explore.

When the evidence appears sufficient, present a concise recommended direction and ask whether the user wants to finalize it. Do not emit a full Accord merely because the agent believes Explore has converged. Wait for an explicit user signal such as accepting the direction, asking for the complete Accord, or authorizing direct implementation.

Exit Explore only when all of these are true:

1. current behavior or root cause has enough evidence;
2. the intended outcome and important boundaries are clear;
3. the implementation direction and affected scope are identified;
4. acceptance can be checked through observable behavior or executable verification;
5. every unresolved item is either non-blocking or presented as an explicit decision;
6. the user has signaled that the direction is ready to be finalized, or has explicitly pre-authorized direct implementation.

## Classify the change

Choose the mode from evidence rather than keywords:

- **Product change:** The user wants new behavior or a deliberate change to existing behavior.
- **Bug fix:** Existing behavior violates an established contract, documented behavior, or reproducible expectation.
- **Mixed change:** Resolving the defect also requires a product decision or new contract.

When classification is uncertain, investigate first. Ask the user only when the distinction changes the desired outcome or compatibility contract.

## Choose the response path

Choose the path from evidence before writing a response. Both paths keep the same read-only Explore discipline.

**Quick path** — use only when every condition holds:

- the goal is unambiguous and no product, compatibility, or data decision is open;
- the change touches one file or one call site, at most two files;
- it does not alter a public interface, configuration format, schema, persisted format, concurrency behavior, or deployment behavior;
- it is reversible and non-destructive;
- it can be implemented and verified within the current context;
- for a bug, the root cause is already established rather than still being investigated.

On the quick path, do not write a checkpoint and do not emit an Accord or Accord delta. Before editing, state in one to three sentences which file and location changes, what the behavior becomes, and how it will be verified, then wait for one confirmation. After that confirmation, edit and run the most relevant focused check. When the user has already pre-authorized direct implementation, state the same brief description and continue without waiting for another reply.

**Full path** — use for everything else, and whenever the path itself is uncertain. Run the complete lifecycle, the full Accord, the recovery checkpoint, and the persistence barrier below.

Prefer the full path when several small edits share one decision, when a caller or other component depends on the behavior, or when verification needs a tool or environment this context cannot provide.

## Authorization boundary

A request such as “add this feature,” “help me implement this,” or “fix this bug” starts the lifecycle. It does not skip the confirmation gate by itself; on the quick path that gate is the brief description rather than a full Accord.

Before accord, use read-only investigation against product code, configuration, tests, logs, history, and documentation. Do not edit implementation files, tests, configuration, or product documentation.

The only file CodeAccord may create or update before accord is `.codeaccord/checkpoint.md` under **Recovery checkpoint**. It is temporary recovery state and does not authorize implementation. The full path maintains it; the quick path does not create it.

The user may waive waiting at the separate agreement gate by explicitly asking to proceed immediately, saying no review is needed, or having already confirmed the same concrete scope earlier in the conversation. Even then, complete enough Explore to avoid an unsupported assumption and state the fixed Accord — or the quick-path description — before Build; continue without waiting for another reply.

Answers to discovery questions are decisions, not implementation authorization. Once the user explicitly confirms the complete brief with language such as “approved,” “go ahead,” or an equivalent response in their language, treat the whole stated scope as authorized.

On the full path, confirmation creates a persistence barrier. Immediately merge the authorized Accord or delta into `.codeaccord/checkpoint.md` and verify that the write succeeded before editing implementation files, tests, configuration, or product documentation. If the checkpoint update fails, remain at the agreement boundary and do not start Build. A message saying that the checkpoint will be updated does not satisfy this barrier; the file must actually be current first. Because the quick path creates no checkpoint, its confirmation authorizes the described edit directly.

Do not ask again for routine implementation choices inside the accord. Pause only when evidence requires a material change to product behavior, public contracts, data migration, deployment behavior, or another boundary the user did not approve. Present and confirm only that delta.

Committing, pushing, deploying, publishing, deleting durable data, and messaging external parties require their own authorization unless the user already requested them.

## Inspect

Before proposing a solution:

1. Read the nearest project instructions and inspect repository status without disturbing existing work.
2. Trace the real entrypoint, data flow, contracts, persistence, runtime processes, and tests relevant to the request.
3. For a bug, reproduce it or establish equivalent evidence from logs, tests, and code paths.
4. Separate observed facts, supported inferences, user decisions, and unresolved questions.
5. Ask only questions whose answers cannot be derived from available evidence and materially change the result.

Do not let the user's suggested file or diagnosis artificially narrow the investigation.

## Challenge

Evaluate the requested approach before adopting it:

- Identify false premises, missing cases, duplicated mechanisms, and avoidable compatibility costs.
- Prefer existing project patterns and the smallest complete change over parallel abstractions.
- Offer alternatives only when they represent a real tradeoff.
- Recommend a direction when evidence supports one; do not offload ordinary engineering decisions to the user.
- State uncertainty directly. Continue investigating instead of presenting a guess as a root cause.

For bugs, locate the earliest point where the state becomes incorrect. Fix that source rather than masking downstream symptoms with defaults, broad exception handling, or speculative compatibility branches.

## Form the accord

This section describes the full path; the quick path states its change as described in **Choose the response path**. The initial Accord is the fixed exit from Explore. Produce it only after the user signals that the explored direction is ready to finalize. Render labels in the user's language, but preserve the following section order and meanings so readiness can be reviewed at a glance:

```markdown
## Accord

**Implementation readiness:** Ready after confirmation | Pre-authorized | Blocked by decisions
**Type:** Product change | Bug fix | Mixed change

### Goal
One sentence describing the intended result.

### Current facts
- Confirmed behavior, call path, root cause, or evidence that affects the decision.
- Mark any remaining inference explicitly.

### Implementation
- The recommended behavior and technical direction.
- The reason this direction is preferred when that is not obvious.

### Change scope
- Change: affected components, contracts, configuration, tests, and documentation.
- Preserve: behavior or boundaries that must remain unchanged.
- Exclude: related work outside this accord.

### Compatibility and risks
- API, data, deployment, runtime, caller, or operational effects.
- Write "No known compatibility impact" when none are known.

### Acceptance checks
- [ ] Observable or executable completion criteria.

### Open decisions
- None; confirmation authorizes implementation.
```

Use `Ready after confirmation` when no decision blocks implementation but a separate approval is still required. Use `Pre-authorized` when the user already asked to proceed directly; state the complete Accord, then continue to Build without waiting for another reply. If a user-owned decision remains, use `Blocked by decisions`, list the exact choices under **Open decisions**, and do not ask the user to approve an incomplete implementation scope.

Keep every heading in a full-path Accord, but keep its content proportional: a small scope still gets one sentence per section. **Current facts** contains only evidence that affects the implementation decision, not a chronological investigation log. Present one final recommendation rather than preserving rejected alternatives unless a real user decision remains.

When confirmation is still required, end a ready Accord with one direct request to confirm it. After confirmation, proceed directly to Build without generating a second plan. Produce the initial full Accord only once unless the user explicitly asks for a consolidated restatement or the prior baseline cannot be recovered.

## Update an accord

After an initial Accord exists, discuss later changes through the same brief Explore responses. Once the user accepts the changed direction, output only this delta structure instead of repeating the full Accord:

```markdown
## Accord delta

**Status:** Merge after confirmation | Pre-authorized | Blocked by decisions

### Decision change
- Previous:
- New:

### Scope impact
- Added, removed, or changed components and behavior.

### Acceptance changes
- Added, removed, or revised completion checks.

### Open decisions
- None; confirmation merges this delta into the current Accord.
```

Omit unchanged goals, facts, scope, risks, and acceptance checks. Use `Merge after confirmation` when approval is still required, `Pre-authorized` when the user already authorized the change, and `Blocked by decisions` when implementation cannot continue.

When the initial change used the quick path, later revisions of the same small scope stay on the quick path: restate the revised change briefly and confirm once. Output an Accord delta only after a full Accord exists.

Before confirmation, keep a proposed delta under checkpoint **Unresolved** and do not overwrite the confirmed scope. **Confirmed scope contains only behavior authorized for Build**; a user preference, tentative agreement, or answer to an Explore question is not enough. After confirmation, merge the delta into the checkpoint's complete current state, increment `accord_revision`, remove it from **Unresolved**, and cross the persistence barrier before Build resumes. During Build, pause for confirmation only when new evidence crosses an unapproved material boundary, and present only the delta. Reissue a full Accord only when the user explicitly requests it or no reliable baseline can be recovered.

## Recovery checkpoint

The conversation is the primary working surface. Use one short checkpoint only to recover the active change after context compaction, session resumption, or an interrupted implementation. It is a recovery cache, not a second specification system or a history archive.

Use exactly `.codeaccord/checkpoint.md` at the project root. Never create per-change files or accumulate completed records. Decide whether a checkpoint is needed from the response path:

- the quick path never creates a checkpoint;
- on the full path, create it when investigation or implementation is likely to span context compaction, a session boundary, or a long-running tool call;
- on the full path, create it before editing;
- skip it only when the whole task is small enough to complete and verify in the current context without meaningful recovery risk.

Keep the checkpoint semantically current. Refresh it:

1. immediately after the user confirms the initial Accord or an Accord delta;
2. after any approved material scope change;
3. after an important implementation or verification milestone;
4. before a long-running command, test suite, delegation, or other operation that may interrupt the turn;
5. before compaction when the platform signals it or the remaining context indicates it is approaching.

Treat each refresh as an actual persistence operation: write the file, read or validate the result, then continue. Because automatic compaction may arrive without warning, also refresh after each completed implementation batch whose conclusions are needed to resume safely; do not leave `Current state` saying that no code has changed after product files have already been edited.

When a checkpoint already exists for this workspace and session, a quick-path edit still changes the worktree and invalidates its stored fingerprint. Update **Current state** and refresh `git_head` and `worktree_fingerprint` before finishing, rather than leaving a stale checkpoint behind.

Do not wait for a mechanical `PreCompact` hook to summarize the conversation. A command hook cannot infer unrecorded decisions reliably. Platform hooks may validate and reload the file, but the active agent owns the semantic update.

Treat **Confirmed scope** as the merged current Accord. Keep unapproved proposed changes under **Unresolved** until the user confirms them. A compaction or resume must never promote an unresolved delta into confirmed scope.

Keep phase fields self-consistent:

- `exploring` may contain candidate changes under Unresolved but does not authorize Build;
- `approved` means a complete Accord is confirmed and persisted but implementation has not started;
- `implementing` and `verifying` require a positive confirmed `accord_revision` and no unresolved decision that would materially change the authorized behavior;
- when a user-owned decision blocks progress, keep the current confirmed scope unchanged and record the proposed delta under Unresolved.

One checkpoint belongs to one workspace and one session. Record both ownership fields and keep them when you refresh the file:

- `workspace`: the absolute project root;
- `session`: the session id reported by the `SessionStart` hook, or the equivalent session identifier available in your environment.

These fields are how a later session decides whether the checkpoint is its own. Because there is only one checkpoint per workspace, do not run two CodeAccord tasks in the same workspace at the same time; park one task or use a separate worktree.

When a `SessionStart` or `PreCompact` hook reports that the checkpoint belongs to another session, do not adopt its scope and do not overwrite it until the user confirms. After the user confirms they are continuing that task, take ownership by updating `workspace` and `session` to the current values. When the hook reports no recorded owner, or a recorded workspace that does not match the checkpoint's location, treat the checkpoint as moved or copied and verify with the user before continuing. The hook never writes the file, so ownership is always yours to maintain.

After compaction or session resumption, cross a recovery barrier before continuing:

1. read the checkpoint from disk;
2. inspect Git HEAD, status, and relevant current source;
3. reconcile any difference between the checkpoint and the workspace;
4. state the recovered goal, phase, and next action in the recorded user language;
5. refresh the checkpoint when it is legacy, stale, or materially incomplete.

Do not edit implementation files, tests, configuration, or product documentation until this barrier is complete. Source and tests remain authoritative for implementation state, while Confirmed scope remains the product boundary. Do not silently expand scope from a generated compaction summary.

Keep it concise, normally no more than 500–800 tokens. Store decisions and state, not raw transcripts, long evidence, source code, logs, or secrets. `Current state` contains only conclusions needed to resume the task; do not turn it into a chronological investigation or implementation log. Use this shape and omit empty bullets rather than adding more sections:

```markdown
---
status: exploring | approved | implementing | verifying
updated: YYYY-MM-DDTHH:MM:SSZ
workspace: /absolute/project/root
session: <session id>
checkpoint_version: 1
language: <BCP-47 language tag>
accord_revision: <positive integer after the initial Accord is confirmed>
git_head: <current Git commit>
worktree_fingerprint: <hash from checkpoint_hook.py snapshot>
checkpoint_reason: accord_confirmed | delta_confirmed | milestone | precompact
---

# Goal

## Confirmed scope

## Non-goals

## Current state

## Next action

## Acceptance checks

## Unresolved
```

For a Git workspace, obtain `git_head` and `worktree_fingerprint` from the bundled read-only helper and copy both values into the frontmatter after the semantic content is current:

```bash
python3 .agents/skills/codeaccord/scripts/checkpoint_hook.py snapshot "$(git rev-parse --show-toplevel)"
```

The fingerprint covers HEAD, staged changes, unstaged tracked changes, and untracked file contents while excluding `.codeaccord/`; only the hash is stored. If Git freshness is unavailable, record `unavailable` and reconcile the workspace manually after recovery. Hooks never write these fields.

When verification is complete and the final result has been reported, remove the checkpoint. If work remains incomplete or verification is blocked, keep it updated for recovery. Do not archive it automatically.

## Build

After confirmation:

1. On the full path, cross the confirmation persistence barrier before the first product edit. The quick path has no barrier; its confirmed description is the authorization.
2. Implement the entire approved scope and preserve unrelated user changes.
3. Update affected contracts, callers, configuration, migrations, tests, and documentation together.
4. Follow project-local instructions and established patterns.
5. Keep working through ordinary implementation failures without reopening the accord.
6. Remove dead code introduced or made obsolete by this change when it is safely within scope.

Do not create an OpenSpec change or another planning system unless the user explicitly requests it.

## Verify

Run focused checks first, then expand according to the actual impact. Verification must test the agreed behavior rather than merely mirror implementation details.

On the quick path the focused check is the verification: run it and report the result. The full acceptance matrix applies to the full path.

Before declaring completion:

- compare the result with every acceptance criterion;
- verify the original bug reproduction no longer fails when applicable;
- check affected contracts and callers;
- report commands actually run and their results;
- disclose remaining limitations, skipped checks, or unresolved risks;
- compare Confirmed scope and every acceptance check with the actual changed-file list, and explain any file that is not an obvious part of the authorized scope;
- update the checkpoint after major verification results and remove it only after the work is complete.

Lead the final response with the outcome. Explain what changed, why it changed, how it was verified, and any material limitations.
