# Lube Oil System Connectivity

## System Overview

**System Name:** Lube Oil System for Compressor K-01  
**Purpose:** Provide continuous lubrication and seal oil to compressor equipment with temperature control, filtration, and pressure relief capabilities  
**Design Philosophy:** Redundant pumping and filtration with comprehensive safety instrumentation

---

## Main Flow Path

### Primary Supply Route
```
TK-001 (Lube Oil Tank)
    ↓
P-01 / P-02 (Lube Oil Pumps - Parallel/Redundant)
    ↓
AIR COOLER (Heat Rejection)
    ↓
TCV-005 (Temperature Control Valve)
    ↓
E-001 / E-002 (Dual Oil Filters)
    ↓
K-01 (Compressor)
```

### Flow Description
1. **Oil Storage:** Lube oil stored in TK-001 with heating capability
2. **Suction:** Both pumps (P-01, P-02) draw from common tank header
3. **Pressurization:** Pumps increase pressure for system circulation
4. **Cooling:** Air cooler removes heat from oil
5. **Temperature Control:** TCV-005 regulates oil temperature before filtration
6. **Filtration:** Dual filters remove contaminants (one operating, one standby)
7. **Delivery:** Clean oil supplied to compressor bearings and seals

---

## Component Connections

### Tank System (TK-001)

**Connected To:**
- **P-01** via suction line
- **P-02** via suction line
- **HEATER (XL-001)** for tank heating
- **HEATER (XL-002)** for tank heating (redundant)
- **PCV-001** via recirculation return line
- **PZV-001** via pressure relief return
- **PZV-002** via pressure relief return
- **PCV-002** via bypass return
- **PSV-005** via safety valve relief

**Instrumentation:**
- **LG-001** - Local glass gauge for level indication
- **LS-004** - Level switch for alarm
- **L-004** - Local level indicator/alarm light
- **DIP STICK** - Manual level measurement
- **TG-001** - Temperature gauge
- **MANWAY** - Tank access for maintenance

---

### Pump System (P-01 and P-02)

**P-01 Connections:**
- **From:** TK-001 (suction)
- **To:** AIR COOLER (discharge)
- **Instruments:** PI-001 (pressure indicator), PG-001 (pressure gauge)
- **Safety:** PZV-001 (pressure relief valve), CV-001 (check valve)
- **Protection:** Suction strainer

**P-02 Connections:**
- **From:** TK-001 (suction)
- **To:** AIR COOLER (discharge)
- **Instruments:** PI-005 (pressure indicator), PG-005 (pressure gauge)
- **Safety:** PZV-002 (pressure relief valve), CV-002 (check valve)
- **Protection:** Suction strainer

**Redundancy:** One pump operating, one on standby for reliability

---

### Air Cooling System

**AIR COOLER Connections:**
- **From:** P-01 / P-02 (hot oil inlet)
- **To:** TCV-005 (cooled oil outlet)
- **Instrumentation:** TG-003 (temperature gauge at outlet)

**Function:** Removes heat from lube oil using ambient air

---

### Temperature Control System

**TCV-005 (Temperature Control Valve) Connections:**
- **From:** AIR COOLER
- **To:** E-001 / E-002 (filters)
- **Control:** TIC-005 (temperature indicator controller)
- **Reference:** TG-004 (temperature gauge)

**Control Loop:**
```
TG-004 (Temperature Measurement)
    ↓
TIC-005 (Controller)
    ↓
TCV-005 (Control Valve)
```

---

### Filtration System

**E-001 (Oil Filter 1) Connections:**
- **From:** TCV-005
- **To:** K-01 (compressor)
- **Recirculation:** PCV-001 (back to tank)
- **Instrumentation:** PDT-004, PDI-004, PD-004, PS-007

**E-002 (Oil Filter 2) Connections:**
- **From:** TCV-005
- **To:** K-01 (compressor)
- **Recirculation:** PCV-001 (back to tank)
- **Instrumentation:** PDT-004, PDI-004, PD-004, PS-007

**Filter Monitoring:**
- **PDT-004** - Differential pressure transmitter
- **PDI-004** - Differential pressure indicator
- **PDS-004** - Differential pressure switch (alarm)
- **PD-004** - Pressure drop indicator
- **PS-007** - Pressure switch (filter protection)

**Dual Filter Operation:** One filter online, one standby for maintenance without shutdown

---

### Recirculation Loop

**Path:**
```
E-001 / E-002
    ↓
PCV-001 (Pressure Control Valve)
    ↓
TK-001 (Tank)
```

**Purpose:** Maintains oil circulation when compressor demand is low or during startup

---

### Pressure Relief System

**Relief Paths:**
1. **PZV-001** → TK-001 (P-01 discharge relief)
2. **PZV-002** → TK-001 (P-02 discharge relief)
3. **PCV-002** → TK-001 (Bypass relief)
4. **PSV-005** → TK-001 (Safety valve relief)

**Function:** Protects system from over-pressurization

---

### Tank Heating System

**Heater 1 (XL-001):**
- **Connected to:** TK-001
- **Control:** TS-001 (temperature switch)
- **Manual:** HS-001 (heater switch)
- **Indication:** XL-001 (status light)

**Heater 2 (XL-002):**
- **Connected to:** TK-001
- **Control:** TS-002 (temperature switch)
- **Manual:** HS-002 (heater switch)
- **Indication:** XL-002 (status light)

**Purpose:** Maintains oil viscosity during cold conditions or startup

---

## Safety Systems

### Pressure Protection
- **PZV-001, PZV-002** - Pump discharge pressure relief
- **PCV-002** - Bypass pressure control
- **PSV-005** - Safety relief valve
- **PI-001, PI-005** - Pressure indication
- **PG-001, PG-005** - Local pressure gauges

### Temperature Protection
- **TS-001, TS-002** - Temperature switches for heater control
- **TIC-005** - Temperature controller for cooling control
- **TG-001, TG-003, TG-004** - Temperature gauges at key points

### Level Protection
- **LS-004** - Level switch (high/low alarm)
- **LG-001** - Local glass gauge
- **L-004** - Local indicator/alarm
- **DIP STICK** - Manual verification

### Filter Protection
- **PDT-004** - Differential pressure monitoring
- **PDS-004** - High differential pressure alarm
- **PS-007** - Filter pressure protection

---

## Redundancy Features

### Pump Redundancy
- **P-01 and P-02** in parallel configuration
- One operating, one standby
- Automatic or manual switchover capability

### Filter Redundancy
- **E-001 and E-002** dual arrangement
- Allows filter change without system shutdown
- Differential pressure monitoring indicates filter condition

### Heater Redundancy
- **XL-001 and XL-002** independent heating circuits
- Ensures temperature maintenance during heater failure

### Pressure Relief Redundancy
- Multiple relief paths (PZV-001, PZV-002, PCV-002, PSV-005)
- Ensures overpressure protection even if one device fails

---

## Key Connection Summary

| From Component | To Component | Connection Type | Purpose |
|----------------|--------------|-----------------|---------|
| TK-001 | P-01 | Pipe | Suction supply |
| TK-001 | P-02 | Pipe | Suction supply |
| P-01 | AIR COOLER | Pipe | Discharge to cooling |
| P-02 | AIR COOLER | Pipe | Discharge to cooling |
| AIR COOLER | TCV-005 | Pipe | Cooled oil to control |
| TCV-005 | E-001 | Pipe | To filter 1 |
| TCV-005 | E-002 | Pipe | To filter 2 |
| E-001 | K-01 | Pipe | Lubrication supply |
| E-002 | K-01 | Pipe | Lubrication supply (redundant) |
| E-001 | PCV-001 | Pipe | Recirculation |
| E-002 | PCV-001 | Pipe | Recirculation |
| PCV-001 | TK-001 | Pipe | Return to tank |
| PZV-001 | TK-001 | Pipe | Pressure relief |
| PZV-002 | TK-001 | Pipe | Pressure relief |
| PSV-005 | TK-001 | Pipe | Safety relief |

---

## Process Safety Considerations

### Hazard Identification
- **Fire Risk:** Oil leaks near hot surfaces (heaters, compressor)
- **Overpressure:** Pump deadhead or blockage scenarios
- **Cavitation:** Low oil level or high temperature causing viscosity loss
- **Contamination:** Filter failure allowing particles to reach compressor

### Protection Measures
- **Pressure Relief:** Multiple relief devices prevent overpressure
- **Temperature Control:** Heaters and coolers maintain optimal viscosity
- **Level Monitoring:** Alarms prevent pump cavitation from low level
- **Filtration:** Dual filters ensure oil cleanliness
- **Containment:** Tank design with manways for safe maintenance access

### Operational Safeguards
- **Redundant Pumps:** Continuous operation during pump failure
- **Bypass Capability:** Maintenance without shutdown
- **Local Indication:** Gauges allow operator verification
- **Alarm Systems:** Switches provide early warning of abnormal conditions
