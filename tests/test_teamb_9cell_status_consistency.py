from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from sram_layoutgen.openyield_adapter.teamb_9cell_input_lock import _resolve_bundle_artifact_path


def test_resolve_bundle_artifact_path_falls_back_to_connectivity_graph(tmp_path: Path) -> None:
    bundle = tmp_path / "AND2"
    bundle.mkdir()
    (bundle / "connectivity_graph.json").write_text("{}", encoding="utf-8")
    resolved = _resolve_bundle_artifact_path(
        bundle,
        "physical_connectivity_report.json",
        alternates=["connectivity_graph.json", "AND2_connectivity_graph.json"],
    )
    assert resolved.name == "connectivity_graph.json"
    assert resolved.exists()


def test_resolve_bundle_artifact_path_keeps_existing_primary(tmp_path: Path) -> None:
    bundle = tmp_path / "pdrive"
    bundle.mkdir()
    (bundle / "physical_connectivity_report.json").write_text("{}", encoding="utf-8")
    (bundle / "connectivity_graph.json").write_text("{}", encoding="utf-8")
    resolved = _resolve_bundle_artifact_path(
        bundle,
        "physical_connectivity_report.json",
        alternates=["connectivity_graph.json", "pdrive_connectivity_graph.json"],
    )
    assert resolved.name == "physical_connectivity_report.json"
    assert resolved.exists()


def test_resolve_bundle_artifact_path_returns_primary_when_no_candidates_exist(tmp_path: Path) -> None:
    bundle = tmp_path / "missing"
    bundle.mkdir()
    resolved = _resolve_bundle_artifact_path(
        bundle,
        "physical_connectivity_report.json",
        alternates=["connectivity_graph.json"],
    )
    assert resolved == bundle / "physical_connectivity_report.json"
    assert resolved.exists() is False
