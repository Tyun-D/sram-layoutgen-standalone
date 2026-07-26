# Wave3 DFF_BUF Hierarchical Net Namespace

- top_level_nets: `['TOP::VDD', 'TOP::VSS', 'TOP::D', 'TOP::CLK', 'TOP::Q', 'TOP::QB']`
- parent_internal_nets: `['PARENT::qint']`
- dff_nets: `['dff::VDD', 'dff::VSS', 'dff::D', 'dff::Q', 'dff::CLK', 'dff::CLKB_internal', 'dff::D_b_internal', 'dff::z1_internal', 'dff::z2_internal', 'dff::z3_internal', 'dff::z4_internal', 'dff::z5_internal', 'dff::QB_internal']`
- inv1_nets: `['inv1::A', 'inv1::Z', 'inv1::VDD', 'inv1::VSS']`
- inv2_nets: `['inv2::A', 'inv2::Z', 'inv2::VDD', 'inv2::VSS']`
- notes: `['TOP::QB is distinct from dff::QB_internal.', 'PARENT::qint may connect only to dff::Q and inv1::A.', 'TOP::CLK may connect only to dff::CLK.']`
