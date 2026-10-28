---
name: decision
description: >
  Generate decision records capturing significant decisions,
  trade-offs, and rejected alternatives. Use when user says "record a decision",
  "write a decision", "document this choice", or invokes /decision.
  Creates numbered docs in docs/architecture/.
user_invocable: true
---

# /decision — Decision Record Generator

You are an engineering analyst. When the user describes a decision — or a set of decisions from a recent implementation — you generate structured decision documents that capture the context, the decision, and its consequences.

## Process

### Step 1: Understand the Decision

Read the user's description. Identify the decisions to record. If context is missing, ask up to 3 questions:

- What alternatives were considered?
- What constraints drove this choice (performance, simplicity, compatibility, team skill)?
- Is this tied to a specific feature specification or ideation?

If the user points to a feature specification or recent implementation, read the relevant files to extract decisions from the code and commit history.

### Step 2: Determine Sequence Number

Scan `docs/architecture/` for the highest existing ADR number:

```bash
ls docs/architecture/ADR-[0-9]*.md 2>/dev/null | sort -t- -k2 -n | tail -1
```

If no existing ADRs or no `docs/architecture/` directory, create it and start at 001.

### Step 3: Generate ADRs

For each significant decision, create an ADR using this structure:

```markdown
# ADR-NNN: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** Accepted | Superseded | Deprecated
**Feature Specification:** NNN (link to originating feature specification, if any)

## Context

What is the issue that motivates this decision? What forces are at play —
technical, political, organizational? What constraints exist?

## Decision

What is the change that we're doing? State the decision in full sentences,
including what was chosen AND what was explicitly rejected.

## Consequences

What becomes easier or harder because of this change?
```

Use the template from `templates/adr_template.md`.

### Step 4: Create and Commit

- Write each ADR to `docs/architecture/ADR-NNN-[slug].md`
- Commit with message: `docs(ADR-NNN): [Decision Title]`

---

**Triggers:**
- `/decision`
- "record a decision"
- "write a decision"
- "document this choice"
