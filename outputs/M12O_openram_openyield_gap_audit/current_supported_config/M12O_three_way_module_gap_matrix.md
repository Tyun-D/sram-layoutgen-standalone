# M12O Three Way Module Gap Matrix

- row_count: `22`

| module_or_function | exists_in_openram | exists_in_layoutgen_golden | exists_in_openyield | difference_type | blocking_level | recommended_action |
|---|---|---|---|---|---|---|
| bitcell_array | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|PARAMETERIZATION_UNKNOWN | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| dummy_array | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|PARAMETERIZATION_UNKNOWN | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| replica_array | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|PARAMETERIZATION_UNKNOWN | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| precharge | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|PARAMETERIZATION_UNKNOWN | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| sense_amp | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|PARAMETERIZATION_UNKNOWN | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| write_driver | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|PARAMETERIZATION_UNKNOWN | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| column_mux | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|PARAMETERIZATION_UNKNOWN | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| row_decoder | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|NETLIST_CONNECTIVITY_DIFFERS | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| wordline_decoder | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|NETLIST_CONNECTIVITY_DIFFERS | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| wordline_driver | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS|PARAMETERIZATION_UNKNOWN | MEDIUM | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| CONTROL_LOGIC | True | False | True | MODULE_MISSING_IN_LAYOUTGEN|CONTROL_LOGIC_DECOMPOSITION_DIFFERS | HIGH | Lock OpenYield authoritative top netlist before promoting this module into parameterized planning. |
| DELAY_CHAIN | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS | LOW | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| DFF_ROW | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS | LOW | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| GATED_CLOCK_PATH | True | False | True | MODULE_MISSING_IN_LAYOUTGEN|CONTROL_LOGIC_DECOMPOSITION_DIFFERS | HIGH | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| PRECHARGE_ENABLE_PATH | True | False | True | MODULE_MISSING_IN_LAYOUTGEN|CONTROL_LOGIC_DECOMPOSITION_DIFFERS | HIGH | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| SENSE_ENABLE_PATH | True | False | True | MODULE_MISSING_IN_LAYOUTGEN|CONTROL_LOGIC_DECOMPOSITION_DIFFERS | HIGH | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| WRITE_ENABLE_PATH | True | False | True | MODULE_MISSING_IN_LAYOUTGEN|CONTROL_LOGIC_DECOMPOSITION_DIFFERS | HIGH | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| WORDLINE_ENABLE_PATH | True | False | True | MODULE_MISSING_IN_LAYOUTGEN|CONTROL_LOGIC_DECOMPOSITION_DIFFERS | HIGH | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| decoder_gate_cells | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS | LOW | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| wordline_driver_gate_cells | True | True | True | MODULE_PRESENT_BUT_PHYSICAL_DIFFERS | LOW | Keep as audited reference only until netlist authority and parameter mapping are locked. |
| top-level pins | True | True | False | MODULE_MISSING_IN_OPENYIELD_PHYSICAL|NETLIST_CONNECTIVITY_DIFFERS | MEDIUM | Lock OpenYield authoritative top netlist before promoting this module into parameterized planning. |
| VDD/GND rails | True | True | True | NETLIST_CONNECTIVITY_DIFFERS | MEDIUM | Lock OpenYield authoritative top netlist before promoting this module into parameterized planning. |
