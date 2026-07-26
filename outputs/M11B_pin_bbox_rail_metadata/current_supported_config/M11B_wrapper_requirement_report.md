# M11B Wrapper Requirement Report

- `sense_amp` requires_wrapper=`False` reason=`No wrapper required; machine-verified pins align directly with the golden sense_amp leaf.`
- `wordline_driver` requires_wrapper=`True` reason=`A wrapper remains required because D/G/S metadata pins are not machine-resolved in the parsed candidate geometry.`
