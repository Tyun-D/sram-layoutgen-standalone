# OpenYield Power Intent

- VDD nets: VDD
- GND nets: GND, VSS
- array rail expectation: ARRAY_CORE, ARRAY_DUMMY, and ARRAY_REPLICA must expose rail directions compatible with later top-level stitching.
- row path rail expectation: ROW_PATH modules need rail continuity aligned with array-facing side placement.
- column path rail expectation: COLUMN_PATH modules need rail continuity aligned with array-facing column pitch placement.
- control path rail expectation: CONTROL_PATH rails remain periphery-distributed and must later stitch into top-level VDD/GND export.
- top-level export expectation: Top-level VDD/GND pins must be exported by a future R4 power planner using real geometry proof.

| module_name | has_power_pins | power_pin_names | rail_status | uses_candidate_geometry |
| --- | --- | --- | --- | --- |
| bitcell_array | True | GND;VDD | module_boundary_rails_exported | False |
| dummy_array | True | GND;VDD | module_boundary_rails_exported | False |
| replica_array | True | GND;VDD | module_boundary_rails_exported | False |
| row_decoder | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| wordline_decoder | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| decoder_gate_cells | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| wordline_driver | True | GND;VDD | hardmacro_wrapper_rail_metadata_exported | False |
| wordline_driver_gate_cells | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| column_mux | True | GND;VDD | hardmacro_wrapper_rail_metadata_exported | False |
| sense_amp | True | GND;VDD | hardmacro_wrapper_rail_metadata_exported | False |
| write_driver | True | GND;VDD | hardmacro_wrapper_rail_metadata_exported | False |
| precharge | True | VDD | hardmacro_wrapper_rail_metadata_exported | False |
| DELAY_CHAIN | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| PRECHARGE_ENABLE_PATH | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| SENSE_ENABLE_PATH | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| WRITE_ENABLE_PATH | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| WORDLINE_ENABLE_PATH | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| GATED_CLOCK_PATH | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| DFF_ROW | True | GND;VDD | candidate_row_rail_metadata_exported | True |
| CONTROL_LOGIC | True | GND;VDD | candidate_row_rail_metadata_exported | True |

