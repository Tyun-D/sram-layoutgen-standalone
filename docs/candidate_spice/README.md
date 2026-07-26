# Candidate SPICE Templates

These files are planning-only candidate artifacts.

```spice
* CANDIDATE / PLANNING-ONLY
* NOT VALIDATED SPICE
* NOT TIMING PROOF
* DO NOT CLAIM TIMING CLOSURE
* REQUIRES MANUAL REVIEW, PDK MODEL BINDING, AND CHARACTERIZATION
```

- Directory: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\candidate_spice`
- `can_generate_candidate_spice=True`
- `can_run_ngspice_or_hspice_now=False`
- `missing_required_external_file=none_for_model_binding`
- `needs_teacher_or_project_provider=False`

## Found model binding

- Preferred include: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include`
- Direct TT PMOS include: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_VTG.inc`
- Direct TT NMOS include: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_VTG.inc`
- `can_bind_openyield_model_names_directly=True`

## Emitted files

- `gen_delay_inv_candidate.sp`
- `delay_chain_symbolic_tb.sp`
- `delay_chain_measure.inc`
- `delay_chain_corner_placeholder.inc`

## Still missing before any real simulation

- Project-specified simulator: ngspice / hspice / spectre
- Project-specified VDD
- Project-specified PVT corner
- Measurement threshold policy, e.g. 50% VDD or 10%-90% slew
- Manual review of candidate `gen_delay_inv` subckt against source and project signoff expectations

## Source-backed context

- `next_recommended_proof_task` from recovery: `four_load_inverter_stage_model_plan`
- `recommended_planning_binding` from four-load model: `same_source_Pinv_as_delay_stage`
