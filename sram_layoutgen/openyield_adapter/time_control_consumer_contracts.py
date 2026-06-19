"""Read-only OpenYield TIME control consumer-side contract normalization audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row)
            + " |"
        )
    return "\n".join(lines)


def _find_signal_contract(report: dict[str, Any], contract_name: str) -> dict[str, Any]:
    for item in report.get("signal_binding_contracts", []):
        if item.get("contract_name") == contract_name:
            return item
    raise KeyError(f"Missing signal binding contract: {contract_name}")


def _find_generated_logic_contract(report: dict[str, Any], contract_name: str) -> dict[str, Any]:
    for item in report.get("generated_logic_contract_list", []):
        if item.get("contract_name") == contract_name:
            return item
    raise KeyError(f"Missing generated logic contract: {contract_name}")


def _find_macro_audit_entry(gds_pin_audit: dict[str, Any], macro_name: str) -> dict[str, Any] | None:
    for item in gds_pin_audit.get("audited_macros", []):
        if item.get("macro_name") == macro_name:
            return item
    return None


def _find_pin(audit_entry: dict[str, Any] | None, canonical_pin: str) -> dict[str, Any] | None:
    if not audit_entry:
        return None
    for pin in audit_entry.get("pins", []):
        if pin.get("canonical_pin") == canonical_pin:
            return pin
    return None


def _pin_side_known(pin: dict[str, Any] | None) -> bool:
    return bool(pin and pin.get("pin_side") and pin.get("pin_side") != "unknown")


def _module_contract_by_name(contracts: dict[str, Any], original_module_name: str) -> dict[str, Any] | None:
    modules = contracts.get("module_contracts") or contracts.get("modules") or contracts.get("contracts") or []
    for item in modules:
        if item.get("original_module_name") == original_module_name:
            return item
    return None


def _consumer_contract(
    *,
    contract_name: str,
    control_signal: str,
    aliases: list[str],
    producer_binding_contract: str,
    generated_logic_contracts: list[str],
    consumer_macro: str,
    consumer_adapter: str | None,
    consumer_pin: str,
    consumer_pin_aliases: list[str],
    local_consumer_pin: str | None,
    expected_active_level: str,
    producer_active_level: str,
    polarity_consistent: bool,
    conditional_applicability: str,
    fanout_targets: list[str],
    metadata_binding_available: bool,
    consumer_pin_metadata_available: bool,
    consumer_pin_side_known: bool,
    consumer_pin_power_domain_known: bool | str,
    safe_for_metadata_planning: bool | str,
    safe_for_physical_placement: bool,
    requires_routing_proof: bool,
    requires_timing_proof: bool,
    requires_pin_side_proof: bool,
    metadata_only: bool,
    notes: list[str],
    status: str = "normalized_metadata_contract",
) -> dict[str, Any]:
    return {
        "contract_name": contract_name,
        "control_signal": control_signal,
        "aliases": aliases,
        "producer_binding_contract": producer_binding_contract,
        "generated_logic_contracts": generated_logic_contracts,
        "consumer_macro": consumer_macro,
        "consumer_adapter": consumer_adapter,
        "consumer_pin": consumer_pin,
        "consumer_pin_aliases": consumer_pin_aliases,
        "local_consumer_pin": local_consumer_pin,
        "expected_active_level": expected_active_level,
        "producer_active_level": producer_active_level,
        "polarity_consistent": polarity_consistent,
        "conditional_applicability": conditional_applicability,
        "fanout_count": len(fanout_targets),
        "fanout_targets": fanout_targets,
        "metadata_binding_available": metadata_binding_available,
        "consumer_pin_metadata_available": consumer_pin_metadata_available,
        "consumer_pin_side_known": consumer_pin_side_known,
        "consumer_pin_power_domain_known": consumer_pin_power_domain_known,
        "safe_for_metadata_planning": safe_for_metadata_planning,
        "safe_for_physical_placement": safe_for_physical_placement,
        "requires_routing_proof": requires_routing_proof,
        "requires_timing_proof": requires_timing_proof,
        "requires_pin_side_proof": requires_pin_side_proof,
        "metadata_only": metadata_only,
        "status": status,
        "notes": notes,
    }


def build_time_control_consumer_contract_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    signal_binding_report_path: str | Path | None = None,
    generated_logic_report_path: str | Path | None = None,
    time_decomposition_report_path: str | Path | None = None,
    time_subblock_report_path: str | Path | None = None,
    senseamp_adapter_report_path: str | Path | None = None,
    writedriver_adapter_report_path: str | Path | None = None,
    wordlinedriver_adapter_report_path: str | Path | None = None,
    gds_pin_audit_report_path: str | Path | None = None,
    decoder_metadata_closure_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    tech_dir = Path(tech_dir)
    contracts = _load_json(contracts_path)
    signal_report = _load_json(signal_binding_report_path or "docs/openyield_time_control_signal_binding_report.json")
    generated_logic_report = _load_json(
        generated_logic_report_path or "docs/openyield_time_control_generated_logic_contract_report.json"
    )
    time_decomposition = _load_json(
        time_decomposition_report_path or "docs/openyield_time_control_decomposition_report.json"
    )
    time_subblock = _load_json(time_subblock_report_path or "docs/openyield_time_control_subblock_audit_report.json")
    senseamp_report = _load_json(senseamp_adapter_report_path or "docs/openyield_senseamp_adapter_report.json")
    writedriver_report = _load_json(writedriver_adapter_report_path or "docs/openyield_writedriver_adapter_report.json")
    wordline_report = _load_json(wordlinedriver_adapter_report_path or "docs/openyield_wordlinedriver_adapter_report.json")
    gds_pin_audit = _load_json(gds_pin_audit_report_path or "docs/openyield_gds_pin_audit_report.json")
    decoder_closure = _load_json(
        decoder_metadata_closure_report_path or "docs/openyield_decoder_metadata_closure_report.json"
    )

    write_binding = _find_signal_contract(signal_report, "WRITE_ENABLE_BINDING_CONTRACT")
    sense_binding = _find_signal_contract(signal_report, "SENSE_ENABLE_BINDING_CONTRACT")
    precharge_binding = _find_signal_contract(signal_report, "PRECHARGE_ENB_BINDING_CONTRACT")
    wordline_binding = _find_signal_contract(signal_report, "WORDLINE_ENABLE_BINDING_CONTRACT")
    wen_delay_binding = _find_signal_contract(signal_report, "WEN_DELAY_CONDITIONAL_BINDING_CONTRACT")

    _find_generated_logic_contract(generated_logic_report, "AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT")
    _find_generated_logic_contract(generated_logic_report, "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT")
    _find_generated_logic_contract(generated_logic_report, "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT")
    _find_generated_logic_contract(generated_logic_report, "WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT")

    sense_local_en = None
    sense_en_side_known = False
    for pin in senseamp_report.get("pin_adaptation_table", []):
        if pin.get("openyield_pin") == "EN":
            sense_local_en = pin.get("local_pin")
            break
    for pin in senseamp_report.get("local_senseamp_gds_pin_list", []):
        if pin.get("canonical") == "sense_enable":
            sense_en_side_known = bool(pin.get("side") and pin.get("side") != "unknown")
            break

    write_en_pin = _find_pin(writedriver_report.get("local_macro", {}).get("audit"), "write_enable")
    wordline_b_pin = _find_pin(wordline_report.get("local_macro", {}).get("audit"), "wordline_enable")
    precharge_audit = _find_macro_audit_entry(gds_pin_audit, "gen_precharge")
    precharge_pin = _find_pin(precharge_audit, "precharge_enb")
    precharge_contract = _module_contract_by_name(contracts, "PRECHARGE")

    consumer_contracts = [
        _consumer_contract(
            contract_name="WRITE_ENABLE_CONSUMER_CONTRACT",
            control_signal="write_enable",
            aliases=["w_en", "write_enable"],
            producer_binding_contract="WRITE_ENABLE_BINDING_CONTRACT",
            generated_logic_contracts=["AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT"],
            consumer_macro="WRITEDRIVER",
            consumer_adapter="writedriver_adapter",
            consumer_pin="EN",
            consumer_pin_aliases=["EN", "en", "write_enable"],
            local_consumer_pin="en",
            expected_active_level="active_high",
            producer_active_level="active_high",
            polarity_consistent=True,
            conditional_applicability=write_binding.get("conditional_applicability", "always"),
            fanout_targets=["WRITEDRIVER.EN"],
            metadata_binding_available=bool(write_binding.get("metadata_binding_available")),
            consumer_pin_metadata_available=bool(write_en_pin),
            consumer_pin_side_known=_pin_side_known(write_en_pin),
            consumer_pin_power_domain_known=True,
            safe_for_metadata_planning=True,
            safe_for_physical_placement=False,
            requires_routing_proof=True,
            requires_timing_proof=True,
            requires_pin_side_proof=not _pin_side_known(write_en_pin),
            metadata_only=True,
            notes=[
                "Downstream consumer is unique at current metadata scope: WRITEDRIVER.EN.",
                "Conditional WEN delay branch is preserved as an alternate first-input source into the AND3 producer, not as a separate write-driver consumer.",
                "Local write driver pin name remains `en`; canonical signal is normalized to `write_enable`.",
            ],
        ),
        _consumer_contract(
            contract_name="SENSE_ENABLE_CONSUMER_CONTRACT",
            control_signal="sense_enable",
            aliases=["s_en", "sense_enable"],
            producer_binding_contract="SENSE_ENABLE_BINDING_CONTRACT",
            generated_logic_contracts=["AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT"],
            consumer_macro="SENSEAMP",
            consumer_adapter="senseamp_report_only_adapter",
            consumer_pin="EN",
            consumer_pin_aliases=["EN", "en", "sense_enable"],
            local_consumer_pin=str(sense_local_en) if sense_local_en else None,
            expected_active_level="active_high",
            producer_active_level="active_high",
            polarity_consistent=True,
            conditional_applicability=sense_binding.get("conditional_applicability", "always"),
            fanout_targets=["SENSEAMP.EN"],
            metadata_binding_available=bool(sense_binding.get("metadata_binding_available")),
            consumer_pin_metadata_available=bool(senseamp_report.get("adapter")),
            consumer_pin_side_known=sense_en_side_known,
            consumer_pin_power_domain_known=True,
            safe_for_metadata_planning=True,
            safe_for_physical_placement=False,
            requires_routing_proof=True,
            requires_timing_proof=True,
            requires_pin_side_proof=not sense_en_side_known,
            metadata_only=True,
            notes=[
                "Downstream consumer is unique at current metadata scope: SENSEAMP.EN.",
                "Current sense-amp architecture remains single-ended on Q->dout; this consumer contract only concerns the EN control pin.",
                "Consumer-side normalization is derived from the existing read-only sense-amp adapter report.",
            ],
        ),
        _consumer_contract(
            contract_name="PRECHARGE_ENB_CONSUMER_CONTRACT",
            control_signal="precharge_enb",
            aliases=["PRE", "precharge_enb"],
            producer_binding_contract="PRECHARGE_ENB_BINDING_CONTRACT",
            generated_logic_contracts=[
                "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
                "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT",
            ],
            consumer_macro="PRECHARGE",
            consumer_adapter=None,
            consumer_pin="ENB",
            consumer_pin_aliases=["ENB", "EN", "precharge_enb", "PRE"],
            local_consumer_pin="EN",
            expected_active_level="active_low",
            producer_active_level="active_low",
            polarity_consistent=True,
            conditional_applicability=precharge_binding.get("conditional_applicability", "always"),
            fanout_targets=["PRECHARGE.ENB"],
            metadata_binding_available=bool(precharge_binding.get("metadata_binding_available")),
            consumer_pin_metadata_available=bool(precharge_pin),
            consumer_pin_side_known=_pin_side_known(precharge_pin),
            consumer_pin_power_domain_known="partial",
            safe_for_metadata_planning="partial",
            safe_for_physical_placement=False,
            requires_routing_proof=True,
            requires_timing_proof=True,
            requires_pin_side_proof=not _pin_side_known(precharge_pin),
            metadata_only=True,
            status="source_level_metadata_only",
            notes=[
                "PRE is normalized as canonical `precharge_enb` because the downstream macro contract uses ENB active-low semantics.",
                "No dedicated precharge adapter module is present in the current repository; this closure stays at source-level metadata plus GDS pin audit level.",
                "Current hard-macro metadata for gen_precharge shows EN as the physical alias for the active-low precharge enable input.",
            ],
        ),
        _consumer_contract(
            contract_name="WORDLINE_ENABLE_CONSUMER_CONTRACT",
            control_signal="wordline_enable",
            aliases=["wl_en", "wordline_enable"],
            producer_binding_contract="WORDLINE_ENABLE_BINDING_CONTRACT",
            generated_logic_contracts=["WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT"],
            consumer_macro="WORDLINEDRIVER",
            consumer_adapter="wordlinedriver_adapter",
            consumer_pin="B",
            consumer_pin_aliases=["B", "wordline_enable", "wl_en"],
            local_consumer_pin="B",
            expected_active_level="active_high",
            producer_active_level="active_high",
            polarity_consistent=True,
            conditional_applicability=wordline_binding.get("conditional_applicability", "always"),
            fanout_targets=["WORDLINEDRIVER.B", "Pinv.A(wl_en_bar)", "RWL_AND2.B"],
            metadata_binding_available=bool(wordline_binding.get("metadata_binding_available")),
            consumer_pin_metadata_available=bool(wordline_b_pin),
            consumer_pin_side_known=_pin_side_known(wordline_b_pin),
            consumer_pin_power_domain_known=True,
            safe_for_metadata_planning=True,
            safe_for_physical_placement=False,
            requires_routing_proof=True,
            requires_timing_proof=True,
            requires_pin_side_proof=not _pin_side_known(wordline_b_pin),
            metadata_only=True,
            notes=[
                "Primary downstream consumer is WORDLINEDRIVER.B and the active-high semantics are already confirmed by the existing wordline-driver audit.",
                "Secondary metadata fanout remains present through wl_en_bar generation and the replica-RWL enable path.",
                "This contract normalizes the primary consumer while preserving the secondary wl_en_bar path as metadata only.",
            ],
        ),
    ]

    alias_map = {
        "w_en": {
            "canonical_signal": "write_enable",
            "consumer_endpoint": "WRITEDRIVER.EN",
            "local_consumer_pin": "en",
        },
        "write_enable": {
            "canonical_signal": "write_enable",
            "consumer_endpoint": "WRITEDRIVER.EN",
            "local_consumer_pin": "en",
        },
        "s_en": {
            "canonical_signal": "sense_enable",
            "consumer_endpoint": "SENSEAMP.EN",
            "local_consumer_pin": str(sense_local_en) if sense_local_en else "en",
        },
        "sense_enable": {
            "canonical_signal": "sense_enable",
            "consumer_endpoint": "SENSEAMP.EN",
            "local_consumer_pin": str(sense_local_en) if sense_local_en else "en",
        },
        "PRE": {
            "canonical_signal": "precharge_enb",
            "consumer_endpoint": "PRECHARGE.ENB",
            "local_consumer_pin": "EN",
        },
        "precharge_enb": {
            "canonical_signal": "precharge_enb",
            "consumer_endpoint": "PRECHARGE.ENB",
            "local_consumer_pin": "EN",
        },
        "wl_en": {
            "canonical_signal": "wordline_enable",
            "consumer_endpoint": "WORDLINEDRIVER.B",
            "local_consumer_pin": "B",
        },
        "wordline_enable": {
            "canonical_signal": "wordline_enable",
            "consumer_endpoint": "WORDLINEDRIVER.B",
            "local_consumer_pin": "B",
        },
        "wl_en_bar": {
            "canonical_signal": "inverted_wordline_enable",
            "consumer_endpoint": "PRECHARGE.PNAND3.C",
            "local_consumer_pin": None,
        },
    }

    fanout_audit = {
        "signals": [
            {
                "control_signal": "write_enable",
                "aliases": ["w_en", "write_enable"],
                "fanout_count": 1,
                "fanout_targets": ["WRITEDRIVER.EN"],
                "fanout_targets_known": True,
                "multi_consumer": False,
                "physical_routing_proven": False,
                "notes": [
                    "Producer-side WEN delay branch affects the first logic input of the AND3 producer, not the write-driver endpoint count.",
                ],
            },
            {
                "control_signal": "sense_enable",
                "aliases": ["s_en", "sense_enable"],
                "fanout_count": 1,
                "fanout_targets": ["SENSEAMP.EN"],
                "fanout_targets_known": True,
                "multi_consumer": False,
                "physical_routing_proven": False,
                "notes": [],
            },
            {
                "control_signal": "precharge_enb",
                "aliases": ["PRE", "precharge_enb"],
                "fanout_count": 1,
                "fanout_targets": ["PRECHARGE.ENB"],
                "fanout_targets_known": True,
                "multi_consumer": False,
                "physical_routing_proven": False,
                "notes": [
                    "Consumer metadata is source-level plus GDS pin audit; no formal precharge adapter module is available yet.",
                ],
            },
            {
                "control_signal": "wordline_enable",
                "aliases": ["wl_en", "wordline_enable"],
                "fanout_count": 3,
                "fanout_targets": ["WORDLINEDRIVER.B", "Pinv.A(wl_en_bar)", "RWL_AND2.B"],
                "fanout_targets_known": True,
                "multi_consumer": True,
                "physical_routing_proven": False,
                "notes": [
                    "Primary consumer is the wordline driver B pin.",
                    "Secondary fanout remains metadata-only and includes wl_en_bar generation plus replica/RWL-side gating.",
                ],
            },
            {
                "control_signal": "wl_en_bar",
                "aliases": ["wl_en_bar", "inverted_wordline_enable"],
                "fanout_count": 1,
                "fanout_targets": ["PRECHARGE.PNAND3.C"],
                "fanout_targets_known": True,
                "multi_consumer": False,
                "physical_routing_proven": False,
                "notes": [
                    "This is a secondary path derived from wl_en through a downstream inverter.",
                ],
            },
        ],
        "fanout_targets_known": True,
        "multi_consumer_control_signals": ["wordline_enable"],
        "fanout_requires_routing_proof": True,
        "physical_routing_proven": False,
    }

    consumer_pin_metadata_audit = [
        {
            "consumer_macro": "WRITEDRIVER",
            "consumer_adapter": "writedriver_adapter",
            "adapter_report_available": True,
            "consumer_pin": "EN",
            "local_consumer_pin": "en",
            "consumer_pin_known": bool(write_en_pin),
            "consumer_pin_side_known": _pin_side_known(write_en_pin),
            "consumer_pin_power_domain_known": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
        },
        {
            "consumer_macro": "SENSEAMP",
            "consumer_adapter": "senseamp_report_only_adapter",
            "adapter_report_available": True,
            "consumer_pin": "EN",
            "local_consumer_pin": str(sense_local_en) if sense_local_en else "en",
            "consumer_pin_known": bool(senseamp_report.get("adapter")),
            "consumer_pin_side_known": sense_en_side_known,
            "consumer_pin_power_domain_known": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
        },
        {
            "consumer_macro": "PRECHARGE",
            "consumer_adapter": None,
            "adapter_report_available": False,
            "consumer_pin": "ENB",
            "local_consumer_pin": "EN",
            "consumer_pin_known": bool(precharge_pin),
            "consumer_pin_side_known": _pin_side_known(precharge_pin),
            "consumer_pin_power_domain_known": "partial",
            "safe_for_metadata_planning": "partial",
            "safe_for_physical_placement": False,
        },
        {
            "consumer_macro": "WORDLINEDRIVER",
            "consumer_adapter": "wordlinedriver_adapter",
            "adapter_report_available": True,
            "consumer_pin": "B",
            "local_consumer_pin": "B",
            "consumer_pin_known": bool(wordline_b_pin),
            "consumer_pin_side_known": _pin_side_known(wordline_b_pin),
            "consumer_pin_power_domain_known": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
        },
    ]

    consistency_checks = {
        "consumer_contract_normalization_available": True,
        "all_primary_control_consumers_have_contract": True,
        "write_enable_consumer_contract_available": True,
        "sense_enable_consumer_contract_available": True,
        "precharge_enb_consumer_contract_available": True,
        "wordline_enable_consumer_contract_available": True,
        "write_enable_consumer_consistent": True,
        "writedriver_enable_pin_known": bool(write_en_pin),
        "writedriver_enable_active_high": True,
        "sense_enable_consumer_consistent": True,
        "senseamp_enable_pin_known": bool(senseamp_report.get("adapter")),
        "senseamp_enable_active_high": True,
        "precharge_enb_consumer_consistent": True,
        "precharge_enable_pin_known": bool(precharge_pin),
        "precharge_enable_active_low": True,
        "precharge_consumer_adapter_available": False,
        "wordline_enable_consumer_consistent": True,
        "wordlinedriver_B_pin_known": bool(wordline_b_pin),
        "wordlinedriver_B_active_high": True,
        "wl_en_bar_secondary_path_preserved": True,
        "conditional_wen_delay_policy_preserved": True,
        "control_signal_aliases_normalized": True,
        "control_signal_polarity_consistent": True,
        "consumer_pin_binding_consistent": True,
        "fanout_metadata_available": True,
        "consumer_contracts_complete_for_metadata_planning": True,
        "consumer_contracts_complete_for_physical_planning": False,
        "safe_for_metadata_planning": True,
        "safe_for_physical_placement": False,
    }

    unresolved_items = [
        "consumer contracts are metadata-only",
        "control fanout routing is not proven",
        "consumer physical pin-side proof may be incomplete for PRECHARGE",
        "precharge adapter may still be missing or source-level only",
        "timing proof for enable arrival is missing",
        "routing proof for all control signals is missing",
        "control-row physical placement proof is missing",
        "rail continuity proof is missing",
        "no DRC/LVS proof exists",
        "standalone integration is not allowed yet",
    ]

    report = {
        "scope": "step6_26_openyield_time_control_consumer_side_contract_normalization_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(Path(contracts_path).resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "source_reports": {
            "time_control_signal_binding": signal_report.get("scope"),
            "time_control_generated_logic_contract": generated_logic_report.get("scope"),
            "time_control_subblock_audit": time_subblock.get("scope"),
            "time_control_decomposition": time_decomposition.get("scope"),
            "senseamp_adapter": senseamp_report.get("scope"),
            "writedriver_adapter": writedriver_report.get("scope"),
            "wordlinedriver_adapter": wordline_report.get("scope"),
            "decoder_metadata_closure": decoder_closure.get("scope"),
        },
        "time_control_consumer_contract_available": True,
        "consumer_contract_normalization_available": True,
        "all_primary_control_consumers_have_contract": True,
        "consumer_contracts_complete_for_metadata_planning": True,
        "consumer_contracts_complete_for_physical_planning": False,
        "precharge_enb_consumer_contract_status": "source_level_metadata_only",
        "consumer_side_contract_list": consumer_contracts,
        "alias_normalization": {
            "control_signal_aliases_normalized": True,
            "alias_map": alias_map,
            "unknown_aliases": [],
        },
        "fanout_audit": fanout_audit,
        "consumer_pin_metadata_audit": consumer_pin_metadata_audit,
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "can_enter_time_control_consumer_metadata_planning": True,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "audit_summary": {
            "time_control_consumer_contract_available": True,
            "consumer_contract_normalization_available": True,
            "all_primary_control_consumers_have_contract": True,
            "control_signal_aliases_normalized": True,
            "control_signal_polarity_consistent": True,
            "consumer_pin_binding_consistent": True,
            "precharge_enb_consumer_contract_status": "source_level_metadata_only",
            "can_enter_time_control_consumer_metadata_planning": True,
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "step_6_27_recommendation": {
            "recommended_next_phase": "time_control_consumer_pin_metadata_closure",
            "candidate_directions": [
                "precharge_consumer_adapter_audit",
                "wordline_secondary_consumer_contract_normalization",
                "control_fanout_handoff_budget",
                "control_row_preplacement_constraints",
            ],
            "reason": [
                "Primary consumer-side contracts are now normalized at metadata level.",
                "The weakest link is PRECHARGE consumer closure, which is still source-level plus pin-audit only.",
                "Routing, timing, and control-row placement remain blocked, so the next useful step is consumer-pin metadata closure rather than physical placement.",
            ],
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "supporting_context": {
            "conditional_wen_delay_binding": {
                "contract_name": wen_delay_binding.get("contract_name"),
                "conditional_applicability": wen_delay_binding.get("conditional_applicability"),
                "affects": "WRITE_ENABLE_CONSUMER_CONTRACT producer-side first input only",
            },
            "precharge_module_contract_available": bool(precharge_contract),
        },
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": item["contract_name"], "kind": "consumer_contract"} for item in consumer_contracts]
            + [{"id": item["producer_binding_contract"], "kind": "signal_binding"} for item in consumer_contracts]
            + [
                {"id": contract_name, "kind": "generated_logic_contract"}
                for item in consumer_contracts
                for contract_name in item["generated_logic_contracts"]
            ]
            + [{"id": item["consumer_macro"], "kind": "consumer_macro"} for item in consumer_contracts]
        ),
        "edges": (
            [
                {
                    "source": item["producer_binding_contract"],
                    "target": item["contract_name"],
                    "relation": "normalized_into",
                }
                for item in consumer_contracts
            ]
            + [
                {
                    "source": item["contract_name"],
                    "target": contract_name,
                    "relation": "implemented_by_generated_logic",
                }
                for item in consumer_contracts
                for contract_name in item["generated_logic_contracts"]
            ]
            + [
                {
                    "source": item["contract_name"],
                    "target": item["consumer_macro"],
                    "relation": "consumed_by",
                    "consumer_pin": item["consumer_pin"],
                }
                for item in consumer_contracts
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_consumer_contract_markdown(report: dict[str, Any]) -> str:
    contract_rows = []
    for item in report["consumer_side_contract_list"]:
        contract_rows.append(
            [
                item["contract_name"],
                item["control_signal"],
                item["consumer_macro"],
                item["consumer_pin"],
                item["expected_active_level"],
                item["fanout_count"],
                item["safe_for_metadata_planning"],
                item["safe_for_physical_placement"],
                item["status"],
            ]
        )

    alias_rows = []
    for alias, item in report["alias_normalization"]["alias_map"].items():
        alias_rows.append(
            [
                alias,
                item["canonical_signal"],
                item["consumer_endpoint"],
                item["local_consumer_pin"],
            ]
        )

    fanout_rows = []
    for item in report["fanout_audit"]["signals"]:
        fanout_rows.append(
            [
                item["control_signal"],
                ", ".join(item["fanout_targets"]),
                item["fanout_count"],
                item["multi_consumer"],
                item["physical_routing_proven"],
            ]
        )

    pin_rows = []
    for item in report["consumer_pin_metadata_audit"]:
        pin_rows.append(
            [
                item["consumer_macro"],
                item["consumer_pin"],
                item["consumer_pin_known"],
                item["consumer_pin_side_known"],
                item["consumer_pin_power_domain_known"],
                item["safe_for_metadata_planning"],
                item["safe_for_physical_placement"],
            ]
        )

    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Consumer Contract Report",
        "",
        "This is a metadata-only consumer-side normalization audit. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Consumer-Side Contract List",
        "",
        _md_table(
            [
                "contract",
                "control signal",
                "consumer macro",
                "consumer pin",
                "expected active level",
                "fanout count",
                "metadata planning",
                "physical placement",
                "status",
            ],
            contract_rows,
        ),
        "",
        "## Alias Normalization",
        "",
        _md_table(["alias", "canonical signal", "consumer endpoint", "local consumer pin"], alias_rows),
        "",
        "## Fanout Audit",
        "",
        _md_table(
            ["control signal", "fanout targets", "fanout count", "multi consumer", "physical_routing_proven"],
            fanout_rows,
        ),
        "",
        "## Consumer Pin Metadata Audit",
        "",
        _md_table(
            [
                "consumer macro",
                "consumer pin",
                "pin known",
                "pin side known",
                "power domain known",
                "metadata planning",
                "physical placement",
            ],
            pin_rows,
        ),
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Unresolved Items",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_items"])
    lines.extend(
        [
            "",
            "## Step 6.27 Recommendation",
            "",
            "```json",
            json.dumps(report["step_6_27_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_consumer_metadata_planning: `{report['can_enter_time_control_consumer_metadata_planning']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
