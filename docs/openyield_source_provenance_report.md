# OpenYield Source Provenance Report

- Main repo path: `/data1/qujh/work/sram_layoutgen_step45_clean`
- Main repo HEAD: `fc85009cd68cacd4c682ec2cdadb576a2583bdb3`
- OpenYield source path: `/data1/qujh/work/external/OpenYield`
- OpenYield remote URL: `https://github.com/ShenShan123/OpenYield.git`
- OpenYield branch: `main`
- OpenYield HEAD: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- OpenYield latest commit message: `完善等效电路`

## Source Evidence

- `time_generate.py` found: `/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py`
- `DelayChain` found: `time_generate.py:299`
- `Pinv` found: `standard_cell.py:5`
- `sram_compiler` tree found: `True`

## Source Presence Summary

```json
{
  "source_files_found": [
    "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py",
    "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/standard_cell.py",
    "/data1/qujh/work/external/OpenYield/sram_compiler"
  ],
  "source_files_missing": []
}
```

## Boundary Assertions

```json
{
  "openyield_source_committed_into_main_repo": false,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```

## Gates

```json
{
  "openyield_source_available": true,
  "openyield_source_path": "/data1/qujh/work/external/OpenYield",
  "openyield_remote_available": true,
  "openyield_remote_url": "https://github.com/ShenShan123/OpenYield.git",
  "openyield_head_recorded": true,
  "time_generate_py_found": true,
  "delay_chain_source_found": true,
  "pinv_source_found": true,
  "source_provenance_report_available": true,
  "evidence_timeline_updated": true,
  "milestone_summary_updated": true,
  "can_reproduce_candidate_spice_from_source": false,
  "can_enter_delay_chain_transient_smoke": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_claim_openyield_full_integration_now": false
}
```
