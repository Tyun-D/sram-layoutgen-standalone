from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(".").resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from sram_layoutgen.openyield_adapter.m1_layoutgen_binding import (
        M1LayoutgenBindingConfig,
        M1LayoutgenBindingRunner,
    )

    M1LayoutgenBindingRunner(M1LayoutgenBindingConfig(repo_root=repo_root)).run()


if __name__ == "__main__":
    main()
