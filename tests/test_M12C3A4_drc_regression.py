from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import run_cell_drc


def _sanitized_rows() -> list[tuple[str, Path]]:
    root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    rows = []
    for cell_dir in sorted(root.iterdir()):
        if cell_dir.is_dir():
            rows.append((cell_dir.name, cell_dir / f"{cell_dir.name}.gds"))
    return rows


def main() -> int:
    drc_deck = REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc"
    total_markers = 0
    pass_count = 0
    with tempfile.TemporaryDirectory(prefix="m12c3a4_drc_") as tempdir:
        out_dir = Path(tempdir)
        for cell_name, gds_path in _sanitized_rows():
            report = run_cell_drc(Path("/usr/bin/klayout"), drc_deck, gds_path, cell_name, out_dir)
            assert report["drc_run"] is True
            assert report["drc_parse_passed"] is True
            assert report["marker_count"] == 0
            assert report["drc_passed"] is True
            total_markers += int(report["marker_count"])
            pass_count += 1
    assert pass_count == 10
    assert total_markers == 0
    print("M12C3A4_drc_regression_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
