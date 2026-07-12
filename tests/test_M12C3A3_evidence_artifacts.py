from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    out_root = REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config"
    cell_dir = out_root / "TRANSMISSION_GATE_NW250_PW500_L50"
    fingerprint = json.loads((cell_dir / "TRANSMISSION_GATE_NW250_PW500_L50_geometry_fingerprint.json").read_text())
    assert fingerprint["digest"]
    assert fingerprint["algorithm"]
    assert fingerprint["normalized_geometry_used"] is True
    assert fingerprint["layer_histogram"]
    assert fingerprint["bbox"]

    clean = out_root / "M12C3A3_transmission_gate_clean.gds"
    annotated = out_root / "M12C3A3_transmission_gate_annotated.gds"
    atlas = out_root / "M12C3A3_transmission_gate_review_atlas.gds"
    assert _sha256(clean) != _sha256(annotated)
    assert _sha256(clean) != _sha256(atlas)
    assert _sha256(annotated) != _sha256(atlas)

    report = json.loads((REPO_ROOT / "docs/M12C3A3_transmission_gate_adapter_repair_report.json").read_text())
    assert report["pinv_geometry_changed_by_repair"] is False
    for cell_name, baseline_digest in report["pinv_fingerprint_baseline"].items():
        gds_path = REPO_ROOT / f"outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/cells/{cell_name}/{cell_name}.gds"
        assert geometry_fingerprint(gds_path, cell_name)["digest"] == baseline_digest
    print("M12C3A3_evidence_artifacts_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
