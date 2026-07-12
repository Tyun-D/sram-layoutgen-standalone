from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gds_label_sanitizer import load_pin_map, recursive_label_inventory, sanitize_gds_labels
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import (
    conductive_geometry_fingerprint,
    geometry_fingerprint,
    non_text_geometry_fingerprint,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_rows() -> list[tuple[str, Path, Path]]:
    pinv_root = REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/cells"
    tg_root = REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/TRANSMISSION_GATE_NW250_PW500_L50"
    rows = []
    for cell_dir in sorted(pinv_root.glob("PINV_*")):
        rows.append((cell_dir.name, cell_dir / f"{cell_dir.name}.gds", cell_dir / f"{cell_dir.name}_pin_map.json"))
    rows.append(
        (
            "TRANSMISSION_GATE_NW250_PW500_L50",
            tg_root / "TRANSMISSION_GATE_NW250_PW500_L50.gds",
            tg_root / "TRANSMISSION_GATE_NW250_PW500_L50_pin_map.json",
        )
    )
    return rows


def _graph_signature(graph: dict[str, object]) -> dict[str, object]:
    return {
        "layers_present": graph["layers_present"],
        "parent_active_to_segments": graph["parent_active_to_segments"],
        "active_segments": graph["active_segments"],
        "contact_links": graph["contact_links"],
        "components": graph["components"],
        "rectangles": graph["rectangles"],
    }


def main() -> int:
    reusable_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    for cell_name, original_gds, pin_map_path in _source_rows():
        sanitized_gds = reusable_root / cell_name / f"{cell_name}.gds"
        assert _sha256(original_gds) != _sha256(sanitized_gds)

        original_full = geometry_fingerprint(original_gds, cell_name)
        sanitized_full = geometry_fingerprint(sanitized_gds, cell_name)
        assert original_full["digest"] != sanitized_full["digest"]

        original_non_text = non_text_geometry_fingerprint(original_gds, cell_name)
        sanitized_non_text = non_text_geometry_fingerprint(sanitized_gds, cell_name)
        assert original_non_text == sanitized_non_text

        original_conductive = conductive_geometry_fingerprint(original_gds, cell_name)
        sanitized_conductive = conductive_geometry_fingerprint(sanitized_gds, cell_name)
        assert original_conductive == sanitized_conductive

        assert original_non_text["layer_histogram"]["239/0"] == sanitized_non_text["layer_histogram"]["239/0"]
        assert original_non_text["bbox"] == sanitized_non_text["bbox"]

        with tempfile.TemporaryDirectory(prefix=f"m12c3a4_geom_{cell_name}_") as tempdir:
            regenerated_gds = Path(tempdir) / f"{cell_name}.gds"
            sanitize_gds_labels(
                source_gds=original_gds,
                source_top_name=cell_name,
                pin_map=load_pin_map(pin_map_path),
                output_gds=regenerated_gds,
            )
            assert geometry_fingerprint(regenerated_gds, cell_name) == sanitized_full
            assert non_text_geometry_fingerprint(regenerated_gds, cell_name) == sanitized_non_text
            assert conductive_geometry_fingerprint(regenerated_gds, cell_name) == sanitized_conductive
            assert recursive_label_inventory(regenerated_gds, cell_name) == recursive_label_inventory(sanitized_gds, cell_name)
            assert _graph_signature(extract_physical_connectivity(regenerated_gds, cell_name)) == _graph_signature(
                extract_physical_connectivity(sanitized_gds, cell_name)
            )

    out_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config"
    clean = out_root / "M12C3A4_reusable_primitives_clean.gds"
    annotated = out_root / "M12C3A4_reusable_primitives_annotated.gds"
    atlas = out_root / "M12C3A4_label_cleanup_review_atlas.gds"
    assert _sha256(clean) != _sha256(annotated)
    assert _sha256(clean) != _sha256(atlas)
    assert _sha256(annotated) != _sha256(atlas)

    print("M12C3A4_geometry_preservation_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
