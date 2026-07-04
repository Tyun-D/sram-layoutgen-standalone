# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Stage

- current_stage: `T1`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 3. M5 Human Review

- Current GDS is visually cluttered by OpenYield/M5 debug text labels.
- The physical hierarchy still mainly uses layoutgen cells.
- Current evidence does not yet prove the final GDS is truly generated from the OpenYield netlist.
- OpenYield-to-layoutgen integration must be proven by a netlist-to-layout trace, not by text labels.
- Bitcell power rail merging / rail continuity appears not fully restored in the generated GDS.
- Next immediate work is cleanup + complete OpenYield file inventory, not another integration attempt.

## 4. T1 Result

- clean_review_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/T1_clean_m5_review/current_supported_config/openyield_layoutgen_integrated_sram_clean_review.gds`
- clean_gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- removed_text_count: `74`
- physical_shape_preserved: `True`
- cell_hierarchy_preserved: `True`
- openyield_file_count_total: `130`
- openyield_source_file_count: `94`
- openyield_netlist_candidate_file_count: `37`

## 5. Next Immediate Task

先对 clean review GDS 做人工 KLayout 复核，再进入 netlist-to-layout translator 设计；在此之前不进入下一阶段。详见 `/data1/qujh/work/sram_layoutgen_step45_clean/docs/T1_openyield_full_file_report.md`。
