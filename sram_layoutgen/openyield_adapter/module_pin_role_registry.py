from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MODULE_PIN_ROLE_REGISTRY: dict[str, dict[str, str]] = {
    "PINV": {
        "VDD": "POWER",
        "VSS": "GROUND",
        "A": "SIGNAL_INPUT",
        "Z": "SIGNAL_OUTPUT",
    },
    "TRANSMISSION_GATE": {
        "VDD": "BODY_POWER",
        "VSS": "BODY_GROUND",
        "IN": "BIDIRECTIONAL_SWITCH_TERMINAL",
        "OUT": "BIDIRECTIONAL_SWITCH_TERMINAL",
        "CTR_P": "CONTROL_INPUT",
        "CTR_N": "CONTROL_INPUT",
    },
    "DFF": {
        "VDD": "POWER",
        "VSS": "GROUND",
        "D": "SIGNAL_INPUT",
        "Q": "SIGNAL_OUTPUT",
        "CLK": "CLOCK_INPUT",
    },
    "DFF_BUF": {
        "VDD": "POWER",
        "VSS": "GROUND",
        "D": "SIGNAL_INPUT",
        "Q": "SIGNAL_OUTPUT",
        "QB": "SIGNAL_OUTPUT",
        "CLK": "CLOCK_INPUT",
    },
}


def pin_role(module_name: str, pin_name: str) -> str:
    return MODULE_PIN_ROLE_REGISTRY.get(module_name, {}).get(pin_name, "UNKNOWN")


def write_module_pin_role_registry(json_path: Path, md_path: Path) -> dict[str, Any]:
    payload = {
        "registry_version": "M12C4A_PIN_ROLE_REGISTRY_V1",
        "modules": MODULE_PIN_ROLE_REGISTRY,
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# M12C4A Module Pin Role Registry", ""]
    for module_name, roles in MODULE_PIN_ROLE_REGISTRY.items():
        lines.append(f"## {module_name}")
        lines.append("")
        for pin_name, role_name in roles.items():
            lines.append(f"- `{pin_name}`: `{role_name}`")
        lines.append("")
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return payload
