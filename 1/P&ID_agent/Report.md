# HAZOP Study Report - Lube Oil System for Compressor K-01

## System Identification

**System Name:** Lube Oil System for Compressor K-01  
**Process Function:** Provide continuous lubrication and seal oil to compressor equipment with temperature control, filtration, and pressure relief capabilities  
**Design Philosophy:** Redundant pumping and filtration with comprehensive safety instrumentation  
**System Boundary:** From Lube Oil Tank (TK-001) through pumps, cooling, filtration to Compressor K-01 bearings and seals

---

## Process Description

### Main Process Flow
```
TK-001 (Lube Oil Tank)
    ↓ (Suction to parallel pumps)
P-01 / P-02 (Lube Oil Pumps - Redundant)
    ↓ (Discharge to cooling)
AIR COOLER (Heat Rejection)
    ↓ (Temperature controlled flow)
TCV-005 (Temperature Control Valve)
    ↓ (To dual filters)
E-001 / E-002 (Dual Oil Filters - One operating, one standby)
    ↓ (Clean oil supply)
K-01 (Compressor - Bearings and Seals)
```

### Supporting Flows
**Recirculation Loop:** E-001/E-002 → PCV-001 → TK-001 (maintains circulation during low demand/startup)  
**Pressure Relief Paths:** PZV-001/PZV-002/PCV-002/PSV-005 → TK-001 (overpressure protection)  
**Tank Heating:** XL-001/XL-002 heaters maintain oil viscosity

---

## Equipment Inventory

### Major Equipment

| Tag | Description | Service | Criticality |
|-----|-------------|---------|-------------|
| TK-001 | Lube and Seal Oil Tank | Oil Storage | High - Primary reservoir |
| P-01 | Lube Oil Pump | Lube Oil Circulation | High - Primary pump |
| P-02 | Lube Oil Pump | Lube Oil Circulation | High - Standby pump |
| AIR COOLER | Air Cooled Heat Exchanger | Lube Oil Cooling | High - Temperature control |
| E-001 | Oil Filter 1 | Lube Oil Filtration | High - Contamination control |
| E-002 | Oil Filter 2 | Lube Oil Filtration | High - Standby filter |
| K-01 | Compressor | Process Equipment | High - End user of lube oil |
| HEATER-01 | Tank Heater Element | Tank Heating | Medium - Viscosity control |
| STRAINER | Suction Strainer | Pump Protection | Medium - Particulate removal |

### Equipment Functions
- **TK-001:** Stores lube oil, provides suction header to pumps, receives return flows
- **P-01/P-02:** Pressurize oil for system circulation (one operating, one standby)
- **AIR COOLER:** Removes heat from oil using ambient air
- **E-001/E-002:** Remove contaminants from oil (dual arrangement for maintenance without shutdown)
- **K-01:** Receives clean, temperature-controlled lubrication oil

---

## Instrumentation List

### Pressure Instruments

| Tag | Type | Service | Location | Function |
|-----|------|---------|----------|----------|
| PI-001 | Pressure Indicator | Lube Oil | P-01 Discharge | Local pressure monitoring |
| PI-005 | Pressure Indicator | Lube Oil | P-02 Discharge | Local pressure monitoring |
| PG-001 | Pressure Gauge | Lube Oil | Header/Main Line | Visual pressure verification |
| PG-005 | Pressure Gauge | Lube Oil | P-02 Discharge | Local pressure monitoring |
| PDT-004 | Differential Pressure Transmitter | Filter | E-001/E-002 | Filter condition monitoring |
| PDI-004 | Differential Pressure Indicator | Filter | E-001/E-002 | Local filter differential pressure |
| PD-004 | Pressure Drop Indicator | Filter | E-001/E-002 | Filter pressure drop indication |
| PDS-004 | Differential Pressure Switch | Filter | E-001/E-002 | High differential pressure alarm |
| PS-007 | Pressure Switch | Filter | E-001/E-002 | Filter pressure protection |
| PZV-001 | Pressure Switch/Valve | Lube Oil | P-01 Discharge | Pressure relief/control |
| PZV-002 | Pressure Switch/Valve | Lube Oil | P-02 Discharge | Pressure relief/control |

### Temperature Instruments

| Tag | Type | Service | Location | Function |
|-----|------|---------|----------|----------|
| TG-001 | Temperature Gauge | Lube Oil | Tank/Suction | Local temperature indication |
| TG-003 | Temperature Gauge | Lube Oil | Air Cooler Outlet | Cooling performance monitoring |
| TG-004 | Temperature Gauge | Lube Oil | Post-TCV-005 | Temperature control reference |
| TS-001 | Temperature Switch | Lube Oil | Tank/Heater Control | Heater control interlock |
| TS-002 | Temperature Switch | Lube Oil | Tank/Heater Control | Heater control interlock |
| TIC-005 | Temperature Indicator Controller | Lube Oil | TCV-005 Control | Temperature control loop |
| TC-001 | Temperature Controller | Heating | Heater Control | Temperature control |
| TT-001 | Temperature Transmitter | Heating | Heater Control | Temperature measurement |
| XS-001 | High Temperature Switch | Heating | Heater | Safety interlock |

### Level Instruments

| Tag | Type | Service | Location | Function |
|-----|------|---------|----------|----------|
| LG-001 | Local Glass Gauge | Lube Oil | TK-001 | Visual level indication |
| LS-004 | Level Switch | Lube Oil | TK-001 | High/low level alarm |
| L-004 | Local Level Indicator | Lube Oil | TK-001 | Local level indication/alarm |
| LSH-002 | High Level Switch | Oil System | TK-001 | High level alarm |
| K-004 | Low Level Switch | Oil System | TK-001 | Low level alarm |
| DIP STICK | Manual Level Measurement | Lube Oil | TK-001 | Manual level verification |

### Control and Status Instruments

| Tag | Type | Service | Function |
|-----|------|---------|----------|
| XL-001 | Heater Status Light/Switch | Electric | Heater 1 status indication |
| XL-002 | Heater Status Light/Switch | Electric | Heater 2 status indication |
| HS-001 | Heater Switch | Electric | Heater 1 manual control |
| HS-002 | Heater Switch | Electric | Heater 2 manual control |
| XV-001 | Shut-off Valve/Isolator | Heating | Heater isolation |

---

## Control Valves and Relief Devices

### Control Valves

| Tag | Type | Service | Location | Function |
|-----|------|---------|----------|----------|
| TCV-005 | Temperature Control Valve | Lube Oil | Post-Air Cooler | Regulates oil temperature |
| PCV-001 | Pressure Control Valve | Recirculation | Filter Discharge | Recirculation flow control |
| PCV-002 | Pressure Control Valve | Bypass | System Bypass | Bypass pressure control |

### Relief and Safety Valves

| Tag | Type | Service | Location | Setpoint (if known) | Function |
|-----|------|---------|----------|-------------------|----------|
| PZV-001 | Pressure Relief Valve | Lube Oil | P-01 Discharge | Unknown | Pump discharge overpressure protection |
| PZV-002 | Pressure Relief Valve | Lube Oil | P-02 Discharge | Unknown | Pump discharge overpressure protection |
| PSV-005 | Pressure Safety Valve | Discharge | Filter Loop | Unknown | Safety relief for downstream piping |
| CV-001 | Check Valve | Lube Oil | P-01 Discharge | N/A | Backflow prevention |
| CV-002 | Check Valve | Lube Oil | P-02 Discharge | N/A | Backflow prevention |

---

## Piping and Connections

### Suction System
- **TK-001 to P-01:** Suction line with strainer
- **TK-001 to P-02:** Suction line with strainer
- **Common suction header** from tank to both pumps

### Discharge System
- **P-01 to AIR COOLER:** Hot oil discharge line
- **P-02 to AIR COOLER:** Hot oil discharge line (redundant)
- **Check valves** on each pump discharge to prevent backflow

### Cooling and Temperature Control
- **AIR COOLER to TCV-005:** Cooled oil transfer
- **TCV-005 to E-001/E-002:** Temperature-controlled oil to filters

### Filtration System
- **TCV-005 to E-001:** Oil to filter 1
- **TCV-005 to E-002:** Oil to filter 2 (standby)
- **E-001 to K-01:** Clean oil to compressor
- **E-002 to K-01:** Clean oil to compressor (redundant path)

### Recirculation and Return
- **E-001 to PCV-001:** Recirculation from filter 1
- **E-002 to PCV-001:** Recirculation from filter 2
- **PCV-001 to TK-001:** Return to tank

### Relief Paths
- **PZV-001 to TK-001:** P-01 discharge relief
- **PZV-002 to TK-001:** P-02 discharge relief
- **PCV-002 to TK-001:** Bypass relief
- **PSV-005 to TK-001:** Safety valve relief

---

## Process Parameters

### Operating Conditions (Inferred)
- **Fluid:** Lube Oil (mineral or synthetic)
- **Pressure Range:** Low to medium pressure (typical for lube oil systems)
- **Temperature Range:** Controlled via heaters and coolers to maintain optimal viscosity
- **Flow:** Continuous circulation to compressor bearings and seals

### Key Parameters to Monitor
- **Pressure:** Pump discharge, filter differential, system header
- **Temperature:** Tank temperature, oil temperature pre/post cooling, heater temperature
- **Level:** Tank level (critical for pump suction)
- **Differential Pressure:** Filter condition (indicates fouling)

---

## Safety Systems

### Pressure Protection
- **Primary Relief:** PZV-001, PZV-002 (pump discharge protection)
- **Secondary Relief:** PSV-005 (downstream safety relief)
- **Control Relief:** PCV-002 (bypass pressure control)
- **Monitoring:** PI-001, PI-005, PG-001, PG-005

### Temperature Protection
- **Heater Control:** TS-001, TS-002 (temperature switches for heater interlock)
- **Cooling Control:** TIC-005, TCV-005 (temperature control loop)
- **High Temperature Trip:** XS-001 (heater safety interlock)
- **Monitoring:** TG-001, TG-003, TG-004

### Level Protection
- **Low Level Alarm:** LS-004, K-004 (prevent pump cavitation)
- **High Level Alarm:** LSH-002 (prevent overfill)
- **Local Indication:** LG-001, L-004
- **Manual Verification:** Dip stick

### Filter Protection
- **Differential Pressure Monitoring:** PDT-004, PDI-004, PD-004
- **High DP Alarm:** PDS-004 (filter change indication)
- **Pressure Protection:** PS-007

### Redundancy Features
- **Pump Redundancy:** P-01 and P-02 (one operating, one standby)
- **Filter Redundancy:** E-001 and E-002 (online/standby arrangement)
- **Heater Redundancy:** XL-001 and XL-002 (independent heating circuits)
- **Relief Redundancy:** Multiple relief paths (PZV-001, PZV-002, PCV-002, PSV-005)

---

## Process Safety Observations from Layout Analysis

### Tile 2 (Main Lube Oil System)
- **Key Safety Features:** Pressure switches (PZV-001, PZV-002) on pump discharge headers for low/high pressure protection
- **Thermal Management:** Heater (XL-001) with temperature switch (TS-001) for viscosity control
- **Pressure Relief:** PCV-002 and PCV-001 protect pump discharges and downstream sections
- **Level Monitoring:** Multiple level indicators (LG-001, LS-004, L-004) for tank level safety
- **Hazards Identified:** Oil leak fire risks, over-pressurization of lube oil circuit

### Tile 3 (Filtration and Recirculation)
- **Dual Filter Arrangement:** E-001/E-002 with differential pressure monitoring (PDT-004) for filtration integrity
- **Safety Instrumentation:** High-level switch (LSH-002) and low-level alarm (L-004) on tank
- **Pressure Relief:** PSV-005 on discharge line of filtration/recirculation loop
- **Thermal Control:** Tank heater (XL-002) with temperature switch (TS-002)
- **Maintenance Access:** Manways require strict isolation and depressurization procedures

### Tile 6 (Pump P-01 Detail)
- **Pressure Relief:** Two relief valves (PZV-001, PZV-002) on pump discharge headers
- **Thermal Control:** Heater system with TS-001, TG-001, HS-001, XL-001 for viscosity maintenance
- **Instrumentation Strategy:** Separate instruments for monitoring (TG) and safety interlock (TS)
- **Process Flow:** Clear separation between suction and discharge sides

### Tile 7 (Pump P-02 Detail)
- **Pressure Switch:** LS-004 connected to pump discharge for high pressure alarm
- **Level Monitoring:** LS-004, LG-001, L-004 for tank level safety
- **Relief Protection:** PZV-002 on discharge line, PCV-001 on overhead line
- **Observation:** Lack of explicit relief protection on immediate pump discharge loop noted

### Tile 9 (Pump Station Detail)
- **Suction Protection:** Strainer upstream of pump for particulate contamination protection
- **Discharge Protection:** Pressure transmitters (PZV-001, PZV-002) and check valves
- **Temperature/Level Indicators:** TG-001, TS-001 on suction/tank
- **Standard Installation:** Pump with necessary protections (strainer, check valve, heating, monitoring)

---

## Hazard Identification Summary

### Process Hazards
1. **Fire Hazard:** Oil leaks near hot surfaces (heaters, compressor)
2. **Overpressure:** Pump deadhead or blockage scenarios in discharge lines
3. **Cavitation:** Low oil level or high temperature causing viscosity loss
4. **Contamination:** Filter failure allowing particles to reach compressor bearings
5. **Thermal Runaway:** Heater malfunction causing excessive oil temperature
6. **Loss of Lubrication:** Pump failure, loss of level, or blockage causing compressor damage

### Equipment Hazards
1. **Pump Failure:** Loss of lubrication to compressor
2. **Filter Blockage:** High differential pressure, reduced flow
3. **Heater Failure:** Inability to maintain oil viscosity in cold conditions
4. **Cooler Failure:** Overheating of oil, reduced viscosity
5. **Tank Overflow:** High level causing environmental issues
6. **Tank Underflow:** Low level causing pump cavitation

### Operational Hazards
1. **Maintenance Hazards:** Entry into tank via manways requires isolation
2. **Switching Hazards:** Pump/filter switching during operation
3. **Start-up Hazards:** Cold oil viscosity, improper priming
4. **Shutdown Hazards:** Thermal contraction, oil drainage issues

---

## Existing Safeguards

### Engineering Safeguards
- Redundant pumps (P-01, P-02)
- Dual filter arrangement (E-001, E-002)
- Multiple pressure relief devices (PZV-001, PZV-002, PSV-005)
- Check valves on pump discharges
- Suction strainers
- Temperature control systems (heaters and cooler)

### Instrumentation Safeguards
- Pressure switches and transmitters
- Temperature switches and controllers
- Level switches and indicators
- Differential pressure monitoring for filters
- Local gauges for operator verification

### Procedural Safeguards
- Manual level verification (dip stick)
- Local indication for operator monitoring
- Alarm systems for abnormal conditions
- Maintenance access via manways with isolation procedures

---

## Recommendations for HAZOP Study

### Guide Words to Apply
- **NO** - No flow, no pressure, no level, no temperature
- **MORE** - More pressure, more temperature, more flow, more level
- **LESS** - Less pressure, less temperature, less flow, less level
- **REVERSE** - Reverse flow through check valves
- **AS WELL AS** - Contamination, water ingress
- **OTHER THAN** - Wrong fluid, wrong viscosity

### Key Nodes for HAZOP Analysis
1. **Tank Suction** - Level, temperature, contamination
2. **Pump Suction** - NPSH, strainer blockage, viscosity
3. **Pump Discharge** - Overpressure, deadhead, check valve failure
4. **Air Cooler** - Cooling failure, fouling, ambient conditions
5. **Temperature Control** - TCV-005 failure, sensor error
6. **Filters** - Blockage, bypass, differential pressure
7. **Compressor Supply** - Flow interruption, contamination, temperature
8. **Recirculation** - PCV-001 failure, flow control
9. **Relief System** - Relief valve failure, setpoint drift
10. **Heater System** - Thermal runaway, heater failure

### Parameters to Analyze
- **Flow** - Flow rate to compressor, recirculation flow
- **Pressure** - Suction pressure, discharge pressure, differential pressure
- **Temperature** - Tank temperature, oil temperature, heater temperature
- **Level** - Tank level (critical for pump NPSH)
- **Composition** - Oil quality, contamination, water content

---

## Additional Information Needed for Complete HAZOP
- Design pressure and temperature ratings for all equipment
- Relief valve setpoints
- Normal operating ranges for all parameters
- Compressor lubrication requirements (flow rate, pressure, temperature)
- Oil specifications (viscosity grade, flash point)
- Electrical classification for hazardous areas
- Material of construction for piping and equipment
- P&ID legend for symbol interpretation
- Operating procedures (start-up, normal operation, shutdown, emergency)
- Maintenance procedures
- Previous incident history
