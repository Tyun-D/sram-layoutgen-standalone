# Step 4.5 standalone.py Diff Review

## Scope

This review compares the current working-tree `sram_layoutgen/standalone.py` against the pre-Step-4.5 safety snapshot:

- `docs/git_safety_snapshots/pre_step45_standalone.patch`
- current `sram_layoutgen/standalone.py`

The goal is to identify the Step 4.5-only changes and decide whether they can be safely partial-staged without including older historical modifications already present in `standalone.py`.

## Findings

| Item | Result | Notes |
| --- | --- | --- |
| `StandaloneSpec.enable_openyield_array_aggregation` added in Step 4.5 | Yes | A new dataclass field `enable_openyield_array_aggregation: bool = False` was added. Default remains closed. |
| Restricted OpenYield aggregation calls added | Yes | `standalone.py` now imports `ALLOWED_AGGREGATION_MACROS`, `EXCLUDED_PERIPHERAL_MACROS`, `build_standalone_storage_array_aggregation`, and `load_ready_storage_macro_specs` from `sram_layoutgen.openyield_adapter.array_aggregation`. |
| Storage-only placement replacement | Yes | The new path wraps only `bitcell_array`, `dummy_left_array`, `dummy_right_array`, and `replica_bitline_array`. It calls `build_standalone_storage_array_aggregation(...)`, validates allowed macros, and creates R0/no-mirror `CellArray` entries through the existing `add_hard_array(...)` helper. |
| Peripheral placement changed by Step 4.5 | No direct peripheral placement changes found | The Step 4.5 branch does not instantiate or aggregate `sense_amp`, `write_driver`, `dff`, `tri_gate`, `gen_col_mux`, `gen_wl_driver`, `gen_nand2`, `gen_nand4`, or `gen_precharge`. Existing peripheral placement remains on the old path. |
| Routing changed by Step 4.5 | No routing code changes found | The Step 4.5 code does not add or edit route construction logic. When the switch is enabled, existing coordinate calculations will naturally see the storage pitch from the OpenYield audit; this is placement-driven and guarded by `enable_openyield_array_aggregation`. |
| GDS writer changed by Step 4.5 | No | `sram_layoutgen/gds_writer.py` is not modified. The integration reuses existing `CellArray` expansion behavior. |
| Integration report metadata added | Yes | `db.metadata["openyield_array_aggregation_integration"]` records enabled state, allowed/excluded macros, macro counts, storage bboxes, pitch/origin, `peripherals_old_path`, `changed_gds_flow`, `routing_changed`, `shared_rail_merge`, `generated_gds`, and the storage plan. |
| Mirroring audit exception added | Yes | `_audit_cell_array_mirroring(...)` now treats explicitly enabled OpenYield storage aggregation as an R0-only exception for the four storage arrays. |

## Step 4.5 standalone.py Change Areas

1. Import block:
   - Adds OpenYield storage aggregation imports.
   - This hunk is mixed with older historical imports, including architecture/correctness/occupancy changes that predate Step 4.5.

2. `StandaloneSpec`:
   - Adds `enable_openyield_array_aggregation: bool = False`.
   - This hunk is small and separable in concept.

3. Storage pitch selection:
   - Adds `openyield_gds_pin_audit_path`.
   - Loads audited `cell_1rw`, `dummy_cell_1rw`, and `replica_cell_1rw` dimensions only when the flag is enabled.
   - Keeps legacy pitch when the flag is disabled.
   - This hunk is adjacent to historical placement helper changes and is not cleanly isolated in the full file diff.

4. Storage array placement:
   - Replaces only the four storage array creation calls behind the flag.
   - Default disabled path keeps the original `add_hard_array(... mirror_x=True)` behavior.
   - Enabled path creates R0/no-mirror arrays from `build_standalone_storage_array_aggregation(...)`.
   - Adds metadata report fields.
   - This is the largest Step 4.5-specific section, but it appears inside a large historical hunk when diffed from `HEAD`.

5. Cell-array mirroring audit:
   - Adds an OpenYield storage R0 exception.
   - This hunk is comparatively isolated, but still depends on metadata introduced by the larger storage placement hunk.

## Partial Staging Risk

`sram_layoutgen/standalone.py` had a large historical working-tree diff before Step 4.5. The current `git diff -- sram_layoutgen/standalone.py` shows Step 4.5 lines mixed with earlier changes in the same hunks:

- The import hunk includes both old OpenYield Step 4.5 imports and earlier architecture/correctness/occupancy imports.
- The storage pitch hunk is next to earlier local GDS text-pin helper and placement logic changes.
- The storage array placement hunk contains the actual Step 4.5 integration, but the surrounding file diff is already offset by large historical edits.
- The mirroring audit hunk is cleaner, but cannot be committed alone because it depends on the new metadata and switch.

Because the index is based on `HEAD`, a normal `git add -p sram_layoutgen/standalone.py` would require manually editing hunks that are interleaved with older work. That is possible in theory, but not safe enough to automate in this dirty worktree.

## Recommendation

Do not commit `sram_layoutgen/standalone.py` from the current dirty worktree.

Recommended path:

1. Keep the current non-risk Step 4.5 files staged.
2. Leave `sram_layoutgen/standalone.py` unstaged.
3. Create a clean worktree or clean branch from the current baseline commit.
4. Re-apply only the Step 4.5 standalone changes as a small patch:
   - OpenYield storage aggregation imports.
   - `StandaloneSpec.enable_openyield_array_aggregation`.
   - guarded OpenYield storage pitch selection.
   - guarded storage-only array replacement and metadata.
   - mirroring audit R0 exception.
5. Commit that clean patch together with the already staged adapter/report/smoke files.

Conclusion: use a clean-worktree cherry-pick/manual patch for `standalone.py`; do not use `git add -p` in the current dirty worktree unless a human manually edits and verifies each hunk.
