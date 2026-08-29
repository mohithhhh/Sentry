# Project skills

Claude Code skills scoped to the Sentry repo live here. Anything added under
this directory is available to anyone with the repo checked out (invoked as
`/<skill-name>`), unlike personal skills under `~/.claude/skills/`.

## Adding a skill

```
.claude/skills/<skill-name>/SKILL.md
```

Minimal template:

```markdown
---
name: <skill-name>
description: One-line summary of when to use this skill.
---

# /<skill-name>

Step-by-step instructions for what the skill should do.
```

- `name` and `description` are required frontmatter.
- Reference extra files (scripts, templates) by relative path from the same
  directory.
- No skills are defined yet — this repo is still scaffolding. A likely first
  candidate is a `dev-sentry` skill that knows how to run the backend
  (`uvicorn main:app --reload`) and frontend (`npm run dev`) together for a
  local smoke test, once there's real behavior to exercise.
