"""Exploratory LCLayout adapter stub for this project's current FreePDK45.

This file is generated for provenance and integration planning. It is not a
formal technology adapter until every UNKNOWN_RULE entry in
LCLAYOUT_FREEPDK45_RULE_PROVENANCE.csv is resolved from current project
FreePDK45 sources and LCLayout is installed in the isolated experiment env.
"""

PDK_NAME = "current_project_freepdk45"
PDK_CHANGED = False
EXTERNAL_STDCELL_LIBRARY_ALLOWED = False
LAYER_MAP_SOURCE = "technology/freepdk45/layers.map"
DRC_DECK_SOURCE = "technology/freepdk45/tech/freepdk45.lydrc"
MANUFACTURING_GRID_SOURCE = "current project FreePDK45 grid evidence"

STATUS = {
    "lclayout_installed": False,
    "formal_candidate_allowed": False,
    "reason": "LCLayout adapter remains exploratory until tool install and UNKNOWN_RULE closure."
}
