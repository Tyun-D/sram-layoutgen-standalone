from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.dff_array_adapter import (  # noqa: E402
    build_dff_array_adapter_markdown,
    build_dff_array_adapter_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield DFF/ADDR_DFF/DATA_DFF adapter compatibility.")
    parser.add_argument("--openyield-root", default="third_party/OpenYield")
    parser.add_argument("--contracts", default="docs/openyield_module_contracts.json")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--out-json", default="docs/openyield_dff_array_adapter_report.json")
    parser.add_argument("--out-md", default="docs/openyield_dff_array_adapter_report.md")
    args = parser.parse_args()

    report = build_dff_array_adapter_report(
        resolve_input(args.openyield_root),
        resolve_input(args.contracts),
        resolve_input(args.tech_dir),
    )
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_dff_array_adapter_markdown(report), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(
        "safe_for_metadata_plan="
        f"{report['dff_adapter_safe_for_metadata_plan']} "
        f"metadata_placement={report['dff_array_can_enter_metadata_placement']} "
        f"standalone_placement={report['dff_array_can_enter_standalone_placement']}"
    )
    return 0


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return path


def resolve_output(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else STANDALONE_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
