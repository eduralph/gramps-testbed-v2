---
title: 'GEPS 049: Versioned Addon API surface and 2 axis lifecyle model'
categories:
- Developers/General
- GEPS
- Pages with broken file links
managed: false
source: wiki-scrape
wiki_revid: 131311
wiki_fetched_at: '2026-06-27T17:58:11Z'
---

# GEPS 049: Addon API Versioning and Plugin Lifecycle

## Type

Standards Track

## Status

Draft — under review. Background discussion at [Discourse thread 9491](https://gramps.discourse.group/t/architectural-thoughts-on-the-addon-mechanism-api-versioning-lifecycle-states-manager-behaviour/9491) and [GitHub Discussion \#2297](https://github.com/gramps-project/gramps/discussions/2297). Current review thread for this proposal: [GitHub Discussion \#2311](https://github.com/gramps-project/gramps/discussions/2311).

## Authors

- Eduard Ralph (eduralph) — proposal, specification, and analysis
- Claude (Anthropic) — drafting, structural editing, and the griffe API-stability analysis (see [Credits](#Credits))

## Abstract

This GEPS proposes two coupled changes to the Gramps addon mechanism:

1.  A versioned, explicitly-declared **Addon API surface**, decoupled from the Gramps release version. Addons declare a range against the API contract (e.g. `addon_api=">=1.0,<2.0"`) instead of a literal Gramps release string (`gramps_target_version="6.0"`).
2.  A two-axis **lifecycle model** that separates *code quality* (the existing `status=` field, extended) from *maintenance state* (a new field), so that the Addon Manager, CI, and human maintainers can disambiguate "in development" from "abandoned" without inventing new tribal knowledge.

It also subsumes and reconciles two parallel proposals already on the table:

- [Discussion \#2297](https://github.com/gramps-project/gramps/discussions/2297) (Doug Blank): move `gramps_target_version` to semver range matching and collapse the per-Gramps-version branches in `addons-source` to a single source tree.
- [PR \#2250](https://github.com/gramps-project/gramps/pull/2250) (Doug Blank): tuple form for `requires_mod` to disambiguate PyPI install name from importable name (Pillow/PIL, python-dateutil/dateutil, psycopg-binary/psycopg).

This GEPS is a **collection of phased, independently-landable changes**, not a single all-or-nothing proposal. Each part ships value alone:

- PR \#2250 is self-contained and should land on its own review schedule — it is not gated by adoption of this GEPS.
- Range-based `gramps_target_version` (#2297) can land independently as a parser change with backwards-compatible literal-string handling.
- The `check_mod` fallback proposed below (Phase 1a) is a ~10-line bug fix that resolves the Pillow/PIL case today without any other change in this GEPS.
- The lifecycle model (Part 2) and repository consolidation (Part 3) are additive to the above and can land in any order.

The four core parts interact only in the single-sourcing story — see Part 4 for where they compose — but none gates the others. Reviewers can accept, reject, or defer each part on its own merits.

## Motivation

### Symptoms

- **Per-release busywork.** Every Gramps minor release triggers a cycle of bumping `gramps_target_version` across ~140 addons. Most bumps are no-op code-wise; just a string change. Maintainers who have moved on can't do them, so the addon rots from a process failure rather than a code failure.
- **Status field is overloaded.** `status=UNSTABLE` currently signals both "early in development, expect bugs" (the Mediawiki-extension-status sense Nick Hall designed it for) and "abandoned, needs porting." Combined with `include_in_listing=False`, addons end up in ambiguous limbo. A lint-cleanup pass on `addons-source` in May 2026 surfaced 12–13 such directories — neither published nor maintained, neither failing CI nor passing it. The CI can't tell which is which. The Addon Manager UI can't tell users. Maintainers can't tell what to do with them.
- **Per-Gramps-version branches multiply state.** `maintenance/gramps60`, `maintenance/gramps61`, and master all carry near-identical addon source. PRs are cherry-picked across branches. Translations require careful curation against the latest branch only (Nick: "Backporting changes to `po` files is not advisable"). All of this exists because `gramps_target_version` is a literal, not a range.
- **Dependency declarations are not portable across Gramps versions.** `requires_mod` uses a single string that has to serve as both an importable name (for `find_spec()` at runtime) and a PyPI install name (in error messages and, if PR \#2250 lands, in `pip install` suggestions). For matching-name packages (`networkx`, `boto3`) this is fine. For divergent-name packages (Pillow/PIL, python-dateutil/dateutil, psycopg-binary/psycopg, gramps-gedcom7/gramps_gedcom7) it forces a choice between a string that passes the runtime check and one that informs users correctly. This concretely surfaced in addons-source PRs \#878 and \#890, which had to declare `requires_mod=["PIL"]` rather than `["Pillow"]`.
- **No declared migration paths.** For addons that maintain persistent state on disk (database backends, configuration files, indexes, caches), there is no metadata channel for "upgrading addon X v1.x to v2.0 requires running this hook." addons-source PR [\#781](https://github.com/gramps-project/addons-source/pull/781) (PostgreSQLEnhanced v1.5.2 → v1.7.3) is the concrete case: breaking changes ship with migration scripts the user has to run manually because Gramps has no way to know they exist. See the PR for the specific defects this produces.

## Rationale

This section states what the proposal is trying to achieve (Goals), what it deliberately does not attempt (Non-goals), and the scope and terminology that bound it.

### Goals

1.  Decouple addon compatibility declaration from Gramps release cadence.
2.  Eliminate the "bump string in every gpr file per Gramps release" busywork for the majority of addons that need no code change.
3.  Make maintenance state explicit and machine-readable, separately from code quality.
4.  Surface lifecycle state in the Addon Manager UI so users can make informed decisions.
5.  Provide a declared migration path for addon major version bumps.
6.  Keep `.gpr.py` files purely declarative (no conditional logic).
7.  Stay forward-compatible with eventual move to JSON registration files (per Nick's stated direction).

### Non-goals

- **Not** replacing Gramps's existing major/feature/maintenance versioning scheme with semver. Gramps core's release versioning stays as-is.
- **Not** enforcing a fixed API surface forever. The surface can grow; major bumps remain possible.
- **Not** a single-repo-for-everything restructure. `addons-source` and `addons` remain separate (source and built listings).
- **Not** silently auto-migrating user data. Any future mechanism for addon-state migration would be explicit and addon-author-owned; the present GEPS does not specify such a mechanism (see [Part 5](#Addon_state_migration_(Part_5))).

### Terminology and scope

**"Addon" vs "plugin".** The two terms are used precisely throughout this document, following the convention Nick Hall stated in [Discussion \#2311](https://github.com/gramps-project/gramps/discussions/2311): **all addons are plugins, but not all plugins are addons**. "Plugin" is the technical term for any extension using the registration mechanism (`register()`, `.gpr.py`, the `PTYPE_*` taxonomy), and appears in the codebase and in the API surface where it is embedded (`gramps.gen.plug`, the user plugin directory, plugin-type constants). A **built-in plugin** is a plugin shipped as part of core Gramps and maintained by the core team. An **addon** is a **third-party plugin** — one that lives in `addons-source`, is maintained by someone outside the core team, and is installed by users via the Addon Manager rather than shipped with core. The distinction that matters for this GEPS is *who maintains it and where it lives*: the lifecycle and maintenance problems the proposal addresses arise precisely because addons are third-party and the core team does not control their upkeep. Where the term has become muddled in Addon Manager UI strings, cleanup is editorial work, not a metadata change, and is out of scope.

**What this proposal is about.** The problem domain is the addon **supply chain**: how a third-party plugin declares its compatibility with Gramps, how that declaration is versioned independently of the Gramps release cadence, how its maintenance state is made explicit and surfaced to users, how its dependencies are declared portably, and how the source repository and built listings are structured to remove per-release busywork.

**What it changes in the plugin mechanism, and what built-in plugins gain.** The proposal does touch the plugin *mechanism*, not just the addon ecosystem — and this is deliberate. Several parts are **registration-schema and loader changes that apply to every plugin**, built-in plugins included:

- The `addon_api`, `maintenance_state`, and extended `status` fields are additions to the `register()` schema that every plugin uses. A built-in plugin can carry them too.
- The documented Addon API surface ([Phase 1d](#Phase_1d:_Document_the_Addon_API_surface)) is the same contract built-in plugins depend on; documenting it serves both.
- The `requires_mod`/`requires_gi` tuple forms and the `check_mod` fallback are loader-level dependency-checking improvements that benefit any plugin declaring dependencies.

Built-in plugins **profit** from these without needing the rest: clearer dependency declarations, a documented contract they also rely on, and the option to declare `addon_api` for the same forward-compatibility benefit. They simply do not *need* the orchestration-heavy parts, because the core team maintains them on the core release cycle.

**What is addon-specific (built-ins do not need it).** The orchestration parts apply only to third-party addons: the repository consolidation and single-source model ([Phase 4](#Phase_4:_Repository_consolidation)), the PyPI-style distribution and listing flow, the maintenance-state cron / staleness / adopter machinery, and the elimination of per-release `gramps_target_version` busywork. Built-in plugins live in the core tree, ship with core, and are never "orphaned" in the addon sense, so none of this orchestration is relevant to them.

**Audience / "Use" categorization.** Distinct from the lifecycle metadata proposed here. The addon "Use" field (visible in wiki listings) was simplified when the Addon Manager was created — "Beginning user", "Normal user", and "Intermediate user" consolidated into "Everyone" (Nick Hall, Discussion \#2311). It categorizes *audience*, not *state*, and is unrelated to `status=` or `maintenance_state=`. Out of scope, noted only to disambiguate.

## Specification

The proposal has four core parts (1–4). Each ships value independently; see the [abstract](#Abstract) for the independently-landable framing. Forward-looking items that this work enables or that reviewers raised but that fall outside the scope above are collected in [Future Work](#Future_Work).

### Part 1: The Addon API surface

#### What is "the Addon API"

The Addon API is the set of names, signatures, and behaviours that Gramps core promises to keep stable for addon authors. It is *not* the entire Gramps codebase; an addon poking at `gramps.gen.db.generic._Generic.__some_private__` has always been on its own.

In scope:

- `gramps.gen.plug` — the registration interface, all `PTYPE_*` / `CATEGORY_*` constants, the `register()` signature for each plugin type, plugin base classes (`Plugin`, `ImportPlugin`, `ExportPlugin`, `DocGenPlugin`, etc.).
- The documented subset of `gramps.gen.lib` (object model: `Person`, `Family`, `Event`, etc., and their public methods).
- The documented subset of `gramps.gen.db` (transaction handles, `commit_*` signatures, iterators).
- The documented subset of `gramps.gui` hook points used by view, gramplet, and tool plugins.
- The `.gpr.py` registration schema itself (which fields are valid, their types, their semantics).
- The set of **translatable string *keys* (msgids)** in `gramps.pot` that addons may reference via `_()`. This is a consequence of the build-time translation dedup (see [the translation paragraph in Phase 4](#Migration_plan)): the addon build subtracts Gramps's strings from the addon catalog on the assumption that Gramps will provide them at runtime, so removing or renaming a Gramps msgid that an addon references observably breaks that addon (it falls through to an untranslated string). The msgid set is therefore part of the surface; the *translations* of those msgids (msgstr values) are not — translation freshness is handled by the runtime fallback chain and changes to msgstr never constitute an API event. See [Versioning scheme](#Versioning_scheme) and [Detecting API changes](#Detecting_API_changes) for how msgid changes are versioned and detected.

Out of scope (not part of the API surface; may change without an API version bump):

- Internal helpers in `gramps.gen.utils.*` not documented for addon use.
- Implementation details of dialogs, widget internals, GUI assembly code.
- Anything in a module whose name begins with an underscore.
- The *translations* (msgstr values) of UI strings — these change freely and are resolved at runtime via the gettext fallback chain. (The string *keys* — msgids — are in scope, per above.)

The first concrete deliverable of this GEPS is a documented enumeration of the in-scope surface, published as part of the Gramps developer documentation. Until that document exists, addon authors are inferring the contract from source, which is what produces the current churn.

**What "decoupling" does and does not mean.** An addon depends on Gramps intrinsically — a CRUD addon calls `db.commit_person()`, `Person.set_primary_name()`, the transaction handles, the object-model methods; it cannot function without Gramps providing those symbols with those signatures and behaviours. That dependency is the addon's reason for existing and cannot be removed by any versioning scheme. This GEPS does not claim to decouple addons *from Gramps*; it decouples the addon's compatibility *declaration* from Gramps's release *cadence*. The addon still depends on Gramps — but it depends on a *named, stable contract* (`addon_api`) that spans many releases, rather than on a *specific release number* (`gramps_target_version`) that churns every time Gramps ships anything. The in-scope surface above *is* that dependency, made explicit and given a version of its own. So a CRUD addon declaring `addon_api=">=1.0,<2.0"` is saying "I rely on the data-model and db contract as it stood at API 1.0, and Gramps has promised not to break it before 2.0" — the dependency is named and pinned to a slow-moving contract, not eliminated.

#### Versioning scheme

The Addon API uses semver 2.0.0:

- **MAJOR** — incremented on any breaking change to the surface (removal, signature change, behavioural break). For the string surface specifically: **removal or rename of a `gramps.pot` msgid** that addons may reference is a MAJOR trigger. gettext keys are exact strings, so a rename is structurally identical to removal-of-old plus addition-of-new — an addon referencing the old form gets an untranslated string at runtime.
- **MINOR** — incremented on additions to the surface (new fields, new helpers, new optional parameters). Adding a new msgid to `gramps.pot` is additive and does not break existing addons.
- **PATCH** — incremented on bug-fix-only changes within the surface (a method that was specified to return X but returned Y). Changes to a msgid's *translation* (msgstr) are not an API event at all — they are resolved at runtime via the fallback chain and never require a bump.

This is independent of Gramps's release version. A single API major version typically spans multiple Gramps feature releases. Illustrative trajectory, assuming Phase 1 of the [migration plan](#Migration_plan) lands in Gramps 6.2 (see that section for the 6.1 / 6.2 sequencing question):

| Gramps release | Addon API | Comment |
|----|----|----|
| ≤ 6.1 | *(none)* | No declared API. Compatibility via legacy `gramps_target_version`. |
| 6.2.0 | 1.0.0 | Initial formal declaration of the Addon API surface. |
| 6.2.4 | 1.0.0 | Patch release of Gramps; API surface unchanged. |
| 6.3.0 | 1.1.0 | Feature release; adds `Citation.set_source_handle()`. Old addons keep working. |
| 6.3.2 | 1.1.1 | Bug fix in `EventRef.get_role()` behaviour. |
| 6.4.0 | 1.2.0 | Adds new gramplet hook. Old addons keep working. |
| 7.0.0 | 2.0.0 | Breaking changes; addon authors required to verify. |
| 7.1.0 | 2.1.0 | Additions on top of 2.x. |

If Phase 1 lands in 6.1 rather than 6.2, shift the table down one minor version. The scheme is independent of which concrete release anchors API 1.0.

The benefit of the scheme concentrates at maintenance-release granularity, where the API surface is empirically stable. Running [griffe](https://mkdocstrings.github.io/griffe/)'s breaking-change detection across the proposed API surface (`gramps.gen.plug._pluginreg`, `gramps.gen.lib`, `gramps.gen.db`, `gramps.gen.const`) over the actual Gramps release history:

| Transition | Type | Breakages | Comment |
|----|----|----|----|
| v6.0.0 → v6.0.4 | maintenance (mid) | **0** | No API surface change. |
| v6.0.0 → v6.0.8 | maintenance (full 6.0.x) | **1** | Only the `COPYRIGHT_MSG` string value changed. |
| v5.1.6 → v5.2.0 | minor bump | 58 | Expected: minor releases introduce changes. |
| v5.2.4 → v6.0.0 | major bump | 224 | Expected: major releases introduce changes by design. |

Minor and major releases introduce changes by design — that is what those version numbers mean, and the scheme reflects them. The decisive row is the maintenance series: across the entire 6.0.x line (eight patch releases) the API surface is essentially unchanged. The current scheme nonetheless forces every addon to bump `gramps_target_version` for each of those patch releases, producing the ~140-addons-times-N-releases of busywork described in the [Motivation](#Symptoms). A range-based `addon_api` lets an addon declare `>=1.0,<2.0` once and stay compatible across the whole maintenance series with no further action. **That is the concrete benefit: the per-maintenance-release bump, which is pure overhead, disappears.** Whether the minor-version breakage would benefit from a deprecation cycle is addressed in [Detecting API changes](#Detecting_API_changes).

#### Declaration

A new optional field `addon_api` is added to `register()`:

``` python
register(
    GRAMPLET,
    id="example-gramplet",
    name=_("Example Gramplet"),
    description=_("An example gramplet demonstrating the registration fields"),
    version="1.0.0",
    addon_api=">=1.0,<2.0",          # NEW
    gramps_target_version=">=6.0",   # transitional: see migration plan
    status=STABLE,
    maintenance_state=PUBLISHED,     # NEW: see Part 2
    fname="example_gramplet.py",
    gramplet="ExampleGramplet",
    gramplet_title=_("Example"),
    height=200,
    authors=["Jane Developer"],
    authors_email=["jane@example.org"],
)
```

Range syntax follows [PEP 440](https://packaging.python.org/en/latest/specifications/version-specifiers/) (parsed via `packaging.specifiers.SpecifierSet`), not python-semver. Rationale:

- `packaging` is already a transitive dependency of every Python install that has `pip`; adding it as a declared dep is cheap.
- PEP 440 handles pre-releases, local versions, and epochs correctly. Hand-rolled comparators get these wrong in subtle ways.
- The same parser can be reused for `requires_mod` version pins (Part 4), so the codebase doesn't carry two incompatible version-spec dialects.
- `>=1.0,<2.0` is unambiguous in both PEP 440 and semver dialects, so the most common form reads the same either way.

PEP 440 also supports **exclusion** via the `!=` operator, which handles the case where a specific Gramps release is known broken for an addon. Example raised by emyoulation in [Discussion \#2311](https://github.com/gramps-project/gramps/discussions/2311): a built-in plugin ships with a bug in Gramps 6.0.5 that corrupts trees; an emergency addon version replaces it via the existing Plugin lib (GENERAL) supersession mechanism (see [Future Work](#Addon-supersedes-built-in_mechanism)); the addon can opt out of the specific buggy release:

``` python
addon_api=">=1.0,<2.0,!=1.0.5"
```

Users on the excluded Gramps version see no compatible addon entry, rather than getting an install that cannot work safely.

#### Compatibility check

Gramps core declares which API versions it implements in a module-level constant:

``` python
# gramps/gen/plug/__init__.py
ADDON_API_VERSIONS = ["1.7.2"]
```

`valid_plugin_version()` checks `addon_api` against this. If `addon_api` is absent, fall back to the legacy `gramps_target_version` check for the transition period.

A future version of this check can support multiple installed API versions side-by-side (e.g. a Gramps that publishes both 1.x and 2.x APIs during a transition release), but that is not required for v1 of the proposal.

#### Detecting API changes

A version number on the addon API surface is only useful if there is a mechanical answer to *when to bump it*. Without one, the number drifts: developers over-bump out of caution (devaluing the contract), or under-bump out of inertia (silently breaking addons). Three tiers, composable, in increasing investment:

**Tier 1 — Define the surface explicitly.** Today there is no canonical list of "this is what addons may import." Anything in `gramps.*` is fair game and addons reach into whatever happens to work. The first concrete step is curating the list:

``` python
# gramps/api_surface.py
ADDON_API_MODULES = [
    "gramps.gen.plug._pluginreg",  # registration contract
    "gramps.gen.plug",              # base plugin classes addons subclass
    "gramps.gen.lib",               # data model
    "gramps.gen.db",                # database access
    "gramps.gen.utils",             # utility functions
    "gramps.gen.const",             # constants
    "gramps.gui.editors",           # GUI editor base classes (GUI addons)
    "gramps.gui.plug",              # GUI plugin support
]
```

Anything not on this list is internal. Addons that import from outside it do so at their own risk; Gramps core is free to change those modules without API-version implications. Curation is human work that happens once and is maintained when new addon-relevant modules emerge.

**The list above is a starting hypothesis, not a verified specification.** The defensible way to commit to it is empirically: scan every addon in `addons-source` for its `gramps.*` imports, aggregate the resulting set, and review what shows up. Modules that no addon imports do not need formal API status. Modules outside `gramps.gen.*` that show up in addon import graphs (e.g. addons that reach into `gramps.gui.*` or `gramps.plugins.*`) are either accidental couplings to internals (which should be documented as private and migrated to a public alternative) or genuine extension points that warrant inclusion. The audit is itself part of Phase 1/2 work, not done in this GEPS — the list above should be treated as a hypothesis to verify against the addon corpus, not as a final commitment. Empirical derivation also has the side benefit of surfacing previously-undocumented dependencies on internals (e.g. an addon importing from `gramps.plugins.lib.libhtml`) before the API contract is frozen around them.

**Tier 2 — Mechanical detection via [griffe](https://mkdocstrings.github.io/griffe/).** A CI workflow runs on every PR to gramps master and on every release branch:

``` bash
for mod in $ADDON_API_MODULES; do
    griffe check "$mod" -b HEAD -a v6.0.0 --output-format json
done | jq '... aggregate breakages ...'
```

The CI rule: if griffe reports any breakage and the `ADDON_API_VERSIONS` constant has not been bumped in the same PR, the check fails. This makes the version a forced, conscious choice rather than something to remember. Griffe's breakage taxonomy (parameter removed, parameter changed default, parameter added as required, return type changed, public object removed, base class removed, attribute type changed) maps cleanly onto MAJOR/MINOR/PATCH:

- **MAJOR** — any of: parameter removed, parameter added as required, public object removed, base class removed, return type changed (incompatibly).
- **MINOR** — any of: parameter added with default, new public object, attribute added.
- **PATCH** — no API-surface change; only implementation changed.

Griffe surfaces some breakages that are technically detected but addon-irrelevant — most prominently "attribute value changed" for module-level constants whose *value* moved but whose *name* stayed (e.g. `COPYRIGHT_MSG` updated). A small allowlist of "value-change-only is OK for this attribute" entries handles those without weakening the rule.

**Tier 3 — Empirical validation through addon test coverage.** Signature-equivalent changes can still break addons through behavioural drift (a method that used to accept `None` now raises, an iteration order changes, a default fallback path is removed). Static analysis cannot catch these. As more addons gain test coverage — unit tests within each addon's own source tree, and integration tests that exercise the parts of the Gramps API the addon depends on — those tests can be run against Gramps release candidates as part of a release readiness check. Regressions surface as failures in addons whose declared `addon_api` range *should* permit the new Gramps; each such regression is then either a Gramps bug (revert or version-bump) or an addon over-promising its compatibility range.

Tier 3 is not implementable on day one: addon test coverage in the current ecosystem is sparse. But the mechanism follows naturally from Tiers 1 and 2 once coverage exists, and the proposal does not depend on it for the core `addon_api` contract to work. Encouraging addon authors to add tests — and providing scaffolding in `addons-source` for those tests to run in CI — is a parallel workstream that this GEPS makes more valuable but does not require.

The three tiers compose: Tier 1 defines *what* is API; Tier 2 detects *whether* it changed mechanically; Tier 3, as it becomes available, would identify *whether anyone was actually relying on* the thing that changed. Tiers 1 and 2 are sufficient for the `addon_api` contract to work; Tier 3 sharpens it over time.

**Deprecation policy as a complement.** Breaking changes go through one feature release marked `@deprecated` (with a warning) before removal. Griffe sees the deprecation marker and accepts a breaking change in the next major bump without surprise. This is the same policy used by Django, FastAPI, and others, and it converts "is this safe to remove?" from a judgment call into a paperwork question.

**Enforcement is mechanical.** The CI rule for accepting a breaking change without external review is: griffe records the symbol as `@deprecated` in the prior feature release's API snapshot. Removing or breaking a symbol that was never marked `@deprecated` requires either reversing the change, adding a deprecation cycle and waiting one release, or an explicit reviewer override in the PR with an "intentional break, no deprecation possible" note. The deprecation snapshots are stored alongside the gramps repository (a `docs/api_history/` directory updated on each tagged release works); the check then becomes a cross-reference rather than a judgment call, and the audit trail for "why is this break in this release" lives in the snapshots themselves.

The mechanism described here is also what generated the empirical data in the [Versioning scheme](#Versioning_scheme) section above — running griffe across the existing Gramps git history produced the breakage counts cited there. The data is a historical measurement; the proposal's recommendation rests on that measurement holding broadly true going forward, which is itself something Tier 2 in CI would verify on an ongoing basis.

**Tier 4 — string-surface detection via POT diff.** Griffe covers the code surface but not the string surface (the `gramps.pot` msgids addons reference, per [the In-scope list](#What_is_&quot;the_Addon_API&quot;)). Detecting msgid removals/renames between Gramps versions is mechanical and uses standard gettext tooling (`msgcomm`), in three layers:

1.  **Layer 1 — what changed in Gramps.** `msgcomm --less-than=2 --unique old/gramps.pot new/gramps.pot` yields msgids present in the old version but absent in the new — the removed-or-renamed set (a rename appears as removal of the old key). Additions are informational only.
2.  **Layer 2 — filter to addon-relevant.** Intersect that set with the union of all addon `template.pot` files (`xgettext -j` to combine, then `msgcomm --more-than=1` against the removed set). The result is the precise list of msgids that Gramps removed/renamed *and* at least one addon references — the set that warrants a MAJOR `addon_api` bump. For most releases this is small or empty; maintenance releases should produce zero.
3.  **Layer 3 — per-addon impact report.** `template.pot` source references (`#: AddonName/file.py:NN`) survive aggregation, so a short script maps each affected msgid back to the addons (and source lines) that reference it. This is what the maintainer and affected addon authors actually consume: "addon X references string Y which is being removed; rebuild against the new Gramps or your declared `addon_api` should not include it."

This plugs into the same CI gate as Tier 2: a Gramps release that removes/renames an addon-referenced msgid without bumping `ADDON_API_VERSIONS` MAJOR fails the check. The tooling is ~15–20 lines for Layers 1–2 plus ~30 lines of Python for Layer 3; `msgcomm` is part of standard gettext and already present wherever addons are built. Layers 1–2 distinguish nothing about *why* a msgid disappeared (rename vs. genuine removal) — both are MAJOR triggers, so the tool doesn't need to; the maintainer reviews the (typically short) Layer 3 report to confirm the bump is warranted.

### Part 2: Lifecycle (two orthogonal axes)

#### Quality axis (existing `status=` field, extended)

Nick Hall's original intent for `status` is preserved: it signals how mature/finished the addon's **code** is, modelled on the [Mediawiki extension status](https://www.mediawiki.org/wiki/Extension_status). We extend with the two new values Nick proposed in post 7 of the Discourse thread:

| Value | Meaning | Visibility |
|----|----|----|
| `UNSTABLE` | In the early stages of development. | Dev mode only. (existing) |
| `EXPERIMENTAL` | Usable, but expect many bugs. | In listing with warning. (existing) |
| `BETA` | Ready for wider testing. | In listing. (existing) |
| `STABLE` | Complete. | In listing. (existing) |
| `UNCHECKED` | Maintainer has not verified against the current Addon API version. Loadable; UI shows a banner. | In listing with warning. (NEW) |
| `BROKEN` | Known not to work in current state. Treated like `UNSTABLE` for visibility. | Dev mode only. (NEW) |

State transitions on the quality axis are driven by the addon author, except for `STABLE → UNCHECKED`, which is set automatically when the installed Gramps's Addon API version moves outside the addon's declared range. The author bumps the addon's `addon_api` range, retests, and sets back to `STABLE`.

#### Maintenance axis (new `maintenance_state=` field)

Orthogonal to quality. An addon can be `STABLE` and `ORPHANED` simultaneously — the code works, but nobody is on the hook for keeping it that way.

| Value | Meaning | CI/UI behaviour |
|----|----|----|
| `INCUBATING` | New addon under development, or existing addon being actively ported. | Not in user listing. CI gating active (active dev needs feedback). Time-bound: 12 months without graduation triggers review. |
| `PUBLISHED` | Released to users, actively maintained. | Full CI, full listing visibility. |
| `DEPRECATED` | Still loadable; on a path to removal. Requires `removed_in` field giving target Gramps version. | UI banner: "Going away in Gramps X." Encouraged to point to a replacement via `superseded_by`. |
| `ORPHANED` | No active maintainer. The addon may still be operational, but nobody is on the hook for keeping it that way. See [the rationale below](#Why_a_separate_field_rather_than_inferring_from_the_maintainer_list) for why this is an explicit state rather than inferred from `maintainers=`. | Stays loadable for existing users. UI banner: "No longer maintained, looking for adopter." CI gating relaxed to warnings. |
| `ARCHIVED` | Moved to `addons-source/archive/AddonName/`. Not built. Source preserved for history. | Not in listing. Not buildable. Not discoverable via Addon Manager. |

State transitions on the maintenance axis:

- **INCUBATING → PUBLISHED**: Author declares ready. Reviewer signs off. Quality is whatever the author claims independently.
- **PUBLISHED → DEPRECATED**: Author or maintainer team declares. `removed_in` required.
- **PUBLISHED → ORPHANED**: Driven by the periodic cron described below.
- **ORPHANED → PUBLISHED**: An adopter steps forward and updates `maintainers=`. No code change required to switch state.
- **DEPRECATED → ARCHIVED**: After the `removed_in` Gramps version ships.
- **ORPHANED → ARCHIVED**: After a configurable orphan window (default 24 months) with no adopter.

#### Why a separate field rather than inferring from the maintainer list

One could argue that a separate field is redundant because maintenance state is *derivable*: an empty `maintainers=` means orphaned, a populated one means maintained, and the rest can be inferred from commit activity. That is the strongest form of the case against a dedicated field.

This GEPS proposes `maintenance_state=` anyway. Six reasons, in roughly decreasing order of weight:

1.  **Five states, not one.** The field has to encode `INCUBATING`, `PUBLISHED`, `DEPRECATED`, `ORPHANED`, and `ARCHIVED`. The `maintainers=` field can in principle carry information about *one* of those — orphaned, implicitly, via emptiness. The other four cannot be inferred from a contact list at any threshold. Even if we accept "`maintainers=` covers orphaned," we still need explicit metadata for the other four. The asymmetric scheme — one state inferred from emptiness, four explicit — is more cognitive load than the uniform scheme.
2.  **Empty does not equal orphaned.** A missing or empty `maintainers=` field could mean: (a) the addon was never assigned a maintainer (true for several legacy addons that predate the field), (b) the maintainer was removed during a cleanup pass, or (c) the listed maintainer left the project. Only (c) is "orphaned." The other two are "we have no record." The Addon Manager UI banner ("looking for adopter") and the adopter-finding query both need to distinguish these cases; an explicit enum value does that, an inferred-from-emptiness rule does not.
3.  **Populated does not equal actively maintained.** The 12–13 `UNSTABLE`, `include_in_listing=False` addons surfaced in the May 2026 lint-cleanup pass on `addons-source` *do* have entries in their maintainer fields. Some of the listed maintainers stopped engaging with the project years ago. `maintainers=` is contact information; it has no temporal dimension. Effective maintenance state is determined by *activity*, and activity is what the maintainer-departure cron tracks — but the cron has to write its conclusion *somewhere*, and the contact list is the wrong place to write it. Writing the conclusion to a dedicated state field is what makes the conclusion machine-readable for the Addon Manager and CI.
4.  **Some transitions can't be modelled by editing a contact list at all.** `PUBLISHED → DEPRECATED` is an announcement with a target removal version. `INCUBATING → PUBLISHED` is a deliberate sign-off. `DEPRECATED → ARCHIVED` is a removal event. None of these can be encoded by adding or removing names from `maintainers=`. If we accept that these need an explicit field, then adding `ORPHANED` to the same field is the consistent choice.
5.  **Parallel to the precedent already set by `status=`.** Code quality could, in principle, be inferred from CI artefacts, issue counts, and test pass rates. We don't infer it; we declare it via `status=`. The argument for declaring quality applies equally to declaring maintenance state: explicit, single-source-of-truth metadata that every consumer reads from the same place. Inference rules embedded in N consumers diverge; a field does not.
6.  **Decouples state from contact list, which matters socially.** If "remove name from `maintainers=`" is the only way to flag an addon as orphaned, the orphaning act doubles as the act of removing a person's name from a record. People are reasonably reluctant to do that, particularly with long-standing contributors who simply moved on. With an explicit `maintenance_state=` field, the listed maintainer can stay listed (as historical author / past contact) and the state can move to `ORPHANED` independently. This sounds cosmetic but is what determines whether the mechanism actually gets exercised in the project's social context.

A reasonable fallback position, if the full field is contested: introduce `maintenance_state=` with the four uncontroversial values (`INCUBATING`, `PUBLISHED`, `DEPRECATED`, `ARCHIVED`) and leave `ORPHANED` out of the initial set. The Addon Manager can still infer "no maintainer" from empty `maintainers=` for UI purposes in the interim. This loses (2) and (6) above but keeps the rest of the lifecycle machinery intact. The full five-state version remains the recommendation; the four-state fallback is offered as the smallest scheme that still does useful work.

#### Detecting maintainer departure

This is the only part of the lifecycle that needs process beyond metadata. A periodic GitHub Actions cron in `addons-source` runs monthly and:

1.  For each addon, computes "days since last commit touching this addon's directory" (excluding lint/translation-aggregator commits, which are identifiable by author and message).
2.  Cross-references the `maintainers=` field with the [Addons MAINTAINERS](wiki:Addons_MAINTAINERS) wiki list.
3.  When days-since-last-commit exceeds a threshold (default 540 days, ~18 months) and the addon is still `PUBLISHED`, opens a tracking issue tagging the listed maintainers.
4.  After a response window (default 90 days) without maintainer activity on the issue, an addons-source committer can flip the addon's `maintenance_state` to `ORPHANED` via a PR.

This is mechanical surfacing, not automation of the state change. A human decision is always in the loop. The cron exists to make sure the decision is *taken* rather than indefinitely deferred.

#### MAINTAINERS wiki integration

The [Addons MAINTAINERS](wiki:Addons_MAINTAINERS) wiki page can be restructured similar to [Portal:Translators](wiki:Portal:Translators), where "Vacancy" entries explicitly advertise orphaned addons. This is editorial work outside the scope of this GEPS, but the metadata proposed here supports it: an addon's `maintenance_state=ORPHANED` is what flags it as a Vacancy candidate.

### Part 3: Source repository structure

#### Current structure (problem)

    addons-source/
    ├── maintenance/gramps51/    (branch)
    ├── maintenance/gramps52/    (branch)
    ├── maintenance/gramps60/    (branch)
    ├── maintenance/gramps61/    (branch)
    └── master/                  (currently 6.2-targeting)

    addons/
    └── master/
        ├── gramps51/
        │   ├── download/
        │   └── listings/
        ├── gramps52/
        ├── gramps60/
        └── gramps61/

Each Gramps minor release creates a new branch in `addons-source` and a new directory in `addons`. PRs are cherry-picked. Translations are curated against the latest branch. The maintainer (Gary Griffin) walks a bulk-edit + `make.py` ritual each release.

#### Proposed structure

    addons-source/                              (source of truth; single branch)
    └── master/
        ├── AddonName/
        │   ├── AddonName.gpr.py                # declares addon_api range; one current version
        │   ├── AddonName.py
        │   ├── po/                             # per-addon translations
        │   │   ├── template.pot                #   strings extracted from this addon
        │   │   ├── fr-local.po                 #   per-locale addon translations (→ .mo at build)
        │   │   └── de-local.po
        │   ├── test/
        │   └── README.md
        ├── OtherAddon/
        │   └── ...                             # ~140 addons, one current version each
        └── po/                                 # top-level: the Weblate translation surface
            ├── addons.pot                      #   aggregated + deduplicated across all addons
            ├── fr.po                           #   per-locale; what translators edit in Weblate
            └── de.po

            │  make.py build   → download/
            │  make.py listing → metadata/ + index.json
            ▼

    addons/                                     (build artifacts + index; append-only, served over HTTP)
    └── master/
        ├── download/                           # versioned tarballs, retained indefinitely
        │   ├── AddonName-1.5.0.tgz
        │   ├── AddonName-2.0.0.tgz
        │   └── AddonName-2.0.1.tgz
        ├── metadata/                           # one JSON per addon, listing ALL its published versions
        │   ├── AddonName.json
        │   └── OtherAddon.json
        └── index.json                          # lightweight: addon IDs + last-modified timestamps

![[_media/addon_repo_structure.png|The two-repository model: addons-source (the source of truth, holding one current version per addon, with per-addon po/ translations and a top-level po/ for Weblate) produces, via make.py build and make.py listing, the addons artifact store — append-only versioned tarballs in download/, one metadata JSON per addon in metadata/, and a lightweight index.json for cheap change checks.]]

Notes:

- **One source per addon, current version only.** `addons-source` carries one current version of each addon. Cherry-picking across maintenance branches goes away. Gary's per-release bulk-edit ritual goes away. Git history is the audit trail for any prior version that needs to be reconstructed.
- **Two-level translations.** Each addon keeps its own `po/` (`template.pot` + `<lang>-local.po`, compiled into the addon's `.mo` at build time), and a top-level `po/` holds the aggregated, deduplicated `addons.pot` plus the per-locale `<lang>.po` files Weblate operates on. This is the existing structure; single-sourcing just means each level exists once rather than once per maintenance branch (see [Phase 4 translation](#Migration_plan)).
- **`addons` as an artifact store.** Old tarballs in `download/` are retained indefinitely. Users running an older Gramps still get the correct tarball because the metadata filter resolves their `addon_api` match to the right historical version.
- **Per-addon metadata + lightweight index.** Rather than one monolithic listing, `metadata/<Addon>.json` holds every published version of that one addon, and `index.json` is a small file of addon IDs plus last-modified timestamps. The Addon Manager fetches `index.json` once, then fetches an addon's `metadata/<Addon>.json` only when the user views or installs it (see [Listing semantics](#Listing_semantics) below).
- **Maps to the existing two-repo split.** This is not a new repository design — `addons-source` and `addons` already exist as separate repos today. The change is that `addons-source` goes from per-Gramps-version branches to a single branch, and `addons` goes from per-Gramps-version subdirectories to a single download tree plus per-addon metadata and one index.
- **Pattern is the same as pip/PyPI.** `addons-source` is the source repo; `addons` is the index. PyPI retains old wheels forever; we retain old `.tgz` files forever. `index.json` is the simple-index analogue; `metadata/<Addon>.json` is the per-project metadata analogue.

**Retrieving an old version (worked example).** A user is running a Gramps release that implements addon API 1.x. They install MyAddon, which has both v1.5.0 and v2.0.0 published. The Addon Manager:

1.  Fetches `addons/master/index.json` once, to see which addons exist and what changed.
2.  Fetches `addons/master/metadata/MyAddon.json` when the user opens MyAddon, and filters its version entries by `addon_api` compatibility against the running Gramps's API version. Only the v1.5.0 entry matches.
3.  Downloads `addons/master/download/MyAddon-1.5.0.tgz`.

When the same user later upgrades Gramps to a release implementing API 2.x, the Addon Manager re-runs the filter on the same `metadata/MyAddon.json`; this time v2.0.0 matches, and the user is offered the upgrade.

**Building a new version (worked example).** The MyAddon maintainer ships a v2.0.1 patch:

1.  Edit in `addons-source/master/MyAddon/`; bump `version=` in the `.gpr.py` from `2.0.0` to `2.0.1`.
2.  `make.py build MyAddon` produces `MyAddon-2.0.1.tgz` in `addons/master/download/`.
3.  `make.py listing MyAddon` regenerates only `addons/master/metadata/MyAddon.json` (appends the v2.0.1 entry; v2.0.0 and v1.5.0 entries remain) and updates MyAddon's row in `index.json`. The other ~140 addons' files are untouched.

![[_media/api_bump_flow.png|API generation bump flow: an external trigger (a Gramps release implementing a new API generation) prompts the author to update one addon's .gpr.py and rebuild. Only that addon's tarball, its metadata entry, and its index.json timestamp change (new entries shown in green); the other ~140 addons' files are untouched. No addons-source restructuring, no new branches, no per-API-version subdirectories.]]

**Backporting across major versions (the uncommon case).** If MyAddon at v2.0.0 needs a security fix that also has to apply to v1.5.0 (because there are still Gramps users who cannot upgrade to API 2.x), three options:

- **Ephemeral rebuild from history.** `git checkout` the v1.5.0 tag in `addons-source`, apply the fix, build, push the new tarball to `addons/master/download/MyAddon-1.5.1.tgz`. The mainline source stays on v2.x.
- **Long-lived support branch.** Maintain a `support/1.x` branch in `addons-source` for this specific addon. Resurrects the per-branch maintenance problem at the addon level, which is the cost of long-term parallel support.
- **Declare older versions EOL.** Mark the v1.5.0 entry in the addon's `metadata/MyAddon.json` as deprecated (or remove it). Users on older Gramps lose the addon; the addon author isn't on the hook for back-versions.

Most addons will not need any of these — the common case is linear version progression. The third option is the recommended default for addons whose authors haven't committed to long-term parallel support.

#### Listing semantics

The listing is split into two levels, matching the PyPI simple-index pattern: a lightweight top-level `index.json`, and one `metadata/<Addon>.json` per addon containing every published version of that addon.

`index.json` is small — addon IDs plus last-modified timestamps — so the Addon Manager can fetch it on every open to answer "did anything change?" cheaply:

``` python
{
    "example-gramplet": {"updated": "2026-05-20T19:15:00Z"},
    "myaddon":          {"updated": "2026-05-23T22:02:00Z"},
    ...
}
```

`metadata/<Addon>.json` is fetched on demand, only when the user views or installs that addon. It carries a `versions` array, one entry per published version:

``` python
{
    "id": "example-gramplet",
    "name": "Example Gramplet",
    "versions": [
        {
            "version": "1.0.0",
            "addon_api": ">=1.0,<2.0",            # author's declaration
            "tested_against": ["6.0.4", "6.0.5"], # CI-verified set; empty until Tier 3 coverage exists
            "status": "STABLE",
            "maintenance_state": "PUBLISHED",
            "tarball": "download/ExampleGramplet-1.0.0.tgz",
            "tarball_sha256": "...",
            "requires_mod": [...],
            "requires_gi": [...],
            "removed_in": null,                   # set only if DEPRECATED
            "superseded_by": null,                # optional pointer to replacement
        }
    ]
}
```

The Addon Manager filters the `versions` array client-side by `addon_api` compatibility against its own implemented API version, then offers the highest matching version. Multiple versions of one addon coexist in the same file, each with its own `addon_api` range, so an addon that genuinely differs across API generations needs no separate listing file:

``` python
"versions": [
    {"version": "1.5.0", "addon_api": ">=1.0,<2.0", ...},
    {"version": "2.0.0", "addon_api": ">=2.0,<3.0", ...},
]
```

This is the same model pip / PyPI uses: `index.json` is the simple index, `metadata/<Addon>.json` is the per-project metadata, and old `.tgz` files in `download/` are retained like old wheels. The cost is a one-line client-side filter; the benefit is that publishing a new version of one addon rewrites only that addon's metadata file plus one row of `index.json`, never a monolithic catalog — so per-addon publishing has no central-file contention.

**Claimed vs. tested compatibility.** `addon_api` is the author's declared compatibility range. `tested_against` is the set of concrete Gramps versions the addon's tests have actually been run against in CI (Tier 3 in [Detecting API changes](#Detecting_API_changes)). Until addon test coverage exists in the ecosystem, `tested_against` stays empty and the Addon Manager uses `addon_api` alone. Once coverage starts to exist, the Addon Manager can surface the verified subset alongside the claimed range: "compatible with Gramps 6.0.x (CI-verified against 6.0.4, 6.0.5, 6.0.6)." A user running 6.0.8 then sees that the addon claims compatibility but has not been re-verified for their specific version — informative without being alarming, and the gap is something the user, the author, or the addons-source maintainer can act on.

#### User plugin directory

The per-version layout under `~/.gramps/grampsXX/plugins/` stays unchanged. This is what allows two Gramps versions to coexist on one machine with potentially different installed addons.

What changes:

- **Cross-version persistence of installed state.** When a user upgrades Gramps 6.1 → 6.2, the Addon Manager looks at the installed state in `~/.gramps/gramps61/plugins/` and offers to bring forward any addon whose `addon_api` range covers the new Gramps's API version. The user does not have to re-discover and re-install everything.
- **Independent update notifications.** Periodic listing checks, prompting when a newer addon version is available. This functionality is partially in place already and needs to be surfaced more visibly.

### Part 4: Dependency declarations

This part folds in [PR \#2250](https://github.com/gramps-project/gramps/pull/2250).

#### Problem statement

`requires_mod` is checked at runtime by `check_mod()` in `gramps/gen/utils/requirements.py`, which calls `find_spec(name)` on the declared string. For matching-name packages this works. For divergent-name packages it does not:

| Pillow          | PyPI: `Pillow`, importable as `PIL`                    |
|-----------------|--------------------------------------------------------|
| python-dateutil | PyPI: `python-dateutil`, importable as `dateutil`      |
| psycopg-binary  | PyPI: `psycopg-binary`, importable as `psycopg`        |
| gramps-gedcom7  | PyPI: `gramps-gedcom7`, importable as `gramps_gedcom7` |

`requires_mod=["Pillow"]` fails the runtime gate even on systems with Pillow installed, because `find_spec("Pillow")` returns `None`. addons-source PRs \#878 (gramps60) and \#890 (gramps61) had to declare `["PIL"]` instead, which then makes the error message and install hint wrong.

#### Tuple form (PR \#2250)

``` python
requires_mod = [
    ("PIL", "Pillow>=10.0"),                # importable, pip spec
    ("dateutil", "python-dateutil>=2.8"),
    ("gramps_gedcom7", "gramps-gedcom7>=0.4.0"),
]
```

Adopted as proposed. The runtime gate checks `find_spec("PIL")`, the install hint references `pip install "Pillow>=10.0"`, and the version pin is enforced via `importlib.metadata.version("Pillow")` compared against `packaging.specifiers.SpecifierSet`.

#### Backward-compatibility fallback for plain-string form

The tuple form is the recommended declaration going forward, but addons targeting a Gramps version that pre-dates \#2250 cannot use it (the older parser will reject the tuple). To let those addons single-source across the transition, the runtime check is extended:

``` python
def check_mod(name):
    if find_spec(name) is not None:
        return True
    # Fallback: maybe `name` is the distribution name, not the importable name.
    try:
        dist = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        return False
    top_level = dist.read_text("top_level.txt")
    if not top_level:
        return False
    return any(find_spec(line.strip()) is not None
               for line in top_level.splitlines() if line.strip())
```

Empirically `importlib.metadata.distribution("Pillow").read_text("top_level.txt")` returns `"PIL\n"`, so plain `requires_mod=["Pillow"]` resolves correctly via the fallback. This is a ~10-line pure-additive change to `check_mod`:

- Matching-name packages still take the fast `find_spec` path.
- The fallback never makes a failing check succeed unless the package is actually installed.
- Backportable to `maintenance/gramps60` and `maintenance/gramps61` independently of the rest of this GEPS.

This is a *mitigation*, not a complete answer. It fixes the import-name/install-name divergence for the plain-string form, but it does not handle *version pinning* from a plain-string declaration. An addon that must pin `gramps-gedcom7 >= 0.4.0` still requires the tuple form, and therefore still requires a Gramps that has \#2250 merged. This is acceptable: pinned addons are a smaller surface than name-divergent ones, and "needs a recent Gramps" is a reasonable constraint for addons declaring version pins.

#### requires_gi

Parallel issue: `check_gi` compares the declared `("GExiv2", "0.10")` against an exact `gi.require_version()`. addons-source PR \#829 moved EditExifMetadata to a dynamic GExiv2 version on gramps61, exposing that single-source addons that work on both 6.0's hard pin and 6.1's flexible path have no portable declaration.

Proposal: extend `requires_gi` to accept range specifications using the same PEP 440 syntax:

``` python
requires_gi = [
    ("GExiv2", ">=0.10"),     # range
    ("Gtk", "3.0"),           # exact, equivalent to "==3.0"
]
```

For backward compatibility, a bare version string is interpreted as exact equality (matching today's behaviour).

#### Relationship to PR \#2308 (PyPI wheel installer)

[PR \#2308](https://github.com/gramps-project/gramps/pull/2308) (Doug Blank, "Add Python PyPI wheel installer for addon module dependencies") replaces the previous subprocess-based pip invocation with a stdlib-only wheel installer in `gramps/gen/utils/pypi.py`. The motivation is that `pip` as a subprocess does not work reliably in frozen bundles (Windows AIO is a cx_Freeze binary; Mac `.app` bundles do not have a usable `sys.executable`). The new installer fetches wheels from the PyPI JSON API, verifies SHA-256, and extracts them via `zipfile`, without depending on any external binary.

Key behaviours relevant to this GEPS:

- **Stdlib-only wheel installer for frozen bundles** (Windows AIO, Mac `.app`). Supports both pure-Python (`py3-none-any`) and compiled wheels with platform-tag matching (Windows: `win_amd64`/`win_arm64`/`win32`; macOS: `macosx_X_Y_arm64`/`x86_64`/`universal2`).
- **pip fallback** for source, snap, and flatpak environments, which handles compiled packages on Linux via manylinux without needing those tag families implemented in the stdlib code.
- **`top_level.txt` lookup in the install path.** Before extracting a downloaded wheel, the installer reads its `top_level.txt` metadata to discover the importable name; if that name is already importable, extraction is skipped. This is the same metadata channel proposed for Phase 1a's `check_mod` fallback, used in a different position in the pipeline.
- **Hardened `check_mod()`.** After `find_spec()` succeeds, the function now calls `import_module()` to catch compiled extensions whose native dependencies are missing — a real failure mode in bundled apps (originally addressed in PR \#2303 and ported here).

PR \#2308 is undergoing review as of mid-May 2026, with positive testing reports from contributors on multiple addons (LifeLineAncestorChart, TMGimporter, ChatWithTree, S3 Upload). Nick Hall has indicated the bug-fix subset should target the `maintenance/gramps61` branch.

**Relationship to this GEPS.** \#2250, \#2308, and the Phase 1a `check_mod` fallback are three independent pieces of one coherent design:

- **PR \#2250 (tuple form)** lets addon authors declare both the importable name and the pip spec when they diverge.
- **PR \#2308 (wheel installer)** makes "install this dependency" actionable in environments where subprocess pip does not work, and incidentally handles the install-side of the divergent-name case via `top_level.txt`.
- **Phase 1a (`check_mod` fallback)** handles the check-side of the divergent-name case: when an addon declares `requires_mod=["Pillow"]` and PIL is already installed (e.g. via system package), `check_mod` can recognise the package as satisfied rather than triggering an install attempt that \#2308 would then skip-extract anyway.

The three are complementary, not redundant. With all three in place, the divergent-name problem is solved at both check time (no spurious "missing" verdicts) and install time (no spurious downloads). With only \#2250 + \#2308, the worst case is a redundant PyPI fetch that ultimately no-ops via `top_level.txt` — wasteful but not broken. Phase 1a's value is therefore correctness-of-state-reporting rather than functional necessity, which lowers its urgency without removing its usefulness.

## Addon Manager UI changes

These are the user-facing surface of the metadata changes above. None are blocking for the metadata to land; they can be implemented incrementally.

- **Status column shows both axes.** "Stable / Published" vs "Stable / Orphaned" vs "Unchecked / Published" — quality slash maintenance.
- **Banners:**
  - `DEPRECATED`: "This addon will be removed in Gramps X.Y. See \[replacement\] for an alternative." Banner sourced from `removed_in` and `superseded_by`.
  - `ORPHANED`: "No longer actively maintained. Looking for an adopter — see \[link\]."
  - `UNCHECKED`: "Not yet verified for this Gramps version. May work; report issues if it does not."
  - `BROKEN`: only visible in dev mode; banner is "Known to be broken in this Gramps version."
- **Cross-version persistence prompt on Gramps upgrade.** "You had these addons installed in Gramps 6.1. They are compatible with 6.2. Install now?"
- **Independent update notifications.** Background listing check, surfaced via a non-blocking indicator.

## Migration plan

This GEPS is non-trivial. Sequencing matters. The phases below are designed so each lands as a self-contained, shippable change, and the value increases monotonically with each phase.

At the time of writing (May 2026), Gramps 6.0 is current stable and Gramps 6.1 is in active development. Realistic earliest landing for any item in this proposal is 6.1 or 6.2, depending on when each item clears review relative to 6.1's feature freeze. Larger items targeting 6.1 are unlikely; smaller, well-scoped, bug-fix-shaped items are plausible. The phases below are version-agnostic in framing, with concrete target windows noted.

**Who acts when.** A deliberate property of the rollout is that addon authors are not asked to act in Phases 1, 2, or 3. Phase 1 is Gramps core changes only — existing `.gpr.py` files keep working unchanged. Phase 2 (`addon_api` rollout) is run as a maintainer-driven bulk audit: `make.py audit-addon-api` derives the proposed range from each addon's existing `gramps_target_version`, runs griffe to verify, and emits per-addon patches that the addons-source maintainer commits directly for the mechanically safe cases. Phase 3 (lifecycle states) follows the same audit pattern with the staleness heuristic. Author input is solicited only for the small minority of cases where the audit cannot derive a value with confidence. **Phase 4 is the first phase that materially requires addon-author action** — and even then, only for authors with cross-branch divergence to resolve, open PRs to retarget, or personal forks to consolidate. Authors of stable addons whose source is identical across maintenance branches see no action required in Phase 4 either; the maintainer-side consolidation happens around them. This sequencing protects sporadic and semi-active contributors from being asked to relearn the metadata surface multiple times: the only *contributor-facing* relearning is the one in Phase 4, and the audits in Phases 2–3 are themselves the mechanism that makes that one transition manageable when it arrives.

### Phase 1: Foundations

The four Phase 1 items have very different review surfaces and can land independently.

#### Phase 1a: `check_mod` fallback

A ~10-line pure-additive change to `gramps/gen/utils/requirements.py` that uses `importlib.metadata` to resolve distribution-name vs import-name divergence. Bug-fix-shaped; resolves the Pillow/PIL case today without any other change in this GEPS.

**Realistic target:** Gramps 6.1 if review timing allows, otherwise 6.2. Backportable to `maintenance/gramps60` independently of this GEPS.

This item is a candidate for a standalone PR independent of the rest of the proposal. Acceptance does not require buying into anything else.

#### Phase 1b: Range-acceptance for `gramps_target_version`

Range-acceptance for `gramps_target_version` in isolation. Plain `"6.0"` stays valid; `">=6.0"` and `">=6.0,<7.0"` work. Parser is `packaging.specifiers.SpecifierSet`.

**Realistic target:** Gramps 6.1 or 6.2. The change is small but affects the registration parser, which is a more sensitive surface than the runtime gate. 6.2 is the safer assumption; 6.1 is possible if Doug or Nick takes it on early.

#### Phase 1c: PR \#2250 (`requires_mod` tuple form) and parallel `requires_gi` tuple form

PR \#2250 already exists and is awaiting review. The parallel `requires_gi` work is a near-copy.

**Realistic target:** PR \#2250 — whatever release the existing PR lands in. The `requires_gi` parallel: same release as \#2250 if scoped onto that PR, otherwise the next feature window.

#### Phase 1d: Document the Addon API surface

Publish an enumeration of in-scope names as part of developer documentation. Highest-leverage item in this proposal — the rest is metadata around a contract that has to exist first — but also the most labour-intensive and the one with the least clear ownership.

**Realistic target:** Gramps 6.2. Unlikely to fit into 6.1's remaining feature window.

After Phase 1, the dependency-declaration pain is resolved (1a + 1c) and the per-release addon-bump ritual is optional rather than mandatory (1b).

### Phase 2: API version

1.  Declare initial Addon API version (1.0.0) as of the Gramps release where Phase 1d lands. Add `ADDON_API_VERSIONS` constant. Document increment policy in developer docs.
2.  Add `addon_api` field to `register()`. Compatibility check prefers `addon_api` when present, falls back to `gramps_target_version`.
3.  Update `make.py listing` to emit the lightweight `index.json` plus per-addon `metadata/<Addon>.json` files (see [Listing semantics](#Listing_semantics)) alongside the existing per-Gramps-version listings during the transition.

**Realistic target:** Gramps 6.2 or 6.3. Depends on Phase 1d's landing. The initial API version cannot be declared before the surface itself is documented.

After Phase 2, new addons can declare against the API instead of Gramps releases. Existing addons keep working unchanged.

### Phase 3: Lifecycle states

1.  Add `maintenance_state` field to `register()`. Default value `PUBLISHED` for backward compatibility.
2.  Add `UNCHECKED` and `BROKEN` to allowed `status` values.
3.  Implement Addon Manager UI banners.
4.  Stand up the maintainer-departure cron in `addons-source` with a long initial threshold (24 months) to avoid false positives on stable-but-quiet addons.

**Realistic target:** Gramps 6.3 or 6.4. Independent of Phase 2's API-version mechanism but pairs naturally with it because the UI surface for both lands in the Addon Manager.

After Phase 3, the addon catalogue has accurate lifecycle data and the Addon Manager surfaces it.

### Phase 4: Repository consolidation

1.  Migrate `addons-source` to a single-branch model. Existing `maintenance/gramps*` branches are frozen as read-only history.
2.  Migrate `addons` repository to the `index.json` + per-addon `metadata/` model. Existing per-Gramps-version listing files stay as redirects/aliases for old Gramps installs.
3.  Deprecate `gramps_target_version` (still accepted, but emits a registration warning when used in addons that also declare `addon_api`).

**Realistic target:** coordinated with Gramps 7.0 or a designated transition release. This is the largest disruption and should land at a clear "before/after" version boundary so users and the maintainer can reason about it as a single switchover rather than a creeping migration.

### Tooling for the transition

The phase rollouts are largely mechanizable. The major tooling categories:

**Phase 1 — verification fixtures.** Each of the 1a–1d landings ships with an automated regression suite: a divergent-name test matrix (Pillow/PIL, python-dateutil/dateutil, psycopg-binary/psycopg, gramps-gedcom7/gramps_gedcom7 and the rest of the known cases) for the `check_mod` fallback; a parser equivalence suite verifying that every existing `gramps_target_version` literal still resolves to the same Gramps versions after the range parser lands; and tuple-vs-string equivalence tests for PR \#2250 and its `requires_gi` parallel. Standard CI work, called out so it doesn't get skipped.

**Phase 2 — bulk audit for `addon_api`.** A `make.py audit-addon-api` step that parses every addon's `.gpr.py`, derives a proposed `addon_api` range from the existing `gramps_target_version` plus a griffe-based check of what the addon actually imports against Gramps, and emits per-addon patches. The maintainer commits the mechanically safe cases directly; only addons where griffe disagrees with the literal declaration get flagged for human review. Reduces the ~140-author coordination problem to "Gary runs the audit; exceptions surface."

**Phase 3 — bulk audit with staleness heuristic.** The same audit shape, applied to `maintenance_state`. Default rule: commits within the last 12 months → `PUBLISHED`; no commits in 12+ months → `PUBLISHED` with a suggestion of `ORPHANED` for the maintainer to review; explicit deprecation markers in README or commit messages → `DEPRECATED`. Suggestions surfaced, never auto-applied.

**Phase 4 — branch reconciliation.** The hardest phase, but mechanizable in two pieces:

- A **branch-divergence analyzer** that compares the live writable branches at consolidation time (whichever `maintenance/grampsXX` branches are still active alongside `master` when Phase 4 lands — likely a later maintenance series than the 6.0/6.1 named today) per-addon and categorizes each as identical, linear progression, true divergence, or branch-specific files. Most addons fall in the first two categories and consolidate mechanically; only the third category requires human resolution, and isolating it from the easy cases is the leverage. Branches that are already frozen read-only by then (current 6.0, 6.1) are excluded from the analysis — those serve as historical references, not consolidation inputs.
- **Strangler-fig listing transition** — generate both old and new listing formats from the same source during the transition window so the Addon Manager in both old and new Gramps versions sees something valid. The old format is removed once the transition is complete.

Translation consolidation under Phase 4 leans on Weblate's existing per-source-project flow rather than custom tooling; the consolidation merges the per-branch `po/` trees into the new single-source layout once, after which Weblate operates normally.

**Two specific questions raised by Nick Hall in Discussion \#2311:**

- **Top-level `po/` directory in `addons-source`?** Yes — already present on the `maintenance/gramps60` and `maintenance/gramps61` branches of upstream `gramps-project/addons-source`, and used by the current Weblate workflow. The structure is two-level: each addon still has its own `<Addon>/po/` with a per-addon `template.pot` and per-locale `<lang>-local.po` files (which end up compiled into the addon's `.mo` at build time), AND there is a top-level `po/` containing `addons.pot` (an aggregated, deduplicated template across all addons) plus per-locale `po/<lang>.po` files that Weblate operates on. The GEPS doesn't change this structure; under single-source consolidation each level just exists once rather than once per maintenance branch.
- **Which Gramps version do we aggregate against?** The aggregation is more sophisticated than a simple merge. Looking at `make.py`'s `aggregate_pot()` (around line 287): it concatenates every addon's `template.pot`, then uses `msgcomm` against `$GRAMPSPATH/po/gramps.pot` to **subtract** strings that Gramps already has — the result is `po/addons.pot` containing *only strings unique to addons* (i.e., strings Gramps doesn't translate). Weblate translates that. `make.py extract-po` then distributes the resulting per-locale translations back into each addon's `<Addon>/po/<lang>-local.po`. The subtraction is purely a translator-facing optimization: it keeps shared strings (`Cancel`, `Person`, …) out of the Weblate component so translators don't re-translate what Gramps already covers. It is built against the current stable Gramps.

**Recommended build process: play the shared translations back into each addon (Nick Hall's proposal in Discussion \#2311).** Deduplication keeps the *translator* view lean, but if nothing further is done the addon's compiled catalog omits shared strings and relies on Gramps's catalog at runtime — which is the [string-surface dependency](#What_is_&quot;the_Addon_API&quot;) discussed above. To make each addon's shipped catalog self-contained, the build adds a **merge-back** step: after `extract-po`, merge the current Gramps `<lang>.po` translations for any shared strings the addon references into that addon's `<lang>-local.po`, before compiling to `.mo`. The result:

1.  Translators still see only addon-unique strings on Weblate (dedup preserved — no change to their workload).
2.  Each addon ships a **self-contained** catalog: every string it references, shared or unique, has a translation baked in as of build time.
3.  At runtime, the fallback chain (Gramps primary, addon fallback) still serves Gramps's *current* translation for shared strings the running Gramps has — so freshness is preserved — and falls back to the addon's baked-in copy for anything the running Gramps lacks.

This narrows the window in which the string-surface dependency can bite: an addon is correct for every string it referenced as of its last build, regardless of what the running Gramps later does to those strings. The merge-back must run on **every build** (not once), so that strings an addon adopts between builds are captured against the Gramps current at that build.

**What merge-back does and does not solve.** It does not *eliminate* the string-surface dependency — that dependency is intrinsic, exactly as an addon's dependence on `db.commit_person()` is intrinsic (see [What "decoupling" does and does not mean](#What_is_&quot;the_Addon_API&quot;)). The residual case is real: if an addon references a Gramps string, Gramps later removes or renames it, and the addon has not rebuilt since, the baked-in copy still covers it — but a string the addon adopts *after* its last build, that Gramps removes *before* the addon's next build, degrades (the user sees the untranslated source string). Whether that degradation is acceptable or warrants action is precisely why the Gramps string contract is treated as part of the Addon API surface: removal/rename of an addon-referenced msgid is a MAJOR `addon_api` event, detected mechanically (see [Tier 4](#Detecting_API_changes)). Merge-back is the build-time mitigation that keeps the common case correct; the API-surface treatment is the contract-level handling of the residual. The two are complementary — merge-back narrows the window, the API-surface treatment versions what remains.

**Cross-cutting — phase completion gates.** Each phase ships with a verification CI workflow that asserts the phase's goal post-merge: after Phase 1a, divergent-name resolution works; after Phase 2, every addon loads under the new path or the legacy fallback; after Phase 4, every listing entry resolves to the same addon under the new format as under the old. A red gate means the phase isn't done; discovering this in CI is much cheaper than discovering it in user reports.

## Backwards Compatibility

### For addon authors

Existing addons keep working through Phase 4 without any change. The legacy `gramps_target_version` string match is preserved during the transition. Authors who do nothing get the same experience as today, less the per-release bump if they switch to range form.

Authors who want to opt in to the new model do so by adding `addon_api` alongside their existing `gramps_target_version`. When `addon_api` is present, it is the authoritative compatibility check; `gramps_target_version` can be removed in Phase 4.

### For the addons-source maintainer

Phase 1–3 changes are additive and do not require restructuring. Phase 4 is the disruptive one and requires the per-release ritual ([enumerated by Gary Griffin in \#2297](https://github.com/gramps-project/gramps/discussions/2297#discussioncomment-16864218)) to be retired:

- `create gramps61 branch from gramps60` — no longer needed; single branch.
- `bulk edit gpr for version change` — no longer needed; addons target the API range.
- `make.py gramps61 init all` — replaced by a per-API-version variant.
- `make.py gramps61 aggregate-pot` — replaced by `make.py aggregate-pot` against a single source tree. The Gramps version is selected via `$GRAMPSPATH` (pointing at the latest stable Gramps in the current series; see [translation paragraph in Phase 4](#Migration_plan) above for the detailed rationale). Eliminates Nick's "backporting changes to `po` files is not advisable" maintainer concern by removing the per-branch translation surface entirely.
- `make.py gramps61 build all` — replaced by `make.py build all`.
- `make.py gramps61 listing all` — replaced by `make.py listing all` producing the per-addon `metadata/<Addon>.json` files and the lightweight `index.json`.
- Cherry-picking PRs across maintenance branches — no longer needed.

### For end users

- Through Phase 3: invisible.
- Phase 4: the Addon Manager URL changes. Existing users on Phase 3 Gramps are pointed at the new URL by a redirect/alias in the listings repo.
- The local plugin directory layout under `~/.gramps/grampsXX/plugins/` does **not** change. Different Gramps versions remain isolated.

## Objections and responses

Two objections to the versioning approach were raised in review, pulling in opposite directions. Both concern the API-version axis.

### A separate API version may add too little value

The objection: a distinct API version gains little, because it would increment for every feature release anyway. This is partly correct — major and minor Gramps transitions do introduce API changes that addons must track, and any version scheme reflects that. But it does not hold at maintenance-release granularity, which is exactly where the current overhead lives: the empirical data in [Versioning scheme](#Versioning_scheme) shows zero effective breakages across the entire 6.0.x series, yet the current literal `gramps_target_version` forces a bump on every one of those releases. The proposal does not claim the API is stable across feature releases — it is not, and should not be — only that there is a demonstrated, recurring win at the maintenance level, which is the busywork the proposal removes.

### The dual-version scheme may be more complex than necessary

The opposing objection: maintaining both a Gramps release version and an `addon_api` version is more complex than necessary, and a single version compatible with the API aims would be simpler. Three considerations on why two numbers remain the better answer *within the current Gramps convention*:

- **Gramps does not commit to strict semver.** Nick Hall noted in [Discourse 9491 post 2](https://gramps.discourse.group/t/architectural-thoughts-on-the-addon-mechanism-api-versioning-lifecycle-states-manager-behaviour/9491/2) that "Gramps core doesn't use semantic versioning." The single-version alternative implicitly assumes Gramps's release version IS its API version — strict semver. Changing Gramps's release-versioning convention is explicitly a [non-goal](#Non-goals).
- **Gramps releases bump for reasons beyond API changes** — translation updates, security fixes, schema migrations, UI changes. If the API version IS the Gramps version, then either every release implies an API bump (over-versioning), or Gramps loses the ability to signal those other change categories via its release number.
- **The two numbers stay related in practice.** The empirical data shows API 1.0 is stable across all of Gramps 6.0.x. The cost is conceptual on first contact, not operational — most authors set `addon_api=">=1.0,<2.0"` once and never revisit it.

Even if Gramps eventually adopts strict semver as a project-level decision, `addon_api` would not become fully redundant. Gramps's release version tracks the whole project — the `.gramps` file format, the CLI surface, the DBAPI (a separate provider-side contract; see [Future Work](#Provider-side_API_contracts_(DBAPI))), and internal layout — in addition to the consumer-side addon API. An addon unaffected by a Gramps major bump driven by, say, a file-format migration is captured by a focused `addon_api` but not by a single unified version. The DBAPI remains its own versioning axis regardless.

## Impact assessment

The previous section covers *mechanical* transition compatibility — what does and doesn't change in the registration surface, the maintainer's workflow, the user's local directory. This section is about the more diffuse effects on user experience and addon quality, where the gains and costs are less clear-cut.

### User experience

The largest UX gains are invisible. A user who upgrades from Gramps 6.0.4 to 6.0.5 currently loses every installed addon that hasn't had its `gramps_target_version` string bumped by its maintainer. With `addon_api`, the addons stay working. The user never notices anything because nothing went wrong — which is precisely the goal. Similarly, the combined effect of PR \#2250 plus the `check_mod` fallback (Phase 1) turns today's \*"Plugin error (from 'editexifmetadata'): No module named 'PIL'"\* into an actionable \*"Pillow needs to be installed"\* with a working install hint; users who never saw the failure path notice no change, but users who hit it get a friendlier story.

The visible UX changes are a trade-off rather than a clear win. The two-axis status display adds expressiveness (the Addon Manager can finally distinguish "in development" from "abandoned") but also adds visual density. Banner copy will matter a great deal: "Unchecked" reads as a warning to a non-technical user even though the intended meaning is closer to "not yet verified for this Gramps version, may work fine." The `BROKEN` banner risks the opposite problem — making "known broken" too normalized as a label. Both are solvable with careful editorial work on the user-facing strings, but neither is solved by the metadata change alone.

The `ORPHANED` / `UNCHECKED` / `DEPRECATED` labels also expose ecosystem realities that are currently hidden; some users will read this transparency as the ecosystem dying rather than as the labeling improving. This is an honest trade-off rather than a clear win.

### Addon quality

The proposal's effect on addon quality is the strongest part of the case for it, but it depends on follow-through, not just landing the metadata.

Dependency declarations stop being optional in practice. The EditExifMetadata case (PRs [\#878](https://github.com/gramps-project/addons-source/pull/878) / [\#890](https://github.com/gramps-project/addons-source/pull/890)) shipped for years without declaring `requires_mod` because nothing enforced it. Once the auto-derivation step in addons-source CI (the Phase 1c sibling work) treats undeclared imports as a CI failure, this class of bug disappears at PR time rather than at user-install time. Similarly, the single-source-tree story (Phase 4) eliminates an entire class of cherry-pick drift: \#878 and \#890 had to be two PRs because the gramps60 and gramps61 code paths had already diverged in ways the fix had to account for.

A deprecation cycle — breaking changes marked `@deprecated` for one feature release before removal — is the part most likely to lift the quality floor across the ecosystem. Most third-party Django libraries ship updates for a new Django release before the release, because Django's deprecation policy gives them a six-month warning. Gramps doesn't have this dynamic today; an addon author finds out their addon broke when a user reports it. The proposal makes the deprecation cycle possible (Tier 2 in CI accepts a breaking change without a major bump only if the symbol was already deprecated), but the policy has to be adopted and followed — that's discipline, not metadata.

The quality risks are real and worth naming. Griffe sees Python's public API, not "what addons actually rely on." Without Tier 3 (addon test coverage), the version-bump signal will sometimes fire for changes nobody was using, producing busywork that looks like quality assurance but isn't. Mechanical CI can also crowd out human review — "griffe passed, we're fine" is easier to say than "I've thought about whether this affects the actual addons." Neither risk is dispositive, but both argue against treating Tier 2 as the whole story.

### The cross-cutting risk

The dominant risk for both UX and quality is uneven implementation. A half-landed version of this proposal would leave the ecosystem with new fields that addons partially populate, a transitional `gramps_target_version` + `addon_api` dual-declaration that gets out of sync, a lifecycle UI that some Addon Manager versions show and others don't, and the old per-version branch ritual still partially in place underneath. That is a worse state than the current one, which is at least internally consistent.

The independently-landable framing in the [Abstract](#Abstract) is the first line of defense against this: each phase delivers value alone, and rejecting or deferring a phase leaves a coherent intermediate state. The remainder of this section enumerates further mitigations.

## De-risking the implementation

### Sequencing for safe stall points

The migration plan is ordered so that any prefix of phases leaves the ecosystem strictly better than the status quo.

- **Stall after Phase 1**: Pillow/PIL works without addon changes; range-based `gramps_target_version` exists; PR \#2250 is in; the addon API surface is documented. No new behavior anywhere in the lifecycle UI. Net result: maintenance-release busywork is reduced, dependency declarations work correctly, nothing else changed.
- **Stall after Phase 2**: the `addon_api` contract exists. Addons that opt in get the maintenance-release stability win. Addons that don't keep working under the legacy path. No lifecycle changes.
- **Stall after Phase 3**: lifecycle states exist and are visible. `BROKEN` can be set on known-broken addons; CI knows the difference. Repository structure is still per-branch.
- **Stall after Phase 4**: single-source. The big disruptive change has landed. The API-versioning story is complete.

This is how to recover if the work runs out of bandwidth at any of those points.

### Mechanical CI as checklist, not verdict

Tier 2 (griffe in CI) detects API-shaped changes. It does not determine, by itself, whether a version bump is warranted. The intended flow is:

1.  Griffe reports breakages on a PR.
2.  Reviewer asks: were the affected symbols deprecated? If yes, the bump is automatic. If no, the change either needs a deprecation cycle first or a major-version bump and human-judgment confirmation that the break is intentional.
3.  The deprecation cycle is what gives griffe's output teeth: a "breaking change" that was already deprecated is paperwork, not a debate.

This keeps human review in the loop without making it perform the mechanical part of the check.

### Reducing addon-author friction

The ~140 addon authors should not have to do a coordinated migration. Specifically:

- `addon_api` is optional throughout. Addons that don't declare it use the legacy `gramps_target_version` path indefinitely. The Phase 4 retirement of the legacy field, once reached, can be preceded by a one-time bulk lint pass that proposes defaults for every addon, which authors accept or override.
- **Auto-derived `addon_api` range.** Griffe data plus an addon's import graph let CI propose the narrowest `addon_api` range that covers everything the addon actually uses against Gramps. The CI surfaces this as a suggestion on the PR; authors accept or override. Replaces the "I think this works" guess with a defensible number derived from what the addon actually imports.
- The auto-derivation step in addons-source CI (PR 820's machinery) can propose `requires_mod` declarations from import scans, surfacing them as a CI hint rather than a blocking failure during the transition. Authors fix or override at their own pace.
- **Auto-bump of addon `version=` on substantive change.** PRs that touch addon code can trigger a version bump using conventional-commits style or explicit commit-message tags (`BREAKING:`, `feat:`, `fix:`). The bump level follows the same MAJOR/MINOR/PATCH taxonomy used for the addon API surface, applied to the addon's own public surface. Eliminates the "forgot to bump version" mistake that currently surfaces in addons-source review.
- `maintenance_state` defaults to `PUBLISHED` for existing addons unless an explicit audit assigns otherwise. The default is the least surprising state; deviations require deliberate action.

### UI complexity management

The two-axis lifecycle introduces combinations users have never seen. Mitigations:

- **Default Addon Manager view hides non-default states.** Users see "available addons" by default. `UNCHECKED`, `ORPHANED`, `BROKEN` are filter-toggleable, not visible by default. Power users opt in; novice users see a clean list.
- **Banner copy is editorial.** The strings shown to users for each state are written and reviewed by humans, not auto-generated from enum names. `UNCHECKED` in the UI should read "Not yet verified for this Gramps version — may work fine; report issues if not."
- **Start with a smaller maintenance-state set.** If the five-state proposal feels too granular, an initial rollout with three (`PUBLISHED`, `ORPHANED`, `DEPRECATED`) covers most of the value. `INCUBATING` and `ARCHIVED` can be added later if the simpler set proves insufficient.

### Detecting field staleness

The new fields introduce a "label exists, isn't maintained" risk. Two mechanical countermeasures:

- **Listing-time staleness check.** When `make.py listing` runs, it flags addons whose `addon_api` range is no longer satisfied by any current Gramps release, addons whose declared `maintenance_state` contradicts their commit activity (e.g., `PUBLISHED` with no commits for 18 months), and addons whose declared dependencies cannot be resolved.
- **Time-based `ORPHANED` suggestion.** If commit activity drops below a threshold (no commits in 12 months, no maintainer response on issues), CI can *suggest* `ORPHANED` in the listing build. The addons-source maintainer reviews and applies — automatic flagging without automatic transitions.

These are recommendations rather than enforcement: the field is still the addon author's (or maintainer's) declaration. The CI surfaces a probable mismatch; a human decides what to do about it.

Staleness is genuinely hard to detect mechanically. Many addons couple lightly to the Gramps API — they import a stable subset and keep working across API changes that don't touch the parts they use. Conversely, an addon with no recent commits may be perfectly functional and unchanged because nothing needed changing. The staleness check above is therefore **heuristic, not authoritative**: it flags probable mismatches for human review, and never overrides what the addon's maintainer or the addons-source maintainer has declared. `ORPHANED`'s value is not in how often it gets applied; it is in being the right label available when the case warrants it. Even if `ORPHANED` is used rarely, having a clear way to express "this addon is no longer maintained" — distinct from "this addon is in early development" or "this addon is broken on the current Gramps" — improves the signal users see in the Addon Manager. A label that is occasionally correct is more useful than no label at all.

## Reference Implementation

No full prototype of the complete proposal exists yet; the migration plan is structured so the first shippable pieces are small and independent. Two parts have working reference code:

- **API-stability measurement (Tier 2 detection).** The griffe analysis cited in [Versioning scheme](#Versioning_scheme) is a runnable script: it checks out successive Gramps tags, runs [griffe](https://mkdocstrings.github.io/griffe/)'s breaking-change detection over the proposed API surface (`gramps.gen.plug._pluginreg`, `gramps.gen.lib`, `gramps.gen.db`, `gramps.gen.const`), and reports per-transition breakage counts. This is the mechanism behind both the empirical table and the proposed CI gate.
- **`check_mod` fallback (Phase 1a).** The ~10-line `importlib.metadata`-based resolution of distribution-name vs import-name divergence ([Part 4](#Backward-compatibility_fallback_for_plain-string_form)) is complete and self-contained; it resolves the Pillow/PIL case today and is backportable to `maintenance/gramps60` independently of the rest of this GEPS.

The remaining components — the `addon_api` registration field and compatibility check, the `maintenance_state` field and Addon Manager banners, the single-source repository model, and the listing generator — are specified here but not yet implemented. Each phase in the [migration plan](#Migration_plan) is scoped to land and be verified independently.

## Review discussion and open questions

This section consolidates the review history: what prior discussion agreed on, the points raised by reviewers in [Discussion \#2311](https://github.com/gramps-project/gramps/discussions/2311) and how the proposal addresses them, and the questions that remain genuinely open. It is kept separate from the proposal body so the body reads as a specification rather than a debate transcript.

### Consensus from prior discussion

The [Discourse thread](https://gramps.discourse.group/t/architectural-thoughts-on-the-addon-mechanism-api-versioning-lifecycle-states-manager-behaviour/9491) and [Discussion \#2297](https://github.com/gramps-project/gramps/discussions/2297) together established rough consensus on:

- Range-based `gramps_target_version` (Nick: "I am happy with changing the `gramps_target_version` to include ranges, and also allow a single addon to support multiple versions").
- Adding "Unchecked" and "Broken" to the `status` field (Nick: "Perhaps we could add 'Unchecked' and 'Broken'?").
- Maintenance state can occur at any quality level (Nick: "An addon could become unmaintained/orphaned at any stage in the lifecycle.") — implying quality and maintenance are orthogonal axes rather than positions on a single spectrum.
- `.gpr.py` files should remain pure key-value, with conditional logic moved into the implementation modules (Nick: "The `gpr` files should only contain the key value pairs and not conditional logic or any additional code").
- Single addon-source repository, no per-Gramps-version branches in the source tree (Doug, agreed by Gary on the maintainer-impact summary).
- Per-Gramps-version *listings* may still be needed because metadata can differ between versions (Nick: "I'm not sure about merging the listings. Metadata may change between versions").

### Points raised in review and how they are addressed

- **Does a separate API version add enough value, or will it just bump every feature release?** (Nick Hall, Discourse post 2.) Addressed in [Objections and responses](#A_separate_API_version_may_add_too_little_value), drawing on the empirical griffe analysis in [Versioning scheme](#Versioning_scheme) (0 effective API breakages across 6.0.0→6.0.8).
- **Is the dual-version scheme (Gramps release + `addon_api`) too complex; could one version do?** (Kulath, Discussion \#2311.) Addressed in [Objections and responses](#The_dual-version_scheme_may_be_more_complex_than_necessary). Carried forward as an open question below.
- **Staleness is hard to detect; `ORPHANED` may rarely apply.** (Kulath, Discussion \#2311.) Addressed in [Detecting field staleness](#Detecting_field_staleness): the check is explicitly heuristic, never overrides the maintainer's declaration, and the label's value is availability when warranted, not frequency of use.
- **Relationship to PR \#2308 (PyPI wheel installer).** (Doug Blank, Discussion \#2311.) Addressed in [Part 4](#Relationship_to_PR_#2308_(PyPI_wheel_installer)): \#2308 recharacterizes Phase 1a from a correctness fix to a state-reporting improvement; the two are complementary.
- **Top-level `po/` directory and which Gramps version to aggregate against.** (Nick Hall, Discussion \#2311.) Addressed in [Phase 4 translation](#Migration_plan): the two-level structure is retained, with a merge-back build step making addon catalogs self-contained; the residual intrinsic dependency is handled by treating `gramps.pot` msgids as part of the API surface.
- **Addon-supersedes-built-in via versioning.** (emyoulation, Discussion \#2311.) Addressed in [Versioning scheme](#Versioning_scheme) (the `!=` exclusion example) and [Future Work](#Addon-supersedes-built-in_mechanism): the capability already exists (Plugin lib GENERAL); the proposal's version-comparison building blocks are consumable by it without modification.
- **"Addon" vs "plugin" terminology / audience categorization.** (Doug Blank, Nick Hall, kulath, emyoulation, Discussion \#2311.) Addressed in [Terminology and scope](#Terminology_and_scope).
- **Two-step change vs. bundling JSON migration.** (emyoulation, Discussion \#2311.) Addressed in [Future Work](#JSON_registration_files): sequencing keeps the contributor-facing learning cost lower; the pure-key-value framing makes the later conversion tool-driven.
- **Developer tooling (creation GUI, make.py wrapper, reload_plugins test loop).** (emyoulation, Discussion \#2311.) Addressed in [Future Work](#Developer_tooling_around_registration): downstream consumers of the spec, enabled by it but out of scope, with natural homes identified.

**Open items prior discussion did not resolve** (addressed in the proposal body): how the `requires_mod` tuple form (#2250) coexists with addons targeting pre-#2250 Gramps under a single source ([Part 4](#Backward-compatibility_fallback_for_plain-string_form)); whether `requires_gi` needs parallel treatment ([Part 4](#requires_gi)); per-Gramps-version listings reconciliation under a single source tree ([Part 3](#Listing_semantics)).

### Open questions

1.  **Whether the dual-version scheme (Gramps release version + `addon_api`) is worth the complexity it introduces (Kulath's concern in Discussion \#2311).** The proposal's defense (see [Objections and responses](#The_dual-version_scheme_may_be_more_complex_than_necessary)) is that the alternative — coupling addon API stability to Gramps's release version — over-versions when Gramps changes for reasons that do not affect addons (file format, internal layout, DBAPI), and would still leave the DBAPI as its own provider-side versioning axis. Reducing to one version is not free; the GEPS argues for the dual-version cost as the better tradeoff.
2.  **Default maintenance_state for legacy addons during Phase 3 rollout.** Treat all addons as `PUBLISHED` unless explicitly flagged otherwise? Or run a one-time audit and assign maintenance state based on last-commit-age at the rollout date? Audit is more accurate but requires reviewer time.
3.  **`BROKEN` visibility.** Nick suggested treating `BROKEN` like `UNSTABLE` (dev mode only). For an addon that *was* in user listings and is *now* broken, hiding it entirely may be worse than showing it with a banner. Recommendation: `BROKEN` stays loadable for users who already have it installed, but is hidden from new-install discovery.
4.  **Per-addon-version entry deduplication.** Within an addon's `metadata/<Addon>.json`, if two versions only differ by additive metadata (e.g., a wider `addon_api` range), do we emit one entry with the wider range or two entries? Emitting two is simpler client-side; emitting one is denser but couples the listing generator to range-merging logic. Recommendation: emit one entry per published addon-version, even if neighbouring versions would merge cleanly. Disk and bandwidth are cheap; client logic stays simple.
5.  **Translation surface for new metadata.** Status and maintenance-state labels need translating. Are they keyed off the enum value (current pattern for `status`) or independently?
6.  **Multi-installed Gramps interactions.** If a user has Gramps 6.1 and 6.2 on one machine, and an addon is installed under `~/.gramps/gramps61/plugins/`, the Phase 4 Addon Manager in 6.2 should detect this and offer to copy. Mechanism is straightforward; the UX is the question. Recommendation: surface as part of the cross-version persistence prompt described under UI changes.
7.  **Cross-major-version backport workflow.** When an addon at v2.0.0 needs a fix that also applies to v1.5.0 (because there are still users on a Gramps that implements the older API), what is the supported workflow? Three options enumerated in [Proposed structure](#Proposed_structure): ephemeral `git checkout` + rebuild, long-lived `support/1.x` branch in `addons-source`, or declare v1.5.0 EOL. Recommendation: default to EOL, with rebuild-from-history available for security fixes, and reserve long-lived support branches for the very few addons that genuinely commit to parallel support (precedent: Django LTS).

## Future Work

The following are not part of this GEPS but are forward-looking items that either this work enables, or that reviewers raised as related improvements. They are collected here so the dependency on this proposal — and the natural next step for each — is explicit. None gates the four core parts; all are separately proposable.

### Addon state migration (Part 5)

When an addon changes incompatibly across its **own** major version bump (DB schema, on-disk config format, persistent cache format), Gramps currently has no metadata channel to coordinate migration of user state. addons-source PR [\#781](https://github.com/gramps-project/addons-source/pull/781) (PostgreSQLEnhanced) is the documented case where this surfaces in practice; that PR's discussion has the details.

A future GEPS or design proposal could define declarative fields on `register()` (e.g. `migrates_from`, `migration_hook`) so that the Addon Manager can detect a version transition and invoke a hook the addon author owns. This is orthogonal to API versioning: Parts 1–4 work without it, and the design space is large enough (user-data safety, dry-run, rollback, idempotency) to warrant its own proposal rather than a tail end of this one. It re-uses the same registration metadata channel this GEPS establishes, which is why it is the most natural follow-on. **Next step:** its own design proposal once a willing implementer and pilot addon (PostgreSQLEnhanced) align.

### JSON registration files

Nick Hall has noted a move from Python `.gpr.py` registration files to JSON as a possible future direction. This is a change to the plugin *mechanism* (how registration is encoded and loaded), not to the addon supply chain, which is why it sits outside this GEPS's scope. The two are independent because the field *contract* — which fields exist and what they mean — is identical regardless of encoding. This GEPS is deliberately built to be encoding-agnostic: keeping the fields pure key-value (per Nick's stated direction) is exactly what makes a future Python→JSON conversion mechanical rather than semantic. **Next step:** a separate discussion or proposal on the registration format; if it concludes in time, the conversion could be co-delivered with [Phase 4](#Phase_4:_Repository_consolidation), but the field work here neither blocks nor depends on it. Sequencing the two rather than bundling them keeps the contributor-facing learning cost lower (the conversion can be tool-driven for the pure-key-value files this GEPS produces).

### Provider-side API contracts (DBAPI)

Database backend addons (e.g. PostgreSQLEnhanced, SharedPostgreSQL) *implement* the DBAPI contract rather than *consume* the general addon API. The mechanics differ in ways that matter for versioning: total rather than partial conformance is required, the contract is coupled to persisted-data schema (a v1 backend cannot open a v2 tree), and exactly one backend runs per tree. A change to the DBAPI base class breaks every backend, not "some" — Doug Blank's pending DBAPI change adding `json_extract_expression()` as a required method (on the `dsb/db-config-and-parallel` feature branch as of May 2026) is the live example; PR [\#781](https://github.com/gramps-project/addons-source/pull/781) tracks it against an unmerged Gramps commit precisely because no `addon_api`-style channel exists for it. Folding DBAPI under the consumer-side `addon_api` axis would mix two different versioning concerns and over-bump every consumer addon for changes that affect only backends. **Next step:** a separate provider-side mechanism — a `provides_dbapi=` declaration or equivalent, paired with schema versioning. This GEPS's versioning approach is a usable template for it.

### Developer tooling around registration

Raised by emyoulation in [Discussion \#2311](https://github.com/gramps-project/gramps/discussions/2311): a GUI for authoring a valid `.gpr.py`/JSON registration file, a graphical wrapper over `make.py` that produces a tarball and listing JSON for a registered addon, and using [kkujansuu's "Reload Plugins" addon](https://github.com/kkujansuu/gramps/tree/master/addons/reload_plugins) as the foundation of a registration-compiler test loop. These are *downstream consumers* of the registration spec rather than part of defining it — and the GEPS's pure-key-value framing is what makes a creation tool tractable (generating valid key-value declarations is mechanizable in a way generating arbitrary Python is not). **Next steps:** a separate developer-utility addon or an Addon Manager feature proposal (the creation tool); a discussion against `addons-source` with a `from make import …` library refactor so CLI and GUI share one source of truth (the `make.py` wrapper); coordination with the addon's author (the Reload Plugins test loop).

### Addon-supersedes-built-in mechanism

The capability for an addon to supersede a built-in plugin already exists in the Gramps plugin architecture — the [Plugin lib (GENERAL)](https://www.gramps-project.org/wiki/index.php/Addon_list_legend) addon type is documented as one that "can add, replace and or modifies builtin Gramps options," and [Plugin Manager Enhanced](https://gramps-project.org/wiki/index.php/Addon:Plugin_Manager) is itself an example, replacing the original Plugin Manager and providing extended UI (Built-in / Available / Installed / Update Available status). This GEPS does not redefine that mechanism; rather, the building blocks it provides — PEP 440 version comparison on the addon's own `version` field, `addon_api` ranges including `!=` exclusions, and the lifecycle states — are directly consumable by the existing mechanism without modification. Raised by emyoulation in [Discussion \#2311](https://github.com/gramps-project/gramps/discussions/2311) (the Gramps-6.0.5-corruption scenario): an emergency addon can patch-bump and exclude the broken release via `!=`, and the loader's existing version comparison prefers it. **Next step:** none required for the mechanism itself; if the supersession UX warrants enhancement, that is an Addon Manager / Plugin Manager Enhanced concern, not a registration-metadata one.

### Addon Manager enhancements

Two user-facing improvements raised in [Discussion \#2297](https://github.com/gramps-project/gramps/discussions/2297), orthogonal to versioning and lifecycle but natural companions in the same UI surface: **thumbnail support** in the Addon Manager, and a **ratings / feedback system** for addons. Both are independent of this GEPS's metadata and could be proposed on their own; they are noted here so the Addon Manager's evolution is considered as a whole rather than piecemeal.

### Repository ACLs and contributor onboarding

If the maintenance-axis surfacing works as intended and causes a rise in adopter offers for orphaned addons (which is part of the goal), the maintainer-onboarding process — repository access, review delegation, contributor ramp-up — may need work to absorb them. This is a process/governance change rather than a technical one, and is out of scope here, but it is a foreseeable second-order consequence of the lifecycle work succeeding. **Next step:** a governance discussion if and when adopter volume materializes.

## References

- [Discourse thread 9491: Architectural thoughts on the addon mechanism](https://gramps.discourse.group/t/architectural-thoughts-on-the-addon-mechanism-api-versioning-lifecycle-states-manager-behaviour/9491)
- [Discussion \#2297: Refactor addons to use semantic versioning](https://github.com/gramps-project/gramps/discussions/2297)
- [PR \#2250: Allow requires_mod entries to specify pip package name and version](https://github.com/gramps-project/gramps/pull/2250)
- [PR \#2308: Python PyPI wheel installer for addon module dependencies](https://github.com/gramps-project/gramps/pull/2308) — complementary to \#2250 (see [Part 4](#Relationship_to_PR_#2308_(PyPI_wheel_installer)))
- [addons-source PR \#878](https://github.com/gramps-project/addons-source/pull/878): Pillow/PIL declaration on gramps60
- [addons-source PR \#890](https://github.com/gramps-project/addons-source/pull/890): Pillow/PIL declaration on gramps61
- [addons-source PR \#829](https://github.com/gramps-project/addons-source/pull/829): GExiv2 version handling in EditExifMetadata
- [addons-source PR \#744](https://github.com/gramps-project/addons-source/pull/744): `gramps-gedcom7` name-and-version pin issue
- [addons-source PR \#781](https://github.com/gramps-project/addons-source/pull/781): PostgreSQLEnhanced state-migration case (see [Part 5](#Addon_state_migration_(Part_5)))
- [GEPS 014: Plugin registration and management](wiki:GEPS_014:_Plugin_registration_and_management) — historical context for the existing registration mechanism
- [MediaWiki extension status](https://www.mediawiki.org/wiki/Extension_status) — inspiration for the current `status` field
- [PEP 440](https://packaging.python.org/en/latest/specifications/version-specifiers/) — version specifier syntax
- [Semantic Versioning 2.0.0](https://semver.org/)

## See Also

- [GEPS 014: Plugin registration and management](wiki:GEPS_014:_Plugin_registration_and_management) — the existing registration mechanism this proposal extends
- [GEPS 048: Format Negotiation Layer for Import-Export Plugins](wiki:GEPS_048:_Format_Negotiation_Layer_for_Import-Export_Plugins) — a parallel addon-mechanism proposal; shares the "wrap, don't modify core" and "addon-first, integrate later" patterns
- [Plugin Manager Enhanced](https://gramps-project.org/wiki/index.php/Addon:Plugin_Manager) — implements the addon-supersedes-built-in and hide mechanisms referenced here
- [Addons MAINTAINERS](wiki:Addons_MAINTAINERS) — the maintainer registry the lifecycle metadata integrates with

## Credits

This proposal was developed with AI assistance, in accordance with the Gramps project policy on AI-generated contributions.

- **Human author and coordinator**: Eduard Ralph (eduralph). Originated the proposal, directed its scope and structure, supplied the domain knowledge and the addons-source lint-campaign data, and is responsible for its content.
- **AI assistance**: Claude (Anthropic). Drafting and structural editing, the griffe-based API-stability analysis, conversion between MediaWiki / Markdown / docx formats, and reconciliation of the review discussion.

[Category:GEPS](wiki:Category:GEPS) [Category:Developers/General](wiki:Category:Developers/General) [Category:GEPS](wiki:Category:GEPS) [Category:Developers/General](wiki:Category:Developers/General)
