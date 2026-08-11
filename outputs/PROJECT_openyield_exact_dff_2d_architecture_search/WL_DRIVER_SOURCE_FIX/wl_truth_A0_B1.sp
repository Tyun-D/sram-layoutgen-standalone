.include /tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/outputs/PROJECT_openyield_exact_dff_2d_architecture_search/SOURCE_AUTHORITY/canonical_spice/wl_driver_openyield_original.sp
VDD VDD 0 1.0
VA A 0 0
VB B 0 1
X1 VDD 0 A B WL wl_driver_openyield_original
Cwl WL 0 2f
.tran 1p 0.2n
.measure tran wl_val FIND v(WL) AT=0.1n
.end
