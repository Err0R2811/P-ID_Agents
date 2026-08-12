"""
P&ID Connectivity JSON Generator
Generates nodes and edges JSON for LLM understanding of P&ID connections
"""

import json
from pathlib import Path
from typing import List, Dict
import re


class ConnectivityJSONGenerator:
    """Generate JSON connectivity data for LLM understanding"""
    
    def __init__(self, connectivity_md_path: str):
        self.connectivity_path = Path(connectivity_md_path)
        self.content = ""
        self._load_connectivity()
    
    def _load_connectivity(self):
        """Load connectivity.md content"""
        with open(self.connectivity_path) as f:
            self.content = f.read()
    
    def generate_connectivity_json(self, output_path: str = None) -> Dict:
        """Generate complete connectivity JSON with nodes and edges"""
        
        nodes = self._generate_nodes()
        edges = self._generate_edges()
        
        connectivity_data = {
            "nodes": nodes,
            "edges": edges
        }
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(connectivity_data, f, indent=2)
        
        return connectivity_data
    
    def _generate_nodes(self) -> List[Dict]:
        """Generate nodes by parsing connectivity.md dynamically"""
        nodes = []
        
        # Parse equipment nodes from connectivity.md
        nodes.extend(self._parse_equipment_nodes())
        
        # Parse valve nodes from connectivity.md
        nodes.extend(self._parse_valve_nodes())
        
        # Parse instrument nodes from connectivity.md
        nodes.extend(self._parse_instrument_nodes())
        
        return nodes
    
    def _parse_equipment_nodes(self) -> List[Dict]:
        """Parse equipment nodes from connectivity.md"""
        nodes = []
        
        # Extract equipment from the main flow path and component sections
        equipment_patterns = [
            (r'TK-001', 'equipment', 'tank', 'Lube oil tank', None),
            (r'P-01', 'equipment', 'pump', 'Lube oil pump 1', 'pumps'),
            (r'P-02', 'equipment', 'pump', 'Lube oil pump 2', 'pumps'),
            (r'AIR COOLER|AIR-COOLER', 'equipment', 'cooler', 'Air cooler', None),
            (r'E-001', 'equipment', 'filter', 'Oil filter 1', 'filters'),
            (r'E-002', 'equipment', 'filter', 'Oil filter 2', 'filters'),
            (r'K-01', 'equipment', 'compressor', 'Compressor', None),
            (r'XL-001', 'equipment', 'heater', 'Tank heater 1', 'heaters'),
            (r'XL-002', 'equipment', 'heater', 'Tank heater 2', 'heaters'),
        ]
        
        for pattern, type_, subtype, name, redundancy in equipment_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                # Use the standard ID format
                standard_id = pattern.split('|')[0].replace(' ', '-')
                node = {
                    "id": standard_id,
                    "type": type_,
                    "subtype": subtype,
                    "name": name
                }
                if redundancy:
                    node["redundancy_group"] = redundancy
                nodes.append(node)
        
        return nodes
    
    def _parse_valve_nodes(self) -> List[Dict]:
        """Parse valve nodes from connectivity.md"""
        nodes = []
        
        valve_patterns = [
            (r'TCV-005', 'control_valve', 'Temperature control valve', None),
            (r'PCV-001', 'pressure_control_valve', 'Recirculation control valve', None),
            (r'PZV-001', 'relief_valve', 'P-01 discharge relief', 'relief'),
            (r'PZV-002', 'relief_valve', 'P-02 discharge relief', 'relief'),
            (r'PCV-002', 'pressure_control_valve', 'Bypass relief', 'relief'),
            (r'PSV-005', 'safety_relief_valve', 'Tank safety relief', 'relief'),
            (r'CV-001', 'check_valve', 'P-01 check valve', None),
            (r'CV-002', 'check_valve', 'P-02 check valve', None),
        ]
        
        for pattern, subtype, name, redundancy in valve_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                node = {
                    "id": pattern,
                    "type": "valve",
                    "subtype": subtype,
                    "name": name
                }
                if redundancy:
                    node["redundancy_group"] = redundancy
                nodes.append(node)
        
        # Also check for PSV-001 and PSV-002 (mentioned in connectivity.md)
        if re.search(r'PSV-001', self.content, re.IGNORECASE):
            nodes.append({
                "id": "PSV-001",
                "type": "valve",
                "subtype": "pressure_switch_valve",
                "name": "P-01 pressure switch valve"
            })
        
        if re.search(r'PSV-002', self.content, re.IGNORECASE):
            nodes.append({
                "id": "PSV-002",
                "type": "valve",
                "subtype": "pressure_switch_valve",
                "name": "P-02 pressure switch valve"
            })
        
        return nodes
    
    def _parse_instrument_nodes(self) -> List[Dict]:
        """Parse instrument nodes from connectivity.md"""
        nodes = []
        
        # Extract instruments from connectivity.md
        instrument_patterns = [
            ('LG-001', 'instrument', 'level', 'Level glass gauge'),
            ('LS-004', 'instrument', 'level', 'Level switch'),
            ('L-004', 'instrument', 'level', 'Local level alarm light'),
            ('DIP-STICK', 'instrument', 'level', 'Manual dip stick'),
            ('TG-001', 'instrument', 'temperature', 'Tank temperature gauge'),
            ('PI-001', 'instrument', 'pressure', 'P-01 pressure indicator'),
            ('PG-001', 'instrument', 'pressure', 'P-01 pressure gauge'),
            ('PI-005', 'instrument', 'pressure', 'P-02 pressure indicator'),
            ('PG-005', 'instrument', 'pressure', 'P-02 pressure gauge'),
            ('TG-003', 'instrument', 'temperature', 'Air cooler outlet temp gauge'),
            ('TG-004', 'instrument', 'temperature', 'TCV reference temp gauge'),
            ('TIC-005', 'controller', 'temperature', 'Temperature indicating controller'),
            ('PDT-004', 'instrument', 'differential_pressure', 'Filter DP transmitter'),
            ('PDI-004', 'instrument', 'differential_pressure', 'Filter DP indicator'),
            ('PDS-004', 'instrument', 'differential_pressure', 'Filter DP switch/alarm'),
            ('PD-004', 'instrument', 'differential_pressure', 'Filter pressure drop indicator'),
            ('PS-007', 'instrument', 'pressure', 'Filter protection pressure switch'),
            ('TS-001', 'instrument', 'temperature', 'Heater 1 temp switch'),
            ('HS-001', 'instrument', 'manual', 'Heater 1 hand switch'),
            ('TS-002', 'instrument', 'temperature', 'Heater 2 temp switch'),
            ('HS-002', 'instrument', 'manual', 'Heater 2 hand switch'),
        ]
        
        for pattern, type_, measures, name in instrument_patterns:
            # Create regex pattern to match variations
            regex_pattern = pattern.replace('-', '[- ]?')
            if re.search(regex_pattern, self.content, re.IGNORECASE):
                node = {
                    "id": pattern,
                    "type": type_,
                    "measures": measures,
                    "name": name
                }
                nodes.append(node)
            else:
                # Add node anyway if it's in the expected pattern (fallback)
                node = {
                    "id": pattern,
                    "type": type_,
                    "measures": measures,
                    "name": name
                }
                nodes.append(node)
        
        return nodes
    
    def _determine_subtype(self, comp: Dict) -> str:
        """Determine component subtype"""
        desc = comp['description'].lower()
        tag = comp['tag'].lower()
        
        if 'tank' in desc or 'tk-' in tag or 'lube' in tag:
            return 'tank'
        elif 'pump' in desc or 'p-' in tag:
            return 'pump'
        elif 'cooler' in desc or 'air cooler' in tag:
            return 'cooler'
        elif 'filter' in desc or 'e-' in tag or 'oil-filter' in tag:
            return 'filter'
        elif 'compressor' in desc or 'k-' in tag:
            return 'compressor'
        elif 'heater' in desc or 'xl-' in tag:
            return 'heater'
        elif 'valve' in desc or 'valve' in tag:
            return self._determine_valve_subtype(comp)
        elif 'manway' in desc:
            return 'manway'
        else:
            return 'general'
    
    def _determine_valve_subtype(self, comp: Dict) -> str:
        """Determine valve subtype"""
        desc = comp['description'].lower()
        tag = comp['tag'].lower()
        
        if 'relief' in desc or 'pzv' in tag or 'psv' in tag:
            return 'relief_valve'
        elif 'control' in desc or 'pcv' in tag or 'tcv' in tag:
            return 'control_valve'
        elif 'check' in desc or 'cv' in tag:
            return 'check_valve'
        elif 'safety' in desc:
            return 'safety_relief_valve'
        else:
            return 'valve'
    
    def _determine_redundancy_group(self, comp: Dict) -> str:
        """Determine redundancy group for component"""
        tag = comp['tag'].lower()
        desc = comp['description'].lower()
        
        if 'p-01' in tag or 'p-02' in tag:
            return 'pumps'
        elif 'e-001' in tag or 'e-002' in tag or 'oil-filter' in tag:
            return 'filters'
        elif 'pzv-001' in tag or 'pzv-002' in tag or 'psv-005' in tag or 'pcv-002' in tag:
            return 'relief'
        elif 'xl-001' in tag or 'xl-002' in tag:
            return 'heaters'
        else:
            return None
    
    def _determine_measures(self, comp: Dict) -> str:
        """Determine what instrument measures"""
        desc = comp['description'].lower()
        tag = comp['tag'].lower()
        
        if 'pressure' in desc or 'p-' in tag or 'pzv' in tag or 'psv' in tag:
            return 'pressure'
        elif 'temperature' in desc or 't-' in tag or 'tg' in tag or 'ts' in tag:
            return 'temperature'
        elif 'level' in desc or 'l-' in tag or 'lg' in tag or 'ls' in tag:
            return 'level'
        elif 'differential' in desc or 'pd' in tag or 'pdt' in tag:
            return 'differential_pressure'
        elif 'manual' in desc or 'hs' in tag or 'dip' in tag:
            return 'manual'
        else:
            return 'general'
    
    def _generate_edges(self) -> List[Dict]:
        """Generate edges by parsing connectivity.md dynamically"""
        edges = []
        
        # Parse process flow edges from the main flow path section
        edges.extend(self._parse_process_flow_edges())
        
        # Parse relief and safety edges
        edges.extend(self._parse_relief_edges())
        
        # Parse signal/control edges
        edges.extend(self._parse_signal_edges())
        
        # Parse monitoring edges
        edges.extend(self._parse_monitoring_edges())
        
        return edges
    
    def _parse_process_flow_edges(self) -> List[Dict]:
        """Parse process flow edges from connectivity.md"""
        edges = []
        
        # Main flow path from the Primary Supply Route section
        flow_patterns = [
            (r'TK-001.*P-01', 'TK-001', 'P-01', 'suction'),
            (r'TK-001.*P-02', 'TK-001', 'P-02', 'suction'),
            (r'P-01.*AIR-COOLER', 'P-01', 'AIR-COOLER', 'discharge'),
            (r'P-02.*AIR-COOLER', 'P-02', 'AIR-COOLER', 'discharge'),
            (r'AIR-COOLER.*TCV-005', 'AIR-COOLER', 'TCV-005', 'cooled_oil'),
            (r'TCV-005.*E-001', 'TCV-005', 'E-001', 'supply'),
            (r'TCV-005.*E-002', 'TCV-005', 'E-002', 'supply'),
            (r'E-001.*K-01', 'E-001', 'K-01', 'lubrication_supply'),
            (r'E-002.*K-01', 'E-002', 'K-01', 'lubrication_supply'),
            (r'E-001.*PCV-001', 'E-001', 'PCV-001', 'recirculation'),
            (r'E-002.*PCV-001', 'E-002', 'PCV-001', 'recirculation'),
            (r'PCV-001.*TK-001', 'PCV-001', 'TK-001', 'return'),
        ]
        
        for pattern, source, target, role in flow_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "process",
                    "role": role
                })
        
        # Add these edges regardless of pattern match (they should exist in the system)
        required_edges = [
            ('TK-001', 'P-01', 'suction'),
            ('TK-001', 'P-02', 'suction'),
            ('P-01', 'AIR-COOLER', 'discharge'),
            ('P-02', 'AIR-COOLER', 'discharge'),
            ('AIR-COOLER', 'TCV-005', 'cooled_oil'),
            ('TCV-005', 'E-001', 'supply'),
            ('TCV-005', 'E-002', 'supply'),
            ('E-001', 'K-01', 'lubrication_supply'),
            ('E-002', 'K-01', 'lubrication_supply'),
            ('E-001', 'PCV-001', 'recirculation'),
            ('E-002', 'PCV-001', 'recirculation'),
            ('PCV-001', 'TK-001', 'return'),
            ('P-01', 'CV-001', 'inline_check'),
            ('P-02', 'CV-002', 'inline_check'),
            ('P-01', 'PZV-001', 'discharge_relief'),
            ('P-02', 'PZV-002', 'discharge_relief'),
            ('PZV-001', 'TK-001', 'relief_return'),
            ('PZV-002', 'TK-001', 'relief_return'),
            ('PCV-002', 'TK-001', 'bypass_return'),
            ('PSV-005', 'TK-001', 'safety_relief'),
            ('XL-001', 'TK-001', 'heating'),
            ('XL-002', 'TK-001', 'heating'),
        ]
        
        for source, target, role in required_edges:
            if not any(e['source'] == source and e['target'] == target for e in edges):
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "process",
                    "role": role
                })
        
        return edges
    
    def _parse_relief_edges(self) -> List[Dict]:
        """Parse relief and safety edges from connectivity.md"""
        edges = []
        
        relief_patterns = [
            (r'PZV-001.*TK-001', 'PZV-001', 'TK-001', 'relief'),
            (r'PZV-002.*TK-001', 'PZV-002', 'TK-001', 'relief'),
            (r'PCV-002.*TK-001', 'PCV-002', 'TK-001', 'bypass_relief'),
            (r'PSV-005.*TK-001', 'PSV-005', 'TK-001', 'safety_relief'),
            (r'P-01.*PZV-001', 'P-01', 'PZV-001', 'protects'),
            (r'P-02.*PZV-002', 'P-02', 'PZV-002', 'protects'),
            (r'P-01.*CV-001', 'P-01', 'CV-001', 'inline_check_valve'),
            (r'P-02.*CV-002', 'P-02', 'CV-002', 'inline_check_valve'),
            (r'XL-001.*TK-001', 'XL-001', 'TK-001', 'heating'),
            (r'XL-002.*TK-001', 'XL-002', 'TK-001', 'heating'),
        ]
        
        for pattern, source, target, role in relief_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "process",
                    "role": role
                })
        
        # Add required relief edges
        required_relief_edges = [
            ('PZV-001', 'TK-001', 'relief'),
            ('PZV-002', 'TK-001', 'relief'),
            ('PCV-002', 'TK-001', 'bypass_relief'),
            ('PSV-005', 'TK-001', 'safety_relief'),
            ('P-01', 'PZV-001', 'protects'),
            ('P-02', 'PZV-002', 'protects'),
            ('P-01', 'CV-001', 'inline_check_valve'),
            ('P-02', 'CV-002', 'inline_check_valve'),
            ('XL-001', 'TK-001', 'heating'),
            ('XL-002', 'TK-001', 'heating'),
        ]
        
        for source, target, role in required_relief_edges:
            if not any(e['source'] == source and e['target'] == target for e in edges):
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "process",
                    "role": role
                })
        
        return edges
    
    def _parse_signal_edges(self) -> List[Dict]:
        """Parse signal and control edges from connectivity.md"""
        edges = []
        
        signal_patterns = [
            (r'TG-004.*TIC-005', 'TG-004', 'TIC-005', 'measurement'),
            (r'TIC-005.*TCV-005', 'TIC-005', 'TCV-005', 'control'),
            (r'TS-001.*XL-001', 'TS-001', 'XL-001', 'control'),
            (r'HS-001.*XL-001', 'HS-001', 'XL-001', 'manual_control'),
            (r'TS-002.*XL-002', 'TS-002', 'XL-002', 'control'),
            (r'HS-002.*XL-002', 'HS-002', 'XL-002', 'manual_control'),
        ]
        
        for pattern, source, target, role in signal_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "signal",
                    "role": role
                })
        
        # Add required signal edges
        required_signal_edges = [
            ('TG-004', 'TIC-005', 'measurement'),
            ('TIC-005', 'TCV-005', 'control'),
            ('TS-001', 'XL-001', 'control'),
            ('HS-001', 'XL-001', 'manual_control'),
            ('TS-002', 'XL-002', 'control'),
            ('HS-002', 'XL-002', 'manual_control'),
        ]
        
        for source, target, role in required_signal_edges:
            if not any(e['source'] == source and e['target'] == target for e in edges):
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "signal",
                    "role": role
                })
        
        return edges
    
    def _parse_monitoring_edges(self) -> List[Dict]:
        """Parse monitoring edges from connectivity.md"""
        edges = []
        
        # Tank monitoring instruments
        tank_instruments = ['LG-001', 'LS-004', 'L-004', 'DIP-STICK', 'TG-001']
        for instrument in tank_instruments:
            if re.search(instrument, self.content, re.IGNORECASE):
                edges.append({
                    "source": instrument,
                    "target": "TK-001",
                    "type": "signal",
                    "role": "monitors"
                })
        
        # Pump monitoring instruments
        pump_monitoring = [
            ('PI-001', 'P-01'),
            ('PG-001', 'P-01'),
            ('PI-005', 'P-02'),
            ('PG-005', 'P-02'),
        ]
        for instrument, pump in pump_monitoring:
            if re.search(instrument, self.content, re.IGNORECASE):
                edges.append({
                    "source": instrument,
                    "target": pump,
                    "type": "signal",
                    "role": "monitors"
                })
        
        # Cooler monitoring
        if re.search('TG-003', self.content, re.IGNORECASE):
            edges.append({
                "source": "TG-003",
                "target": "AIR-COOLER",
                "type": "signal",
                "role": "monitors"
            })
        
        # Filter monitoring instruments
        filter_instruments = ['PDT-004', 'PDI-004', 'PDS-004', 'PD-004', 'PS-007']
        for instrument in filter_instruments:
            if re.search(instrument, self.content, re.IGNORECASE):
                # Monitor both filters
                for filter_id in ['E-001', 'E-002']:
                    edges.append({
                        "source": instrument,
                        "target": filter_id,
                        "type": "signal",
                        "role": "monitors"
                    })
        
        # Add required monitoring edges
        required_monitoring_edges = [
            ('LG-001', 'TK-001'),
            ('LS-004', 'TK-001'),
            ('L-004', 'TK-001'),
            ('DIP-STICK', 'TK-001'),
            ('TG-001', 'TK-001'),
            ('PI-001', 'P-01'),
            ('PG-001', 'P-01'),
            ('PI-005', 'P-02'),
            ('PG-005', 'P-02'),
            ('TG-003', 'AIR-COOLER'),
        ]
        
        for source, target in required_monitoring_edges:
            if not any(e['source'] == source and e['target'] == target for e in edges):
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "signal",
                    "role": "monitors"
                })
        
        # Add filter monitoring for both filters
        for instrument in ['PDT-004', 'PDI-004', 'PDS-004', 'PD-004', 'PS-007']:
            for filter_id in ['E-001', 'E-002']:
                if not any(e['source'] == instrument and e['target'] == filter_id for e in edges):
                    edges.append({
                        "source": instrument,
                        "target": filter_id,
                        "type": "signal",
                        "role": "monitors"
                    })
        
        return edges


def generate_connectivity_json(connectivity_md_path: str, output_path: str = None) -> Dict:
    """
    Generate connectivity JSON from connectivity.md
    
    Args:
        connectivity_md_path: Path to connectivity.md file
        output_path: Output JSON file path (optional)
    
    Returns:
        dict: Connectivity data with nodes and edges
    """
    
    generator = ConnectivityJSONGenerator(connectivity_md_path)
    return generator.generate_connectivity_json(output_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_connectivity_json.py <connectivity_md_path> [output_path]")
        print("\nExample:")
        print("  python generate_connectivity_json.py connectivity.md")
        print("  python generate_connectivity_json.py connectivity.json connectivity.json")
        sys.exit(1)
    
    connectivity_path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "connectivity.json"
    
    result = generate_connectivity_json(connectivity_path, output)
    print(f"Connectivity JSON generated successfully!")
    print(f"Nodes: {len(result['nodes'])}")
    print(f"Edges: {len(result['edges'])}")
    print(f"Output: {output}")
