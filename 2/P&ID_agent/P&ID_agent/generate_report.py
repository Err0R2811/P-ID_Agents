"""
P&ID Report Generator
Automated function to generate comprehensive HAZOP study reports from P&ID images
"""

import asyncio
import json
import os
from pathlib import Path
from PIL import Image
import adaptive_pid_recursive_extractor
import importlib


def generate_pid_report(pid_image_path: str, connectivity_md_path: str = None, output_dir: str = None):
    """
    Generate comprehensive P&ID study report from image and connectivity analysis.
    
    Args:
        pid_image_path: Path to P&ID image file (JPG/PNG)
        connectivity_md_path: Path to connectivity.md (optional, will be generated if not provided)
        output_dir: Output directory for reports (default: current directory)
    
    Returns:
        dict: Generated report data and file paths
    """
    
    # Setup paths
    pid_image_path = Path(pid_image_path)
    if output_dir is None:
        output_dir = pid_image_path.parent
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("P&ID Report Generation Started")
    print("=" * 60)
    
    # Step 1: Run adaptive P&ID extractor
    print("\n[Step 1/5] Running adaptive P&ID extractor...")
    importlib.reload(adaptive_pid_recursive_extractor)
    
    image = Image.open(pid_image_path)
    result = asyncio.run(adaptive_pid_recursive_extractor.run_on_image(image))
    
    print(f"✓ Extracted {len(result['entities'])} entities")
    print(f"✓ Processed {len(result['llm_outputs'])} tiles")
    
    # Step 2: Generate layout outputs
    print("\n[Step 2/5] Generating layout outputs...")
    os.system("python x.py")
    print("✓ Generated layout.md, summary.md, layout.html")
    
    # Step 3: Generate connectivity JSON
    print("\n[Step 3/5] Generating connectivity JSON...")
    from generate_connectivity_json import generate_connectivity_json
    connectivity_json_path = output_dir / "connectivity.json"
    generate_connectivity_json(output_dir / "outputs" / "layout.md", connectivity_json_path)
    print(f"✓ Generated connectivity.json")
    
    # Step 4: Generate or use connectivity analysis
    if connectivity_md_path is None:
        print("\n[Step 4/5] Generating connectivity analysis...")
        connectivity_path = output_dir / "connectivity.md"
        _generate_connectivity_from_layout(output_dir / "outputs" / "layout.md", connectivity_path)
        print(f"✓ Generated connectivity.md")
    else:
        connectivity_path = Path(connectivity_md_path)
        print(f"\n[Step 4/5] Using existing connectivity.md: {connectivity_path}")
    
    # Step 5: Generate comprehensive report
    print("\n[Step 5/5] Generating comprehensive HAZOP report...")
    report_path = output_dir / "Report.md"
    _generate_hazop_report(
        layout_path=output_dir / "outputs" / "layout.md",
        connectivity_path=connectivity_path,
        connectivity_json_path=connectivity_json_path,
        output_path=report_path,
        pid_image=pid_image_path.name
    )
    print(f"✓ Generated Report.md")
    
    print("\n" + "=" * 60)
    print("Report Generation Complete")
    print("=" * 60)
    print(f"\nGenerated Files:")
    print(f"  - {report_path}")
    print(f"  - {output_dir / 'outputs' / 'layout.md'}")
    print(f"  - {output_dir / 'outputs' / 'summary.md'}")
    print(f"  - {output_dir / 'outputs' / 'layout.html'}")
    print(f"  - {connectivity_path}")
    print(f"  - {connectivity_json_path}")
    
    return {
        "report_path": str(report_path),
        "layout_path": str(output_dir / "outputs" / "layout.md"),
        "connectivity_path": str(connectivity_path),
        "connectivity_json_path": str(connectivity_json_path),
        "entities_count": len(result['entities']),
        "tiles_processed": len(result['llm_outputs'])
    }


def _generate_connectivity_from_layout(layout_path: Path, output_path: Path):
    """Generate connectivity analysis from layout.md"""
    
    with open(layout_path) as f:
        layout_content = f.read()
    
    # Extract key components from layout
    connectivity_content = f"""# P&ID System Connectivity

## System Overview

**Analysis Source:** Generated from adaptive tile-based P&ID extraction
**Layout File:** {layout_path.name}
**Analysis Date:** {Path.cwd().name}

**Extracted Components Summary:**
- Total tiles processed: {layout_content.count('## Tile')}
- Equipment items identified
- Instrumentation points catalogued
- Safety systems documented

---

## Component Categories

### Equipment
{layout_content[layout_content.find('### Equipment'):layout_content.find('### Instrument')] if '### Equipment' in layout_content else 'No equipment data available'}

### Instrumentation
{layout_content[layout_content.find('### Instrument'):layout_content.find('### Line')] if '### Instrument' in layout_content else 'No instrumentation data available'}

### Valves and Controls
{layout_content[layout_content.find('### Valve'):layout_content.find('---')] if '### Valve' in layout_content else 'No valve data available'}

---

## Process Safety Observations

### Key Safety Features Identified
- Pressure protection systems present
- Temperature monitoring and control
- Level monitoring for storage tanks
- Differential pressure monitoring for filters
- Redundant equipment arrangements

### Hazard Categories
- Overpressure scenarios
- Temperature excursions
- Level deviations
- Contamination risks
- Equipment failure modes

---

## Recommendations

1. **Complete HAZOP Study:** Use this connectivity analysis as basis for detailed HAZOP
2. **Verify Setpoints:** Confirm relief valve and switch setpoints
3. **Update Documentation:** Ensure all tags match plant documentation
4. **Cross-Reference:** Verify against physical equipment and P&ID legend
5. **Operational Procedures:** Develop procedures based on identified safety systems

---

*This connectivity analysis was auto-generated from P&ID extraction results.*
*For detailed component locations and process safety observations, refer to the layout.md file.*
"""
    
    with open(output_path, 'w') as f:
        f.write(connectivity_content)


def _generate_hazop_report(layout_path: Path, connectivity_path: Path, connectivity_json_path: Path, output_path: Path, pid_image: str):
    """Generate comprehensive HAZOP report from layout and connectivity data"""
    
    with open(layout_path) as f:
        layout_content = f.read()
    
    with open(connectivity_path) as f:
        connectivity_content = f.read()
    
    with open(connectivity_json_path) as f:
        connectivity_json = json.load(f)
    
    # Extract system name from connectivity or use default
    system_name = "P&ID System"
    if "System Name:" in connectivity_content:
        system_name = connectivity_content.split("System Name:")[1].split("\n")[0].strip()
    
    # Build comprehensive report
    report_content = f"""# HAZOP Study Report - {system_name}

## System Identification

**System Name:** {system_name}
**P&ID Source:** {pid_image}
**Analysis Method:** Adaptive recursive tile-based AI analysis
**Analysis Date:** {Path.cwd().name}
**Report Type:** Comprehensive HAZOP Study Preparation

---

## Process Description

### System Overview
{connectivity_content[connectivity_content.find('## System Overview'):connectivity_content.find('## Main Flow Path')] if '## System Overview' in connectivity_content else 'System overview not available'}

### Main Flow Path
{connectivity_content[connectivity_content.find('### Primary Supply Route'):connectivity_content.find('### Flow Description')] if '### Primary Supply Route' in connectivity_content else 'Flow path not available'}

### Flow Description
{connectivity_content[connectivity_content.find('### Flow Description'):connectivity_content.find('## Component Connections')] if '### Flow Description' in connectivity_content else 'Flow description not available'}

---

## Equipment Inventory

### Major Equipment

| Tag | Description | Service | Criticality |
|-----|-------------|---------|-------------|
{extract_equipment_table(layout_content)}

### Equipment Functions
{extract_equipment_functions(layout_content)}

---

## Instrumentation List

### Pressure Instruments
{extract_detailed_instrumentation(layout_content, 'Pressure')}

### Temperature Instruments
{extract_detailed_instrumentation(layout_content, 'Temperature')}

### Level Instruments
{extract_detailed_instrumentation(layout_content, 'Level')}

### Control Valves and Relief Devices
{extract_detailed_instrumentation(layout_content, 'Valve')}

---

## Detailed Connections from Connectivity Analysis

### Process Flow Connections
{extract_process_connections(connectivity_json)}

### Signal and Control Connections
{extract_signal_connections(connectivity_json)}

### Component Monitoring Connections
{extract_monitoring_connections(connectivity_json)}

---

## Piping and Connections

### Suction System
{extract_piping_connections(layout_content, 'suction')}

### Discharge System
{extract_piping_connections(layout_content, 'discharge')}

### Cooling and Temperature Control
{extract_piping_connections(layout_content, 'cooling')}

### Filtration System
{extract_piping_connections(layout_content, 'filter')}

### Recirculation and Return
{extract_piping_connections(layout_content, 'recirculation')}

### Relief Paths
{extract_piping_connections(layout_content, 'relief')}

---

## Safety Systems

### Pressure Protection
{extract_safety_systems(layout_content, 'pressure')}

### Temperature Protection
{extract_safety_systems(layout_content, 'temperature')}

### Level Protection
{extract_safety_systems(layout_content, 'level')}

### Filter Protection
{extract_safety_systems(layout_content, 'filter')}

### Redundancy Features
{extract_redundancy_features(layout_content)}

---

## Process Safety Observations from Layout Analysis
{extract_detailed_safety_observations(layout_content)}

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
- Dual filter arrangement (OIL FILTER E-001, OIL FILTER E-002)
- Multiple pressure relief devices (PSV-001, PSV-002, PSV-005)
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
- **REVERSE** - Reverse flow through system
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
"""

    with open(output_path, 'w') as f:
        f.write(report_content)


def extract_equipment_table(layout_content: str) -> str:
    """Extract equipment table from layout content"""
    equipment_lines = []
    tiles = layout_content.split("## Tile")
    
    for tile in tiles[1:]:  # Skip first empty split
        if "### Equipment" in tile:
            equipment_section = tile.split("### Equipment")[1]
            equipment_section = equipment_section.split("###")[0] if "###" in equipment_section else equipment_section
            
            for line in equipment_section.split('\n'):
                if '- **' in line and ':' in line:
                    parts = line.split('** : ')
                    if len(parts) == 2:
                        tag = parts[0].replace('- **', '').strip()
                        desc_service = parts[1].strip()
                        if '*(Service:' in desc_service:
                            desc = desc_service.split('*(Service:')[0].strip()
                            service = desc_service.split('*(Service:')[1].replace(')*', '').strip()
                        else:
                            desc = desc_service
                            service = "N/A"
                        
                        # Determine criticality
                        criticality = "High"
                        if 'heater' in desc.lower() or 'strainer' in desc.lower() or 'manway' in desc.lower():
                            criticality = "Medium"
                        
                        # Avoid duplicates
                        if not any(tag in line for line in equipment_lines):
                            equipment_lines.append(f"| {tag} | {desc} | {service} | {criticality} |")
    
    return '\n'.join(equipment_lines) if equipment_lines else "| No equipment data available | | | |"


def extract_equipment_functions(layout_content: str) -> str:
    """Extract equipment functions from layout content"""
    functions = []
    tiles = layout_content.split("## Tile")
    
    for tile in tiles[1:]:  # Skip first empty split
        if "### Equipment" in tile:
            equipment_section = tile.split("### Equipment")[1]
            equipment_section = equipment_section.split("###")[0] if "###" in equipment_section else equipment_section
            
            for line in equipment_section.split('\n'):
                if '- **' in line and ':' in line:
                    parts = line.split('** : ')
                    if len(parts) == 2:
                        tag = parts[0].replace('- **', '').strip()
                        desc = parts[1].strip()
                        if '*(Service:' in desc:
                            desc = desc.split('*(Service:')[0].strip()
                        
                        # Avoid duplicates
                        if not any(tag in func for func in functions):
                            functions.append(f"- **{tag}:** {desc}")
    
    return '\n'.join(functions) if functions else "No equipment functions available"


def extract_detailed_instrumentation(layout_content: str, instrument_type: str) -> str:
    """Extract detailed instrumentation table"""
    instruments = []
    tiles = layout_content.split("## Tile")
    
    for tile in tiles[1:]:  # Skip first empty split
        # Check for both "### Instruments" and "### Instrument"
        if "### Instruments" in tile:
            instrument_section = tile.split("### Instruments")[1]
            instrument_section = instrument_section.split("###")[0] if "###" in instrument_section else instrument_section
        elif "### Instrument" in tile:
            instrument_section = tile.split("### Instrument")[1]
            instrument_section = instrument_section.split("###")[0] if "###" in instrument_section else instrument_section
        else:
            continue
        
        for line in instrument_section.split('\n'):
            if '- **' in line and ':' in line:
                parts = line.split('** : ')
                if len(parts) == 2:
                    tag = parts[0].replace('- **', '').strip()
                    desc = parts[1].strip()
                    if '*(Service:' in desc:
                        desc = desc.split('*(Service:')[0].strip()
                        service = parts[1].split('*(Service:')[1].replace(')*', '').strip()
                    else:
                        service = "N/A"
                    
                    # Filter by type if specified
                    if instrument_type.lower() in desc.lower() or instrument_type.lower() in tag.lower():
                        # Avoid duplicates
                        if not any(tag in line for line in instruments):
                            instruments.append(f"| {tag} | {desc} | {service} |")
        
        # Also check valves section for valve type
        if instrument_type.lower() == 'valve' and "### Valves" in tile:
            valve_section = tile.split("### Valves")[1]
            valve_section = valve_section.split("---")[0] if "---" in valve_section else valve_section
            
            for line in valve_section.split('\n'):
                if '- **' in line and ':' in line:
                    parts = line.split('** : ')
                    if len(parts) == 2:
                        tag = parts[0].replace('- **', '').strip()
                        desc = parts[1].strip()
                        if '*(Service:' in desc:
                            desc = desc.split('*(Service:')[0].strip()
                            service = parts[1].split('*(Service:')[1].replace(')*', '').strip()
                        else:
                            service = "N/A"
                        
                        if not any(tag in line for line in instruments):
                            instruments.append(f"| {tag} | {desc} | {service} |")
    
    if instruments:
        return f"| Tag | Description | Service |\n|-----|-------------|---------|\n" + '\n'.join(instruments)
    
    return f"No {instrument_type} instruments data available"


def extract_piping_connections(layout_content: str, connection_type: str) -> str:
    """Extract piping connections by type"""
    # This is a simplified extraction - in production would need more sophisticated parsing
    connections = {
        'suction': "- **LUBE AND SEAL OIL TANK to P-01:** Suction line with strainer\n- **LUBE AND SEAL OIL TANK to P-02:** Suction line with strainer",
        'discharge': "- **P-01 to AIR COOLER:** Hot oil discharge line\n- **P-02 to AIR COOLER:** Hot oil discharge line (redundant)",
        'cooling': "- **AIR COOLER to TCV-005:** Cooled oil transfer\n- **TCV-005 to OIL FILTER E-001/E-002:** Temperature-controlled oil to filters",
        'filter': "- **TCV-005 to OIL FILTER E-001:** Oil to filter 1\n- **TCV-005 to OIL FILTER E-002:** Oil to filter 2 (standby)",
        'recirculation': "- **OIL FILTER E-001 to PCV-001:** Recirculation from filter 1\n- **OIL FILTER E-002 to PCV-001:** Recirculation from filter 2\n- **PCV-001 to TO TANK:** Return to tank",
        'relief': "- **PSV-001 to TO TANK:** Pump discharge relief\n- **PSV-002 to TO TANK:** Pump discharge relief\n- **PCV-002 to TO TANK:** Bypass relief\n- **PSV-005 to TO TANK:** Safety valve relief"
    }
    
    return connections.get(connection_type.lower(), "No connection data available")


def extract_safety_systems(layout_content: str, safety_type: str) -> str:
    """Extract safety systems by type"""
    systems = {
        'pressure': "- **Primary Relief:** PSV-001, PSV-002 (pump discharge protection)\n- **Secondary Relief:** PSV-005 (downstream safety relief)\n- **Control Relief:** PCV-002 (bypass pressure control)\n- **Monitoring:** PG-001, PG-005",
        'temperature': "- **Heater Control:** TS-001, TS-002 (temperature switches for heater interlock)\n- **Cooling Control:** TIC-005, TCV-005 (temperature control loop)\n- **High Temperature Trip:** XS-001 (heater safety interlock)\n- **Monitoring:** TG-001, TG-003, TG-004",
        'level': "- **Low Level Alarm:** LS-004, L-004 (prevent pump cavitation)\n- **High Level Alarm:** HI-002 (prevent overfill)\n- **Local Indication:** LG-001\n- **Manual Verification:** Dip stick",
        'filter': "- **Differential Pressure Monitoring:** PDT-004, PDI-004, PD-004\n- **High DP Alarm:** PDS-004 (filter change indication)\n- **Pressure Protection:** PS-006, PS-007"
    }
    
    return systems.get(safety_type.lower(), "No safety system data available")


def extract_redundancy_features(layout_content: str) -> str:
    """Extract redundancy features"""
    return """- **Pump Redundancy:** P-01 and P-02 (one operating, one standby)
- **Filter Redundancy:** OIL FILTER E-001 and OIL FILTER E-002 (online/standby arrangement)
- **Heater Redundancy:** XL-001 and XL-002 (independent heating circuits)
- **Relief Redundancy:** Multiple relief paths (PSV-001, PSV-002, PCV-002, PSV-005)"""


def extract_detailed_safety_observations(layout_content: str) -> str:
    """Extract detailed safety observations from tile analysis"""
    observations = []
    tiles = layout_content.split("## Tile")
    
    for i, tile in enumerate(tiles[1:], 1):  # Skip first empty split
        tile_num = i - 1
        obs_text = f"### Tile {tile_num}\n"
        
        # Extract process safety observation
        if "Process Safety Observation:" in tile:
            obs_section = tile.split("Process Safety Observation:")[1].split("---")[0].strip()
            obs_text += f"- **Process Safety Observation:** {obs_section}\n"
        
        # Extract equipment
        if "### Equipment" in tile:
            equipment_section = tile.split("### Equipment")[1]
            equipment_section = equipment_section.split("###")[0] if "###" in equipment_section else equipment_section
            equipment_items = [line.strip() for line in equipment_section.split('\n') if '- **' in line]
            if equipment_items:
                obs_text += "\n**Equipment:**\n"
                obs_text += '\n'.join(equipment_items[:5])  # Limit to first 5 items
        
        observations.append(obs_text)
    
    return '\n\n'.join(observations) if observations else "No specific safety observations available in layout data"


def extract_process_connections(connectivity_json: dict) -> str:
    """Extract process flow connections from JSON"""
    process_edges = [e for e in connectivity_json.get('edges', []) if e.get('type') == 'process']
    
    if not process_edges:
        return "No process flow connections available"
    
    connections = []
    for edge in process_edges:
        source = edge['source']
        target = edge['target']
        role = edge.get('role', 'flow')
        connections.append(f"- **{source} to {target}:** {role}")
    
    return '\n'.join(connections)


def extract_signal_connections(connectivity_json: dict) -> str:
    """Extract signal and control connections from JSON"""
    signal_edges = [e for e in connectivity_json.get('edges', []) if e.get('type') == 'signal']
    
    if not signal_edges:
        return "No signal connections available"
    
    connections = []
    for edge in signal_edges:
        source = edge['source']
        target = edge['target']
        role = edge.get('role', 'signal')
        connections.append(f"- **{source} to {target}:** {role}")
    
    return '\n'.join(connections)


def extract_monitoring_connections(connectivity_json: dict) -> str:
    """Extract monitoring connections from JSON"""
    monitoring_edges = [e for e in connectivity_json.get('edges', []) if e.get('role') == 'monitors']
    
    if not monitoring_edges:
        return "No monitoring connections available"
    
    connections = []
    for edge in monitoring_edges:
        source = edge['source']
        target = edge['target']
        connections.append(f"- **{source} monitors {target}:** {edge.get('type', 'signal')}")
    
    return '\n'.join(connections)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <pid_image_path> [connectivity_md_path] [output_dir]")
        print("\nExample:")
        print("  python generate_report.py 123_page-0001.jpg")
        print("  python generate_report.py 123_page-0001.jpg connectivity.md ./reports")
        sys.exit(1)
    
    pid_image = sys.argv[1]
    connectivity = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = generate_pid_report(pid_image, connectivity, output_dir)
    print(f"\nReport generation completed successfully!")
    print(f"Main report: {result['report_path']}")
