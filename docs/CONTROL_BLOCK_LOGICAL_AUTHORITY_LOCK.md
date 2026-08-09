# Control Block Logical Authority Lock

- parent logical block: `CONTROL_BLOCK_HIERARCHICAL_V1`
- source file: `docs/mapping/M12C4R2_config_active_net_connection_matrix_16x16.csv`
- source SHA256: `136d0be48e607909e8e42a80fc3f67a51f2d3ed639bf012e3562371d3178bc33`
- monolithic control_logic required: `false`
- authority: `CURRENT_SOURCE_EXACT` for source matrix rows; physical expansion of ADDR/DATA DFF rows is `DERIVED_FROM_EXACT_RELATIONS`.

| instance | logical module | physical module |
|---|---|---|
| `addr_dff_0` | `ADDR_DFF_BIT` | `DFF_BUF` |
| `addr_dff_1` | `ADDR_DFF_BIT` | `DFF_BUF` |
| `addr_dff_2` | `ADDR_DFF_BIT` | `DFF_BUF` |
| `addr_dff_3` | `ADDR_DFF_BIT` | `DFF_BUF` |
| `data_dff_0` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_1` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_2` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_3` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_4` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_5` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_6` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_7` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_8` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_9` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_10` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_11` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_12` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_13` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_14` | `DATA_DFF_BIT` | `DFF_BUF` |
| `data_dff_15` | `DATA_DFF_BIT` | `DFF_BUF` |
| `clkbuf` | `pdrive` | `pdrive` |
| `inv_clk_bar` | `PINV` | `PINV` |
| `dff_buf` | `DFF_BUF` | `DFF_BUF` |
| `dff_buf1` | `DFF_BUF` | `DFF_BUF` |
| `and2_gated_clk_bar` | `AND2` | `AND2` |
| `and2_gated_clk_buf` | `AND2` | `AND2` |
| `wl_en` | `wl_pdrive` | `wl_pdrive` |
| `inv_wl_en_bar` | `PINV` | `PINV` |
| `delaychain` | `delay_chain` | `delay_chain` |
| `inv_rbl_delay_bar` | `PINV` | `PINV` |
| `w_en` | `AND3` | `AND3` |
| `s_en` | `AND3` | `AND3` |
| `pre_unbuf` | `PNAND3` | `PNAND3` |
| `pre` | `pdrive2_for_pre` | `pdrive2_for_pre` |
