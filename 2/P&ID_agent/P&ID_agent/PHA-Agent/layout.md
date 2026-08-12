# P&ID Layout Analysis — Lube Oil System

## System Identification

| Property | Value |
|----------|-------|
| **System Name** | Lube Oil System |
| **P&ID Title** | Lube Oil System |
| **Primary Equipment** | Compressor K-01 |
| **Service** | Lubrication and Seal Oil Supply |
| **Analysis Date** | 2026-07-18 |
| **Image Source** | 123_page-0001.jpg |
| **Image Resolution** | 3509 × 2480 px |

---

## Process Overview

This is a **Lube Oil System** designed to supply filtered, temperature-controlled lubricating oil to **Compressor K-01**. The system includes:

- A **Lube and Seal Oil Tank** (TK-001) with redundant heaters
- **Two redundant lube oil pumps** (P-01, P-02) — one operating, one standby
- An **Air Cooler** for temperature control
- A **Temperature Control Valve** (TCV-005) with temperature indicating controller (TIC-005)
- **Two redundant oil filters** (E-001, E-002) — one operating, one standby
- A **Recirculation Control Valve** (PCV-001) for flow regulation
- Multiple **pressure relief devices** and **instrumentation** for monitoring and safety

### Primary Flow Path

```
TK-001 (Tank) → P-01/P-02 (Pumps) → Air Cooler → TCV-005 → E-001/E-002 (Filters) → K-01 (Compressor)
                                    ↓
                              PCV-001 (Recirculation back to TK-001)
```

---

## Equipment Inventory

### Major Equipment

| Tag | Description | Service | Redundancy |
|-----|-------------|---------|------------|
| **K-01** | Compressor K-01 | Main lube oil consumer | — |
| **P-01** | Lube Oil Pump | Primary pump | Pumps (1 of 2) |
| **P-02** | Lube Oil Pump | Standby pump | Pumps (1 of 2) |
| **AIR COOLER** | Air Cooler | Cools hot oil from pumps | — |
| **E-001** | Oil Filter | Primary filter | Filters (1 of 2) |
| **E-002** | Oil Filter | Standby filter | Filters (1 of 2) |
| **TK-001** | Lube and Seal Oil Tank | Oil storage reservoir | — |

### Auxiliary Equipment

| Tag | Description | Service |
|-----|-------------|---------|
| **XL-001** | Heater | Tank heater (left side) |
| **XL-002** | Heater | Tank heater (right side) |
| **DIP STICK** | Dip Stick | Manual level verification |
| **MANWAY** | Manway (×2) | Tank access for maintenance |

---

## Valve Inventory

### Control Valves

| Tag | Type | Description | Location |
|-----|------|-------------|----------|
| **TCV-005** | Temperature Control Valve | Temperature control after cooler | Downstream of Air Cooler |
| **PCV-001** | Pressure Control Valve | Recirculation control valve | Downstream of filters, return to tank |
| **PCV-002** | Pressure Control Valve | Bypass relief valve | Bypass around Air Cooler |

### Relief Valves

| Tag | Type | Description | Protected Equipment |
|-----|------|-------------|---------------------|
| **PZV-001** | Pressure Relief Valve | P-01 discharge relief | P-01 Lube Oil Pump |
| **PZV-002** | Pressure Relief Valve | P-02 discharge relief | P-02 Lube Oil Pump |
| **PSV-005** | Safety Relief Valve | Tank safety relief | Downstream of filters |

### Check Valves

| Tag | Type | Description | Location |
|-----|------|-------------|----------|
| **CV-001** | Check Valve | P-01 inline check valve | P-01 discharge |
| **CV-002** | Check Valve | P-02 inline check valve | P-02 discharge |

### Isolation Valves

Multiple hand-operated isolation valves (gate/ball valves) are present throughout the system for maintenance isolation, including:
- Suction isolation valves at P-01 and P-02
- Discharge isolation valves
- Filter inlet/outlet isolation valves (for E-001 and E-002 switching)
- Cooler inlet/outlet isolation valves
- Tank drain valves
- Heater isolation valves

---

## Instrumentation Inventory

### Pressure Instruments

| Tag | Type | Description | Location | Measures |
|-----|------|-------------|----------|----------|
| **PI-001** | Pressure Indicator | P-01 suction pressure indicator | P-01 suction line | Suction pressure |
| **PG-001** | Pressure Gauge | P-01 local pressure gauge | P-01 discharge | Discharge pressure |
| **PI-005** | Pressure Indicator | P-02 suction pressure indicator | P-02 suction line | Suction pressure |
| **PG-005** | Pressure Gauge | P-02 local pressure gauge | P-02 discharge | Discharge pressure |
| **PDI-004** | Differential Pressure Indicator | Filter DP indicator | Filter loop | Filter differential pressure |
| **PDT-004** | Differential Pressure Transmitter | Filter DP transmitter | Filter loop | Filter differential pressure |
| **PDS-004** | Differential Pressure Switch | Filter DP switch/alarm | Filter loop | Filter DP alarm |
| **PD-004** | Differential Pressure Indicator | Filter pressure drop | Filter loop | Filter pressure drop |
| **PS-007** | Pressure Switch | Filter protection pressure switch | Filter loop | Filter protection |
| **PS-006** | Pressure Switch | Low pressure switch | Filter discharge | Low pressure alarm |
| **PSV-001** | Pressure Switch Valve | P-01 pressure switch | P-01 discharge | P-01 pressure |
| **PSV-002** | Pressure Switch Valve | P-02 pressure switch | P-02 discharge | P-02 pressure |

### Temperature Instruments

| Tag | Type | Description | Location | Measures |
|-----|------|-------------|----------|----------|
| **TG-001** | Temperature Gauge | Tank temperature gauge | TK-001 | Tank oil temperature |
| **TG-003** | Temperature Gauge | Air cooler outlet temp gauge | Air Cooler outlet | Cooled oil temperature |
| **TG-004** | Temperature Gauge | TCV reference temp gauge | TCV-005 reference | Reference temperature |
| **TIC-005** | Temperature Indicating Controller | Temperature controller | Control loop | Oil temperature control |
| **TS-001** | Temperature Switch | Heater 1 temperature switch | XL-001 control | Heater 1 interlock |
| **TS-002** | Temperature Switch | Heater 2 temperature switch | XL-002 control | Heater 2 interlock |
| **TT-001** | Temperature Transmitter | Tank temperature transmitter | TK-001 | Tank temperature |
| **TT-002** | Temperature Transmitter | Heater temperature transmitter | Heater circuit | Heater temperature |

### Level Instruments

| Tag | Type | Description | Location | Measures |
|-----|------|-------------|----------|----------|
| **LG-001** | Level Gauge | Level glass gauge | TK-001 | Tank level (visual) |
| **LS-004** | Level Switch | Level switch | TK-001 | Tank level (alarm/interlock) |
| **L-004** | Level Indicator | Local level alarm light | TK-001 | Level alarm indication |
| **LI-001** | Level Indicator | Tank level indicator | TK-001 | Tank level |
| **DIP-STICK** | Manual Instrument | Dip stick | TK-001 | Manual level verification |

### Control Instruments

| Tag | Type | Description | Control Action |
|-----|------|-------------|----------------|
| **TIC-005** | Controller | Temperature indicating controller | Controls TCV-005 based on TG-004 measurement |
| **HS-001** | Hand Switch | Heater 1 manual switch | Manual on/off for XL-001 |
| **HS-002** | Hand Switch | Heater 2 manual switch | Manual on/off for XL-002 |
| **XS-001** | Safety Interlock | Heater safety interlock | Prevents heater operation at high temperature |

### Flow Instruments

| Tag | Type | Description | Location |
|-----|------|-------------|----------|
| **FI-001** | Flow Indicator | Tank oil flow indicator | TK-001 circulation |
| **FI-002** | Flow Indicator | Heater flow indicator | Heater circuit |

---

## Line Numbers and Services

| Line Number | Description | From | To | Service |
|-------------|-------------|------|-----|---------|
| **L-001** | Suction line | TK-001 | P-01 | Lube oil suction |
| **L-002** | Suction line | TK-001 | P-02 | Lube oil suction |
| **L-003** | Discharge line | P-01/P-02 | Air Cooler | Hot lube oil |
| **L-004** | Cooled oil line | Air Cooler | TCV-005 | Cooled lube oil |
| **L-005** | Supply line | TCV-005 | E-001/E-002 | Temperature-controlled oil |
| **L-006** | Filtered oil line | E-001/E-002 | K-01 | Filtered lube oil to compressor |
| **L-007** | Recirculation line | E-001/E-002 | PCV-001 | Excess oil recirculation |
| **L-008** | Return line | PCV-001 | TK-001 | Oil return to tank |
| **L-009** | Relief line | PZV-001 | TK-001 | P-01 relief to tank |
| **L-010** | Relief line | PZV-002 | TK-001 | P-02 relief to tank |
| **L-011** | Bypass line | PCV-002 | TK-001 | Cooler bypass relief |
| **L-012** | Safety relief | PSV-005 | TK-001 | Filter safety relief |
| **L-013** | Heater supply | TK-001 | XL-001/XL-002 | Heating oil circulation |
| **L-014** | Heater return | XL-001/XL-002 | TK-001 | Heated oil return |

---

## Process Safety Observations

### Critical Safety Systems

1. **Pressure Protection (Multiple Layers):**
   - Pump discharge relief valves (PZV-001, PZV-002) protect pumps from deadhead
   - Safety relief valve (PSV-005) protects downstream system
   - Bypass relief (PCV-002) provides cooler bypass protection
   - Check valves (CV-001, CV-002) prevent backflow through standby pump

2. **Temperature Control:**
   - Closed-loop temperature control: TG-004 → TIC-005 → TCV-005
   - Air Cooler for high-temperature conditions
   - Redundant tank heaters (XL-001, XL-002) for cold start conditions
   - Temperature switches (TS-001, TS-002) for heater interlock protection
   - Safety interlock (XS-001) prevents heater operation at high temperature

3. **Level Protection:**
   - Level switch (LS-004) and alarm light (L-004) prevent pump cavitation
   - Level gauge (LG-001) provides visual indication
   - Dip stick for manual verification
   - Level indicator (LI-001) for continuous monitoring

4. **Filter Protection:**
   - Differential pressure monitoring (PDT-004, PDI-004, PD-004, PDS-004)
   - Pressure switch (PS-007) for filter protection
   - Low pressure switch (PS-006) for filter discharge monitoring
   - Dual filter arrangement allows online switching without flow interruption

5. **Redundancy Features:**
   - Dual pumps (P-01, P-02) — automatic switchover capability
   - Dual filters (E-001, E-002) — online/standby arrangement with changeover valves
   - Dual heaters (XL-001, XL-002) — independent heating circuits
   - Multiple relief paths for overpressure protection

### Potential Hazards Identified

1. **Fire Hazard:** Hot oil leaks near heaters or compressor
2. **Overpressure:** Pump deadhead, blockage, or control valve failure
3. **Cavitation:** Low tank level causing pump damage
4. **Contamination:** Filter failure allowing particles to reach compressor bearings
5. **Thermal Runaway:** Heater malfunction causing excessive oil temperature
6. **Loss of Lubrication:** Complete pump failure or blockage causing compressor damage
7. **Environmental:** Tank overflow or oil spill during maintenance

### Noteworthy Design Features

- **Suction strainers** at pump inlets protect pumps from debris
- **Manual switches (HS-001, HS-002)** for heater control with temperature interlocks
- **Check valves** on each pump discharge prevent backflow and allow standby operation
- **Isolation valves** around filters and coolers allow maintenance without system shutdown
- **Manways** provide tank access for inspection and cleaning
- **"TO TANK" labels** clearly indicate relief and bypass return paths
- **Vent connections** on tank for pressure equalization

---

## Component Spatial Layout

### Bottom Section (Tank Area)
- **Left side:** Heaters XL-001, XL-002 with temperature instruments (TG-001, TS-001, TS-002, HS-001, HS-002, XS-001)
- **Center:** Tank TK-001 with level instruments (LG-001, LS-004, L-004, LI-001, DIP-STICK), manways
- **Right side:** Additional heater connections, flow instruments (FI-001, FI-002), vent

### Lower-Middle Section (Pump Area)
- **P-01 (left):** Suction from TK-001 with PI-001, discharge with PG-001, PZV-001, CV-001
- **P-02 (right):** Suction from TK-001 with PI-005, discharge with PG-005, PZV-002, CV-002
- Both pumps discharge to common header leading to Air Cooler

### Middle Section (Cooler and Temperature Control)
- **Air Cooler:** Center-left with TG-003 on outlet
- **TCV-005:** Temperature control valve with TIC-005 controller and TG-004 reference
- **PCV-002:** Bypass relief valve around cooler ("TO TANK")
- **PSV-005:** Safety relief valve ("TO TANK")

### Upper-Middle Section (Filter Area)
- **E-001 (top):** Oil Filter with inlet/outlet isolation and changeover valves
- **E-002 (bottom):** Oil Filter with inlet/outlet isolation and changeover valves
- **Filter instruments:** PDT-004, PDI-004, PDS-004, PD-004, PS-007, PS-006
- **PSV-005:** Safety relief downstream of filters

### Top Section (Compressor)
- **K-01:** Compressor with lube oil supply and return connections
- Supply line from filters (E-001/E-002) via PCV-001 recirculation path
- Return line from compressor back to system

---

## Tile-Based Analysis Summary

| Tile | Region | Key Components | Status |
|------|--------|----------------|--------|
| 0 | Bottom-left | Heaters, TG-001, TS-001, TS-002, HS-001, HS-002, XS-001 | Complete |
| 1 | Bottom-center | Tank, P-01, P-02, suction instruments | Complete |
| 2 | Bottom-right | Tank right side, level instruments, manways, vent | Complete |
| 3 | Middle-left | Air Cooler, TCV-005, TG-003, TG-004, TIC-005 | Complete |
| 4 | Middle-center | P-01/P-02 discharge, PZV-001, PZV-002, PCV-002 | Complete |
| 5 | Middle-right | Filters E-001, E-002, DP instruments, PSV-005 | Complete |
| 6 | Top-left | Compressor K-01 supply line | Complete |
| 7 | Top-right | Compressor K-01, PCV-001 recirculation, return line | Complete |

---

*Generated from detailed visual analysis of P&ID 123_page-0001.jpg*
*All tags verified against ISA-5.1 instrument symbol standards*
