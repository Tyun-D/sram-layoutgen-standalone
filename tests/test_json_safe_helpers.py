from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.pnand2_verification_gate import json_safe


@dataclass
class _Payload:
    root: Path
    nested: dict[str, object]


def test_json_safe_converts_path_objects() -> None:
    payload = {
        "path": Path("/tmp/example"),
        "items": [Path("/tmp/a"), {"inner": Path("/tmp/b")}],
    }
    converted = json_safe(payload)
    assert converted == {
        "path": "/tmp/example",
        "items": ["/tmp/a", {"inner": "/tmp/b"}],
    }


def test_json_safe_converts_nested_dataclass() -> None:
    payload = _Payload(
        root=Path("/tmp/root"),
        nested={
            "more": [Path("/tmp/c"), {"leaf": Path("/tmp/d")}],
        },
    )
    converted = json_safe(payload)
    assert converted == {
        "root": "/tmp/root",
        "nested": {
            "more": ["/tmp/c", {"leaf": "/tmp/d"}],
        },
    }
