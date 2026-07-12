from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from sram_layoutgen.signoff import count_klayout_items


def _nm(expr: str) -> int:
    return int(round(float(expr.replace("_", "")) * 1e9))


def _parse_requested_dimensions(child_row: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    params = child_row.get("parameter_expression") or {}
    if isinstance(params, str):
        try:
            params = ast.literal_eval(params)
        except Exception:
            params = {}
    if child_row["child_logical_module"] == "PINV":
        arg_text = str(params.get("__args__", ""))
        pieces = [piece.strip() for piece in arg_text.split("|") if piece.strip()]
        if len(pieces) >= 5:
            return _nm(pieces[2]), _nm(pieces[3]), _nm(pieces[4])
    if child_row["child_logical_module"] == "TRANSMISSION_GATE":
        return 250, 500, 50
    return None, None, None


def _fingerprint_digest(cell_dir: Path) -> str:
    payload = json.loads((cell_dir / f"{cell_dir.name}_geometry_fingerprint.json").read_text(encoding="utf-8"))
    return str(payload.get("digest", ""))


def _pin_names(cell_dir: Path) -> list[str]:
    pin_map = json.loads((cell_dir / f"{cell_dir.name}_pin_map.json").read_text(encoding="utf-8"))
    return list(pin_map.keys())


def _connectivity_contract_passed(path: Path) -> bool:
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels = set(payload.get("pin_labels", {}).keys())
    return bool(payload.get("components")) and bool(labels)


def build_dff_instance_binding_matrix(
    *,
    repo_root: Path,
    contract: dict[str, Any],
    dff_child_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    approved_root = Path(contract["approved_reusable_cell_root"]).resolve()
    expected_pinv = "PINV_NW250_PW500_L50"
    expected_tg = contract["approved_transmission_gate_cell"]
    rows: list[dict[str, Any]] = []

    for child_row in dff_child_rows:
        instance_name = str(child_row["instance_name_expression"]).strip("'\"")
        child_module = child_row["child_logical_module"]
        expected_pins = contract["approved_canonical_pin_names"]["PINV" if child_module == "PINV" else "TRANSMISSION_GATE"]
        requested_nmos, requested_pmos, requested_length = _parse_requested_dimensions(child_row)
        resolved_cell = expected_pinv if child_module == "PINV" else expected_tg
        cell_dir = approved_root / resolved_cell
        gds_path = cell_dir / f"{resolved_cell}.gds"
        pin_map_path = cell_dir / f"{resolved_cell}_pin_map.json"
        connectivity_path = Path(contract["approved_connectivity_reports"][resolved_cell])
        drc_path = Path(contract["approved_drc_reports"][resolved_cell])
        fingerprint_path = cell_dir / f"{resolved_cell}_geometry_fingerprint.json"
        actual_pin_names = _pin_names(cell_dir) if pin_map_path.exists() else []
        actual_digest = _fingerprint_digest(cell_dir) if fingerprint_path.exists() else ""
        marker_count = count_klayout_items(drc_path) if drc_path.exists() else -1
        geometry_match = actual_digest == contract["approved_geometry_fingerprints"][resolved_cell]
        pin_namespace_match = actual_pin_names == expected_pins
        forbidden_source_root_used = not str(cell_dir.resolve()).startswith(str(approved_root))
        connectivity_contract_passed = _connectivity_contract_passed(connectivity_path) if connectivity_path.exists() else False
        binding_status = "APPROVED_EXACT_BINDING"
        binding_failure_reason = ""
        if forbidden_source_root_used:
            binding_status = "FORBIDDEN_SOURCE"
            binding_failure_reason = "resolved cell is outside approved reusable root"
        elif not gds_path.exists():
            binding_status = "MISSING_GDS"
            binding_failure_reason = "approved reusable GDS path missing"
        elif not geometry_match:
            binding_status = "FINGERPRINT_MISMATCH"
            binding_failure_reason = "geometry fingerprint does not match composition contract"
        elif not pin_namespace_match:
            binding_status = "PIN_NAMESPACE_MISMATCH"
            binding_failure_reason = "canonical pin namespace mismatch"
        elif marker_count != 0:
            binding_status = "DRC_NOT_CLEAN"
            binding_failure_reason = "approved DRC report marker count is not zero"
        elif not connectivity_contract_passed:
            binding_status = "CONNECTIVITY_NOT_APPROVED"
            binding_failure_reason = "approved connectivity artifact is missing or incomplete"
        elif child_module == "PINV" and (requested_nmos, requested_pmos, requested_length) != (250, 500, 50):
            binding_status = "PARAMETER_MISMATCH"
            binding_failure_reason = f"requested PINV dimensions {(requested_nmos, requested_pmos, requested_length)} do not match approved DFF inverter"

        rows.append(
            {
                "instance_name": instance_name,
                "source_line": int(child_row["source_line"]),
                "child_logical_module": child_module,
                "child_pin_order": json.dumps(child_row["child_pin_order"]),
                "parent_net_connections": json.dumps(child_row["parent_net_connections"]),
                "requested_nmos_width_nm": requested_nmos,
                "requested_pmos_width_nm": requested_pmos,
                "requested_channel_length_nm": requested_length,
                "resolved_physical_cell_name": resolved_cell,
                "approved_reusable_gds_path": str(gds_path.resolve()),
                "approved_geometry_fingerprint": actual_digest,
                "approved_pin_map_path": str(pin_map_path.resolve()),
                "approved_connectivity_report_path": str(connectivity_path.resolve()),
                "approved_drc_report_path": str(drc_path.resolve()),
                "expected_canonical_pin_names": json.dumps(expected_pins),
                "actual_canonical_pin_names": json.dumps(actual_pin_names),
                "pin_namespace_match": pin_namespace_match,
                "forbidden_source_root_used": forbidden_source_root_used,
                "geometry_fingerprint_match": geometry_match,
                "drc_marker_count": marker_count,
                "connectivity_contract_passed": connectivity_contract_passed,
                "binding_status": binding_status,
                "binding_failure_reason": binding_failure_reason,
            }
        )

    approved_count = sum(1 for row in rows if row["binding_status"] == "APPROVED_EXACT_BINDING")
    failed_count = len(rows) - approved_count
    return {
        "rows": rows,
        "summary": {
            "dff_binding_row_count": len(rows),
            "dff_approved_binding_count": approved_count,
            "dff_failed_binding_count": failed_count,
            "dff_pinv_approved_binding_count": sum(1 for row in rows if row["child_logical_module"] == "PINV" and row["binding_status"] == "APPROVED_EXACT_BINDING"),
            "dff_tg_approved_binding_count": sum(1 for row in rows if row["child_logical_module"] == "TRANSMISSION_GATE" and row["binding_status"] == "APPROVED_EXACT_BINDING"),
            "dff_forbidden_source_binding_count": sum(1 for row in rows if row["binding_status"] == "FORBIDDEN_SOURCE"),
            "dff_unique_physical_cell_count": len({row["resolved_physical_cell_name"] for row in rows}),
            "dff_concrete_binding_complete": approved_count == len(rows) and failed_count == 0,
        },
    }
