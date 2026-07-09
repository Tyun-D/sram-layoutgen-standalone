# M11C SRAM Spec

- word_size: `8`
- num_words: `64`
- words_per_row: `4`
- num_rows: `16` sourced from `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json:last_M8_report.num_rows`
- num_cols: `32` sourced from `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json:last_M8_report.num_cols`
- substitution_scope: `sense_amp`
- excluded_modules: `wordline_driver, column_mux, write_driver, CONTROL_LOGIC`
- baseline_gds: `outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds`
- golden_reference_gds: `outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`
- openyield_sense_amp_gds_path: `outputs/openyield_module_gds/sense_amp/sense_amp.gds`
