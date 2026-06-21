"""Optional OpenYield validation backend adapters.

This package intentionally does not import OpenYield at module import time.
The SRAM GDS/layout generator must remain runnable when OpenYield, PySpice,
Xyce, or their conda environment are absent.
"""

from .contracts import ModuleContract, ParsedPySpiceModule, PinContract
from .macro_compat import MacroCompatibility, MacroPinCheck, check_contract_payload
from .module_mapper import build_module_contracts, module_to_contract
from .pyspice_source_parser import parse_openyield_pyspice_sources, parse_pyspice_source_file

__all__ = [
    "ModuleContract",
    "MacroCompatibility",
    "MacroPinCheck",
    "ParsedPySpiceModule",
    "PinContract",
    "build_module_contracts",
    "check_contract_payload",
    "module_to_contract",
    "parse_openyield_pyspice_sources",
    "parse_pyspice_source_file",
]

try:
    from .config_export import OpenYieldExportConfig, export_config_from_report
except ModuleNotFoundError:
    pass
else:
    __all__.extend(["OpenYieldExportConfig", "export_config_from_report"])

try:
    from .netlist_export import OpenYieldNetlistExport, export_netlist_for_openyield
except ModuleNotFoundError:
    pass
else:
    __all__.extend(["OpenYieldNetlistExport", "export_netlist_for_openyield"])

try:
    from .result_parser import parse_openyield_results
except ModuleNotFoundError:
    pass
else:
    __all__.append("parse_openyield_results")

try:
    from .testbench_adapter import OpenYieldEnvironment, check_openyield_environment, generate_smoke_testbench
except ModuleNotFoundError:
    pass
else:
    __all__.extend(["OpenYieldEnvironment", "check_openyield_environment", "generate_smoke_testbench"])

try:
    from .time_control_experimental_contract import (
        TimeControlExperimentalConfigSurface,
        TimeControlExperimentalContract,
        TimeControlPrototypeSubplan,
        build_time_control_experimental_contract,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.extend(
        [
            "TimeControlExperimentalConfigSurface",
            "TimeControlExperimentalContract",
            "TimeControlPrototypeSubplan",
            "build_time_control_experimental_contract",
        ]
    )

try:
    from .time_control_abstract_floorplan_payload import (
        AbstractFloorplanHandoff,
        AbstractFloorplanRegion,
        AbstractFloorplanSubblock,
        TimeControlAbstractFloorplanPayload,
        build_time_control_abstract_floorplan_payload,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.extend(
        [
            "AbstractFloorplanHandoff",
            "AbstractFloorplanRegion",
            "AbstractFloorplanSubblock",
            "TimeControlAbstractFloorplanPayload",
            "build_time_control_abstract_floorplan_payload",
        ]
    )

try:
    from .time_control_packing_invariants import build_time_control_packing_invariant_report
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_packing_invariant_report")

try:
    from .time_control_payload_completeness import build_time_control_payload_completeness_report
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_payload_completeness_report")

try:
    from .time_control_payload_consumption_contract import (
        build_time_control_payload_consumption_contract_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_payload_consumption_contract_report")

try:
    from .time_control_payload_materialization_boundary import (
        build_time_control_payload_materialization_boundary_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_payload_materialization_boundary_report")

try:
    from .time_control_prototype_execution_guard import (
        build_time_control_prototype_execution_guard_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_prototype_execution_guard_report")

try:
    from .time_control_prototype_state_machine import (
        build_time_control_prototype_state_machine_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_prototype_state_machine_report")

try:
    from .time_control_prototype_interface_surface import (
        build_time_control_prototype_interface_surface_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_prototype_interface_surface_report")

try:
    from .time_control_goal_progress_audit import (
        build_time_control_goal_progress_audit_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_goal_progress_audit_report")

try:
    from .time_control_prototype_artifact_contract import (
        build_time_control_prototype_artifact_contract_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_prototype_artifact_contract_report")

try:
    from .time_control_builder_output_regression import (
        build_time_control_builder_output_regression_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_builder_output_regression_report")

try:
    from .time_control_final_boundary_summary import (
        build_time_control_final_boundary_summary_report,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.append("build_time_control_final_boundary_summary_report")
