# Brief — issue 13707 / webconnect-depends-on-libwebconnect

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** webconnect-depends-on-libwebconnect
- **Defect:** The Web Connect Pack addons (DE/FR/NL/RU/UA/UK/US) require libwebconnect but
  their .gpr.py did not declare it, so the AddonManager installed a pack without pulling in
  libwebconnect and the pack failed to load (note 3: "we need the line
  `depends_on=["libwebconnect"]`").
- **Success criterion:** Every Web Connect Pack .gpr.py declares
  `depends_on=["libwebconnect"]` so installing a pack also installs its dependency. Already
  satisfied on the target branch — the brief confirms the declaration is present in all
  packs; there is no patch.diff to carry, so the bundle is discontinued as superseded by
  the change that added it, with the PR referenced.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
- **Surfaces:** data (addon registration metadata; no GUI logic).
- **Scope:** confirm the `depends_on=["libwebconnect"]` line is present in each WebConnect
  pack .gpr.py and close. / out of scope: the broader requires_mod import→pip table work
  (tracked separately); any change to libwebconnect itself.
- **Repro instruction:** On Gramps 6.0 with libwebconnect not installed, install a Web
  Connect Pack (e.g. DE) via the Addon Manager; pre-fix the install left the pack unable to
  load. With `depends_on=["libwebconnect"]` declared, the dependency installs too.
- **Test file:** none — metadata-only addon registration; verified by reading the .gpr.py
  files (no production code path to red→green).
- **Citations expected:** n/a (no new patch). Declaration present at, e.g.,
  DEWebConnectPack/DEWebPack.gpr.py:18 `depends_on=["libwebconnect"]` — identically in
  FR/NL/RU/UA/UK/US pack .gpr.py files.
- **Prior-art check (triage cycles):** searched by file path `*WebConnectPack/*.gpr.py` on
  maintenance/gramps60 — `depends_on=["libwebconnect"]` is present in all seven packs;
  introduced via commit 7c3002157 ("Add help_urls", PR 640). No outstanding change needed.
- **Mantis:** 13707
- **Disposition hint:** likely-close

## STOP discipline

Draft only until Check sign-off. No patch.diff to carry — the declaration is already in
place. **Recommended sign-off disposition: `discontinue`** (`pdca signoff --discontinue`),
superseded by addons-source PR 640 (which added `depends_on=["libwebconnect"]`) — per
INTEGRATION §7. No new PR.
