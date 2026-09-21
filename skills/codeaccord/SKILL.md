---
name: codeaccord
description: Investigate, challenge, agree, implement, and verify software changes with one explicit agreement gate. Use for product requirements, bug fixes, refactors, configuration changes, and other codebase work where the agent should establish evidence and scope before editing instead of blindly accepting assumptions or immediately changing code.
license: MIT
metadata:
  author: CodeAccord contributors
  version: "0.1.0"
---

# CodeAccord

Turn a software change request into an evidence-based agreement, then carry that agreement through implementation and verification.

The user's desired outcome and explicit constraints are authoritative. Their diagnosis, proposed files, and preferred implementation are hypotheses to evaluate. Agree when the evidence supports them. Disagree plainly when they are incomplete, incorrect, risky, or less effective than an available alternative.

Use the user's language unless project instructions require another language.

## Lifecycle

Use one continuous lifecycle:

```text
Inspect -> Challenge -> Accord -> Build -> Verify
```

- **Inspect:** Establish the current behavior and relevant constraints from the actual project.
- **Challenge:** Test assumptions and compare meaningful alternatives.
- **Accord:** Present one concrete change brief and obtain one explicit confirmation.
- **Build:** Complete the agreed implementation, tests, and necessary documentation.
- **Verify:** Check the delivered behavior against the accord and report evidence.

Do not split this lifecycle across separate planning and implementation skills. Infer the current stage from the conversation and continue from the latest confirmed accord.

## Classify the change

Choose the mode from evidence rather than keywords:

- **Product change:** The user wants new behavior or a deliberate change to existing behavior.
- **Bug fix:** Existing behavior violates an established contract, documented behavior, or reproducible expectation.
- **Mixed change:** Resolving the defect also requires a product decision or new contract.

When classification is uncertain, investigate first. Ask the user only when the distinction changes the desired outcome or compatibility contract.

## Authorization boundary

A request such as “add this feature,” “help me implement this,” or “fix this bug” starts the lifecycle. It does not skip the accord by itself.

Before accord, use read-only investigation against product code, configuration, tests, logs, history, and documentation. Do not edit implementation files, tests, configuration, or product documentation.

The only file CodeAccord may create or update before accord is a durable change record selected under **Durable change records**. Creating that record does not authorize implementation.

Skip the separate accord only when the user explicitly asks to proceed immediately, says no review is needed, or has already confirmed the same concrete scope earlier in the conversation. Even then, inspect enough evidence to avoid implementing an unsupported assumption.

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

Produce a concise, reviewable brief after the investigation is sufficient.

For a product change, cover:

- desired outcome and boundaries;
- confirmed current behavior;
- assessment of the user's initial approach;
- recommended behavior and implementation direction;
- affected components and files;
- API, data, deployment, compatibility, and operational effects;
- acceptance criteria and verification;
- open decisions that genuinely require the user.

For a bug fix, cover:

- observed and expected behavior;
- reproduction or evidence;
- root cause and trigger;
- impact scope;
- proposed fix location and behavior;
- regression coverage;
- any compatibility or operational effects.

Keep the brief proportional to the change. Do not manufacture sections with no meaningful content. End with one direct request to confirm the complete scope when confirmation is still required.

## Durable change records

Decide whether the accord needs to survive outside the conversation. Create a record when any of these apply:

- work spans multiple modules, services, or repositories;
- public interfaces, persisted data, security boundaries, deployment, or operations change;
- several product decisions or unresolved branches must be tracked;
- implementation is likely to span sessions or require a handoff;
- the user requests a saved plan.

Skip the record for localized work that can be completed in the current session without losing material context.

When a record is needed:

1. Reuse a project-designated change directory when project instructions define one and it is compatible with this workflow.
2. Otherwise use `.codeaccord/changes/<kebab-case-name>.md` at the project root.
3. Tell the user that a durable record is being created, but do not ask for a separate confirmation.
4. Do not modify ignore rules or commit the record unless requested.
5. Maintain one record for the change; do not split it into proposal, design, specification, and task files.

Use this compact shape and omit empty optional sections:

```markdown
---
status: exploring | proposed | approved | implementing | verified
type: product | bug | mixed
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# <Change title>

## Outcome or problem

## Facts and evidence

## Decisions and recommendation

## Change scope

## Acceptance and verification

## Out of scope

## Open decisions

## Confirmation
```

Update the record as decisions change. Record the user's accord without inventing approval metadata. Mark it `verified` only after implementation and required checks actually pass. Do not sync or archive it automatically.

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
- update a durable record to `verified` only when the evidence supports it.

Lead the final response with the outcome. Explain what changed, why it changed, how it was verified, and any material limitations.
