---
name: project-execution-framework
description: "Execute project-style tasks through a repeatable delivery loop: plan the work in playbook.md, create or update task scripts under scripts/, run them to produce output/, inspect results against acceptance criteria, iterate until valid, and summarize the final delivery. Use when Codex needs a structured project execution workflow, especially for tasks that should leave reusable planning, scripts, generated artifacts, logs, or traceable outputs in a project folder."
---

# Project Execution Framework

## Overview

Use this skill to turn a user request into a traceable project execution cycle. Keep the work organized around four files or folders: `project.md` for the framework definition, `playbook.md` for the current task plan, `scripts/` for executable task logic, and `output/` for generated results.

## Folder Contract

Use or create this structure in the active project folder:

```text
<project-name>/
+-- project.md
+-- playbook.md
+-- scripts/
|   +-- <task_name>.<ext>
+-- output/
    +-- <task_name>/
```

`project.md` is the stable framework document. Do not rewrite it for each task unless the user asks to change the framework.

`playbook.md` is task-scoped and may be overwritten for each new user request.

`scripts/` contains task scripts named after the task or execution unit.

`output/<task_name>/` contains generated artifacts, logs, intermediate files, and final results.

## Execution Workflow

### Phase 1: Plan

Parse the user request into a concrete plan and write `playbook.md`. Include:

- Task objective
- Inputs and constraints
- Ordered execution steps
- Expected output format and location
- Quality and acceptance criteria
- Status fields: current task, playbook version, execution round, latest error, and state

### Phase 2: Script

Create or update scripts for each execution unit in `scripts/`. Each script should define inputs, implement the core logic, write outputs under `output/<task_name>/`, and include clear error handling or logging.

Prefer small deterministic scripts for repeatable or data-heavy work. For simple tasks where a script adds no value, explain that choice in `playbook.md` and still preserve outputs when useful.

### Phase 3: Run

Run scripts in the order defined by `playbook.md`. Capture meaningful stdout, stderr, logs, or result summaries into `output/<task_name>/`.

### Phase 4: Iterate

Inspect output against the acceptance criteria. If results fail:

1. Identify the root cause.
2. Update `playbook.md` if the plan, assumptions, or acceptance criteria need correction.
3. Update the affected script.
4. Re-run from the relevant phase.

Repeat until the acceptance criteria pass or a true blocker requires user input.

### Phase 5: Deliver

Summarize the final result for the user. Include the relevant output path, what was generated or changed, what validation was performed, and any remaining risks or follow-up options.

## Playbook Template

Use this structure for `playbook.md` unless the task calls for a tighter format:

```markdown
# Playbook: <task name>

## Objective

## Inputs and Constraints

## Execution Steps

## Expected Outputs

## Acceptance Criteria

## Status

| Field | Value |
| --- | --- |
| Current task | <task name> |
| Playbook version | v1 |
| Execution round | 0 |
| Latest error | None |
| State | PLANNED |
```

## Operating Rules

- Keep project paths task-local. Do not reference unrelated project paths or contents.
- Name tasks and output folders with concise, filesystem-safe identifiers.
- Update the status fields as the work moves from planned to running, iterating, validated, or blocked.
- Do not treat generated output as final until it has been checked against the acceptance criteria.
- Preserve enough logs or notes for the next Codex instance to understand what ran and why.
