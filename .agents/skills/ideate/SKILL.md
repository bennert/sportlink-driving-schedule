---
name: ideate
description: >
  Generate a structured ideation document exploring a problem space.
  Use when user says "ideate", "explore this problem", "write an ideation",
  or invokes /ideate. Creates numbered docs in docs/ideation/.
user_invocable: true
---

# /ideate — Structured Ideation Generator

You are a systems thinker. When the user describes a problem, opportunity, or area to explore, you generate a structured ideation document with brutal honesty about what's proven vs. aspirational.

## Process

### Step 1: Understand the Problem Space

Read the user's description. If anything is unclear, ask up to 3 questions:

- What's the actual problem (not the assumed solution)?
- What constraints exist (time, tech, team, budget)?
- What's been tried before?

### Step 2: Determine Sequence Number

Scan `docs/ideation/` for the highest existing number:

```bash
ls docs/ideation/[0-9]*.md 2>/dev/null | sort -t/ -k3 -n | tail -1
```

If no existing ideations or no `docs/ideation/` directory, create it and start at 001.

### Step 3: Generate the Ideation

Use this structure:

```markdown
# NNN: [Title]

**Date:** YYYY-MM-DD
**Status:** Active
**Author:** [user or inferred]

## Problem Statement

What's broken, missing, or suboptimal? Be specific and honest.

## Prior Art

What exists today? Competing approaches, existing tools, prior attempts.
For each: what works, what doesn't, and why.

## Proposed Approach

The recommended path forward. Distinguish clearly:
- **Proven:** We know this works because [evidence]
- **Likely:** Strong reasons to believe this works
- **Aspirational:** We hope this works but have no evidence yet
```

Use the template from `templates/ideation_template.md`.

### Step 4: Next Steps

- Save to `docs/ideation/NNN_[slug].md` (e.g., `docs/ideation/001_async-loader.md`)
- If the user wants a feature specification based on this ideation, offer to use `/feature-spec`
- Commit with: `docs(ideation): NNN_[slug]`

---

**Triggers:**
- `/ideate`
- "ideate [topic]"
- "explore this problem"
- "write an ideation"
