"""Generate guarded legacy and hybrid OpenYield layout prototypes."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sram_layoutgen.gds_util import inspect_gds_hierarchy, measure_gds_bbox
from sram_layoutgen.standalone import StandaloneSpec, write_standalone

from .timing_metadata_consumer import (
    build_consumable_timing_objects,
    emit_consumer_summary,
    load_candidate_contracts,
    load_control_mapping,
    summary_to_dict,
)


DEFAULT_LAYOUT_CASE = {
    "word_size": 8,
    "num_words": 64,
    "words_per_row": 4,
}

REQUIRED_COVERAGE_OBJECTS = [
    "bitcell_array",
    "dummy_array",
    "replica_array",
    "DELAY_CHAIN",
    "PRECHARGE",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
    "sense_amp",
    "write_driver",
    "column_mux",
    "wordline_driver",
]


def generate_layout_prototype(
    repo_root: str | Path,
    mode: str,
    out_dir: str | Path,
    metadata_dir: str | Path = "docs",
    word_size: int = DEFAULT_LAYOUT_CASE["word_size"],
    num_words: int = DEFAULT_LAYOUT_CASE["num_words"],
    words_per_row: int = DEFAULT_LAYOUT_CASE["words_per_row"],
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    out = resolve_dir(repo, out_dir)
    docs = resolve_dir(repo, metadata_dir)
    out.mkdir(parents=True, exist_ok=True)

    support = load_support_bundle(docs)
    spec = build_spec(mode, word_size, num_words, words_per_row)
    metrics = write_standalone(spec, out)
    gds_path = (repo / metrics["gds"]).resolve() if not Path(metrics["gds"]).is_absolute() else Path(metrics["gds"]).resolve()
    sanity = build_gds_sanity(repo, gds_path, metrics, out)
    coverage = build_module_coverage(mode, metrics, support)

    coverage_json = out / "module_coverage.json"
    coverage_md = out / "module_coverage.md"
    write_json(coverage_json, coverage)
    coverage_md.write_text(render_module_coverage_markdown(coverage), encoding="utf-8")

    log_name = "baseline_generation.log" if mode == "legacy_baseline" else "hybrid_generation.log"
    log_path = out / log_name
    log_path.write_text(render_generation_log(mode, spec, metrics, support, sanity, coverage), encoding="utf-8")

    result = {
        "mode": mode,
        "spec": {
            "word_size": spec.word_size,
            "num_words": spec.num_words,
            "words_per_row": spec.resolved_words_per_row(),
            "name": spec.resolved_name(),
            "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
            "enable_openyield_senseamp_adapter": spec.enable_openyield_senseamp_adapter,
            "enable_openyield_columnmux_adapter": spec.enable_openyield_columnmux_adapter,
            "enable_openyield_writedriver_adapter": spec.enable_openyield_writedriver_adapter,
            "enable_openyield_wordlinedriver_adapter": spec.enable_openyield_wordlinedriver_adapter,
            "openyield_storage_row_orientation_policy": spec.openyield_storage_row_orientation_policy,
        },
        "out_dir": str(out),
        "metrics": metrics,
        "gds_path": str(gds_path),
        "gds_size_bytes": gds_path.stat().st_size if gds_path.exists() else 0,
        "generation_log": str(log_path),
        "module_coverage_json": str(coverage_json),
        "module_coverage_md": str(coverage_md),
        "support_bundle": support,
        "gds_sanity": sanity,
        "module_coverage": coverage,
        "openyield_driven_modules": [
            row["module_or_object"]
            for row in coverage
            if not row["fallback_used"] and row["source"].startswith("openyield")
        ],
        "fallback_modules": [row["module_or_object"] for row in coverage if row["fallback_used"]],
        "routing_modified": any(
            bool(metrics.get(key, {}).get("routing_changed", False))
            for key in (
                "openyield_columnmux_adapter",
                "openyield_senseamp_adapter",
                "openyield_writedriver_adapter",
                "openyield_wordlinedriver_adapter",
                "openyield_array_aggregation_integration",
            )
        ),
        "gds_writer_modified": any(
            bool(metrics.get(key, {}).get("gds_writer_changed", False))
            for key in (
                "openyield_columnmux_adapter",
                "openyield_senseamp_adapter",
                "openyield_writedriver_adapter",
                "openyield_wordlinedriver_adapter",
                "openyield_array_aggregation_integration",
            )
        ),
        "standalone_default_behavior_preserved": True,
        "standalone_modified_for_explicit_opt_in": True,
    }
    write_json(out / "prototype_result.json", result)

    docs_report = build_docs_report(repo)
    write_json(repo / "docs/openyield_layout_prototype_generation_report.json", docs_report)
    (repo / "docs/openyield_layout_prototype_generation_report.md").write_text(
        render_docs_report_markdown(docs_report),
        encoding="utf-8",
    )
    return result


def resolve_dir(repo: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def build_spec(mode: str, word_size: int, num_words: int, words_per_row: int) -> StandaloneSpec:
    if mode == "legacy_baseline":
        return StandaloneSpec(
            word_size=word_size,
            num_words=num_words,
            words_per_row=words_per_row,
            name="legacy_baseline",
        )
    if mode == "hybrid_openyield_prototype":
        return StandaloneSpec(
            word_size=word_size,
            num_words=num_words,
            words_per_row=words_per_row,
            name="hybrid_openyield_prototype",
            enable_openyield_array_aggregation=True,
            enable_openyield_senseamp_adapter=True,
            enable_openyield_columnmux_adapter=True,
            enable_openyield_writedriver_adapter=True,
            enable_openyield_wordlinedriver_adapter=True,
            openyield_storage_row_orientation_policy="alternating_mx",
        )
    raise ValueError(f"unsupported mode: {mode}")


def load_support_bundle(docs_root: Path) -> dict[str, Any]:
    timing_json = docs_root / "openyield_delay_chain_timing_metadata_report.json"
    source_json = docs_root / "openyield_source_provenance_linking_report.json"
    audit_json = docs_root / "openyield_source_linked_timing_metadata_audit_report.json"
    mapping_csv = docs_root / "mapping/openyield_control_timing_mapping.csv"
    contracts_csv = docs_root / "mapping/openyield_control_path_candidate_contracts.csv"
    consumer_summary = summary_to_dict(
        emit_consumer_summary(
            timing_json,
            source_json,
            audit_json,
            mapping_csv,
        )
    )
    timing_objects = {
        name: asdict(obj)
        for name, obj in build_consumable_timing_objects(timing_json, source_json, mapping_csv).items()
    }
    mappings = [asdict(item) for item in load_control_mapping(mapping_csv)]
    contracts = [asdict(item) for item in load_candidate_contracts(contracts_csv)]
    return {
        "timing_json": str(timing_json.resolve()),
        "source_json": str(source_json.resolve()),
        "audit_json": str(audit_json.resolve()),
        "mapping_csv": str(mapping_csv.resolve()),
        "contracts_csv": str(contracts_csv.resolve()),
        "consumer_summary": consumer_summary,
        "timing_objects": timing_objects,
        "control_mapping": mappings,
        "candidate_contracts": contracts,
        "openyield_metadata_consumed": bool(consumer_summary["gates"].get("consumer_api_ready", False)),
        "timing_metadata_consumer_used": True,
        "candidate_contracts_used": True,
    }


def build_gds_sanity(repo: Path, gds_path: Path, metrics: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    exists = gds_path.exists()
    size = gds_path.stat().st_size if exists else 0
    bbox = measure_gds_bbox(gds_path) if exists else None
    hierarchy = inspect_gds_hierarchy(gds_path) if exists else {}
    summary_path = out_dir / "klayout_summary.json"
    klayout = shutil.which("klayout")
    klayout_ok = False
    klayout_error = None
    if klayout and exists:
        cmd = [
            klayout,
            "-b",
            "-r",
            str((repo / "scripts/klayout_gds_summary.rb").resolve()),
            "-rd",
            f"input={gds_path}",
            "-rd",
            f"output={summary_path}",
            "-rd",
            f"topcell={metrics['name']}",
        ]
        run = subprocess.run(cmd, capture_output=True, text=True)
        klayout_ok = run.returncode == 0 and summary_path.exists()
        if not klayout_ok:
            klayout_error = (run.stderr or run.stdout).strip() or f"klayout exited {run.returncode}"
    klayout_summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
    return {
        "gds_file_exists": exists,
        "gds_file_size_bytes": size,
        "gds_file_size_gt_zero": size > 0,
        "top_cell_name": metrics["name"],
        "bbox_um": bbox.to_dict() if bbox else None,
        "structure_count": hierarchy.get("structure_count"),
        "can_be_opened_by_klayout": klayout_ok,
        "klayout_summary": klayout_summary,
        "klayout_error": klayout_error,
    }


def build_module_coverage(mode: str, metrics: dict[str, Any], support: dict[str, Any]) -> list[dict[str, Any]]:
    counts = metrics.get("role_counts", {})
    storage = metrics.get("openyield_array_aggregation_integration", {})
    sense = metrics.get("openyield_senseamp_adapter", {})
    column = metrics.get("openyield_columnmux_adapter", {})
    write = metrics.get("openyield_writedriver_adapter", {})
    wordline = metrics.get("openyield_wordlinedriver_adapter", {})
    mappings = {row["openyield_object"]: row for row in support["control_mapping"]}
    contracts = {row["control_object"]: row for row in support["candidate_contracts"]}
    delay = support["timing_objects"].get("DELAY_CHAIN", {})

    def row(
        module: str,
        source: str,
        used: bool,
        physical: str,
        placement: str,
        routing: str,
        power: str,
        fallback: bool,
        reason: str,
        evidence: str,
        next_action: str,
    ) -> dict[str, Any]:
        return {
            "module_or_object": module,
            "source": source,
            "used_in_gds": used,
            "physical_cell_source": physical,
            "placement_status": placement,
            "routing_status": routing,
            "power_status": power,
            "fallback_used": fallback,
            "fallback_reason": reason,
            "evidence_status": evidence,
            "next_required_action": next_action,
        }

    rows = [
        row(
            "bitcell_array",
            "openyield_storage_array_aggregation" if storage.get("enabled") else "legacy_layoutgen",
            bool(counts.get("bitcell_array", 0)),
            "cell_1rw hardcell array",
            "openyield_storage_opt_in" if storage.get("enabled") else "legacy_array_placement",
            "array_abutment",
            "bundled_freepdk45_power_rails",
            not bool(storage.get("enabled")),
            "legacy storage aggregation path retained" if not storage.get("enabled") else "",
            "storage_array_physical_ready" if storage.get("enabled") else "legacy_only",
            "physical gap closure on non-storage peripherals",
        ),
        row(
            "dummy_array",
            "openyield_storage_array_aggregation" if storage.get("enabled") else "legacy_layoutgen",
            bool(counts.get("dummy_bitcell", 0)),
            "dummy_cell_1rw hardcell array",
            "openyield_storage_opt_in" if storage.get("enabled") else "legacy_array_placement",
            "array_abutment",
            "bundled_freepdk45_power_rails",
            not bool(storage.get("enabled")),
            "legacy storage aggregation path retained" if not storage.get("enabled") else "",
            "storage_array_physical_ready" if storage.get("enabled") else "legacy_only",
            "keep dummy-row physical evidence aligned with storage aggregation",
        ),
        row(
            "replica_array",
            "openyield_storage_array_aggregation" if storage.get("enabled") else "legacy_layoutgen",
            bool(counts.get("replica_bitline", 0)),
            "replica_cell_1rw hardcell array",
            "openyield_storage_opt_in" if storage.get("enabled") else "legacy_array_placement",
            "array_abutment",
            "bundled_freepdk45_power_rails",
            not bool(storage.get("enabled")),
            "legacy replica placement retained" if not storage.get("enabled") else "",
            "storage_array_physical_ready" if storage.get("enabled") else "legacy_only",
            "extend replica/control coupling proof",
        ),
        row(
            "DELAY_CHAIN",
            "openyield_timing_metadata_consumer_plus_legacy_hardmacro",
            bool(counts.get("delay_chain", 0)),
            "legacy gen_delay_inv macro chain",
            "legacy_fallback_control_timing",
            "legacy_top_level_routing",
            "bundled_freepdk45_power_rails",
            True,
            "timing metadata is consumable but physical integration is not claimed",
            delay.get("evidence_status", mappings.get("DELAY_CHAIN", {}).get("evidence_status", "unknown")),
            mappings.get("DELAY_CHAIN", {}).get("next_required_action", "implement physical control-timing adapter"),
        ),
        row(
            "PRECHARGE",
            "openyield_precharge_source_plus_legacy_macro",
            bool(counts.get("precharge", 0)),
            "legacy gen_precharge macro",
            "legacy_fallback_precharge_row",
            "legacy_top_level_routing",
            "bundled_freepdk45_power_rails",
            True,
            "source-linked candidate exists but no OpenYield physical macro is installed",
            mappings.get("PRECHARGE", {}).get("evidence_status", "source_linked_candidate_only"),
            mappings.get("PRECHARGE", {}).get("next_required_action", "confirm pin polarity and physical macro evidence"),
        ),
    ]
    for control_object in [
        "PRECHARGE_ENABLE_PATH",
        "SENSE_ENABLE_PATH",
        "WRITE_ENABLE_PATH",
        "WORDLINE_ENABLE_PATH",
        "GATED_CLOCK_PATH",
        "DFF_ROW",
    ]:
        mapping = mappings.get(control_object, {})
        contract = contracts.get(control_object, {})
        rows.append(
            row(
                control_object,
                "openyield_candidate_contract_plus_legacy_control_logic",
                True,
                "legacy control-logic composition",
                "legacy_fallback_control_logic",
                "legacy_top_level_routing",
                "bundled_freepdk45_power_rails",
                True,
                "candidate contract exists, but no physical-ready OpenYield implementation is present",
                mapping.get("evidence_status", contract.get("source_evidence_status", "candidate_contract_only")),
                mapping.get("next_required_action", contract.get("next_required_action", "decompose TIME/control path physically")),
            )
        )
    rows.extend([
        row(
            "sense_amp",
            "openyield_senseamp_semantic_adapter" if sense.get("enabled") else "legacy_layoutgen",
            bool(counts.get("sense_amp", 0)),
            "legacy sense_amp hardmacro",
            "openyield_adapter_applied" if sense.get("enabled") else "legacy_placement",
            "legacy_top_level_routing",
            "bundled_freepdk45_power_rails",
            not bool(sense.get("enabled")),
            "legacy sense_amp path retained" if not sense.get("enabled") else "",
            "semantic_adapter_ready" if sense.get("enabled") else "legacy_only",
            "prove grouped read-path fanout and downstream physical timing",
        ),
        row(
            "write_driver",
            "openyield_writedriver_adapter" if write.get("enabled") else "legacy_layoutgen",
            bool(counts.get("write_driver", 0)),
            write.get("local_macro", "write_driver"),
            "openyield_adapter_applied" if write.get("enabled") else "legacy_placement",
            "legacy_top_level_routing",
            "shared_rail_disabled" if write.get("enabled") else "bundled_freepdk45_power_rails",
            not bool(write.get("enabled")),
            "legacy write-driver path retained" if not write.get("enabled") else "",
            "physical_mapping_ready" if write.get("safe_for_physical_mapping") else "adapter_not_enabled",
            "complete grouped write-path fanout proof and rail continuity proof",
        ),
        row(
            "column_mux",
            "openyield_columnmux_adapter" if column.get("enabled") else "legacy_layoutgen",
            bool(counts.get("column_mux", 0)),
            column.get("local_macro", "gen_col_mux"),
            "openyield_adapter_applied" if column.get("enabled") else "legacy_placement",
            "legacy_top_level_routing",
            "shared_rail_disabled" if column.get("enabled") else "bundled_freepdk45_power_rails",
            not bool(column.get("enabled")),
            "legacy column mux path retained" if not column.get("enabled") else "",
            "repaired_alias_candidate_only" if column.get("enabled") else "legacy_only",
            "prove shared rail continuity and preserve repaired candidate install discipline",
        ),
        row(
            "wordline_driver",
            "openyield_wordlinedriver_adapter" if wordline.get("enabled") else "legacy_layoutgen",
            bool(counts.get("wordline_driver", 0)),
            wordline.get("local_macro", "gen_wl_driver"),
            "openyield_adapter_applied" if wordline.get("enabled") else "legacy_placement",
            "legacy_top_level_routing",
            "shared_rail_disabled" if wordline.get("enabled") else "bundled_freepdk45_power_rails",
            not bool(wordline.get("enabled")),
            "legacy wordline-driver path retained" if not wordline.get("enabled") else "",
            wordline.get("semantic_confirmation", "legacy_only"),
            "finish TIME/control-path physical decomposition and rail proof",
        ),
    ])
    if mode == "legacy_baseline":
        for item in rows:
            if item["module_or_object"] not in {"DELAY_CHAIN", "PRECHARGE"}:
                item["source"] = "legacy_layoutgen"
            item["fallback_used"] = True
            if not item["fallback_reason"]:
                item["fallback_reason"] = "legacy baseline mode keeps the default path only"
    assert {item["module_or_object"] for item in rows} == set(REQUIRED_COVERAGE_OBJECTS)
    return rows


def render_generation_log(
    mode: str,
    spec: StandaloneSpec,
    metrics: dict[str, Any],
    support: dict[str, Any],
    sanity: dict[str, Any],
    coverage: list[dict[str, Any]],
) -> str:
    return "\n".join([
        f"mode={mode}",
        f"name={metrics['name']}",
        f"word_size={spec.word_size}",
        f"num_words={spec.num_words}",
        f"words_per_row={spec.resolved_words_per_row()}",
        f"gds={metrics['gds']}",
        f"gds_size_bytes={sanity['gds_file_size_bytes']}",
        f"drc_clean={metrics['drc_clean']}",
        f"openyield_metadata_consumed={support['openyield_metadata_consumed']}",
        f"timing_metadata_consumer_used={support['timing_metadata_consumer_used']}",
        f"candidate_contracts_used={support['candidate_contracts_used']}",
        f"module_coverage_rows={len(coverage)}",
        f"fallback_count={sum(1 for row in coverage if row['fallback_used'])}",
        f"klayout_open_ok={sanity['can_be_opened_by_klayout']}",
    ]) + "\n"


def build_docs_report(repo: Path) -> dict[str, Any]:
    baseline = load_result(repo / "outputs/layout_prototype/baseline_legacy/prototype_result.json")
    hybrid = load_result(repo / "outputs/layout_prototype/hybrid_openyield/prototype_result.json")
    hybrid_coverage = hybrid.get("module_coverage", []) if hybrid else []
    gates = {
        "layout_prototype_generation_available": bool(baseline or hybrid),
        "legacy_baseline_attempted": bool(baseline),
        "legacy_baseline_gds_generated": bool(baseline and baseline["gds_sanity"]["gds_file_exists"] and baseline["gds_sanity"]["gds_file_size_gt_zero"]),
        "hybrid_openyield_attempted": bool(hybrid),
        "hybrid_openyield_gds_generated": bool(hybrid and hybrid["gds_sanity"]["gds_file_exists"] and hybrid["gds_sanity"]["gds_file_size_gt_zero"]),
        "gds_output_path": hybrid.get("gds_path") if hybrid else (baseline.get("gds_path") if baseline else None),
        "module_coverage_available": bool(hybrid and hybrid.get("module_coverage_json")),
        "openyield_metadata_consumed": bool(hybrid and hybrid["support_bundle"].get("openyield_metadata_consumed", False)),
        "timing_metadata_consumer_used": bool(hybrid and hybrid["support_bundle"].get("timing_metadata_consumer_used", False)),
        "candidate_contracts_used": bool(hybrid and hybrid["support_bundle"].get("candidate_contracts_used", False)),
        "fallbacks_recorded": any(row.get("fallback_used", False) for row in hybrid_coverage),
        "standalone_default_behavior_preserved": bool((hybrid or baseline) and (hybrid or baseline).get("standalone_default_behavior_preserved", False)),
        "standalone_modified_for_explicit_opt_in": bool((hybrid or baseline) and (hybrid or baseline).get("standalone_modified_for_explicit_opt_in", False)),
        "routing_modified": bool(hybrid and hybrid.get("routing_modified", False)),
        "gds_writer_modified": bool(hybrid and hybrid.get("gds_writer_modified", False)),
        "can_claim_full_openyield_layout_now": False,
        "can_claim_lvs_clean_now": False,
        "can_claim_drc_clean_now": False,
        "can_claim_timing_closure_now": False,
        "can_enter_physical_gap_closure": bool(hybrid and hybrid["gds_sanity"]["gds_file_exists"]),
        "can_enter_guarded_openyield_layout_integration": bool(hybrid and hybrid["gds_sanity"]["gds_file_exists"]),
    }
    return {
        "scope": "openyield_layout_prototype_generation",
        "baseline": baseline,
        "hybrid": hybrid,
        "gates": gates,
        "openyield_driven_modules": hybrid.get("openyield_driven_modules", []) if hybrid else [],
        "fallback_modules": hybrid.get("fallback_modules", []) if hybrid else [],
        "physical_gap_summary": [
            "TIME / DFF / control logic remain candidate-contract or metadata-only; no full physical OpenYield implementation is installed.",
            "Routing is still legacy/top-level layoutgen routing, not OpenYield-driven routing.",
            "Shared rail continuity is not proven for repaired/peripheral hardmacros.",
            "Column mux repaired alias is candidate-only and must not be treated as full signoff collateral.",
            "No LVS closure, no timing closure, and no full-chip DRC signoff are claimed.",
        ],
    }


def render_docs_report_markdown(report: dict[str, Any]) -> str:
    gates = report["gates"]
    lines = [
        "# OpenYield Layout Prototype Generation Report",
        "",
        f"- legacy baseline attempted: `{gates['legacy_baseline_attempted']}`",
        f"- legacy baseline GDS generated: `{gates['legacy_baseline_gds_generated']}`",
        f"- hybrid OpenYield attempted: `{gates['hybrid_openyield_attempted']}`",
        f"- hybrid OpenYield GDS generated: `{gates['hybrid_openyield_gds_generated']}`",
        f"- module coverage available: `{gates['module_coverage_available']}`",
        f"- openyield metadata consumed: `{gates['openyield_metadata_consumed']}`",
        f"- timing metadata consumer used: `{gates['timing_metadata_consumer_used']}`",
        f"- candidate contracts used: `{gates['candidate_contracts_used']}`",
        f"- fallbacks recorded: `{gates['fallbacks_recorded']}`",
        f"- standalone default behavior preserved: `{gates['standalone_default_behavior_preserved']}`",
        f"- standalone modified for explicit opt-in: `{gates['standalone_modified_for_explicit_opt_in']}`",
        f"- routing modified: `{gates['routing_modified']}`",
        f"- gds writer modified: `{gates['gds_writer_modified']}`",
        f"- can claim full OpenYield layout now: `{gates['can_claim_full_openyield_layout_now']}`",
        f"- can claim LVS clean now: `{gates['can_claim_lvs_clean_now']}`",
        f"- can claim DRC clean now: `{gates['can_claim_drc_clean_now']}`",
        f"- can claim timing closure now: `{gates['can_claim_timing_closure_now']}`",
        f"- can enter physical gap closure: `{gates['can_enter_physical_gap_closure']}`",
        f"- can enter guarded OpenYield layout integration: `{gates['can_enter_guarded_openyield_layout_integration']}`",
        "",
        "## OpenYield-Driven Modules",
        "",
    ]
    for item in report.get("openyield_driven_modules", []):
        lines.append(f"- {item}")
    if not report.get("openyield_driven_modules"):
        lines.append("- none yet")
    lines.extend(["", "## Fallback Modules", ""])
    for item in report.get("fallback_modules", []):
        lines.append(f"- {item}")
    if not report.get("fallback_modules"):
        lines.append("- none recorded")
    lines.extend(["", "## Physical Gaps", ""])
    for item in report.get("physical_gap_summary", []):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def render_module_coverage_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Module Coverage",
        "",
        "| module_or_object | source | used_in_gds | physical_cell_source | placement_status | routing_status | power_status | fallback_used | fallback_reason | evidence_status | next_required_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {module_or_object} | {source} | {used_in_gds} | {physical_cell_source} | {placement_status} | {routing_status} | {power_status} | {fallback_used} | {fallback_reason} | {evidence_status} | {next_required_action} |".format(**row)
        )
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_result(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
