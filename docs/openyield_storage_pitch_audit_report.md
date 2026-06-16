# OpenYield Storage Pitch Audit Report

This report audits storage-cell legal abutment pitch using GDS boundary rectangles and TEXT pin records. It does not modify placement policy, routing, GDS writer behavior, shared rails, or peripheral aggregation.

## Conclusion

- recommended_storage_pitch_policy: `use_full_bbox_pitch`
- reason: Full bbox pitch is conservative and eliminates same-layer physical overlap.
- area impact: Area increases by the amount measured in Step 4.6.
- DRC risk: low for cell-cell overlap, higher for global placement/routing impact.
- LVS risk: low for pitch policy alone.
- OpenYield netlist semantics: Pitch policy is physical-layout metadata only. It does not change OpenYield netlist hierarchy, ports, or instance connectivity.
- keep enable_openyield_array_aggregation default closed: `True`
- connectivity_not_proven: `True`
- manual_layout_review_required: `True`

## Macro Summary

| macro | bbox | legacy overlap x/y | legacy risky layers | audit overlap | recommended pitch | confidence |
| --- | --- | --- | --- | --- | --- | --- |
| cell_1rw | (-0.095, -0.1)-(0.8, 1.465); 0.895 x 1.565 | 0.19 / 0.2 | active, contact, m1, m2, via1 | False | 0.895 x 1.565 | medium |
| dummy_cell_1rw | (-0.095, -0.1)-(0.8, 1.465); 0.895 x 1.565 | 0.19 / 0.2 | active, contact, m1, m2, via1 | False | 0.895 x 1.565 | medium |
| replica_cell_1rw | (-0.095, -0.1)-(0.8, 1.465); 0.895 x 1.565 | 0.19 / 0.2 | active, contact, m1, m2, via1 | False | 0.895 x 1.565 | medium |

## cell_1rw

- GDS bbox: `(-0.095, -0.1)-(0.8, 1.465); 0.895 x 1.565`
- logical marker pitch: `0.705 x 1.365`
- text marker bbox: `(0.0, 0.02)-(0.705, 1.365); 0.705 x 1.345`
- boundary extension: `{'left': 0.095, 'right': 0.095, 'bottom': 0.1, 'top': 0.1, 'negative_origin': True}`

Pin / rail bbox:

| pin | layer | point | bbox | found boundary |
| --- | --- | --- | --- | --- |
| bl | m2 | {'x': 0.19, 'y': 0.003} | (0.15, -0.08)-(0.22, 1.465); 0.07 x 1.545 | True |
| br | m2 | {'x': 0.52, 'y': 0.003} | (0.485, -0.08)-(0.555, 1.465); 0.07 x 1.545 | True |
| gnd | m1 | {'x': 0.345, 'y': 0.0} | (-0.09, -0.0325)-(0.795, 0.0325); 0.885 x 0.065 | True |
| q | m1 | {'x': 0.0825, 'y': 0.46} | (0.05, 0.2775)-(0.12, 0.5675); 0.07 x 0.29 | True |
| q_bar | m1 | {'x': 0.625, 'y': 0.48} | (0.59, 0.2775)-(0.66, 0.5675); 0.07 x 0.29 | True |
| vdd | m1 | {'x': 0.345, 'y': 1.365} | (-0.09, 1.3325)-(0.795, 1.3975); 0.885 x 0.065 | True |
| wl | m1 | {'x': -0.05, 'y': 0.167} | (-0.09, 0.1275)-(0.795, 0.1925); 0.885 x 0.065 | True |

Legacy pitch overlap:

- pitch: `0.705 x 1.365`
- bbox overlap x/y: `0.19 / 0.2`
- fully bbox separated: `False`
- extra gap x/y: `0.0 / 0.0`
- classification: `{'has_real_shape_overlap': True, 'risky_layers': ['active', 'contact', 'm1', 'm2', 'via1'], 'mostly_power_or_boundary': False, 'acceptable_as_legal_abutment': False, 'connectivity_not_proven': True, 'manual_layout_review_required': True, 'reason': 'Risk layers overlap; manual GDS/DRC review is required.'}`

| direction | overlap count | area | layers | risky layers |
| --- | --- | --- | --- | --- |
| horizontal | 687 | 5.812404 | active:0.2727, contact:0.00845, m1:1.801056, m2:1.9203, nimplant:0.01435, nwell:0.177925, pimplant:0.0063, pwell:0.405825, via1:0.6422, vtg:0.5633 | active:0.2727, contact:0.00845, m1:1.801056, m2:1.9203, via1:0.6422 |
| vertical R0-MX | 43 | 1.016798 | active:0.0324, contact:0.004225, m1:0.057525, m2:0.0791, nimplant:0.0324, nwell:0.57125, vtg:0.2399 | active:0.0324, contact:0.004225 |

Audit bbox pitch overlap:

- pitch: `0.895 x 1.565`
- bbox overlap x/y: `0.0 / 0.0`
- fully bbox separated: `True`
- extra gap x/y: `0.0 / 0.0`
- classification: `{'has_real_shape_overlap': False, 'risky_layers': [], 'mostly_power_or_boundary': False, 'acceptable_as_legal_abutment': False, 'connectivity_not_proven': True, 'manual_layout_review_required': False, 'reason': 'No same-layer shape overlap was found.'}`

| direction | overlap count | area | layers | risky layers |
| --- | --- | --- | --- | --- |
| horizontal | 0 | 0.0 | - | - |
| vertical R0-MX | 0 | 0.0 | - | - |

Recommendation: `0.895 x 1.565` (medium) - Full bbox pitch eliminates same-layer physical overlap; legacy pitch has risky overlaps.

## dummy_cell_1rw

- GDS bbox: `(-0.095, -0.1)-(0.8, 1.465); 0.895 x 1.565`
- logical marker pitch: `0.705 x 1.365`
- text marker bbox: `(0.0, 0.02)-(0.705, 1.365); 0.705 x 1.345`
- boundary extension: `{'left': 0.095, 'right': 0.095, 'bottom': 0.1, 'top': 0.1, 'negative_origin': True}`

Pin / rail bbox:

| pin | layer | point | bbox | found boundary |
| --- | --- | --- | --- | --- |
| bl | m2 | {'x': 0.19, 'y': 0.003} | (0.15, -0.08)-(0.22, 1.465); 0.07 x 1.545 | True |
| br | m2 | {'x': 0.52, 'y': 0.003} | (0.485, -0.08)-(0.555, 1.465); 0.07 x 1.545 | True |
| gnd | m1 | {'x': 0.345, 'y': 0.0} | (-0.09, -0.0325)-(0.795, 0.0325); 0.885 x 0.065 | True |
| vdd | m1 | {'x': 0.345, 'y': 1.365} | (-0.09, 1.3325)-(0.795, 1.3975); 0.885 x 0.065 | True |
| wl | m1 | {'x': -0.05, 'y': 0.167} | (-0.09, 0.1275)-(0.795, 0.1925); 0.885 x 0.065 | True |

Legacy pitch overlap:

- pitch: `0.705 x 1.365`
- bbox overlap x/y: `0.19 / 0.2`
- fully bbox separated: `False`
- extra gap x/y: `0.0 / 0.0`
- classification: `{'has_real_shape_overlap': True, 'risky_layers': ['active', 'contact', 'm1', 'm2', 'via1'], 'mostly_power_or_boundary': False, 'acceptable_as_legal_abutment': False, 'connectivity_not_proven': True, 'manual_layout_review_required': True, 'reason': 'Risk layers overlap; manual GDS/DRC review is required.'}`

| direction | overlap count | area | layers | risky layers |
| --- | --- | --- | --- | --- |
| horizontal | 699 | 5.877856 | active:0.2697, contact:0.00845, m1:1.836156, m2:1.9537, nimplant:0.01435, nwell:0.177925, pimplant:0.0063, pwell:0.405825, via1:0.6422, vtg:0.5633 | active:0.2697, contact:0.00845, m1:1.836156, m2:1.9537, via1:0.6422 |
| vertical R0-MX | 43 | 1.016798 | active:0.0324, contact:0.004225, m1:0.057525, m2:0.0791, nimplant:0.0324, nwell:0.57125, vtg:0.2399 | active:0.0324, contact:0.004225 |

Audit bbox pitch overlap:

- pitch: `0.895 x 1.565`
- bbox overlap x/y: `0.0 / 0.0`
- fully bbox separated: `True`
- extra gap x/y: `0.0 / 0.0`
- classification: `{'has_real_shape_overlap': False, 'risky_layers': [], 'mostly_power_or_boundary': False, 'acceptable_as_legal_abutment': False, 'connectivity_not_proven': True, 'manual_layout_review_required': False, 'reason': 'No same-layer shape overlap was found.'}`

| direction | overlap count | area | layers | risky layers |
| --- | --- | --- | --- | --- |
| horizontal | 0 | 0.0 | - | - |
| vertical R0-MX | 0 | 0.0 | - | - |

Recommendation: `0.895 x 1.565` (medium) - Full bbox pitch eliminates same-layer physical overlap; legacy pitch has risky overlaps.

## replica_cell_1rw

- GDS bbox: `(-0.095, -0.1)-(0.8, 1.465); 0.895 x 1.565`
- logical marker pitch: `0.705 x 1.365`
- text marker bbox: `(0.0, 0.02)-(0.705, 1.365); 0.705 x 1.345`
- boundary extension: `{'left': 0.095, 'right': 0.095, 'bottom': 0.1, 'top': 0.1, 'negative_origin': True}`

Pin / rail bbox:

| pin | layer | point | bbox | found boundary |
| --- | --- | --- | --- | --- |
| bl | m2 | {'x': 0.19, 'y': 0.003} | (0.15, -0.08)-(0.22, 1.465); 0.07 x 1.545 | True |
| br | m2 | {'x': 0.52, 'y': 0.003} | (0.485, -0.08)-(0.555, 1.465); 0.07 x 1.545 | True |
| gnd | m1 | {'x': 0.345, 'y': 0.0} | (-0.09, -0.0325)-(0.795, 0.0325); 0.885 x 0.065 | True |
| vdd | m1 | {'x': 0.35, 'y': 1.365} | (-0.09, 1.3325)-(0.795, 1.3975); 0.885 x 0.065 | True |
| wl | m1 | {'x': -0.05, 'y': 0.167} | (-0.09, 0.1275)-(0.795, 0.1925); 0.885 x 0.065 | True |

Legacy pitch overlap:

- pitch: `0.705 x 1.365`
- bbox overlap x/y: `0.19 / 0.2`
- fully bbox separated: `False`
- extra gap x/y: `0.0 / 0.0`
- classification: `{'has_real_shape_overlap': True, 'risky_layers': ['active', 'contact', 'm1', 'm2', 'via1'], 'mostly_power_or_boundary': False, 'acceptable_as_legal_abutment': False, 'connectivity_not_proven': True, 'manual_layout_review_required': True, 'reason': 'Risk layers overlap; manual GDS/DRC review is required.'}`

| direction | overlap count | area | layers | risky layers |
| --- | --- | --- | --- | --- |
| horizontal | 699 | 5.877856 | active:0.2697, contact:0.00845, m1:1.836156, m2:1.9537, nimplant:0.01435, nwell:0.177925, pimplant:0.0063, pwell:0.405825, via1:0.6422, vtg:0.5633 | active:0.2697, contact:0.00845, m1:1.836156, m2:1.9537, via1:0.6422 |
| vertical R0-MX | 45 | 1.018422 | active:0.0324, contact:0.004225, m1:0.05915, m2:0.0791, nimplant:0.0324, nwell:0.57125, vtg:0.2399 | active:0.0324, contact:0.004225 |

Audit bbox pitch overlap:

- pitch: `0.895 x 1.565`
- bbox overlap x/y: `0.0 / 0.0`
- fully bbox separated: `True`
- extra gap x/y: `0.0 / 0.0`
- classification: `{'has_real_shape_overlap': False, 'risky_layers': [], 'mostly_power_or_boundary': False, 'acceptable_as_legal_abutment': False, 'connectivity_not_proven': True, 'manual_layout_review_required': False, 'reason': 'No same-layer shape overlap was found.'}`

| direction | overlap count | area | layers | risky layers |
| --- | --- | --- | --- | --- |
| horizontal | 0 | 0.0 | - | - |
| vertical R0-MX | 0 | 0.0 | - | - |

Recommendation: `0.895 x 1.565` (medium) - Full bbox pitch eliminates same-layer physical overlap; legacy pitch has risky overlaps.

## Pitch Metadata Recommendation

The generator should distinguish `physical_bbox_pitch`, `legal_abutment_pitch`, `routing_keepout_pitch`, and `report_bbox_pitch`. Full bbox pitch is useful for reporting and conservative spacing, while legal abutment pitch should remain a separate field until DRC/manual review proves the allowed overlap.

- should modify `array_aggregation.py` now: `False`
- recommendation: Do not change array_aggregation.py yet. First decide whether to add separate physical_bbox_pitch, legal_abutment_pitch, routing_keepout_pitch, and report_bbox_pitch metadata.

## Next Steps

- Keep the OpenYield enabled path on full bbox pitch for now; use legacy logical marker pitch only as an area baseline unless DRC/manual review proves the overlap is legal.
- Add explicit pitch metadata fields before changing the enabled OpenYield aggregation path.
- Run KLayout visual/DRC review on a tiny storage-only array to classify well/implant/rail stitching versus illegal active/poly overlap.
