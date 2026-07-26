# M12C3 Generator Architecture Comparison

- architecture_option=A_LAYOUTGEN_EXISTING_DEVICE_GATE_GENERATOR, recommended_scope=REFERENCE_ONLY, risk=High risk of proxy geometry misuse
- architecture_option=B_OPENRAM_FREEPDK45_DEVICE_CONTACT_ADAPTER, recommended_scope=TRUSTED_REUSE_CANDIDATE, risk=Best option if adapter controls cache and source trace
- architecture_option=C_NEW_KLAYOUT_PRIMITIVE_GENERATOR, recommended_scope=FALLBACK_ONLY, risk=Highest implementation risk
