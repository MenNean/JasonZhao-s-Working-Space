# Brainstorming Skill

A Claude Code skill for turning ideas into fully formed designs and specs through natural collaborative dialogue.

**Use before any creative work** — creating features, building components, adding functionality, or modifying behavior. This skill explores user intent, requirements, and design before implementation.

## What it does

- Walks from raw idea to approved design spec via one-question-at-a-time dialogue
- Presents 2-3 approaches with tradeoffs before settling on one
- Writes a design doc (`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`)
- Self-reviews the spec for placeholders, contradictions, ambiguity, and scope
- Hands off to `writing-plans` for implementation planning

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/qwwiwi/brainstorming-skill ~/.claude/skills/brainstorming
```

Or use `skill-installer` if you have it configured.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main skill definition, checklist, process flow |
| `visual-companion.md` | Guide for browser-based visual brainstorming |
| `spec-document-reviewer-prompt.md` | Template for spec review subagent |
| `scripts/` | Visual companion server (Node.js + HTML frame) |

## Usage

Claude Code auto-invokes this skill when the user describes creative work. You can also invoke it manually:

```
Use the brainstorming skill to help me design a new feature for X.
```

## Visual Companion (optional)

For visual questions (mockups, layouts, diagrams), the skill offers a local browser-based companion. Run:

```bash
bash scripts/start-server.sh
```

It watches a directory for HTML files and serves the newest one. Claude writes mockups, you click to pick options, selections are logged back.

## Source

Adapted from [Anthropic Claude Code Superpowers](https://github.com/anthropics/superpowers). MIT licensed.

## License

MIT — see `LICENSE`.
