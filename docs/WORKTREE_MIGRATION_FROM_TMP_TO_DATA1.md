# Worktree Migration From Tmp To Data1

- current_worktree: `/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726`
- recommended_target: `/data1/qujh/worktrees/project_mainline_inventory_20260726`
- generated_at: `2026-08-03T16:46:54Z`

## Goal
Move the active Git worktree from `/tmp` to `/data1/qujh/worktrees` so project state survives temporary filesystem cleanup.

## Preconditions
- Confirm no active layout generation, DRC, LVS, archive, or editor processes still use the current worktree.
- Confirm enough free disk space under `/data1/qujh`.
- Confirm `git worktree list` shows the current worktree as healthy before migration.
- Confirm package artifacts have already been copied to `/data1/qujh/decoder_multiline_review`.

## Recommended Command
```bash
git worktree move \
  /tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726 \
  /data1/qujh/worktrees/project_mainline_inventory_20260726
```

## Validation Steps
1. Run `git worktree list` and confirm the new `/data1/qujh/worktrees/project_mainline_inventory_20260726` path is registered.
2. Run `git -C /data1/qujh/worktrees/project_mainline_inventory_20260726 status --short`.
3. Re-open the three review GDS paths and confirm SHA-stable outputs still match the archived package manifest.
4. Update any automation or documentation that still points at the `/tmp/.../project_mainline_inventory_20260726` path.

## This Round
This document is a migration plan only. The worktree itself has not been moved in this round.
