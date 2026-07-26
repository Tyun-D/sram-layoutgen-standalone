from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DelayChainRole:
    instance_role: str
    stage_index: int
    role_type: str
    load_index: int | None


def stage_driver_role(stage_index: int) -> str:
    return f"stage_{stage_index:02d}_driver"


def stage_load_role(stage_index: int, load_index: int) -> str:
    return f"stage_{stage_index:02d}_load_{load_index:02d}"


def build_role_manifest(*, stage_count: int, loads_per_stage: int) -> list[DelayChainRole]:
    rows: list[DelayChainRole] = []
    for stage_index in range(stage_count):
        rows.append(
            DelayChainRole(
                instance_role=stage_driver_role(stage_index),
                stage_index=stage_index,
                role_type="driver",
                load_index=None,
            )
        )
        for load_index in range(loads_per_stage):
            rows.append(
                DelayChainRole(
                    instance_role=stage_load_role(stage_index, load_index),
                    stage_index=stage_index,
                    role_type="load",
                    load_index=load_index,
                )
            )
    return rows


def stage_net_name(stage_index: int, *, stage_count: int) -> str:
    return "out" if stage_index == stage_count - 1 else f"stage_{stage_index:02d}_net"


def stage_endpoint_contract(*, stage_count: int, loads_per_stage: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stage_index in range(stage_count):
        endpoints = [f"{stage_driver_role(stage_index)}.Z"]
        endpoints.extend(f"{stage_load_role(stage_index, load_index)}.A" for load_index in range(loads_per_stage))
        if stage_index < stage_count - 1:
            endpoints.append(f"{stage_driver_role(stage_index + 1)}.A")
        else:
            endpoints.append("TOP.out")
        rows.append(
            {
                "stage_index": stage_index,
                "net_name": stage_net_name(stage_index, stage_count=stage_count),
                "expected_endpoint_count": len(endpoints),
                "expected_endpoints": endpoints,
            }
        )
    return rows


def build_stage_topology(*, module_name: str, stage_count: int, loads_per_stage: int, output_polarity: str) -> dict[str, Any]:
    rows = []
    for stage_index in range(stage_count):
        rows.append(
            {
                "stage_index": stage_index,
                "driver_role": stage_driver_role(stage_index),
                "load_roles": [stage_load_role(stage_index, load_index) for load_index in range(loads_per_stage)],
                "stage_net_name": stage_net_name(stage_index, stage_count=stage_count),
                "prev_driver_input_role": "TOP.in" if stage_index == 0 else f"{stage_driver_role(stage_index)}.A",
                "next_driver_input_role": "TOP.out" if stage_index == stage_count - 1 else f"{stage_driver_role(stage_index + 1)}.A",
            }
        )
    return {
        "module_name": module_name,
        "stage_count": stage_count,
        "loads_per_stage": loads_per_stage,
        "driver_count": stage_count,
        "load_count": stage_count * loads_per_stage,
        "child_count": stage_count * (loads_per_stage + 1),
        "output_polarity": output_polarity,
        "stages": rows,
        "endpoint_contract": stage_endpoint_contract(stage_count=stage_count, loads_per_stage=loads_per_stage),
    }
