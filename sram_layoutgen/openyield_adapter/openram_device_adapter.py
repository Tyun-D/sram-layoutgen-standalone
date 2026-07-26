from __future__ import annotations

from pathlib import Path

from sram_layoutgen.openyield_adapter.openram_backend_context import OpenRamBackendContext


def build_backend_context(openram_root: Path) -> OpenRamBackendContext:
    return OpenRamBackendContext(openram_root)

