"""Create or refresh the replacement macro manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sram_layoutgen.brick_library import materialize_generated_bricks  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="overwrite the replacement macro manifest")
    args = parser.parse_args()
    written = materialize_generated_bricks(ROOT, force=args.force)
    if written:
        print("Wrote replacement macro manifest:")
        for path in written:
            print(path)
    else:
        print("Replacement macro manifest already exists; use --force to refresh it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
