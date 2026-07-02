from __future__ import annotations

import tempfile
from pathlib import Path
import sys

import gdstk

REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gds_hierarchy_export import (
    TopCellImportPlan,
    build_top_level_library,
    diagnose_gds_hierarchy,
)


def _write_gds(path: Path, cells: list[gdstk.Cell]) -> None:
    lib = gdstk.Library()
    for cell in cells:
        lib.add(cell)
    lib.write_gds(path)


def test_build_top_level_library_resolves_self_ref_with_external_source() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        module_gds = root / "sense_amp_module.gds"
        hardmacro_gds = root / "sense_amp_hardmacro.gds"

        leaf = gdstk.Cell("leaf")
        leaf.add(gdstk.rectangle((0, 0), (0.2, 0.2), layer=11, datatype=0))
        hard = gdstk.Cell("sense_amp")
        hard.add(gdstk.Reference(leaf, origin=(0.1, 0.0)))
        _write_gds(hardmacro_gds, [hard, leaf])

        broken_wrapper = gdstk.Cell("sense_amp")
        broken_wrapper.add(gdstk.Reference("sense_amp", origin=(0.0, 0.0)))
        _write_gds(module_gds, [broken_wrapper])

        lib, manifest = build_top_level_library(
            [
                TopCellImportPlan(
                    module_name="sense_amp",
                    module_gds_path=module_gds,
                    root_cell_name="sense_amp",
                    instance_name="sense_amp_u0",
                    origin_x=0.0,
                    origin_y=0.0,
                    orientation="R0",
                )
            ],
            [module_gds, hardmacro_gds],
        )

        out_gds = root / "top.gds"
        lib.write_gds(out_gds)
        diagnosis = diagnose_gds_hierarchy(out_gds, {"sense_amp": module_gds}, root)

        assert diagnosis["missing_referenced_cells"] == []
        assert diagnosis["self_references"] == []
        assert diagnosis["cycles"] == []
        assert manifest["self_reference_redirects"], "expected wrapper self-reference to be redirected"
        assert manifest["unresolved_references"] == []


def main() -> None:
    test_build_top_level_library_resolves_self_ref_with_external_source()
    print("OpenYield GDS hierarchy export tests passed.")


if __name__ == "__main__":
    main()
