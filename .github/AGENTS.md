# Purpose

- Own the manual GitHub Actions and Pages execution workflow.

# Ownership

- `workflows/cotizaciones.yml` prepares, publishes, verifies and persists quotes. Root Python modules own data logic.

# Local Contracts

- Only `workflow_dispatch`; no cron, push or automatic FCI-upload trigger.
- Run from the default branch, serialize every run, never cancel an in-progress publication automatically.
- Use the ephemeral GITHUB_TOKEN; no pCloud credentials or user-generated token is needed.
- Deploy only the explicit staged site. Store history on `feed-history` only after public verification; never force-push it.
- Stage a previous-site artifact for attempted rollback. A failed/uncertain deployment or history commit must stay red even after recovery. Initial publication has no previous site to restore.
- A GitHub-hosted run and Pages propagation must be tested live before claiming end-to-end success.

# Work Guidance

- Main UI name is `Actualizar cotizaciones`; default mode is `Actualizar`. `Inicializar` is for first publication and `Validar` does not deploy.
- Preserve whole-workflow concurrency and the ordering prepare, deploy, verify, commit.
- Use reviewed stable action versions declaring Node.js 24; inspect nested actions in composite wrappers too. Do not suppress runtime deprecation by allowing an insecure Node version. The Python quote runtime remains 3.12.

# Verification

- Root offline tests cover staging, manual uploads, persistence and URL verification. Validate YAML and action inputs against official actions documentation.

# Child DOX Index

- None. The single workflow is owned here.
