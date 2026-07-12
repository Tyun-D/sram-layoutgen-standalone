from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


CANONICAL_DFF_TOPOLOGY_IDENTITY_VERSION = "M12C4AC_CANONICAL_DFF_TOPOLOGY_IDENTITY_V1"


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_canonical_dff_topology_payload(
    *,
    binding_rows: list[dict[str, Any]],
    corrected_net_contract: dict[str, Any],
    top_pin_order: list[str],
    internal_net_order: list[str],
    module_pin_role_registry: dict[str, Any],
    openyield_files: list[Path],
) -> dict[str, Any]:
    ordered_rows = []
    for row in binding_rows:
        ordered_rows.append(
            {
                "instance_name": row["instance_name"],
                "child_logical_module": row["child_logical_module"],
                "child_pin_order": json.loads(row["child_pin_order"]) if isinstance(row["child_pin_order"], str) else row["child_pin_order"],
                "parent_net_connections": json.loads(row["parent_net_connections"]) if isinstance(row["parent_net_connections"], str) else row["parent_net_connections"],
                "source_line": int(row["source_line"]),
            }
        )
    provenance = []
    for path in openyield_files:
        provenance.append({"path": str(path), "sha256": _file_sha(path)})
    return {
        "schema_version": CANONICAL_DFF_TOPOLOGY_IDENTITY_VERSION,
        "top_pin_order": list(top_pin_order),
        "internal_net_order": list(internal_net_order),
        "ordered_child_instances": ordered_rows,
        "module_pin_role_registry_version": module_pin_role_registry.get("schema_version", "UNKNOWN"),
        "top_pin_contracts": corrected_net_contract["top_pin_contracts"],
        "internal_net_contracts": {name: corrected_net_contract["internal_nets"][name] for name in internal_net_order},
        "openyield_source_provenance": provenance,
    }


def canonical_dff_topology_hash(payload: dict[str, Any], length: int = 12) -> str:
    serialized = json.dumps(payload, indent=None, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:length]


def write_canonical_identity(payload: dict[str, Any], json_path: Path, md_path: Path) -> str:
    topology_hash = canonical_dff_topology_hash(payload)
    wrapped = {"source_topology_hash": topology_hash, "payload": payload}
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(wrapped, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# M12C4AC Canonical DFF Topology Identity",
                "",
                f"- schema_version: `{payload['schema_version']}`",
                f"- source_topology_hash: `{topology_hash}`",
                f"- ordered_child_instance_count: `{len(payload['ordered_child_instances'])}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return topology_hash

