# OpenYield Generator Component Plan

## P0

- goal: Unblock R3 structure-complete prototype architecture and generator-owned floorplanning
- components: `OpenYieldIntentLoader; CanonicalSramParameterModel; PhysicalModuleRegistry; BitcellArrayPhysicalGenerator; RowPeripheryPhysicalGenerator; ColumnPeripheryPhysicalGenerator; SRAMTopologyFloorplanner`

## P1

- goal: Complete traceability, backend binding, and structure-stage validation
- components: `ControlPeripheryPhysicalGenerator; InstanceMapper; GDSBackend; ValidationHookManager`

## P2

- goal: Add R4 routing, power, and pin proof layers
- components: `WordlineRouter; BitlineRouter; ControlRouter; PowerPlanner; PinLabelExporter; NetToShapeMapper`
