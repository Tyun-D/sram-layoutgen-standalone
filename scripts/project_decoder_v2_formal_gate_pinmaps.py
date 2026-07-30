from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
DOCS = REPO_ROOT / "docs"
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_v2_formal_gate_pinmaps" / "current_supported_config"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git_head() -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git rev-parse HEAD failed")
    return completed.stdout.strip()


def build_rect_index(rectangles: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for layer_name, items in rectangles.items():
        for item in items:
            index[str(item["rect_id"])] = {
                "layer_name": layer_name,
                "bbox": [round(float(v), 6) for v in item["bbox"]],
            }
    return index


def union_bbox(boxes: list[list[float]]) -> list[float]:
    return [
        round(min(box[0] for box in boxes), 6),
        round(min(box[1] for box in boxes), 6),
        round(max(box[2] for box in boxes), 6),
        round(max(box[3] for box in boxes), 6),
    ]


def extract_gate_pin_map(module_name: str) -> dict[str, Any]:
    base = PRIMARY_REPO_ROOT / "outputs" / "TeamB_remaining9_reference_demo" / "current_supported_config" / module_name
    graph = read_json(base / "connectivity_graph.json")
    top_report = read_json(base / "direct_top_label_report.json")
    rect_index = build_rect_index(graph["rectangles"])
    pin_map: dict[str, list[dict[str, Any]]] = {}
    evidence_rows = []
    for row in top_report["direct_top_label_rows"]:
        pin_name = str(row["text"])
        hit = next(item for item in graph["label_hits"] if str(item["text"]) == pin_name and [round(float(v), 6) for v in item["origin"]] == [round(float(v), 6) for v in row["origin"]])
        hit_boxes = [rect_index[shape_id]["bbox"] for shape_id in hit["shape_ids"] if shape_id in rect_index]
        if not hit_boxes:
            raise RuntimeError(f"no shape bbox found for {module_name}:{pin_name}")
        bbox = union_bbox(hit_boxes)
        layer_name = rect_index[hit["shape_ids"][0]]["layer_name"]
        if layer_name != "m1":
            raise RuntimeError(f"unexpected layer for {module_name}:{pin_name}: {layer_name}")
        pin_map[pin_name] = [
            {
                "layer": layer_name,
                "lx": bbox[0],
                "by": bbox[1],
                "rx": bbox[2],
                "uy": bbox[3],
            }
        ]
        evidence_rows.append(
            {
                "module": module_name,
                "pin_name": pin_name,
                "label_origin": row["origin"],
                "shape_ids": hit["shape_ids"],
                "bbox": bbox,
                "layer": layer_name,
            }
        )
    return {
        "module": module_name,
        "git_head": git_head(),
        "source_base": str(base.resolve()),
        "pin_map": pin_map,
        "evidence_rows": evidence_rows,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "scope": "project_decoder_v2_formal_gate_pinmaps",
        "git_head": git_head(),
        "modules": {},
    }
    for module_name in ("AND2", "AND3"):
        payload = extract_gate_pin_map(module_name)
        write_json(OUT_DIR / f"{module_name}_pin_map.json", payload["pin_map"])
        write_json(OUT_DIR / f"{module_name}_pinmap_evidence.json", payload)
        manifest["modules"][module_name] = {
            "pin_map_path": str((OUT_DIR / f"{module_name}_pin_map.json").resolve()),
            "evidence_path": str((OUT_DIR / f"{module_name}_pinmap_evidence.json").resolve()),
            "pin_names": sorted(payload["pin_map"]),
        }
    write_json(DOCS / "DECODER_V2_FORMAL_GATE_PINMAPS.json", manifest)


if __name__ == "__main__":
    main()
