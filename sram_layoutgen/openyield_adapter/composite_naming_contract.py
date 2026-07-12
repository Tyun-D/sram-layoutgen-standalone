from __future__ import annotations

import hashlib
from typing import Any


def build_composite_naming_contract() -> dict[str, Any]:
    templates = {
        "DFF": "DFF_L50_<topology_hash>",
        "DFF_BUF": "DFF_BUF_<child_variant_hash>",
        "ADDR_DFF": "ADDR_DFF_BITS<bit_count>_<topology_hash>",
        "DATA_DFF": "DATA_DFF_BITS<bit_count>_<topology_hash>",
        "PDRIVE": "PDRIVE_<stage_variant_sequence_hash>",
        "PDRIVE2_PRE": "PDRIVE2_PRE_<stage_variant_sequence_hash>",
        "WL_PDRIVE": "WL_PDRIVE_<stage_variant_sequence_hash>",
        "DELAY_CHAIN": "DELAY_CHAIN_ST<stage_count>_<variant_hash>",
        "TIME": "TIME_R<rows>_C<cols>_<operation>_<contract_hash>",
    }
    cache_fields = [
        "technology",
        "module_type",
        "operation",
        "rows",
        "cols",
        "bit_count",
        "stage_count",
        "ordered_child_physical_cells",
        "child_orientations",
        "placement_policy",
        "routing_contract_version",
        "power_policy",
        "topology_hash",
    ]
    matrix_rows = [{"module_type": key, "cache_identity_fields": "|".join(cache_fields)} for key in templates]
    return {
        "templates": templates,
        "cache_identity_fields": cache_fields,
        "matrix_rows": matrix_rows,
        "composite_naming_contract_locked": True,
        "composite_cache_contract_locked": True,
        "contract_hash": hashlib.sha256("|".join(cache_fields).encode("utf-8")).hexdigest()[:24],
    }
