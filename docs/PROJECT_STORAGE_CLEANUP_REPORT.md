# Project Storage Cleanup Report

## Checkpoint

- checkpoint_dir: `/data1/qujh/project_checkpoints/industrial_gap_cleanup_20260730_032115`
- checkpoint_commit: `68e7340daaecbcc48a23cce6757e8247efedfbc1`
- latest package SHA verification:
  - `PROJECT_INDUSTRIAL_GAP_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz`
    `0ca315a99a3c05deb3c96629dfb5fbfc652cab672e03330a268d41b56058d6e3`
  - `PROJECT_INDUSTRIAL_GAP_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz`
    `4df1067aa6d888203aac0f404bc7d93a090b5970c00a587d4d0fe1d129246ad8`

## Local Ignore And Dry Run

- project worktree local exclude updated
- main repository local exclude updated
- `git clean -ndX` dry-run result:
  - `scripts/__pycache__/`
  - `simulation/logic/__pycache__/`
  - `simulation/spice/logs/`
  - `sram_layoutgen/__pycache__/`
  - `sram_layoutgen/openyield_adapter/__pycache__/`
  - `sram_layoutgen/verification/__pycache__/`
- `git clean -nd` dry-run result: no additional untracked paths scheduled

## Explicit Cleanup Performed

- removed `__pycache__` directories
- removed `simulation/spice/logs/*.log`
- did not run destructive `git clean -fdx`
- did not delete any package permanently

## Quarantine

- quarantine_dir: `/data1/qujh/delete_quarantine_20260730`
- moved replaced old package set:
  - `PROJECT_LONG_RANGE_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz`
  - `PROJECT_LONG_RANGE_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz.sha256`
  - `PROJECT_LONG_RANGE_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz`
  - `PROJECT_LONG_RANGE_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz.sha256`
- quarantine_size: `44K`
- quarantine_manifest: `/data1/qujh/delete_quarantine_20260730/QUARANTINE_SHA256SUMS.txt`

## Activity Change

- active changes before checkpoint/cleanup: `64`
- active changes immediately after checkpoint commit and explicit cleanup: `0`

## Retention Policy

- retained formal package list is recorded in `docs/PROJECT_STORAGE_RETENTION_MANIFEST.csv`
- old `PROJECT_LONG_RANGE_*` packages were isolated instead of removed because they are replaced by the new industrial-gap package set but still worth preserving during the next review cycle
