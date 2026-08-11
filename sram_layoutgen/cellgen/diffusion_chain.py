from __future__ import annotations

from .mos_graph import MosDevice


def diffusion_compatible(left: MosDevice, right: MosDevice) -> bool:
    return left.type == right.type and (left.d == right.s or left.s == right.d)


def compatibility_edges(devices: list[MosDevice]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i, left in enumerate(devices):
        for right in devices[i + 1 :]:
            rows.append(
                {
                    "left": left.instance,
                    "right": right.instance,
                    "same_type": left.type == right.type,
                    "shared_diffusion_net": sorted({left.s, left.d}.intersection({right.s, right.d})),
                    "compatible": diffusion_compatible(left, right),
                }
            )
    return rows

