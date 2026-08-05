from pathlib import Path

import gdstk

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity


def test_m1_to_m6_stack_forms_one_component(tmp_path: Path) -> None:
    library = gdstk.Library()
    top = library.new_cell("m6_stack")
    for layer, half in ((11, 0.0675), (12, 0.0325), (13, 0.0675), (14, 0.0325), (15, 0.07), (16, 0.035), (17, 0.07), (18, 0.07), (19, 0.07), (20, 0.07), (21, 0.07)):
        top.add(gdstk.rectangle((-half, -half), (half, half), layer=layer))
    top.add(gdstk.rectangle((-0.07, -0.07), (2.0, 0.07), layer=21))
    gds = tmp_path / "m6_stack.gds"
    library.write_gds(gds)

    graph = extract_physical_connectivity(gds, "m6_stack", metal_only=True)
    layers = graph["components"][0]["layers"]
    assert {"m1", "m2", "m3", "m4", "m5", "m6", "via1", "via2", "via3", "via4", "via5"} <= set(layers)
    assert len(graph["components"]) == 1


def test_parallel_m6_tracks_remain_isolated(tmp_path: Path) -> None:
    library = gdstk.Library()
    top = library.new_cell("m6_parallel")
    top.add(gdstk.rectangle((0.0, -0.07), (2.0, 0.07), layer=21))
    top.add(gdstk.rectangle((0.0, 0.93), (2.0, 1.07), layer=21))
    gds = tmp_path / "m6_parallel.gds"
    library.write_gds(gds)

    graph = extract_physical_connectivity(gds, "m6_parallel", metal_only=True)
    assert len(graph["components"]) == 2
