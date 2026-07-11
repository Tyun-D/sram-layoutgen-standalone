# M12C3 Existing Layout Generator Inventory

- source_path=/data1/qujh/OpenRAM/compiler/modules/ptx.py, reuse_feasibility=TRUSTED_REUSE_CANDIDATE, recommended_role=Trusted device generator backend
- source_path=/data1/qujh/OpenRAM/compiler/base/contact.py, reuse_feasibility=TRUSTED_REUSE_CANDIDATE, recommended_role=Trusted contact/via backend
- source_path=/data1/qujh/OpenRAM/compiler/modules/pinv.py, reuse_feasibility=TRUSTED_REUSE_CANDIDATE, recommended_role=Trusted gate generator backend for PINV family
- source_path=/data1/qujh/OpenRAM/compiler/modules/tri_gate.py, reuse_feasibility=REFERENCE_ONLY, recommended_role=Reference for tri-state concepts, not direct primitive generator
- source_path=/data1/qujh/OpenRAM/compiler/modules/dff.py, reuse_feasibility=REFERENCE_ONLY, recommended_role=Reference for DFF interface only
- source_path=/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/stdcell.py, reuse_feasibility=PROXY_ONLY_DO_NOT_USE, recommended_role=Reference geometry only
- source_path=/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/openyield_adapter/module_gds_generators.py, reuse_feasibility=REFERENCE_ONLY, recommended_role=Audit/reference only
- source_path=/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/openyield_adapter/primitive_composition_generators.py, reuse_feasibility=REFERENCE_ONLY, recommended_role=Planning helper only
- source_path=/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/tech/freepdk45.lydrc, reuse_feasibility=REFERENCE_ONLY, recommended_role=Qualification deck only
- source_path=/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py, reuse_feasibility=REFERENCE_ONLY, recommended_role=Logical primitive contract source
- source_path=/data1/qujh/work/sram_layoutgen_step45_clean/scripts/M11W_wordline_driver_wrapper_pin_repair.py, reuse_feasibility=REFERENCE_ONLY, recommended_role=Repair evidence only
