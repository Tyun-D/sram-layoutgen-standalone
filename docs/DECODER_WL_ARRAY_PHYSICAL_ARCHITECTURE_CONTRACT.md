# Decoder WL Array Physical Architecture Contract

- generated_at: `2026-08-03T17:29:44Z`
- array_side: `right`
- array_object_type: `approved_nonzero_physical_shell`
- row_pitch: `1.565`
- driver_size: `2.16 x 1.8875`
- legal_driver_orientations: `R0`
- decoder_stage_legal_orientations: `R0`

## WL Contract

- WL0-WL15 must remain monotonic and bit-exact.
- Driver outputs should align to array row Y centers and avoid staircase routing as a final architecture.
- Timing proxy thresholds are engineering limits only until authoritative timing contracts exist.
