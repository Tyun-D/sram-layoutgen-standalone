# GitHub Workflow

## Preferred Path

- Keep code, tests, JSON, CSV, and Markdown in normal Git.
- Use a private GitHub branch/PR flow only if remote push works.
- Push only:
- integration collaboration-preparation commit on `feature/step45-clean-array-aggregation`
- Team-B preparation branch `collab/team-b-control-support`

## Explicit Non-Goals For COLLAB-P0

- Do not create module PRs.
- Do not merge module PRs.
- Do not migrate historical large files into Git LFS.

## Fallback

- If GitHub push fails, deliver a `bundle`, `patch`, SHA256 sidecar, and evidence tar under `collaboration/artifacts/`.
