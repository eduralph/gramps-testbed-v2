# Host precondition: reviewer agent must be user-global

**Status:** interim workaround — tracked for removal by **pdca-harness #161**.

## Symptom

Every bundle's advisory **reviewer** step fails during `flow`, and `check-review.md`
becomes a `# Advisory review — NOT COMPLETED` §6 placeholder. The run log shows:

```
--agent 'reviewer' not found. Available agents: claude, Explore, general-purpose, Plan, statusline-setup
leaves: <bundle> — advisory review unavailable (reviewer leaf failed: … --agent reviewer … exit status 1)
```

## Why

The reviewer leaf runs in a temp **sandbox cwd** (the build-notes independence contract:
`_run_review_sandboxed`, `src/pdca_harness/leaves.py`). Claude Code (≥ 2.1.x) discovers
project subagents by walking up from the subprocess cwd, and the sandbox has no
`.claude/agents/` above it — so the project-local `reviewer` agent is invisible. The
builder leaf is unaffected because it runs from the repo root.

## Fix on this (or any) host until #161 lands

Symlink the project reviewer agent into the user-global agents dir so it resolves
regardless of cwd:

```bash
mkdir -p ~/.claude/agents
ln -sfn "$(git rev-parse --show-toplevel)/.claude/agents/reviewer.md" ~/.claude/agents/reviewer.md
```

This **preserves the independence contract** — only the agent *definition* is made
global; the sandbox cwd and the agent's `tools: Read, Bash, Grep, Glob` still gate which
files the reviewer can read (`build-notes.md` stays unreachable). It is host state, not
captured in the repo — hence this note, so parallel lanes / other sessions / other
operators reproduce it.

Verify: `test -f ~/.claude/agents/reviewer.md && echo ok`.

## When #161 lands

The durable fix seeds the sandbox with the agent definition, making this symlink
unnecessary. After re-vendoring the harness with that fix, remove the symlink and delete
this note.
