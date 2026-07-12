from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    out_root = REPO_ROOT / "outputs/M12C4R2_dff_source_binding_gate/current_supported_config"
    assert list(out_root.rglob("*.gds")) == []


if __name__ == "__main__":
    main()
