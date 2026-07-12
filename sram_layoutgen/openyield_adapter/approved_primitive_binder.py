from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PINV_WIDTH_MAP_NM = {
    (90, 270): "PINV_NW90_PW270_L50",
    (180, 270): "PINV_NW180_PW270_L50",
    (180, 540): "PINV_NW180_PW540_L50",
    (250, 500): "PINV_NW250_PW500_L50",
    (270, 810): "PINV_NW270_PW810_L50",
    (360, 1080): "PINV_NW360_PW1080_L50",
    (450, 1350): "PINV_NW450_PW1350_L50",
    (910, 2430): "PINV_NW910_PW2430_L50",
    (2430, 7290): "PINV_NW2430_PW7290_L50",
}


def _nm(value_expr: str | float | int) -> int:
    if isinstance(value_expr, (int, float)):
        return int(round(float(value_expr) * 1e9))
    text = str(value_expr).replace("_", "").strip()
    if text.endswith("e-6"):
        return int(round(float(text) * 1e9))
    return int(round(float(text) * 1e9))


def resolve_pinv_variant(nmos_expr: str | float | int, pmos_expr: str | float | int) -> str | None:
    try:
        key = (_nm(nmos_expr), _nm(pmos_expr))
    except Exception:
        return None
    return PINV_WIDTH_MAP_NM.get(key)


def provenance_source_trace_path(repo_root: Path, cell_name: str) -> str:
    if cell_name.startswith("PINV_"):
        return str((repo_root / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/cells" / cell_name / f"{cell_name}_source_trace.json").resolve())
    return str(
        (
            repo_root
            / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/TRANSMISSION_GATE_NW250_PW500_L50/TRANSMISSION_GATE_NW250_PW500_L50_source_trace.json"
        ).resolve()
    )


def load_contract(contract_path: Path) -> dict[str, Any]:
    return json.loads(contract_path.read_text(encoding="utf-8"))


def bind_child_instances(
    *,
    repo_root: Path,
    contract: dict[str, Any],
    child_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    approved_root = contract["approved_reusable_cell_root"]
    approved_bindings = 0
    new_generator_count = 0
    reference_only_rejected_count = 0
    forbidden_source_binding_count = 0
    unresolved_count = 0
    rows: list[dict[str, Any]] = []

    for row in child_rows:
        child_module = str(row["child_logical_module"]).split(".")[-1]
        binding_status = "UNRESOLVED_PARAMETER"
        resolved = ""
        reason = ""
        params = row.get("child_parameter_expression") or {}
        if child_module in {"Pinv", "PINV"}:
            nmos_expr = params.get("nmos_width") or params.get("arg", "")
            pmos_expr = params.get("pmos_width") or params.get("arg", "")
            constructor_expr = str(row.get("child_constructor_expression", ""))
            if "Pinv(" in constructor_expr:
                args_text = constructor_expr[constructor_expr.find("(") + 1 : constructor_expr.rfind(")")]
                args = [part.strip() for part in args_text.split(",")]
                if len(args) >= 5:
                    nmos_expr = args[2]
                    pmos_expr = args[3]
            resolved = resolve_pinv_variant(nmos_expr, pmos_expr) or ""
            if resolved:
                binding_status = "APPROVED_EXACT_BINDING"
            elif any(symbol in str(nmos_expr) or symbol in str(pmos_expr) for symbol in ["drive_scale", "stage", "s1", "s2", "s3", "s4", "w_en_scale", "pre_drive_scale"]):
                binding_status = "UNRESOLVED_PARAMETER"
                reason = f"symbolic PINV width expression requires concrete configuration expansion: nmos={nmos_expr} pmos={pmos_expr}"
                unresolved_count += 1
            else:
                binding_status = "NEW_PRIMITIVE_GENERATOR_REQUIRED"
                reason = f"no approved PINV variant for nmos={nmos_expr} pmos={pmos_expr}"
                new_generator_count += 1
        elif child_module in {"TransmissionGate", "TRANSMISSION_GATE"}:
            resolved = contract["approved_transmission_gate_cell"]
            binding_status = "APPROVED_EXACT_BINDING"
        elif child_module in {"PNAND2", "PNAND3"}:
            binding_status = "NEW_PRIMITIVE_GENERATOR_REQUIRED"
            reason = "OpenYield NAND physical primitive is not approved in the M12C3A4R reusable contract."
            new_generator_count += 1
        elif child_module in {"AND2", "AND3", "dff", "DFF", "DFF_BUF", "ADDR_DFF", "DATA_DFF", "pdrive", "pdrive2_for_pre", "wl_pdrive", "DelayChain", "delay_chain", "WenDelayChain", "TIME"}:
            binding_status = "APPROVED_SHARED_PHYSICAL_VARIANT"
            reason = "composite child stays hierarchical; leaf primitive binding is resolved separately"
        else:
            unresolved_count += 1
            reason = "unrecognized child logical module"
        if binding_status.startswith("APPROVED"):
            approved_bindings += 1
        rows.append(
            {
                "parent_composite_module": row["module_name"],
                "parent_instance_context": row["child_instance_name"],
                "child_logical_alias": row["child_logical_module"],
                "child_source_parameter_tuple": json.dumps(row.get("child_parameter_expression") or {}, sort_keys=True),
                "resolved_physical_cell_name": resolved,
                "approved_reusable_root": approved_root if resolved else "",
                "geometry_fingerprint": contract["approved_geometry_fingerprints"].get(resolved, "") if resolved else "",
                "canonical_pin_map": contract["approved_connectivity_reports"].get(resolved, "").replace("_connectivity.json", "_pin_map.json") if resolved else "",
                "drc_report": contract["approved_drc_reports"].get(resolved, "") if resolved else "",
                "connectivity_report": contract["approved_connectivity_reports"].get(resolved, "") if resolved else "",
                "source_trace": provenance_source_trace_path(repo_root, resolved) if resolved else "",
                "binding_status": binding_status,
                "binding_failure_reason": reason,
            }
        )
    return {
        "rows": rows,
        "summary": {
            "approved_child_binding_count": approved_bindings,
            "new_primitive_generator_requirement_count": new_generator_count,
            "reference_only_binding_rejected_count": reference_only_rejected_count,
            "forbidden_binding_rejected_count": forbidden_source_binding_count,
            "forbidden_source_binding_count": forbidden_source_binding_count,
            "unresolved_concrete_binding_count": unresolved_count,
        },
    }
