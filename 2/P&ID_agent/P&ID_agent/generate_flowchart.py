"""
P&ID Flow Chart Generator
Generates professional P&ID diagrams from JSON connectivity data
"""

import json
from pathlib import Path
from typing import List, Dict


class FlowChartGenerator:
    """Generate professional P&ID diagrams from JSON connectivity data"""
    
    def __init__(self, connectivity_json_path: str):
        self.json_path = Path(connectivity_json_path)
        self.nodes = []
        self.edges = []
        self._load_connectivity_data()
    
    def _load_connectivity_data(self):
        """Load connectivity JSON data"""
        with open(self.json_path) as f:
            data = json.load(f)
        
        self.nodes = data.get('nodes', [])
        self.edges = data.get('edges', [])
    
    def generate_mermaid_flowchart(self, output_path: str = None) -> str:
        """Generate Mermaid.js flow chart from JSON connectivity data"""
        
        mermaid_code = "```mermaid\ngraph TD\n"
        
        # Define nodes with styling
        for node in self.nodes:
            node_id = node['id']
            label = f"{node['id']}\\n{node['name']}"
            
            # Add styling based on type
            if node['type'] == 'equipment':
                if node.get('subtype') == 'tank':
                    mermaid_code += f'    {node_id}["{label}"]:::tank\n'
                elif node.get('subtype') == 'pump':
                    mermaid_code += f'    {node_id}["{label}"]:::pump\n'
                elif node.get('subtype') == 'cooler':
                    mermaid_code += f'    {node_id}["{label}"]:::cooler\n'
                elif node.get('subtype') == 'filter':
                    mermaid_code += f'    {node_id}["{label}"]:::filter\n'
                elif node.get('subtype') == 'compressor':
                    mermaid_code += f'    {node_id}["{label}"]:::compressor\n'
                else:
                    mermaid_code += f'    {node_id}["{label}"]:::equipment\n'
            elif node['type'] == 'valve':
                mermaid_code += f'    {node_id}["{label}"]:::valve\n'
            elif node['type'] == 'instrument':
                mermaid_code += f'    {node_id}["{label}"]:::instrument\n'
            else:
                mermaid_code += f'    {node_id}["{label}"]\n'
        
        # Define edges
        for edge in self.edges:
            source = edge['source']
            target = edge['target']
            role = edge.get('role', '')
            
            if edge['type'] == 'process':
                mermaid_code += f'    {source} -->|{role}| {target}\n'
            elif edge['type'] == 'signal':
                mermaid_code += f'    {source} -.->|{role}| {target}\n'
        
        # Add CSS styling
        mermaid_code += """
    classDef tank fill:#f093fb,stroke:#333,stroke-width:2px
    classDef pump fill:#4facfe,stroke:#333,stroke-width:2px
    classDef cooler fill:#43e97b,stroke:#333,stroke-width:2px
    classDef filter fill:#fa709a,stroke:#333,stroke-width:2px
    classDef compressor fill:#a8edea,stroke:#333,stroke-width:2px
    classDef equipment fill:#667eea,stroke:#333,stroke-width:2px
    classDef valve fill:#f39c12,stroke:#333,stroke-width:2px
    classDef instrument fill:#e74c3c,stroke:#333,stroke-width:2px
```\n"""
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(mermaid_code)
        
        return mermaid_code
    
    def _identify_main_flow_components(self) -> List[Dict]:
        """Identify main flow components for flow chart"""
        # Filter and sort components for main flow
        main_flow = []
        
        # Priority order for flow chart
        priority_keywords = [
            'tank', 'storage', 'reservoir',
            'pump',
            'cooler', 'heater', 'exchanger',
            'valve', 'control',
            'filter', 'strainer',
            'compressor', 'turbine', 'engine'
        ]
        
        # Score components based on priority
        scored_components = []
        for comp in self.components:
            score = 0
            desc_lower = comp['description'].lower()
            tag_lower = comp['tag'].lower()
            
            for i, keyword in enumerate(priority_keywords):
                if keyword in desc_lower or keyword in tag_lower:
                    score = len(priority_keywords) - i
                    break
            
            scored_components.append((score, comp))
        
        # Sort by score and take top components
        scored_components.sort(key=lambda x: x[0], reverse=True)
        main_flow = [comp for score, comp in scored_components if score > 0]
        
        # If no components matched, return all equipment
        if not main_flow:
            main_flow = [c for c in self.components if c['type'] == 'Equipment']
        
        return main_flow[:10]  # Limit to top 10 components
    
    def generate_ascii_flowchart(self, output_path: str = None) -> str:
        """Generate ASCII art flow chart"""
        
        main_components = self._identify_main_flow_components()
        
        if not main_components:
            return "No components found for flow chart generation"
        
        ascii_chart = []
        ascii_chart.append("=" * 60)
        ascii_chart.append("PROCESS FLOW CHART")
        ascii_chart.append("=" * 60)
        ascii_chart.append("")
        
        # Build vertical flow
        for i, comp in enumerate(main_components):
            # Component box
            tag = comp['tag']
            desc = comp['description']
            
            # Truncate description if too long
            if len(desc) > 30:
                desc = desc[:27] + "..."
            
            box_width = max(len(tag), len(desc)) + 4
            box_line = "+" + "-" * (box_width - 2) + "+"
            
            ascii_chart.append(box_line)
            ascii_chart.append(f"| {tag.center(box_width - 4)} |")
            ascii_chart.append(f"| {desc.center(box_width - 4)} |")
            ascii_chart.append(box_line)
            
            # Add arrow if not last component
            if i < len(main_components) - 1:
                ascii_chart.append("    |")
                ascii_chart.append("    |")
                ascii_chart.append("    v")
                ascii_chart.append("")
        
        ascii_chart.append("")
        ascii_chart.append("=" * 60)
        ascii_chart.append(f"Total Components: {len(main_components)}")
        ascii_chart.append("=" * 60)
        
        chart_text = "\n".join(ascii_chart)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(chart_text)
        
        return chart_text
    
    def generate_html_flowchart(self, output_path: str) -> str:
        """Generate technical P&ID-style diagram with SVG"""
        
        # Build horizontal layout positions
        layout_data = self._build_horizontal_layout()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>P&ID Technical Diagram</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f0f0;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        .diagram-container {{
            overflow-x: auto;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            background: #ffffff;
            padding: 20px;
        }}
        .legend {{
            margin-top: 30px;
            padding: 20px;
            background: #ecf0f1;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .legend h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .legend-section {{
            margin-bottom: 20px;
        }}
        .legend-section h4 {{
            margin-top: 0;
            margin-bottom: 10px;
            color: #34495e;
            font-size: 14px;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 25px;
            margin-bottom: 10px;
        }}
        .legend-symbol {{
            display: inline-block;
            width: 24px;
            height: 24px;
            margin-right: 8px;
            vertical-align: middle;
            border-radius: 4px;
        }}
        .connection-description {{
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 6px;
            border: 1px solid #bdc3c7;
        }}
        .connection-description h4 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .connection-description ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .connection-description li {{
            margin-bottom: 5px;
            color: #34495e;
        }}
        .info {{
            margin-top: 20px;
            padding: 15px;
            background: #d5f4e6;
            border-radius: 8px;
            color: #27ae60;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>P&ID Technical Diagram</h1>
        <div class="diagram-container">
            {self._generate_svg_diagram(layout_data)}
        </div>
        <div class="legend">
            <h3>Legend</h3>
            <div class="legend-section">
                <h4>Component Types</h4>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: white; border: 2px solid #2c3e50;"></span>
                    Equipment (Tanks, Pumps, Filters, etc.)
                </div>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: white; border: 2px solid #2c3e50;"></span>
                    Valves (Control, Relief, Check)
                </div>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: white; border: 2px solid #e74c3c;"></span>
                    Temperature Instruments
                </div>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: white; border: 2px solid #3498db;"></span>
                    Pressure Instruments
                </div>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: white; border: 2px solid #9b59b6;"></span>
                    Level Instruments
                </div>
            </div>
            <div class="legend-section">
                <h4>Connection Types</h4>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: #2c3e50;"></span>
                    Main Process Lines (Thick dark)
                </div>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: #7f8c8d;"></span>
                    Secondary Lines (Medium gray)
                </div>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: #e74c3c;"></span>
                    Electrical Signals (Red dashed)
                </div>
                <div class="legend-item">
                    <span class="legend-symbol" style="background: #3498db;"></span>
                    Pneumatic Signals (Blue long-dash)
                </div>
            </div>
            <div class="connection-description">
                <h4>Connection Descriptions</h4>
                <ul>
                    <li><strong>Suction:</strong> Oil flow from tank to pumps</li>
                    <li><strong>Discharge:</strong> Pressurized oil from pumps to cooler</li>
                    <li><strong>Cooled Oil:</strong> Temperature-controlled oil to filters</li>
                    <li><strong>Supply:</strong> Filtered oil to compressor</li>
                    <li><strong>Recirculation:</strong> Return flow to tank via control valve</li>
                    <li><strong>Relief:</strong> Pressure relief paths to tank</li>
                    <li><strong>Heating:</strong> Tank heating from heaters</li>
                    <li><strong>Control:</strong> Pneumatic control signals</li>
                    <li><strong>Monitors:</strong> Electrical monitoring signals</li>
                </ul>
            </div>
        </div>
        <div class="info">
            <strong>Nodes:</strong> {len(self.nodes)} | 
            <strong>Edges:</strong> {len(self.edges)} | 
            <strong>Source:</strong> Generated from JSON connectivity data
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return html
    
    def _build_horizontal_layout(self) -> dict:
        """Build improved horizontal layout positions for technical P&ID diagram"""
        layout = {
            'nodes': {},
            'edges': []
        }
        
        # Define layout stages based on process flow with EXTREME spacing to prevent overlaps
        stages = [
            # Stage 0: Tank (leftmost)
            {'type': 'equipment', 'subtype': 'tank', 'x_offset': 0, 'y_offset': 0},
            # Stage 1: Heaters (above tank)
            {'type': 'equipment', 'subtype': 'heater', 'x_offset': 0, 'y_offset': -800},
            # Stage 2: Pumps (parallel)
            {'type': 'equipment', 'subtype': 'pump', 'x_offset': 1500, 'y_offset': 0},
            # Stage 3: Check valves (inline with pumps)
            {'type': 'valve', 'subtype': 'check_valve', 'x_offset': 2000, 'y_offset': 0},
            # Stage 4: Relief valves (above pumps)
            {'type': 'valve', 'subtype': 'relief_valve', 'x_offset': 1750, 'y_offset': -700},
            # Stage 5: Air cooler
            {'type': 'equipment', 'subtype': 'cooler', 'x_offset': 3000, 'y_offset': 0},
            # Stage 6: Temperature control valve
            {'type': 'valve', 'subtype': 'control_valve', 'x_offset': 3800, 'y_offset': 0},
            # Stage 7: Filters (parallel)
            {'type': 'equipment', 'subtype': 'filter', 'x_offset': 4500, 'y_offset': 0},
            # Stage 8: Recirculation valve (below filters)
            {'type': 'valve', 'subtype': 'pressure_control_valve', 'x_offset': 4500, 'y_offset': 700},
            # Stage 9: Compressor (rightmost)
            {'type': 'equipment', 'subtype': 'compressor', 'x_offset': 5500, 'y_offset': 0},
            # Stage 10: Safety relief (top right)
            {'type': 'valve', 'subtype': 'safety_relief_valve', 'x_offset': 750, 'y_offset': -1200},
        ]
        
        start_x = 300
        start_y = 1000
        y_spacing = 700
        
        # Position components by stage
        for stage in stages:
            components = []
            for node in self.nodes:
                if node.get('type') == stage['type'] and node.get('subtype') == stage['subtype']:
                    components.append(node)
            
            for i, comp in enumerate(components):
                x = start_x + stage['x_offset']
                y = start_y + stage['y_offset'] + (i - len(components)/2) * y_spacing
                
                layout['nodes'][comp['id']] = {
                    'x': x,
                    'y': y,
                    'type': comp['type'],
                    'subtype': comp['subtype']
                }
        
        # Position instruments near their monitored equipment with better spacing
        instruments = [n for n in self.nodes if n.get('type') in ['instrument', 'controller']]
        instrument_positions = {}
        
        for instrument in instruments:
            # Find what this instrument monitors based on edges
            monitored_equipment = None
            for edge in self.edges:
                if edge['source'] == instrument['id'] and edge.get('role') == 'monitors':
                    monitored_equipment = edge['target']
                    break
            
            if monitored_equipment and monitored_equipment in layout['nodes']:
                eq_pos = layout['nodes'][monitored_equipment]
                # Position instruments in a grid around equipment
                if monitored_equipment not in instrument_positions:
                    instrument_positions[monitored_equipment] = 0
                
                offset = instrument_positions[monitored_equipment]
                # Arrange instruments in a 3x2 grid around equipment with more spacing
                grid_x = (offset % 3) * 70 - 35
                grid_y = (offset // 3) * 50 - 25
                
                layout['nodes'][instrument['id']] = {
                    'x': eq_pos['x'] + grid_x + 80,
                    'y': eq_pos['y'] + grid_y - 60,
                    'type': instrument['type'],
                    'subtype': 'instrument'
                }
                
                instrument_positions[monitored_equipment] += 1
        
        # Position bypass relief valve
        bypass_relief = [n for n in self.nodes if n.get('subtype') == 'pressure_control_valve' and 'bypass' in n.get('name', '').lower()]
        for valve in bypass_relief:
            layout['nodes'][valve['id']] = {
                'x': start_x + 150,
                'y': start_y - 180,
                'type': valve['type'],
                'subtype': valve['subtype']
            }
        
        return layout
    
    def _generate_svg_diagram(self, layout_data: dict) -> str:
        """Generate SVG technical diagram"""
        
        # Calculate canvas size
        max_x = max(pos['x'] for pos in layout_data['nodes'].values()) + 200
        max_y = max(pos['y'] for pos in layout_data['nodes'].values()) + 200
        
        svg = f'<svg width="{max_x}" height="{max_y}" viewBox="0 0 {max_x} {max_y}" xmlns="http://www.w3.org/2000/svg">'
        
        # Add background
        svg += '<rect width="100%" height="100%" fill="white"/>'
        
        # Add grid
        svg += self._add_grid(max_x, max_y)
        
        # Draw process edges (piping lines) with appropriate line types and labels
        process_edges = [e for e in self.edges if e.get('type') == 'process']
        for edge in process_edges:
            if edge['source'] in layout_data['nodes'] and edge['target'] in layout_data['nodes']:
                source_pos = layout_data['nodes'][edge['source']]
                target_pos = layout_data['nodes'][edge['target']]
                # Determine line type based on role
                role = edge.get('role', '')
                if role in ['suction', 'discharge', 'lubrication_supply']:
                    line_type = "main"
                elif role in ['recirculation', 'relief', 'bypass_relief']:
                    line_type = "secondary"
                else:
                    line_type = "tertiary"
                svg += self._draw_process_line(source_pos['x'], source_pos['y'], target_pos['x'], target_pos['y'], line_type)
                # Add edge label
                if role:
                    svg += self._draw_edge_label(source_pos['x'], source_pos['y'], target_pos['x'], target_pos['y'], role.replace('_', ' ').title())
        
        # Draw signal edges with appropriate signal types and labels
        signal_edges = [e for e in self.edges if e.get('type') == 'signal']
        for edge in signal_edges:
            if edge['source'] in layout_data['nodes'] and edge['target'] in layout_data['nodes']:
                source_pos = layout_data['nodes'][edge['source']]
                target_pos = layout_data['nodes'][edge['target']]
                # Determine signal type based on role
                role = edge.get('role', '')
                if role in ['control', 'manual_control']:
                    signal_type = "pneumatic"
                elif role == 'monitors':
                    signal_type = "electrical"
                else:
                    signal_type = "electrical"
                svg += self._draw_signal_line(source_pos['x'], source_pos['y'], target_pos['x'], target_pos['y'], signal_type)
                # Add edge label for important signals
                if role in ['control', 'manual_control']:
                    svg += self._draw_edge_label(source_pos['x'], source_pos['y'], target_pos['x'], target_pos['y'], role.replace('_', ' ').title())
        
        # Draw nodes
        for node_id, pos in layout_data['nodes'].items():
            node = next((n for n in self.nodes if n['id'] == node_id), None)
            if node:
                svg += self._draw_technical_symbol(pos['x'], pos['y'], node)
        
        svg += '</svg>'
        
        return svg
    
    def _add_grid(self, width: float, height: float) -> str:
        """Add background grid"""
        grid = '<defs><pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">'
        grid += '<path d="M 50 0 L 0 0 0 50" fill="none" stroke="#e0e0e0" stroke-width="1"/>'
        grid += '</pattern>'
        grid += '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        grid += '<polygon points="0 0, 10 3.5, 0 7" fill="#2c3e50"/>'
        grid += '</marker>'
        grid += '<marker id="arrowhead-secondary" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        grid += '<polygon points="0 0, 8 3, 0 6" fill="#7f8c8d"/>'
        grid += '</marker></defs>'
        grid += f'<rect width="{width}" height="{height}" fill="url(#grid)"/>'
        return grid
    
    def _draw_process_line(self, x1: float, y1: float, x2: float, y2: float, line_type: str = "main") -> str:
        """Draw process piping line with proper routing and P&ID line types"""
        # Different line weights for different pipe sizes
        stroke_width = 4 if line_type == "main" else 2 if line_type == "secondary" else 1
        stroke_color = "#2c3e50" if line_type == "main" else "#7f8c8d" if line_type == "secondary" else "#95a5a6"
        marker = "url(#arrowhead)" if line_type == "main" else "url(#arrowhead-secondary)" if line_type == "secondary" else ""
        
        # Use improved orthogonal routing with better spacing to avoid overlaps
        if abs(x2 - x1) > abs(y2 - y1):
            # Horizontal primary, then vertical with offset
            mid_x = x1 + (x2 - x1) / 2
            # Add vertical offset to avoid overlapping with other horizontal lines
            offset = 15 if y1 > y2 else -15
            path = f'<path d="M {x1},{y1} L {mid_x},{y1} L {mid_x},{y2 + offset} L {x2},{y2 + offset} L {x2},{y2}" stroke="{stroke_color}" stroke-width="{stroke_width}" fill="none" marker-end="{marker}"/>'
        else:
            # Vertical primary, then horizontal with offset
            mid_y = y1 + (y2 - y1) / 2
            # Add horizontal offset to avoid overlapping with other vertical lines
            offset = 15 if x1 > x2 else -15
            path = f'<path d="M {x1},{y1} L {x1},{mid_y} L {x2 + offset},{mid_y} L {x2 + offset},{y2} L {x2},{y2}" stroke="{stroke_color}" stroke-width="{stroke_width}" fill="none" marker-end="{marker}"/>'
        return path
    
    def _draw_signal_line(self, x1: float, y1: float, x2: float, y2: float, signal_type: str = "electrical") -> str:
        """Draw signal line with proper routing and P&ID signal types"""
        # Different line styles for different signal types
        if signal_type == "electrical":
            stroke_color = "#e74c3c"
            stroke_dash = "5,3"
        elif signal_type == "pneumatic":
            stroke_color = "#3498db"
            stroke_dash = "10,5,2,5"
        elif signal_type == "hydraulic":
            stroke_color = "#27ae60"
            stroke_dash = "15,3"
        else:
            stroke_color = "#9b59b6"
            stroke_dash = "5,5"
        
        # Use orthogonal routing for signal lines
        if abs(x2 - x1) > abs(y2 - y1):
            # Horizontal primary, then vertical
            mid_x = x1 + (x2 - x1) / 2
            path = f'<path d="M {x1},{y1} L {mid_x},{y1} L {mid_x},{y2} L {x2},{y2}" stroke="{stroke_color}" stroke-width="1.5" fill="none" stroke-dasharray="{stroke_dash}"/>'
        else:
            # Vertical primary, then horizontal
            mid_y = y1 + (y2 - y1) / 2
            path = f'<path d="M {x1},{y1} L {x1},{mid_y} L {x2},{mid_y} L {x2},{y2}" stroke="{stroke_color}" stroke-width="1.5" fill="none" stroke-dasharray="{stroke_dash}"/>'
        return path
    
    def _draw_edge_label(self, x1: float, y1: float, x2: float, y2: float, label: str) -> str:
        """Draw label for edge connection with background for readability"""
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        # Add white background rectangle for text readability
        return f'<rect x="{mid_x - 25}" y="{mid_y - 12}" width="50" height="16" fill="white" stroke="#bdc3c7" stroke-width="1" rx="3"/>' + \
               f'<text x="{mid_x}" y="{mid_y}" text-anchor="middle" fill="#2c3e50" font-size="8" font-weight="bold" dominant-baseline="middle">{label}</text>'
    
    def _draw_technical_symbol(self, x: float, y: float, node: dict) -> str:
        """Draw professional P&ID symbol following ISA-5.1 standards"""
        svg = ''
        node_type = node.get('type', 'equipment')
        subtype = node.get('subtype', 'general')
        tag = node['id']
        name = node['name']
        
        if node_type == 'equipment':
            if subtype == 'tank':
                # Tank symbol - vertical vessel with rounded ends (EXTREMELY LARGE)
                svg += f'<rect x="{x-80}" y="{y-120}" width="160" height="240" rx="20" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<line x1="{x-80}" y1="{y}" x2="{x+80}" y2="{y}" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<text x="{x}" y="{y-140}" text-anchor="middle" fill="#2c3e50" font-size="28" font-weight="bold">{tag}</text>'
                svg += f'<text x="{x}" y="{y+160}" text-anchor="middle" fill="#7f8c8d" font-size="22">{name}</text>'
            elif subtype == 'pump':
                # Pump symbol - circle with impeller (EXTREMELY LARGE)
                svg += f'<circle cx="{x}" cy="{y}" r="60" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<circle cx="{x}" cy="{y}" r="40" fill="none" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<line x1="{x}" y1="{y-40}" x2="{x}" y2="{y+40}" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<line x1="{x-40}" y1="{y}" x2="{x+40}" y2="{y}" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<text x="{x}" y="{y+90}" text-anchor="middle" fill="#2c3e50" font-size="26" font-weight="bold">{tag}</text>'
            elif subtype == 'filter':
                # Filter symbol - Y-strainer (EXTREMELY LARGE)
                svg += f'<polygon points="{x},{y-80} {x+80},{y} {x},{y+80} {x-80},{y}" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<line x1="{x-60}" y1="{y-60}" x2="{x+60}" y2="{y+60}" stroke="#2c3e50" stroke-width="3"/>'
                svg += f'<line x1="{x-60}" y1="{y+60}" x2="{x+60}" y2="{y-60}" stroke="#2c3e50" stroke-width="3"/>'
                svg += f'<text x="{x}" y="{y+110}" text-anchor="middle" fill="#2c3e50" font-size="26" font-weight="bold">{tag}</text>'
            elif subtype == 'cooler':
                # Cooler symbol - heat exchanger (EXTREMELY LARGE)
                svg += f'<rect x="{x-100}" y="{y-70}" width="200" height="140" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<line x1="{x-100}" y1="{y-35}" x2="{x+100}" y2="{y-35}" stroke="#2c3e50" stroke-width="3"/>'
                svg += f'<line x1="{x-100}" y1="{y}" x2="{x+100}" y2="{y}" stroke="#2c3e50" stroke-width="3"/>'
                svg += f'<line x1="{x-100}" y1="{y+35}" x2="{x+100}" y2="{y+35}" stroke="#2c3e50" stroke-width="3"/>'
                svg += f'<text x="{x}" y="{y+110}" text-anchor="middle" fill="#2c3e50" font-size="26" font-weight="bold">{tag}</text>'
            elif subtype == 'compressor':
                # Compressor symbol - circle with K (EXTREMELY LARGE)
                svg += f'<circle cx="{x}" cy="{y}" r="70" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<text x="{x}" y="{y+20}" text-anchor="middle" fill="#2c3e50" font-size="50" font-weight="bold">K</text>'
                svg += f'<text x="{x}" y="{y+110}" text-anchor="middle" fill="#2c3e50" font-size="26" font-weight="bold">{tag}</text>'
            elif subtype == 'heater':
                # Heater symbol - rectangle with heating coils (EXTREMELY LARGE)
                svg += f'<rect x="{x-90}" y="{y-60}" width="180" height="120" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<path d="M {x-70},{y-40} Q {x-50},{y-60} {x-30},{y-40} Q {x-10},{y-20} {x+10},{y-40} Q {x+30},{y-60} {x+50},{y-40} Q {x+70},{y-60} {x+70},{y-40}" stroke="#e74c3c" stroke-width="5" fill="none"/>'
                svg += f'<path d="M {x-70},{y+40} Q {x-50},{y+20} {x-30},{y+40} Q {x-10},{y+60} {x+10},{y+40} Q {x+30},{y+20} {x+50},{y+40} Q {x+70},{y+60} {x+70},{y+40}" stroke="#e74c3c" stroke-width="5" fill="none"/>'
                svg += f'<text x="{x}" y="{y+100}" text-anchor="middle" fill="#2c3e50" font-size="26" font-weight="bold">{tag}</text>'
            else:
                # Generic equipment
                svg += f'<rect x="{x-30}" y="{y-20}" width="60" height="40" fill="white" stroke="#2c3e50" stroke-width="3"/>'
                svg += f'<text x="{x}" y="{y+5}" text-anchor="middle" fill="#2c3e50" font-size="10" font-weight="bold">{tag}</text>'
        
        elif node_type == 'valve':
            if 'control' in subtype:
                # Control valve symbol - bowtie with actuator (EXTREMELY LARGE)
                svg += f'<polygon points="{x-50},{y-50} {x+50},{y-50} {x},{y+50}" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<rect x="{x-20}" y="{y-110}" width="40" height="60" fill="white" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<line x1="{x}" y1="{y-110}" x2="{x}" y2="{y-130}" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<circle cx="{x}" cy="{y-135}" r="12" fill="white" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<text x="{x}" y="{y+80}" text-anchor="middle" fill="#2c3e50" font-size="24" font-weight="bold">{tag}</text>'
            elif 'relief' in subtype:
                # Relief valve symbol - T-shape with spring (EXTREMELY LARGE)
                svg += f'<polygon points="{x-50},{y-60} {x+50},{y-60} {x},{y+35}" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<path d="M {x-20},{y-70} L {x-20},{y-110} M {x+20},{y-70} L {x+20},{y-110}" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<path d="M {x-30},{y-110} Q {x},{y-130} {x+30},{y-110}" stroke="#2c3e50" stroke-width="4" fill="none"/>'
                svg += f'<text x="{x}" y="{y+70}" text-anchor="middle" fill="#2c3e50" font-size="24" font-weight="bold">{tag}</text>'
            elif 'check' in subtype:
                # Check valve symbol - triangle with line (EXTREMELY LARGE)
                svg += f'<polygon points="{x-50},{y-50} {x+50},{y} {x-50},{y+50}" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<line x1="{x-50}" y1="{y}" x2="{x+50}" y2="{y}" stroke="#2c3e50" stroke-width="4"/>'
                svg += f'<text x="{x}" y="{y+80}" text-anchor="middle" fill="#2c3e50" font-size="24" font-weight="bold">{tag}</text>'
            else:
                # Generic valve (EXTREMELY LARGE)
                svg += f'<polygon points="{x-40},{y-40} {x+40},{y-40} {x},{y+40}" fill="white" stroke="#2c3e50" stroke-width="6"/>'
                svg += f'<text x="{x}" y="{y+70}" text-anchor="middle" fill="#2c3e50" font-size="24" font-weight="bold">{tag}</text>'
        
        elif node_type in ['instrument', 'controller']:
            # Instrument bubble - circle with proper ISA tag format (EXTREMELY LARGE)
            measures = node.get('measures', 'general')
            color = '#e74c3c' if measures == 'temperature' else '#3498db' if measures == 'pressure' else '#9b59b6' if measures == 'level' else '#95a5a6'
            svg += f'<circle cx="{x}" cy="{y}" r="50" fill="white" stroke="{color}" stroke-width="6"/>'
            svg += f'<text x="{x}" y="{y+12}" text-anchor="middle" fill="{color}" font-size="22" font-weight="bold">{tag}</text>'
        
        return svg
    
    def _generate_flow_html(self, flow_sequence: list) -> str:
        """Generate HTML for flow diagram"""
        html_parts = []
        
        for i, stage in enumerate(flow_sequence):
            stage_type = stage['type']
            components = stage['components']
            label = stage.get('label', '')
            
            if len(components) == 1:
                # Single component
                comp = components[0]
                html_parts.append(self._create_component_html(comp, stage_type))
            else:
                # Multiple components (parallel)
                html_parts.append('<div class="parallel-group">')
                if label:
                    html_parts.append(f'<div class="parallel-label">{label}</div>')
                for comp in components:
                    html_parts.append(self._create_component_html(comp, stage_type))
                html_parts.append('</div>')
            
            # Add arrow if not last stage
            if i < len(flow_sequence) - 1:
                html_parts.append('<div class="arrow">&darr;</div>')
        
        return '\n'.join(html_parts)
    
    def _create_component_html(self, node: dict, comp_type: str) -> str:
        """Create HTML for individual component"""
        tag = node['id']
        name = node['name']
        
        # Truncate name if too long
        if len(name) > 25:
            name = name[:22] + "..."
        
        return f"""
            <div class="component {comp_type}">
                <div class="tag">{tag}</div>
                <div class="description">{name}</div>
            </div>
        """
    
    def _generate_svg_diagram_old(self, width: float, height: float, scale: float) -> str:
        """Generate SVG content for P&ID diagram (deprecated - use layout-based version)"""
        
        svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        
        # Add grid background
        svg += self._add_grid(width, height)
        
        # Add tile boundaries
        svg += self._add_tile_boundaries(scale)
        
        # Add components
        svg += self._add_components(scale)
        
        # Add connections (simplified)
        svg += self._add_connections(scale)
        
        svg += '</svg>'
        
        return svg
    
    def _add_grid(self, width: float, height: float) -> str:
        """Add grid background to SVG"""
        grid = '<defs><pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">'
        grid += '<path d="M 50 0 L 0 0 0 50" fill="none" stroke="#e0e0e0" stroke-width="1"/>'
        grid += '</pattern></defs>'
        grid += f'<rect width="{width}" height="{height}" fill="url(#grid)"/>'
        return grid
    
    def _add_tile_boundaries(self, scale: float) -> str:
        """Add tile boundary rectangles"""
        boundaries = ''
        for tile in self.tiles:
            x1, y1, x2, y2 = tile['bbox']
            boundaries += f'<rect x="{x1 * scale}" y="{y1 * scale}" width="{(x2-x1) * scale}" height="{(y2-y1) * scale}" '
            boundaries += 'fill="none" stroke="#bdc3c7" stroke-width="2" stroke-dasharray="5,5" opacity="0.5"/>'
            boundaries += f'<text x="{x1 * scale + 10}" y="{y1 * scale + 20}" font-size="12" fill="#7f8c8d">Tile {tile["tile_id"]}</text>'
        return boundaries
    
    def _add_components(self, scale: float) -> str:
        """Add component symbols to SVG"""
        components_svg = ''
        
        for comp in self.components:
            x = comp['x'] * scale
            y = comp['y'] * scale
            tag = comp['tag']
            comp_type = comp['type']
            
            # Choose color based on type
            if comp_type == 'Equipment':
                if 'pump' in comp['description'].lower() or 'P-' in tag:
                    color = '#f39c12'  # Orange for pumps
                    shape = 'pump'
                elif 'tank' in comp['description'].lower() or 'TK-' in tag:
                    color = '#9b59b6'  # Purple for tanks
                    shape = 'tank'
                elif 'filter' in comp['description'].lower() or 'E-' in tag:
                    color = '#1abc9c'  # Teal for filters
                    shape = 'filter'
                else:
                    color = '#3498db'  # Blue for equipment
                    shape = 'circle'
            elif comp_type == 'Instrument':
                color = '#e74c3c'  # Red for instruments
                shape = 'instrument'
            elif comp_type == 'Valve':
                color = '#27ae60'  # Green for valves
                shape = 'valve'
            else:
                color = '#95a5a6'  # Gray for others
                shape = 'circle'
            
            # Draw component
            components_svg += self._draw_component(x, y, tag, color, shape)
        
        return components_svg
    
    def _draw_component(self, x: float, y: float, tag: str, color: str, shape: str) -> str:
        """Draw individual component symbol"""
        svg = ''
        size = 30
        
        if shape == 'pump':
            # Draw pump symbol (circle with triangle)
            svg += f'<circle cx="{x}" cy="{y}" r="{size}" fill="{color}" stroke="#2c3e50" stroke-width="2"/>'
            svg += f'<polygon points="{x},{y-size+10} {x-size+10},{y+size-10} {x+size-10},{y+size-10}" fill="white" stroke="#2c3e50" stroke-width="2"/>'
        elif shape == 'tank':
            # Draw tank symbol (rectangle with rounded corners)
            svg += f'<rect x="{x-size}" y="{y-size*1.5}" width="{size*2}" height="{size*3}" rx="10" fill="{color}" stroke="#2c3e50" stroke-width="2"/>'
        elif shape == 'filter':
            # Draw filter symbol (diamond)
            svg += f'<polygon points="{x},{y-size} {x+size},{y} {x},{y+size} {x-size},{y}" fill="{color}" stroke="#2c3e50" stroke-width="2"/>'
        elif shape == 'instrument':
            # Draw instrument symbol (small circle)
            svg += f'<circle cx="{x}" cy="{y}" r="{size/2}" fill="{color}" stroke="#2c3e50" stroke-width="2"/>'
        elif shape == 'valve':
            # Draw valve symbol (bowtie)
            svg += f'<polygon points="{x-size},{y-size} {x+size},{y-size} {x-size},{y+size} {x+size},{y+size}" fill="{color}" stroke="#2c3e50" stroke-width="2"/>'
        else:
            # Default circle
            svg += f'<circle cx="{x}" cy="{y}" r="{size}" fill="{color}" stroke="#2c3e50" stroke-width="2"/>'
        
        # Add tag label
        svg += f'<text x="{x}" y="{y + size + 15}" font-size="11" font-weight="bold" text-anchor="middle" fill="#2c3e50">{tag}</text>'
        
        return svg
    
    def _add_connections(self, scale: float) -> str:
        """Add simplified connections between components"""
        connections = ''
        
        # Sort components by Y position (top to bottom flow)
        sorted_comps = sorted(self.components, key=lambda c: c['y'])
        
        # Connect sequential components
        for i in range(len(sorted_comps) - 1):
            comp1 = sorted_comps[i]
            comp2 = sorted_comps[i + 1]
            
            # Only connect if they're reasonably close in Y (same flow path)
            if abs(comp2['y'] - comp1['y']) < 300:  # Threshold for same flow path
                x1 = comp1['x'] * scale
                y1 = comp1['y'] * scale
                x2 = comp2['x'] * scale
                y2 = comp2['y'] * scale
                
                # Draw connection line
                connections += f'<line x1="{x1}" y1="{y1 + 30}" x2="{x2}" y2="{y2 - 30}" '
                connections += 'stroke="#34495e" stroke-width="3" marker-end="url(#arrowhead)"/>'
        
        # Add arrowhead marker
        connections += '<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        connections += '<polygon points="0 0, 10 3.5, 0 7" fill="#34495e"/></marker></defs>'
        
        return connections


def generate_flowchart(connectivity_json_path: str, output_format: str = "html", output_path: str = None):
    """
    Generate flow chart from connectivity JSON
    
    Args:
        connectivity_json_path: Path to connectivity.json file
        output_format: Format - 'mermaid', 'ascii', or 'html' (default: html)
        output_path: Output file path (optional)
    
    Returns:
        str: Generated flow chart content
    """
    
    generator = FlowChartGenerator(connectivity_json_path)
    
    if output_format == "mermaid":
        if output_path is None:
            output_path = Path(connectivity_json_path).parent / "flowchart_mermaid.md"
        return generator.generate_mermaid_flowchart(output_path)
    
    elif output_format == "ascii":
        if output_path is None:
            output_path = Path(connectivity_json_path).parent / "flowchart_ascii.txt"
        return generator.generate_ascii_flowchart(output_path)
    
    elif output_format == "html":
        if output_path is None:
            output_path = Path(connectivity_json_path).parent / "flowchart.html"
        return generator.generate_html_flowchart(output_path)
    
    else:
        raise ValueError(f"Unknown format: {output_format}. Use 'mermaid', 'ascii', or 'html'")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_flowchart.py <connectivity_json_path> [format] [output_path]")
        print("\nFormats:")
        print("  html   - Interactive HTML flow chart (default)")
        print("  mermaid- Mermaid.js flow chart")
        print("  ascii  - ASCII art flow chart")
        print("\nExamples:")
        print("  python generate_flowchart.py connectivity.json")
        print("  python generate_flowchart.py connectivity.json mermaid")
        print("  python generate_flowchart.py connectivity.json html my_flowchart.html")
        sys.exit(1)
    
    json_path = sys.argv[1]
    format_type = sys.argv[2] if len(sys.argv) > 2 else "html"
    output = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = generate_flowchart(json_path, format_type, output)
    print(f"Flow chart generated successfully!")
    print(f"Format: {format_type}")
    if output:
        print(f"Output: {output}")
    else:
        print(f"Output: Default location for {format_type} format")
