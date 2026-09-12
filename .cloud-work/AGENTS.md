# Purpose

- Store private portable-run artifacts without modifying original feeds.

# Ownership

- Root `cloud_feed.py` owns timestamped run directories, candidate JSON, validation/result reports, optional recovery reports and previous remote snapshots.
- Root `github_feed.py` owns Pages staging: `site/`, `previous-site/`, `next-history/`, `run.json` and `verified.json`. Each specified work directory must be new.
- `run.lock` is the local OS locking file. A run directory is one artifact bundle, not a separate workflow boundary.

# Local Contracts

- Never upload this directory as a public folder or include it in the Android installation ZIP.
- Deploy only the explicitly validated `site/` content; `previous-site/` is exclusively a rollback artifact. Never deploy `next-history/` or the entire run directory. Documentation may be included in an explicit installation package.
- Quote backups and reports contain no access tokens, private config or portfolio data.
- Only `published_verified` reports establish complete publication and persistence; staged data and `validated_not_published` do not. This status does not guarantee every series refreshed: inspect `run.json` warnings and publication report outcomes (`refreshed`, `retained`, `retained_after_error`), last dates and error reasons.
- Preserve `previous/` and `recovery.json` for investigation of incomplete publication. No automatic cleanup or deletion is part of routine runs.
- Each run uses a new UTC timestamp and suffix. Earlier reports must not be interpreted as the current run's status.

# Work Guidance

- Read `result.json`, then `recovery.json` if present; `validation.json` describes candidates, not necessarily the final remote state.
- Remote restoration may fail or be interrupted; check pCloud revisions when local recovery did not finish.
- For Pages, `verified.json` means public checks passed; only `run.json` status `published_verified` also confirms the history commit. The Actions run remains the authority for deployment failures and restoration attempts. Inspect Pages deployment history and `feed-history` after an uncertain interruption.

# Verification

- Root offline tests exercise recovery artifacts with temporary directories. Live `local-check` validates staged data without publishing it.

# Child DOX Index

- None. All run directories share this contract.
