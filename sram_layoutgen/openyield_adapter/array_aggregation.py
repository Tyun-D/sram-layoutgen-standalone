"""Limited OpenYield array aggregation planning.

This module deliberately plans only storage-array style cells that passed the
GDS pin/rail audit: bitcell, dummy cell, and replica cell.  It does not place
peripheral macros, modify GDS output, merge rails, or connect to the main
layout generator flow.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ALLOWED_AGGREGATION_MACROS = ("cell_1rw", "dummy_cell_1rw", "replica_cell_1rw")
ROW_ORIENTATION_POLICIES = ("all_r0", "alternating_mx")
EXCLUDED_PERIPHERAL_MACROS = {
    "sense_amp": "architecture_adapter_required: OpenYield has Q/QB, local sense_amp has single-ended dout.",
    "write_driver": "rail_needs_manual_review: keep legacy/peripheral placement until rail sharing is proven.",
    "dff": "standard_cell_row_required: do not aggregate with storage-array cells.",
    "tri_gate": "standard_cell_row_required: do not aggregate with storage-array cells.",
    "gen_col_mux": "missing_power_metadata: vdd is not proven, shared rail is forbidden.",
    "gen_wl_driver": "needs_semantic_confirmation: B/wordline_enable semantics still need confirmation.",
    "gen_nand2": "logic_gate: not part of limited storage-array aggregation.",
    "gen_nand4": "logic_gate: not part of limited storage-array aggregation.",
    "gen_precharge": "peripheral_macro: not part of limited storage-array aggregation.",
}


@dataclass(frozen=True)
class AggregatedCellPlacement:
    instance_name: str
    macro_name: str
    row: int
    col: int
    x: float
    y: float
    width: float
    height: float
    orientation: str
    role: str
    nets: dict[str, str]
    shared_power_hint: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AggregatedArrayPlan:
    role: str
    rows: int
    cols: int
    cell_macro: str
    placements: list[AggregatedCellPlacement]
    width: float
    height: float
    power_rail_policy: str
    row_orientation_policy: str = "all_r0"
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["placements"] = [placement.to_dict() for placement in self.placements]
        return data


@dataclass(frozen=True)
class LimitedArrayAggregationResult:
    enabled: bool
    rows: int
    cols: int
    plans: tuple[AggregatedArrayPlan, ...] = ()
    allowed_macros: tuple[str, ...] = ALLOWED_AGGREGATION_MACROS
    row_orientation_policy: str = "all_r0"
    excluded_macros: dict[str, str] = field(default_factory=lambda: dict(EXCLUDED_PERIPHERAL_MACROS))
    changed_gds_flow: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["plans"] = [plan.to_dict() for plan in self.plans]
        return data


@dataclass(frozen=True)
class StandaloneStorageArrayPlan:
    array_name: str
    role: str
    rows: int
    cols: int
    cell_macro: str
    origin_x: float
    origin_y: float
    pitch_x: float
    pitch_y: float
    width: float
    height: float
    orientation: str = "R0"
    row_orientation_policy: str = "all_r0"
    power_rail_policy: str = "tb_shared_hint_only"
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StandaloneStorageArrayAggregationResult:
    enabled: bool
    rows: int
    cols: int
    plans: tuple[StandaloneStorageArrayPlan, ...] = ()
    allowed_macros: tuple[str, ...] = ALLOWED_AGGREGATION_MACROS
    row_orientation_policy: str = "all_r0"
    excluded_macros: dict[str, str] = field(default_factory=lambda: dict(EXCLUDED_PERIPHERAL_MACROS))
    power_rail_policy: str = "tb_shared_hint_only"
    cross_row_power_short_risk: bool | None = None
    changed_gds_flow: bool = False
    routing_changed: bool = False
    shared_rail_merge: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["plans"] = [plan.to_dict() for plan in self.plans]
        return data


def build_limited_array_aggregation(
    rows: int,
    cols: int,
    *,
    enable_openyield_array_aggregation: bool = False,
    row_orientation_policy: str = "all_r0",
    gds_pin_audit_path: str | Path = "docs/openyield_gds_pin_audit_report.json",
    array_origin_x: float = 0.0,
    array_origin_y: float = 0.0,
) -> LimitedArrayAggregationResult:
    """Build a limited storage-array aggregation plan.

    The default is disabled.  When disabled, no placements are produced, which
    keeps existing layout flows unchanged.
    """

    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive")
    validate_row_orientation_policy(row_orientation_policy)
    if not enable_openyield_array_aggregation:
        return LimitedArrayAggregationResult(
            enabled=False,
            rows=rows,
            cols=cols,
            row_orientation_policy=row_orientation_policy,
            notes=("enable_openyield_array_aggregation is False; no aggregation plan was generated.",),
        )

    macro_specs = load_ready_storage_macro_specs(gds_pin_audit_path)
    missing = [name for name in ALLOWED_AGGREGATION_MACROS if name not in macro_specs]
    if missing:
        raise ValueError(f"required abutment-ready macros are missing from GDS audit: {', '.join(missing)}")

    bitcell = _build_bitcell_plan(rows, cols, macro_specs["cell_1rw"], array_origin_x, array_origin_y, row_orientation_policy=row_orientation_policy)
    dummy_row = _build_dummy_row_plan(
        cols,
        macro_specs["dummy_cell_1rw"],
        array_origin_x,
        array_origin_y - macro_specs["dummy_cell_1rw"]["height"],
        row_orientation_policy=row_orientation_policy,
    )
    dummy_col = _build_dummy_column_plan(
        rows,
        macro_specs["dummy_cell_1rw"],
        array_origin_x - macro_specs["dummy_cell_1rw"]["width"],
        array_origin_y,
        row_orientation_policy=row_orientation_policy,
    )
    replica_col = _build_replica_column_plan(
        rows,
        macro_specs["replica_cell_1rw"],
        array_origin_x + cols * macro_specs["cell_1rw"]["width"],
        array_origin_y,
        row_orientation_policy=row_orientation_policy,
    )
    return LimitedArrayAggregationResult(
        enabled=True,
        rows=rows,
        cols=cols,
        plans=(bitcell, dummy_row, dummy_col, replica_col),
        row_orientation_policy=row_orientation_policy,
        notes=(
            "Limited aggregation is metadata/plan-only; it does not write GDS or merge power shapes.",
            "Only cell_1rw, dummy_cell_1rw, and replica_cell_1rw are included.",
            "power_rail_policy is tb_shared_hint_only; LR shared rail remains disabled.",
            f"row_orientation_policy={row_orientation_policy}",
        ),
    )


def build_standalone_storage_array_aggregation(
    rows: int,
    cols: int,
    *,
    enable_openyield_array_aggregation: bool = False,
    row_orientation_policy: str = "all_r0",
    gds_pin_audit_path: str | Path = "docs/openyield_gds_pin_audit_report.json",
    origins: dict[str, tuple[float, float]] | None = None,
) -> StandaloneStorageArrayAggregationResult:
    """Build the storage-only aggregation shape used by ``standalone``.

    This preserves the existing generator topology: one bitcell array, left and
    right dummy columns, and one replica column.  It intentionally excludes
    dummy rows and all peripheral cells.
    """

    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive")
    validate_row_orientation_policy(row_orientation_policy)
    if not enable_openyield_array_aggregation:
        return StandaloneStorageArrayAggregationResult(
            enabled=False,
            rows=rows,
            cols=cols,
            row_orientation_policy=row_orientation_policy,
            notes=("enable_openyield_array_aggregation is False; standalone storage placement stays on the legacy path.",),
        )
    origins = origins or {
        "bitcell_array": (0.0, 0.0),
        "dummy_left_array": (-1.0, 0.0),
        "dummy_right_array": (cols * 1.0, 0.0),
        "replica_bitline_array": ((cols + 1) * 1.0, 0.0),
    }
    macro_specs = load_ready_storage_macro_specs(gds_pin_audit_path)
    missing = [name for name in ALLOWED_AGGREGATION_MACROS if name not in macro_specs]
    if missing:
        raise ValueError(f"required abutment-ready macros are missing from GDS audit: {', '.join(missing)}")
    plan_specs = (
        ("bitcell_array", "bitcell_array", "cell_1rw", rows, cols),
        ("dummy_left_array", "dummy_bitcell", "dummy_cell_1rw", rows, 1),
        ("dummy_right_array", "dummy_bitcell", "dummy_cell_1rw", rows, 1),
        ("replica_bitline_array", "replica_bitline", "replica_cell_1rw", rows, 1),
    )
    plans: list[StandaloneStorageArrayPlan] = []
    for array_name, role, cell_macro, plan_rows, plan_cols in plan_specs:
        if cell_macro not in ALLOWED_AGGREGATION_MACROS:
            raise ValueError(f"disallowed macro in standalone aggregation plan: {cell_macro}")
        if array_name not in origins:
            raise ValueError(f"missing origin for standalone aggregation array: {array_name}")
        spec = macro_specs[cell_macro]
        origin_x, origin_y = origins[array_name]
        plans.append(
            StandaloneStorageArrayPlan(
                array_name=array_name,
                role=role,
                rows=plan_rows,
                cols=plan_cols,
                cell_macro=cell_macro,
                origin_x=float(origin_x),
                origin_y=float(origin_y),
                pitch_x=spec["width"],
                pitch_y=spec["height"],
                width=plan_cols * spec["width"],
                height=plan_rows * spec["height"],
                orientation=orientation_summary(row_orientation_policy),
                row_orientation_policy=row_orientation_policy,
                notes=(
                    "x=origin_x+col*cell_width, y=origin_y+row*cell_height.",
                    f"row_orientation_policy={row_orientation_policy}",
                ),
            )
        )
    return StandaloneStorageArrayAggregationResult(
        enabled=True,
        rows=rows,
        cols=cols,
        plans=tuple(plans),
        row_orientation_policy=row_orientation_policy,
        cross_row_power_short_risk=True if row_orientation_policy == "all_r0" and rows >= 2 else False if row_orientation_policy == "alternating_mx" and rows >= 2 else None,
        notes=(
            "Standalone integration replaces only bitcell/dummy/replica CellArray placement.",
            "Peripheral placement, routing, GDS writer behavior, and rail-shape merging remain unchanged.",
            f"row_orientation_policy={row_orientation_policy}",
        ),
    )


def summarize_m5_openyield_array_bindings(result: StandaloneStorageArrayAggregationResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plan in result.plans:
        rows.append(
            {
                "array_name": plan.array_name,
                "role": plan.role,
                "cell_macro": plan.cell_macro,
                "rows": plan.rows,
                "cols": plan.cols,
                "origin_x": round(plan.origin_x, 6),
                "origin_y": round(plan.origin_y, 6),
                "width": round(plan.width, 6),
                "height": round(plan.height, 6),
                "row_orientation_policy": plan.row_orientation_policy,
                "power_rail_policy": plan.power_rail_policy,
                "notes": "; ".join(plan.notes),
            }
        )
    return rows


def _build_bitcell_plan(
    rows: int,
    cols: int,
    spec: dict[str, float],
    x0: float,
    y0: float,
    *,
    row_orientation_policy: str,
) -> AggregatedArrayPlan:
    width = spec["width"]
    height = spec["height"]
    placements = [
        AggregatedCellPlacement(
            instance_name=f"Xbit_r{row}_c{col}",
            macro_name="cell_1rw",
            row=row,
            col=col,
            x=x0 + col * width,
            y=y0 + row * height,
            width=width,
            height=height,
            orientation=orientation_for_row(row, row_orientation_policy),
            role="bitcell",
            nets={"vdd": "vdd", "gnd": "gnd", "bl": f"bl[{col}]", "br": f"br[{col}]", "wl": f"wl[{row}]"},
            shared_power_hint=True,
        )
        for row in range(rows)
        for col in range(cols)
    ]
    return AggregatedArrayPlan(
        role="bitcell_array",
        rows=rows,
        cols=cols,
        cell_macro="cell_1rw",
        placements=placements,
        width=cols * width,
        height=rows * height,
        row_orientation_policy=row_orientation_policy,
        power_rail_policy="tb_shared_hint_only",
        notes=(
            "x=origin_x+col*cell_width, y=origin_y+row*cell_height.",
            f"row_orientation_policy={row_orientation_policy}",
        ),
    )


def _build_dummy_row_plan(
    cols: int,
    spec: dict[str, float],
    x0: float,
    y0: float,
    *,
    row_orientation_policy: str,
) -> AggregatedArrayPlan:
    width = spec["width"]
    height = spec["height"]
    placements = [
        AggregatedCellPlacement(
            instance_name=f"Xdumrow_c{col}",
            macro_name="dummy_cell_1rw",
            row=0,
            col=col,
            x=x0 + col * width,
            y=y0,
            width=width,
            height=height,
            orientation=orientation_for_row(0, row_orientation_policy),
            role="dummy_row",
            nets={"vdd": "vdd", "gnd": "gnd", "bl": f"dummy_bl[{col}]", "br": f"dummy_br[{col}]", "wl": "dummy_wl"},
            shared_power_hint=True,
        )
        for col in range(cols)
    ]
    return AggregatedArrayPlan(
        role="dummy_row",
        rows=1,
        cols=cols,
        cell_macro="dummy_cell_1rw",
        placements=placements,
        width=cols * width,
        height=height,
        row_orientation_policy=row_orientation_policy,
        power_rail_policy="tb_shared_hint_only",
        notes=("dummy_connectivity_needs_confirmation", f"row_orientation_policy={row_orientation_policy}"),
    )


def _build_dummy_column_plan(
    rows: int,
    spec: dict[str, float],
    x0: float,
    y0: float,
    *,
    row_orientation_policy: str,
) -> AggregatedArrayPlan:
    width = spec["width"]
    height = spec["height"]
    placements = [
        AggregatedCellPlacement(
            instance_name=f"Xdumcol_r{row}",
            macro_name="dummy_cell_1rw",
            row=row,
            col=0,
            x=x0,
            y=y0 + row * height,
            width=width,
            height=height,
            orientation=orientation_for_row(row, row_orientation_policy),
            role="dummy_column",
            nets={"vdd": "vdd", "gnd": "gnd", "bl": "dummy_bl_col", "br": "dummy_br_col", "wl": f"dummy_wl[{row}]"},
            shared_power_hint=True,
        )
        for row in range(rows)
    ]
    return AggregatedArrayPlan(
        role="dummy_column",
        rows=rows,
        cols=1,
        cell_macro="dummy_cell_1rw",
        placements=placements,
        width=width,
        height=rows * height,
        row_orientation_policy=row_orientation_policy,
        power_rail_policy="tb_shared_hint_only",
        notes=("dummy_connectivity_needs_confirmation", f"row_orientation_policy={row_orientation_policy}"),
    )


def _build_replica_column_plan(
    rows: int,
    spec: dict[str, float],
    x0: float,
    y0: float,
    *,
    row_orientation_policy: str,
) -> AggregatedArrayPlan:
    width = spec["width"]
    height = spec["height"]
    placements = [
        AggregatedCellPlacement(
            instance_name=f"Xreplica_r{row}",
            macro_name="replica_cell_1rw",
            row=row,
            col=0,
            x=x0,
            y=y0 + row * height,
            width=width,
            height=height,
            orientation=orientation_for_row(row, row_orientation_policy),
            role="replica_column",
            nets={"vdd": "vdd", "gnd": "gnd", "rbl": "rbl", "rblb": "rblb", "wl": f"replica_wl[{row}]"},
            shared_power_hint=True,
        )
        for row in range(rows)
    ]
    return AggregatedArrayPlan(
        role="replica_column",
        rows=rows,
        cols=1,
        cell_macro="replica_cell_1rw",
        placements=placements,
        width=width,
        height=rows * height,
        row_orientation_policy=row_orientation_policy,
        power_rail_policy="tb_shared_hint_only",
        notes=("replica_wl_semantics_need_confirmation", f"row_orientation_policy={row_orientation_policy}"),
    )


def load_ready_storage_macro_specs(path: str | Path) -> dict[str, dict[str, float]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    specs: dict[str, dict[str, float]] = {}
    for item in payload.get("audited_macros", []):
        name = item.get("macro_name")
        if name not in ALLOWED_AGGREGATION_MACROS:
            continue
        if item.get("abutment_readiness") != "abutment_ready":
            continue
        specs[name] = {"width": float(item["width"]), "height": float(item["height"])}
    return specs


def _load_ready_macro_specs(path: str | Path) -> dict[str, dict[str, float]]:
    return load_ready_storage_macro_specs(path)


def validate_row_orientation_policy(policy: str) -> str:
    if policy not in ROW_ORIENTATION_POLICIES:
        raise ValueError(f"unsupported row orientation policy: {policy}")
    return policy


def orientation_for_row(row: int, policy: str) -> str:
    validate_row_orientation_policy(policy)
    if policy == "alternating_mx":
        return "R0" if row % 2 == 0 else "MX"
    return "R0"


def orientation_summary(policy: str) -> str:
    return "R0/MX by row" if policy == "alternating_mx" else "R0"
