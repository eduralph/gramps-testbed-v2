export const meta = {
  name: 'build-core-dev-section',
  description: 'Author the "05 - Gramps development" core manual section as an analog of "06 - Addon development"',
  phases: [
    { title: 'Author', detail: 'one agent per page, writes the .md file directly' },
    { title: 'Review', detail: 'global consistency check across the finished section' },
    { title: 'Fix', detail: 'apply the consistency fixes per page' },
  ],
}

const VAULT = '/home/eddie/workspace/gramps-testbed-v2/wiki/pages'
const SECTION = `${VAULT}/05 - Gramps development`
const SRC = `${VAULT}/04 - Technical Documentation`
const ADDON = `${VAULT}/06 - Addon development`
const GRAMPS = '/home/eddie/workspace/gramps'
const INTEGRATION = '/home/eddie/workspace/gramps-testbed-v2/docs/INTEGRATION.md'
const GUIDELINES = `${SECTION}/16-guidelines.md`

const HOUSE_STYLE = `
HOUSE STYLE — follow exactly, this section must match "06 - Addon development":
- YAML frontmatter:
    ---
    title: "Gramps 6.1 Wiki Manual - Core Development - <Section>"
    categories: [Developers, Gramps 6.1]
    managed: true
    ---
- First content line after frontmatter: <!--wiki:{{man index|6.1}}-->
- Last line of the file: <!--wiki:{{stub}}-->
- Open with "## Overview". Close with "## See also".
- Use H2 (##) for sections, H3 (###) for sub-sections. Use tables and fenced code
  blocks with language tags (python, bash) liberally, like the addon pages.
- Internal links within this section: [[NN-name]] (e.g. [[06-data-access]]).
- Cross-links to the addon section: [Addon X](../06%20-%20Addon%20development/NN-name.md).
- Upstream wiki links: [label](wiki:Page_Name). External: full https URLs.
- Cite authoritative origins INLINE the way the addon pages and 16-guidelines.md do:
  a PR number, a maintainer ruling, or path:line on maintenance/gramps61. Do NOT
  invent citations — only cite a path:line / symbol you actually verified in the
  gramps checkout, or a PR already cited in 16-guidelines.md / INTEGRATION.md.
- Audience: a Gramps CORE contributor working on gramps-project/gramps (NOT addons).
- Where the addon analog page says something correct and core-applicable, mirror the
  wording for consistency; where core differs, state the delta. Remember the one-way
  fallback from 16-guidelines.md: core never inherits FROM addon, so do not import
  addon-specific rules (tests/ plural, gramps60 branch, make.py) into core pages.

KEY CORE FACTS (verified this session — reuse, don't re-derive):
- Repository: gramps-project/gramps. Production branch: maintenance/gramps61
  (v6.1.0), forward-merged to master; master is feature-only.
- Tests: stdlib unittest only; test files are <module>_test.py (SUFFIX) inside a
  test/ package (SINGULAR) beside the module. Run: GRAMPS_RESOURCES=. python3 -m
  unittest discover -p "*_test.py". mypy IS enforced (mypy.ini: files = ./gramps,
  ./test; *.gpr.py excluded). Black enforced in CI.
- gen self-containment: gramps.gen.* imports no other gramps submodule.
- i18n: wrap user strings with _(); ngettext for plurals; _(string, context)
  preferred over pgettext; maintain po/POTFILES.in and po/POTFILES.skip by hand;
  check via PYTHONPATH=../../gramps python po/test/po_test.py.
- Commit: subject <=70 chars, body wrapped at 80, Mantis trailer on the LAST line
  (Fixes #NNNN), full hashes when referencing commits.
- The normative rules live in [[16-guidelines]] — reference it, don't restate it
  wholesale; these pages are how-to/explanatory, 16-guidelines is the MUST/SHOULD ref.

VERIFICATION: you have read-only shell. Confirm any path:line, symbol, or module
existence against the gramps checkout at ${GRAMPS} on branch maintenance/gramps61
before citing it (grep, ls, git -C ${GRAMPS} log -1 -- <path>). A green grep is the
bar for citing a path; don't cite from memory.

OUTPUT: write the finished Markdown to the given file path with the Write tool. Your
returned value is metadata only (see schema), NOT the page body.
`

const PAGE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['file', 'title', 'sections', 'crosslinks', 'citations', 'openTODOs'],
  properties: {
    file: { type: 'string' },
    title: { type: 'string' },
    sections: { type: 'array', items: { type: 'string' } },
    crosslinks: { type: 'array', items: { type: 'string' }, description: '[[NN-name]] targets this page links to' },
    citations: { type: 'array', items: { type: 'string' }, description: 'path:line / PR / ruling cited, each verified' },
    openTODOs: { type: 'array', items: { type: 'string' } },
  },
}

// Each page: filename, title, brief (what to cover), sources (abs paths), analog addon page.
const PAGES = [
  {
    file: '01-overview.md', title: 'Overview',
    analog: `${ADDON}/01-overview.md`,
    sources: [`${SRC}/portal-developers.md`, `${SRC}/getting-started-with-gramps-development.md`, `${SRC}/programming-guidelines.md`, `${SRC}/team.md`, `${SRC}/contact.md`, `${SRC}/project-license.md`],
    brief: `What Gramps core is: a GTK3/PyGObject + Python 3.10+ genealogy application. The architecture at a glance (gen = headless model/db, gui = GTK layer, plugins = bundled plugins, cli). The codebase layout (point at ${GRAMPS}/gramps/*). The object model in one paragraph (primary objects: Person, Family, Event, Place, Source, Citation, Repository, Media, Note + handles). GPL-2.0-or-later license. Where the community is (mailing lists, Matrix/IRC, bug tracker) and who maintains it (team), as a short "community" section + See also. Keep it a concise orientation page like the addon 01-overview, with an "Anatomy of the codebase" table. Point onward to [[02-get-started]], [[04-architecture]], [[16-guidelines]].`,
  },
  {
    file: '02-get-started.md', title: 'Getting started',
    analog: `${ADDON}/02-get-started.md`,
    sources: [`${SRC}/getting-started-with-gramps-development.md`, `${SRC}/getting-started-with-gramps-master.md`, `${SRC}/brief-introduction-to-git.md`],
    brief: `First-time core contributor: from "I want to fix a Gramps bug" to "my change runs and its test passes". Cover: prerequisites (Python 3.10+, GTK3/PyGObject, build deps); cloning your fork + adding the upstream remote; branching from upstream/maintenance/gramps61 (NOT the fork's tracking copy) — cite INTEGRATION §2 / 16-guidelines; running Gramps from source (python Gramps.py); running parallel versions/branches safely with backups (from getting-started-…-master — emphasise the data-backup precaution before running master); the edit→run→test loop; a minimal Git workflow (feature branch, commit, push, draft PR) summarised here with the full git reference linked. Include the test command (GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"). Defer rules to [[16-guidelines]], deep debugging to [[09-debug]].`,
  },
  {
    file: '03-tutorials.md', title: 'Tutorials',
    analog: `${ADDON}/03-tutorials.md`,
    sources: [`${SRC}/report-writing-tutorial.md`, `${SRC}/quick-views.md`, `${SRC}/report-generation.md`, `${SRC}/report-api.md`],
    brief: `End-to-end walkthroughs for a core contributor. Tutorial 1: fix a bug end-to-end — reproduce against example.gramps, write a failing <module>_test.py in the right test/ dir, make the fix, watch it go green, prepare the PR (Root cause / Fix / Verified against / Test). Tutorial 2: write a report — condense report-writing-tutorial (options class, the docgen TextDoc/DrawDoc interface, register via .gpr.py, write_report()). Tutorial 3: a Quick View (runfunc signature, category, context-menu access). Keep each tutorial a numbered, runnable sequence. Link [[06-data-access]], [[07-api-reference]], [[08-testing]], [[16-guidelines]].`,
  },
  {
    file: '04-architecture.md', title: 'Architecture & subsystems',
    analog: `${ADDON}/04-addon-kinds.md`,
    sources: [`${SRC}/getting-started-with-gramps-development.md`, `${SRC}/using-database-api.md`, `${SRC}/signals-and-callbacks.md`],
    brief: `The core analog of "addon kinds": a map of the codebase subsystems a contributor works in. Cover, as a table + per-subsystem H3s: gramps/gen (headless model, db, lib objects, plug registry, utils, config, const) — and the MUST that gen imports no other submodule; gramps/gui (GTK3 views, editors, widgets); gramps/plugins (the plugins SHIPPED with core — report/tool/view/gramplet/importer/exporter, contrast with third-party addons); gramps/cli; gramps/plug (the plugin framework that core provides and addons consume). Explain the layering/dependency direction (gui depends on gen, gen depends on nothing gramps). Note the data flow: DbState/DbTxn → signals → views. Verify the actual subdirectories exist with ls ${GRAMPS}/gramps. Optionally embed ![[_media/API.svg|The Gramps database API surface]]. Link [[05-fundamentals]], [[06-data-access]], [[07-api-reference]].`,
  },
  {
    file: '05-fundamentals.md', title: 'Fundamentals',
    analog: `${ADDON}/05-fundamentals.md`,
    sources: [`${SRC}/signals-and-callbacks.md`, `${SRC}/programming-guidelines.md`, `${SRC}/using-database-api.md`],
    brief: `Cross-cutting concerns every core contributor hits. Sections: the plugin system from core's side (how register()/_pluginreg builds the catalog, plugin kinds); signals & callbacks (the Callback base class, connect/disconnect/emit, CallbackManager in gramps.gen.utils.callman, the db-change signals, deferred-until-commit ordering) — this is the strong source (signals-and-callbacks.md); the config manager (gramps.gen.config); logging (module-level LOG = logging.getLogger(__name__), no print()); _() setup in core modules; transactions (DbTxn) as the write discipline. Mirror the depth of the addon 05-fundamentals. Verify Callback/CallbackManager locations in ${GRAMPS}/gramps/gen. Link [[06-data-access]], [[07-api-reference]], [[09-debug]], [[16-guidelines]].`,
  },
  {
    file: '06-data-access.md', title: 'Data access',
    analog: `${ADDON}/06-data-access.md`,
    sources: [`${SRC}/using-database-api.md`],
    brief: `The Database API for core devs — the deepest data page. Cover: DbReadBase / DbWriteBase abstract interfaces; the concrete DBAPI/SQLite backend (and the legacy bsddb note); primary objects vs secondary objects; handles (stable, internal) vs gramps_id (user-facing, mutable); get_*_from_handle / get_*_from_gramps_id; iterating (iter_people, get_person_handles); find_backlink_handles returning (class_name:str, handle) tuples — string compare, not class identity; the DbTxn write pattern with worked add/commit/remove examples; cursors for bulk reads. Use handle/ID types from gramps.gen.types. Verify method names against ${GRAMPS}/gramps/gen/db (grep DbReadBase/DbWriteBase) and object classes in ${GRAMPS}/gramps/gen/lib. Link [[07-api-reference]], [[05-fundamentals]], [[08-testing]], [[16-guidelines]].`,
  },
  {
    file: '07-api-reference.md', title: 'API reference',
    analog: `${ADDON}/07-api-reference.md`,
    sources: [`${SRC}/using-database-api.md`, `${SRC}/report-api.md`, `${SRC}/signals-and-callbacks.md`],
    brief: `A curated map of the API surface a core contributor uses, organised by module. For core (unlike addons) gramps.gui.* and gramps.plugins.* are in scope, but note gen stays self-contained. Tables per area: gramps.gen.lib (the object classes), gramps.gen.db (DbReadBase/DbWriteBase/DbTxn/DbState), gramps.gen.plug (plugin registry + report base), gramps.gen.utils (callman, etc.), gramps.gen.config/const/errors/types, gramps.gui.* (editors, views, widgets, dialog), the report docgen API (TextDoc/DrawDoc/GVDoc from report-api). Note stability: gen is the stable contract; gui/plugins move between minors. Verify module existence with ls/grep against ${GRAMPS}/gramps/gen and gramps/gen/__init__.py on maintenance/gramps61. Link [[06-data-access]], [[05-fundamentals]], [[14-compatibility]].`,
  },
  {
    file: '08-testing.md', title: 'Testing',
    analog: `${ADDON}/08-testing.md`,
    sources: [`${GRAMPS}/AGENTS.md`, `${SRC}/programming-guidelines.md`, INTEGRATION],
    brief: `How core is tested. THE central distinctions vs addons: stdlib unittest only; test files <module>_test.py (SUFFIX) in a test/ package (SINGULAR) beside the module — and MUST NOT use tests/ (plural) anywhere under gramps/ (that's the addon convention; cite 16-guidelines + INTEGRATION §3). Running: GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py". mypy is enforced (mypy.ini files = ./gramps, ./test; gpr.py excluded) — show the mypy invocation. example.gramps as the canonical fixture (example/gramps/example.gramps) for DB-traversal tests; the red-before/green-after regression-test rule. Class-header nav comment applies to TestCase subclasses too. Verify the test/ dir count and a sample <x>_test.py with ls/find against ${GRAMPS}. Mirror the addon 08-testing depth. Link [[09-debug]], [[11-code-analysis]], [[06-data-access]], [[16-guidelines]].`,
  },
  {
    file: '09-debug.md', title: 'Debugging',
    analog: `${ADDON}/09-debug.md`,
    sources: [`${SRC}/debugging-gramps.md`],
    brief: `Debugging Gramps core. Cover: hard crashes (running from a terminal to see the traceback); adding debug statements vs the logging infrastructure (LOG levels, --debug / GRAMPS_DEBUG, the Help→Log window); the warn/error filter; Python debugging with pdb / breakpoint(); winpdb for GUI debugging (you may embed ![[_media/Winpdb.png|Winpdb debugging a running Gramps]]); profiling (cProfile); gdb for the C/GTK layer. Strong single source (debugging-gramps.md). Mirror addon 09-debug shape but core-scoped. Link [[10-troubleshoot]], [[08-testing]], [[05-fundamentals]].`,
  },
  {
    file: '10-troubleshoot.md', title: 'Triage & troubleshooting',
    analog: `${ADDON}/10-troubleshoot.md`,
    sources: [`${SRC}/bug-triage.md`, `${SRC}/using-the-bug-tracker.md`, `${SRC}/debugging-gramps.md`],
    brief: `Two halves. (a) Triage & the bug tracker from a dev's view: the MantisBT status workflow (new/acknowledged/confirmed/assigned/feedback/resolved), how to reproduce against example.gramps first ("couldn't reproduce" is the top reason a fix stalls), filing a good report, what the status states mean — you may embed ![[_media/Mantisbt-valid-status-states.png|MantisBT status transitions]]. (b) Common core-dev failure modes table: symptom → cause → fix (e.g. plugin not appearing, gen importing gui breaking headless, mypy/black CI failures, GRAMPS_RESOURCES unset in tests). Link [[09-debug]], [[08-testing]], [[16-guidelines]].`,
  },
  {
    file: '11-code-analysis.md', title: 'Code analysis',
    analog: `${ADDON}/11-code-analysis.md`,
    sources: [`${GRAMPS}/AGENTS.md`, `${SRC}/programming-guidelines.md`, `${SRC}/ui-style.md`],
    brief: `The static-analysis / quality gate for core. Cover: Black (the changed-files invocation from AGENTS.md), mypy (mypy.ini config, the gen self-containment that mypy + discipline protect), pylint (aim >=9, never at the cost of clarity/Black), PEP8 deltas where Black wins, import grouping (the three comment-headed sections), class-header nav comments, cb_ callbacks, the po/test/po_test.py check for POTFILES, and UI-style review concerns (GNOME HIG, from ui-style.md) as a review dimension. Distinguish what CI enforces vs what is reviewer judgment. Verify mypy.ini contents and that AGENTS.md sections exist. Link [[08-testing]], [[12-internationalization]], [[16-guidelines]].`,
  },
  {
    file: '12-internationalization.md', title: 'Internationalization',
    analog: `${ADDON}/12-internationalization.md`,
    sources: [`${SRC}/translating-gramps.md`, `${GRAMPS}/AGENTS.md`],
    brief: `i18n for core. Cover: wrap user-visible strings with _(); the no-f-string/.format()-inside-_() rule (xgettext can't extract); ngettext for plurals; _(string, context) preferred over pgettext; N_() for deferred translation; the GRAMPS_LOCALE / glocale setup; gettext .po/.pot format basics for contributors (header, msgid/msgstr, fuzzy) from translating-gramps.md; and the CORE-SPECIFIC duty: maintain po/POTFILES.in (translatable) and po/POTFILES.skip (excluded) by hand when adding/removing .py files, checked via PYTHONPATH=../../gramps python po/test/po_test.py. Contrast: addons regenerate template.pot via make.py (one-way note, don't import the addon rule). Verify po/POTFILES.in and po/test/po_test.py exist in ${GRAMPS}. Link [[11-code-analysis]], [[16-guidelines]].`,
  },
  {
    file: '13-packaging.md', title: 'Building & releasing',
    analog: `${ADDON}/13-packaging.md`,
    sources: [`${SRC}/what-to-do-for-a-release.md`, `${SRC}/getting-started-with-gramps-master.md`],
    brief: `The core analog of addon packaging: building and releasing Gramps itself. Cover: the build/install from source (point at ${GRAMPS}/INSTALL, pyproject.toml, the data/ and po/ trees), how a release is cut (the maintainer checklist from what-to-do-for-a-release.md: feature freeze → string freeze → translation update → tag → build → announce), version/branch handling (maintenance/gramps61 vs master), and the platform builds (AIO/Windows UCRT64, mac) at a high level. Frame the release process as maintainer-run; a contributor's role is landing fixes on the right branch in time for the freeze. Verify pyproject.toml / INSTALL / po exist. Link [[14-compatibility]], [[02-get-started]], [[16-guidelines]].`,
  },
  {
    file: '14-compatibility.md', title: 'Compatibility',
    analog: `${ADDON}/14-compatibility.md`,
    sources: [`${SRC}/getting-started-with-gramps-master.md`, `${GRAMPS}/NEWS`],
    brief: `Cross-version concerns for core devs. Cover: the supported Python (3.10+) and GTK3/PyGObject baselines; the maintenance/gramps61 vs master split and why fixes ride maintenance and forward-merge (cite 16-guidelines/INTEGRATION §2); deprecation policy and how API changes propagate to addons (link the addon compatibility page); cross-branch cherry-pick correctness ("applies cleanly" != "remains correct" — verify against the target branch's related code); the Windows toolchain (UCRT64 for 6.1+). Keep it focused and link onward to [[15-whats-new]] (retrospective) and [[17-roadmap]] (prospective). Pull a few concrete 6.0→6.1 deltas from ${GRAMPS}/NEWS if clearly present; otherwise point at NEWS rather than invent. Link [[15-whats-new]], [[17-roadmap]], [[07-api-reference]].`,
  },
  {
    file: '15-whats-new.md', title: "What's new",
    analog: `${ADDON}/15-whats-new.md`,
    sources: [`${GRAMPS}/NEWS`, `${GRAMPS}/RELEASE_NOTES`],
    brief: `Retrospective: per-Gramps-version changes that affect core developers (API/behaviour deltas), the counterpart to [[17-roadmap]]. This page is mostly a structured pointer: explain how to read it (each entry = version, change, impact on dev/API, source), then seed it from ${GRAMPS}/NEWS / RELEASE_NOTES with a few real 6.1 developer-facing entries IF clearly identifiable; where you can't verify specifics, leave a clearly-marked outline with HTML-comment TODOs pointing at NEWS (mirror how the addon 15-whats-new / 17-roadmap leave TODO scaffolding rather than inventing). Do NOT fabricate version specifics. Link [[14-compatibility]], [[17-roadmap]].`,
  },
  {
    file: '17-roadmap.md', title: 'Roadmap',
    analog: `${ADDON}/17-roadmap.md`,
    sources: [`${SRC}/portal-enhancement-proposals.md`, `${SRC}/portal-developers.md`],
    brief: `Prospective counterpart to [[15-whats-new]]: in-flight work, accepted-not-yet-implemented, deprecations/removals, open design questions, deferred/rejected — for CORE. Explain GEPs (Gramps Enhancement Proposals) as the design-proposal mechanism (from portal-enhancement-proposals.md) and where they live. Follow the addon 17-roadmap's structure closely (Status/Target/Impact/Tracking table; sections with "_none recorded yet_" + HTML-comment TODOs where there's nothing verifiable). Include the documentation-roadmap section noting this section's own draft state. Do NOT invent roadmap items — scaffold with TODOs like the addon page does. Link [[15-whats-new]], [[16-guidelines]], [[14-compatibility]].`,
  },
]

phase('Author')
log(`Authoring ${PAGES.length} core-development pages...`)

const authored = await parallel(PAGES.map((p) => () =>
  agent(
    `Author the Gramps CORE wiki page "${p.title}" and WRITE it to:\n  ${SECTION}/${p.file}\n\n` +
    `WHAT TO COVER:\n${p.brief}\n\n` +
    `READ THESE SOURCES FIRST (raw upstream material + authoritative refs):\n` +
    p.sources.map((s) => `  - ${s}`).join('\n') + '\n' +
    `  - ANALOG PAGE to match voice/format/length: ${p.analog}\n` +
    `  - Normative rules to defer to (do not restate wholesale): ${GUIDELINES}\n` +
    `  - Authoritative coding standard: ${GRAMPS}/AGENTS.md ; contributor pointers: ${GRAMPS}/CONTRIBUTING\n` +
    `  - Project integration facts (branch targets, test placement): ${INTEGRATION}\n\n` +
    HOUSE_STYLE,
    { label: `author:${p.file}`, phase: 'Author', schema: PAGE_SCHEMA }
  )
)).then((r) => r.filter(Boolean))

log(`Authored ${authored.length}/${PAGES.length} pages. Writing sidebar...`)

// Sidebar authored last, seeded with the final list.
const sidebar = await agent(
  `Write the vault-internal navigation sidebar for the Gramps Core Development section to:\n` +
  `  ${SECTION}/00-sidebar.md\n\n` +
  `Match the structure and tone of the addon sidebar EXACTLY: ${ADDON}/00-sidebar.md (read it first).\n` +
  `Frontmatter: title "Core Development — Sidebar", managed: false (vault-internal, NOT published).\n` +
  `Include the same kind of HTML-comment rationale block (author-journey ordering), a "## Sidebar"\n` +
  `numbered list linking every page [[01-overview]] … [[17-roadmap]] with a one-line gloss each\n` +
  `(use the real core titles/topics below), and a "## Status" note. Link 16 as [[05 - Gramps development/16-guidelines]].\n` +
  `Do NOT add the {{stub}} wiki shim (the addon sidebar has none — it's vault-only).\n\n` +
  `The pages and their topics:\n` +
  PAGES.map((p) => `  ${p.file.replace('.md','')} — ${p.title}`).join('\n') +
  `\n  16-guidelines — Rules (normative MUST/SHOULD/MAY; the page to cite in review)`,
  { label: 'author:00-sidebar.md', phase: 'Author', schema: PAGE_SCHEMA }
)

phase('Review')
log('Running global consistency review across the section...')

const REVIEW_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['issuesByFile', 'sectionLevelIssues'],
  properties: {
    sectionLevelIssues: { type: 'array', items: { type: 'string' } },
    issuesByFile: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['file', 'issues'],
        properties: {
          file: { type: 'string' },
          issues: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  },
}

const review = await agent(
  `Consistency review of the finished section folder: ${SECTION}\n\n` +
  `Read EVERY .md file in that folder (00-sidebar through 17-roadmap, including the pre-existing 16-guidelines.md).\n` +
  `Also list the folder so you know which files exist (ls "${SECTION}"). Then check and report issues:\n` +
  `1. Frontmatter uniform: title "Gramps 6.1 Wiki Manual - Core Development - <Section>", categories [Developers, Gramps 6.1], managed: true (EXCEPT 00-sidebar which is managed: false).\n` +
  `2. Each published page starts with <!--wiki:{{man index|6.1}}--> and ends with <!--wiki:{{stub}}-->.\n` +
  `3. Every internal [[NN-name]] link resolves to a file that EXISTS in the folder. Flag any dangling target.\n` +
  `4. Every ../06%20-%20Addon%20development/NN-name.md cross-link points to a real file in ${ADDON} (ls it).\n` +
  `5. No addon-only rule leaked into a core page: NO "tests/" (plural) prescribed for core, NO "maintenance/gramps60" as the core branch, NO make.py/template.pot as a core duty. (Mentioning them as an addon CONTRAST is fine.)\n` +
  `6. Each page opens with ## Overview and closes with ## See also.\n` +
  `7. Embedded images reference only files that exist in ${SECTION}/_media (ls it): API.svg, Winpdb.png, Mantisbt-valid-status-states.png.\n` +
  `8. Sidebar (00-sidebar.md) lists every page 01–17.\n` +
  `Report concrete, actionable issues per file (exact link text / line context) plus section-level issues. If a file is clean, omit it. Do not rewrite anything — report only.`,
  { label: 'review:section', phase: 'Review', schema: REVIEW_SCHEMA }
)

const filesToFix = (review.issuesByFile || []).filter((f) => (f.issues || []).length > 0)
log(`Review found issues in ${filesToFix.length} file(s); ${ (review.sectionLevelIssues||[]).length } section-level note(s).`)

phase('Fix')
let fixed = []
if (filesToFix.length) {
  fixed = (await parallel(filesToFix.map((f) => () =>
    agent(
      `Apply these consistency fixes to the file ${SECTION}/${f.file} and nothing else.\n` +
      `Read the file, make the minimal edits to resolve each issue, keep house style intact, re-save.\n` +
      `Issues:\n${f.issues.map((i) => `  - ${i}`).join('\n')}\n\n` +
      `Section-level context that may be relevant:\n${(review.sectionLevelIssues||[]).map((i)=>`  - ${i}`).join('\n')}\n\n` +
      `Authoritative refs if needed: ${GUIDELINES} ; ${GRAMPS}/AGENTS.md ; ${INTEGRATION}. ` +
      `Return a one-line summary of what you changed.`,
      { label: `fix:${f.file}`, phase: 'Fix' }
    )
  ))).filter(Boolean)
}

return {
  authoredPages: authored.map((a) => a.file),
  sidebar: sidebar?.file,
  reviewSectionIssues: review.sectionLevelIssues || [],
  filesFixed: filesToFix.map((f) => f.file),
  fixSummaries: fixed,
  allTODOs: authored.flatMap((a) => (a.openTODOs || []).map((t) => `${a.file}: ${t}`)),
}
