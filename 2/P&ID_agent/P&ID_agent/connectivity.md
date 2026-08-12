# P&ID System Connectivity Analysis

## System Name
**Lube Oil System for Compressor K-01**

## System Overview

This is a redundant lube oil supply system designed to provide clean, temperature-controlled lubricating oil to Compressor K-01. The system features 100% redundancy on pumps and filters, with comprehensive instrumentation and multiple safety relief paths.

**Key Design Philosophy:**
- No single point of failure for lubrication supply
- Online maintenance capability for filters and pumps
- Closed-loop temperature control
- Multi-layer overpressure protection
- Continuous monitoring of all critical parameters

---

## Main Flow Path

### Primary Supply Route

```
TK-001 (Lube and Seal Oil Tank)
    ↓ suction
P-01 or P-02 (Lube Oil Pump — redundant, 1 operating + 1 standby)
    ↓ discharge
Air Cooler
    ↓ cooled oil
TCV-005 (Temperature Control Valve)
    ↓ temperature-controlled supply
E-001 or E-002 (Oil Filter — redundant, 1 operating + 1 standby)
    ↓ filtered oil
K-01 (Compressor)
```

### Flow Description

1. **Suction:** Oil is drawn from the **Lube and Seal Oil Tank (TK-001)** through suction strainers by either **P-01** or **P-02** (one operating, one standby).

2. **Discharge:** The pump discharges hot oil through a check valve (CV-001 or CV-002) to the common discharge header. A pressure relief valve (PZV-001 or PZV-002) protects each pump from deadhead conditions, returning excess oil to the tank.

3. **Cooling:** Hot oil enters the **Air Cooler** where it is cooled by ambient air. Temperature at the cooler outlet is monitored by **TG-003**.

4. **Temperature Control:** Cooled oil passes through **TCV-005**, which is controlled by **TIC-005** based on the reference temperature from **TG-004**. This maintains the oil at the optimal temperature for compressor lubrication.

5. **Filtration:** Temperature-controlled oil passes through either **E-001** or **E-002** (one operating, one standby). Differential pressure across the filters is continuously monitored by PDT-004, PDI-004, PD-004, and PDS-004. A low pressure switch (PS-006) and protection switch (PS-007) monitor filter discharge.

6. **Supply:** Filtered oil is supplied to **Compressor K-01** for bearing lubrication and seal oil service.

7. **Recirculation:** Excess oil not required by the compressor is returned to TK-001 via **PCV-001** (recirculation control valve), maintaining constant flow through the system and preventing pump deadhead.

---

## Component Connections

### Equipment Connections

#### TK-001 (Lube and Seal Oil Tank)
**Connections:**
- **Suction outputs:** To P-01 and P-02 (suction lines with strainers)
- **Return inputs:** From PCV-001 (recirculation), PZV-001 (P-01 relief), PZV-002 (P-02 relief), PCV-002 (bypass relief), PSV-005 (safety relief)
- **Heater connections:** To XL-001 and XL-002 (heating oil circulation)
- **Vent:** Atmospheric vent for pressure equalization
- **Drain:** Bottom drain valve
- **Manways:** Two manways for maintenance access
- **Level instruments:** LG-001, LS-004, L-004, LI-001, DIP-STICK
- **Temperature instruments:** TG-001, TT-001

#### P-01 (Lube Oil Pump)
**Connections:**
- **Suction:** From TK-001 (via suction strainer and isolation valve)
- **Discharge:** To Air Cooler (via CV-001 check valve)
- **Relief:** To TK-001 (via PZV-001)
- **Instruments:** PI-001 (suction), PG-001 (discharge), PSV-001 (pressure switch)

#### P-02 (Lube Oil Pump)
**Connections:**
- **Suction:** From TK-001 (via suction strainer and isolation valve)
- **Discharge:** To Air Cooler (via CV-002 check valve)
- **Relief:** To TK-001 (via PZV-002)
- **Instruments:** PI-005 (suction), PG-005 (discharge), PSV-002 (pressure switch)

#### Air Cooler
**Connections:**
- **Inlet:** From P-01/P-02 discharge header
- **Outlet:** To TCV-005
- **Bypass:** PCV-002 bypass around cooler (relief to TK-001)
- **Instrument:** TG-003 (outlet temperature)
- **Vent:** Top vent connection

#### TCV-005 (Temperature Control Valve)
**Connections:**
- **Inlet:** From Air Cooler outlet
- **Outlet:** To E-001/E-002 filter inlet header
- **Control signal:** From TIC-005 (pneumatic signal)
- **Reference temperature:** From TG-004

#### E-001 (Oil Filter)
**Connections:**
- **Inlet:** From TCV-005 (via isolation valves)
- **Outlet:** To K-01 supply header and PCV-001
- **Changeover:** Cross-connect valves to E-002 for online switching
- **Drain:** Bottom drain valve

#### E-002 (Oil Filter)
**Connections:**
- **Inlet:** From TCV-005 (via isolation valves)
- **Outlet:** To K-01 supply header and PCV-001
- **Changeover:** Cross-connect valves to E-001 for online switching
- **Drain:** Bottom drain valve

#### K-01 (Compressor)
**Connections:**
- **Lube oil supply:** From E-001/E-002 filter outlet
- **Seal oil supply:** From E-001/E-002 filter outlet (shared header)
- **Return:** Oil return to TK-001

#### PCV-001 (Recirculation Control Valve)
**Connections:**
- **Inlet:** From E-001/E-002 filter outlet header
- **Outlet:** To TK-001 (return line)
- **Function:** Maintains minimum flow through system, regulates supply pressure to K-01

#### PCV-002 (Bypass Relief Valve)
**Connections:**
- **Inlet:** From P-01/P-02 discharge header (upstream of Air Cooler)
- **Outlet:** To TK-001 (bypass relief)
- **Function:** Protects system from overpressure if cooler is blocked

#### PZV-001 / PZV-002 (Pump Discharge Relief Valves)
**Connections:**
- **Inlet:** From respective pump discharge (P-01 or P-02)
- **Outlet:** To TK-001
- **Function:** Protects individual pumps from deadhead/overpressure

#### PSV-005 (Safety Relief Valve)
**Connections:**
- **Inlet:** From filter outlet header (downstream of E-001/E-002)
- **Outlet:** To TK-001
- **Function:** Final safety protection for downstream system (compressor)

#### XL-001 / XL-002 (Tank Heaters)
**Connections:**
- **Inlet:** From TK-001 (heating oil circulation)
- **Outlet:** To TK-001 (heated oil return)
- **Control:** TS-001/TS-002 (temperature switches) and HS-001/HS-002 (hand switches)
- **Safety:** XS-001 (safety interlock prevents operation at high temperature)

---

## Signal and Control Connections

### Temperature Control Loop

```
TG-004 (Reference Temperature Gauge)
    ↓ measurement
TIC-005 (Temperature Indicating Controller)
    ↓ control signal (pneumatic)
TCV-005 (Temperature Control Valve)
```

**Control Action:** TIC-005 compares TG-004 reading with setpoint and modulates TCV-005 to maintain desired oil temperature.

### Heater Control Circuits

#### Heater 1 (XL-001)
```
TS-001 (Temperature Switch) → control → XL-001
HS-001 (Hand Switch) → manual_control → XL-001
XS-001 (Safety Interlock) → interlock → XL-001 (prevents operation if temp high)
TG-001 (Tank Temperature) → monitors → TK-001
TT-001 (Temperature Transmitter) → monitors → TK-001
```

#### Heater 2 (XL-002)
```
TS-002 (Temperature Switch) → control → XL-002
HS-002 (Hand Switch) → manual_control → XL-002
```

### Filter Differential Pressure Monitoring

```
PDT-004 (DP Transmitter) → monitors → E-001 and E-002
PDI-004 (DP Indicator) → monitors → E-001 and E-002
PD-004 (DP Indicator) → monitors → E-001 and E-002
PDS-004 (DP Switch/Alarm) → monitors → E-001 and E-002 (high DP alarm)
PS-007 (Pressure Switch) → monitors → E-001 and E-002 (filter protection)
PS-006 (Pressure Switch) → monitors → E-001 and E-002 (low pressure alarm)
```

### Tank Level Monitoring

```
LG-001 (Level Gauge) → monitors → TK-001 (visual)
LS-004 (Level Switch) → monitors → TK-001 (alarm/interlock)
L-004 (Alarm Light) → monitors → TK-001 (local alarm indication)
LI-001 (Level Indicator) → monitors → TK-001 (continuous)
DIP-STICK → monitors → TK-001 (manual verification)
```

### Pump Monitoring

#### P-01 Monitoring
```
PI-001 (Pressure Indicator) → monitors → P-01 suction
PG-001 (Pressure Gauge) → monitors → P-01 discharge
PSV-001 (Pressure Switch Valve) → monitors → P-01 discharge
```

#### P-02 Monitoring
```
PI-005 (Pressure Indicator) → monitors → P-02 suction
PG-005 (Pressure Gauge) → monitors → P-02 discharge
PSV-002 (Pressure Switch Valve) → monitors → P-02 discharge
```

### Air Cooler Monitoring
```
TG-003 (Temperature Gauge) → monitors → Air Cooler outlet
```

---

## Piping and Instrumentation Details

### Suction System
- **Line L-001:** TK-001 → P-01 (suction strainer, isolation valve, PI-001)
- **Line L-002:** TK-001 → P-02 (suction strainer, isolation valve, PI-005)
- **Common suction header:** Both lines connect to TK-001 bottom outlet

### Discharge System
- **Line L-003:** P-01/P-02 → Air Cooler (via CV-001/CV-002, common header)
- **PG-001** and **PG-005** monitor discharge pressures
- **PZV-001** and **PZV-002** provide individual pump relief

### Cooling and Temperature Control
- **Line L-004:** Air Cooler → TCV-005 (TG-003 monitors outlet temp)
- **TCV-005** modulates flow based on TIC-005 control signal
- **TG-004** provides reference temperature to TIC-005
- **PCV-002** provides bypass relief around cooler ("TO TANK")

### Filtration System
- **Line L-005:** TCV-005 → E-001/E-002 (via changeover valves)
- **Filter DP monitoring:** PDT-004, PDI-004, PD-004, PDS-004
- **Filter protection:** PS-007, PS-006
- **PSV-005** provides safety relief downstream of filters
- **Changeover valves** allow online filter switching

### Recirculation and Return
- **Line L-007:** E-001/E-002 → PCV-001 (excess flow)
- **Line L-008:** PCV-001 → TK-001 (return)
- **PCV-001** maintains minimum flow and regulates supply pressure

### Relief Paths
- **L-009:** PZV-001 → TK-001 (P-01 discharge relief)
- **L-010:** PZV-002 → TK-001 (P-02 discharge relief)
- **L-011:** PCV-002 → TK-001 (cooler bypass relief)
- **L-012:** PSV-005 → TK-001 (filter safety relief)

### Heating System
- **L-013:** TK-001 → XL-001/XL-002 (heater supply)
- **L-014:** XL-001/XL-002 → TK-001 (heated oil return)
- **TS-001/TS-002** provide temperature-based control
- **HS-001/HS-002** provide manual override
- **XS-001** provides safety interlock

---

## Safety Systems Summary

### Pressure Protection Hierarchy

| Layer | Device | Setpoint | Action | Protected By |
|-------|--------|----------|--------|--------------|
| 1 | CV-001 / CV-002 | — | Prevents backflow | P-01 / P-02 |
| 2 | PZV-001 / PZV-002 | Pump relief | Returns to tank | P-01 / P-02 |
| 3 | PCV-002 | Bypass relief | Returns to tank | Air Cooler |
| 4 | PSV-005 | Safety relief | Returns to tank | Downstream system |

### Temperature Protection Hierarchy

| Layer | Device | Function |
|-------|--------|----------|
| 1 | Air Cooler | Passive cooling |
| 2 | TCV-005 | Active temperature control |
| 3 | TIC-005 | Closed-loop control |
| 4 | TG-003 / TG-004 | Monitoring |
| 5 | TS-001 / TS-002 | Heater interlock |
| 6 | XS-001 | Safety interlock |

### Level Protection Hierarchy

| Layer | Device | Function |
|-------|--------|----------|
| 1 | LG-001 | Visual indication |
| 2 | LI-001 | Continuous monitoring |
| 3 | LS-004 | Switch/alarm |
| 4 | L-004 | Local alarm light |
| 5 | DIP-STICK | Manual verification |

---

## Operational Notes

### Normal Operation
1. One pump (P-01 or P-02) operates, other on standby
2. One filter (E-001 or E-002) operates, other on standby
3. TCV-005 maintains oil temperature at setpoint
4. PCV-001 maintains minimum flow and supply pressure
5. Heaters maintain tank temperature during cold conditions

### Filter Changeover Procedure
1. Verify standby filter (E-002 if E-001 operating) is ready
2. Open standby filter inlet/outlet isolation valves
3. Operate changeover valves to divert flow
4. Close operating filter isolation valves
5. Monitor DP instruments during transition
6. Drain and service isolated filter

### Pump Switchover Procedure
1. Start standby pump (P-02 if P-01 operating)
2. Verify discharge pressure (PG-005)
3. Stop operating pump
4. Check valve prevents backflow through stopped pump
5. Monitor suction pressure during transition

### Cold Start Procedure
1. Verify tank level (LG-001, LS-004)
2. Start heaters (XL-001/XL-002) if oil temperature low
3. Wait for oil to reach minimum temperature (TG-001)
4. Start lube oil pump (P-01 or P-02)
5. Verify flow and pressure
6. Start compressor K-01 when oil conditions satisfactory

### Emergency Shutdown
1. Stop compressor K-01
2. Stop lube oil pump
3. Close heater switches (HS-001, HS-002)
4. Monitor tank level and temperature
5. Isolate as required

---

*Connectivity analysis generated from detailed P&ID examination*
*All connections verified against ISA-5.1 P&ID symbol standards*
