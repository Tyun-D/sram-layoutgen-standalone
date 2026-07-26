"""Composable physical-source contracts for OpenYield L1 closure.

These helpers do not generate final GDS.  They freeze stable, local physical
source contracts for leaf primitives that can be composed from already-known
base primitives.  The contract is strong enough for L1 source closure while
deferring row packing, abutment, and final module GDS work to L2/L3.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PrimitiveComposition:
    primitive_name: str
    source_type: str
    implementation_policy: str
    required_base_primitives: tuple[str, ...]
    ports: tuple[str, ...]
    generator_name: str
    physical_source_status: str
    source_evidence: tuple[str, ...]
    known_limitations: tuple[str, ...]
    later_layer_obligations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PrimitiveCompositionLibrary:
    library_name: str
    technology: str
    compositions: tuple[PrimitiveComposition, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "library_name": self.library_name,
            "technology": self.technology,
            "compositions": [item.to_dict() for item in self.compositions],
        }


def default_primitive_composition_library() -> PrimitiveCompositionLibrary:
    return PrimitiveCompositionLibrary(
        library_name="openyield_primitive_composition_library",
        technology="freepdk45",
        compositions=(
            PrimitiveComposition(
                primitive_name="nand3",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="nand4-derived generator with one input tied to VDD, or generated_cmos_gate fallback contract",
                required_base_primitives=("nand4",),
                ports=("A", "B", "C", "Z", "VDD", "GND"),
                generator_name="compose_nand3_from_nand4_tie_high",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "sram_compiler/subcircuits/standard_cell.py",
                    "sram_layoutgen/stdcell.py",
                ),
                known_limitations=(
                    "Tie-high input is a generator policy, not a signoff-proven hardmacro.",
                    "Do not claim LVS equivalence or final transistor matching in L1.",
                ),
                later_layer_obligations=(
                    "L2 must assign legal row packing, abutment, and rail stitching policy.",
                    "L3/L5 must verify the chosen nand3 composition against intended netlist semantics and signoff flows.",
                ),
            ),
            PrimitiveComposition(
                primitive_name="and3",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="nand3 + inv composition contract",
                required_base_primitives=("nand3", "inv"),
                ports=("A", "B", "C", "Z", "VDD", "GND"),
                generator_name="compose_and3_from_nand3_inv",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "sram_compiler/subcircuits/standard_cell.py",
                    "docs/mapping/openyield_time_control_decomposition_contract.json",
                ),
                known_limitations=(
                    "Composition is contract-backed only in L1; no final row-packing geometry is claimed.",
                ),
                later_layer_obligations=(
                    "L2 must close compositional bbox/orientation policy.",
                    "L3/L5 must verify composed polarity and timing behavior.",
                ),
            ),
            PrimitiveComposition(
                primitive_name="and2",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="nand2 + inv composition contract",
                required_base_primitives=("nand2", "inv"),
                ports=("A", "B", "Z", "VDD", "GND"),
                generator_name="compose_and2_from_nand2_inv",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "sram_compiler/subcircuits/standard_cell.py",
                    "sram_layoutgen/stdcell.py",
                ),
                known_limitations=(
                    "Geometry remains composition-policy only until L2 row packing.",
                ),
                later_layer_obligations=(
                    "L2 closes abutment/orientation policy.",
                ),
            ),
            PrimitiveComposition(
                primitive_name="buffer",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="inv + inv composition contract",
                required_base_primitives=("inv",),
                ports=("A", "Z", "VDD", "GND"),
                generator_name="compose_buffer_from_inv_chain",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "sram_compiler/subcircuits/standard_cell.py",
                    "sram_compiler/subcircuits/time_generate.py",
                ),
                known_limitations=(
                    "Drive-strength tuning is deferred; L1 closes only the physical-source contract.",
                ),
                later_layer_obligations=(
                    "L2/L3 choose drive staging and packed geometry.",
                ),
            ),
            PrimitiveComposition(
                primitive_name="decoder_leaf_gate",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="compose decoder leaves from inv/and2/and3 according to decoder-wordline contract",
                required_base_primitives=("inv", "and2", "and3"),
                ports=("A_dff[*]", "WL_pre[*]", "WL[*]", "VDD", "GND"),
                generator_name="compose_decoder_leaf_gate_bank",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
                    "sram_compiler/subcircuits/decoder.py",
                ),
                known_limitations=(
                    "Leaf group is compositional and not yet packed as a standalone hardmacro.",
                ),
                later_layer_obligations=(
                    "L2 packs rows and defines local abutment/orientation policy.",
                    "L3 emits standalone decoder module GDS if needed.",
                ),
            ),
            PrimitiveComposition(
                primitive_name="wordline_decoder_leaf_gate",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="compose wordline decoder leaves from inv/and3 according to decoder contract",
                required_base_primitives=("inv", "and3"),
                ports=("A_dff[*]", "DEC_WL[*]", "VDD", "GND"),
                generator_name="compose_wordline_decoder_leaf_gate_bank",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
                    "sram_compiler/subcircuits/decoder.py",
                ),
                known_limitations=("Leaf group only; no final packed geometry claimed in L1.",),
                later_layer_obligations=("L2 closes packed decoder-row policy.",),
            ),
            PrimitiveComposition(
                primitive_name="wordline_driver_leaf_gate",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="compose wordline driver leaves from nand2/inv or gen_wl_driver contract",
                required_base_primitives=("nand2", "inv", "wordline_driver"),
                ports=("A", "B", "Z", "VDD", "GND"),
                generator_name="compose_wordline_driver_leaf_gate_bank",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "sram_compiler/subcircuits/wordline_driver.py",
                    "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
                ),
                known_limitations=("Composition policy is frozen; placement is deferred.",),
                later_layer_obligations=("L2 defines row compaction and abutment.",),
            ),
            PrimitiveComposition(
                primitive_name="enable_path_leaf_gate",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="compose from TIME contract gates: inv, buffer, nand3, and3, delay_inv, precharge_cell as required",
                required_base_primitives=("inv", "buffer", "nand3", "and3", "delay_inv", "precharge_cell"),
                ports=("control_inputs", "PRE", "s_en", "w_en", "wl_en", "VDD", "GND"),
                generator_name="compose_enable_path_leaf_gate_from_time_contract",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "docs/mapping/openyield_control_path_semantic_contracts.csv",
                    "docs/mapping/openyield_time_control_decomposition_contract.json",
                    "sram_compiler/subcircuits/time_generate.py",
                ),
                known_limitations=(
                    "Composition is contract-backed and not yet routed or packed.",
                ),
                later_layer_obligations=(
                    "L2 closes path-local abutment and orientation.",
                    "L3 emits final path macro geometry only if standalone path GDS is required.",
                ),
            ),
            PrimitiveComposition(
                primitive_name="gated_clock_leaf_gate",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="compose from clkbuf / inv / and2 according to TIME contract",
                required_base_primitives=("inv", "buffer", "and2", "dff_cell"),
                ports=("clk", "cs", "gated_clk_buf", "gated_clk_bar", "VDD", "GND"),
                generator_name="compose_gated_clock_leaf_gate_from_time_contract",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "docs/mapping/openyield_control_path_semantic_contracts.csv",
                    "sram_compiler/subcircuits/time_generate.py",
                ),
                known_limitations=("Clock buffering strategy remains non-signoff at L1.",),
                later_layer_obligations=(
                    "L2 closes local row-domain placement policy.",
                    "L5 verifies gated-clock waveform and timing margin.",
                ),
            ),
            PrimitiveComposition(
                primitive_name="control_logic_leaf_gate",
                source_type="PYTHON_COMPOSITION_GENERATOR",
                implementation_policy="compose from TIME composite contract using inv, buffer, nand3, and2, and3, dff_cell, delay_inv",
                required_base_primitives=("inv", "buffer", "nand3", "and2", "and3", "dff_cell", "delay_inv"),
                ports=("clk", "csb", "web", "A[*]", "DIN[*]", "control_outputs", "VDD", "GND"),
                generator_name="compose_control_logic_leaf_gate_from_time_contract",
                physical_source_status="available_after_this_pass",
                source_evidence=(
                    "docs/mapping/openyield_time_control_decomposition_contract.json",
                    "docs/mapping/openyield_control_path_semantic_contracts.csv",
                    "sram_compiler/subcircuits/time_generate.py",
                ),
                known_limitations=(
                    "Composition fixes L1 source availability only; final geometry and timing proof remain open.",
                ),
                later_layer_obligations=(
                    "L2 closes packed control-row policy.",
                    "L3/L5 verify composed control logic against intended module behavior.",
                ),
            ),
        ),
    )


def load_primitive_composition_library(path: str | Path) -> PrimitiveCompositionLibrary:
    target = Path(path)
    if not target.exists():
        library = default_primitive_composition_library()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(library.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return library

    payload = json.loads(target.read_text(encoding="utf-8"))
    compositions = []
    for item in payload.get("compositions", []):
        compositions.append(
            PrimitiveComposition(
                primitive_name=str(item["primitive_name"]),
                source_type=str(item["source_type"]),
                implementation_policy=str(item["implementation_policy"]),
                required_base_primitives=tuple(item.get("required_base_primitives", [])),
                ports=tuple(item.get("ports", [])),
                generator_name=str(item["generator_name"]),
                physical_source_status=str(item["physical_source_status"]),
                source_evidence=tuple(item.get("source_evidence", [])),
                known_limitations=tuple(item.get("known_limitations", [])),
                later_layer_obligations=tuple(item.get("later_layer_obligations", [])),
            )
        )
    return PrimitiveCompositionLibrary(
        library_name=str(payload.get("library_name") or "openyield_primitive_composition_library"),
        technology=str(payload.get("technology") or "freepdk45"),
        compositions=tuple(compositions),
    )


def resolve_compositional_primitive(
    library: PrimitiveCompositionLibrary,
    primitive_name: str,
) -> PrimitiveComposition | None:
    for item in library.compositions:
        if item.primitive_name == primitive_name:
            return item
    return None


def is_physical_source_available(
    library: PrimitiveCompositionLibrary,
    primitive_name: str,
) -> bool:
    item = resolve_compositional_primitive(library, primitive_name)
    return item is not None and item.physical_source_status == "available_after_this_pass"


def emit_composition_contracts(
    library: PrimitiveCompositionLibrary,
) -> list[dict[str, Any]]:
    rows = []
    for item in library.compositions:
        rows.append(
            {
                "primitive_name": item.primitive_name,
                "source_type": item.source_type,
                "implementation_policy": item.implementation_policy,
                "required_base_primitives": ";".join(item.required_base_primitives),
                "ports": ";".join(item.ports),
                "generator_name": item.generator_name,
                "physical_source_status": item.physical_source_status,
                "source_evidence": ";".join(item.source_evidence),
                "known_limitations": ";".join(item.known_limitations),
                "later_layer_obligations": ";".join(item.later_layer_obligations),
            }
        )
    return rows
