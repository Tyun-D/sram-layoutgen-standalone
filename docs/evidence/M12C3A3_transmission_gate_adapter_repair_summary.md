# M12C3A3 Transmission Gate Adapter Repair Summary

- reused_previous_artifacts: `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.*, PROJECT_NETLIST_TO_LAYOUT_*, docs/M12C3A_parameterized_device_gate_generator_report.*, outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/*`
- deprecated_previous_artifacts: `original Transmission Gate shorted source-drain-to-power helper metal, poly-only control pin exports, identical aggregate GDS artifacts, empty geometry fingerprint digest artifacts`
- human_review_findings: `PINV passed 9 reviewed variants; Transmission Gate failed due to IN-VDD/VSS short and poly-only control pins.`
- why_M12C3A_cannot_be_claimed_fully_qualified: `human review found a real electrical defect after machine generation and DRC.`
- why_DRC_zero_did_not_detect_the_short: `cell-level DRC checks spacing/width/enclosure markers, not transistor-level net semantics.`
- current_stage_delta_from_M12C3A: `repair-only regeneration of the Transmission Gate plus machine connectivity verification.`
- why_only_transmission_gate_is_regenerated: `all 9 PINV variants already passed human review and remain unchanged.`
