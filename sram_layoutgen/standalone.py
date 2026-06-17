'''Standalone SRAM macro generator that uses only bundled PDK library files.'''

from __future__ import annotations

import json
import math
from html import escape
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path

from .gds_writer import GDSWriter
from .gds_util import inspect_gds_hierarchy, inspect_gds_layers, inspect_gds_text_records, measure_gds_bbox
from .geometry import CellArray, Instance, LayoutDB, Point, Rect, Shape
from .lef_writer import LEFWriter
from .netlist_writer import NetlistWriter
from .occupancy import analyze_floorplan_occupancy, write_occupancy_svg
from .openram_placement import array_mirror, placed_bbox_from_openram_origin
from .openyield_adapter.array_aggregation import (
    ALLOWED_AGGREGATION_MACROS,
    EXCLUDED_PERIPHERAL_MACROS,
    build_standalone_storage_array_aggregation,
    load_ready_storage_macro_specs,
    orientation_for_row,
)
from .openyield_adapter.architecture_adapter import build_senseamp_architecture_adapter
from .openyield_adapter.columnmux_placement import build_columnmux_limited_placement_plan
from .openyield_adapter.writedriver_adapter import (
    build_writedriver_adapter,
    build_writedriver_contract_summary,
    classify_writedriver_power_status,
    inspect_local_writedriver_macro,
)
from .openyield_adapter.writedriver_placement import build_writedriver_limited_placement_plan
from .openyield_adapter.wordlinedriver_adapter import (
    build_wordlinedriver_adapter,
    build_wordlinedriver_contract_summary,
    classify_wordlinedriver_power_status,
    inspect_local_wordlinedriver_macro,
    inspect_openyield_wordlinedriver_source,
    wordlinedriver_semantics,
)
from .openyield_adapter.wordlinedriver_placement import build_wordlinedriver_limited_placement_plan
from .openyield_adapter.senseamp_placement import (
    build_senseamp_placement_plan,
    inspect_local_senseamp_macro,
)
from .stdcell import add_generated_cell, generated_cell_pins, generated_instance_pins
from .tech import Tech
from .verifier import Verifier


@dataclass(frozen=True)
class StandaloneSpec:
    word_size: int
    num_words: int
    words_per_row: int | None = None
    name: str | None = None
    perimeter_pins: bool = True
    enable_openyield_array_aggregation: bool = False
    enable_openyield_senseamp_adapter: bool = False
    enable_openyield_columnmux_adapter: bool = False
    enable_openyield_writedriver_adapter: bool = False
    enable_openyield_wordlinedriver_adapter: bool = False
    openyield_storage_row_orientation_policy: str = "all_r0"

    def __post_init__(self) -> None:
        if self.word_size <= 0:
            raise ValueError("word_size must be positive")
        if self.num_words <= 0:
            raise ValueError("num_words must be positive")
        if self.words_per_row is not None and self.words_per_row <= 0:
            raise ValueError("words_per_row must be positive when specified")
        if self.words_per_row is not None:
            self._validate_words_per_row(self.words_per_row)
        if self.openyield_storage_row_orientation_policy not in {"all_r0", "alternating_mx"}:
            raise ValueError(
                "openyield_storage_row_orientation_policy must be one of: all_r0, alternating_mx"
            )

    def legal_words_per_row(self) -> list[int]:
        return [wpr for wpr in (1, 2, 4, 8, 16) if self.num_words % wpr == 0 and self.num_words // wpr >= 16]

    def _validate_words_per_row(self, wpr: int) -> None:
        legal = self.legal_words_per_row()
        if wpr not in legal:
            legal_text = ", ".join(str(item) for item in legal) or "none"
            raise ValueError(
                f"illegal words_per_row={wpr} for {self.word_size}x{self.num_words}; "
                f"legal values: {legal_text}"
            )

    def resolved_words_per_row(self) -> int:
        if self.words_per_row:
            return self.words_per_row
        legal = self.legal_words_per_row()
        if not legal:
            raise ValueError(f"No legal words_per_row for {self.word_size}x{self.num_words}")
        return max(legal)

    def resolved_name(self) -> str:
        return self.name or f"sram_{self.word_size}x{self.num_words}_wpr{self.resolved_words_per_row()}_fd45"


def package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return package_root().parents[1]


def default_pdk_root() -> Path:
    return package_root() / "technology" / "freepdk45"


def columnmux_repaired_alias_path() -> Path:
    return default_pdk_root() / "openyield_repaired_macro_aliases.json"


def load_repaired_columnmux_alias(tech: Tech) -> dict[str, object]:
    alias_path = columnmux_repaired_alias_path()
    if not alias_path.exists():
        raise ValueError(f"Missing repaired column mux alias metadata: {alias_path}")
    payload = json.loads(alias_path.read_text(encoding="utf-8"))
    aliases = payload.get("aliases", [])
    alias = next((item for item in aliases if item.get("local_macro") == "gen_col_mux_vdd_labeled"), None)
    if not isinstance(alias, dict):
        raise ValueError(f"Repaired column mux alias not found in metadata: {alias_path}")
    source_macro = tech.cell(str(alias.get("source_macro") or "gen_col_mux"))
    candidate_gds = Path(str(alias.get("candidate_gds") or "")).expanduser()
    if not candidate_gds.is_absolute():
        candidate_gds = package_root() / candidate_gds
    if not candidate_gds.exists():
        raise ValueError(f"Repaired column mux candidate GDS not found: {candidate_gds}")
    alias_cell = replace(
        source_macro,
        name=str(alias["local_macro"]),
        gds_path=str(candidate_gds.resolve()),
    )
    tech.cells[alias_cell.name] = alias_cell
    return {
        "metadata_path": str(alias_path.resolve()),
        "alias": alias,
        "alias_cell": alias_cell,
        "source_cell": source_macro,
    }


def writedriver_contracts_path() -> Path:
    return package_root() / "docs" / "openyield_module_contracts.json"


def load_writedriver_contract() -> dict[str, object]:
    contracts_path = writedriver_contracts_path()
    payload = json.loads(contracts_path.read_text(encoding="utf-8"))
    contracts = payload if isinstance(payload, list) else payload.get("contracts", [])
    for contract in contracts:
        if contract.get("original_module_name") == "WRITEDRIVER":
            contract_copy = dict(contract)
            contract_copy["source_path"] = str(contracts_path.resolve())
            return contract_copy
    raise ValueError(f"Missing WRITEDRIVER contract in {contracts_path}")


def load_wordlinedriver_contract() -> dict[str, object]:
    contracts_path = writedriver_contracts_path()
    payload = json.loads(contracts_path.read_text(encoding="utf-8"))
    contracts = payload if isinstance(payload, list) else payload.get("contracts", [])
    for contract in contracts:
        if contract.get("original_module_name") == "WORDLINEDRIVER":
            contract_copy = dict(contract)
            contract_copy["source_path"] = str(contracts_path.resolve())
            return contract_copy
    raise ValueError(f"Missing WORDLINEDRIVER contract in {contracts_path}")


def load_bundled_freepdk45() -> Tech:
    # Uses only files bundled inside this deliverable: technology/freepdk45/*.
    return Tech.freepdk45(package_root())


def build_layout(spec: StandaloneSpec, tech: Tech) -> LayoutDB:
    name = spec.resolved_name()
    wpr = spec.resolved_words_per_row()
    rows = spec.num_words // wpr
    cols = spec.word_size * wpr

    bitcell = tech.cell("cell_1rw")
    dummy_cell = tech.cell("dummy_cell_1rw")
    replica_cell = tech.cell("replica_cell_1rw")
    dff = tech.cell("dff")
    sense = tech.cell("sense_amp")
    write_driver = tech.cell("write_driver")
    tri_gate = tech.cell("tri_gate")

    strict_macro_spacing = 0.30
    gap = 0.475
    array_edge_gap = 0.50
    column_macro_keepout = strict_macro_spacing
    row_logic_keepout = strict_macro_spacing
    control_array_keepout = strict_macro_spacing
    replica_bitline_keepout = strict_macro_spacing
    perimeter_pin_w = 0.16
    perimeter_pin_h = 0.50
    addr_bits = max(1, (spec.num_words - 1).bit_length())
    row_addr_bits = max(1, (rows - 1).bit_length())
    col_addr_bits = max(0, (wpr - 1).bit_length())
    control_cols = 2 if addr_bits + 4 >= 6 else 1
    control_rows = math.ceil((addr_bits + 4) / control_cols)
    control_w = control_cols * dff.width + (control_cols - 1) * gap
    dff_row_pitch = dff.height + gap + control_array_keepout
    control_h = control_rows * dff.height + (control_rows - 1) * (gap + control_array_keepout)
    control_logic_gap = max(1.20, dff.height * 0.45)
    def physical_cell_width(cell_name: str) -> float:
        cell = tech.cell(cell_name)
        return max(cell.width, cell.bbox_x1 - cell.bbox_x0)

    def physical_cell_height(cell_name: str) -> float:
        cell = tech.cell(cell_name)
        return max(cell.height, cell.bbox_y1 - cell.bbox_y0)

    pitch_layer_names = [
        name for name in tech.layers
        if name != "boundary" and not name.endswith("_label") and not name.endswith("_pin")
    ]
    layer_bbox_cache: dict[tuple[str, str], Rect | None] = {}

    def layer_bbox(cell_name: str, layer_name: str) -> Rect | None:
        key = (cell_name, layer_name)
        if key in layer_bbox_cache:
            return layer_bbox_cache[key]
        cell = tech.cell(cell_name)
        if not cell.gds_path:
            layer_bbox_cache[key] = None
            return None
        layer = tech.layer(layer_name)
        bbox = measure_gds_bbox(Path(str(cell.gds_path)), boundary_layers={layer.gds_layer})
        layer_bbox_cache[key] = bbox
        return bbox

    def snap_up(value: float) -> float:
        grid = tech.manufacturing_grid
        return math.ceil((value - 1e-12) / grid) * grid

    power_ring_width = 0.20
    boundary_margin = snap_up(max(
        strict_macro_spacing,
        power_ring_width + tech.layer("m4").min_space + tech.manufacturing_grid,
    ))

    def required_pitch_gap(layer_name: str, conservative_well: bool = False) -> float:
        layer = tech.layer(layer_name)
        if layer_name in {"pwell", "nwell"}:
            margin = 10 * tech.manufacturing_grid if conservative_well else 0.0
            return max(layer.min_space, layer.min_width + margin)
        return layer.min_space

    def legal_origin_delta_x(left_cell_name: str, right_cell_name: str, conservative_well: bool = False) -> float:
        required = 0.0
        for layer_name in pitch_layer_names:
            left_bbox = layer_bbox(left_cell_name, layer_name)
            right_bbox = layer_bbox(right_cell_name, layer_name)
            if left_bbox is None or right_bbox is None:
                continue
            required = max(required, left_bbox.x1 - right_bbox.x0 + required_pitch_gap(layer_name, conservative_well))
        return snap_up(required)

    def layer_y_interval(cell_name: str, layer_name: str, mirror: str) -> tuple[float, float] | None:
        bbox = layer_bbox(cell_name, layer_name)
        if bbox is None:
            return None
        cell = tech.cell(cell_name)
        if mirror in {"MX", "XY"}:
            return cell.height - bbox.y1, cell.height - bbox.y0
        return bbox.y0, bbox.y1

    def legal_origin_delta_y(
        lower_cell_name: str,
        upper_cell_name: str,
        lower_mirror: str = "R0",
        upper_mirror: str = "R0",
        conservative_well: bool = False,
    ) -> float:
        required = 0.0
        for layer_name in pitch_layer_names:
            lower_interval = layer_y_interval(lower_cell_name, layer_name, lower_mirror)
            upper_interval = layer_y_interval(upper_cell_name, layer_name, upper_mirror)
            if lower_interval is None or upper_interval is None:
                continue
            required = max(required, lower_interval[1] - upper_interval[0] + required_pitch_gap(layer_name, conservative_well))
        return snap_up(required)

    def local_text_pin_x(cell_name: str, labels: set[str]) -> float:
        cell = tech.cell(cell_name)
        xs = [
            float(record["x"])
            for record in inspect_gds_text_records(Path(str(cell.gds_path)))
            if str(record["text"]).strip().lower() in labels
        ]
        if not xs:
            raise ValueError(f"cell {cell_name} is missing expected GDS TEXT pin labels {sorted(labels)}")
        return sum(xs) / len(xs)

    def local_text_pin_point(cell_name: str, labels: set[str]) -> tuple[float, float]:
        cell = tech.cell(cell_name)
        points = [
            (float(record["x"]), float(record["y"]))
            for record in inspect_gds_text_records(Path(str(cell.gds_path)))
            if str(record["text"]).strip().lower() in labels
        ]
        if not points:
            raise ValueError(f"cell {cell_name} is missing expected GDS TEXT pin labels {sorted(labels)}")
        return (
            sum(x for x, _ in points) / len(points),
            sum(y for _, y in points) / len(points),
        )

    def abutted_origin_x(left_origin_x: float, left_cell_name: str, right_cell_name: str, extra_gap: float = 0.0) -> float:
        return left_origin_x + legal_origin_delta_x(left_cell_name, right_cell_name) + extra_gap

    def abutted_origin_y(
        lower_origin_y: float,
        lower_cell_name: str,
        upper_cell_name: str,
        extra_gap: float = 0.0,
        lower_mirror: str = "R0",
        upper_mirror: str = "R0",
    ) -> float:
        return lower_origin_y + legal_origin_delta_y(lower_cell_name, upper_cell_name, lower_mirror, upper_mirror) + extra_gap

    def origin_y_for_bbox_y0(cell_name: str, target_y0: float, mirror: str = "R0") -> float:
        cell = tech.cell(cell_name)
        if mirror in {"MX", "XY"}:
            return target_y0 - cell.height + cell.bbox_y1
        return target_y0 - cell.bbox_y0

    openyield_storage_specs: dict[str, dict[str, float]] = {}
    openyield_gds_pin_audit_path = package_root() / "docs" / "openyield_gds_pin_audit_report.json"
    if spec.enable_openyield_array_aggregation:
        openyield_storage_specs = load_ready_storage_macro_specs(openyield_gds_pin_audit_path)
        missing_openyield_storage = [
            name for name in ALLOWED_AGGREGATION_MACROS if name not in openyield_storage_specs
        ]
        if missing_openyield_storage:
            raise ValueError(
                "OpenYield array aggregation requires audited storage macros: "
                + ", ".join(missing_openyield_storage)
            )
    storage_cell_spacing = 0.0
    # OpenRAM tiles bitcells by their abstract module pitch, not by inserting
    # generic same-layer DRC spacing between hard cells. The bitcell GDS
    # intentionally overhangs its abstract boundary so adjacent cells can
    # stitch wells, implants, rails, and bitlines into a compact array.
    if spec.enable_openyield_array_aggregation:
        bitcell_pitch_x = openyield_storage_specs["cell_1rw"]["width"]
        bitcell_pitch_y = openyield_storage_specs["cell_1rw"]["height"]
        storage_cell_w = bitcell_pitch_x
        storage_cell_h = bitcell_pitch_y
        dummy_cell_pitch_x = openyield_storage_specs["dummy_cell_1rw"]["width"]
        replica_cell_pitch_x = openyield_storage_specs["replica_cell_1rw"]["width"]
    else:
        bitcell_pitch_x = bitcell.width + storage_cell_spacing
        bitcell_pitch_y = bitcell.height + storage_cell_spacing
        storage_cell_w = bitcell.width
        storage_cell_h = bitcell.height
        dummy_cell_pitch_x = dummy_cell.width
        replica_cell_pitch_x = replica_cell.width
    array_w = (cols - 1) * bitcell_pitch_x + storage_cell_w
    array_h = (rows - 1) * bitcell_pitch_y + storage_cell_h
    lower_rows = rows
    upper_rows = 0
    lower_array_h = array_h
    upper_array_h = 0.0

    control_dff_pitch_x = legal_origin_delta_x("dff", "dff")
    dff_row_pitch = max(
        legal_origin_delta_y("dff", "dff", "R0", "MX"),
        legal_origin_delta_y("dff", "dff", "MX", "R0"),
    )
    control_w = (control_cols - 1) * control_dff_pitch_x + dff.width
    control_h = (control_rows - 1) * dff_row_pitch + dff.height
    logic_group_gap = 0.0
    control_logic_gap = logic_group_gap
    module_stack_gap = max(required_pitch_gap("nwell", conservative_well=True), required_pitch_gap("pwell", conservative_well=True))
    control_glue_h = max(
        legal_origin_delta_y("gen_inv", "gen_nand2", "R0", "MX") + physical_cell_height("gen_nand2"),
        legal_origin_delta_y("gen_nand2", "gen_inv", "R0", "MX") + physical_cell_height("gen_inv"),
    )
    column_select_cell = "gen_nand2" if col_addr_bits else "gen_inv"
    column_select_rows = math.ceil(max(1, wpr) / 2)
    column_select_row_pitch = max(
        legal_origin_delta_y(column_select_cell, column_select_cell, "R0", "MX"),
        legal_origin_delta_y(column_select_cell, column_select_cell, "MX", "R0"),
    )
    col_select_h = (column_select_rows - 1) * column_select_row_pitch + physical_cell_height(column_select_cell)
    delay_row_pitch = max(
        legal_origin_delta_y("gen_delay_inv", "gen_delay_inv", "R0", "MX"),
        legal_origin_delta_y("gen_delay_inv", "gen_delay_inv", "MX", "R0"),
    )
    delay_chain_h = delay_row_pitch + physical_cell_height("gen_delay_inv")
    # OpenRAM's FreePDK45 decoder composes rows from predecode/AND2-style
    # generated blocks. This lightweight floorplan keeps that replaceable
    # physical style instead of inventing a non-OpenRAM NAND4 cell.
    row_decode_cell = "gen_nand2"
    row_decode_to_driver_gap = 0.0
    decoder_w = physical_cell_width(row_decode_cell) + row_decode_to_driver_gap + physical_cell_width("gen_wl_driver")
    mux_h = tech.cell("gen_col_mux").height
    precharge_h = tech.cell("gen_precharge").height
    column_macro_pitch = bitcell_pitch_x
    column_macro_w = (cols - 1) * column_macro_pitch + max(physical_cell_width("gen_precharge"), physical_cell_width("gen_col_mux"))
    row_logic_pitch = max(
        bitcell_pitch_y,
        legal_origin_delta_y(row_decode_cell, row_decode_cell, "R0", "MX"),
        legal_origin_delta_y("gen_wl_driver", "gen_wl_driver", "R0", "MX"),
        legal_origin_delta_y(row_decode_cell, row_decode_cell, "MX", "R0"),
        legal_origin_delta_y("gen_wl_driver", "gen_wl_driver", "MX", "R0"),
    )
    row_logic_h = rows * row_logic_pitch
    # Dummy, bitcell, and replica cells belong to one storage-array family.
    # Use the same native bitcell pitch across the whole family so the visual
    # array is a stitched OpenRAM-style fabric instead of separated islands.
    left_dummy_to_array_delta = dummy_cell_pitch_x
    array_to_replica_delta = storage_cell_w
    replica_to_right_dummy_delta = replica_cell_pitch_x
    array_edge_gap = max(left_dummy_to_array_delta - dummy_cell.width, tech.manufacturing_grid)
    bitcell_bl_x = local_text_pin_x("cell_1rw", {"bl"})
    bitcell_br_x = local_text_pin_x("cell_1rw", {"br"})
    bitcell_wl_x, bitcell_wl_y = local_text_pin_point("cell_1rw", {"wl"})
    dummy_wl_x, dummy_wl_y = local_text_pin_point("dummy_cell_1rw", {"wl"})
    replica_wl_x, replica_wl_y = local_text_pin_point("replica_cell_1rw", {"wl"})
    bitcell_bitline_mid_x = (bitcell_bl_x + bitcell_br_x) / 2.0
    replica_bl_x = local_text_pin_x("replica_cell_1rw", {"bl"})
    replica_br_x = local_text_pin_x("replica_cell_1rw", {"br"})
    replica_bitline_mid_x = (replica_bl_x + replica_br_x) / 2.0
    precharge_mid_x = (local_text_pin_x("gen_precharge", {"bl"}) + local_text_pin_x("gen_precharge", {"br"})) / 2.0
    col_mux_mid_x = (local_text_pin_x("gen_col_mux", {"bl"}) + local_text_pin_x("gen_col_mux", {"br"})) / 2.0
    precharge_x_offset = bitcell_bitline_mid_x - precharge_mid_x
    replica_precharge_x_offset = replica_bitline_mid_x - precharge_mid_x
    col_mux_x_offset = bitcell_bitline_mid_x - col_mux_mid_x
    # Keep the bitcell array contiguous. Earlier versions split the array with
    # a central channel, which made a visible "trench" that OpenRAM does not
    # require for this single-bank 1RW floorplan.
    bank_channel_h = 0.0
    decoder_h = max(array_h + bank_channel_h, row_logic_h)
    column_pitch = max(array_w / max(1, spec.word_size), column_macro_pitch * wpr)
    column_cell_w = max(sense.width, write_driver.width, tri_gate.width)
    column_hard_w = (spec.word_size - 1) * column_pitch + column_cell_w
    column_array_w = max(array_w, column_hard_w, column_macro_w)
    column_h = sense.height + gap + write_driver.height + gap + tri_gate.height

    x_control = boundary_margin
    x_decoder = x_control + control_w + gap
    x_dummy_left = x_decoder + decoder_w + gap
    x_array = x_dummy_left + left_dummy_to_array_delta
    x_replica = x_array + (cols - 1) * bitcell_pitch_x + array_to_replica_delta
    x_dummy_right = x_replica + replica_to_right_dummy_delta
    x_replica_precharge = x_replica + replica_precharge_x_offset
    x_right_edge = max(
        x_dummy_right + dummy_cell.width,
        x_replica + replica_cell.width,
        x_replica_precharge + tech.cell("gen_precharge").width,
        x_array + column_array_w,
    )

    row_decode_to_driver_delta_x = legal_origin_delta_x(row_decode_cell, "gen_wl_driver") + row_decode_to_driver_gap
    folded_pair_step_x = (
        row_decode_to_driver_delta_x
        + legal_origin_delta_x("gen_wl_driver", row_decode_cell)
        + strict_macro_spacing
    )

    def row_logic_plan(
        candidate_y_array: float,
        candidate_y_precharge: float,
        candidate_macro_w: float,
        enable_folding: bool = True,
    ) -> dict[str, object]:
        precharge_clear_y0 = candidate_y_precharge + precharge_h + strict_macro_spacing
        folded_start: int | None = None
        if enable_folding:
            for row in range(rows):
                mirror = "MX" if row % 2 else "R0"
                origin_y = candidate_y_array + row * row_logic_pitch
                driver_y0 = placed_bbox_from_openram_origin(tech.cell("gen_wl_driver"), 0.0, origin_y, mirror).y0
                if driver_y0 >= precharge_clear_y0 - 1e-9:
                    folded_start = row
                    break
        folded_rows = list(range(folded_start, rows)) if folded_start is not None else []
        fold_origin_x0 = x_array - tech.cell(row_decode_cell).bbox_x0
        fold_right_limit = candidate_macro_w - boundary_margin
        lanes = max(1, int((fold_right_limit - fold_origin_x0) // max(folded_pair_step_x, tech.manufacturing_grid)) + 1)
        positions: dict[int, dict[str, float | int | bool | str]] = {}
        top = candidate_y_array
        right = x_decoder
        for row in range(rows):
            mirror = "MX" if row % 2 else "R0"
            if row in folded_rows:
                lane = folded_rows.index(row) % lanes
                band = folded_rows.index(row) // lanes
                driver_target_y0 = precharge_clear_y0 + band * row_logic_pitch
                origin_y = origin_y_for_bbox_y0("gen_wl_driver", driver_target_y0, mirror)
                decoder_x = fold_origin_x0 + lane * folded_pair_step_x
            else:
                lane = 0
                band = 0
                origin_y = candidate_y_array + row * row_logic_pitch
                decoder_x = x_decoder
            driver_x = abutted_origin_x(decoder_x, row_decode_cell, "gen_wl_driver", row_decode_to_driver_gap)
            decoder_rect = placed_bbox_from_openram_origin(tech.cell(row_decode_cell), decoder_x, origin_y, mirror)
            driver_rect = placed_bbox_from_openram_origin(tech.cell("gen_wl_driver"), driver_x, origin_y, mirror)
            top = max(top, decoder_rect.y1, driver_rect.y1)
            right = max(right, decoder_rect.x1, driver_rect.x1)
            positions[row] = {
                "decoder_x": decoder_x,
                "driver_x": driver_x,
                "origin_y": origin_y,
                "folded": row in folded_rows,
                "lane": lane,
                "band": band,
                "mirror": mirror,
            }
        return {
            "strategy": (
                "fold top row drivers into occupancy gaps above precharge"
                if enable_folding and folded_rows
                else "linear row drivers"
            ),
            "enabled": enable_folding and bool(folded_rows),
            "folded_rows": folded_rows,
            "folded_row_count": len(folded_rows),
            "lanes": lanes,
            "top_um": top,
            "right_um": right,
            "positions": positions,
        }

    def data_dff_dimensions(candidate_cols: int) -> tuple[int, float, float]:
        candidate_cols = max(1, min(spec.word_size, candidate_cols))
        candidate_rows = math.ceil(spec.word_size / candidate_cols)
        candidate_w = (candidate_cols - 1) * control_dff_pitch_x + dff.width
        candidate_h = (candidate_rows - 1) * dff_row_pitch + dff.height
        return candidate_rows, candidate_w, candidate_h

    def score_data_dff_columns(candidate_cols: int) -> dict[str, object]:
        candidate_rows, candidate_w, candidate_h = data_dff_dimensions(candidate_cols)
        candidate_y_data = boundary_margin
        candidate_y_column = candidate_y_data + candidate_h + gap
        candidate_y_mux = candidate_y_column + column_h + gap
        candidate_y_array = candidate_y_mux + mux_h + gap
        candidate_y_array_top = candidate_y_array + lower_array_h + bank_channel_h + upper_array_h
        candidate_y_precharge = candidate_y_array_top + gap
        candidate_w_total = max(x_array + max(array_w, column_array_w, candidate_w), x_right_edge) + boundary_margin
        variants = []
        for enable_folding in (False, True):
            candidate_row_logic_plan = row_logic_plan(candidate_y_array, candidate_y_precharge, candidate_w_total, enable_folding)
            variant_w_total = max(candidate_w_total, float(candidate_row_logic_plan["right_um"]) + boundary_margin)
            candidate_y_row_logic_top = float(candidate_row_logic_plan["top_um"])
            candidate_h_total = max(
                candidate_y_precharge + precharge_h + boundary_margin,
                candidate_y_row_logic_top + boundary_margin,
                candidate_y_data + control_h + module_stack_gap + control_glue_h + module_stack_gap + col_select_h + module_stack_gap + delay_chain_h + boundary_margin,
            )
            variants.append({
                "columns": candidate_cols,
                "rows": candidate_rows,
                "data_width_um": round(candidate_w, 6),
                "data_height_um": round(candidate_h, 6),
                "macro_width_um": round(variant_w_total, 6),
                "macro_height_um": round(candidate_h_total, 6),
                "macro_area_um2": round(variant_w_total * candidate_h_total, 6),
                "row_logic_folding_enabled": candidate_row_logic_plan["enabled"],
                "folded_row_count": candidate_row_logic_plan["folded_row_count"],
            })
        return min(
            variants,
            key=lambda item: (
                float(item["macro_area_um2"]),
                float(item["macro_height_um"]),
                float(item["macro_width_um"]),
                int(item["columns"]),
            ),
        )

    data_packing_candidates = [score_data_dff_columns(cols_) for cols_ in range(1, spec.word_size + 1)]
    best_data_packing = min(
        data_packing_candidates,
        key=lambda item: (
            float(item["macro_area_um2"]),
            float(item["macro_height_um"]),
            float(item["macro_width_um"]),
            int(item["columns"]),
        ),
    )
    data_cols = int(best_data_packing["columns"])
    data_rows, data_w, data_h = data_dff_dimensions(data_cols)

    y_data = boundary_margin
    y_column = y_data + data_h + gap
    y_mux = y_column + column_h + gap
    y_array = y_mux + mux_h + gap
    y_array_lower = y_array
    y_bank_channel = y_array_lower + lower_array_h
    y_array_upper = y_bank_channel + bank_channel_h
    y_array_top = y_array_upper + upper_array_h
    # Keep the row decoder / wordline-driver stack aligned to the bitcell
    # array rows. This follows OpenRAM's floorplan intent more closely than a
    # lower-left control-quadrant placement: each decoder row sits beside the
    # row it drives, and the top-left void is reduced without overlapping the
    # lower control/data periphery.
    y_row_logic = y_array_lower
    # OpenRAM anchors data-side circuitry to the bitcell array edge. A tall
    # decoder/wordline-driver stack may extend above the array on the left,
    # but it must not force the column-side precharge row upward because the
    # two regions are separated in X.
    y_precharge = y_array_top + gap

    columnmux_alias_info: dict[str, object] | None = None
    columnmux_limited_plan: object | None = None
    columnmux_macro_name = "gen_col_mux"
    if spec.enable_openyield_columnmux_adapter:
        columnmux_alias_info = load_repaired_columnmux_alias(tech)
        columnmux_macro_name = str(columnmux_alias_info["alias"]["local_macro"])
        columnmux_limited_plan = build_columnmux_limited_placement_plan(
            cols=cols,
            mux_ratio=wpr,
            origin_x=x_array,
            origin_y=y_mux,
            pitch_x=bitcell_pitch_x,
            use_repaired_vdd_label=True,
            power_status=str(columnmux_alias_info["alias"].get("power_status", "vdd_label_present")),
            safe_for_physical_mapping=bool(columnmux_alias_info["alias"].get("safe_for_physical_mapping", True)),
            safe_for_shared_rail=bool(columnmux_alias_info["alias"].get("safe_for_shared_rail", False)),
        )

    writedriver_contract_info: dict[str, object] | None = None
    writedriver_local_macro: dict[str, object] | None = None
    writedriver_adapter_info: object | None = None
    writedriver_limited_plan: object | None = None
    if spec.enable_openyield_writedriver_adapter:
        writedriver_contract_info = load_writedriver_contract()
        writedriver_local_macro = inspect_local_writedriver_macro(default_pdk_root())
        writedriver_adapter_info = build_writedriver_adapter(writedriver_local_macro, writedriver_contract_info)
        writedriver_limited_plan = build_writedriver_limited_placement_plan(
            cols=spec.word_size,
            mux_ratio=1,
            origin_x=x_array,
            origin_y=y_column + tri_gate.height + gap,
            pitch_x=column_pitch,
            power_status=writedriver_adapter_info.power_status,
            safe_for_physical_mapping=writedriver_adapter_info.safe_for_physical_mapping,
            safe_for_shared_rail=writedriver_adapter_info.safe_for_shared_rail,
        )

    wordlinedriver_contract_info: dict[str, object] | None = None
    wordlinedriver_local_macro: dict[str, object] | None = None
    wordlinedriver_source_audit: object | None = None
    wordlinedriver_adapter_info: object | None = None
    wordlinedriver_limited_plan: object | None = None
    if spec.enable_openyield_wordlinedriver_adapter:
        wordlinedriver_contract_info = load_wordlinedriver_contract()
        wordlinedriver_local_macro = inspect_local_wordlinedriver_macro(default_pdk_root())
        wordlinedriver_source_audit = inspect_openyield_wordlinedriver_source(repo_root() / "third_party" / "OpenYield")
        wordlinedriver_adapter_info = build_wordlinedriver_adapter(
            wordlinedriver_local_macro,
            wordlinedriver_contract_info,
            wordlinedriver_source_audit,
        )
        wordlinedriver_limited_plan = build_wordlinedriver_limited_placement_plan(
            rows=rows,
            origin_x=x_decoder + row_decode_to_driver_delta_x,
            origin_y=y_row_logic,
            pitch_y=row_logic_pitch,
            power_status=wordlinedriver_adapter_info.power_status,
            safe_for_physical_mapping=wordlinedriver_adapter_info.safe_for_physical_mapping,
            safe_for_shared_rail=wordlinedriver_adapter_info.safe_for_shared_rail,
        )

    macro_w = max(x_array + max(array_w, column_array_w, data_w), x_right_edge) + boundary_margin
    selected_row_logic_plan = row_logic_plan(
        y_row_logic,
        y_precharge,
        macro_w,
        bool(best_data_packing.get("row_logic_folding_enabled")),
    )
    macro_w = max(macro_w, float(selected_row_logic_plan["right_um"]) + boundary_margin)
    y_row_logic_top = float(selected_row_logic_plan["top_um"])
    macro_h = max(
        y_precharge + precharge_h + boundary_margin,
        y_row_logic_top + boundary_margin,
        y_data + control_h + module_stack_gap + control_glue_h + module_stack_gap + col_select_h + module_stack_gap + delay_chain_h + boundary_margin,
    )

    db = LayoutDB(name)
    db.metadata.update({
        "backend": "standalone",
        "word_size": spec.word_size,
        "num_words": spec.num_words,
        "words_per_row": wpr,
        "legal_words_per_row": spec.legal_words_per_row(),
        "enable_openyield_senseamp_adapter": spec.enable_openyield_senseamp_adapter,
        "enable_openyield_columnmux_adapter": spec.enable_openyield_columnmux_adapter,
        "enable_openyield_writedriver_adapter": spec.enable_openyield_writedriver_adapter,
        "enable_openyield_wordlinedriver_adapter": spec.enable_openyield_wordlinedriver_adapter,
        "num_rows": rows,
        "num_cols": cols,
        "bank_style": "contiguous-openram-origin-array",
        "floorplan_compaction_strategy": "occupancy-guided compact perimeter margin",
        "boundary_margin_um": boundary_margin,
        "legacy_boundary_margin_um": 1.2,
        "data_dff_packing_strategy": "global macro area search",
        "data_dff_packing_candidates": data_packing_candidates,
        "selected_data_dff_packing": best_data_packing,
        "row_logic_folding": {
            "strategy": selected_row_logic_plan["strategy"],
            "enabled": selected_row_logic_plan["enabled"],
            "folded_rows": selected_row_logic_plan["folded_rows"],
            "folded_row_count": selected_row_logic_plan["folded_row_count"],
            "lanes": selected_row_logic_plan["lanes"],
        },
        "lower_bank_rows": lower_rows,
        "upper_bank_rows": upper_rows,
        "bank_channel_height_um": bank_channel_h,
        "addr_bits": addr_bits,
        "row_addr_bits": row_addr_bits,
        "col_addr_bits": col_addr_bits,
        "bitcell_width_um": bitcell.width,
        "bitcell_height_um": bitcell.height,
        "bitcell_pitch_x_um": bitcell_pitch_x,
        "bitcell_pitch_y_um": bitcell_pitch_y,
        "storage_cell_spacing_um": storage_cell_spacing,
        "control_dff_pitch_x_um": control_dff_pitch_x,
        "control_dff_pitch_y_um": dff_row_pitch,
        "logic_group_gap_um": logic_group_gap,
        "module_stack_gap_um": module_stack_gap,
        "row_decode_to_driver_gap_um": row_decode_to_driver_gap,
        "bitcell_bl_x_um": bitcell_bl_x,
        "bitcell_br_x_um": bitcell_br_x,
        "bitcell_wl_x_um": bitcell_wl_x,
        "bitcell_wl_y_um": bitcell_wl_y,
        "dummy_wl_x_um": dummy_wl_x,
        "dummy_wl_y_um": dummy_wl_y,
        "replica_wl_x_um": replica_wl_x,
        "replica_wl_y_um": replica_wl_y,
        "replica_bl_x_um": replica_bl_x,
        "replica_br_x_um": replica_br_x,
        "precharge_x_offset_um": precharge_x_offset,
        "replica_precharge_x_offset_um": replica_precharge_x_offset,
        "col_mux_x_offset_um": col_mux_x_offset,
        "control_logic_keepout_um": control_logic_gap,
        "column_macro_pitch_um": column_macro_pitch,
        "row_logic_pitch_um": row_logic_pitch,
        "array_edge_keepout_um": array_edge_gap,
        "column_macro_keepout_um": column_macro_keepout,
        "row_logic_keepout_um": row_logic_keepout,
        "control_array_keepout_um": control_array_keepout,
        "replica_bitline_keepout_um": replica_bitline_keepout,
        "replica_precharge_origin_x_um": x_replica_precharge,
        "strict_macro_spacing_um": strict_macro_spacing,
        "placement_rule": "OpenRAM-style independent decoder and column-side vertical extents",
        "row_logic_origin_y_um": y_row_logic,
        "formal_gds_keeps_guides_separate": False,
    })
    db.metadata["openyield_columnmux_adapter"] = {
        "enabled": spec.enable_openyield_columnmux_adapter,
        "local_macro": columnmux_macro_name,
        "source_macro": "gen_col_mux",
        "repaired_alias_metadata": columnmux_alias_info["metadata_path"] if columnmux_alias_info else None,
        "power_status": columnmux_alias_info["alias"].get("power_status", "vdd_label_present") if columnmux_alias_info else "legacy_metadata_only",
        "safe_for_physical_mapping": bool(columnmux_alias_info["alias"].get("safe_for_physical_mapping", True)) if columnmux_alias_info else False,
        "safe_for_shared_rail": bool(columnmux_alias_info["alias"].get("safe_for_shared_rail", False)) if columnmux_alias_info else False,
        "uses_repaired_alias": bool(spec.enable_openyield_columnmux_adapter),
        "replacement_macros_modified": False,
        "shared_rail_enabled": False,
        "routing_changed": False,
        "gds_writer_changed": False,
        "write_driver_changed": False,
        "wordline_driver_changed": False,
        "senseamp_pairing": {
            "IN": "mux_out[group]",
            "INB": "mux_out_b[group]",
            "Q": "dout[group]",
            "QB": "dropped_complementary_output",
        },
        "limited_placement_plan": columnmux_limited_plan.to_dict() if columnmux_limited_plan is not None else {},
    }
    if spec.enable_openyield_writedriver_adapter and writedriver_adapter_info is not None and writedriver_contract_info is not None and writedriver_local_macro is not None:
        db.metadata["openyield_writedriver_adapter"] = {
            "enabled": True,
            "contract_summary": build_writedriver_contract_summary(writedriver_contract_info),
            "contract_path": writedriver_contract_info.get("source_path"),
            "local_macro": writedriver_local_macro["macro_name"],
            "gds_path": writedriver_local_macro["gds_path"],
            "spice_path": writedriver_local_macro["spice_path"],
            "power_status": writedriver_adapter_info.power_status,
            "safe_for_physical_mapping": writedriver_adapter_info.safe_for_physical_mapping,
            "safe_for_shared_rail": writedriver_adapter_info.safe_for_shared_rail,
            "requires_netlist_rewrite": writedriver_adapter_info.requires_netlist_rewrite,
            "pin_adaptations": [pin.to_dict() for pin in writedriver_adapter_info.pin_adaptations],
            "notes": list(writedriver_adapter_info.notes),
            "placement_plan": writedriver_limited_plan.to_dict() if writedriver_limited_plan is not None else {},
            "placement_count": len(writedriver_limited_plan.placements) if writedriver_limited_plan is not None else 0,
            "adapter_applied_to_placement": False,
            "routing_changed": False,
            "gds_writer_changed": False,
            "shared_rail_enabled": False,
            "write_driver_changed": False,
            "column_mux_changed": spec.enable_openyield_columnmux_adapter,
            "senseamp_changed": spec.enable_openyield_senseamp_adapter,
            "storage_aggregation_enabled": spec.enable_openyield_array_aggregation,
        }
    else:
        db.metadata["openyield_writedriver_adapter"] = {
            "enabled": False,
            "local_macro": "write_driver",
            "power_status": "legacy_metadata_only",
            "safe_for_physical_mapping": False,
            "safe_for_shared_rail": False,
            "requires_netlist_rewrite": False,
            "pin_adaptations": [],
            "notes": [
                "Write driver adapter is opt-in only.",
                "Legacy standalone write_driver placement remains unchanged until explicitly enabled.",
            ],
            "placement_plan": {},
            "placement_count": 0,
            "adapter_applied_to_placement": False,
            "routing_changed": False,
            "gds_writer_changed": False,
            "shared_rail_enabled": False,
            "write_driver_changed": False,
            "column_mux_changed": spec.enable_openyield_columnmux_adapter,
            "senseamp_changed": spec.enable_openyield_senseamp_adapter,
            "storage_aggregation_enabled": spec.enable_openyield_array_aggregation,
        }
    if spec.enable_openyield_wordlinedriver_adapter and wordlinedriver_adapter_info is not None and wordlinedriver_contract_info is not None and wordlinedriver_local_macro is not None and wordlinedriver_source_audit is not None:
        db.metadata["openyield_wordlinedriver_adapter"] = {
            "enabled": True,
            "contract_summary": build_wordlinedriver_contract_summary(wordlinedriver_contract_info),
            "contract_path": wordlinedriver_contract_info.get("source_path"),
            "local_macro": wordlinedriver_local_macro["macro_name"],
            "gds_path": wordlinedriver_local_macro["gds_path"],
            "spice_path": wordlinedriver_local_macro["spice_path"],
            "power_status": wordlinedriver_adapter_info.power_status,
            "safe_for_physical_mapping": wordlinedriver_adapter_info.safe_for_physical_mapping,
            "safe_for_shared_rail": wordlinedriver_adapter_info.safe_for_shared_rail,
            "can_enter_limited_placement": wordlinedriver_adapter_info.can_enter_limited_placement,
            "pin_adaptations": [pin.to_dict() for pin in wordlinedriver_adapter_info.pin_adaptations],
            "notes": list(wordlinedriver_adapter_info.notes) + list(wordlinedriver_source_audit.evidence),
            "placement_plan": wordlinedriver_limited_plan.to_dict() if wordlinedriver_limited_plan is not None else {},
            "placement_count": len(wordlinedriver_limited_plan.placements) if wordlinedriver_limited_plan is not None else 0,
            "adapter_applied_to_placement": True,
            "routing_changed": False,
            "gds_writer_changed": False,
            "shared_rail_enabled": False,
            "write_driver_changed": False,
            "column_mux_changed": spec.enable_openyield_columnmux_adapter,
            "senseamp_changed": spec.enable_openyield_senseamp_adapter,
            "storage_aggregation_enabled": spec.enable_openyield_array_aggregation,
            "b_polarity": wordlinedriver_source_audit.b_polarity,
            "semantic_confirmation": "confirmed_active_high",
            "wordline_driver_changed": False,
            "decoder_changed": False,
            "time_control_changed": False,
        }
    else:
        db.metadata["openyield_wordlinedriver_adapter"] = {
            "enabled": False,
            "local_macro": "gen_wl_driver",
            "power_status": "legacy_metadata_only",
            "safe_for_physical_mapping": False,
            "safe_for_shared_rail": False,
            "can_enter_limited_placement": False,
            "pin_adaptations": [],
            "notes": [
                "Wordline driver adapter is opt-in only.",
                "Legacy standalone wordline driver placement remains unchanged until explicitly enabled.",
            ],
            "placement_plan": {},
            "placement_count": 0,
            "adapter_applied_to_placement": False,
            "routing_changed": False,
            "gds_writer_changed": False,
            "shared_rail_enabled": False,
            "write_driver_changed": False,
            "column_mux_changed": spec.enable_openyield_columnmux_adapter,
            "senseamp_changed": spec.enable_openyield_senseamp_adapter,
            "storage_aggregation_enabled": spec.enable_openyield_array_aggregation,
            "wordline_driver_changed": False,
            "decoder_changed": False,
            "time_control_changed": False,
        }
    db.metadata["openyield_senseamp_adapter"] = {
        "enabled": False,
        "adapter_strategy": "single_ended_q_to_dout",
        "q_to_dout": True,
        "qb_to_dout_b": False,
        "dropped_pins": {"QB": "dropped_complementary_output"},
        "requires_netlist_rewrite": True,
        "requires_layout_pin": False,
        "generated_fake_dout_b": False,
        "routing_changed": False,
        "gds_writer_changed": False,
        "write_driver_changed": False,
        "column_mux_changed": spec.enable_openyield_columnmux_adapter,
        "wordline_driver_changed": spec.enable_openyield_wordlinedriver_adapter,
        "placement_count": 0,
        "local_macro": "sense_amp",
        "local_pins": ["bl", "br", "dout", "en", "vdd", "gnd"],
        "plan": {},
        "example_placements": [],
        "adapter_applied_to_placement": False,
    }

    db.add_shape("boundary", Rect(0, 0, macro_w, macro_h), "boundary", name="prBoundary")

    def add_hard_array(
        name: str,
        cell_name: str,
        x: float,
        y: float,
        columns: int,
        rows_: int,
        pitch_x: float,
        pitch_y: float,
        role: str,
        mirror_x: bool = False,
        mirror_y: bool = False,
        row_offset: int = 0,
        column_offset: int = 0,
    ) -> Rect:
        cell = tech.cell(cell_name)
        placed_rects = [
            placed_bbox_from_openram_origin(
                cell,
                x + col * pitch_x,
                y + row * pitch_y,
                array_mirror(row, col, mirror_x, mirror_y, row_offset, column_offset),
            )
            for row in range(rows_)
            for col in range(columns)
        ]
        rect = Rect.union(placed_rects)
        db.add_cell_array(
            CellArray(
                name,
                cell_name,
                Point(x, y),
                columns,
                rows_,
                pitch_x,
                pitch_y,
                rect,
                role,
                mirror_x,
                mirror_y,
                row_offset,
                column_offset,
            )
        )
        return rect

    if spec.enable_openyield_array_aggregation:
        openyield_storage_aggregation = build_standalone_storage_array_aggregation(
            rows,
            cols,
            enable_openyield_array_aggregation=True,
            row_orientation_policy=spec.openyield_storage_row_orientation_policy,
            gds_pin_audit_path=openyield_gds_pin_audit_path,
            origins={
                "bitcell_array": (x_array, y_array_lower),
                "dummy_left_array": (x_dummy_left, y_array_lower),
                "dummy_right_array": (x_dummy_right, y_array_lower),
                "replica_bitline_array": (x_replica, y_array_lower),
            },
        )
        plan_by_name = {plan.array_name: plan for plan in openyield_storage_aggregation.plans}
        disallowed_storage_macros = sorted(
            {
                plan.cell_macro
                for plan in openyield_storage_aggregation.plans
                if plan.cell_macro not in ALLOWED_AGGREGATION_MACROS
            }
        )
        if disallowed_storage_macros:
            raise ValueError(
                "OpenYield array aggregation produced disallowed storage macros: "
                + ", ".join(disallowed_storage_macros)
            )

        def add_openyield_storage_array(array_name: str) -> Rect:
            plan = plan_by_name[array_name]
            return add_hard_array(
                plan.array_name,
                plan.cell_macro,
                plan.origin_x,
                plan.origin_y,
                plan.cols,
                plan.rows,
                plan.pitch_x,
                plan.pitch_y,
                plan.role,
                mirror_x=plan.row_orientation_policy == "alternating_mx",
                mirror_y=False,
            )

        array_rect = add_openyield_storage_array("bitcell_array")
        dummy_left_rect = add_openyield_storage_array("dummy_left_array")
        dummy_right_rect = add_openyield_storage_array("dummy_right_array")
        replica_rect = add_openyield_storage_array("replica_bitline_array")
    else:
        openyield_storage_aggregation = build_standalone_storage_array_aggregation(
            rows,
            cols,
            enable_openyield_array_aggregation=False,
            row_orientation_policy=spec.openyield_storage_row_orientation_policy,
        )
        array_rect = add_hard_array("bitcell_array", "cell_1rw", x_array, y_array_lower, cols, rows, bitcell_pitch_x, bitcell_pitch_y, "bitcell_array", mirror_x=True)
        dummy_left_rect = add_hard_array("dummy_left_array", "dummy_cell_1rw", x_dummy_left, y_array_lower, 1, rows, bitcell_pitch_x, bitcell_pitch_y, "dummy_bitcell", mirror_x=True)
        dummy_right_rect = add_hard_array("dummy_right_array", "dummy_cell_1rw", x_dummy_right, y_array_lower, 1, rows, bitcell_pitch_x, bitcell_pitch_y, "dummy_bitcell", mirror_x=True)
        replica_rect = add_hard_array("replica_bitline_array", "replica_cell_1rw", x_replica, y_array_lower, 1, rows, bitcell_pitch_x, bitcell_pitch_y, "replica_bitline", mirror_x=True)
    storage_macro_counts: dict[str, int] = {}
    for plan in openyield_storage_aggregation.plans:
        storage_macro_counts[plan.cell_macro] = storage_macro_counts.get(plan.cell_macro, 0) + plan.rows * plan.cols
    db.metadata["openyield_array_aggregation_integration"] = {
        "enabled": openyield_storage_aggregation.enabled,
        "row_orientation_policy": openyield_storage_aggregation.row_orientation_policy,
        "allowed_macros": list(ALLOWED_AGGREGATION_MACROS),
        "excluded_peripheral_macros": dict(EXCLUDED_PERIPHERAL_MACROS),
        "storage_only": True,
        "peripherals_old_path": True,
        "changed_gds_flow": openyield_storage_aggregation.changed_gds_flow,
        "routing_changed": openyield_storage_aggregation.routing_changed,
        "gds_writer_changed": False,
        "shared_rail_merge": openyield_storage_aggregation.shared_rail_merge,
        "generated_gds": False,
        "cross_row_power_short_risk": openyield_storage_aggregation.cross_row_power_short_risk,
        "storage_plan": openyield_storage_aggregation.to_dict(),
        "storage_arrays": {
            "bitcell_array": array_rect.to_dict(),
            "dummy_left_array": dummy_left_rect.to_dict(),
            "dummy_right_array": dummy_right_rect.to_dict(),
            "replica_bitline_array": replica_rect.to_dict(),
        },
        "macro_counts": storage_macro_counts,
        "instance_count": sum(storage_macro_counts.values()),
        "pitch": {"x": bitcell_pitch_x, "y": bitcell_pitch_y},
        "origin": {"x": x_array, "y": y_array_lower},
        "power_rail_policy": openyield_storage_aggregation.power_rail_policy,
    }
    db.add_shape("m1", array_rect, "module", name="ARRAY")
    db.add_shape("m1", dummy_left_rect, "module", name="dummy_left_bbox")
    db.add_shape("m1", dummy_right_rect, "module", name="dummy_right_bbox")
    db.add_shape("m1", replica_rect, "module", name="RBL")
    if bank_channel_h > 0:
        db.add_shape("m2", Rect(x_decoder, y_bank_channel, x_array + array_w, y_array_upper), "module", name="WL_DRIVER_CHANNEL")

    def add_openram_generated_cell(
        name: str,
        cell_name: str,
        x: float,
        y: float,
        role: str,
        mirror: str = "R0",
    ) -> Rect:
        return add_generated_cell(
            db,
            tech,
            name,
            cell_name,
            x,
            y,
            role,
            mirror=mirror,
            placement_mode="openram_origin",
        )

    precharge_rects: list[Rect] = []
    column_mux_rects: list[Rect] = []
    for col in range(cols):
        cell_x = x_array + col * bitcell_pitch_x
        precharge_name = f"precharge_{col}"
        mux_name = f"column_mux_{col}"
        precharge_rects.append(add_openram_generated_cell(precharge_name, "gen_precharge", cell_x + precharge_x_offset, y_precharge, "precharge", mirror="MX"))
        column_mux_rects.append(add_openram_generated_cell(mux_name, columnmux_macro_name, cell_x + col_mux_x_offset, y_mux, "column_mux", mirror="MX"))
        precharge_inst = next(inst for inst in db.instances if inst.name == precharge_name)
        mux_inst = next(inst for inst in db.instances if inst.name == mux_name)
        precharge_pins = {str(pin["name"]): pin for pin in generated_instance_pins(tech, precharge_inst)}
        mux_pins = {str(pin["name"]): pin for pin in generated_instance_pins(tech, mux_inst)}
        for pin_name, local_x in [("BL", bitcell_bl_x), ("BR", bitcell_br_x)]:
            net = f"{pin_name.lower()}[{col}]"
            bitline_x = cell_x + local_x
            y0 = float(mux_pins[pin_name]["y"])
            y1 = float(precharge_pins[pin_name]["y"])
            ylo, yhi = sorted((y0, y1))
            db.add_shape("m2", Rect(bitline_x - 0.035, ylo, bitline_x + 0.035, yhi), "route_guide", net, f"{pin_name.lower()}_route_{col}")
            for endpoint, pin in [("mux", mux_pins[pin_name]), ("precharge", precharge_pins[pin_name])]:
                px = float(pin["x"])
                py = float(pin["y"])
                xlo, xhi = sorted((px, bitline_x))
                if xhi - xlo > tech.manufacturing_grid:
                    db.add_shape("m2", Rect(xlo, py - 0.035, xhi, py + 0.035), "route_guide", net, f"{pin_name.lower()}_{endpoint}_jog_{col}")
    db.add_shape("m1", Rect.union(precharge_rects), "module", name="precharge_array_bbox")
    db.add_shape("m1", Rect.union(column_mux_rects), "module", name="column_mux_array_bbox")

    # Replica timing path.
    add_openram_generated_cell("replica_precharge", "gen_precharge", x_replica_precharge, y_precharge, "replica_precharge", mirror="MX")
    replica_precharge_inst = next(inst for inst in db.instances if inst.name == "replica_precharge")
    replica_precharge_pins = {str(pin["name"]): pin for pin in generated_instance_pins(tech, replica_precharge_inst)}
    for pin_name, local_x in [("BL", replica_bl_x), ("BR", replica_br_x)]:
        net = f"replica_{pin_name.lower()}"
        bitline_x = x_replica + local_x
        pin = replica_precharge_pins[pin_name]
        ylo, yhi = sorted((y_array_lower, float(pin["y"])))
        db.add_shape("m2", Rect(bitline_x - 0.035, ylo, bitline_x + 0.035, yhi), "route_guide", net, f"replica_{pin_name.lower()}_route")
        px = float(pin["x"])
        py = float(pin["y"])
        xlo, xhi = sorted((px, bitline_x))
        if xhi - xlo > tech.manufacturing_grid:
            db.add_shape("m2", Rect(xlo, py - 0.035, xhi, py + 0.035), "route_guide", net, f"replica_{pin_name.lower()}_precharge_jog")

    def row_y(row: int) -> float:
        return y_array_lower + row * bitcell_pitch_y

    def storage_row_mirror(row: int) -> str:
        if spec.enable_openyield_array_aggregation:
            return orientation_for_row(row, openyield_storage_aggregation.row_orientation_policy)
        return array_mirror(row, 0, mirror_x=True)

    def storage_pin_y(row: int, cell, local_y: float) -> float:
        mirror = storage_row_mirror(row)
        y = cell.height - local_y if mirror in {"MX", "XY"} else local_y
        return row_y(row) + y

    def storage_wl_y(row: int) -> float:
        return storage_pin_y(row, bitcell, bitcell_wl_y)

    def storage_wl_extent(row: int) -> tuple[float, float]:
        bitcell_xs = [
            x_array + col * bitcell_pitch_x + bitcell_wl_x
            for col in range(cols)
        ]
        xs = [
            x_dummy_left + dummy_wl_x,
            *bitcell_xs,
            x_replica + replica_wl_x,
            x_dummy_right + dummy_wl_x,
        ]
        extension = max(tech.layer("m1").min_width, tech.manufacturing_grid)
        entry_keepout = tech.layer("m2").min_space + 0.03
        entry_x = x_dummy_left + dummy_cell.bbox_x0 - entry_keepout
        return min(entry_x, min(xs) - extension), max(xs) + extension

    def row_logic_y(row: int) -> float:
        return float(selected_row_logic_plan["positions"][row]["origin_y"])  # type: ignore[index]

    def row_decoder_x(row: int) -> float:
        return float(selected_row_logic_plan["positions"][row]["decoder_x"])  # type: ignore[index]

    def row_driver_x(row: int) -> float:
        return float(selected_row_logic_plan["positions"][row]["driver_x"])  # type: ignore[index]

    row_decoder_rects: list[Rect] = []
    wordline_driver_rects: list[Rect] = []
    for row in range(rows):
        y = row_logic_y(row)
        wl_target_y = storage_wl_y(row)
        wl_target_x, _ = storage_wl_extent(row)
        row_mirror = "MX" if row % 2 else "R0"
        row_decode_x = row_decoder_x(row)
        row_decoder_rects.append(add_openram_generated_cell(f"row_decode_{row}", row_decode_cell, row_decode_x, y, "row_decoder", mirror=row_mirror))
        wl_driver_x = row_driver_x(row)
        wordline_driver_rects.append(add_openram_generated_cell(
            f"wordline_driver_{row}",
            "gen_wl_driver",
            wl_driver_x,
            y,
            "wordline_driver",
            mirror=row_mirror,
        ))
        wl_y = y + tech.cell("gen_wl_driver").height * 0.5
        decoder_z_x = row_decode_x + tech.cell(row_decode_cell).width - 0.18
        driver_a_x = wl_driver_x + tech.cell("gen_wl_driver").width * 0.28
        driver_z_x = wl_driver_x + tech.cell("gen_wl_driver").width - 0.18
        db.add_shape("m1", Rect(decoder_z_x, wl_y - 0.045, driver_a_x, wl_y + 0.045), "route_guide", f"wl_decode[{row}]", f"wl_decode_route_{row}")
        if abs(wl_y - wl_target_y) > 1e-9:
            db.add_shape(
                "m2",
                Rect(driver_z_x - 0.045, min(wl_y, wl_target_y), driver_z_x + 0.045, max(wl_y, wl_target_y)),
                "route_guide",
                f"wl[{row}]",
                f"wl_driver_jog_{row}",
            )
        wl_x0, wl_x1 = sorted((driver_z_x, wl_target_x))
        db.add_shape("m2", Rect(wl_x0, wl_target_y - 0.07, wl_x1, wl_target_y + 0.07), "route_guide", f"wl[{row}]", f"wl_route_{row}")
    db.add_shape("m2", Rect.union(row_decoder_rects), "module", name="DECODER")
    db.add_shape("m2", Rect.union(wordline_driver_rects), "module", name="WL_DRIVER")

    control_rect = add_hard_array(
        "control_dff_array",
        "dff",
        x_control,
        y_data,
        control_cols,
        control_rows,
        control_dff_pitch_x,
        dff_row_pitch,
        "control_logic",
        mirror_x=True,
    )
    db.add_shape("m3", control_rect, "module", name="control_dff_array")
    control_gate_y = origin_y_for_bbox_y0("gen_inv", control_rect.y1 + module_stack_gap, "R0")
    control_glue_rects: list[Rect] = []
    control_glue_rows = [["gen_inv", "gen_nand2"], ["gen_nand2", "gen_inv"]]
    for row_i, row_cells in enumerate(control_glue_rows):
        y = control_gate_y if row_i == 0 else abutted_origin_y(control_gate_y, "gen_inv", "gen_nand2", logic_group_gap, "R0", "MX")
        x = x_control
        previous_cell: str | None = None
        for col_i, cell_name in enumerate(row_cells):
            if previous_cell is not None:
                x = abutted_origin_x(x, previous_cell, cell_name, logic_group_gap)
            i = row_i * 2 + col_i
            row_mirror = "MX" if row_i % 2 else "R0"
            control_glue_rects.append(add_openram_generated_cell(
                f"control_glue_{i}",
                cell_name,
                x,
                y,
                "control_glue",
                mirror=row_mirror,
            ))
            previous_cell = cell_name
    db.add_shape("m3", Rect.union(control_glue_rects), "module", name="timing_control_glue_bbox")
    column_select_rects: list[Rect] = []
    column_select_y0 = origin_y_for_bbox_y0(column_select_cell, Rect.union(control_glue_rects).y1 + module_stack_gap, "R0")
    for i in range(max(1, wpr)):
        row = i // 2
        col = i % 2
        row_mirror = "MX" if row % 2 else "R0"
        x = x_control if col == 0 else abutted_origin_x(x_control, column_select_cell, column_select_cell, logic_group_gap)
        if row == 0:
            y = column_select_y0
        else:
            y = column_select_y0 + row * column_select_row_pitch
        column_select_rects.append(add_openram_generated_cell(
            f"column_select_{i}",
            column_select_cell,
            x,
            y,
            "column_select",
            mirror=row_mirror,
        ))
    db.add_shape("m3", Rect.union(column_select_rects), "module", name="column_select_logic_bbox")
    delay_y = origin_y_for_bbox_y0("gen_delay_inv", Rect.union(column_select_rects).y1 + module_stack_gap, "R0")
    delay_rects: list[Rect] = []
    for i in range(6):
        row = i // 3
        col = i % 3
        row_mirror = "MX" if row % 2 else "R0"
        delay_rects.append(add_openram_generated_cell(
            f"control_delay_{i}",
            "gen_delay_inv",
            x_control + col * legal_origin_delta_x("gen_delay_inv", "gen_delay_inv"),
            delay_y + row * delay_row_pitch,
            "delay_chain",
            mirror=row_mirror,
        ))
    db.add_shape("m3", Rect.union(delay_rects), "module", name="replica_timing_delay_bbox")
    timing_control_rect = Rect.union([control_rect, Rect.union(control_glue_rects), Rect.union(column_select_rects), Rect.union(delay_rects)])
    db.add_shape("m3", timing_control_rect, "module", name="TIMING_CONTROL")

    sense_origin_x = x_array
    sense_origin_y = y_column + write_driver.height + tri_gate.height + 2 * gap
    if spec.enable_openyield_senseamp_adapter:
        senseamp_adapter = build_senseamp_architecture_adapter(qb_required_downstream=False)
        senseamp_local_macro = inspect_local_senseamp_macro(default_pdk_root())
        senseamp_plan = build_senseamp_placement_plan(
            cols=cols,
            mux_ratio=wpr,
            origin_x=sense_origin_x,
            origin_y=sense_origin_y,
            pitch_x=column_pitch,
            adapter=senseamp_adapter,
            local_macro=senseamp_local_macro,
        )
        if len(senseamp_plan.placements) != spec.word_size:
            raise ValueError(
                f"sense_amp adapter placement count mismatch: expected {spec.word_size}, "
                f"got {len(senseamp_plan.placements)}"
            )
        db.metadata["openyield_senseamp_adapter"] = {
            "enabled": True,
            "adapter_strategy": senseamp_plan.adapter_strategy,
            "q_to_dout": senseamp_local_macro.q_to_dout_established,
            "qb_to_dout_b": senseamp_local_macro.qb_to_dout_b_established,
            "dropped_pins": {"QB": "dropped_complementary_output"},
            "requires_netlist_rewrite": senseamp_plan.requires_netlist_rewrite,
            "requires_layout_pin": senseamp_plan.requires_layout_pin,
            "generated_fake_dout_b": False,
            "routing_changed": False,
            "gds_writer_changed": False,
            "write_driver_changed": False,
            "column_mux_changed": spec.enable_openyield_columnmux_adapter,
            "wordline_driver_changed": False,
            "placement_count": len(senseamp_plan.placements),
            "local_macro": senseamp_local_macro.macro_name,
            "local_pins": list(senseamp_local_macro.spice_pins),
            "plan": senseamp_plan.to_dict(),
            "example_placements": [item.to_dict() for item in senseamp_plan.placements[: min(4, len(senseamp_plan.placements))]],
            "adapter_applied_to_placement": True,
            "sense_rect_origin": {"x": sense_origin_x, "y": sense_origin_y},
            "column_pitch_um": column_pitch,
            "mux_ratio": wpr,
            "storage_aggregation_enabled": spec.enable_openyield_array_aggregation,
        }
    sense_rect = add_hard_array("sense_amp_array", "sense_amp", sense_origin_x, sense_origin_y, spec.word_size, 1, column_pitch, sense.height, "sense_amp")
    write_rect = add_hard_array("write_driver_array", "write_driver", x_array, y_column + tri_gate.height + gap, spec.word_size, 1, column_pitch, write_driver.height, "write_driver")
    tri_rect = add_hard_array("tri_gate_array", "tri_gate", x_array, y_column, spec.word_size, 1, column_pitch, tri_gate.height, "tri_gate")
    periph_rect = Rect(x_array, y_column, max(sense_rect.x1, write_rect.x1, tri_rect.x1), sense_rect.y1)
    db.add_shape("m1", periph_rect, "module", name="SA_SWITCH_LATCH_MUX")
    db.add_shape("m1", sense_rect, "module", name="sense_amp_array_bbox")
    db.add_shape("m1", write_rect, "module", name="write_driver_array_bbox")
    db.add_shape("m1", tri_rect, "module", name="data_latch_trigate_array_bbox")
    mux_probe_instance = next(inst for inst in db.instances if inst.name == "column_mux_0")
    mux_probe_pins = {str(pin["name"]): pin for pin in generated_instance_pins(tech, mux_probe_instance)}
    mux_out_y = float(mux_probe_pins["OUT"]["y"])
    mux_sel_y = float(mux_probe_pins["SEL"]["y"])
    for i in range(spec.word_size):
        first_col = i * wpr
        mux_x0 = x_array + first_col * bitcell_pitch_x
        last_col = min(first_col + wpr, cols) - 1
        mux_x1 = x_array + last_col * bitcell_pitch_x + bitcell.width
        bus_y = y_mux + 0.22 + i * 0.14
        db.add_shape("m3", Rect(mux_x0, bus_y - 0.035, mux_x1, bus_y + 0.035), "route_guide", f"mux_d[{i}]", f"mux_bus_{i}")
        out_y = mux_out_y
        out_route_w = tech.layer("m3").min_width
        for col in range(first_col, min(first_col + wpr, cols)):
            out_x = x_array + col * bitcell_pitch_x + bitcell.width * 0.50
            y0, y1 = sorted((out_y, bus_y))
            if y1 - y0 < out_route_w:
                center = (y0 + y1) / 2.0
                y0 = center - out_route_w / 2.0
                y1 = center + out_route_w / 2.0
            db.add_shape(
                "m3",
                Rect(out_x - out_route_w / 2.0, y0, out_x + out_route_w / 2.0, y1),
                "route_guide",
                f"mux_d[{i}]",
                f"mux_out_{col}_to_bus_{i}",
            )
        sense_x = x_array + i * column_pitch + sense.width * 0.5
        db.add_shape("m2", Rect(sense_x - 0.035, y_column, sense_x + 0.035, y_mux), "route_guide", f"mux_d[{i}]", f"sense_drop_{i}")

    for i in range(spec.word_size):
        col = i % data_cols
        row = i // data_cols
        x = x_array + col * control_dff_pitch_x
        y = y_data + row * dff_row_pitch
        rect = Rect(x, y, x + physical_cell_width("dff"), y + physical_cell_height("dff"))
        db.add_instance(Instance(f"data_dff_{i}", "dff", rect, "data_dff"))
    data_rect = Rect(x_array, y_data, x_array + data_w, y_data + data_h)
    db.add_shape("m2", data_rect, "module", name="data_dff_array")

    pin_w = perimeter_pin_w
    pin_h = perimeter_pin_h

    # Top-level interconnect. These are intentionally visible macro-level straps
    # that bridge the hard macros and generated peripheral cells.
    route_w = 0.09
    via_w = 0.065
    via_enclosure = 0.035

    def route_width(layer: str) -> float:
        return max(route_w, tech.layer(layer).min_width)

    def hrect(layer: str, x0: float, x1: float, y: float) -> Rect:
        lo, hi = sorted((x0, x1))
        width = route_width(layer)
        if hi - lo < width:
            center = (lo + hi) / 2
            lo = center - width / 2
            hi = center + width / 2
        return Rect(lo, y - width / 2, hi, y + width / 2)

    def vrect(layer: str, x: float, y0: float, y1: float) -> Rect:
        lo, hi = sorted((y0, y1))
        width = route_width(layer)
        if hi - lo < width:
            center = (lo + hi) / 2
            lo = center - width / 2
            hi = center + width / 2
        return Rect(x - width / 2, lo, x + width / 2, hi)

    def via_rect(x: float, y: float) -> Rect:
        x = tech.snap(x)
        y = tech.snap(y)
        return Rect(x - via_w / 2, y - via_w / 2, x + via_w / 2, y + via_w / 2)

    def via_landing_rect(x: float, y: float) -> Rect:
        x = tech.snap(x)
        y = tech.snap(y)
        width = via_w + 2 * via_enclosure
        return Rect(x - width / 2, y - width / 2, x + width / 2, y + width / 2)

    def hroute(layer: str, x0: float, x1: float, y: float, net: str, name: str, purpose: str = "route_guide") -> None:
        lo, hi = sorted((x0, x1))
        if hi > lo:
            db.add_shape(layer, hrect(layer, lo, hi, y), purpose, net, name)

    def vroute(layer: str, x: float, y0: float, y1: float, net: str, name: str, purpose: str = "route_guide") -> None:
        lo, hi = sorted((y0, y1))
        if hi > lo:
            db.add_shape(layer, vrect(layer, x, lo, hi), purpose, net, name)

    def hroute_with_width(layer: str, x0: float, x1: float, y: float, width: float, net: str, name: str, purpose: str = "route_guide") -> None:
        lo, hi = sorted((x0, x1))
        if hi > lo:
            db.add_shape(layer, Rect(lo, y - width / 2, hi, y + width / 2), purpose, net, name)

    def vroute_with_width(layer: str, x: float, y0: float, y1: float, width: float, net: str, name: str, purpose: str = "route_guide") -> None:
        lo, hi = sorted((y0, y1))
        if hi > lo:
            db.add_shape(layer, Rect(x - width / 2, lo, x + width / 2, hi), purpose, net, name)

    def via(layer: str, x: float, y: float, net: str, name: str, purpose: str = "route_guide") -> None:
        x = tech.snap(x)
        y = tech.snap(y)
        via_rule = tech.vias.get(layer)
        if via_rule is not None:
            pad = via_landing_rect(x, y)
            db.add_shape(via_rule.lower, pad, purpose, net, f"{name}_{via_rule.lower}_landing")
            db.add_shape(via_rule.upper, pad, purpose, net, f"{name}_{via_rule.upper}_landing")
        db.add_shape(layer, via_rect(x, y), purpose, net, name)

    def pin_access(layer: str, x: float, y: float, net: str, name: str, purpose: str = "route_guide") -> None:
        width = max(route_w, tech.layer(layer).min_width)
        db.add_shape(layer, Rect(x - width / 2, y - width / 2, x + width / 2, y + width / 2), purpose, net, name)

    def wordline_escape_lane_x(row: int, driver_x: float, target_x: float) -> float:
        if bool(selected_row_logic_plan["positions"][row]["folded"]):  # type: ignore[index]
            return tech.snap(driver_x)
        pitch = max(route_width("m3") + tech.layer("m3").min_space, 0.21)
        left = min(driver_x, target_x)
        right = macro_w - boundary_margin - pitch
        lanes = max(1, int((right - left) // pitch) + 1)
        return tech.snap(left + (row % lanes) * pitch)

    def route_generated_pin_to_m3(
        pin: dict[str, object],
        end_x: float,
        track_y: float,
        net: str,
        name: str,
        purpose: str = "route_guide",
    ) -> None:
        x = float(pin["x"])
        y = float(pin["y"])
        pin_layer = str(pin["layer"])
        pin_access(pin_layer, x, y, net, f"{name}_access", purpose)
        if pin_layer == "m1":
            via("via1", x, y, net, f"{name}_via1", purpose)
            vroute("m2", x, y, track_y, net, f"{name}_m2_escape", purpose)
            via("via2", x, track_y, net, f"{name}_via2", purpose)
            hroute("m3", x, end_x, track_y, net, f"{name}_m3_track", purpose)
        elif pin_layer == "m2":
            vroute("m2", x, y, track_y, net, f"{name}_m2_escape", purpose)
            via("via2", x, track_y, net, f"{name}_via2", purpose)
            hroute("m3", x, end_x, track_y, net, f"{name}_m3_track", purpose)
        else:
            hroute(pin_layer, x, end_x, track_y, net, f"{name}_track", purpose)

    control_bus_x = x_control + control_w + 0.15
    decoder_bus_x = x_decoder - 0.14
    first_precharge = next(inst for inst in db.instances if inst.name == "precharge_0")
    first_precharge_pins = {str(pin["name"]): pin for pin in generated_instance_pins(tech, first_precharge)}
    precharge_en_y = float(first_precharge_pins.get("EN", {"y": y_precharge + precharge_h * 0.55})["y"])
    sense_en_y = sense_rect.center.y
    write_en_y = write_rect.center.y
    tri_en_y = tri_rect.center.y
    data_bus_y = max(data_rect.y1 + 0.18, tri_rect.y0 - 0.18)

    # Local control stubs touch the generated control cells through their
    # modeled pin access points, making signal entry/exit explicit in clean GDS.
    local_control_roles = {"control_glue", "column_select", "delay_chain"}
    local_track_pitch = max(tech.layer("m3").min_width + tech.layer("m3").min_space + 0.02, 0.16)
    local_track_counts: dict[float, int] = {}

    def local_track_y_for(instance: Instance) -> float:
        row_key = round(instance.rect.y0, 3)
        lane = local_track_counts.get(row_key, 0)
        local_track_counts[row_key] = lane + 1
        return instance.rect.y0 + 0.22 + lane * local_track_pitch

    for instance in [inst for inst in db.instances if inst.role in local_control_roles]:
        pins = generated_instance_pins(tech, instance)
        for pin in pins:
            pin_name = str(pin["name"])
            if pin_name in {"gnd", "vdd"}:
                continue
            track_y = local_track_y_for(instance)
            if pin_name in {"A", "B", "C", "D", "SEL"}:
                net = f"{instance.name}_{pin_name.lower()}_in"
                route_generated_pin_to_m3(
                    pin,
                    control_rect.x1,
                    track_y,
                    net,
                    f"{instance.name}_{pin_name.lower()}",
                    "route_guide",
                )
            elif pin_name in {"Z", "OUT", "OUTB"}:
                net = f"{instance.name}_{pin_name.lower()}_out"
                route_generated_pin_to_m3(
                    pin,
                    control_bus_x,
                    track_y,
                    net,
                    f"{instance.name}_{pin_name.lower()}",
                    "route_guide",
                )
            else:
                continue

    for instance in [inst for inst in db.instances if inst.role == "replica_precharge"]:
        for pin in generated_instance_pins(tech, instance):
            pin_name = str(pin["name"])
            net = pin_name if pin_name in {"gnd", "vdd"} else f"replica_{pin_name.lower()}"
            pin_access(str(pin["layer"]), float(pin["x"]), float(pin["y"]), net, f"{instance.name}_{pin_name}_access")

    for instance in [inst for inst in db.instances if inst.role in {"precharge", "column_mux"}]:
        index = int(instance.name.rsplit("_", 1)[-1]) if instance.name.rsplit("_", 1)[-1].isdigit() else 0
        for pin in generated_instance_pins(tech, instance):
            pin_name = str(pin["name"])
            if pin_name in {"gnd", "vdd"}:
                continue
            if instance.role == "precharge":
                net = "pchg_en" if pin_name == "EN" else f"{pin_name.lower()}[{index}]"
            elif pin_name == "SEL":
                net = f"col_sel[{index % max(1, wpr)}]"
            elif pin_name in {"OUT", "OUTB"}:
                net = f"mux_d[{index // max(1, wpr)}]"
            else:
                net = f"{pin_name.lower()}[{index}]"
            pin_access(str(pin["layer"]), float(pin["x"]), float(pin["y"]), net, f"{instance.name}_{pin_name.lower()}_access", "route")

    for instance in [inst for inst in db.instances if inst.role == "row_decoder"]:
        row_index = int(instance.name.rsplit("_", 1)[-1]) if instance.name.rsplit("_", 1)[-1].isdigit() else -1
        for pin in generated_instance_pins(tech, instance):
            pin_name = str(pin["name"])
            if pin_name in {"gnd", "vdd"}:
                continue
            net = f"wl_decode[{row_index}]" if pin_name == "Z" and row_index >= 0 else f"{instance.name}_{pin_name.lower()}_access"
            pin_access(str(pin["layer"]), float(pin["x"]), float(pin["y"]), net, f"{instance.name}_{pin_name.lower()}_access")

    row_decoders = {instance.name: instance for instance in db.instances if instance.role == "row_decoder"}
    for driver in [inst for inst in db.instances if inst.role == "wordline_driver"]:
        row_index = int(driver.name.rsplit("_", 1)[-1]) if driver.name.rsplit("_", 1)[-1].isdigit() else -1
        driver_pins = {str(pin["name"]): pin for pin in generated_instance_pins(tech, driver)}
        decoder = row_decoders.get(f"row_decode_{row_index}")
        decoder_pins = {str(pin["name"]): pin for pin in generated_instance_pins(tech, decoder)} if decoder is not None else {}
        drv_a = driver_pins.get("A")
        drv_z = driver_pins.get("Z")
        dec_z = decoder_pins.get("Z")
        if row_index >= 0 and dec_z is not None and drv_a is not None:
            net = f"wl_decode[{row_index}]"
            pin_access(str(drv_a["layer"]), float(drv_a["x"]), float(drv_a["y"]), net, f"{driver.name}_a_access")
            hroute("m1", float(dec_z["x"]), float(drv_a["x"]), float(drv_a["y"]), net, f"{driver.name}_decode_to_a")
        if row_index >= 0 and drv_z is not None:
            net = f"wl[{row_index}]"
            wl_target_y = storage_wl_y(row_index)
            wl_rail_x0, wl_rail_x1 = storage_wl_extent(row_index)
            drv_z_x = float(drv_z["x"])
            drv_z_y = float(drv_z["y"])
            lane_x = wordline_escape_lane_x(row_index, drv_z_x, wl_rail_x0)
            pin_access(str(drv_z["layer"]), drv_z_x, drv_z_y, net, f"{driver.name}_z_access", "route")
            via("via1", drv_z_x, drv_z_y, net, f"{driver.name}_z_via1", "route")
            via("via2", drv_z_x, drv_z_y, net, f"{driver.name}_z_via2", "route")
            hroute("m3", drv_z_x, lane_x, drv_z_y, net, f"{driver.name}_z_to_escape_lane", "route")
            vroute("m3", lane_x, drv_z_y, wl_target_y, net, f"{driver.name}_z_escape", "route")
            via("via2", lane_x, wl_target_y, net, f"{driver.name}_escape_lane_via2", "route")
            hroute("m2", lane_x, wl_rail_x0, wl_target_y, net, f"{driver.name}_to_array", "route")
            via("via1", wl_rail_x0, wl_target_y, net, f"{driver.name}_array_entry_via1", "route")
            hroute("m1", wl_rail_x0, wl_rail_x1, wl_target_y, net, f"wl_row_rail_{row_index}", "route")

    # Address and row decode buses: external address pins enter from the right,
    # then turn down/up into the row decoder input spine.
    vroute("m3", decoder_bus_x, y_array_lower, y_precharge + precharge_h, "addr_bus", "addr_decode_spine")
    for i in range(addr_bits):
        y = y_array_lower + i * max(0.45, min(bitcell_pitch_y, decoder_h / max(addr_bits, 1)))
        net = f"addr[{i}]"
        hroute("m3", decoder_bus_x, macro_w - pin_w, y + pin_h * 0.5, net, f"addr_{i}_to_decoder")
        via("via2", decoder_bus_x, y + pin_h * 0.5, net, f"addr_{i}_decoder_via")
    for row in range(rows):
        y = row_y(row) + bitcell.height * 0.35
        decoder = row_decoders.get(f"row_decode_{row}")
        if decoder is not None:
            hroute("m3", decoder.rect.x0, decoder.rect.x1, y, f"dec_in[{row}]", f"row_decode_input_{row}")

    # Column-select rails drive every column mux group.
    sel_source_y = control_gate_y + control_glue_h + gap + tech.cell("gen_inv").height * 0.5
    colsel_pitch = max(tech.layer("m3").pitch, route_width("m3") + tech.layer("m3").min_space)
    colsel_count = max(1, wpr)

    def clone_with_shapes(extra_shapes: list[Shape]) -> LayoutDB:
        trial = LayoutDB(db.top_name)
        trial.shapes = [
            Shape(shape.layer, shape.rect, shape.purpose, shape.net, shape.name)
            for shape in db.shapes
        ]
        trial.shapes.extend(extra_shapes)
        return trial

    def col_select_shapes(y0: float) -> list[Shape]:
        m3_half_width = route_width("m3") / 2.0
        shapes: list[Shape] = [
            Shape(
                "m3",
                vrect("m3", control_bus_x, sel_source_y - m3_half_width, y0 + colsel_count * colsel_pitch),
                "route_guide",
                "col_sel_bus",
                "col_select_spine",
            ),
            Shape(
                "m3",
                hrect("m3", control_rect.x1, control_bus_x + m3_half_width, sel_source_y),
                "route_guide",
                "col_sel_bus",
                "col_select_from_control",
            ),
        ]
        for sel in range(colsel_count):
            y = y0 + sel * colsel_pitch
            net = f"col_sel[{sel}]"
            shapes.append(Shape("m3", hrect("m3", control_bus_x, x_array + array_w, y), "route_guide", net, f"col_sel_{sel}_rail"))
            for bit in range(spec.word_size):
                x = x_array + (bit * wpr + min(sel, wpr - 1)) * bitcell_pitch_x + bitcell.width * 0.5
                shapes.append(Shape("m2", vrect("m2", x, y, mux_sel_y), "route_guide", net, f"col_sel_{sel}_drop_{bit}"))
                shapes.append(Shape("via2", via_rect(x, y), "route_guide", net, f"col_sel_{sel}_via_{bit}"))
        return shapes

    def score_col_select_candidate(y0: float) -> tuple[int, int, float, float]:
        shapes = col_select_shapes(y0)
        names = {shape.name for shape in shapes}
        trial = clone_with_shapes(shapes)
        metrics = _promote_drc_clean_guides(trial, tech)
        remaining_candidate_guides = sum(
            1 for shape in trial.shapes if shape.name in names and shape.purpose == "route_guide"
        )
        wirelength = sum(max(shape.rect.width, shape.rect.height) for shape in shapes if shape.layer not in tech.vias)
        preferred_y0 = y_mux + 0.20
        return (
            remaining_candidate_guides,
            int(metrics["remaining_route_guides"]),
            round(wirelength, 6),
            abs(y0 - preferred_y0),
        )

    def select_col_select_y0() -> float:
        preferred_y0 = y_mux + 0.20
        min_y = y_column + 0.05
        max_y = y_array - 0.05
        span_steps = max(10, spec.word_size + colsel_count + 2)
        candidates: list[float] = []
        for offset in range(-span_steps, span_steps + 1):
            y0 = tech.snap(preferred_y0 + offset * colsel_pitch)
            y_last = y0 + (colsel_count - 1) * colsel_pitch
            if y0 < min_y or y_last > max_y:
                continue
            if y0 not in candidates:
                candidates.append(y0)
        scored = [(score_col_select_candidate(y0), y0) for y0 in candidates]
        best_score, best_y0 = min(scored, key=lambda item: item[0])
        db.metadata["routing_track_selection"] = {
            "col_select": {
                "algorithm": "DRC-aware candidate route-guide promotion scoring",
                "candidate_count": len(scored),
                "preferred_y0": round(preferred_y0, 4),
                "selected_y0": round(best_y0, 4),
                "pitch": round(colsel_pitch, 4),
                "score": {
                    "remaining_candidate_guides": best_score[0],
                    "remaining_total_guides": best_score[1],
                    "candidate_wirelength_um": best_score[2],
                    "preferred_offset_um": round(best_score[3], 4),
                },
            }
        }
        return best_y0

    colmux_y0 = select_col_select_y0()
    m3_half_width = route_width("m3") / 2.0
    vroute("m3", control_bus_x, sel_source_y - m3_half_width, colmux_y0 + colsel_count * colsel_pitch, "col_sel_bus", "col_select_spine")
    hroute("m3", control_rect.x1, control_bus_x + m3_half_width, sel_source_y, "col_sel_bus", "col_select_from_control")
    for sel in range(colsel_count):
        y = colmux_y0 + sel * colsel_pitch
        net = f"col_sel[{sel}]"
        hroute("m3", control_bus_x, x_array + array_w, y, net, f"col_sel_{sel}_rail")
        for bit in range(spec.word_size):
            x = x_array + (bit * wpr + min(sel, wpr - 1)) * bitcell_pitch_x + bitcell.width * 0.5
            vroute("m2", x, y, mux_sel_y, net, f"col_sel_{sel}_drop_{bit}")
            via("via2", x, y, net, f"col_sel_{sel}_via_{bit}")

    # Global control enables for precharge, sense, write, and output tri-state.
    enable_x = max(control_rect.x1 + 0.20, control_bus_x)
    vroute("m3", enable_x, tri_en_y, precharge_en_y, "control_enable_bus", "control_enable_spine")
    for net, y in [
        ("pchg_en", precharge_en_y),
        ("sense_en", sense_en_y),
        ("write_en", write_en_y),
        ("tri_en", tri_en_y),
    ]:
        hroute("m3", control_rect.x1, enable_x, y, net, f"{net}_from_control")
        hroute("m3", enable_x, x_array + array_w, y, net, f"{net}_global")
        via("via2", enable_x, y, net, f"{net}_enable_via")
    for col in range(cols):
        x = x_array + col * bitcell_pitch_x + bitcell.width * 0.5
        vroute("m2", x, precharge_en_y, y_precharge + precharge_h * 0.50, "pchg_en", f"pchg_en_drop_{col}")
    for instance in [inst for inst in db.instances if inst.role == "precharge"]:
        pins = {str(pin["name"]): pin for pin in generated_instance_pins(tech, instance)}
        pin = pins.get("EN")
        if pin is not None:
            pin_access(str(pin["layer"]), float(pin["x"]), float(pin["y"]), "pchg_en", f"{instance.name}_en_access")
    for bit in range(spec.word_size):
        x = x_array + bit * column_pitch + column_cell_w * 0.5
        for net, y in [("sense_en", sense_en_y), ("write_en", write_en_y), ("tri_en", tri_en_y)]:
            vroute("m2", x, y, y, net, f"{net}_tap_{bit}")
            via("via2", x, y, net, f"{net}_tap_via_{bit}")

    # Data path: din pins feed data DFFs/write drivers; tri-gates drive dout pins.
    data_pin_rects: list[Rect] = []
    for bit in range(spec.word_size):
        data_col = bit % data_cols
        data_row = bit // data_cols
        rows_in_col = math.ceil((spec.word_size - data_col) / data_cols)
        tap_fraction = min(0.75, max(0.25, (data_row + 1) / (rows_in_col + 1)))
        data_x = x_array + data_col * control_dff_pitch_x + dff.width * tap_fraction
        periph_x = x_array + bit * column_pitch + column_cell_w * 0.5
        din_y = pin_w
        net_in = f"din[{bit}]"
        data_pin_rects.append(Rect(data_x - pin_h * 0.5, 0, data_x + pin_h * 0.5, pin_w))
        vroute("m2", data_x, din_y, data_rect.y0, net_in, f"din_{bit}_to_dff")
        hroute("m3", data_x, periph_x, data_bus_y + bit * 0.10, net_in, f"din_{bit}_write_bus")
        vroute("m2", periph_x, data_bus_y + bit * 0.10, write_rect.center.y, net_in, f"din_{bit}_write_drop")
        via("via2", data_x, data_bus_y + bit * 0.10, net_in, f"din_{bit}_dff_via")
        via("via2", periph_x, data_bus_y + bit * 0.10, net_in, f"din_{bit}_write_via")

        net_out = f"dout[{bit}]"
        dout_y = y_column + bit * 0.55 + 0.125
        hroute("m3", periph_x, macro_w - pin_w, dout_y, net_out, f"dout_{bit}_to_pin")
        vroute("m2", periph_x, tri_rect.center.y, dout_y, net_out, f"dout_{bit}_tri_drop")
        via("via2", periph_x, dout_y, net_out, f"dout_{bit}_tri_via")

    # Power stitching across the main module rows.
    for y in [y_data + 0.12, y_column + 0.12, y_mux + 0.12, y_array_lower + 0.12, y_bank_channel + 0.12, y_array_upper + 0.12, y_precharge + 0.12]:
        hroute("m4", 0.20, macro_w - 0.20, y, "gnd", f"gnd_stitch_{round(y, 3)}")
    for y in [data_rect.y1 - 0.12, periph_rect.y1 - 0.12, y_mux + mux_h - 0.12, y_bank_channel - 0.12, y_array_top - 0.12, y_precharge + precharge_h - 0.12]:
        hroute("m4", 0.20, macro_w - 0.20, y, "vdd", f"vdd_stitch_{round(y, 3)}")

    # Simple preferred-direction routes and perimeter pins.
    for i, net in enumerate(["clk", "csb", "web"]):
        y = control_rect.y0 + i * 0.75
        db.add_pin(net, net, "m2", Rect(0, y, pin_w, y + pin_h), "INPUT")
        db.add_shape("m2", Rect(pin_w, y + pin_h / 2 - 0.035, control_rect.x0, y + pin_h / 2 + 0.035), "route", net)

    for i in range(addr_bits):
        y = y_array_lower + i * max(0.45, min(bitcell_pitch_y, decoder_h / max(addr_bits, 1)))
        db.add_pin(f"addr[${i}]".replace("$", ""), f"addr[{i}]", "m3", Rect(macro_w - pin_w, y, macro_w, y + pin_h), "INPUT")

    for i in range(spec.word_size):
        db.add_pin(f"din[${i}]".replace("$", ""), f"din[{i}]", "m2", data_pin_rects[i], "INPUT")
        db.add_pin(f"dout[${i}]".replace("$", ""), f"dout[{i}]", "m3", Rect(macro_w - pin_w, y_column + i * 0.55, macro_w, y_column + i * 0.55 + 0.25), "OUTPUT")

    db.add_pin("vdd", "vdd", "m4", Rect(0, macro_h - 0.2, macro_w, macro_h - 0.05), "INOUT", "POWER")
    db.add_pin("gnd", "gnd", "m4", Rect(0, 0.05, macro_w, 0.2), "INOUT", "GROUND")
    db.add_shape("m4", Rect(0.05, 0, 0.2, macro_h), "route", "gnd", "left_gnd_ring")
    db.add_shape("m4", Rect(macro_w - 0.2, 0, macro_w - 0.05, macro_h), "route", "vdd", "right_vdd_ring")
    for x in (x_control, x_array, x_array + array_w, x_replica):
        db.add_shape("m4", Rect(x, 0.2, x + 0.16, macro_h - 0.2), "route", "vdd", "vdd_strap")
    return db


def write_standalone(spec: StandaloneSpec, out_dir: Path) -> dict:
    tech = load_bundled_freepdk45()
    layout = build_layout(spec, tech)
    route_guide_promotion = _promote_drc_clean_guides(layout, tech)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = layout.top_name
    gds = out_dir / f"{name}.gds"
    presentation_gds = out_dir / f"{name}.presentation.gds"
    debug_gds = out_dir / f"{name}.debug.gds"
    complete_gds = out_dir / f"{name}.complete.gds"
    integration_gds = out_dir / f"{name}.integration.gds"
    architecture_gds = out_dir / f"{name}.architecture.gds"
    architecture_svg = out_dir / f"{name}.architecture.svg"
    occupancy_svg = out_dir / f"{name}.occupancy.svg"
    route_guide_gds = out_dir / f"{name}.route_guides.gds"
    lef = out_dir / f"{name}.lef"
    layout_json = out_dir / f"{name}.layout.json"
    spice = out_dir / f"{name}.sp"
    report_json = out_dir / f"{name}.report.json"
    report_md = out_dir / f"{name}.report.md"

    GDSWriter(tech).write(layout, gds)
    GDSWriter(
        tech,
        include_pin_labels=False,
        include_cell_pin_labels=False,
        strip_imported_text=True,
    ).write(layout, presentation_gds)
    GDSWriter(
        tech,
        include_route_guides=True,
        include_debug_probes=True,
        include_module_overlay=True,
    ).write(layout, debug_gds)
    GDSWriter(tech, include_route_guides=True).write(layout, complete_gds)
    GDSWriter(tech, omit_cell_refs=True).write(layout, integration_gds)
    GDSWriter(tech, include_module_overlay=True).write(layout, architecture_gds)
    GDSWriter(tech, include_route_guides=True, include_debug_probes=True).write(layout, route_guide_gds)
    _write_architecture_svg(layout, architecture_svg)
    LEFWriter(tech).write(layout, lef, ["m1", "m2", "m3", "m4"])
    NetlistWriter(tech).write(layout, spice)
    layout.write_json(layout_json)
    drc = Verifier(tech).run(layout)
    bounds = layout.bounds
    boundary_margin = float(layout.metadata.get("boundary_margin_um", 0.0) or 0.0)
    legacy_boundary_margin = float(layout.metadata.get("legacy_boundary_margin_um", boundary_margin) or boundary_margin)
    legacy_margin_delta = max(0.0, legacy_boundary_margin - boundary_margin)
    estimated_legacy_w = bounds.width + 2 * legacy_margin_delta
    estimated_legacy_h = bounds.height + 2 * legacy_margin_delta
    estimated_legacy_area = estimated_legacy_w * estimated_legacy_h
    useful = spec.word_size * spec.num_words * tech.cell("cell_1rw").area
    hardcell_arrays: dict[str, int] = {}
    for array in layout.cell_arrays:
        hardcell_arrays[array.cell] = hardcell_arrays.get(array.cell, 0) + array.columns * array.rows
    hardcell_instances: dict[str, int] = {}
    generated_instances: dict[str, int] = {}
    abstract_instances: dict[str, int] = {}
    for instance in layout.instances:
        if instance.cell in tech.cells:
            cell = tech.cell(instance.cell)
            if cell.gds_path:
                hardcell_instances[instance.cell] = hardcell_instances.get(instance.cell, 0) + 1
            if cell.role == "generated_stdcell":
                generated_instances[instance.cell] = generated_instances.get(instance.cell, 0) + 1
            elif not cell.gds_path:
                abstract_instances[instance.cell] = abstract_instances.get(instance.cell, 0) + 1
        else:
            abstract_instances[instance.cell] = abstract_instances.get(instance.cell, 0) + 1
    role_counts: dict[str, int] = {}
    for array in layout.cell_arrays:
        role_counts[array.role or array.cell] = role_counts.get(array.role or array.cell, 0) + array.columns * array.rows
    for instance in layout.instances:
        role_counts[instance.role or instance.cell] = role_counts.get(instance.role or instance.cell, 0) + 1
    route_guide_count = sum(1 for shape in layout.shapes if shape.purpose == "route_guide")
    gds_hierarchy = inspect_gds_hierarchy(gds)
    layer_audit = _audit_layers(tech, gds, route_guide_gds)
    expected_roles = {
        "bitcell_array",
        "column_mux",
        "column_select",
        "control_glue",
        "control_logic",
        "data_dff",
        "delay_chain",
        "dummy_bitcell",
        "precharge",
        "replica_bitline",
        "replica_precharge",
        "row_decoder",
        "sense_amp",
        "tri_gate",
        "wordline_driver",
        "write_driver",
    }
    missing_roles = sorted(role for role in expected_roles if role_counts.get(role, 0) <= 0)
    used_gds_cells = sorted(
        cell for cell in set(hardcell_arrays) | set(hardcell_instances)
        if cell in tech.cells and tech.cell(cell).gds_path
    )
    used_gds_files = sorted({str(Path(str(tech.cell(cell).gds_path)).resolve()) for cell in used_gds_cells})
    cell_bbox_audit = _audit_cell_bboxes(tech, used_gds_cells)
    hardcell_pin_access = _inspect_hardcell_pin_access(tech, used_gds_cells)
    abstract_macro_instances = {
        cell: count
        for cell, count in abstract_instances.items()
        if cell in tech.cells and tech.cell(cell).role == "abstract_macro"
    }
    replacement_macro_instances = {
        cell: count
        for cell, count in hardcell_instances.items()
        if cell.startswith("gen_") and cell in tech.cells and tech.cell(cell).gds_path
    }
    generated_pin_access = _inspect_generated_pin_access(
        tech,
        {**generated_instances, **abstract_macro_instances, **replacement_macro_instances},
    )
    connectivity_audit = _audit_generated_connectivity(layout, include_guides=True)
    route_only_connectivity_audit = _audit_generated_connectivity(layout, include_guides=False)
    generated_pin_route_audit = _audit_generated_pin_coverage(layout, tech, {"route"})
    generated_pin_route_or_guide_audit = _audit_generated_pin_coverage(layout, tech, {"route", "route_guide"})
    generated_gds_cells = sorted(
        cell for cell in set(generated_instances) | set(replacement_macro_instances)
        if gds_hierarchy["reference_counts"].get(cell, 0) > 0
    )
    macro_replacement_audit = _audit_macro_replacements(
        tech,
        {**abstract_macro_instances, **replacement_macro_instances},
    )
    openram_cell_source_audit = _audit_openram_cell_sources(tech, used_gds_cells, generated_instances, abstract_instances)
    architecture_quality = _audit_architecture(layout)
    geometry_audit = _audit_geometry(layout, tech)
    occupancy_audit = analyze_floorplan_occupancy(layout)
    write_occupancy_svg(occupancy_svg, occupancy_audit)
    cell_array_mirror_audit = _audit_cell_array_mirroring(layout)
    cell_array_layer_audit = _audit_cell_array_layer_abutment(tech, layout)
    structural_audit = _audit_structural_consistency(tech, layout)
    debug_probe_count = sum(1 for shape in layout.shapes if shape.purpose == "debug_probe")
    signoff_blockers = []
    if abstract_instances:
        signoff_blockers.append("abstract peripheral logic remains")
    if missing_roles:
        signoff_blockers.append("missing SRAM peripheral roles: " + ", ".join(missing_roles))
    if not geometry_audit["clean"]:
        signoff_blockers.append("geometry audit found placement outside prBoundary or module overhang")
    if not cell_array_mirror_audit["clean"]:
        signoff_blockers.append("OpenRAM-style bitcell/dummy/replica row mirroring is incomplete")
    if not cell_array_layer_audit["clean"]:
        signoff_blockers.append("cell-array layer audit found physical same-layer overlap from too-small pitch")
    if not structural_audit["clean"]:
        signoff_blockers.append("structural audit found loose abutment, unused column mux/precharge, or bitline misalignment")
    if generated_instances:
        signoff_blockers.append("generated decoder/control stdcells need external DRC/LVS validation before signoff")
    if not openram_cell_source_audit["clean"]:
        signoff_blockers.append("some used cells are missing GDS or come from synthetic non-OpenRAM generated-cell geometry")
    if not route_only_connectivity_audit["all_generated_roles_touched_by_routes"]:
        signoff_blockers.append("some replacement macro roles are not touched by drawn detailed routes")
    if not generated_pin_route_audit["all_generated_signal_pins_covered"]:
        signoff_blockers.append("some replacement macro signal pins only have debug probes/guides or are still unrouted")
    if route_guide_count:
        signoff_blockers.append("top-level route guides show intended connectivity but must be replaced by DRC-clean detailed routing")
    signoff_blockers.append("external signoff DRC/LVS/PEX has not been run; install KLayout/Magic/netgen or project signoff tools")
    signoff_blockers.append("SPICE netlist is structural; complete LVS equivalence must be proven with extracted netlist")
    signoff_criteria = {
        "no_abstract_instances": not bool(abstract_instances),
        "all_structural_roles_present": not missing_roles,
        "drawn_routes_touch_generated_roles": route_only_connectivity_audit["all_generated_roles_touched_by_routes"],
        "drawn_routes_cover_generated_signal_pins": generated_pin_route_audit["all_generated_signal_pins_covered"],
        "built_in_drc_clean": drc.clean,
        "layers_match_freepdk45": layer_audit["matches_bundled_freepdk45_layers"],
        "architecture_floorplan_clean": architecture_quality["sample_like_floorplan"],
        "geometry_clean": geometry_audit["clean"],
        "cell_array_mirroring_clean": cell_array_mirror_audit["clean"],
        "cell_array_layers_clean": cell_array_layer_audit["clean"],
        "structural_consistency_clean": structural_audit["clean"],
        "used_cells_are_openram_or_bundled_freepdk45_gds": openram_cell_source_audit["clean"],
        "external_drc_clean": False,
        "external_lvs_clean": False,
        "external_pex_available": False,
    }
    metrics = {
        "backend": "standalone",
        "name": name,
        "word_size": spec.word_size,
        "num_words": spec.num_words,
        "words_per_row": spec.resolved_words_per_row(),
        "legal_words_per_row": spec.legal_words_per_row(),
        "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
        "enable_openyield_senseamp_adapter": spec.enable_openyield_senseamp_adapter,
        "enable_openyield_columnmux_adapter": spec.enable_openyield_columnmux_adapter,
        "enable_openyield_writedriver_adapter": spec.enable_openyield_writedriver_adapter,
        "enable_openyield_wordlinedriver_adapter": spec.enable_openyield_wordlinedriver_adapter,
        "openyield_storage_row_orientation_policy": spec.openyield_storage_row_orientation_policy,
        "bank_style": layout.metadata.get("bank_style"),
        "floorplan_compaction_strategy": layout.metadata.get("floorplan_compaction_strategy"),
        "boundary_margin_um": boundary_margin,
        "legacy_boundary_margin_um": legacy_boundary_margin,
        "data_dff_packing_strategy": layout.metadata.get("data_dff_packing_strategy"),
        "selected_data_dff_packing": layout.metadata.get("selected_data_dff_packing", {}),
        "data_dff_packing_candidates": layout.metadata.get("data_dff_packing_candidates", []),
        "row_logic_folding": layout.metadata.get("row_logic_folding", {}),
        "estimated_legacy_width_um": estimated_legacy_w,
        "estimated_legacy_height_um": estimated_legacy_h,
        "estimated_legacy_macro_area_um2": estimated_legacy_area,
        "estimated_compaction_area_savings_um2": estimated_legacy_area - bounds.area,
        "estimated_compaction_area_savings_percent": (
            (estimated_legacy_area - bounds.area) / estimated_legacy_area if estimated_legacy_area else 0.0
        ),
        "lower_bank_rows": layout.metadata.get("lower_bank_rows"),
        "upper_bank_rows": layout.metadata.get("upper_bank_rows"),
        "bank_channel_height_um": layout.metadata.get("bank_channel_height_um"),
        "width_um": bounds.width,
        "height_um": bounds.height,
        "macro_area_um2": bounds.area,
        "useful_array_area_um2": useful,
        "utilization": useful / bounds.area if bounds.area else 0.0,
        "dead_area_um2": bounds.area - useful,
        "drc_clean": drc.clean,
        "drc_violation_count": len(drc.violations),
        "drc": drc.to_dict(),
        "hardcell_arrays": dict(sorted(hardcell_arrays.items())),
        "hardcell_instances": dict(sorted(hardcell_instances.items())),
        "generated_instances": dict(sorted(generated_instances.items())),
        "replacement_macro_instances": dict(sorted(replacement_macro_instances.items())),
        "abstract_instances": dict(sorted(abstract_instances.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "layout_completeness": {
            "expected_roles": sorted(expected_roles),
            "missing_roles": missing_roles,
            "complete_structural_roles": not missing_roles,
            "top_level_port_count": len(layout.pin_list()),
            "route_guide_count": route_guide_count,
            "debug_probe_count": debug_probe_count,
        },
        "route_metrics": {
            "route_length_um_by_layer": layout.route_length_by_layer({"route"}),
            "route_guide_length_um_by_layer": layout.route_length_by_layer({"route_guide"}),
            "route_and_guide_length_um_by_layer": layout.route_length_by_layer({"route", "route_guide"}),
        },
        "routing_track_selection": layout.metadata.get("routing_track_selection", {}),
        "route_guide_promotion": route_guide_promotion,
        "openyield_columnmux_adapter": layout.metadata.get("openyield_columnmux_adapter", {}),
        "openyield_array_aggregation_integration": layout.metadata.get("openyield_array_aggregation_integration", {}),
        "openyield_senseamp_adapter": layout.metadata.get("openyield_senseamp_adapter", {}),
        "openyield_writedriver_adapter": layout.metadata.get("openyield_writedriver_adapter", {}),
        "openyield_wordlinedriver_adapter": layout.metadata.get("openyield_wordlinedriver_adapter", {}),
        "architecture_modules": _collect_architecture_modules(layout),
        "architecture_quality": architecture_quality,
        "geometry_audit": geometry_audit,
        "floorplan_occupancy": occupancy_audit,
        "cell_array_mirror_audit": cell_array_mirror_audit,
        "cell_array_layer_audit": cell_array_layer_audit,
        "structural_audit": structural_audit,
        "macro_replacement_audit": macro_replacement_audit,
        "openram_cell_source_audit": openram_cell_source_audit,
        "cell_bbox_audit": cell_bbox_audit,
        "gds_hierarchy": gds_hierarchy,
        "layer_audit": layer_audit,
        "hardcell_pin_access": hardcell_pin_access,
        "generated_pin_access": generated_pin_access,
        "connectivity_audit": connectivity_audit,
        "route_only_connectivity_audit": route_only_connectivity_audit,
        "generated_pin_route_audit": generated_pin_route_audit,
        "generated_pin_route_or_guide_audit": generated_pin_route_or_guide_audit,
        "generated_gds_cells": generated_gds_cells,
        "signoff_ready": False,
        "signoff_criteria": signoff_criteria,
        "signoff_blockers": signoff_blockers,
        "gds": str(gds),
        "presentation_gds": str(presentation_gds),
        "debug_gds": str(debug_gds),
        "complete_gds": str(complete_gds),
        "integration_gds": str(integration_gds),
        "architecture_gds": str(architecture_gds),
        "architecture_svg": str(architecture_svg),
        "occupancy_svg": str(occupancy_svg),
        "route_guide_gds": str(route_guide_gds),
        "lef": str(lef),
        "spice": str(spice),
        "layout_json": str(layout_json),
        "report_md": str(report_md),
        "external_files_used": {
            "gds_lib": [
                path for path in used_gds_files
            ],
            "sp_lib": [
                str(default_pdk_root() / "sp_lib" / f"{cell}.sp")
                for cell in used_gds_cells
                if (default_pdk_root() / "sp_lib" / f"{cell}.sp").exists()
            ],
            "layers_map": str(default_pdk_root() / "layers.map"),
            "klayout_decks": [
                str(path)
                for path in sorted((default_pdk_root() / "tech").glob("*.lydrc"))
                + sorted((default_pdk_root() / "tech").glob("*.lylvs"))
            ],
        },
    }
    report_json.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(_format_report_md(metrics), encoding="utf-8")
    return metrics


def _collect_architecture_modules(layout: LayoutDB) -> list[dict[str, object]]:
    modules: list[dict[str, object]] = []
    for shape in layout.shapes:
        if shape.purpose != "module":
            continue
        modules.append({
            "name": shape.name or "module",
            "layer": shape.layer,
            "area_um2": round(shape.rect.area, 4),
            "rect": shape.rect.to_dict(),
        })
    return sorted(modules, key=lambda item: str(item["name"]))


def _audit_architecture(layout: LayoutDB) -> dict[str, object]:
    required = [
        "ARRAY",
        "RBL",
        "WL_DRIVER",
        "DECODER",
        "TIMING_CONTROL",
        "SA_SWITCH_LATCH_MUX",
    ]
    modules = {shape.name: shape for shape in layout.shapes if shape.purpose == "module" and shape.name}
    overlaps: list[dict[str, object]] = []
    allowed_overlaps: list[dict[str, object]] = []

    def legal_featured_module_overlap(left_name: str, right_name: str) -> bool:
        return {left_name, right_name} == {"ARRAY", "RBL"}

    for i, left_name in enumerate(required):
        left = modules.get(left_name)
        if left is None:
            continue
        for right_name in required[i + 1:]:
            right = modules.get(right_name)
            if right is None:
                continue
            if left.rect.overlaps(right.rect):
                item = {
                    "a": left_name,
                    "b": right_name,
                    "a_rect": left.rect.to_dict(),
                    "b_rect": right.rect.to_dict(),
                    "reason": "openram_storage_boundary_stitching" if legal_featured_module_overlap(left_name, right_name) else "",
                }
                if legal_featured_module_overlap(left_name, right_name):
                    allowed_overlaps.append(item)
                else:
                    overlaps.append(item)
    return {
        "required_modules": required,
        "present_modules": [name for name in required if name in modules],
        "missing_modules": [name for name in required if name not in modules],
        "featured_module_overlap_count": len(overlaps),
        "featured_module_overlaps": overlaps,
        "allowed_featured_module_overlap_count": len(allowed_overlaps),
        "allowed_featured_module_overlaps": allowed_overlaps,
        "sample_like_floorplan": all(name in modules for name in required) and not overlaps,
    }


def _audit_structural_consistency(tech: Tech, layout: LayoutDB) -> dict[str, object]:
    eps = max(tech.manufacturing_grid * 0.5, 1e-9)
    metadata = layout.metadata
    cols = int(metadata.get("num_cols", 0) or 0)
    rows = int(metadata.get("num_rows", 0) or 0)
    wpr = int(metadata.get("words_per_row", 1) or 1)
    violations: list[dict[str, object]] = []

    arrays = {array.name: array for array in layout.cell_arrays}
    instances = {instance.name: instance for instance in layout.instances}

    def physical_width(cell_name: str) -> float:
        cell = tech.cell(cell_name)
        return max(cell.width, cell.bbox_x1 - cell.bbox_x0)

    def physical_height(cell_name: str) -> float:
        cell = tech.cell(cell_name)
        return max(cell.height, cell.bbox_y1 - cell.bbox_y0)

    storage_arrays = ["bitcell_array", "dummy_left_array", "dummy_right_array", "replica_bitline_array"]
    storage_pitch_checks: list[dict[str, object]] = []
    expected_storage_pitch_x = float(metadata.get("bitcell_pitch_x_um", 0.0) or 0.0)
    expected_storage_pitch_y = float(metadata.get("bitcell_pitch_y_um", 0.0) or 0.0)
    for name in storage_arrays:
        array = arrays.get(name)
        if array is None:
            violations.append({"type": "missing_storage_array", "array": name})
            continue
        expected_x = expected_storage_pitch_x or physical_width(array.cell)
        expected_y = expected_storage_pitch_y or physical_height(array.cell)
        dx = round(array.pitch_x - expected_x, 6)
        dy = round(array.pitch_y - expected_y, 6)
        info = {
            "array": name,
            "cell": array.cell,
            "pitch_x": array.pitch_x,
            "pitch_y": array.pitch_y,
            "expected_pitch_x": expected_x,
            "expected_pitch_y": expected_y,
            "extra_gap_x_um": dx,
            "extra_gap_y_um": dy,
        }
        storage_pitch_checks.append(info)
        if array.columns > 1 and abs(dx) > eps:
            violations.append({"type": "storage_pitch_x_not_abutted", **info})
        if array.rows > 1 and abs(dy) > eps:
            violations.append({"type": "storage_pitch_y_not_abutted", **info})

    bitcell_array = arrays.get("bitcell_array")
    bitcell_bl_x = float(metadata.get("bitcell_bl_x_um", 0.0) or 0.0)
    bitcell_br_x = float(metadata.get("bitcell_br_x_um", 0.0) or 0.0)
    col_mux_offset = float(metadata.get("col_mux_x_offset_um", 0.0) or 0.0)
    precharge_offset = float(metadata.get("precharge_x_offset_um", 0.0) or 0.0)

    def indexed_instances(role: str) -> dict[int, Instance]:
        indexed: dict[int, Instance] = {}
        for instance in layout.instances:
            if instance.role != role:
                continue
            suffix = instance.name.rsplit("_", 1)[-1]
            if suffix.isdigit():
                indexed[int(suffix)] = instance
        return indexed

    column_muxes = indexed_instances("column_mux")
    precharges = indexed_instances("precharge")
    missing_mux_indices = [i for i in range(cols) if i not in column_muxes]
    extra_mux_indices = sorted(i for i in column_muxes if i < 0 or i >= cols)
    missing_precharge_indices = [i for i in range(cols) if i not in precharges]
    extra_precharge_indices = sorted(i for i in precharges if i < 0 or i >= cols)
    if missing_mux_indices or extra_mux_indices:
        violations.append({
            "type": "column_mux_index_mismatch",
            "expected_indices": [0, max(0, cols - 1)],
            "missing": missing_mux_indices,
            "extra": extra_mux_indices,
        })
    if missing_precharge_indices or extra_precharge_indices:
        violations.append({
            "type": "precharge_index_mismatch",
            "expected_indices": [0, max(0, cols - 1)],
            "missing": missing_precharge_indices,
            "extra": extra_precharge_indices,
        })

    column_alignment: list[dict[str, object]] = []
    if bitcell_array is not None:
        route_shapes = {
            shape.name: shape
            for shape in layout.shapes
            if shape.name and shape.name.startswith(("bl_route_", "br_route_"))
        }
        for col in range(cols):
            cell_x = bitcell_array.origin.x + col * bitcell_array.pitch_x
            expected = {
                "BL": cell_x + bitcell_bl_x,
                "BR": cell_x + bitcell_br_x,
            }
            mux = column_muxes.get(col)
            precharge = precharges.get(col)
            entry = {"column": col, "expected_bl_x": expected["BL"], "expected_br_x": expected["BR"]}
            for role, instance, offset in [("column_mux", mux, col_mux_offset), ("precharge", precharge, precharge_offset)]:
                if instance is None or instance.origin is None:
                    continue
                expected_origin_x = cell_x + offset
                delta = round(instance.origin.x - expected_origin_x, 6)
                entry[f"{role}_origin_delta_x_um"] = delta
                if abs(delta) > eps:
                    violations.append({
                        "type": f"{role}_origin_misaligned",
                        "column": col,
                        "actual_origin_x": instance.origin.x,
                        "expected_origin_x": expected_origin_x,
                        "delta_um": delta,
                    })
            for pin_name, route_name in [("BL", f"bl_route_{col}"), ("BR", f"br_route_{col}")]:
                shape = route_shapes.get(route_name)
                if shape is None:
                    violations.append({"type": "missing_bitline_route", "column": col, "route": route_name})
                    continue
                actual_x = shape.rect.center.x
                delta = round(actual_x - expected[pin_name], 6)
                entry[f"{pin_name.lower()}_route_delta_x_um"] = delta
                if abs(delta) > eps:
                    violations.append({
                        "type": "bitline_route_misaligned",
                        "column": col,
                        "pin": pin_name,
                        "actual_x": actual_x,
                        "expected_x": expected[pin_name],
                        "delta_um": delta,
                    })
            column_alignment.append(entry)

    compact_roles = {"control_glue", "column_select", "delay_chain", "data_dff"}
    compact_gap_checks: list[dict[str, object]] = []
    layer_bbox_cache: dict[tuple[str, str], Rect | None] = {}

    def layer_bbox(cell_name: str, layer_name: str) -> Rect | None:
        key = (cell_name, layer_name)
        if key in layer_bbox_cache:
            return layer_bbox_cache[key]
        cell = tech.cell(cell_name)
        if not cell.gds_path:
            layer_bbox_cache[key] = None
            return None
        layer = tech.layer(layer_name)
        bbox = measure_gds_bbox(Path(str(cell.gds_path)), boundary_layers={layer.gds_layer})
        layer_bbox_cache[key] = bbox
        return bbox

    pitch_layer_names = [
        name for name in tech.layers
        if name != "boundary" and not name.endswith("_label") and not name.endswith("_pin")
    ]

    def required_pitch_gap(layer_name: str) -> float:
        layer = tech.layer(layer_name)
        if layer_name in {"pwell", "nwell"}:
            return max(layer.min_space, layer.min_width)
        return layer.min_space

    def legal_origin_delta_x(left_cell_name: str, right_cell_name: str) -> float:
        required = 0.0
        for layer_name in pitch_layer_names:
            left_bbox = layer_bbox(left_cell_name, layer_name)
            right_bbox = layer_bbox(right_cell_name, layer_name)
            if left_bbox is None or right_bbox is None:
                continue
            required = max(required, left_bbox.x1 - right_bbox.x0 + required_pitch_gap(layer_name))
        grid = tech.manufacturing_grid
        return math.ceil((required - 1e-12) / grid) * grid

    def instance_origin_x(instance: Instance) -> float:
        if instance.origin is not None:
            return instance.origin.x
        cell = tech.cell(instance.cell)
        return instance.rect.x0 - cell.bbox_x0

    storage_family_cells = {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}

    def storage_family_origin_delta_x(left_cell_name: str, right_cell_name: str) -> float:
        if left_cell_name in storage_family_cells and right_cell_name in storage_family_cells:
            return tech.cell(left_cell_name).width
        return legal_origin_delta_x(left_cell_name, right_cell_name)

    storage_boundary_checks: list[dict[str, object]] = []

    def add_storage_boundary_check(
        left_array_name: str,
        right_array_name: str,
        left_col: int,
        right_col: int,
    ) -> None:
        left_array = arrays.get(left_array_name)
        right_array = arrays.get(right_array_name)
        if left_array is None or right_array is None:
            return
        left_origin_x = left_array.origin.x + left_col * left_array.pitch_x
        right_origin_x = right_array.origin.x + right_col * right_array.pitch_x
        expected_delta = storage_family_origin_delta_x(left_array.cell, right_array.cell)
        actual_delta = right_origin_x - left_origin_x
        extra_delta = round(actual_delta - expected_delta, 6)
        info = {
            "left_array": left_array_name,
            "right_array": right_array_name,
            "left_cell": left_array.cell,
            "right_cell": right_array.cell,
            "left_col": left_col,
            "right_col": right_col,
            "origin_delta_x_um": round(actual_delta, 6),
            "expected_origin_delta_x_um": round(expected_delta, 6),
            "extra_origin_delta_x_um": extra_delta,
        }
        storage_boundary_checks.append(info)
        if extra_delta > eps:
            violations.append({"type": "storage_family_extra_gap", **info})
        elif extra_delta < -eps:
            violations.append({"type": "storage_family_overlap", **info})

    add_storage_boundary_check("dummy_left_array", "bitcell_array", 0, 0)
    if bitcell_array is not None and cols > 0:
        add_storage_boundary_check("bitcell_array", "replica_bitline_array", cols - 1, 0)
    add_storage_boundary_check("replica_bitline_array", "dummy_right_array", 0, 0)

    bitcell_wl_x = float(metadata.get("bitcell_wl_x_um", 0.0) or 0.0)
    bitcell_wl_y = float(metadata.get("bitcell_wl_y_um", 0.0) or 0.0)
    dummy_wl_x = float(metadata.get("dummy_wl_x_um", bitcell_wl_x) or bitcell_wl_x)
    dummy_wl_y = float(metadata.get("dummy_wl_y_um", bitcell_wl_y) or bitcell_wl_y)
    replica_wl_x = float(metadata.get("replica_wl_x_um", bitcell_wl_x) or bitcell_wl_x)
    replica_wl_y = float(metadata.get("replica_wl_y_um", bitcell_wl_y) or bitcell_wl_y)
    wordline_row_checks: list[dict[str, object]] = []
    wordline_row_rails = {
        int(shape.name.rsplit("_", 1)[-1]): shape
        for shape in layout.shapes
        if shape.name
        and shape.name.startswith("wl_row_rail_")
        and shape.name.rsplit("_", 1)[-1].isdigit()
        and shape.layer == "m1"
        and shape.purpose == "route"
    }

    def transformed_storage_pin(array: CellArray, row: int, col: int, local_x: float, local_y: float) -> tuple[float, float]:
        cell = tech.cell(array.cell)
        xoffset = array.origin.x + col * array.pitch_x
        yoffset = array.origin.y + row * array.pitch_y
        mirror = array_mirror(
            row,
            col,
            array.mirror_x,
            array.mirror_y,
            array.row_offset,
            array.column_offset,
        )
        ox = xoffset + (cell.width if mirror in {"MY", "XY"} else 0.0)
        oy = yoffset + (cell.height if mirror in {"MX", "XY"} else 0.0)
        x = -local_x if mirror in {"MY", "XY"} else local_x
        y = -local_y if mirror in {"MX", "XY"} else local_y
        return ox + x, oy + y

    if all(name in arrays for name in ["dummy_left_array", "bitcell_array", "replica_bitline_array", "dummy_right_array"]):
        dummy_left = arrays["dummy_left_array"]
        bitcells = arrays["bitcell_array"]
        replica = arrays["replica_bitline_array"]
        dummy_right = arrays["dummy_right_array"]
        for row in range(rows):
            expected_y = transformed_storage_pin(bitcells, row, 0, bitcell_wl_x, bitcell_wl_y)[1]
            storage_pin_points = [
                ("dummy_left", "dummy_left_array", 0, *transformed_storage_pin(dummy_left, row, 0, dummy_wl_x, dummy_wl_y)),
                *[
                    ("bitcell", "bitcell_array", col, *transformed_storage_pin(bitcells, row, col, bitcell_wl_x, bitcell_wl_y))
                    for col in range(cols)
                ],
                ("replica", "replica_bitline_array", 0, *transformed_storage_pin(replica, row, 0, replica_wl_x, replica_wl_y)),
                ("dummy_right", "dummy_right_array", 0, *transformed_storage_pin(dummy_right, row, 0, dummy_wl_x, dummy_wl_y)),
            ]
            expected_xs = [point[3] for point in storage_pin_points]
            extension = max(tech.layer("m1").min_width, tech.manufacturing_grid)
            entry_keepout = tech.layer("m2").min_space + 0.03
            expected_entry_x = dummy_left.origin.x + tech.cell(dummy_left.cell).bbox_x0 - entry_keepout
            expected_x0 = min(expected_entry_x, min(expected_xs) - extension)
            expected_x1 = max(expected_xs) + extension
            rail = wordline_row_rails.get(row)
            info = {
                "row": row,
                "net": f"wl[{row}]",
                "expected_x0": round(expected_x0, 6),
                "expected_x1": round(expected_x1, 6),
                "expected_y": round(expected_y, 6),
                "present": rail is not None,
            }
            if rail is None:
                wordline_row_checks.append(info)
                violations.append({"type": "missing_wordline_row_rail", **info})
                continue
            actual_y = rail.rect.center.y
            pin_probe = max(tech.layer("m1").min_width, 0.055) / 2.0
            pin_contact_checks = []
            missing_pin_contacts = []
            for role, array_name, col, pin_x, pin_y in storage_pin_points:
                pin_rect = Rect(pin_x - pin_probe, pin_y - pin_probe, pin_x + pin_probe, pin_y + pin_probe)
                contacted = rail.rect.overlaps(pin_rect)
                check = {
                    "role": role,
                    "array": array_name,
                    "column": col,
                    "pin_x": round(pin_x, 6),
                    "pin_y": round(pin_y, 6),
                    "contacted_by_row_rail": contacted,
                }
                pin_contact_checks.append(check)
                if not contacted:
                    missing_pin_contacts.append(check)
            info.update({
                "actual_x0": round(rail.rect.x0, 6),
                "actual_x1": round(rail.rect.x1, 6),
                "actual_y": round(actual_y, 6),
                "covers_storage_family": rail.rect.x0 <= expected_x0 + eps and rail.rect.x1 + eps >= expected_x1,
                "y_delta_um": round(actual_y - expected_y, 6),
                "wl_pin_contact_count": len(pin_contact_checks) - len(missing_pin_contacts),
                "expected_wl_pin_contact_count": len(pin_contact_checks),
                "all_storage_wl_pins_contacted": not missing_pin_contacts,
                "missing_wl_pin_contacts": missing_pin_contacts,
            })
            wordline_row_checks.append(info)
            if rail.rect.x0 > expected_x0 + eps or rail.rect.x1 + eps < expected_x1:
                violations.append({"type": "wordline_row_rail_too_short", **info})
            if abs(actual_y - expected_y) > eps:
                violations.append({"type": "wordline_row_rail_y_misaligned", **info})
            if missing_pin_contacts:
                violations.append({"type": "wordline_row_rail_misses_storage_pins", **info})

    for role in compact_roles:
        by_row: dict[float, list[Instance]] = {}
        for instance in layout.instances:
            if instance.role != role:
                continue
            by_row.setdefault(round(instance.rect.y0, 3), []).append(instance)
        for row_key, row_instances in by_row.items():
            ordered = sorted(row_instances, key=lambda item: item.rect.x0)
            for left, right in zip(ordered, ordered[1:]):
                actual_delta = instance_origin_x(right) - instance_origin_x(left)
                expected_delta = legal_origin_delta_x(left.cell, right.cell)
                extra_delta = round(actual_delta - expected_delta, 6)
                gap_x = round(right.rect.x0 - left.rect.x1, 6)
                info = {
                    "role": role,
                    "row_key": row_key,
                    "left": left.name,
                    "right": right.name,
                    "gap_x_um": gap_x,
                    "origin_delta_x_um": round(actual_delta, 6),
                    "expected_min_legal_origin_delta_x_um": round(expected_delta, 6),
                    "extra_origin_delta_x_um": extra_delta,
                }
                compact_gap_checks.append(info)
                if extra_delta > eps:
                    violations.append({"type": "compact_role_extra_gap", **info})
                elif extra_delta < -eps:
                    violations.append({"type": "compact_role_overlap", **info})

    return {
        "method": (
            "Structural consistency audit: storage cells must physically abut, "
            "column mux/precharge instances must match bitcell columns, BL/BR routes "
            "must align to real bitcell GDS pins, wordline row rails must cover every "
            "dummy/bitcell/replica row and physically intersect every storage WL pin "
            "access point, and compact logic/DFF rows must not contain avoidable "
            "internal gaps."
        ),
        "clean": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "storage_pitch_checks": storage_pitch_checks,
        "column_mux_count": len(column_muxes),
        "precharge_count": len(precharges),
        "expected_column_count": cols,
        "expected_row_count": rows,
        "words_per_row": wpr,
        "missing_mux_indices": missing_mux_indices,
        "extra_mux_indices": extra_mux_indices,
        "missing_precharge_indices": missing_precharge_indices,
        "extra_precharge_indices": extra_precharge_indices,
        "column_alignment": column_alignment,
        "storage_boundary_checks": storage_boundary_checks,
        "wordline_row_rail_count": len(wordline_row_rails),
        "wordline_row_checks": wordline_row_checks,
        "compact_gap_checks": compact_gap_checks,
    }


def _audit_geometry(layout: LayoutDB, tech: Tech) -> dict[str, object]:
    pr_boundary = next(
        (shape.rect for shape in layout.shapes if shape.purpose == "boundary" and shape.name == "prBoundary"),
        layout.bounds,
    )
    outside: list[dict[str, object]] = []

    def contains(container: Rect, target: Rect, eps: float = 1e-9) -> bool:
        return (
            container.x0 <= target.x0 + eps
            and container.y0 <= target.y0 + eps
            and container.x1 + eps >= target.x1
            and container.y1 + eps >= target.y1
        )

    def overlaps_with_tolerance(left: Rect, right: Rect, eps: float = 1e-6) -> bool:
        return not (
            left.x1 <= right.x0 + eps
            or right.x1 <= left.x0 + eps
            or left.y1 <= right.y0 + eps
            or right.y1 <= left.y0 + eps
        )

    storage_stitch_roles = {"bitcell_array", "dummy_bitcell", "replica_bitline"}
    replacement_stitch_roles = {"precharge", "replica_precharge", "column_mux"}

    def legal_openram_physical_overlap(left_role: str, right_role: str) -> bool:
        if left_role in storage_stitch_roles and right_role in storage_stitch_roles:
            return True
        if left_role in replacement_stitch_roles and right_role in replacement_stitch_roles:
            return left_role == right_role or {left_role, right_role} == {"precharge", "replica_precharge"}
        return False

    def record(kind: str, name: str | None, role: str | None, layer: str | None, rect: Rect) -> None:
        if contains(pr_boundary, rect):
            return
        outside.append({
            "kind": kind,
            "name": name or "",
            "role": role or "",
            "layer": layer or "",
            "rect": rect.to_dict(),
        })

    for shape in layout.shapes:
        record("shape", shape.name, shape.purpose, shape.layer, shape.rect)
    for instance in layout.instances:
        record("instance", instance.name, instance.role, instance.cell, instance.rect)
    for array in layout.cell_arrays:
        record("cell_array", array.name, array.role, array.cell, array.rect)

    cell_array_pitch_violations: list[dict[str, object]] = []
    allowed_cell_array_pitch_shortfalls: list[dict[str, object]] = []
    for array in layout.cell_arrays:
        cell = tech.cells.get(array.cell)
        if cell is None:
            continue
        physical_cell_width = max(cell.width, cell.bbox_x1 - cell.bbox_x0)
        physical_cell_height = max(cell.height, cell.bbox_y1 - cell.bbox_y0)
        pitch_x_shortfall = max(0.0, physical_cell_width - array.pitch_x)
        pitch_y_shortfall = max(0.0, physical_cell_height - array.pitch_y)
        if pitch_x_shortfall > 1e-9 or pitch_y_shortfall > 1e-9:
            item = {
                "array": array.name,
                "cell": array.cell,
                "role": array.role,
                "columns": array.columns,
                "rows": array.rows,
                "pitch_x": array.pitch_x,
                "pitch_y": array.pitch_y,
                "physical_cell_width": physical_cell_width,
                "physical_cell_height": physical_cell_height,
                "pitch_x_shortfall_um": round(pitch_x_shortfall, 6),
                "pitch_y_shortfall_um": round(pitch_y_shortfall, 6),
            }
            if array.role in storage_stitch_roles and abs(array.pitch_x - cell.width) <= 1e-9 and abs(array.pitch_y - cell.height) <= 1e-9:
                item["reason"] = "openram_logical_pitch_with_physical_boundary_stitching"
                allowed_cell_array_pitch_shortfalls.append(item)
            else:
                cell_array_pitch_violations.append(item)

    hard_regions: list[tuple[str, str, Rect]] = []
    for array in layout.cell_arrays:
        hard_regions.append((array.name, array.role or array.cell, array.rect))
    for instance in layout.instances:
        if not instance.cell.startswith("gen_"):
            hard_regions.append((instance.name, instance.role or instance.cell, instance.rect))

    placed_regions: list[tuple[str, str, str, Rect]] = []
    for array in layout.cell_arrays:
        placed_regions.append(("cell_array", array.name, array.role or array.cell, array.rect))
    for instance in layout.instances:
        placed_regions.append(("instance", instance.name, instance.role or instance.cell, instance.rect))

    placed_cell_overlaps: list[dict[str, object]] = []
    allowed_placed_cell_overlaps: list[dict[str, object]] = []
    for i, left in enumerate(placed_regions):
        left_kind, left_name, left_role, left_rect = left
        for right_kind, right_name, right_role, right_rect in placed_regions[i + 1:]:
            if not overlaps_with_tolerance(left_rect, right_rect):
                continue
            item = {
                "a_kind": left_kind,
                "a_name": left_name,
                "a_role": left_role,
                "a_rect": left_rect.to_dict(),
                "b_kind": right_kind,
                "b_name": right_name,
                "b_role": right_role,
                "b_rect": right_rect.to_dict(),
            }
            if legal_openram_physical_overlap(left_role, right_role):
                item["reason"] = "openram_boundary_stitching"
                allowed_placed_cell_overlaps.append(item)
                continue
            placed_cell_overlaps.append(item)

    generated_hardcell_overlaps: list[dict[str, object]] = []
    generated_hardcell_spacing: list[dict[str, object]] = []
    min_generated_hardcell_spacing_um = 0.0
    for instance in layout.instances:
        if not instance.cell.startswith("gen_"):
            continue
        for hard_name, hard_role, hard_rect in hard_regions:
            spacing = instance.rect.spacing_to(hard_rect)
            if instance.rect.overlaps(hard_rect):
                generated_hardcell_overlaps.append({
                    "generated_instance": instance.name,
                    "generated_role": instance.role,
                    "generated_rect": instance.rect.to_dict(),
                    "hardcell": hard_name,
                    "hardcell_role": hard_role,
                    "hardcell_rect": hard_rect.to_dict(),
                })
            elif spacing < min_generated_hardcell_spacing_um:
                generated_hardcell_spacing.append({
                    "generated_instance": instance.name,
                    "generated_role": instance.role,
                    "hardcell": hard_name,
                    "hardcell_role": hard_role,
                    "spacing_um": round(spacing, 6),
                })

    modules = {shape.name: shape.rect for shape in layout.shapes if shape.purpose == "module" and shape.name}
    data_overhangs: list[dict[str, object]] = []
    allowed_data_overhangs: list[dict[str, object]] = []
    data_dff = modules.get("data_dff_array")
    data_path = modules.get("SA_SWITCH_LATCH_MUX")
    if data_dff is not None and data_path is not None and data_dff.x1 > data_path.x1 + 1e-9:
        item = {
            "module": "data_dff_array",
            "reference": "SA_SWITCH_LATCH_MUX",
            "overhang_um": round(data_dff.x1 - data_path.x1, 6),
            "module_rect": data_dff.to_dict(),
            "reference_rect": data_path.to_dict(),
        }
        if layout.metadata.get("data_dff_packing_strategy") == "global macro area search" and contains(pr_boundary, data_dff):
            item["reason"] = "occupancy_guided_global_data_dff_packing"
            allowed_data_overhangs.append(item)
        else:
            data_overhangs.append(item)

    return {
        "pr_boundary": pr_boundary.to_dict(),
        "objects_outside_pr_boundary": outside,
        "objects_outside_pr_boundary_count": len(outside),
        "data_periphery_overhangs": data_overhangs,
        "data_periphery_overhang_count": len(data_overhangs),
        "allowed_data_periphery_overhangs": allowed_data_overhangs,
        "allowed_data_periphery_overhang_count": len(allowed_data_overhangs),
        "cell_array_pitch_violations": cell_array_pitch_violations,
        "cell_array_pitch_violation_count": len(cell_array_pitch_violations),
        "allowed_cell_array_pitch_shortfalls": allowed_cell_array_pitch_shortfalls,
        "allowed_cell_array_pitch_shortfall_count": len(allowed_cell_array_pitch_shortfalls),
        "placed_cell_overlaps": placed_cell_overlaps,
        "placed_cell_overlap_count": len(placed_cell_overlaps),
        "allowed_placed_cell_overlaps": allowed_placed_cell_overlaps,
        "allowed_placed_cell_overlap_count": len(allowed_placed_cell_overlaps),
        "generated_hardcell_overlaps": generated_hardcell_overlaps,
        "generated_hardcell_overlap_count": len(generated_hardcell_overlaps),
        "generated_hardcell_min_spacing_um": min_generated_hardcell_spacing_um,
        "generated_hardcell_spacing_violations": generated_hardcell_spacing,
        "generated_hardcell_spacing_violation_count": len(generated_hardcell_spacing),
        "generated_hardcell_spacing_is_advisory": False,
        "clean": (
            not outside
            and not data_overhangs
            and not cell_array_pitch_violations
            and not placed_cell_overlaps
            and not generated_hardcell_overlaps
            and not generated_hardcell_spacing
        ),
    }


def _audit_cell_bboxes(tech: Tech, used_gds_cells: list[str]) -> dict[str, object]:
    cells: dict[str, dict[str, object]] = {}
    cells_with_marker_underestimate: list[str] = []
    cells_without_marker: list[str] = []

    def overhang(geometry: dict[str, object], marker: dict[str, object]) -> dict[str, float]:
        return {
            "left_um": round(max(0.0, float(marker["x0"]) - float(geometry["x0"])), 6),
            "bottom_um": round(max(0.0, float(marker["y0"]) - float(geometry["y0"])), 6),
            "right_um": round(max(0.0, float(geometry["x1"]) - float(marker["x1"])), 6),
            "top_um": round(max(0.0, float(geometry["y1"]) - float(marker["y1"])), 6),
        }

    for cell_name in used_gds_cells:
        cell = tech.cell(cell_name)
        selected = {
            "x0": cell.bbox_x0,
            "y0": cell.bbox_y0,
            "x1": cell.bbox_x1,
            "y1": cell.bbox_y1,
            "width": cell.width,
            "height": cell.height,
        }
        geometry = cell.geometry_bbox
        marker = cell.marker_bbox
        marker_overhang = None
        marker_underestimates_geometry = False
        if geometry is not None and marker is not None:
            marker_overhang = overhang(geometry, marker)
            marker_underestimates_geometry = any(value > 1e-9 for value in marker_overhang.values())
            if marker_underestimates_geometry:
                cells_with_marker_underestimate.append(cell_name)
        elif marker is None:
            cells_without_marker.append(cell_name)
        cells[cell_name] = {
            "bbox_source_used_for_placement": cell.bbox_source,
            "selected_bbox": selected,
            "logical_pitch": {"width": cell.width, "height": cell.height},
            "physical_bbox": {
                "x0": cell.bbox_x0,
                "y0": cell.bbox_y0,
                "x1": cell.bbox_x1,
                "y1": cell.bbox_y1,
            },
            "physical_geometry_bbox_excluding_text_layer": geometry,
            "text_marker_bbox_239": marker,
            "marker_underestimates_geometry": marker_underestimates_geometry,
            "geometry_overhang_beyond_marker": marker_overhang,
        }
    return {
        "method": (
            "OpenRAM-style dynamic GDS measurement: use the 239/text marker as logical placement "
            "pitch/origin when present, and keep the real drawn-geometry bbox for boundary and "
            "overhang audits."
        ),
        "placement_uses_logical_marker_pitch": True,
        "audit_uses_physical_geometry": True,
        "cells_with_marker_underestimate": cells_with_marker_underestimate,
        "cells_without_text_marker": cells_without_marker,
        "cells": cells,
    }


def _audit_cell_array_mirroring(layout: LayoutDB) -> dict[str, object]:
    expected_mirror_x_roles = {"bitcell_array", "dummy_bitcell", "replica_bitline"}
    openyield_aggregation = layout.metadata.get("openyield_array_aggregation_integration", {})
    openyield_storage_enabled = bool(openyield_aggregation.get("enabled"))
    openyield_storage_policy = str(openyield_aggregation.get("row_orientation_policy", "all_r0"))
    openyield_storage_r0 = openyield_storage_enabled and openyield_storage_policy == "all_r0"
    openyield_storage_names = {"bitcell_array", "dummy_left_array", "dummy_right_array", "replica_bitline_array"}
    arrays: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    for array in layout.cell_arrays:
        expected_openram_row_mirror = array.role in expected_mirror_x_roles and not (
            openyield_storage_r0 and array.name in openyield_storage_names
        )
        info = {
            "array": array.name,
            "cell": array.cell,
            "role": array.role,
            "columns": array.columns,
            "rows": array.rows,
            "mirror_x": array.mirror_x,
            "mirror_y": array.mirror_y,
            "row_offset": array.row_offset,
            "column_offset": array.column_offset,
            "expected_openram_row_mirror": expected_openram_row_mirror,
            "openyield_storage_r0_exception": openyield_storage_r0 and array.name in openyield_storage_names,
            "openyield_storage_policy": openyield_storage_policy if openyield_storage_enabled and array.name in openyield_storage_names else None,
        }
        arrays.append(info)
        if info["expected_openram_row_mirror"] and array.rows > 1 and not array.mirror_x:
            missing.append(info)
    return {
        "method": (
            "OpenRAM FreePDK45 bitcell placement mirror.x=True, mirror.y=False: "
            "alternate rows use MX while columns remain R0. When limited OpenYield "
            "storage aggregation is explicitly enabled, storage cells follow the "
            "configured row_orientation_policy while keeping peripheral arrays on "
            "the legacy path."
        ),
        "clean": not missing,
        "missing_required_row_mirror_count": len(missing),
        "missing_required_row_mirror": missing,
        "arrays": arrays,
    }


def _audit_macro_replacements(tech: Tech, macro_instances: dict[str, int]) -> dict[str, object]:
    macros: dict[str, dict[str, object]] = {}
    physical_count = 0
    missing_physical_count = 0
    for cell_name, count in sorted(macro_instances.items()):
        cell = tech.cell(cell_name)
        has_physical_gds = bool(cell.gds_path)
        if has_physical_gds:
            physical_count += 1
        else:
            missing_physical_count += 1
        macros[cell_name] = {
            "instance_count": count,
            "width": cell.width,
            "height": cell.height,
            "role": cell.role,
            "placement_bbox_source": cell.bbox_source,
            "gds_path": cell.gds_path,
            "spice_path": cell.spice_path,
            "has_physical_gds": has_physical_gds,
            "replacement_contract": (
                "provide a FreePDK45-compatible GDS/SPICE pair with the same cell name, "
                "pin names from the pin model, and a measured bbox that fits this slot or "
                "update the macro dimensions in the registry"
            ),
        }
    return {
        "method": (
            "Replaceable peripheral macros are emitted only as physical OpenRAM/FreePDK45 GDS references. "
            "A future optimized decoder, wordline driver, mux, or control primitive can replace the GDS/SPICE "
            "behind the same named contract; missing physical macros are reported rather than drawn as fake cells."
        ),
        "manifest": (tech.reference_files.get("replacement_macros") or [None])[0],
        "macro_cell_count": len(macros),
        "abstract_macro_count": missing_physical_count,
        "physical_macro_count": physical_count,
        "missing_physical_macro_count": missing_physical_count,
        "all_used_macros_have_physical_gds": missing_physical_count == 0,
        "physical_gds_emitted_for_abstract_macros": missing_physical_count == 0,
        "macros": macros,
    }


def _audit_openram_cell_sources(
    tech: Tech,
    used_gds_cells: list[str],
    generated_instances: dict[str, int],
    abstract_instances: dict[str, int],
) -> dict[str, object]:
    cells: dict[str, dict[str, object]] = {}
    missing_gds: list[str] = []
    synthetic_generated_gds: list[str] = []
    generated_fallback_cells = sorted(generated_instances)
    abstract_cells = sorted(abstract_instances)
    for cell_name in used_gds_cells:
        cell = tech.cell(cell_name)
        gds_path = Path(str(cell.gds_path)).resolve() if cell.gds_path else None
        source = "bundled_freepdk45_hardcell"
        if cell_name.startswith("gen_"):
            if gds_path is not None and "openram_replacements" in gds_path.parts:
                source = "openram_extracted_replacement_gds"
            else:
                source = "synthetic_generated_gds"
                synthetic_generated_gds.append(cell_name)
        if gds_path is None:
            missing_gds.append(cell_name)
        cells[cell_name] = {
            "role": cell.role,
            "gds_path": str(gds_path) if gds_path is not None else None,
            "source": source,
            "measured_from_gds": cell.measured_from_gds,
            "bbox_source": cell.bbox_source,
        }
    return {
        "method": (
            "All cells instantiated in the top GDS must be imported FreePDK45/OpenRAM GDS. "
            "Generated helper cells are accepted only when they are OpenRAM-extracted replacement macros; "
            "fallback rectangle-drawn stdcell geometry is not signoff-eligible."
        ),
        "clean": not missing_gds and not synthetic_generated_gds and not generated_fallback_cells and not abstract_cells,
        "used_gds_cell_count": len(used_gds_cells),
        "missing_gds_cells": missing_gds,
        "synthetic_generated_gds_cells": sorted(set(synthetic_generated_gds)),
        "generated_fallback_cells": generated_fallback_cells,
        "abstract_cells": abstract_cells,
        "cells": cells,
    }


def _audit_cell_array_layer_abutment(tech: Tech, layout: LayoutDB) -> dict[str, object]:
    """Check OpenRAM-style cell-array pitch against real per-layer GDS extents.

    Generic generated-cell arrays must not overlap. Native OpenRAM storage
    arrays are different: their abstract pitch intentionally lets some GDS
    layers extend past the module boundary so adjacent bitcells stitch into a
    continuous fabric. Those storage overlaps are reported as designed
    stitching and external DRC is used as the final legality check.
    """

    layer_names = [
        "pwell",
        "nwell",
        "nimplant",
        "pimplant",
        "vtg",
        "vth",
        "thkox",
        "active",
        "poly",
        "contact",
        "m1",
        "via1",
        "m2",
        "via2",
        "m3",
        "via3",
        "m4",
    ]
    eps = max(tech.manufacturing_grid * 0.5, 1e-9)
    layer_bbox_cache: dict[tuple[str, str], object | None] = {}
    arrays: list[dict[str, object]] = []
    violations: list[dict[str, object]] = []
    storage_family_cells = {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}

    def layer_bbox(cell_name: str, layer_name: str):
        key = (cell_name, layer_name)
        if key in layer_bbox_cache:
            return layer_bbox_cache[key]
        cell = tech.cell(cell_name)
        layer = tech.layer(layer_name)
        bbox = measure_gds_bbox(Path(str(cell.gds_path)), boundary_layers={layer.gds_layer}) if cell.gds_path else None
        layer_bbox_cache[key] = bbox
        return bbox

    def axis_status(gap: float) -> str:
        if gap < -eps:
            return "overlap"
        if abs(gap) <= eps:
            return "abut"
        return "spaced"

    def required_pitch_gap(layer_name: str) -> float:
        layer = tech.layer(layer_name)
        if layer_name in {"pwell", "nwell"}:
            return max(layer.min_space, layer.min_width)
        return layer.min_space

    for array in layout.cell_arrays:
        if array.cell not in tech.cells:
            continue
        cell = tech.cell(array.cell)
        if not cell.gds_path:
            continue
        layer_summaries: dict[str, dict[str, object]] = {}
        for layer_name in layer_names:
            if layer_name not in tech.layers:
                continue
            bbox = layer_bbox(array.cell, layer_name)
            if bbox is None:
                continue
            check_x = array.columns > 1
            check_y = array.rows > 1
            gap_x = round(array.pitch_x - bbox.width, 6) if check_x else None
            gap_y = round(array.pitch_y - bbox.height, 6) if check_y else None
            overlap_x = round(max(0.0, bbox.width - array.pitch_x), 6) if check_x else 0.0
            overlap_y = round(max(0.0, bbox.height - array.pitch_y), 6) if check_y else 0.0
            info = {
                "gds_layer": tech.layer(layer_name).gds_layer,
                "bbox": bbox.to_dict(),
                "pitch_x": array.pitch_x,
                "pitch_y": array.pitch_y,
                "horizontal_status": axis_status(float(gap_x)) if gap_x is not None else "single_column",
                "vertical_status": axis_status(float(gap_y)) if gap_y is not None else "single_row",
                "horizontal_gap_um": gap_x,
                "vertical_gap_um": gap_y,
                "horizontal_overlap_um": overlap_x,
                "vertical_overlap_um": overlap_y,
            }
            layer_summaries[layer_name] = info
            min_space_x = required_pitch_gap(layer_name) if check_x else 0.0
            min_space_y = required_pitch_gap(layer_name) if check_y else 0.0
            bad_gap_x = gap_x is not None and (float(gap_x) < -eps or eps < float(gap_x) < min_space_x - eps)
            bad_gap_y = gap_y is not None and (float(gap_y) < -eps or eps < float(gap_y) < min_space_y - eps)
            if array.cell in storage_family_cells:
                bad_gap_x = False
                bad_gap_y = False
                info["openram_storage_stitching_allowed"] = True
            if bad_gap_x or bad_gap_y:
                violations.append({
                    "array": array.name,
                    "cell": array.cell,
                    "role": array.role,
                    "layer": layer_name,
                    "columns": array.columns,
                    "rows": array.rows,
                    **info,
                })
        arrays.append({
            "array": array.name,
            "cell": array.cell,
            "role": array.role,
            "columns": array.columns,
            "rows": array.rows,
            "pitch_x": array.pitch_x,
            "pitch_y": array.pitch_y,
            "logical_cell_width": cell.width,
            "logical_cell_height": cell.height,
            "physical_bbox": {
                "x0": cell.bbox_x0,
                "y0": cell.bbox_y0,
                "x1": cell.bbox_x1,
                "y1": cell.bbox_y1,
            },
            "layers": layer_summaries,
        })

    return {
        "method": (
            "Array occupancy audit: generic repeated cells must not overlap, while native "
            "OpenRAM storage cells may use designed boundary stitching at abstract bitcell pitch; "
            "external KLayout DRC remains the final legality check."
        ),
        "epsilon_um": eps,
        "array_count": len(arrays),
        "illegal_layer_overlap_count": len(violations),
        "illegal_layer_overlaps": violations,
        "clean": not violations,
        "arrays": arrays,
    }


def _write_architecture_svg(layout: LayoutDB, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bounds = layout.bounds.inflate(0.8)
    scale = 16.0
    width = max(1.0, bounds.width * scale)
    height = max(1.0, bounds.height * scale)

    def sx(x: float) -> float:
        return (x - bounds.x0) * scale

    def sy(y: float) -> float:
        return height - (y - bounds.y0) * scale

    featured = {
        "ARRAY_TOP",
        "ARRAY_BOT",
        "RBL",
        "WL_DRIVER",
        "WL_DRIVER_CHANNEL",
        "DECODER",
        "TIMING_CONTROL",
        "SA_SWITCH_LATCH_MUX",
    }
    colors = {
        "ARRAY_TOP": "#21d2d6",
        "ARRAY_BOT": "#21d2d6",
        "RBL": "#d7f3ff",
        "WL_DRIVER": "#f29b39",
        "WL_DRIVER_CHANNEL": "#f9c46b",
        "DECODER": "#c9b2ff",
        "TIMING_CONTROL": "#92d6a4",
        "SA_SWITCH_LATCH_MUX": "#95e0c8",
    }
    modules = [shape for shape in layout.shapes if shape.purpose == "module" and shape.name in featured]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height:.1f}" viewBox="0 0 {width:.1f} {height:.1f}">',
        '<rect width="100%" height="100%" fill="#101010"/>',
    ]
    for shape in modules:
        rect = shape.rect
        label = _architecture_label(shape.name or "")
        x = sx(rect.x0)
        y = sy(rect.y1)
        w = rect.width * scale
        h = rect.height * scale
        color = colors.get(shape.name or "", "#dddddd")
        lines.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'fill="{color}" fill-opacity="0.72" stroke="#f4f4f4" stroke-width="1.2"/>'
        )
        font_size = max(9.0, min(24.0, min(w / max(len(label), 1) * 1.6, h * 0.28)))
        label_w = min(w * 0.82, max(54.0, len(label) * font_size * 0.56))
        label_h = min(h * 0.65, max(20.0, font_size * 1.55))
        label_x = x + (w - label_w) / 2.0
        label_y = y + (h - label_h) / 2.0
        lines.append(
            f'<rect x="{label_x:.2f}" y="{label_y:.2f}" width="{label_w:.2f}" height="{label_h:.2f}" '
            'fill="#ffffff" stroke="#111111" stroke-width="0.8"/>'
        )
        lines.append(
            f'<text x="{x + w / 2.0:.2f}" y="{label_y + label_h / 2.0 + font_size * 0.35:.2f}" '
            f'font-family="Times New Roman, serif" font-size="{font_size:.2f}" font-weight="700" '
            f'text-anchor="middle" fill="#000000">{escape(label)}</text>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def _architecture_label(name: str) -> str:
    labels = {
        "ARRAY_TOP": "ARRAY_TOP",
        "ARRAY_BOT": "ARRAY_BOT",
        "RBL": "RBL",
        "WL_DRIVER": "WL_DRIVER",
        "WL_DRIVER_CHANNEL": "WL_CHANNEL",
        "DECODER": "DECODER",
        "TIMING_CONTROL": "TIMING CONTROL",
        "SA_SWITCH_LATCH_MUX": "SA SWITCH LATCH MUX",
    }
    return labels.get(name, name)


def _audit_layers(tech: Tech, gds: Path, route_guide_gds: Path) -> dict:
    known_lpps = {
        f"{layer.gds_layer}/{layer.datatype}": {
            "internal_name": name,
            "lef_name": layer.lef_name,
            "routable": layer.routable,
        }
        for name, layer in sorted(tech.layers.items())
    }
    for name, layer in sorted(tech.layers.items()):
        if not layer.routable:
            continue
        known_lpps[f"{layer.gds_layer}/1"] = {
            "internal_name": f"{name}_label",
            "lef_name": f"{layer.lef_name}_lbl",
            "routable": False,
        }
        known_lpps[f"{layer.gds_layer}/2"] = {
            "internal_name": f"{name}_pin",
            "lef_name": f"{layer.lef_name}_pin",
            "routable": False,
        }
    clean_layers = inspect_gds_layers(gds)
    guide_layers = inspect_gds_layers(route_guide_gds)

    def unknown(layer_counts: dict[str, int]) -> list[str]:
        return sorted(lpp for lpp in layer_counts if lpp not in known_lpps)

    return {
        "known_lpps": known_lpps,
        "clean_gds_layers": clean_layers,
        "route_guide_gds_layers": guide_layers,
        "unknown_clean_boundary_lpps": unknown(clean_layers["boundary"]),
        "unknown_clean_text_lpps": unknown(clean_layers["text"]),
        "unknown_route_guide_boundary_lpps": unknown(guide_layers["boundary"]),
        "unknown_route_guide_text_lpps": unknown(guide_layers["text"]),
        "matches_bundled_freepdk45_layers": not (
            unknown(clean_layers["boundary"])
            or unknown(clean_layers["text"])
            or unknown(guide_layers["boundary"])
            or unknown(guide_layers["text"])
        ),
    }


def _inspect_hardcell_pin_access(tech: Tech, used_gds_cells: list[str]) -> dict:
    cells: dict[str, dict[str, object]] = {}
    for cell_name in used_gds_cells:
        cell = tech.cell(cell_name)
        if not cell.gds_path:
            continue
        records = inspect_gds_text_records(Path(cell.gds_path))
        pins: dict[str, list[dict[str, object]]] = {}
        for record in records:
            text = str(record["text"])
            pins.setdefault(text, []).append(
                {
                    "lpp": record["lpp"],
                    "x": record["x"],
                    "y": record["y"],
                }
            )
        cells[cell_name] = {
            "pin_count": sum(len(items) for items in pins.values()),
            "unique_pins": sorted(pins),
            "pins": {name: pins[name] for name in sorted(pins)},
        }
    return {
        "source": "GDS TEXT records from bundled hardcell libraries",
        "cells": cells,
    }


def _inspect_generated_pin_access(tech: Tech, generated_instances: dict[str, int]) -> dict:
    cells: dict[str, dict[str, object]] = {}
    for cell_name in sorted(generated_instances):
        cell = tech.cell(cell_name)
        pins = generated_cell_pins(cell_name, Rect(0.0, 0.0, cell.width, cell.height))
        cells[cell_name] = {
            "pin_count": len(pins),
            "unique_pins": sorted(str(pin["name"]) for pin in pins),
            "pins": [
                {
                    "name": pin["name"],
                    "layer": pin["layer"],
                    "x": pin["x"],
                    "y": pin["y"],
                }
                for pin in pins
            ],
        }
    return {
        "source": "generated stdcell pin model emitted as GDS TEXT records",
        "cells": cells,
    }


def _promote_drc_clean_guides(layout: LayoutDB, tech: Tech) -> dict:
    initial_guides = [shape for shape in layout.shapes if shape.purpose == "route_guide"]
    if layout.metadata.get("formal_gds_keeps_guides_separate", True):
        return {
            "initial_route_guides": len(initial_guides),
            "promoted_to_routes": 0,
            "remaining_route_guides": len(initial_guides),
            "promoted_by_layer": {},
            "remaining_by_layer": _count_shapes_by_layer(initial_guides),
            "blocked_by_reason": {"formal_gds_keeps_guides_separate_until_obstruction_aware_routing": len(initial_guides)},
            "promoted_examples": [],
            "blocked_examples": [
                {
                    "layer": shape.layer,
                    "net": shape.net,
                    "name": shape.name,
                    "reason": "formal_gds_keeps_guides_separate_until_obstruction_aware_routing",
                }
                for shape in initial_guides[:20]
            ],
        }
    promoted: list[dict[str, object]] = []
    blocked: list[dict[str, object]] = []

    def record(shape, reason: str, promoted_shape: bool) -> None:
        item = {
            "layer": shape.layer,
            "net": shape.net,
            "name": shape.name,
            "reason": reason,
        }
        if promoted_shape:
            promoted.append(item)
        else:
            blocked.append(item)

    for shape in initial_guides:
        if shape.layer in tech.vias:
            continue
        if _shape_can_be_promoted_to_route(layout, tech, shape):
            shape.purpose = "route"
            record(shape, "drc_clean", True)
        else:
            record(shape, "same-layer spacing conflict", False)

    for shape in initial_guides:
        if shape.purpose != "route_guide" or shape.layer not in tech.vias:
            continue
        if not _via_guide_has_drawn_stack(layout, tech, shape):
            record(shape, "missing drawn upper/lower route stack", False)
            continue
        if _shape_can_be_promoted_to_route(layout, tech, shape):
            shape.purpose = "route"
            record(shape, "drc_clean_stack", True)
        else:
            record(shape, "same-layer spacing conflict", False)

    remaining = [shape for shape in layout.shapes if shape.purpose == "route_guide"]
    return {
        "initial_route_guides": len(initial_guides),
        "promoted_to_routes": len(promoted),
        "remaining_route_guides": len(remaining),
        "promoted_by_layer": _count_items_by_key(promoted, "layer"),
        "remaining_by_layer": _count_shapes_by_layer(remaining),
        "blocked_by_reason": _count_items_by_key(blocked, "reason"),
        "promoted_examples": promoted[:20],
        "blocked_examples": blocked[:20],
    }


def _shape_can_be_promoted_to_route(layout: LayoutDB, tech: Tech, candidate) -> bool:
    layer = tech.layers.get(candidate.layer)
    if layer is None or candidate.rect.area <= 0.0:
        return False
    width = min(candidate.rect.width, candidate.rect.height)
    if width + 1e-9 < layer.min_width:
        return False
    is_pin_landing = any(_candidate_is_generated_pin_landing(tech, candidate, instance) for instance in layout.instances)
    if not layer.routable and not is_pin_landing:
        return False
    for hard_rect in [array.rect for array in layout.cell_arrays]:
        if candidate.rect.overlaps(hard_rect) or candidate.rect.spacing_to(hard_rect) + 1e-9 < layer.min_space:
            return False
    for instance in layout.instances:
        if is_pin_landing and _candidate_is_generated_pin_landing(tech, candidate, instance):
            continue
        if candidate.rect.overlaps(instance.rect) or candidate.rect.spacing_to(instance.rect) + 1e-9 < layer.min_space:
            return False
    for shape in layout.shapes:
        if shape is candidate or shape.layer != candidate.layer:
            continue
        if shape.purpose in {"boundary", "pin", "stdcell", "module", "route_guide", "debug_probe"}:
            continue
        if bool(candidate.net and shape.net and candidate.net == shape.net):
            continue
        if candidate.rect.spacing_to(shape.rect) + 1e-9 < layer.min_space:
            return False
    return True


def _hardcell_keepout_rects(layout: LayoutDB) -> list[Rect]:
    rects = [array.rect for array in layout.cell_arrays]
    rects.extend(instance.rect for instance in layout.instances)
    return rects


def _candidate_is_generated_pin_landing(tech: Tech, candidate, instance: Instance) -> bool:
    if not instance.cell.startswith("gen_"):
        return False
    if candidate.purpose != "route_guide" or not candidate.name or "access" not in candidate.name:
        return False
    for pin in generated_instance_pins(tech, instance):
        if str(pin["layer"]) != candidate.layer:
            continue
        probe = Rect(
            float(pin["x"]) - 0.07,
            float(pin["y"]) - 0.07,
            float(pin["x"]) + 0.07,
            float(pin["y"]) + 0.07,
        )
        if candidate.rect.overlaps(probe):
            return True
    return False


def _via_guide_has_drawn_stack(layout: LayoutDB, tech: Tech, via_shape) -> bool:
    via_rule = tech.vias.get(via_shape.layer)
    if via_rule is None:
        return False
    lower_hit = False
    upper_hit = False
    required_cover = via_shape.rect.inflate(via_rule.enclosure)
    for shape in layout.shapes:
        if shape.purpose != "route" or shape.net != via_shape.net:
            continue
        if shape.layer == via_rule.lower and _rect_contains(shape.rect, required_cover):
            lower_hit = True
        elif shape.layer == via_rule.upper and _rect_contains(shape.rect, required_cover):
            upper_hit = True
    return lower_hit and upper_hit


def _rect_contains(container: Rect, target: Rect, eps: float = 1e-9) -> bool:
    return (
        container.x0 <= target.x0 + eps
        and container.y0 <= target.y0 + eps
        and container.x1 + eps >= target.x1
        and container.y1 + eps >= target.y1
    )


def _count_items_by_key(items: list[dict[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _count_shapes_by_layer(shapes) -> dict[str, int]:
    counts: dict[str, int] = {}
    for shape in shapes:
        counts[shape.layer] = counts.get(shape.layer, 0) + 1
    return dict(sorted(counts.items()))


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _audit_generated_connectivity(layout: LayoutDB, include_guides: bool) -> dict:
    generated_roles = sorted(
        {instance.role for instance in layout.instances if instance.cell.startswith("gen_") and instance.role}
    )
    allowed_purposes = {"route", "route_guide"} if include_guides else {"route"}
    route_shapes = [shape for shape in layout.shapes if shape.purpose in allowed_purposes and shape.net]
    touch_key = "instances_touched_by_routes_or_guides" if include_guides else "instances_touched_by_routes"
    missing_key = "roles_with_no_route_or_guide_touch" if include_guides else "roles_with_no_route_touch"
    partial_key = "roles_with_partial_route_or_guide_touch" if include_guides else "roles_with_partial_route_touch"
    all_key = "all_generated_roles_touched" if include_guides else "all_generated_roles_touched_by_routes"
    by_role: dict[str, dict[str, object]] = {}
    for role in generated_roles:
        instances = [instance for instance in layout.instances if instance.role == role]
        touched = set()
        nets = set()
        for instance in instances:
            probe = instance.rect.inflate(0.08)
            for shape in route_shapes:
                if probe.overlaps(shape.rect):
                    touched.add(instance.name)
                    if shape.net:
                        nets.add(shape.net)
        by_role[role] = {
            "instances": len(instances),
            touch_key: len(touched),
            "instances_touched": len(touched),
            "coverage": len(touched) / len(instances) if instances else 0.0,
            "nets": sorted(nets),
        }
    missing_roles = [role for role, info in by_role.items() if info["coverage"] == 0.0]
    partial_roles = [role for role, info in by_role.items() if 0.0 < info["coverage"] < 1.0]
    return {
        "method": (
            "bbox intersection between generated instances and top-level route/route_guide shapes"
            if include_guides
            else "bbox intersection between generated instances and drawn top-level route shapes"
        ),
        "allowed_purposes": sorted(allowed_purposes),
        "by_role": by_role,
        missing_key: missing_roles,
        partial_key: partial_roles,
        all_key: not missing_roles and not partial_roles,
    }


def _audit_generated_pin_coverage(layout: LayoutDB, tech: Tech, allowed_purposes: set[str]) -> dict[str, object]:
    route_shapes = [shape for shape in layout.shapes if shape.purpose in allowed_purposes and shape.net]
    by_role: dict[str, dict[str, object]] = {}
    missing: list[dict[str, object]] = []
    total = 0
    covered = 0
    pin_probe = 0.055
    for instance in sorted((inst for inst in layout.instances if inst.cell.startswith("gen_")), key=lambda item: item.name):
        role = instance.role or instance.cell
        role_info = by_role.setdefault(role, {"signal_pins": 0, "covered_signal_pins": 0, "missing_signal_pins": 0})
        for pin in generated_instance_pins(tech, instance):
            pin_name = str(pin["name"])
            if pin_name in {"gnd", "vdd"}:
                continue
            total += 1
            role_info["signal_pins"] = int(role_info["signal_pins"]) + 1
            pin_rect = Rect(
                float(pin["x"]) - pin_probe,
                float(pin["y"]) - pin_probe,
                float(pin["x"]) + pin_probe,
                float(pin["y"]) + pin_probe,
            )
            hits = [shape for shape in route_shapes if shape.rect.overlaps(pin_rect)]
            if hits:
                covered += 1
                role_info["covered_signal_pins"] = int(role_info["covered_signal_pins"]) + 1
            else:
                role_info["missing_signal_pins"] = int(role_info["missing_signal_pins"]) + 1
                missing.append({
                    "instance": instance.name,
                    "role": role,
                    "cell": instance.cell,
                    "pin": pin_name,
                    "layer": str(pin["layer"]),
                    "x": round(float(pin["x"]), 6),
                    "y": round(float(pin["y"]), 6),
                })
    for info in by_role.values():
        pins = int(info["signal_pins"])
        info["coverage"] = int(info["covered_signal_pins"]) / pins if pins else 1.0
    return {
        "method": "generated stdcell signal pin probe intersection with selected top-level geometry",
        "allowed_purposes": sorted(allowed_purposes),
        "signal_pins": total,
        "covered_signal_pins": covered,
        "missing_signal_pins": total - covered,
        "coverage": covered / total if total else 1.0,
        "all_generated_signal_pins_covered": total == covered,
        "by_role": by_role,
        "missing_examples": missing[:40],
    }


def _format_report_md(metrics: dict) -> str:
    lines = [
        f"# {metrics['name']} Report",
        "",
        f"- Backend: `{metrics['backend']}`",
        f"- Spec: {metrics['word_size']} x {metrics['num_words']}, words/row={metrics['words_per_row']}",
        f"- Legal words/row choices: `{', '.join(str(item) for item in metrics.get('legal_words_per_row', []))}`",
        f"- Size: {metrics['width_um']:.4f} um x {metrics['height_um']:.4f} um",
        f"- Macro area: {metrics['macro_area_um2']:.4f} um^2",
        f"- Useful array area: {metrics['useful_array_area_um2']:.4f} um^2",
        f"- Utilization: {metrics['utilization']:.2%}",
        f"- Built-in DRC-lite: {'clean' if metrics['drc_clean'] else 'violations'} ({metrics['drc_violation_count']})",
        f"- Full signoff-candidate GDS: `{metrics['gds']}`",
        f"- Presentation GDS: `{metrics.get('presentation_gds', 'none')}`",
        f"- Complete visual-routing GDS: `{metrics.get('complete_gds', 'none')}`",
        f"- Debug GDS: `{metrics.get('debug_gds', 'none')}`",
        f"- Integration DRC GDS: `{metrics.get('integration_gds', 'none')}`",
        f"- Architecture-view GDS: `{metrics.get('architecture_gds', 'none')}`",
        f"- Architecture SVG: `{metrics.get('architecture_svg', 'none')}`",
        f"- Occupancy SVG: `{metrics.get('occupancy_svg', 'none')}`",
        f"- Route-guide debug GDS: `{metrics.get('route_guide_gds', 'none')}`",
        "",
        "## Hardcell usage",
        "",
    ]
    for cell, count in metrics["hardcell_arrays"].items():
        lines.append(f"- array `{cell}`: {count}")
    for cell, count in metrics["hardcell_instances"].items():
        lines.append(f"- instance `{cell}`: {count}")
    bbox_audit = metrics.get("cell_bbox_audit", {})
    if bbox_audit:
        lines.extend(["", "## Cell bbox measurement", ""])
        lines.append(f"- method: {bbox_audit.get('method')}")
        underestimated = bbox_audit.get("cells_with_marker_underestimate", [])
        lines.append(
            "- cells where 239/text marker underestimates real geometry: "
            + (", ".join(f"`{cell}`" for cell in underestimated) if underestimated else "none")
        )
        cells = bbox_audit.get("cells", {})
        for cell_name, info in cells.items():
            selected = info.get("selected_bbox", {})
            overhang = info.get("geometry_overhang_beyond_marker")
            lines.append(
                f"- `{cell_name}` placement pitch source `{info.get('bbox_source_used_for_placement')}`: "
                f"{float(selected.get('width', 0.0)):.4f}um x {float(selected.get('height', 0.0)):.4f}um"
            )
            if overhang:
                lines.append(
                    f"- `{cell_name}` geometry overhang beyond 239 marker: "
                    f"L={float(overhang.get('left_um', 0.0)):.4f}um, "
                    f"B={float(overhang.get('bottom_um', 0.0)):.4f}um, "
                    f"R={float(overhang.get('right_um', 0.0)):.4f}um, "
                    f"T={float(overhang.get('top_um', 0.0)):.4f}um"
                )
    lines.extend(["", "## Generated stdcell usage", ""])
    if metrics["generated_instances"]:
        for cell, count in metrics["generated_instances"].items():
            lines.append(f"- `{cell}`: {count}")
    else:
        lines.append("- none; non-OpenRAM generated stdcell geometry is not emitted in formal GDS")
    columnmux_adapter = metrics.get("openyield_columnmux_adapter", {})
    if columnmux_adapter:
        lines.extend(["", "## OpenYield column mux adapter", ""])
        lines.append(f"- enabled: `{columnmux_adapter.get('enabled')}`")
        lines.append(f"- local macro: `{columnmux_adapter.get('local_macro', 'gen_col_mux')}`")
        lines.append(f"- source macro: `{columnmux_adapter.get('source_macro', 'gen_col_mux')}`")
        lines.append(f"- repaired alias metadata: `{columnmux_adapter.get('repaired_alias_metadata')}`")
        lines.append(f"- power status: `{columnmux_adapter.get('power_status')}`")
        lines.append(f"- safe_for_physical_mapping: `{columnmux_adapter.get('safe_for_physical_mapping')}`")
        lines.append(f"- safe_for_shared_rail: `{columnmux_adapter.get('safe_for_shared_rail')}`")
        lines.append(f"- uses repaired alias: `{columnmux_adapter.get('uses_repaired_alias')}`")
        lines.append(f"- shared rail enabled: `{columnmux_adapter.get('shared_rail_enabled')}`")
        lines.append(f"- routing changed: `{columnmux_adapter.get('routing_changed')}`")
        lines.append(f"- gds writer changed: `{columnmux_adapter.get('gds_writer_changed')}`")
        lines.append(f"- write_driver changed: `{columnmux_adapter.get('write_driver_changed')}`")
        lines.append(f"- wordline_driver changed: `{columnmux_adapter.get('wordline_driver_changed')}`")
        lines.append(f"- limited placement plan count: `{len((columnmux_adapter.get('limited_placement_plan') or {}).get('placements', []))}`")
    writedriver_adapter = metrics.get("openyield_writedriver_adapter", {})
    if writedriver_adapter:
        lines.extend(["", "## OpenYield write driver adapter", ""])
        lines.append(f"- enabled: `{writedriver_adapter.get('enabled')}`")
        lines.append(f"- local macro: `{writedriver_adapter.get('local_macro', 'write_driver')}`")
        lines.append(f"- contract path: `{writedriver_adapter.get('contract_path')}`")
        lines.append(f"- power status: `{writedriver_adapter.get('power_status')}`")
        lines.append(f"- safe_for_physical_mapping: `{writedriver_adapter.get('safe_for_physical_mapping')}`")
        lines.append(f"- safe_for_shared_rail: `{writedriver_adapter.get('safe_for_shared_rail')}`")
        lines.append(f"- requires_netlist_rewrite: `{writedriver_adapter.get('requires_netlist_rewrite')}`")
        lines.append(f"- placement count: `{writedriver_adapter.get('placement_count', 0)}`")
        lines.append(f"- adapter applied to placement: `{writedriver_adapter.get('adapter_applied_to_placement')}`")
        lines.append(f"- routing changed: `{writedriver_adapter.get('routing_changed')}`")
        lines.append(f"- gds writer changed: `{writedriver_adapter.get('gds_writer_changed')}`")
        lines.append(f"- shared rail enabled: `{writedriver_adapter.get('shared_rail_enabled')}`")
        lines.append(f"- write_driver changed: `{writedriver_adapter.get('write_driver_changed')}`")
        lines.append(f"- column mux changed: `{writedriver_adapter.get('column_mux_changed')}`")
        lines.append(f"- senseamp changed: `{writedriver_adapter.get('senseamp_changed')}`")
        lines.append(f"- storage aggregation enabled: `{writedriver_adapter.get('storage_aggregation_enabled')}`")
    wordlinedriver_adapter = metrics.get("openyield_wordlinedriver_adapter", {})
    if wordlinedriver_adapter:
        lines.extend(["", "## OpenYield wordline driver adapter", ""])
        lines.append(f"- enabled: `{wordlinedriver_adapter.get('enabled')}`")
        lines.append(f"- local macro: `{wordlinedriver_adapter.get('local_macro', 'gen_wl_driver')}`")
        lines.append(f"- contract path: `{wordlinedriver_adapter.get('contract_path')}`")
        lines.append(f"- power status: `{wordlinedriver_adapter.get('power_status')}`")
        lines.append(f"- safe_for_physical_mapping: `{wordlinedriver_adapter.get('safe_for_physical_mapping')}`")
        lines.append(f"- safe_for_shared_rail: `{wordlinedriver_adapter.get('safe_for_shared_rail')}`")
        lines.append(f"- can enter limited placement: `{wordlinedriver_adapter.get('can_enter_limited_placement')}`")
        lines.append(f"- b polarity: `{wordlinedriver_adapter.get('b_polarity')}`")
        lines.append(f"- semantic confirmation: `{wordlinedriver_adapter.get('semantic_confirmation')}`")
        lines.append(f"- placement count: `{wordlinedriver_adapter.get('placement_count', 0)}`")
        lines.append(f"- adapter applied to placement: `{wordlinedriver_adapter.get('adapter_applied_to_placement')}`")
        lines.append(f"- routing changed: `{wordlinedriver_adapter.get('routing_changed')}`")
        lines.append(f"- gds writer changed: `{wordlinedriver_adapter.get('gds_writer_changed')}`")
        lines.append(f"- shared rail enabled: `{wordlinedriver_adapter.get('shared_rail_enabled')}`")
        lines.append(f"- write_driver changed: `{wordlinedriver_adapter.get('write_driver_changed')}`")
        lines.append(f"- column mux changed: `{wordlinedriver_adapter.get('column_mux_changed')}`")
        lines.append(f"- senseamp changed: `{wordlinedriver_adapter.get('senseamp_changed')}`")
        lines.append(f"- storage aggregation enabled: `{wordlinedriver_adapter.get('storage_aggregation_enabled')}`")
        lines.append(f"- decoder changed: `{wordlinedriver_adapter.get('decoder_changed')}`")
        lines.append(f"- time control changed: `{wordlinedriver_adapter.get('time_control_changed')}`")
    lines.extend(["", "## Remaining abstract blocks", ""])
    if metrics["abstract_instances"]:
        for cell, count in metrics["abstract_instances"].items():
            lines.append(f"- `{cell}`: {count}")
    else:
        lines.append("- none")
    macro_replacement = metrics.get("macro_replacement_audit", {})
    if macro_replacement:
        lines.extend(["", "## Replaceable macro registry", ""])
        lines.append(f"- method: {macro_replacement.get('method')}")
        if macro_replacement.get("manifest"):
            lines.append(f"- manifest: `{macro_replacement.get('manifest')}`")
        lines.append(f"- abstract macro count: `{macro_replacement.get('abstract_macro_count', 0)}`")
        lines.append(f"- physical replacement macro count: `{macro_replacement.get('physical_macro_count', 0)}`")
        lines.append(f"- missing physical macro count: `{macro_replacement.get('missing_physical_macro_count', 0)}`")
        lines.append(
            "- physical GDS emitted for abstract macros: "
            f"`{macro_replacement.get('physical_gds_emitted_for_abstract_macros')}`"
        )
        for cell_name, info in macro_replacement.get("macros", {}).items():
            state = "physical" if info.get("has_physical_gds") else "abstract"
            lines.append(
                f"- `{cell_name}`: {info.get('instance_count')} instances, "
                f"slot={float(info.get('width', 0.0)):.4f}um x {float(info.get('height', 0.0)):.4f}um, "
                f"state=`{state}`"
            )
    lines.extend(["", "## Peripheral coverage", ""])
    for role, count in metrics.get("role_counts", {}).items():
        lines.append(f"- `{role}`: {count}")
    completeness = metrics.get("layout_completeness", {})
    lines.append(f"- complete_structural_roles: `{completeness.get('complete_structural_roles')}`")
    missing = completeness.get("missing_roles") or []
    lines.append(f"- missing_roles: `{', '.join(missing) if missing else 'none'}`")
    lines.append(f"- top-level route guides: `{completeness.get('route_guide_count', 0)}`")
    lines.extend(["", "## Banked architecture", ""])
    lines.append(f"- bank_style: `{metrics.get('bank_style', 'unknown')}`")
    if metrics.get("floorplan_compaction_strategy"):
        lines.append(f"- compaction strategy: `{metrics.get('floorplan_compaction_strategy')}`")
        lines.append(
            f"- boundary margin: `{metrics.get('boundary_margin_um')}`um "
            f"(legacy `{metrics.get('legacy_boundary_margin_um')}`um)"
        )
        lines.append(
            f"- estimated legacy size: `{float(metrics.get('estimated_legacy_width_um', 0.0)):.4f}um x "
            f"{float(metrics.get('estimated_legacy_height_um', 0.0)):.4f}um`, "
            f"area savings `{float(metrics.get('estimated_compaction_area_savings_um2', 0.0)):.4f}um^2` "
            f"({float(metrics.get('estimated_compaction_area_savings_percent', 0.0)):.2%})"
        )
    selected_data_packing = metrics.get("selected_data_dff_packing", {})
    if selected_data_packing:
        lines.append(f"- data DFF packing strategy: `{metrics.get('data_dff_packing_strategy')}`")
        lines.append(
            f"- selected data DFF grid: `{selected_data_packing.get('columns')}` columns x "
            f"`{selected_data_packing.get('rows')}` rows, "
            f"estimated macro area `{float(selected_data_packing.get('macro_area_um2', 0.0)):.4f}um^2`"
        )
    row_folding = metrics.get("row_logic_folding", {})
    if row_folding:
        folded_rows = row_folding.get("folded_rows", [])
        lines.append(f"- row-logic folding strategy: `{row_folding.get('strategy')}`")
        lines.append(
            f"- folded row drivers: `{', '.join(str(row) for row in folded_rows) if folded_rows else 'none'}` "
            f"using `{row_folding.get('lanes')}` horizontal lanes"
        )
    lines.append(f"- lower_bank_rows: `{metrics.get('lower_bank_rows', 'unknown')}`")
    lines.append(f"- upper_bank_rows: `{metrics.get('upper_bank_rows', 'unknown')}`")
    lines.append(f"- bank_channel_height_um: `{metrics.get('bank_channel_height_um', 'unknown')}`")
    quality = metrics.get("architecture_quality", {})
    if quality:
        missing_arch = quality.get("missing_modules", [])
        lines.append(f"- sample_like_floorplan: `{quality.get('sample_like_floorplan')}`")
        lines.append(f"- missing architecture modules: `{', '.join(missing_arch) if missing_arch else 'none'}`")
        lines.append(f"- featured module overlaps: `{quality.get('featured_module_overlap_count', 0)}`")
    geometry = metrics.get("geometry_audit", {})
    if geometry:
        lines.extend(["", "## Geometry audit", ""])
        lines.append(f"- clean: `{geometry.get('clean')}`")
        lines.append(f"- objects outside prBoundary: `{geometry.get('objects_outside_pr_boundary_count', 0)}`")
        lines.append(f"- data periphery overhangs: `{geometry.get('data_periphery_overhang_count', 0)}`")
        lines.append(f"- allowed data periphery overhangs: `{geometry.get('allowed_data_periphery_overhang_count', 0)}`")
        lines.append(f"- cell-array pitch violations: `{geometry.get('cell_array_pitch_violation_count', 0)}`")
        lines.append(f"- placed cell bbox overlaps: `{geometry.get('placed_cell_overlap_count', 0)}`")
        lines.append(f"- generated/hardcell overlaps: `{geometry.get('generated_hardcell_overlap_count', 0)}`")
        lines.append(
            f"- generated/hardcell spacing violations "
            f"(<{geometry.get('generated_hardcell_min_spacing_um', 'n/a')}um): "
            f"`{geometry.get('generated_hardcell_spacing_violation_count', 0)}`"
        )
        for item in geometry.get("data_periphery_overhangs", [])[:5]:
            lines.append(
                f"- overhang `{item.get('module')}` beyond `{item.get('reference')}`: "
                f"{float(item.get('overhang_um', 0.0)):.4f}um"
            )
        for item in geometry.get("allowed_data_periphery_overhangs", [])[:5]:
            lines.append(
                f"- allowed overhang `{item.get('module')}` beyond `{item.get('reference')}`: "
                f"{float(item.get('overhang_um', 0.0)):.4f}um ({item.get('reason')})"
            )
        for item in geometry.get("cell_array_pitch_violations", [])[:5]:
            lines.append(
                f"- cell-array pitch violation `{item.get('array')}`: "
                f"pitch=({float(item.get('pitch_x', 0.0)):.4f}, {float(item.get('pitch_y', 0.0)):.4f})um, "
                f"cell=({float(item.get('physical_cell_width', 0.0)):.4f}, "
                f"{float(item.get('physical_cell_height', 0.0)):.4f})um"
            )
        for item in geometry.get("placed_cell_overlaps", [])[:5]:
            lines.append(
                f"- placed cell overlap `{item.get('a_name')}` / `{item.get('b_name')}` "
                f"(`{item.get('a_role')}` / `{item.get('b_role')}`)"
            )
        for item in geometry.get("generated_hardcell_spacing_violations", [])[:5]:
            lines.append(
                f"- close spacing `{item.get('generated_instance')}` to `{item.get('hardcell')}`: "
                f"{float(item.get('spacing_um', 0.0)):.4f}um"
            )
    occupancy = metrics.get("floorplan_occupancy", {})
    if occupancy:
        lines.extend(["", "## Global occupancy map", ""])
        lines.append(f"- method: {occupancy.get('method')}")
        lines.append(f"- occupied area: `{float(occupancy.get('occupied_area_um2', 0.0)):.4f}um^2`")
        lines.append(f"- empty area: `{float(occupancy.get('empty_area_um2', 0.0)):.4f}um^2`")
        lines.append(f"- occupancy ratio: `{float(occupancy.get('occupancy_ratio', 0.0)):.2%}`")
        lines.append(f"- largest empty region: `{float(occupancy.get('largest_empty_area_um2', 0.0)):.4f}um^2`")
        lines.append(f"- occupancy SVG: `{metrics.get('occupancy_svg', 'none')}`")
        role_areas = occupancy.get("role_primary_area_um2", {})
        if role_areas:
            ranked_roles = sorted(role_areas.items(), key=lambda item: float(item[1]), reverse=True)[:10]
            lines.append(
                "- largest filled roles: "
                + ", ".join(f"`{role}`={float(area):.4f}um^2" for role, area in ranked_roles)
            )
        for index, item in enumerate(occupancy.get("optimization_targets", [])[:6], start=1):
            rect = item.get("rect", {})
            nearest = item.get("nearest_filled_regions", [])
            nearest_text = ", ".join(
                f"`{entry.get('name')}`/{entry.get('role')}@{float(entry.get('spacing_um', 0.0)):.3f}um"
                for entry in nearest[:3]
            )
            lines.append(
                f"- empty target {index}: area={float(item.get('area_um2', 0.0)):.4f}um^2, "
                f"rect=({float(rect.get('x0', 0.0)):.3f}, {float(rect.get('y0', 0.0)):.3f}) to "
                f"({float(rect.get('x1', 0.0)):.3f}, {float(rect.get('y1', 0.0)):.3f}), "
                f"nearest={nearest_text or 'none'}"
            )
        coarse = occupancy.get("coarse_map", {})
        rows_text = coarse.get("rows_text", [])
        legend = coarse.get("legend", {})
        if rows_text:
            lines.append("- coarse map (`.` means empty):")
            lines.append("```text")
            lines.extend(rows_text[:18])
            lines.append("```")
            legend_text = ", ".join(f"{symbol}={name}" for symbol, name in legend.items())
            lines.append(f"- map legend: {legend_text}")
    mirror_audit = metrics.get("cell_array_mirror_audit", {})
    if mirror_audit:
        lines.extend(["", "## OpenRAM-style array mirror audit", ""])
        lines.append(f"- method: {mirror_audit.get('method')}")
        lines.append(f"- clean: `{mirror_audit.get('clean')}`")
        lines.append(f"- missing required row mirrors: `{mirror_audit.get('missing_required_row_mirror_count', 0)}`")
        mirrored = [
            f"`{array.get('array')}` row_offset={array.get('row_offset')}"
            for array in mirror_audit.get("arrays", [])
            if array.get("expected_openram_row_mirror")
        ]
        if mirrored:
            lines.append("- arrays using OpenRAM row mirror rule: " + "; ".join(mirrored[:12]))
    array_layer_audit = metrics.get("cell_array_layer_audit", {})
    if array_layer_audit:
        lines.extend(["", "## OpenRAM-style array layer audit", ""])
        lines.append(f"- method: {array_layer_audit.get('method')}")
        lines.append(f"- clean: `{array_layer_audit.get('clean')}`")
        lines.append(f"- illegal same-layer overlaps from pitch: `{array_layer_audit.get('illegal_layer_overlap_count', 0)}`")
        for item in array_layer_audit.get("illegal_layer_overlaps", [])[:8]:
            lines.append(
                f"- overlap `{item.get('array')}` layer `{item.get('layer')}`: "
                f"x={float(item.get('horizontal_overlap_um', 0.0)):.4f}um, "
                f"y={float(item.get('vertical_overlap_um', 0.0)):.4f}um"
            )
        vtg_rows = []
        for array in array_layer_audit.get("arrays", []):
            vtg = (array.get("layers") or {}).get("vtg")
            if not vtg:
                continue
            vtg_rows.append(
                f"`{array.get('array')}`: x {vtg.get('horizontal_status')} "
                f"({vtg.get('horizontal_gap_um')}um), y {vtg.get('vertical_status')} "
                f"({vtg.get('vertical_gap_um')}um)"
            )
        if vtg_rows:
            lines.append("- layer 6 / `vtg` summary: " + "; ".join(vtg_rows[:8]))
    lines.extend(["", "## Architecture module map", ""])
    architecture_modules = metrics.get("architecture_modules", [])
    if architecture_modules:
        for module in architecture_modules:
            rect = module.get("rect", {})
            lines.append(
                f"- `{module.get('name')}`: "
                f"({float(rect.get('x0', 0.0)):.3f}, {float(rect.get('y0', 0.0)):.3f}) to "
                f"({float(rect.get('x1', 0.0)):.3f}, {float(rect.get('y1', 0.0)):.3f}), "
                f"area={float(module.get('area_um2', 0.0)):.4f}um^2"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Route metrics", ""])
    route_metrics = metrics.get("route_metrics", {})
    for title, key in [
        ("drawn routes", "route_length_um_by_layer"),
        ("route guides", "route_guide_length_um_by_layer"),
        ("routes plus guides", "route_and_guide_length_um_by_layer"),
    ]:
        values = route_metrics.get(key, {})
        joined = ", ".join(f"{layer}={length:.4f}um" for layer, length in values.items()) if values else "none"
        lines.append(f"- {title}: {joined}")
    track_selection = metrics.get("routing_track_selection", {}).get("col_select", {})
    if track_selection:
        score = track_selection.get("score", {})
        lines.extend(["", "## Routing track selection", ""])
        lines.append(f"- col_select algorithm: `{track_selection.get('algorithm')}`")
        lines.append(f"- evaluated candidates: `{track_selection.get('candidate_count')}`")
        lines.append(f"- selected y0: `{track_selection.get('selected_y0')}`")
        lines.append(f"- score remaining candidate guides: `{score.get('remaining_candidate_guides')}`")
    promotion = metrics.get("route_guide_promotion", {})
    if promotion:
        lines.extend(["", "## Route-guide promotion", ""])
        lines.append(f"- initial route guides: `{promotion.get('initial_route_guides', 0)}`")
        lines.append(f"- promoted to clean routes: `{promotion.get('promoted_to_routes', 0)}`")
        lines.append(f"- remaining route guides: `{promotion.get('remaining_route_guides', 0)}`")
        promoted_by_layer = promotion.get("promoted_by_layer", {})
        remaining_by_layer = promotion.get("remaining_by_layer", {})
        blocked_by_reason = promotion.get("blocked_by_reason", {})
        lines.append("- promoted by layer: " + (_format_counts(promoted_by_layer) if promoted_by_layer else "none"))
        lines.append("- remaining by layer: " + (_format_counts(remaining_by_layer) if remaining_by_layer else "none"))
        lines.append("- blocked by reason: " + (_format_counts(blocked_by_reason) if blocked_by_reason else "none"))
    lines.extend(["", "## GDS hierarchy", ""])
    for cell, count in metrics["gds_hierarchy"]["reference_counts"].items():
        lines.append(f"- `{cell}` SREF count: {count}")
    generated_cells = metrics.get("generated_gds_cells", [])
    if generated_cells:
        lines.append("- generated stdcells are emitted as GDS child structures: " + ", ".join(f"`{cell}`" for cell in generated_cells))
    else:
        lines.append("- generated/abstract helper macros emitted as GDS child structures: none")
    layer_audit = metrics.get("layer_audit", {})
    lines.extend(["", "## Layer audit", ""])
    lines.append(f"- matches bundled FreePDK45 layers: `{layer_audit.get('matches_bundled_freepdk45_layers')}`")
    for key in [
        "unknown_clean_boundary_lpps",
        "unknown_clean_text_lpps",
        "unknown_route_guide_boundary_lpps",
        "unknown_route_guide_text_lpps",
    ]:
        values = layer_audit.get(key, [])
        lines.append(f"- {key}: `{', '.join(values) if values else 'none'}`")
    clean_layers = layer_audit.get("clean_gds_layers", {})
    if clean_layers:
        boundary = ", ".join(f"{lpp}={count}" for lpp, count in clean_layers.get("boundary", {}).items())
        text = ", ".join(f"{lpp}={count}" for lpp, count in clean_layers.get("text", {}).items())
        lines.append(f"- clean boundary LPPs: {boundary}")
        lines.append(f"- clean text LPPs: {text}")
    pin_access = metrics.get("hardcell_pin_access", {}).get("cells", {})
    lines.extend(["", "## Hardcell pin access", ""])
    if pin_access:
        for cell, info in pin_access.items():
            pins = ", ".join(info.get("unique_pins", []))
            lines.append(f"- `{cell}` pins ({info.get('pin_count', 0)} labels): {pins}")
    else:
        lines.append("- none")
    generated_pin_access = metrics.get("generated_pin_access", {}).get("cells", {})
    lines.extend(["", "## Abstract macro pin model", ""])
    if generated_pin_access:
        for cell, info in generated_pin_access.items():
            pins = ", ".join(info.get("unique_pins", []))
            lines.append(f"- `{cell}` pins ({info.get('pin_count', 0)} labels): {pins}")
    else:
        lines.append("- none")
    connectivity = metrics.get("connectivity_audit", {})
    lines.extend(["", "## Connectivity audit", ""])
    lines.append(f"- method: {connectivity.get('method', 'none')}")
    lines.append(f"- all generated roles touched: `{connectivity.get('all_generated_roles_touched')}`")
    no_touch = connectivity.get("roles_with_no_route_or_guide_touch", [])
    partial = connectivity.get("roles_with_partial_route_or_guide_touch", [])
    lines.append(f"- roles with no route/guide touch: `{', '.join(no_touch) if no_touch else 'none'}`")
    lines.append(f"- roles with partial route/guide touch: `{', '.join(partial) if partial else 'none'}`")
    for role, info in connectivity.get("by_role", {}).items():
        coverage = float(info.get("coverage", 0.0))
        lines.append(
            f"- `{role}`: {info.get('instances_touched', 0)}/"
            f"{info.get('instances', 0)} touched ({coverage:.1%})"
        )
    route_only = metrics.get("route_only_connectivity_audit", {})
    lines.extend(["", "## Drawn route connectivity audit", ""])
    lines.append(f"- method: {route_only.get('method', 'none')}")
    lines.append(f"- all generated roles touched by drawn routes: `{route_only.get('all_generated_roles_touched_by_routes')}`")
    no_route_touch = route_only.get("roles_with_no_route_touch", [])
    partial_route = route_only.get("roles_with_partial_route_touch", [])
    lines.append(f"- roles with no drawn-route touch: `{', '.join(no_route_touch) if no_route_touch else 'none'}`")
    lines.append(f"- roles with partial drawn-route touch: `{', '.join(partial_route) if partial_route else 'none'}`")
    for role, info in route_only.get("by_role", {}).items():
        coverage = float(info.get("coverage", 0.0))
        lines.append(
            f"- `{role}`: {info.get('instances_touched', 0)}/"
            f"{info.get('instances', 0)} touched ({coverage:.1%})"
        )
    pin_route = metrics.get("generated_pin_route_audit", {})
    lines.extend(["", "## Generated pin routing audit", ""])
    lines.append(f"- drawn-route signal pin coverage: `{float(pin_route.get('coverage', 0.0)):.1%}`")
    lines.append(f"- all generated signal pins covered by drawn routes: `{pin_route.get('all_generated_signal_pins_covered')}`")
    lines.append(f"- missing generated signal pins: `{pin_route.get('missing_signal_pins', 0)}`")
    for item in pin_route.get("missing_examples", [])[:12]:
        lines.append(
            f"- missing `{item.get('instance')}.{item.get('pin')}` "
            f"({item.get('cell')}, {item.get('layer')})"
        )
    lines.extend(["", "## GDS labels", ""])
    labels = metrics["gds_hierarchy"].get("labels", {})
    if labels:
        lines.append(f"- total text labels: {metrics['gds_hierarchy'].get('text_count', 0)}")
        for name, count in labels.items():
            if name in {"clk", "csb", "web", "vdd", "gnd"} or "[" in name:
                lines.append(f"- `{name}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Signoff status", ""])
    if "integration_signoff_ready" in metrics:
        lines.append(f"- integration_signoff_ready: `{metrics['integration_signoff_ready']}`")
        for item in metrics.get("integration_signoff_blockers", []):
            lines.append(f"- integration blocker: {item}")
    lines.append(f"- signoff_ready: `{metrics['signoff_ready']}`")
    criteria = metrics.get("signoff_criteria", {})
    if criteria:
        for key, value in criteria.items():
            lines.append(f"- criterion {key}: `{value}`")
    for item in metrics["signoff_blockers"]:
        lines.append(f"- blocker: {item}")
    lines.append("")
    return "\n".join(lines)
