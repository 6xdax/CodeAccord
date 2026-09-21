---
name: codeaccord
description: Explore, agree, implement, and verify software changes with a read-only inspect-and-challenge loop, one explicit agreement gate, and one compact recovery checkpoint. Use for product requirements, bug fixes, refactors, configuration changes, and other codebase work where the agent should establish evidence and scope before editing instead of blindly accepting assumptions or immediately changing code.
license: MIT
metadata:
  author: CodeAccord contributors
  version: "0.3.1"
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

## Authorization boundary

A request such as “add this feature,” “help me implement this,” or “fix this bug” starts the lifecycle. It does not skip the accord by itself.

Before accord, use read-only investigation against product code, configuration, tests, logs, history, and documentation. Do not edit implementation files, tests, configuration, or product documentation.

The only file CodeAccord may create or update before accord is `.codeaccord/checkpoint.md` under **Recovery checkpoint**. It is temporary recovery state and does not authorize implementation.

The user may waive waiting at the separate agreement gate by explicitly asking to proceed immediately, saying no review is needed, or having already confirmed the same concrete scope earlier in the conversation. Even then, complete enough Explore to avoid an unsupported assumption and state the fixed Accord before Build; continue without waiting for another reply.

Answers to discovery questions are decisions, not implementation authorization. Once the user explicitly confirms the complete brief with language such as “approved,” “go ahead,” or an equivalent response in their language, treat the whole stated scope as authorized.

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

The initial Accord is the fixed exit from Explore. Produce it only after the user signals that the explored direction is ready to finalize. Render labels in the user's language, but preserve the following section order and meanings so readiness can be reviewed at a glance:

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

Keep every heading even for small changes, but keep its content proportional; one sentence is enough where appropriate. **Current facts** contains only evidence that affects the implementation decision, not a chronological investigation log. Present one final recommendation rather than preserving rejected alternatives unless a real user decision remains.

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

Before confirmation, keep a proposed delta under checkpoint **Unresolved** and do not overwrite the confirmed scope. After confirmation, merge it into the checkpoint's complete current state and remove it from **Unresolved**. During Build, pause for confirmation only when new evidence crosses an unapproved material boundary, and present only the delta. Reissue a full Accord only when the user explicitly requests it or no reliable baseline can be recovered.

## Recovery checkpoint

The conversation is the primary working surface. Use one short checkpoint only to recover the active change after context compaction, session resumption, or an interrupted implementation. It is a recovery cache, not a second specification system or a history archive.

Use exactly `.codeaccord/checkpoint.md` at the project root. Never create per-change files or accumulate completed records. Decide whether a checkpoint is needed from the task and context:

- create it when investigation or implementation is likely to span context compaction, a session boundary, or a long-running tool call;
- create it before editing for every non-trivial build;
- skip it only when the whole task is small enough to complete and verify in the current context without meaningful recovery risk.

Keep the checkpoint semantically current. Refresh it:

1. immediately after the user confirms the initial Accord or an Accord delta;
2. after any approved material scope change;
3. after an important implementation or verification milestone;
4. before a long-running command, test suite, delegation, or other operation that may interrupt the turn;
5. before compaction when the platform signals it or the remaining context indicates it is approaching.

Do not wait for a mechanical `PreCompact` hook to summarize the conversation. A command hook cannot infer unrecorded decisions reliably. Platform hooks may validate and reload the file, but the active agent owns the semantic update.

Treat **Confirmed scope** as the merged current Accord. Keep unapproved proposed changes under **Unresolved** until the user confirms them. A compaction or resume must never promote an unresolved delta into confirmed scope.

After compaction or session resumption, read the checkpoint before continuing. Then inspect repository status and relevant code because source and tests remain authoritative for implementation state. Treat the checkpoint as the latest confirmed product boundary; do not silently expand it from a generated compaction summary.

Keep it concise, normally no more than 500–800 tokens. Store decisions and state, not raw transcripts, long evidence, source code, logs, or secrets. `Current state` contains only conclusions needed to resume the task; do not turn it into a chronological investigation or implementation log. Use this shape and omit empty bullets rather than adding more sections:

```markdown
---
status: exploring | approved | implementing | verifying
updated: YYYY-MM-DDTHH:MM:SSZ
---

# Goal

## Confirmed scope

## Non-goals

## Current state

## Next action

## Acceptance checks

## Unresolved
```

When verification is complete and the final result has been reported, remove the checkpoint. If work remains incomplete or verification is blocked, keep it updated for recovery. Do not archive it automatically.

## Build

After accord:

1. Implement the entire approved scope and preserve unrelated user changes.
2. Update affected contracts, callers, configuration, migrations, tests, and documentation together.
3. Follow project-local instructions and established patterns.
4. Keep working through ordinary implementation failures without reopening the accord.
5. Remove dead code introduced or made obsolete by this change when it is safely within scope.

Do not create an OpenSpec change or another planning system unless the user explicitly requests it.

## Verify

Run focused checks first, then expand according to the actual impact. Verification must test the agreed behavior rather than merely mirror implementation details.

Before declaring completion:

- compare the result with every acceptance criterion;
- verify the original bug reproduction no longer fails when applicable;
- check affected contracts and callers;
- report commands actually run and their results;
- disclose remaining limitations, skipped checks, or unresolved risks;
- update the checkpoint after major verification results and remove it only after the work is complete.

Lead the final response with the outcome. Explain what changed, why it changed, how it was verified, and any material limitations.
