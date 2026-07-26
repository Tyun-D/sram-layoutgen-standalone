# M6R Failure Reason Report

## Root Cause

- M6 compared and shipped the wrong artifact class for visual review.
- The fixed reference is `hybrid_openyield_rail_overlap.complete.gds`, but M6's main review artifact was `layoutgen_optimized_reproduced_sram.gds`.
- `layoutgen_optimized_reproduced_sram.gds` has the same macro bbox and many of the same hierarchy statistics as the reference, but it has fewer geometry shapes because it is the primary `.gds`, not the `complete.gds` visual-routing export.
- M6 therefore reported success from the regenerated backend metrics while the user was visually inspecting a different export artifact.

## Evidence

- M6 previous vs reference mismatches: `file_size_bytes, top_cell, boundary_count, bbox, layer_datatype_summary, per_layer_shape_count, cell_hierarchy`
- Reproduced true-entry output vs reference mismatches: `none`
- The true reference-locked rerun uses `generate_layout_prototype(..., mode='hybrid_openyield_prototype', enable_openyield_gate_row_packing=True, enable_openyield_rail_to_rail_abutment=True, enable_openyield_power_rail_overlap_packing=True, exclude_dff_vertical_overlap=True)` and then inspects the resulting `complete.gds` artifact.
