# S0 Project Status Reset Summary

- `openyield_complete_sram.gds` 已降级为 access-view prototype。
- 后续路线改为：layoutgen-based OpenYield route。
- 每阶段必须先读/更新 `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json`。
- 每阶段必须产出 review GDS，并等待人工 KLayout 确认后才能进入下一阶段。
- 本次 review GDS manifest: `outputs/project_status_reset_review/current_supported_config/review_gds_manifest.json`
