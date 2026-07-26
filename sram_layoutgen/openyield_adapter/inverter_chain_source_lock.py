from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_OPENYIELD_COMMIT = "1c34428d8b913963c4971d093b1a7c2df97a2509"
TIME_GENERATE_PATH = "sram_compiler/subcircuits/time_generate.py"
EXPECTED_TIME_GENERATE_BLOB = "16b38c5a5d3165f046557941d15d425bbcab20b5"


MODULE_SPECS: dict[str, dict[str, Any]] = {
    "pdrive2_for_pre": {
        "class_name": "pdrive2_for_pre",
        "top_cell_name": "PDRIVE2_FOR_PRE_FPDK45",
        "top_pin_order": ["VDD", "VSS", "A", "Z"],
        "internal_nets": ["zb1_node"],
        "output_polarity": "NONINVERTING",
        "child_variants": ["PINV_NW90_PW270_L50", "PINV_NW270_PW810_L50"],
        "logical_children": [
            {"logical_child": "inv1", "source_instance_path": "pdrive2_for_pre.inv1", "requested_nmos_width_nm": 90, "requested_pmos_width_nm": 270, "requested_length_nm": 50},
            {"logical_child": "inv2", "source_instance_path": "pdrive2_for_pre.inv2", "requested_nmos_width_nm": 270, "requested_pmos_width_nm": 810, "requested_length_nm": 50},
        ],
    },
    "wl_pdrive": {
        "class_name": "wl_pdrive",
        "top_cell_name": "WL_PDRIVE_FPDK45",
        "top_pin_order": ["VDD", "VSS", "A", "Z"],
        "internal_nets": ["zb1_node"],
        "output_polarity": "NONINVERTING",
        "child_variants": ["PINV_NW90_PW270_L50", "PINV_NW450_PW1350_L50"],
        "logical_children": [
            {"logical_child": "inv1", "source_instance_path": "wl_pdrive.inv1", "requested_nmos_width_nm": 90, "requested_pmos_width_nm": 270, "requested_length_nm": 50},
            {"logical_child": "inv2", "source_instance_path": "wl_pdrive.inv2", "requested_nmos_width_nm": 450, "requested_pmos_width_nm": 1350, "requested_length_nm": 50},
        ],
    },
    "pdrive": {
        "class_name": "pdrive",
        "top_cell_name": "PDRIVE_FPDK45",
        "top_pin_order": ["VDD", "VSS", "A", "Z"],
        "internal_nets": ["zb1_node", "zb2_node", "zb3_node"],
        "output_polarity": "NONINVERTING",
        "child_variants": ["PINV_NW90_PW270_L50", "PINV_NW270_PW810_L50", "PINV_NW910_PW2430_L50", "PINV_NW2430_PW7290_L50"],
        "logical_children": [
            {"logical_child": "inv1", "source_instance_path": "pdrive.inv1", "requested_nmos_width_nm": 90, "requested_pmos_width_nm": 270, "requested_length_nm": 50},
            {"logical_child": "inv2", "source_instance_path": "pdrive.inv2", "requested_nmos_width_nm": 270, "requested_pmos_width_nm": 810, "requested_length_nm": 50},
            {"logical_child": "inv3", "source_instance_path": "pdrive.inv3", "requested_nmos_width_nm": 910, "requested_pmos_width_nm": 2430, "requested_length_nm": 50},
            {"logical_child": "inv4", "source_instance_path": "pdrive.inv4", "requested_nmos_width_nm": 2430, "requested_pmos_width_nm": 7290, "requested_length_nm": 50},
        ],
    },
}


def _run_git(openyield_root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(openyield_root), *args], text=True, capture_output=True, check=True)
    return completed.stdout


def _git_show_bytes(openyield_root: Path, commit: str, relpath: str) -> bytes:
    completed = subprocess.run(["git", "-C", str(openyield_root), "show", f"{commit}:{relpath}"], capture_output=True, check=True)
    return completed.stdout


def _git_blob_sha(openyield_root: Path, commit: str, relpath: str) -> str:
    line = _run_git(openyield_root, "ls-tree", commit, relpath).strip()
    parts = line.split()
    if len(parts) < 3:
        raise RuntimeError(f"unable to read blob sha for {relpath}")
    return parts[2]


def _find_class(module: ast.Module, name: str) -> ast.ClassDef:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise RuntimeError(f"class {name} not found")


def _find_method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError(f"method {class_node.name}.{name} not found")


def _const_eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            else:
                raise ValueError(f"unsupported f-string part: {ast.dump(value)}")
        return "".join(parts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _const_eval(node.operand)
        if isinstance(value, (int, float)):
            return -value
    if isinstance(node, ast.BinOp):
        left = _const_eval(node.left)
        right = _const_eval(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def _expr_text(source_text: str, node: ast.AST | None) -> str:
    if node is None:
        return ""
    return ast.get_source_segment(source_text, node) or ""


def _extract_ctor_defaults(source_text: str, class_node: ast.ClassDef) -> dict[str, Any]:
    ctor = _find_method(class_node, "__init__")
    args = ctor.args.args
    defaults = ctor.args.defaults
    offset = len(args) - len(defaults)
    result: dict[str, Any] = {}
    for index, arg in enumerate(args):
        if index == 0:
            continue
        default_node = defaults[index - offset] if index >= offset else None
        value = None
        if default_node is not None:
            try:
                value = _const_eval(default_node)
            except Exception:
                value = None
        result[arg.arg] = {
            "default_expr": _expr_text(source_text, default_node),
            "default_value": value,
        }
    return result


def _extract_instance_rows(source_text: str, class_node: ast.ClassDef) -> list[dict[str, Any]]:
    method = _find_method(class_node, "add_buffer_chain")
    rows: list[dict[str, Any]] = []
    for stmt in method.body:
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            continue
        call = stmt.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "X" or len(call.args) < 3:
            continue
        rows.append(
            {
                "display_instance_name": _const_eval(call.args[0]),
                "resolved_child_name_expr": _expr_text(source_text, call.args[1]),
                "nets": [(_const_eval(arg) if isinstance(arg, (ast.Constant, ast.JoinedStr, ast.UnaryOp, ast.BinOp)) else _expr_text(source_text, arg)) for arg in call.args[2:]],
                "line_start": stmt.lineno,
                "line_end": stmt.end_lineno,
            }
        )
    return rows


def _asset_lock_candidates(repo_root: Path) -> list[Path]:
    return [
        repo_root / "collaboration/APPROVED_REUSABLE_ASSET_LOCK.json",
        Path("/data1/qujh/work/github_exports/sram-layoutgen-collab_20260715_034308/collaboration/APPROVED_REUSABLE_ASSET_LOCK.json"),
    ]


def load_approved_asset_lock(repo_root: Path) -> dict[str, Any]:
    for candidate in _asset_lock_candidates(repo_root):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    raise RuntimeError("approved reusable asset lock not found")


def resolve_approved_pinv_asset(repo_root: Path, physical_cell: str) -> dict[str, Any]:
    asset_lock = load_approved_asset_lock(repo_root)
    asset = next((row for row in asset_lock["assets"] if row["physical_cell"] == physical_cell), None)
    if asset is None:
        raise RuntimeError(f"approved asset missing for {physical_cell}")
    gds_path = (repo_root / asset["relative_path"]).resolve()
    pin_map_path = gds_path.parent / f"{physical_cell}_pin_map.json"
    if not gds_path.exists():
        raise RuntimeError(f"approved asset gds missing for {physical_cell}: {gds_path}")
    if not pin_map_path.exists():
        raise RuntimeError(f"approved asset pin map missing for {physical_cell}: {pin_map_path}")
    actual_sha = hashlib.sha256(gds_path.read_bytes()).hexdigest()
    if actual_sha != asset["sha256"]:
        raise RuntimeError(f"approved asset sha mismatch for {physical_cell}: {actual_sha} != {asset['sha256']}")
    return {
        **asset,
        "gds_path": str(gds_path),
        "pin_map_path": str(pin_map_path),
        "actual_sha256": actual_sha,
    }


def write_asset_lock_csv(repo_root: Path) -> None:
    asset_lock = load_approved_asset_lock(repo_root)
    csv_path = repo_root / "collaboration/APPROVED_REUSABLE_ASSET_LOCK.csv"
    fieldnames = list(asset_lock["assets"][0].keys())
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asset_lock["assets"])


def build_inverter_chain_source_lock(openyield_root: Path, repo_root: Path, module_name: str) -> dict[str, Any]:
    spec = MODULE_SPECS[module_name]
    openyield_root = openyield_root.resolve()
    source_bytes = _git_show_bytes(openyield_root, EXPECTED_OPENYIELD_COMMIT, TIME_GENERATE_PATH)
    source_text = source_bytes.decode("utf-8")
    source_blob = _git_blob_sha(openyield_root, EXPECTED_OPENYIELD_COMMIT, TIME_GENERATE_PATH)
    if source_blob != EXPECTED_TIME_GENERATE_BLOB:
        raise RuntimeError(f"unexpected time_generate.py blob {source_blob}")
    module = ast.parse(source_text, filename=TIME_GENERATE_PATH)
    cls = _find_class(module, spec["class_name"])
    instance_rows = _extract_instance_rows(source_text, cls)
    ctor_defaults = _extract_ctor_defaults(source_text, cls)
    approved_assets = [resolve_approved_pinv_asset(repo_root, cell_name) for cell_name in spec["child_variants"]]
    return {
        "authority_repository": str(openyield_root),
        "authority_commit": EXPECTED_OPENYIELD_COMMIT,
        "source_relative_path": TIME_GENERATE_PATH,
        "git_blob_sha": source_blob,
        "source_snapshot_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "class_name": spec["class_name"],
        "source_line_range": {"start": cls.lineno, "end": cls.end_lineno},
        "formal_constructor_parameters": ctor_defaults,
        "top_pin_names": spec["top_pin_order"],
        "top_pin_order": spec["top_pin_order"],
        "internal_nets": spec["internal_nets"],
        "output_polarity": spec["output_polarity"],
        "child_contract": spec["logical_children"],
        "approved_assets": approved_assets,
        "instance_rows": instance_rows,
        "topology_digest": hashlib.sha256(
            json.dumps(
                {
                    "pins": spec["top_pin_order"],
                    "internal": spec["internal_nets"],
                    "instances": instance_rows,
                    "children": spec["logical_children"],
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:16],
    }
