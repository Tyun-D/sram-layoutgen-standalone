# OpenYield Column Path Intent

- physical_role: `COLUMN_PATH`
- modules: precharge, column_mux, sense_amp, write_driver
- precharge alignment: precharge must align to BL/BR column pitch and sit on the bitline-side of the column path.
- column mux relation: column_mux is structurally required only when words_per_row > 1 or column_mux_ratio > 1 in a future supported config.
- pitch expectation: Entire column path must be anchored on array column pitch, not on standalone wrapper width.
- BL/BR routing expectation: BL/BR and optional BL_out/BR_out must remain explicit R3/R4 routed nets with column-pitch alignment.
- metadata status: Existing hardmacro wrappers provide reference bbox/pins/rails, but do not yet prove structure-complete column-path composition.

## R3/R4 Required Work

- R3 must define real column-path composition rules relative to ARRAY_CORE column pitch.
- R4 must define BL/BR, mux-select, sense, and write routing ownership.
- R4 must define whether spare/replica timing coupling is explicit or out of current scope.
