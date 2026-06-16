"""Optional OpenYield validation backend adapters.

This package intentionally does not import OpenYield at module import time.
The SRAM GDS/layout generator must remain runnable when OpenYield, PySpice,
Xyce, or their conda environment are absent.
"""

from .config_export import OpenYieldExportConfig, export_config_from_report
from .contracts import ModuleContract, ParsedPySpiceModule, PinContract
from .module_mapper import build_module_contracts, module_to_contract
from .netlist_export import OpenYieldNetlistExport, export_netlist_for_openyield
from .pyspice_source_parser import parse_openyield_pyspice_sources, parse_pyspice_source_file
from .result_parser import parse_openyield_results
from .testbench_adapter import OpenYieldEnvironment, check_openyield_environment, generate_smoke_testbench

__all__ = [
    "ModuleContract",
    "OpenYieldEnvironment",
    "OpenYieldExportConfig",
    "OpenYieldNetlistExport",
    "ParsedPySpiceModule",
    "PinContract",
    "build_module_contracts",
    "check_openyield_environment",
    "export_config_from_report",
    "export_netlist_for_openyield",
    "generate_smoke_testbench",
    "module_to_contract",
    "parse_openyield_pyspice_sources",
    "parse_pyspice_source_file",
    "parse_openyield_results",
]
