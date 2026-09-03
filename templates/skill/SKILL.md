---
name: skill-name-here
description: >
  What it does, concretely, in one or two sentences — the outcome, not the aspiration.
  Then: when to use it. Every situation and every phrasing a user would actually type, in
  every language they would type it in. Name the boundary against any near neighbour, so
  the two do not compete. This paragraph is the only thing Claude sees when deciding
  whether to load the skill; a skill that does not trigger does not exist.
license: Proprietary — © Richard Matos (Pol4720). See repository LICENSE.
---

# Skill Name

<!-- Who Claude is being while running this, and what "done" means — concretely enough to
     be checkable. A bar to clear ("could a hostile reviewer still find something?") works;
     an adjective ("be thorough") does not. -->

---

## Invocation contract

<!-- Every input shape to accept, so the user never has to write a prompt: a bare path, a
     bare instruction, an instruction plus a symptom they already know about, an
     instruction plus a scope limit. Say what changes about the deliverables in each case. -->

## Autonomy

<!-- What to do without asking — this should be most things.
     Then the narrow set worth interrupting for, stated specifically. A skill that asks too
     often is abandoned; one that never asks makes decisions that were not its to make. -->

---

## The rules

<!-- The two to four inviolable rules, stated as overriding everything else in the file.
     These are what stop a skill optimising for the appearance of success. Give each one a
     name and a reason — a rule with a reason survives cases you did not foresee. -->

### 1. <Rule name>

<!-- What it forbids, why the forbidden thing is tempting, and what to do instead. -->

---

## Workflow

<!-- Ordered phases. For each: what it produces, and WHY it comes where it does.
     Ordering that is not explained gets reordered by whoever reads it next. -->

### Phase 0 — <name>

### Phase 1 — <name>

---

## Deliverables

<!-- Exact format, exact location. If a file is written into the user's project, say the
     path precisely, and say what must never be overwritten. -->

---

## Leaning on the rest of the toolbox

<!-- Which other skills, MCP tools, subagents and project tooling this skill expects to
     use, and for what. Naming them makes them part of how the skill works rather than
     optional extras. -->

---

## Bundled resources

| File | When |
|---|---|
| `references/<name>.md` | Phase N — <what it holds> |

| Script | Does |
|---|---|
| `scripts/<name>.py` | <what it does> |

<!-- The validator checks that every path in backticks above actually exists. -->

---

## What finishing looks like

<!-- A checklist that can actually be verified, not a summary. Each line should be
     something you could be wrong about, and therefore something worth checking. -->

- [ ]
- [ ]
- [ ] You can name the specific things you could not do, and why.
