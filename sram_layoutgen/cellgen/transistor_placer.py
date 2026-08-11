from __future__ import annotations

from .mos_graph import MosDevice


def place_transistors(devices: list[MosDevice], *, architecture: str) -> list[dict[str, object]]:
    """Return deterministic conservative placements for isolated MOS devices.

    The first generation deliberately isolates diffusions. That makes the
    topology witness straightforward and gives DRC-clean candidates before
    tighter diffusion-sharing optimization is allowed into the flow.
    """
    if architecture.endswith("REVERSE"):
        ordered = list(reversed(devices))
    elif "PMOS_FIRST" in architecture:
        ordered = sorted(devices, key=lambda d: (d.type != "PMOS", d.instance))
    elif "NMOS_FIRST" in architecture:
        ordered = sorted(devices, key=lambda d: (d.type != "NMOS", d.instance))
    else:
        ordered = list(devices)

    placements: list[dict[str, object]] = []
    n_i = 0
    p_i = 0
    for dev in ordered:
        if dev.type == "PMOS":
            x = 0.25 + p_i * 0.85
            y = 1.25
            p_i += 1
        else:
            x = 0.25 + n_i * 0.85
            y = 0.25
            n_i += 1
        placements.append({"instance": dev.instance, "type": dev.type, "x": round(x, 6), "y": round(y, 6), "orientation": "R0"})
    return placements

