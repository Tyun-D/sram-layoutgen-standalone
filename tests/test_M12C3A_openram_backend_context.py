from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.openram_device_adapter import build_backend_context


def main() -> int:
    with build_backend_context(Path("/data1/qujh/OpenRAM")) as ctx:
        report = ctx.runtime_report().as_dict()
        assert report["openram_bootstrap_passed"] is True
        assert report["openram_license_type"] == "BSD-3-Clause"
        handles = ctx.import_handles()
        assert handles["pinv"] is not None
        assert handles["ptx"] is not None
        assert handles["contact"] is not None
    print("M12C3A_openram_backend_context_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

