# M7C Golden Reference Confirmation Report

- status_file_read: `True`
- status_file_updated: `True`
- golden_reference_user_confirmed: `True`
- golden_reference_is_now_locked: `True`
- current_golden_reference_path: `outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`
- current_golden_reference_clean_review_path: `outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds`
- hybrid_openyield_rail_overlap_is_golden: `False`
- new_uploaded_reference_is_golden: `True`
- m7_blockers_before_count: `2`
- m7_blockers_after_count: `0`
- next_stage_allowed: `M8_REPRODUCE_UPLOADED_GOLDEN_REFERENCE`
- can_enter_M8_after_this_gate: `True`
- human_klayout_review_required_for_M8_output: `True`
- can_enter_next_stage_without_human_review: `False`

## Cleared M7 Blockers

- Human KLayout review of uploaded golden reference is required.
- Next repair stage must reproduce the new uploaded golden reference instead of historical hybrid reference.

## Review GDS Manifest

- source_gds: `outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds`
- copied_review_gds: `outputs/M7C_golden_reference_confirmed/current_supported_config/golden_reference_clean_review.gds`
- size_bytes: `381784`
- sha256: `2367c4a39373704ce43425cad48b918e61a46c4d89e9173a6829d3200f10b0c7`

## Gate Decision

M7C clears the two M7 blockers and allows `M8_REPRODUCE_UPLOADED_GOLDEN_REFERENCE` to start. M8 output still requires a fresh human KLayout review before any later-stage transition.
