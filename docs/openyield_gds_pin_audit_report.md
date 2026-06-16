# OpenYield GDS Pin And Rail Audit

This report reads local GDS TEXT labels and BOUNDARY/PATH bboxes with a read-only internal GDSII parser. It does not write GDS, modify placement/routing, or change OpenYield source.

## Reader

- reader: `internal_gdsii_text_boundary_parser`
- limitations:
  - Extracts TEXT, BOUNDARY, and PATH bboxes only.
  - Does not flatten hierarchy or prove electrical connectivity.
  - Pin shapes are inferred from same-layer shapes containing or near the TEXT label.

## Summary

- audited GDS macros: `14`
- rail status counts: `{"rail_abutment_ready": 3, "rail_needs_manual_review": 11}`
- abutment readiness counts: `{"abutment_ready": 3, "unknown_need_gds_pin_audit": 11}`
- macros ready for aggregation: `cell_1rw, dummy_cell_1rw, replica_cell_1rw`
- macros needing manual confirmation: `dff, gen_col_mux, gen_delay_inv, gen_inv, gen_nand2, gen_nand4, gen_precharge, gen_wl_driver, sense_amp, tri_gate, write_driver`

## Macro Audit

| macro | reader | bbox | width | height | labels | pin sides | rail status | power sides | share rails | abutment | semantic flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cell_1rw | ok | (-0.095,-0.1)-(0.8,1.465) | 0.895 | 1.5650000000000002 | 7 | vdd:top, gnd:bottom, bl:bottom, br:bottom, wl:left | rail_abutment_ready | vdd:top gnd:bottom | LR:False TB:True | abutment_ready | - |
| dff | ok | (0,-0.1)-(2.86,2.57) | 2.8599999999999826 | 2.6699999999999835 | 5 | vdd:top, gnd:bottom, d:left, dout:right, clk:internal | rail_needs_manual_review | vdd:top gnd:bottom | LR:False TB:False | unknown_need_gds_pin_audit | - |
| dummy_cell_1rw | ok | (-0.095,-0.1)-(0.8,1.465) | 0.894999999999988 | 1.564999999999979 | 5 | vdd:top, gnd:bottom, bl:bottom, br:bottom, wl:left | rail_abutment_ready | vdd:top gnd:bottom | LR:False TB:True | abutment_ready | - |
| gen_col_mux | ok | (-0.08,-0.08)-(0.7375,1.8) | 0.8175 | 1.8800000000000001 | 9 | vdd:unknown, gnd:right, bl:top, br:top, mux_out:bottom, mux_out_b:right, column_select:bottom | rail_needs_manual_review | vdd:unknown gnd:right | LR:False TB:False | unknown_need_gds_pin_audit | missing_power_metadata |
| gen_delay_inv | ok | (-0.08,-0.08)-(0.7425,2.505) | 0.8225 | 2.585 | 10 | a:left, z:right, gnd:bottom, vdd:top | rail_needs_manual_review | vdd:top gnd:bottom | LR:False TB:False | unknown_need_gds_pin_audit | - |
| gen_inv | ok | (-0.08,-0.08)-(0.7425,1.4) | 0.8225 | 1.4800000000000002 | 10 | a:left, z:right, gnd:bottom, vdd:top | rail_needs_manual_review | vdd:top gnd:bottom | LR:False TB:False | unknown_need_gds_pin_audit | - |
| gen_nand2 | ok | (-0.08,-0.08)-(0.9575,1.4) | 1.0375 | 1.4800000000000002 | 14 | vdd:top, gnd:bottom, a:left, b:internal, z:right | rail_needs_manual_review | vdd:top gnd:bottom | LR:False TB:False | unknown_need_gds_pin_audit | - |
| gen_nand4 | ok | (0,0)-(2.6,1.565) | 2.5999999999999996 | 1.5649999999999997 | 0 | vdd:unknown, gnd:unknown, a:unknown, b:unknown, c:unknown, d:unknown, z:unknown | rail_needs_manual_review | vdd:unknown gnd:unknown | LR:False TB:False | unknown_need_gds_pin_audit | - |
| gen_precharge | ok | (-0.08,-0.08)-(0.705,1.34) | 0.7849999999999999 | 1.4200000000000002 | 7 | vdd:top, precharge_enb:bottom, bl:left, br:right | rail_needs_manual_review | vdd:top gnd:missing | LR:False TB:False | unknown_need_gds_pin_audit | - |
| gen_wl_driver | ok | (-0.08,-0.105)-(2.965,1.4) | 3.045 | 1.5050000000000001 | 35 | vdd:top, gnd:bottom, decoder_input:left, wordline_enable:left, wl:bottom | rail_needs_manual_review | vdd:top gnd:bottom | LR:False TB:False | unknown_need_gds_pin_audit | - |
| replica_cell_1rw | ok | (-0.095,-0.1)-(0.8,1.465) | 0.894999999999988 | 1.564999999999979 | 5 | vdd:top, gnd:bottom, rbl:bottom, rblb:bottom, wl:left | rail_abutment_ready | vdd:top gnd:bottom | LR:False TB:True | abutment_ready | - |
| sense_amp | ok | (-0.035,0)-(0.74,6.01) | 0.7749999999999954 | 6.009999999999963 | 7 | vdd:left, gnd:right, sense_enable:top, bl:bottom, br:bottom, dout:left, dout_b:unknown | rail_needs_manual_review | vdd:left gnd:right | LR:False TB:False | unknown_need_gds_pin_audit | senseamp_in_to_bl_confirmed, senseamp_inb_to_br_confirmed, senseamp_q_to_dout_confirmed, architecture_adapter_required, senseamp_qb_dout_b_missing |
| tri_gate | ok | (0,0)-(0.74,2.975) | 0.7399999999999956 | 2.974999999999982 | 7 | din:top, dout:bottom, en:left, enb:left, vdd:right, gnd:right | rail_needs_manual_review | vdd:right gnd:right | LR:False TB:False | unknown_need_gds_pin_audit | - |
| write_driver | ok | (-0.1,0)-(0.74,4.175) | 0.839999999999995 | 4.174999999999975 | 6 | vdd:left, gnd:left, write_enable:bottom, din:bottom, bl:top, br:top | rail_needs_manual_review | vdd:left gnd:left | LR:False TB:False | unknown_need_gds_pin_audit | - |

## Pin Details

| macro | pin | canonical | layer | side | distance | shape source | shape bbox |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cell_1rw | VDD | vdd | 11/texttype0 | top | 0.10000000000000009 | label_plus_shape | (-0.09,1.333)-(0.795,1.397) |
| cell_1rw | VSS | gnd | 11/texttype0 | bottom | 0.1 | label_plus_shape | (-0.09,-0.0325)-(0.795,0.0325) |
| cell_1rw | BL | bl | 13/texttype0 | bottom | 0.10300000000000001 | label_plus_shape | (0.15,-0.08)-(0.22,1.465) |
| cell_1rw | BLB | br | 13/texttype0 | bottom | 0.10300000000000001 | label_plus_shape | (0.485,-0.08)-(0.555,1.465) |
| cell_1rw | WL | wl | 11/texttype0 | left | 0.045 | label_plus_shape | (-0.09,0.1275)-(0.795,0.1925) |
| dff | VDD | vdd | 11/texttype0 | top | 0.037499999999999645 | label_plus_shape | (0.1,1.267)-(2.86,2.535) |
| dff | VSS | gnd | 11/texttype0 | bottom | 0.14249999999999913 | label_plus_shape | (0.1,-0.065)-(2.76,0.9875) |
| dff | D | d | 13/texttype0 | left | 0.2949999999999982 | label_plus_shape | (0.245,1.037)-(0.3225,1.172) |
| dff | Q | dout | 13/texttype0 | right | 0.17499999999999893 | label_plus_shape | (2.632,1.047)-(2.71,1.182) |
| dff | CLK | clk | 13/texttype0 | internal | 1.001249999999994 | label_plus_shape | (1.82,1.037)-(1.897,1.172) |
| dummy_cell_1rw | VDD | vdd | 11/texttype0 | top | 0.09999999999999853 | label_plus_shape | (-0.09,1.332)-(0.795,1.397) |
| dummy_cell_1rw | VSS | gnd | 11/texttype0 | bottom | 0.09999999999999866 | label_plus_shape | (0.285,-0.0325)-(0.42,0.0325) |
| dummy_cell_1rw | BL | bl | 13/texttype0 | bottom | 0.10299999999999862 | label_plus_shape | (0.1575,-0.025)-(0.2125,0.0275) |
| dummy_cell_1rw | BLB | br | 13/texttype0 | bottom | 0.10299999999999862 | label_plus_shape | (0.4925,-0.0325)-(0.55,0.0275) |
| dummy_cell_1rw | WL | wl | 11/texttype0 | left | 0.044999999999999395 | label_plus_shape | (-0.085,0.13)-(-0.0325,0.1925) |
| gen_col_mux | VDD | vdd | unknown | unknown | None | missing | - |
| gen_col_mux | gnd | gnd | 11/texttype0 | right | 0.032500000000000084 | label_plus_shape | (0.6725,0.8375)-(0.7375,0.9025) |
| gen_col_mux | BL | bl | 13/texttype0 | top | 0.07000000000000006 | label_plus_shape | (0.14,1.66)-(0.21,1.8) |
| gen_col_mux | BR | br | 13/texttype0 | top | 0.07000000000000006 | label_plus_shape | (0.565,1.66)-(0.635,1.8) |
| gen_col_mux | OUT | mux_out | 13/texttype0 | bottom | 0.15000000000000002 | label_plus_shape | (0.14,0)-(0.21,0.14) |
| gen_col_mux | OUTB | mux_out_b | 13/texttype0 | right | 0.13750000000000007 | label_plus_shape | (0.565,0)-(0.635,0.14) |
| gen_col_mux | SEL | column_select | 9/texttype0 | bottom | 0.1325 | label_plus_shape | (0.3275,0.025)-(0.3775,0.08) |
| gen_delay_inv | A | a | 11/texttype0 | left | 0.22000000000000003 | label_plus_shape | (0.0725,1.157)-(0.2075,1.222) |
| gen_delay_inv | Z | z | 11/texttype0 | right | 0.37000000000000005 | label_plus_shape | (0.3075,0.1025)-(0.3725,2.277) |
| gen_delay_inv | gnd | gnd | 11/texttype0 | bottom | 0.08 | label_plus_shape | (0,-0.0325)-(0.6875,0.0325) |
| gen_delay_inv | vdd | vdd | 11/texttype0 | top | 0.0349999999999997 | label_plus_shape | (0,2.438)-(0.6875,2.502) |
| gen_inv | A | a | 11/texttype0 | left | 0.22000000000000003 | label_plus_shape | (0.0725,0.605)-(0.2075,0.67) |
| gen_inv | Z | z | 11/texttype0 | right | 0.37000000000000005 | label_plus_shape | (0.3075,0.1025)-(0.3725,1.173) |
| gen_inv | gnd | gnd | 11/texttype0 | bottom | 0.08 | label_plus_shape | (0,-0.0325)-(0.6875,0.0325) |
| gen_inv | vdd | vdd | 11/texttype0 | top | 0.03500000000000014 | label_plus_shape | (0,1.333)-(0.6875,1.397) |
| gen_nand2 | vdd | vdd | 11/texttype0 | top | 0.03500000000000014 | label_plus_shape | (0,1.333)-(0.9025,1.397) |
| gen_nand2 | gnd | gnd | 11/texttype0 | bottom | 0.08 | label_plus_shape | (0,-0.0325)-(0.9025,0.0325) |
| gen_nand2 | A | a | 11/texttype0 | left | 0.3125 | label_plus_shape | (0.165,0.395)-(0.3,0.46) |
| gen_nand2 | B | b | 11/texttype0 | internal | 0.51 | label_plus_shape | (0.38,0.675)-(0.515,0.74) |
| gen_nand2 | Z | z | 11/texttype0 | right | 0.27249999999999996 | label_plus_shape | (0.34,0.9075)-(0.685,0.9725) |
| gen_nand4 | vdd | vdd | unknown | unknown | None | missing | - |
| gen_nand4 | gnd | gnd | unknown | unknown | None | missing | - |
| gen_nand4 | A | a | unknown | unknown | None | missing | - |
| gen_nand4 | B | b | unknown | unknown | None | missing | - |
| gen_nand4 | C | c | unknown | unknown | None | missing | - |
| gen_nand4 | D | d | unknown | unknown | None | missing | - |
| gen_nand4 | Z | z | unknown | unknown | None | missing | - |
| gen_precharge | vdd | vdd | 11/texttype0 | top | 0.15500000000000003 | label_plus_shape | (0.34,0.905)-(0.405,1.185) |
| gen_precharge | EN | precharge_enb | 11/texttype0 | bottom | 0.0675 | label_plus_shape | (0,-0.045)-(0.705,0.02) |
| gen_precharge | BL | bl | 13/texttype0 | left | 0.22000000000000003 | label_plus_shape | (0.105,0)-(0.175,1.34) |
| gen_precharge | BR | br | 13/texttype0 | right | 0.1399999999999999 | label_plus_shape | (0.53,0)-(0.6,1.34) |
| gen_wl_driver | vdd | vdd | 11/texttype0 | top | 0.03500000000000014 | label_plus_shape | (0,1.333)-(2.965,1.397) |
| gen_wl_driver | gnd | gnd | 11/texttype0 | bottom | 0.105 | label_plus_shape | (0,-0.0325)-(2.965,0.0325) |
| gen_wl_driver | A | decoder_input | 11/texttype0 | left | 0.3125 | label_plus_shape | (0.165,0.395)-(0.3,0.46) |
| gen_wl_driver | B | wordline_enable | 11/texttype0 | left | 0.5275 | label_plus_shape | (0.38,0.675)-(0.515,0.74) |
| gen_wl_driver | Z | wl | 11/texttype0 | bottom | 0.7275 | label_plus_shape | (1.823,0.59)-(1.887,0.655) |
| replica_cell_1rw | VDD | vdd | 11/texttype0 | top | 0.09999999999999853 | label_plus_shape | (-0.09,1.332)-(0.795,1.397) |
| replica_cell_1rw | VSS | gnd | 11/texttype0 | bottom | 0.09999999999999866 | label_plus_shape | (-0.09,-0.0325)-(0.795,0.0325) |
| replica_cell_1rw | RBL | rbl | 13/texttype0 | bottom | 0.10299999999999862 | label_plus_shape | (0.15,-0.08)-(0.22,1.465) |
| replica_cell_1rw | RBLB | rblb | 13/texttype0 | bottom | 0.10299999999999862 | label_plus_shape | (0.485,-0.08)-(0.555,1.465) |
| replica_cell_1rw | WL | wl | 11/texttype0 | left | 0.044999999999999395 | label_plus_shape | (-0.09,0.1275)-(0.795,0.1925) |
| sense_amp | VDD | vdd | 13/texttype0 | left | 0.3874999999999977 | label_plus_shape | (0.3175,3.735)-(0.3875,3.87) |
| sense_amp | VSS | gnd | 13/texttype0 | right | 0.08449999999999946 | label_plus_shape | (0.6275,0.1025)-(0.7025,0.1775) |
| sense_amp | EN | sense_enable | 11/texttype0 | top | 0.14999999999999858 | label_plus_shape | (0.23,5.827)-(0.295,5.892) |
| sense_amp | IN | bl | 13/texttype0 | bottom | 0.00499999999999997 | label_plus_shape | (0.15,0)-(0.22,6.01) |
| sense_amp | INB | br | 13/texttype0 | bottom | 0.006499999999999961 | label_plus_shape | (0.485,0)-(0.555,6.01) |
| sense_amp | Q | dout | 13/texttype0 | left | 0.06349999999999961 | label_plus_shape | (-0.0075,0.67)-(0.0675,0.745) |
| sense_amp | QB | dout_b | unknown | unknown | None | missing | - |
| tri_gate | in | din | 13/texttype0 | top | 0.16749999999999865 | label_plus_shape | (0.3175,2.735)-(0.3875,2.862) |
| tri_gate | out | dout | 13/texttype0 | bottom | 0.17749999999999894 | label_plus_shape | (0.3175,0)-(0.3875,0.35) |
| tri_gate | en | en | 11/texttype0 | left | 0.35249999999999787 | label_plus_shape | (0,0.3675)-(0.74,0.4325) |
| tri_gate | en_bar | enb | 11/texttype0 | left | 0.30749999999999816 | label_plus_shape | (0.2775,1.915)-(0.34,1.98) |
| tri_gate | vdd | vdd | 13/texttype0 | right | 0.3449999999999979 | label_plus_shape | (0.35,1.852)-(0.42,2.09) |
| tri_gate | gnd | gnd | 13/texttype0 | right | 0.23499999999999865 | label_plus_shape | (0.48,0.4975)-(0.55,0.6325) |
| write_driver | VDD | vdd | 13/texttype0 | left | 0.27249999999999835 | label_plus_shape | (0.105,0.395)-(0.24,0.465) |
| write_driver | VSS | gnd | 13/texttype0 | left | 0.09499999999999942 | label_plus_shape | (-0.035,1.162)-(0.035,3.797) |
| write_driver | EN | write_enable | 11/texttype0 | bottom | 0.29999999999999816 | label_plus_shape | (0.045,0.2675)-(0.635,0.3325) |
| write_driver | DIN | din | 13/texttype0 | bottom | 0.03499999999999979 | label_plus_shape | (0.28,0)-(0.35,0.14) |
| write_driver | BL | bl | 13/texttype0 | top | 0.03699999999999992 | label_plus_shape | (0.15,3.875)-(0.22,4.175) |
| write_driver | BLB | br | 13/texttype0 | top | 0.025000000000000355 | label_plus_shape | (0.485,1.735)-(0.555,4.175) |

## Semantic Conclusions

```json
{
  "SENSEAMP": {
    "IN_to_bl": true,
    "INB_to_br": true,
    "Q_to_dout": true,
    "QB_to_dout_b": false,
    "conclusion": "architecture_adapter_required",
    "recommendation": "Do not force-match QB/dout_b. Current local layoutgen uses single-ended dout sense_amp; adapt Q/QB to dout at architecture contract level."
  },
  "WORDLINEDRIVER": {
    "A_decoder_input_present": true,
    "B_wordline_enable_present": true,
    "Z_wl_present": true,
    "conclusion": "needs_semantic_confirmation",
    "recommendation": "Do not directly route OpenYield B as wordline_enable until gen_wl_driver polarity and physical B/equivalent pin are confirmed."
  },
  "COLUMNMUX": {
    "has_vdd_metadata": false,
    "has_gnd_metadata": true,
    "conclusion": "missing_power_metadata",
    "recommendation": "Do not allow shared rail for gen_col_mux until vdd metadata or a proven vdd shape is added."
  }
}
```

## Placement Aggregation Readiness

- can enter placement aggregation now: `False`

Blockers:

- `The internal parser extracted labels and nearby shape bboxes, but it does not prove electrical connectivity across hierarchy.`
- `SENSEAMP requires an architecture adapter because local sense_amp has no proven QB/dout_b physical output.`
- `WORDLINEDRIVER still needs semantic confirmation for B/wordline_enable before routing.`
- `COLUMNMUX is missing vdd metadata and must not be allowed to share rails.`
- `Power rail sharing must be validated with a full GDS pin-shape/connectivity audit before placement aggregation.`