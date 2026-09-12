# Purpose

- Store fund quote feeds consumed by Portfolio Performance.

# Ownership

- Generated `BCACCA.json`, `BCAHA.json`, and `BCMMA.json` belong here. Root owns their Balanz TXT sources and `fondos_txt_a_json.py`.

# Local Contracts

- Each JSON is a list of `{ "date": "YYYY-MM-DD", "close": number }` objects. Source values are taken from `historico[].valorcuotaparte` without the bond scaling factor.
- Output names match source TXT stems. The converter preserves input order, skips invalid entries, and overwrites an output only when it has quotes to write.

# Work Guidance

- Preserve root source TXT files. Regenerate these feeds only for a requested fund update; adding a bond does not require it.
- Leave `FCI.hash` to its existing owner.
- Balanz TXT acquisition and conversion remain manual on the PC; do not scrape Balanz or build a mobile converter. For GitHub publication, the user uploads the generated quote JSON to `entradas-fci/`; do not overwrite seeds here as a routine cloud update.

# Verification

- For a requested conversion, compare generated dates and values with the corresponding source `historico` entries and confirm JSON validity.

# Child DOX Index

- None.
