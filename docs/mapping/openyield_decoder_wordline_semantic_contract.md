# OpenYield Decoder Wordline Semantic Contract

## Flow

- address A[i] -> ADDR_DFF -> A_dff[i]
- A_dff[i] -> DECODER_CASCADE
- DECODER_CASCADE -> DEC_WL[i]
- CONTROL_LOGIC.wl_en -> WORDLINEDRIVER.B
- DEC_WL[i] -> WORDLINEDRIVER.A
- WORDLINEDRIVER.Z -> WL[i]
- WL[i] -> bitcell_array.WL[i]

## Signal Contracts

| signal | source | sink | role |
| --- | --- | --- | --- |
| A[i] | SRAM_TOP | DFF_ROW | address_input |
| A_dff[i] | DFF_ROW | row_decoder | registered_row_address |
| DEC_WL[i] | row_decoder | wordline_driver.A | decoded_wordline_intent |
| wl_en | CONTROL_LOGIC | wordline_driver.B | wordline_enable |
| WL[i] | wordline_driver.Z | bitcell_array.WL[i] | physical_wordline |
