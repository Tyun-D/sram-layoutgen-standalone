from __future__ import annotations


def pin_contract(pins: list[str]) -> dict[str, dict[str, object]]:
    return {pin: {"pin": pin, "layer": "metal1", "source": "topology_lock", "access": "m1 bus"} for pin in pins}

