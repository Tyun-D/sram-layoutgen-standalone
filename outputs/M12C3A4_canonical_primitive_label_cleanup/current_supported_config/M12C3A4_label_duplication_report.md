# M12C3A4 Label Duplication Report

- label_duplication_root_cause: `OpenRAM-backed wrapper exports canonical top labels, referenced core exports lowercase aliases, and referenced PTX leaves export device-terminal G/S/D labels into the final hierarchy.`
- why_duplicate_text_does_not_change_conductive_geometry: `GDS TEXT/TEXTTYPE records do not alter polygons, contacts, wells, implants, or routing shapes.`
- why_duplicate_labels_can_confuse_lvs_and_extraction: `Duplicate net names, alias overlap, and leaked terminal labels can produce ambiguous net naming during extraction and top-level pin identification.`
- why_composite_generation_is_blocked_until_label_cleanup: `Composite CONTROL_LOGIC assembly needs a stable reusable primitive pin namespace with exactly one canonical top-level label per pin.`
- pinv_duplicate_label_cell_count: `9`
- transmission_gate_duplicate_label_count: `12`
- internal_gsd_label_leakage_detected: `True`
