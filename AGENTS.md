# DOX framework

- DOX is highly performant AGENTS.md hierarchy installed here
- Agent must follow DOX instructions across any edits

## Core Contract

- AGENTS.md files are binding work contracts for their subtrees
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable AGENTS.md plus every parent AGENTS.md above it

## Read Before Editing

1. Read the root AGENTS.md
2. Identify every file or folder you expect to touch
3. Walk from the repository root to each target path
4. Read every AGENTS.md found along each route
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there
6. Use the nearest AGENTS.md as the local contract and parent docs for repo-wide rules
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken DOX

Do not rely on memory. Re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the DOX pass still must happen.

## Hierarchy

- Root AGENTS.md is the DOX rail: project-wide instructions, global preferences, durable workflow rules, and the top-level Child DOX Index
- Child AGENTS.md files own domain-specific instructions and their own Child DOX Index
- Each parent explains what its direct children cover and what stays owned by the parent
- The closer a doc is to the work, the more specific and practical it must be

## Child Doc Shape

- Create a child AGENTS.md when a folder becomes a durable boundary with its own purpose, rules, responsibilities, workflow, materials, or quality standards
- Work Guidance must reflect the current standards of the project or user instructions; if there are no specific standards or instructions yet, leave it empty
- Verification must reflect an existing check; if no verification framework exists yet, leave it empty and update it when one exists

Default section order:
- Purpose
- Ownership
- Local Contracts
- Work Guidance
- Verification
- Child DOX Index

## Style

- Keep docs concise, current, and operational
- Document stable contracts, not diary entries
- Put broad rules in parent docs and concrete details in child docs
- Prefer direct bullets with explicit names
- Do not duplicate rules across many files unless each scope needs a local version
- Delete stale notes instead of explaining history
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist

## Closeout

1. Re-check changed paths against the DOX chain
2. Update nearest owning docs and any affected parents or children
3. Refresh every affected Child DOX Index
4. Remove stale or contradictory text
5. Run existing verification when relevant
6. Report any docs intentionally left unchanged and why

## User Preferences

- Use GitHub Actions for manual initiation from Android and GitHub Pages for static quote hosting, with the PC off. No schedules or external activation during local preparation; explain publication contents and destination before publishing.
- The user explicitly authorized the public repository `PaoloNB56/cotizaciones-pp`. It is installed with Pages source `GitHub Actions`; public quotes use `https://paolonb56.github.io/cotizaciones-pp/`. Verify session and run state before remote changes.
- pCloud and Termux are no longer selected. Retain previous local files without using them in the GitHub workflow or installation package.
- FCI source TXT are generated manually from Balanz. Never scrape or automate requests to Balanz. Convert on the PC with the existing converter and manually upload only quote JSON. No mobile/browser converter is wanted.
- Include S30N6 with all available QuickTrade history and the existing close / 1000 conversion. Preserve source files and historical series; do not refresh unrelated outputs for narrow changes.
- Credentials, portfolio files, transactions and original TXT stay outside the public repository and publication. Use the automatic ephemeral GITHUB_TOKEN; no manual token or developer registration is required by this workflow.

## Project Purpose and Ownership

- Root owns the original Python downloader, FCI converter, BAT, root quote JSON, Balanz TXT and independent Inflación.xlsx. The BAT still targets D:\scriptspython\pp_feed, not this copy; do not use it for validation here.
- update_bonos.py owns QuickTrade/Dolarazo source configuration, shared conversion and the retained HTTP server. The server only serves root files on port 8000/all interfaces; the GitHub flow never starts it.
- fondos_txt_a_json.py converts root Balanz TXT to FCI JSON. It does not download fund data. Its legacy pandas-independent conversion retains its original behavior.
- cloud_feed.py owns portable source retrieval, strict validation and the 17-file SEEDS list. Its pCloud client/CLI are retained legacy functionality, not the chosen runner. It imports shared functions without starting the legacy main or loading pandas.
- github_feed.py owns GitHub history persistence, manual FCI merging, Pages staging and public URL verification. README.md and LEEME-NUBE.md describe the current GitHub workflow.
- test_cloud_feed.py and test_github_feed.py own offline validation, failure/recovery, persistence and manual-input tests. requirements-cloud.in pins the portable dependencies; pandas is only needed by the original DataFrame path.
- package_github.py builds an explicit-list installation package for a new public repository. It never publishes remotely and excludes raw TXT, XLSX, portfolios, credentials, runtime data, pCloud/Termux setup and old ZIPs.
- pcloud_local.py, actualizar-termux.sh, package_android.py and pp-feed-android.zip are unselected legacy alternatives. github-actions.example.yml only points readers to the current workflow. Do not activate legacy paths automatically.
- Existing .git is not an operational repository. Do not modify .git, .agents, .codex or .hash metadata as part of feed changes.

## Local Contracts and Work Guidance

- INSTRUMENTOS_QT maps output names to verified QuickTrade numeric IDs and dd/MM/yyyy start dates. Requests use especieVencimiento="24 hs.". AN29/AO28 select AN29D/AO28D but keep their PP output names.
- S30N6 uses ID 37006 and 01/01/2000 as an all-history lower bound, not an asserted listing date. QuickTrade conversion divides by 1000 and rounds to six decimals; do not extend this factor to FCI or another asset class.
- Quote JSON contains date-sorted objects with exactly ISO date and numeric close. Reject empty, malformed, nonfinite, nonpositive, duplicated or future data. Preserve all original local JSON/TXT/XLSX during portable runs.
- Portable QuickTrade verifies HTTPS, ticker, row validity and known historical date coverage. Dolarazo uses venta, skips weekends and refreshes a seven-day overlap including same-day corrections, while preserving older history. The original local Dolarazo path remains incremental after its last date.
- SEEDS is the explicit publication allowlist of 17 series, including inactive bonds and FCI. FCI paths are flattened only in the published destination. No recursive source-directory publication.
- github_feed.py reads the complete committed snapshot on the dedicated feed-history branch. Missing history requires explicit initialization; corrupt/incomplete history aborts. Pin reads to one commit and verify the saved manifest hashes. Never silently rebuild from stale checkout seeds.
- New FCI uploads in entradas-fci merge by date; supplied dates replace only those dates. Store canonical upload hashes with confirmed history so repeating an old unchanged upload is idempotent. Missing input never removes prior quotes.
- Stage the entire batch before deployment. The Pages artifact contains exactly 17 quote JSON, publication.json and a reserved synthetic _pp_feed_probe.json. No code, source TXT, state file or credentials are deployed.
- Verify every fixed public URL without cache-busting parameters. The generation manifest and synthetic probe change per run, allowing overwrite/cache checks even with unchanged prices. Passing a local/mock test is not live Pages evidence.
- Persist history only after public verification, using parent-linked commits and a non-forced ref update. Attempt whole-site rollback from the previous confirmed artifact if deployment, verification or persistence fails. Keep failed runs red; a first publication has no previous site to restore.
- Deployment and Git history commit are not one atomic transaction. Do not guarantee recovery after cancellation, timeout or network loss; uncertain ref writes are checked before reporting failure. Use one publishing workflow and preserve whole-run concurrency serialization.
- Keep ordinary runs manual. Uploading FCI JSON must not trigger a workflow automatically. Do not auto-delete source uploads, historical commits or execution artifacts.
- Keep dependency manifests as .in, not .txt, to avoid the Balanz converter trying to parse them.
- The old pCloud runner still uses same-name upload/nopartial, authenticated history recovery and restoration attempts. Its credentials remain private; never invoke it during GitHub work.

## Verification

- Parse changed Python with ast.parse without starting the legacy main.
- Run python -B -m unittest -v -b test_cloud_feed test_github_feed for relevant portable changes. Validate YAML/action inputs against official GitHub documentation.
- For a full local provider/staging check use python -B -u github_feed.py stage --local --work .cloud-work/<new-run-name>. This downloads and stages without publishing, touching original feeds or starting HTTP. Existing work directories must be rejected.
- Narrow instrument additions use only the relevant existing download/conversion functions; verify ticker/ID, nonempty ordered unique dates, finite closes and JSON round-trip. Do not run the BAT/main downloader for validation.
- Compare original data with baseline.sha256.json when present. Build the GitHub bundle with python -B package_github.py and check its explicit entries, hashes and ZIP integrity.
- GitHub Linux validation, initial Pages publication and a normal update passed on 2026-09-11 (Actions runs 34663922757, 34663988467 and 34664059981). Both public manifests and all 17 series matched saved history; unchanged URLs served a new generation and probe, dates were preserved and the second history commit retained its parent. Actual rollback and PP desktop/mobile consumption remain untested.

## Child DOX Index

- FCI/AGENTS.md: original generated fund feeds and source relationships. Root owns their converter and cloud merge.
- entradas-fci/AGENTS.md: manual JSON input through GitHub; no Balanz requests.
- .github/AGENTS.md: manual workflow, Pages deployment, verification, persistence and rollback sequencing.
- .cloud-work/AGENTS.md: staged candidates, reports and recovery artifacts; never a publication source directory as a whole.
- .work/AGENTS.md: older research scripts and external dependency junctions; not routine feed processing.
- Other root files and metadata remain root-owned. Single workflows do not require further child levels.
