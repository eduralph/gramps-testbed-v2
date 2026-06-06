# Catching up to the latest `pdca-harness` template

> How `gramps-testbed-v2` reconciles with the upstream template
> (`../pdca-harness`, currently **v0.7.0**). Read this before running `copier update` —
> a blind update will conflict-storm, for a reason worth understanding first.

## The situation: co-evolved trees, not a clean fast-forward

`.copier-answers.yml` pins `_commit: v0.2.0`, but this testbed's code is at roughly
v0.6-level. That is **not** drift to silently overwrite — it is because **this instance is
the source**: the harness features in template versions v0.2.1 → v0.7.0 were developed
*here first* and then generalized upstream. Nobody re-ran `copier update` since v0.2.0, so
the answers file is stale while the content co-evolved.

Consequence: the instance and template are largely **content-convergent** (same features),
but every harness file differs in wording (instance carries the gramps-specific form;
template carries the genericized form). A blind `copier update v0.2.0 → v0.7.0` therefore
3-way-merges two trees that *both* changed heavily — nearly every harness file conflicts,
and most conflicts are "same feature, different spelling." Plan for a careful merge, not a
fast-forward.

## What the instance genuinely LACKS (the real deltas to pull)

Short list — most of v0.3–v0.7 is already here:

- **Publish-on-accept in the flow.** The template wires publish into `flow.py`
  (`do_publish`, `publish.publish()` on accept; `cli --no-publish`); this instance's
  `flow.py` has **no** publish wiring — only standalone `pdca publish`. This is the main
  *behavioral* change an update brings. (Decision already taken: adopt it — keep the
  template ahead.)
- **The refreshed PCDA reference docs.** The instance's `PCDA/quality-cycle/` is v0.2.0-era;
  upstream added/​refreshed: `08-glossary.md`, the new **`09-parallel-lanes.md`** (the
  doctrine behind `docs/parallel-lanes.md`), the staleness fixes across `00–07`, and the
  publish/four-beats wording. Take these wholesale (they're generic, no gramps content).
- **Prose clarifications in the agent files** — e.g. reviewer "this is the canonical order
  the gates assemble / a row you omit is a verdict the human never sees", signoff &
  publisher "a step of the Check beat, not a beat", CLAUDE.md publish + `--no-publish`
  docs, Makefile `.PHONY` including `batch`/`publish` and the publish-in-flow comments.
  Minor; take the wording, keep any gramps specifics.

## What the instance is AHEAD on — do NOT regress

- **`cli.py` `_flow` empty-batch exit code.** This instance correctly returns **0**
  ("nothing in flight to drive — not an error", so a resumable re-run is success). The
  **template currently has a regression here — `return 1`** (a known pending fix, template
  v0.6.1). When you merge `cli.py`, **keep the instance's `return 0`**; do not take the
  template's `return 1`.

## Conflict-resolution rule (when you do merge)

For each conflicted file:

| Keep the **instance** version | Take the **template** version |
|---|---|
| Gramps-specific verbatim src: `leaves.py` Mantis/engine/Docker/GUI **prompt strings** (`_plan_prompt`, `_build_prompt` runner detail, `_publish_prompt` doc-16); `progress.py` the `grampstest-` container probe + `_compact_duration` (Tier-2) | Generic **structure/logic** refinements in those same files where they don't carry gramps strings |
| `pdca.toml` — the live `[[gates.checks]]` rows + Mantis tracker values | New generic stanzas / comments the template added |
| `.claude/settings.json` — `Bash(pytest:*)` and any gramps allow-list entries | New generic allow-list entries (e.g. `Bash(git -C:*)`) |
| Agent `.md` — gramps specifics (Mantis, `../gramps`, doc-16, run-verify) and the reviewer→**claude** fallback | Generic prose clarifications (the "step of Check beat", canonical-table notes) |
| `cli.py` `_flow` empty-batch `return 0` (see above) | `cli.py` `--no-publish` flag + publish threading |
| `flow.py` everything else (it matches) | `flow.py` **publish-on-accept** (`do_publish`, the publish loop) |
| `engine/**`, `wiki/**`, `results/**` (instance-only; template doesn't ship them) | New template files with no instance counterpart (the PCDA docs above, `templates/commit-msg.txt.tpl`, etc.) |

Rule of thumb: **take the template's generic refinements and new files; keep every
gramps-specific value, the live gates, and the reviewer→claude fallback.**

## Procedure

### Path A — Selective (recommended, given the co-evolution)
Pull just the real deltas; skip the conflict storm.
1. Copy the refreshed reference docs from `../pdca-harness/template/PCDA/quality-cycle/`
   over `PCDA/quality-cycle/` (they're generic `.md`; diff first to keep any local notes).
2. Adopt publish-on-accept in `flow.py` + `cli.py --no-publish` by hand from the template
   (the diff is small and self-contained).
3. Apply the prose clarifications to the agent `.md` files where worthwhile.
4. Do **not** bump `_commit` — you've reconciled by hand. (Or bump it to `v0.7.0` *only*
   after a real `copier update` per Path B, so the pin reflects truth.)

### Path B — Full `copier update` (to restore clean future updates)
1. **Clean the tree.** Commit or stash all WIP — `copier update` requires it. (Right now:
   the modified `wiki/.../16-guidelines.md` files and the untracked `process/` /
   `results/` items.)
2. `cd gramps-testbed-v2 && copier update --vcs-ref v0.7.0` (or `update` for the tag tip).
3. **Resolve conflicts** with the table above — expect many "same feature, different
   wording" hunks; resolving them re-aligns the pin without losing gramps content.
4. Re-run the offline guards and a live smoke: `make check`, then a `make rehearse` (and a
   small live `make flow ID=<one>` if you have capacity).
5. Commit. `_commit` is now `v0.7.0`, so the *next* update is small and clean.

## After catching up — verify
- `PYTHONPATH=src python3 -m unittest discover -s tests` green (the instance's own tests).
- `make rehearse ID=demo` reaches COMPLETE and, with publish-on-accept now wired,
  **dry-run publishes** (stub publisher → no real push).
- The cli still exits **0** on an empty resumable batch (`make flow CSV=<empty>` →
  `echo $?` is 0) — confirms the regression wasn't pulled in.
- `git -C ../pdca-harness describe --tags` shows the version you reconciled against.

## Going forward
Keep feeding generic harness improvements upstream (the `docs/template-feedback.md`
discipline) **and** re-running `copier update` periodically, so the pin stops drifting and
each catch-up stays a fast-forward instead of a co-evolution merge.
