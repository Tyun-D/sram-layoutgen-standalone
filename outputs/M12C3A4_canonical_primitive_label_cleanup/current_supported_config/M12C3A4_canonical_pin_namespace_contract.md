# M12C3A4 Canonical Pin Namespace Contract

## PINV
- canonical_pin_names: `['VDD', 'VSS', 'A', 'Z']`
- forbidden_aliases: `['vdd', 'gnd']`
- label_case_policy: `UPPERCASE_CANONICAL_ONLY`
- one_label_per_pin_policy: `EXACTLY_ONE`
- child_label_visibility_policy: `STRIP_FROM_REUSABLE_EXPORT`

## TRANSMISSION_GATE
- canonical_pin_names: `['VDD', 'VSS', 'IN', 'OUT', 'CTR_P', 'CTR_N']`
- forbidden_aliases: `['vdd', 'gnd', 'in', 'out', 'ctr_p', 'ctr_n']`
- label_case_policy: `UPPERCASE_CANONICAL_ONLY`
- one_label_per_pin_policy: `EXACTLY_ONE`
- child_label_visibility_policy: `STRIP_FROM_REUSABLE_EXPORT`
