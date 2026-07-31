# Decoder Hierarchical Resume Guide

1. Re-run `scripts/project_decoder_hierarchical_floorplan_search.py` from the same worktree.
2. The script rebuilds the expected L0 pair set deterministically from `docs/DECODER_GATE_ORIENTATION_LEGALITY.csv` and the aggregate matrix gaps.
3. It never replays completed L0 work because this round consumes the already-finished aggregate matrix and raw pair artifacts as authoritative inputs.
4. Child and stage candidate IDs are deterministic and stable across reruns.
5. Progress is append-only in `docs/DECODER_HIERARCHICAL_SEARCH_PROGRESS.jsonl` and summarized in `docs/DECODER_HIERARCHICAL_SEARCH_PROGRESS.json`.
