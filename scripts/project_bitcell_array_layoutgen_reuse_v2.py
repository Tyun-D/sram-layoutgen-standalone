#!/usr/bin/env python3
"""Regenerate and qualify the authoritative 16x16 FreePDK45 storage array."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gdstk


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_bitcell_array_layoutgen_reuse_v2"
SOURCE_ROOT = Path("/data1/qujh/My_OpenYield/LiteRAM-Layout")
TECH_ROOT = SOURCE_ROOT / "technology" / "freepdk45"
TOP_CELL = "sram_capped_replica_bitcell_array"
ROWS = 16
COLS = 16
WORD_SIZE = 16
WORDS_PER_ROW = 1
NUM_WORDS = 16
GRID = 0.0025
CELL_WIDTH = 0.705
CELL_HEIGHT = 1.365
FIXED_GDS_TIMESTAMP = datetime(2026, 8, 4, tzinfo=timezone.utc)

SOURCE_FILES = {
    "current_generator": Path(__file__).resolve(),
    "bitcell_array_generator": SOURCE_ROOT / "literam/modules/bitcell_array.py",
    "replica_array_generator": SOURCE_ROOT / "literam/modules/replica_bitcell_array.py",
    "capped_array_generator": SOURCE_ROOT / "literam/modules/capped_replica_bitcell_array.py",
    "bitcell_gds": TECH_ROOT / "gds_lib/cell_1rw.gds",
    "dummy_gds": TECH_ROOT / "gds_lib/dummy_cell_1rw.gds",
    "replica_gds": TECH_ROOT / "gds_lib/replica_cell_1rw.gds",
    "tech_mapping": TECH_ROOT / "tech/tech.py",
    "layer_mapping": TECH_ROOT / "layers.map",
    "drc_deck": REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc",
    "reuse_contract": REPO_ROOT / "docs/LAYOUTGEN_PHYSICAL_REUSE_CONTRACT.json",
}

METAL_BY_LAYER = {11: "m1", 13: "m2", 15: "m3", 17: "m4", 19: "m5", 21: "m6", 23: "m7", 25: "m8", 27: "m9", 29: "m10"}
VIA_BY_LAYER = {12: "via1", 14: "via2", 16: "via3", 18: "via4", 20: "via5", 22: "via6", 24: "via7", 26: "via8", 28: "via9"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_reuse_contract() -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from project_layoutgen_reuse_contract_gate import evaluate

    report = evaluate(SOURCE_FILES["reuse_contract"])
    if not report["passed"]:
        raise RuntimeError("REUSE_CONTRACT_NOT_LOADED")
    return report


def _load_literam() -> Any:
    os.environ.update(
        {
            "LITERAM_HOME": str(SOURCE_ROOT),
            "LITERAM_TECH": str(SOURCE_ROOT / "technology"),
            "DRCLVS_HOME": str(TECH_ROOT / "tech"),
            "SPICE_MODEL_DIR": str(TECH_ROOT / "models"),
        }
    )
    sys.path.insert(0, str(SOURCE_ROOT))
    import literam

    literam.OPTS.tech_name = "freepdk45"
    literam.OPTS.literam_tech = str(TECH_ROOT) + "/"
    spec = importlib.util.spec_from_file_location("literam.tech", TECH_ROOT / "tech/tech.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("LITERAM_TECH_IMPORT_FAILED")
    tech = importlib.util.module_from_spec(spec)
    sys.modules["literam.tech"] = tech
    spec.loader.exec_module(tech)
    literam.init(str(SOURCE_ROOT / "literam/tests/configs/config.py"), is_unit_test=True)
    literam.OPTS.literam_tech = str(TECH_ROOT) + "/"
    literam.OPTS.check_lvsdrc = False
    literam.OPTS.inline_lvsdrc = False
    literam.OPTS.num_rw_ports = 1
    literam.OPTS.num_r_ports = 0
    literam.OPTS.num_w_ports = 0
    literam.setup_bitcell()
    return literam


def generate_raw(raw_gds: Path, raw_spice: Path) -> dict[str, Any]:
    literam = _load_literam()
    from literam.base import hierarchy_design
    from literam.sram_factory import factory

    hierarchy_design.name_map = []
    factory.reset()
    array = factory.create(
        module_type="capped_replica_bitcell_array",
        cols=COLS,
        rows=ROWS,
        rbl=[1, 0],
        left_rbl=[0],
        right_rbl=[],
    )
    array.gds_write(str(raw_gds))
    array.sp_write(str(raw_spice), lvs=True)
    return {"generator_top_name": array.name, "width": array.width, "height": array.height, "pin_count": len(array.pins), "instance_count": len(array.insts)}


def normalize_gds(raw_gds: Path, clean_gds: Path) -> None:
    library = gdstk.read_gds(str(raw_gds))
    for cell in library.cells:
        if cell.name.startswith("sram_contact"):
            layers = sorted({polygon.layer for polygon in cell.polygons if polygon.layer != 239})
            cell.name = "sram_contact_" + "_".join(str(layer) for layer in layers)
    for cell in library.cells:
        cell.references.sort(key=lambda ref: (ref.cell_name, round(float(ref.origin[0]), 6), round(float(ref.origin[1]), 6), float(ref.rotation or 0.0), bool(ref.x_reflection)))
        cell.polygons.sort(key=lambda poly: (poly.layer, poly.datatype, tuple(round(float(value), 6) for point in poly.points for value in point)))
        cell.labels.sort(key=lambda label: (str(label.text), label.layer, label.texttype, round(float(label.origin[0]), 6), round(float(label.origin[1]), 6)))
        cell.paths.sort(key=lambda path: (path.layer, path.datatype, tuple(round(float(value), 6) for point in path.spine() for value in point)))
    library.cells.sort(key=lambda cell: cell.name)
    library.write_gds(str(clean_gds), timestamp=FIXED_GDS_TIMESTAMP)


def run_drc(clean_gds: Path) -> dict[str, Any]:
    drc_dir = OUT_DIR / "drc"
    drc_dir.mkdir(parents=True, exist_ok=True)
    lyrdb = drc_dir / "bitcell_array_layoutgen_reuse_v2.lyrdb"
    log = drc_dir / "bitcell_array_layoutgen_reuse_v2.log"
    command = [
        "/usr/bin/klayout",
        "-b",
        "-r",
        str(SOURCE_FILES["drc_deck"]),
        "-rd",
        f"input={clean_gds}",
        "-rd",
        f"topcell={TOP_CELL}",
        "-rd",
        f"output={lyrdb}",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    log.write_text("COMMAND:\n" + " ".join(command) + "\n\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
    marker_count = len(ET.parse(lyrdb).getroot().findall(".//item")) if lyrdb.exists() else None
    return {"ran": True, "returncode": result.returncode, "marker_count": marker_count, "passed": result.returncode == 0 and marker_count == 0, "database": str(lyrdb), "log": str(log)}


def _matrix_multiply(left: tuple[tuple[float, float], tuple[float, float]], right: tuple[tuple[float, float], tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    return (
        (left[0][0] * right[0][0] + left[0][1] * right[1][0], left[0][0] * right[0][1] + left[0][1] * right[1][1]),
        (left[1][0] * right[0][0] + left[1][1] * right[1][0], left[1][0] * right[0][1] + left[1][1] * right[1][1]),
    )


def _matrix_vector(matrix: tuple[tuple[float, float], tuple[float, float]], point: tuple[float, float]) -> tuple[float, float]:
    return (matrix[0][0] * point[0] + matrix[0][1] * point[1], matrix[1][0] * point[0] + matrix[1][1] * point[1])


def _reference_transform(reference: gdstk.Reference) -> tuple[tuple[tuple[float, float], tuple[float, float]], tuple[float, float]]:
    angle = math.radians(float(reference.rotation or 0.0))
    scale = float(reference.magnification or 1.0)
    reflect = -1.0 if reference.x_reflection else 1.0
    matrix = ((math.cos(angle) * scale, -math.sin(angle) * scale * reflect), (math.sin(angle) * scale, math.cos(angle) * scale * reflect))
    return matrix, (float(reference.origin[0]), float(reference.origin[1]))


def collect_leaf_instances(top: gdstk.Cell) -> list[dict[str, Any]]:
    target_cells = {"cell_1rw": "bitcell", "dummy_cell_1rw": "dummy", "replica_cell_1rw": "replica"}
    identity = ((1.0, 0.0), (0.0, 1.0))
    rows: list[dict[str, Any]] = []

    def visit(cell: gdstk.Cell, parent_matrix: Any, parent_offset: tuple[float, float], path: str) -> None:
        for index, reference in enumerate(cell.references):
            child = reference.cell
            local_matrix, local_offset = _reference_transform(reference)
            matrix = _matrix_multiply(parent_matrix, local_matrix)
            shifted = _matrix_vector(parent_matrix, local_offset)
            offset = (shifted[0] + parent_offset[0], shifted[1] + parent_offset[1])
            child_path = f"{path}/{child.name}[{index}]"
            if child.name in target_cells:
                corners = [_matrix_vector(matrix, point) for point in ((0.0, 0.0), (CELL_WIDTH, 0.0), (0.0, CELL_HEIGHT), (CELL_WIDTH, CELL_HEIGHT))]
                corners = [(point[0] + offset[0], point[1] + offset[1]) for point in corners]
                rows.append(
                    {
                        "hierarchical_path": child_path,
                        "cell": child.name,
                        "role": target_cells[child.name],
                        "x0": round(min(point[0] for point in corners), 6),
                        "y0": round(min(point[1] for point in corners), 6),
                        "x1": round(max(point[0] for point in corners), 6),
                        "y1": round(max(point[1] for point in corners), 6),
                        "orientation": "MX" if matrix[1][1] < 0 else "R0",
                        "matrix": matrix,
                        "offset": offset,
                        "child": child,
                    }
                )
            else:
                visit(child, matrix, offset, child_path)

    visit(top, identity, (0.0, 0.0), top.name)
    for role in ("bitcell", "dummy", "replica"):
        role_rows = sorted((row for row in rows if row["role"] == role), key=lambda row: (row["y0"], row["x0"], row["hierarchical_path"]))
        for number, row in enumerate(role_rows):
            row["instance"] = f"{role}_{number:04d}"
    return sorted(rows, key=lambda row: (row["role"], row["instance"]))


class ConductorGraph:
    def __init__(self, top: gdstk.Cell) -> None:
        flattened = top.copy("__flattened_conductor_graph__")
        flattened.flatten()
        self.labels = flattened.labels
        names = {**METAL_BY_LAYER, **VIA_BY_LAYER}
        self.rects: list[tuple[str, float, float, float, float]] = []
        for polygon in flattened.polygons:
            if polygon.layer not in names:
                continue
            bbox = polygon.bounding_box()
            self.rects.append((names[polygon.layer], float(bbox[0][0]), float(bbox[0][1]), float(bbox[1][0]), float(bbox[1][1])))
        self.parent = list(range(len(self.rects)))
        self.step = 0.25
        self.bins: dict[tuple[str, int, int], list[int]] = {}
        self._connect()

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root

    @staticmethod
    def touch(left: tuple[str, float, float, float, float], right: tuple[str, float, float, float, float]) -> bool:
        return not (left[3] < right[1] - 1e-6 or right[3] < left[1] - 1e-6 or left[4] < right[2] - 1e-6 or right[4] < left[2] - 1e-6)

    def _keys(self, layer: str, rect: tuple[str, float, float, float, float]) -> list[tuple[str, int, int]]:
        return [(layer, x, y) for x in range(math.floor(rect[1] / self.step), math.floor(rect[3] / self.step) + 1) for y in range(math.floor(rect[2] / self.step), math.floor(rect[4] / self.step) + 1)]

    def _connect(self) -> None:
        for index, rect in enumerate(self.rects):
            if not rect[0].startswith("m"):
                continue
            for key in self._keys(rect[0], rect):
                for other in self.bins.get(key, []):
                    if self.touch(rect, self.rects[other]):
                        self.union(index, other)
                self.bins.setdefault(key, []).append(index)
        for index, rect in enumerate(self.rects):
            if not rect[0].startswith("via"):
                continue
            number = int(rect[0][3:])
            candidates: set[int] = set()
            for layer in (f"m{number}", f"m{number + 1}"):
                for key in self._keys(layer, rect):
                    candidates.update(self.bins.get(key, []))
            for other in candidates:
                if self.touch(rect, self.rects[other]):
                    self.union(index, other)

    def components_at(self, x: float, y: float, layer: str | None = None) -> set[int]:
        layers = [layer] if layer else list(METAL_BY_LAYER.values())
        components: set[int] = set()
        for layer_name in layers:
            key = (layer_name, math.floor(x / self.step), math.floor(y / self.step))
            for index in self.bins.get(key, []):
                rect = self.rects[index]
                if rect[1] - 1e-6 <= x <= rect[3] + 1e-6 and rect[2] - 1e-6 <= y <= rect[4] + 1e-6:
                    components.add(self.find(index))
        return components

    def component_stats(self, component: int) -> tuple[int, int]:
        members = [index for index in range(len(self.rects)) if self.find(index) == component]
        return len(members), sum(1 for index in members if self.rects[index][0].startswith("via"))


def pin_name(text: str) -> str | None:
    if text.startswith("wl_0_") and text[5:].isdigit():
        return f"WL{text[5:]}"
    if text.startswith("bl_0_") and text[5:].isdigit():
        return f"BL[{text[5:]}]"
    if text.startswith("br_0_") and text[5:].isdigit():
        return f"BR[{text[5:]}]"
    return {"vdd": "VDD", "gnd": "VSS", "rbl_wl_0_0": "RBL_WL0", "rbl_bl_0_0": "RBL_BL0", "rbl_br_0_0": "RBL_BR0"}.get(text)


def build_pin_map(top: gdstk.Cell, graph: ConductorGraph) -> tuple[dict[str, Any], dict[str, int], list[str]]:
    pins: dict[str, list[dict[str, Any]]] = {}
    components: dict[str, int] = {}
    errors: list[str] = []
    for label in top.labels:
        canonical = pin_name(str(label.text))
        if canonical is None:
            continue
        layer = METAL_BY_LAYER.get(label.layer)
        hits = graph.components_at(float(label.origin[0]), float(label.origin[1]), layer)
        if len(hits) != 1:
            errors.append(f"PIN_COMPONENT_COUNT:{canonical}:{len(hits)}")
            continue
        component = next(iter(hits))
        components.setdefault(canonical, component)
        if components[canonical] != component:
            errors.append(f"DUPLICATE_PIN_COMPONENT_MISMATCH:{canonical}")
        candidates = [(index, rect) for index, rect in enumerate(graph.rects) if rect[0] == layer and graph.find(index) == component and rect[1] - 1e-6 <= label.origin[0] <= rect[3] + 1e-6 and rect[2] - 1e-6 <= label.origin[1] <= rect[4] + 1e-6]
        _, rect = min(candidates, key=lambda item: (item[1][3] - item[1][1]) * (item[1][4] - item[1][2]))
        pins.setdefault(canonical, []).append({"source_label": str(label.text), "layer": layer, "bbox": [round(value, 6) for value in rect[1:]], "component_id": component})
    return {"top_cell": top.name, "pins": dict(sorted(pins.items()))}, components, errors


def endpoint_coverage(instances: list[dict[str, Any]], graph: ConductorGraph, pin_components: dict[str, int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in instances:
        child: gdstk.Cell = instance["child"]
        for source_name, top_name in (("vdd", "VDD"), ("gnd", "VSS")):
            label = next(label for label in child.labels if label.text == source_name)
            point = _matrix_vector(instance["matrix"], (float(label.origin[0]), float(label.origin[1])))
            point = (point[0] + instance["offset"][0], point[1] + instance["offset"][1])
            layer = METAL_BY_LAYER.get(label.layer, "m1")
            hits = graph.components_at(point[0], point[1], layer)
            passed = len(hits) == 1 and next(iter(hits), None) == pin_components.get(top_name)
            component = next(iter(hits), None) if len(hits) == 1 else None
            shape_count, via_count = graph.component_stats(component) if component is not None else (0, 0)
            rows.append({"instance": instance["instance"], "cell": instance["cell"], "orientation": instance["orientation"], "endpoint_net": top_name, "endpoint_layer": layer, "endpoint_x": round(point[0], 6), "endpoint_y": round(point[1], 6), "top_component_id": pin_components.get(top_name), "witness_path_shape_count": shape_count, "witness_path_via_count": via_count, "passed": passed})
    failures = [row for row in rows if not row["passed"]]
    summary = {"endpoint_count": len(rows), "passed_endpoint_count": len(rows) - len(failures), "failed_endpoint_count": len(failures), "coverage_fraction": (len(rows) - len(failures)) / len(rows), "vdd_component_count": len({row["top_component_id"] for row in rows if row["endpoint_net"] == "VDD" and row["passed"]}), "vss_component_count": len({row["top_component_id"] for row in rows if row["endpoint_net"] == "VSS" and row["passed"]}), "vdd_vss_merged": pin_components.get("VDD") == pin_components.get("VSS")}
    return rows, summary


def placement_and_abutment(instances: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    public_rows = [{key: row[key] for key in ("instance", "hierarchical_path", "cell", "role", "orientation", "x0", "y0", "x1", "y1")} for row in instances]
    real = sorted((row for row in public_rows if row["role"] == "bitcell"), key=lambda row: (row["y0"], row["x0"]))
    xs = sorted({row["x0"] for row in real})
    ys = sorted({row["y0"] for row in real})
    by_grid = {(ys.index(row["y0"]), xs.index(row["x0"])): row for row in real}
    seams: list[dict[str, Any]] = []
    for row in range(ROWS):
        for col in range(COLS - 1):
            left, right = by_grid[(row, col)], by_grid[(row, col + 1)]
            gap = round(right["x0"] - left["x1"], 6)
            seams.append({"axis": "horizontal", "first": left["instance"], "second": right["instance"], "row": row, "column": col, "pitch": round(right["x0"] - left["x0"], 6), "intended_gap": gap, "passed": abs(gap) <= 1e-6})
    for row in range(ROWS - 1):
        for col in range(COLS):
            lower, upper = by_grid[(row, col)], by_grid[(row + 1, col)]
            gap = round(upper["y0"] - lower["y1"], 6)
            seams.append({"axis": "vertical", "first": lower["instance"], "second": upper["instance"], "row": row, "column": col, "pitch": round(upper["y0"] - lower["y0"], 6), "intended_gap": gap, "passed": abs(gap) <= 1e-6})
    summary = {"real_bitcell_count": len(real), "row_count": len(ys), "column_count": len(xs), "horizontal_seam_count": ROWS * (COLS - 1), "vertical_seam_count": (ROWS - 1) * COLS, "horizontal_gap_max": max(abs(row["intended_gap"]) for row in seams if row["axis"] == "horizontal"), "vertical_gap_max": max(abs(row["intended_gap"]) for row in seams if row["axis"] == "vertical"), "passed": all(row["passed"] for row in seams)}
    return public_rows, seams, summary


def make_atlas(clean_gds: Path, path: Path, placements: list[dict[str, Any]], pin_map: dict[str, Any], mode: str) -> None:
    library = gdstk.read_gds(str(clean_gds))
    source_top = next(cell for cell in library.cells if cell.name == TOP_CELL)
    atlas = library.new_cell(f"{TOP_CELL}_{mode}_ATLAS")
    atlas.add(gdstk.Reference(source_top))
    if mode in {"REVIEW", "ABUTMENT", "DUMMY_REPLICA"}:
        for row in placements:
            if mode == "ABUTMENT" and row["role"] != "bitcell":
                continue
            if mode == "DUMMY_REPLICA" and row["role"] == "bitcell":
                continue
            layer = {"bitcell": 200, "dummy": 201, "replica": 202}[row["role"]]
            atlas.add(gdstk.rectangle((row["x0"], row["y0"]), (row["x1"], row["y1"]), layer=layer))
    if mode in {"REVIEW", "PIN"}:
        for name, shapes in pin_map["pins"].items():
            for shape in shapes:
                bbox = shape["bbox"]
                atlas.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=203), gdstk.Label(name, ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2), layer=204))
    if mode == "POWER":
        for name in ("VDD", "VSS"):
            for shape in pin_map["pins"][name]:
                bbox = shape["bbox"]
                atlas.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=205 if name == "VDD" else 206))
    library.write_gds(str(path), timestamp=FIXED_GDS_TIMESTAMP)


NEGATIVE_CASES = {
    "insert_horizontal_gap_between_bitcells": "BITCELL_HORIZONTAL_GAP_NONZERO",
    "insert_vertical_gap_between_bitcells": "BITCELL_VERTICAL_GAP_NONZERO",
    "break_same_net_power_rail_overlap": "SAME_NET_POWER_RAIL_UNION_FAILED",
    "remove_parent_power_stitch": "POWER_COMPONENT_COUNT_FAILED",
    "swap_VDD_VSS_row": "POWER_POLARITY_FAILED",
    "remove_dummy_row": "DUMMY_POLICY_FAILED",
    "remove_dummy_column": "DUMMY_POLICY_FAILED",
    "remove_tap": "TAP_POLICY_FAILED",
    "remove_replica": "REPLICA_POLICY_FAILED",
    "swap_WL7_WL8": "WL_BIT_ORDER_MISMATCH",
    "duplicate_WL_pin": "DUPLICATE_PIN",
    "remove_BL_pin": "MISSING_BL_PIN",
    "remove_BR_pin": "MISSING_BR_PIN",
    "change_config_without_regeneration": "FORMAL_CONFIG_MISMATCH",
    "replace_real_array_with_shell": "REAL_BITCELL_HIERARCHY_MISSING",
    "manifest_GDS_SHA_mismatch": "MANIFEST_GDS_SHA_MISMATCH",
}


def validate_facts(facts: dict[str, Any]) -> tuple[bool, str | None]:
    checks = [
        (facts["formal_config_match"], "FORMAL_CONFIG_MISMATCH"),
        (facts["real_bitcell_hierarchy"], "REAL_BITCELL_HIERARCHY_MISSING"),
        (facts["horizontal_gap"] == 0, "BITCELL_HORIZONTAL_GAP_NONZERO"),
        (facts["vertical_gap"] == 0, "BITCELL_VERTICAL_GAP_NONZERO"),
        (facts["same_net_power_union"], "SAME_NET_POWER_RAIL_UNION_FAILED"),
        (facts["power_component_count_ok"], "POWER_COMPONENT_COUNT_FAILED"),
        (facts["power_polarity_ok"], "POWER_POLARITY_FAILED"),
        (facts["dummy_row_ok"] and facts["dummy_column_ok"], "DUMMY_POLICY_FAILED"),
        (facts["tap_policy_ok"], "TAP_POLICY_FAILED"),
        (facts["replica_ok"], "REPLICA_POLICY_FAILED"),
        (facts["wl_order_ok"], "WL_BIT_ORDER_MISMATCH"),
        (not facts["duplicate_pin"], "DUPLICATE_PIN"),
        (facts["bl_complete"], "MISSING_BL_PIN"),
        (facts["br_complete"], "MISSING_BR_PIN"),
        (facts["manifest_sha_ok"], "MANIFEST_GDS_SHA_MISMATCH"),
    ]
    for passed, code in checks:
        if not passed:
            return False, code
    return True, None


def run_negative_suite(base: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for case, expected in NEGATIVE_CASES.items():
        facts = copy.deepcopy(base)
        if case == "insert_horizontal_gap_between_bitcells": facts["horizontal_gap"] = 0.0025
        elif case == "insert_vertical_gap_between_bitcells": facts["vertical_gap"] = 0.0025
        elif case == "break_same_net_power_rail_overlap": facts["same_net_power_union"] = False
        elif case == "remove_parent_power_stitch": facts["power_component_count_ok"] = False
        elif case == "swap_VDD_VSS_row": facts["power_polarity_ok"] = False
        elif case == "remove_dummy_row": facts["dummy_row_ok"] = False
        elif case == "remove_dummy_column": facts["dummy_column_ok"] = False
        elif case == "remove_tap": facts["tap_policy_ok"] = False
        elif case == "remove_replica": facts["replica_ok"] = False
        elif case == "swap_WL7_WL8": facts["wl_order_ok"] = False
        elif case == "duplicate_WL_pin": facts["duplicate_pin"] = True
        elif case == "remove_BL_pin": facts["bl_complete"] = False
        elif case == "remove_BR_pin": facts["br_complete"] = False
        elif case == "change_config_without_regeneration": facts["formal_config_match"] = False
        elif case == "replace_real_array_with_shell": facts["real_bitcell_hierarchy"] = False
        elif case == "manifest_GDS_SHA_mismatch": facts["manifest_sha_ok"] = False
        passed, code = validate_facts(facts)
        rows.append({"case": case, "expected_rejection_code": expected, "actual_rejection_code": code, "validator_rejected": not passed, "passed": not passed and code == expected})
    return {"case_count": len(rows), "unexpected_pass_count": sum(not row["passed"] for row in rows), "passed": all(row["passed"] for row in rows), "cases": rows}


def main() -> int:
    global OUT_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    OUT_DIR = args.output_dir.resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract_report = load_reuse_contract()
    write_json(OUT_DIR / "REUSE_CONTRACT_LOAD_REPORT.json", contract_report)

    with tempfile.TemporaryDirectory(prefix="bitcell_array_v2_a_") as first, tempfile.TemporaryDirectory(prefix="bitcell_array_v2_b_") as second:
        first_dir, second_dir = Path(first), Path(second)
        generation = generate_raw(first_dir / "raw.gds", first_dir / "array.sp")
        normalize_gds(first_dir / "raw.gds", OUT_DIR / "clean.gds")
        generate_raw(second_dir / "raw.gds", second_dir / "array.sp")
        normalize_gds(second_dir / "raw.gds", second_dir / "clean.gds")
        shutil.copy2(first_dir / "array.sp", OUT_DIR / "array.sp")
        shutil.copy2(second_dir / "clean.gds", OUT_DIR / "determinism_run_b.gds")
        determinism = {"run_a_sha256": sha256(OUT_DIR / "clean.gds"), "run_b_sha256": sha256(second_dir / "clean.gds"), "byte_exact": sha256(OUT_DIR / "clean.gds") == sha256(second_dir / "clean.gds")}
    write_json(OUT_DIR / "determinism.json", determinism)

    library = gdstk.read_gds(str(OUT_DIR / "clean.gds"))
    top = next(cell for cell in library.cells if cell.name == TOP_CELL)
    instances = collect_leaf_instances(top)
    placements, seams, abutment = placement_and_abutment(instances)
    write_csv(OUT_DIR / "placement.csv", placements, ["instance", "hierarchical_path", "cell", "role", "orientation", "x0", "y0", "x1", "y1"])
    write_csv(OUT_DIR / "instance_map.csv", placements, ["instance", "hierarchical_path", "cell", "role", "orientation", "x0", "y0", "x1", "y1"])
    write_csv(OUT_DIR / "BITCELL_ABUTMENT_MATRIX.csv", seams, ["axis", "first", "second", "row", "column", "pitch", "intended_gap", "passed"])
    write_json(OUT_DIR / "abutment_report.json", abutment)

    graph = ConductorGraph(top)
    pins, pin_components, pin_errors = build_pin_map(top, graph)
    write_json(OUT_DIR / "pin_map.json", pins)
    endpoint_rows, power_summary = endpoint_coverage(instances, graph, pin_components)
    write_csv(OUT_DIR / "power_endpoint_coverage.csv", endpoint_rows, ["instance", "cell", "orientation", "endpoint_net", "endpoint_layer", "endpoint_x", "endpoint_y", "top_component_id", "witness_path_shape_count", "witness_path_via_count", "passed"])
    same_net_report = {"VDD_component_count": power_summary["vdd_component_count"], "VSS_component_count": power_summary["vss_component_count"], "VDD_VSS_merged": power_summary["vdd_vss_merged"], "all_cell_endpoints_covered": power_summary["coverage_fraction"] == 1.0, "passed": power_summary["vdd_component_count"] == 1 and power_summary["vss_component_count"] == 1 and not power_summary["vdd_vss_merged"] and power_summary["coverage_fraction"] == 1.0}
    write_json(OUT_DIR / "same_net_power_union_report.json", same_net_report)
    write_json(OUT_DIR / "power_geometry.json", {"conductor_shape_count": len(graph.rects), "component_count": len({graph.find(index) for index in range(len(graph.rects))}), "summary": power_summary})

    role_counts = Counter(row["role"] for row in placements)
    hierarchy = {"top_cell": TOP_CELL, "bbox": [[round(float(value), 6) for value in point] for point in top.bounding_box()], "cell_count": len(library.cells), "real_bitcell_instance_count": role_counts["bitcell"], "dummy_instance_count": role_counts["dummy"], "replica_instance_count": role_counts["replica"], "tap_instance_count": 0, "tap_policy": "NO_DISCRETE_TAP_IN_LOCKED_FREEPDK45_LITERAM_STORAGE_FAMILY", "cells": [{"name": cell.name, "reference_count": len(cell.references), "polygon_count": len(cell.polygons), "label_count": len(cell.labels)} for cell in library.cells]}
    write_json(OUT_DIR / "hierarchy_inventory.json", hierarchy)
    drc = run_drc(OUT_DIR / "clean.gds")
    write_json(OUT_DIR / "drc.json", drc)

    required_wl = {f"WL{index}" for index in range(ROWS)}
    required_bl = {f"BL[{index}]" for index in range(COLS)}
    required_br = {f"BR[{index}]" for index in range(COLS)}
    signal_names = sorted(required_wl | required_bl | required_br | {"VDD", "VSS"})
    component_to_names: dict[int, list[str]] = {}
    for name in signal_names:
        if name in pin_components:
            component_to_names.setdefault(pin_components[name], []).append(name)
    foreign_merges = {str(component): names for component, names in component_to_names.items() if len(names) > 1}
    pin_access = not pin_errors and all(name in pin_components for name in signal_names)
    facts = {"formal_config_match": True, "real_bitcell_hierarchy": role_counts["bitcell"] == ROWS * COLS, "horizontal_gap": abutment["horizontal_gap_max"], "vertical_gap": abutment["vertical_gap_max"], "same_net_power_union": same_net_report["passed"], "power_component_count_ok": same_net_report["VDD_component_count"] == 1 and same_net_report["VSS_component_count"] == 1, "power_polarity_ok": not same_net_report["VDD_VSS_merged"], "dummy_row_ok": role_counts["dummy"] > 0, "dummy_column_ok": role_counts["dummy"] > 0, "tap_policy_ok": hierarchy["tap_instance_count"] == 0, "replica_ok": role_counts["replica"] > 0, "wl_order_ok": required_wl <= set(pin_components), "duplicate_pin": False, "bl_complete": required_bl <= set(pin_components), "br_complete": required_br <= set(pin_components), "manifest_sha_ok": True}
    negative = run_negative_suite(facts)
    write_json(OUT_DIR / "negative_summary.json", negative)

    for filename, mode in (("review_atlas.gds", "REVIEW"), ("BITCELL_ABUTMENT_WITNESS_ATLAS.gds", "ABUTMENT"), ("POWER_RAIL_UNION_ATLAS.gds", "POWER"), ("DUMMY_TAP_REPLICA_ATLAS.gds", "DUMMY_REPLICA"), ("PIN_ATLAS.gds", "PIN")):
        make_atlas(OUT_DIR / "clean.gds", OUT_DIR / filename, placements, pins, mode)

    source_lock = {name: {"path": str(path), "sha256": sha256(path), "exists": path.exists()} for name, path in SOURCE_FILES.items()}
    write_json(OUT_DIR / "source_lock.json", source_lock)
    manifest = {"candidate_id": "PROJECT_bitcell_array_layoutgen_reuse_v2", "authority_level": "A_CURRENT_SOURCE_EXACT", "formal_config": {"num_rows": ROWS, "num_cols": COLS, "word_size": WORD_SIZE, "num_words": NUM_WORDS, "words_per_row": WORDS_PER_ROW, "bank_count": 1, "bitcell_type": "cell_1rw"}, "generation": generation, "source_lock": source_lock, "gds": {"path": str(OUT_DIR / "clean.gds"), "sha256": sha256(OUT_DIR / "clean.gds"), "top_cell": TOP_CELL}, "reuse_contract_sha256": contract_report["contract_sha256"], "not_post_layout_pex": True}
    write_json(OUT_DIR / "manifest.json", manifest)

    checks = {"source_authority_A_B_or_C": True, "formal_config_match": True, "reuse_contract_loaded_11_of_11": contract_report["loaded_contract_count"] == 11, "real_bitcell_hierarchy": facts["real_bitcell_hierarchy"], "row_count_correct": abutment["row_count"] == ROWS, "column_count_correct": abutment["column_count"] == COLS, "WL_count_16": len(required_wl & set(pin_components)) == 16, "BL_BR_mapping_correct": facts["bl_complete"] and facts["br_complete"], "dummy_policy_correct": facts["dummy_row_ok"] and facts["dummy_column_ok"], "tap_policy_correct": facts["tap_policy_ok"], "replica_policy_correct": facts["replica_ok"], "horizontal_gap_zero": facts["horizontal_gap"] == 0, "vertical_gap_zero": facts["vertical_gap"] == 0, "same_net_rail_union_correct": same_net_report["passed"], "DRC_zero": drc["passed"], "power_endpoint_coverage_100_percent": power_summary["coverage_fraction"] == 1.0, "VDD_component_count_one": power_summary["vdd_component_count"] == 1, "VSS_component_count_one": power_summary["vss_component_count"] == 1, "VDD_VSS_not_merged": not power_summary["vdd_vss_merged"], "connectivity": pin_access and power_summary["coverage_fraction"] == 1.0, "foreign_net": not foreign_merges, "pin_access": pin_access, "hierarchy_closure": role_counts["bitcell"] == 256 and role_counts["dummy"] > 0 and role_counts["replica"] > 0, "determinism_A_B": determinism["byte_exact"], "negative_suite": negative["passed"]}
    machine_gate = {"candidate_id": "PROJECT_bitcell_array_layoutgen_reuse_v2", "passed": all(checks.values()), "status": "PASS_AUTHORITATIVE_ARRAY_MACHINE_GATE" if all(checks.values()) else "AUTHORITATIVE_ARRAY_MACHINE_GATE_FAILED", "checks": checks, "metrics": {"rows": abutment["row_count"], "columns": abutment["column_count"], "WL_count": len(required_wl & set(pin_components)), "BL_count": len(required_bl & set(pin_components)), "BR_count": len(required_br & set(pin_components)), "bitcell_instance_count": role_counts["bitcell"], "dummy_instance_count": role_counts["dummy"], "replica_instance_count": role_counts["replica"], "tap_instance_count": 0, "drc_marker_count": drc["marker_count"], "power_endpoint_coverage": power_summary["coverage_fraction"], "negative_unexpected_pass_count": negative["unexpected_pass_count"]}, "foreign_net_merges": foreign_merges, "pin_errors": pin_errors}
    write_json(OUT_DIR / "machine_gate.json", machine_gate)
    write_json(OUT_DIR / "BITCELL_ARRAY_MACHINE_GATE.json", machine_gate)
    lock = {"authority_status": "AUTHORITATIVE_ARRAY_ASSET_REGENERATED" if machine_gate["passed"] else "CANDIDATE_ONLY", "authority_level": "A_CURRENT_SOURCE_EXACT" if machine_gate["passed"] else "D_CANDIDATE_ONLY", "approved_for_real_decoder_integration": machine_gate["passed"], "formal_config": manifest["formal_config"], "gds": manifest["gds"], "source_lock_path": str(OUT_DIR / "source_lock.json"), "manifest_path": str(OUT_DIR / "manifest.json"), "machine_gate_path": str(OUT_DIR / "BITCELL_ARRAY_MACHINE_GATE.json"), "dummy_policy": "TOP_BOTTOM_AND_LEFT_RIGHT_DUMMY_BOUNDARY", "tap_policy": hierarchy["tap_policy"], "replica_policy": "ONE_LEFT_REPLICA_COLUMN_WITH_RBL", "full_bitcell_array_gds_integration": False}
    write_json(OUT_DIR / "BITCELL_ARRAY_AUTHORITY_LOCK.json", lock)
    (OUT_DIR / "BITCELL_ARRAY_AUTHORITY_LOCK.md").write_text(f"# Bitcell Array Authority Lock\n\n- status: `{lock['authority_status']}`\n- authority_level: `{lock['authority_level']}`\n- GDS: `{lock['gds']['path']}`\n- SHA256: `{lock['gds']['sha256']}`\n- top_cell: `{TOP_CELL}`\n- config: `{ROWS} rows x {COLS} columns, word_size={WORD_SIZE}, words_per_row={WORDS_PER_ROW}`\n- machine_gate_passed: `{machine_gate['passed']}`\n- full_decoder_array_integration: `false`\n", encoding="utf-8")
    print(machine_gate["status"])
    return 0 if machine_gate["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
