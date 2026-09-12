# Purpose

- Accept manually generated FCI quote JSON through GitHub file upload.

# Ownership

- Only `BCACCA.json`, `BCAHA.json`, `BCMMA.json` are data inputs. Root owns conversion and validation code.

# Local Contracts

- Only arrays of ISO date and numeric close; never TXT source exports, account data or credentials.
- Do not fetch or scrape Balanz. The user generates TXT and converts it on their PC with the existing converter.
- No browser/mobile converter is requested.
- A changed upload merges by date; supplied dates replace those dates only, preserving older history. Repeating the same canonical upload is idempotent.
- Absence/removal of an upload leaves the confirmed history intact. An empty or malformed recognized upload is rejected for that fund: retain its confirmed history and applied hash, warn, and allow other valid series to publish. Corrected uploads are retried. Unexpected files or unsafe directory structure still abort staging.
- Uploads remain available on the source branch. Their hashes are recorded with the confirmed history so older unchanged inputs cannot overwrite later results.

# Work Guidance

- Keep exact uppercase filenames. Upload JSON here, then run `Actualizar cotizaciones` manually.
- Do not edit `feed-history` or the FCI seed files to perform a routine upload.

# Verification

- `python -B -m unittest -v test_github_feed` exercises missing, partial, repeated and malformed manual uploads.

# Child DOX Index

- None.
