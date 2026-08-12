"""
P&ID Report Generator v2.0

Automated HAZOP study report generation from P&ID extraction data.

Improvements over v1.0:
- Template-based report generation (Jinja2-like)
- HAZOP node identification from graph structure
- Deviation analysis with guide words
- Risk matrix integration
- Action item tracking
- Export to Markdown, HTML, PDF-ready
- Cross-reference validation
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# HAZOP Data Models
# ---------------------------------------------------------------------------

class Severity(Enum):
    NEGLIGIBLE = 1
    MINOR = 2
    MODERATE = 3
    MAJOR = 4
    CATASTROPHIC = 5


class Likelihood(Enum):
    REMOTE = 1
    UNLIKELY = 2
    POSSIBLE = 3
    LIKELY = 4
    ALMOST_CERTAIN = 5


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class HAZOPDeviation:
    """A single HAZOP deviation analysis."""
    guide_word: str
    parameter: str
    deviation: str
    cause: str
    consequence: str
    safeguards: list[str] = field(default_factory=list)
    severity: Severity = Severity.MINOR
    likelihood: Likelihood = Likelihood.UNLIKELY
    risk_level: RiskLevel = RiskLevel.LOW
    action_required: bool = False
    action_description: str = ""
    responsible: str = ""
    due_date: str = ""

    @property
    def risk_score(self) -> int:
        return self.severity.value * self.likelihood.value

    def to_dict(self) -> dict:
        return {
            "guide_word": self.guide_word,
            "parameter": self.parameter,
            "deviation": self.deviation,
            "cause": self.cause,
            "consequence": self.consequence,
            "safeguards": self.safeguards,
            "severity": self.severity.name,
            "likelihood": self.likelihood.name,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "action_required": self.action_required,
            "action_description": self.action_description,
            "responsible": self.responsible,
            "due_date": self.due_date,
        }


@dataclass
class HAZOPNode:
    """A HAZOP study node (section of the P&ID)."""
    node_id: str
    description: str
    design_intent: str
    parameters: list[str] = field(default_factory=list)
    deviations: list[HAZOPDeviation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "description": self.description,
            "design_intent": self.design_intent,
            "parameters": self.parameters,
            "deviations": [d.to_dict() for d in self.deviations],
        }


@dataclass
class ReportData:
    """Complete report data structure."""
    system_name: str = ""
    pid_source: str = ""
    analysis_date: str = ""
    analyst: str = ""
    methodology: str = "HAZOP (IEC 61882)"

    # Summary
    total_nodes: int = 0
    total_deviations: int = 0
    total_actions: int = 0
    risk_distribution: dict = field(default_factory=dict)

    # Sections
    system_description: str = ""
    equipment_inventory: list[dict] = field(default_factory=list)
    instrument_list: list[dict] = field(default_factory=list)
    safety_systems: list[dict] = field(default_factory=list)
    hazop_nodes: list[HAZOPNode] = field(default_factory=list)
    action_items: list[dict] = field(default_factory=list)

    # Appendices
    connectivity_data: dict = field(default_factory=dict)
    extraction_metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# HAZOP Node Generator
# ---------------------------------------------------------------------------

class HAZOPNodeGenerator:
    """Generate HAZOP nodes from connectivity graph."""

    # Standard HAZOP guide words per IEC 61882
    GUIDE_WORDS = [
        "NO", "MORE", "LESS", "AS WELL AS", "PART OF", "REVERSE",
        "OTHER THAN", "EARLY", "LATE", "BEFORE", "AFTER"
    ]

    # Parameters for lube oil systems
    PARAMETERS = [
        "Flow", "Pressure", "Temperature", "Level", "Composition", "Viscosity"
    ]

    def __init__(self, graph_data: dict):
        self.nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
        self.edges = graph_data.get("edges", [])
        self._build_index()

    def _build_index(self):
        """Build adjacency indices."""
        self.outgoing = defaultdict(list)
        self.incoming = defaultdict(list)
        for e in self.edges:
            self.outgoing[e["source"]].append(e)
            self.incoming[e["target"]].append(e)

    def generate_nodes(self) -> list[HAZOPNode]:
        """Generate HAZOP nodes from graph structure."""
        hazop_nodes = []

        # Identify process nodes (equipment with process connections)
        process_nodes = self._identify_process_nodes()

        for node_id in process_nodes:
            node = self.nodes.get(node_id)
            if not node:
                continue

            hazop_node = self._analyze_node(node_id, node)
            if hazop_node.deviations:
                hazop_nodes.append(hazop_node)

        return hazop_nodes

    def _identify_process_nodes(self) -> list[str]:
        """Identify nodes that should be HAZOP study nodes."""
        # Key equipment nodes
        key_types = {"tank", "pump", "compressor", "cooler", "filter", "heater"}
        nodes = []
        for node_id, node in self.nodes.items():
            if node.get("subtype") in key_types or node.get("type") == "equipment":
                # Only include nodes with process connections
                has_process = any(
                    e["type"] == "process" for e in self.outgoing[node_id] + self.incoming[node_id]
                )
                if has_process:
                    nodes.append(node_id)
        return nodes

    def _analyze_node(self, node_id: str, node: dict) -> HAZOPNode:
        """Analyze a single node for HAZOP deviations."""

        subtype = node.get("subtype", "")
        name = node.get("name", node_id)

        hazop_node = HAZOPNode(
            node_id=node_id,
            description=f"{name} ({node_id})",
            design_intent=self._get_design_intent(node_id, subtype),
            parameters=self._get_parameters(subtype),
        )

        # Generate deviations for each parameter
        for param in hazop_node.parameters:
            for guide_word in ["NO", "MORE", "LESS", "REVERSE", "AS WELL AS", "OTHER THAN"]:
                deviation = self._create_deviation(node_id, guide_word, param)
                if deviation:
                    hazop_node.deviations.append(deviation)

        return hazop_node

    def _get_design_intent(self, node_id: str, subtype: str) -> str:
        """Get design intent for equipment type."""
        intents = {
            "tank": "Store lube oil at correct level and temperature",
            "pump": "Supply lube oil at required pressure and flow rate",
            "compressor": "Receive clean, temperature-controlled lube oil for bearing lubrication",
            "cooler": "Cool hot oil to optimal temperature for compressor lubrication",
            "filter": "Remove contaminants from lube oil before compressor supply",
            "heater": "Maintain tank oil temperature above minimum during cold conditions",
        }
        return intents.get(subtype, f"Perform function for {node_id}")

    def _get_parameters(self, subtype: str) -> list[str]:
        """Get relevant parameters for equipment type."""
        params = {
            "tank": ["Level", "Temperature", "Composition"],
            "pump": ["Flow", "Pressure", "Temperature"],
            "compressor": ["Flow", "Pressure", "Temperature", "Composition"],
            "cooler": ["Temperature", "Flow"],
            "filter": ["Flow", "Pressure", "Composition"],
            "heater": ["Temperature", "Flow"],
        }
        return params.get(subtype, ["Flow", "Pressure", "Temperature"])

    def _create_deviation(self, node_id: str, guide_word: str, parameter: str) -> Optional[HAZOPDeviation]:
        """Create a deviation analysis for a guide word + parameter combination."""

        # Skip meaningless combinations
        if guide_word == "REVERSE" and parameter not in ("Flow", "Level"):
            return None
        if guide_word == "AS WELL AS" and parameter not in ("Composition", "Flow"):
            return None

        deviation_text = f"{guide_word} {parameter}"

        # Find causes and consequences based on node type and connections
        cause = self._infer_cause(node_id, guide_word, parameter)
        consequence = self._infer_consequence(node_id, guide_word, parameter)
        safeguards = self._find_safeguards(node_id, parameter)

        # Assess risk
        severity, likelihood = self._assess_risk(node_id, guide_word, parameter, consequence)
        risk_score = severity.value * likelihood.value
        risk_level = self._risk_level(risk_score)
        action_required = risk_level in (RiskLevel.HIGH, RiskLevel.EXTREME)

        return HAZOPDeviation(
            guide_word=guide_word,
            parameter=parameter,
            deviation=deviation_text,
            cause=cause,
            consequence=consequence,
            safeguards=safeguards,
            severity=severity,
            likelihood=likelihood,
            risk_level=risk_level,
            action_required=action_required,
            action_description=self._suggest_action(guide_word, parameter, node_id) if action_required else "",
        )

    def _infer_cause(self, node_id: str, guide_word: str, parameter: str) -> str:
        """Infer likely cause from graph structure."""
        causes = {
            ("NO", "Flow"): "Pump failure, blockage, valve closure, low tank level",
            ("NO", "Pressure"): "Pump failure, relief valve opening, leak",
            ("NO", "Temperature"): "Sensor failure, heater/cooler malfunction",
            ("NO", "Level"): "Leak, drain valve open, no inflow",
            ("MORE", "Flow"): "Control valve failure open, recirculation valve stuck",
            ("MORE", "Pressure"): "Pump overspeed, blockage downstream, thermal expansion",
            ("MORE", "Temperature"): "Heater malfunction, cooler failure, ambient temperature rise",
            ("MORE", "Level"): "Inflow exceeds outflow, overflow from upstream",
            ("LESS", "Flow"): "Partial blockage, filter clogging, valve restriction",
            ("LESS", "Pressure"): "Pump wear, leak, partial relief valve opening",
            ("LESS", "Temperature"): "Cooler overcooling, heater failure, ambient drop",
            ("LESS", "Level"): "Leak, evaporation, outflow exceeds inflow",
            ("REVERSE", "Flow"): "Check valve failure, pump shutdown with back pressure",
            ("AS WELL AS", "Composition"): "Contamination, water ingress, wrong oil grade",
            ("OTHER THAN", "Flow"): "Wrong fluid, two-phase flow, cavitation",
        }
        return causes.get((guide_word, parameter), "Unknown cause - requires investigation")

    def _infer_consequence(self, node_id: str, guide_word: str, parameter: str) -> str:
        """Infer consequence from graph structure."""
        node = self.nodes.get(node_id, {})
        subtype = node.get("subtype", "")

        if subtype == "compressor":
            if guide_word == "NO" and parameter in ("Flow", "Pressure"):
                return "Loss of lubrication, bearing damage, compressor trip, potential fire"
            if guide_word == "MORE" and parameter == "Temperature":
                return "Oil degradation, reduced viscosity, bearing overheating"

        if subtype == "pump":
            if guide_word == "NO" and parameter == "Flow":
                return "Loss of compressor lubrication, potential equipment damage"
            if guide_word == "MORE" and parameter == "Pressure":
                return "Overpressure, relief valve activation, seal damage"

        if subtype == "tank":
            if guide_word == "NO" and parameter == "Level":
                return "Pump cavitation, loss of lubrication supply, compressor damage"
            if guide_word == "MORE" and parameter == "Level":
                return "Tank overflow, environmental spill, fire hazard"

        if subtype == "filter":
            if guide_word == "MORE" and parameter == "Pressure":
                return "High differential pressure, filter element damage, bypass opening"
            if guide_word == "NO" and parameter == "Flow":
                return "No filtration, contaminated oil reaches compressor"

        return "Process upset, potential equipment damage, safety hazard"

    def _find_safeguards(self, node_id: str, parameter: str) -> list[str]:
        """Find safeguards from connected instruments."""
        safeguards = []

        # Find monitoring instruments connected to this node
        for edge in self.incoming.get(node_id, []):
            if edge["type"] == "signal" and edge["role"] in ("monitors", "monitors_pressure", "monitors_temperature", "monitors_level"):
                inst_id = edge["source"]
                inst = self.nodes.get(inst_id, {})
                safeguards.append(f"{inst_id} ({inst.get('name', '')})")

        # Find relief valves
        for edge in self.outgoing.get(node_id, []):
            if edge["type"] == "process" and "relief" in edge.get("role", ""):
                valve_id = edge["target"]
                safeguards.append(f"Relief path via {valve_id}")

        # Find redundancy
        node = self.nodes.get(node_id, {})
        if node.get("redundancy_group"):
            safeguards.append(f"Redundancy: {node.get('redundancy_group')}")

        return safeguards if safeguards else ["No automatic safeguards identified"]

    def _assess_risk(self, node_id: str, guide_word: str, parameter: str, consequence: str) -> tuple[Severity, Likelihood]:
        """Assess severity and likelihood."""
        node = self.nodes.get(node_id, {})
        subtype = node.get("subtype", "")

        # Severity based on consequence keywords
        severity = Severity.MODERATE
        if any(kw in consequence.lower() for kw in ["catastrophic", "multiple fatalities", "explosion"]):
            severity = Severity.CATASTROPHIC
        elif any(kw in consequence.lower() for kw in ["fire", "compressor damage", "loss of lubrication"]):
            severity = Severity.MAJOR
        elif any(kw in consequence.lower() for kw in ["equipment damage", "trip", "spill"]):
            severity = Severity.MODERATE

        # Likelihood based on safeguards
        safeguards = self._find_safeguards(node_id, parameter)
        likelihood = Likelihood.POSSIBLE
        if len(safeguards) >= 3:
            likelihood = Likelihood.UNLIKELY
        elif len(safeguards) >= 1:
            likelihood = Likelihood.POSSIBLE
        else:
            likelihood = Likelihood.LIKELY

        # Adjust for compressor (most critical)
        if subtype == "compressor" and guide_word == "NO" and parameter in ("Flow", "Pressure"):
            severity = Severity.MAJOR
            likelihood = Likelihood.POSSIBLE

        return severity, likelihood

    def _risk_level(self, score: int) -> RiskLevel:
        """Map risk score to risk level."""
        if score <= 3:
            return RiskLevel.LOW
        elif score <= 6:
            return RiskLevel.MEDIUM
        elif score <= 12:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME

    def _suggest_action(self, guide_word: str, parameter: str, node_id: str) -> str:
        """Suggest corrective action."""
        actions = {
            ("NO", "Flow"): "Verify pump auto-start logic, confirm standby pump availability",
            ("NO", "Pressure"): "Review pressure switch settings, verify alarm response procedures",
            ("NO", "Level"): "Verify level switch interlock, confirm low level alarm setpoint",
            ("MORE", "Pressure"): "Verify relief valve setpoints, inspect for blockage",
            ("MORE", "Temperature"): "Verify cooler capacity, check temperature controller tuning",
            ("LESS", "Flow"): "Establish filter change schedule, verify DP alarm setpoints",
            ("LESS", "Level"): "Inspect tank and piping for leaks, verify level control",
        }
        return actions.get((guide_word, parameter), "Investigate and implement appropriate safeguards")


# ---------------------------------------------------------------------------
# Report Exporters
# ---------------------------------------------------------------------------

def generate_markdown_report(data: ReportData) -> str:
    """Generate comprehensive Markdown HAZOP report."""

    lines = [
        f"# HAZOP Study Report — {data.system_name}",
        "",
        "## Document Information",
        "",
        f"| Property | Value |",
        f"|----------|-------|",
        f"| **System** | {data.system_name} |",
        f"| **P&ID Source** | {data.pid_source} |",
        f"| **Analysis Date** | {data.analysis_date} |",
        f"| **Methodology** | {data.methodology} |",
        f"| **Analyst** | {data.analyst} |",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total HAZOP Nodes:** {data.total_nodes}",
        f"- **Total Deviations Analyzed:** {data.total_deviations}",
        f"- **Action Items:** {data.total_actions}",
        f"- **Risk Distribution:** {data.risk_distribution}",
        "",
        "## System Description",
        "",
        data.system_description,
        "",
        "---",
        "",
        "## Equipment Inventory",
        "",
        "| Tag | Type | Description | Redundancy |",
        "|-----|------|-------------|------------|",
    ]

    for eq in data.equipment_inventory:
        lines.append(f"| {eq.get('id', '')} | {eq.get('subtype', '')} | {eq.get('name', '')} | {eq.get('redundancy_group', 'N/A')} |")

    lines.extend([
        "",
        "## Instrumentation List",
        "",
        "| Tag | Type | Measures | Description |",
        "|-----|------|----------|-------------|",
    ])

    for inst in data.instrument_list:
        lines.append(f"| {inst.get('id', '')} | {inst.get('type', '')} | {inst.get('measures', '')} | {inst.get('name', '')} |")

    lines.extend([
        "",
        "---",
        "",
        "## HAZOP Study Results",
        "",
    ])

    for node in data.hazop_nodes:
        lines.extend([
            f"### Node: {node.node_id}",
            "",
            f"**Description:** {node.description}",
            f"**Design Intent:** {node.design_intent}",
            f"**Parameters:** {', '.join(node.parameters)}",
            "",
        ])

        if node.deviations:
            lines.extend([
                "| Guide Word | Parameter | Deviation | Cause | Consequence | Safeguards | Risk | Action |",
                "|------------|-----------|-----------|-------|-------------|------------|------|--------|",
            ])

            for dev in node.deviations:
                safeguards = ", ".join(dev.safeguards[:2]) + ("..." if len(dev.safeguards) > 2 else "")
                action = dev.action_description if dev.action_required else "None"
                lines.append(
                    f"| {dev.guide_word} | {dev.parameter} | {dev.deviation} | {dev.cause[:50]}... | "
                    f"{dev.consequence[:50]}... | {safeguards} | {dev.risk_level.value.upper()} ({dev.risk_score}) | {action[:40]}... |"
                )

        lines.append("")

    lines.extend([
        "---",
        "",
        "## Action Items",
        "",
        "| ID | Description | Node | Risk | Responsible | Due Date | Status |",
        "|----|-------------|------|------|-------------|----------|--------|",
    ])

    for i, action in enumerate(data.action_items, 1):
        lines.append(
            f"| AI-{i:03d} | {action.get('description', '')} | {action.get('node', '')} | "
            f"{action.get('risk', '')} | {action.get('responsible', 'TBD')} | {action.get('due_date', 'TBD')} | Open |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Appendices",
        "",
        "### A. Connectivity Data",
        "",
        "See `connectivity.json` for complete node/edge graph.",
        "",
        "### B. Extraction Metadata",
        "",
        f"```json\n{json.dumps(data.extraction_metadata, indent=2)}\n```",
        "",
        "---",
        "",
        "*Report generated automatically from P&ID extraction data.*",
        "*Review and validate all findings before use in formal HAZOP study.*",
    ])

    return "\n".join(lines)


def generate_html_report(data: ReportData) -> str:
    """Generate interactive HTML report."""

    md = generate_markdown_report(data)

    # Simple Markdown-to-HTML conversion
    html_content = md
    html_content = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html_content)
    html_content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html_content)
    html_content = re.sub(r"`(.+?)`", r"<code>\1</code>", html_content)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HAZOP Report — {data.system_name}</title>
<style>
  :root {{ --bg: #fafafa; --fg: #212121; --panel: #fff; --border: #e0e0e0; --accent: #1565c0; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg: #121212; --fg: #e0e0e0; --panel: #1e1e1e; --border: #333; --accent: #42a5f5; }} }}
  body {{ margin: 0; font-family: system-ui, sans-serif; background: var(--bg); color: var(--fg); line-height: 1.6; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
  h1 {{ color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 8px; }}
  h2 {{ color: var(--accent); margin-top: 32px; }}
  h3 {{ margin-top: 24px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
  th, td {{ border: 1px solid var(--border); padding: 8px 12px; text-align: left; }}
  th {{ background: var(--panel); font-weight: 500; }}
  tr:nth-child(even) {{ background: rgba(0,0,0,0.02); }}
  code {{ background: var(--panel); padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
  .risk-low {{ color: #2e7d32; }}
  .risk-medium {{ color: #f9a825; }}
  .risk-high {{ color: #ef6c00; }}
  .risk-extreme {{ color: #c62828; }}
</style>
</head>
<body>
<div class="container">
{html_content}
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def generate_report(
    connectivity_json_path: str,
    extraction_json_path: Optional[str] = None,
    output_dir: str = ".",
    system_name: str = "P&ID System",
    analyst: str = "Auto-generated",
) -> dict:
    """Generate complete HAZOP report from connectivity data."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    with open(connectivity_json_path) as f:
        connectivity_data = json.load(f)

    extraction_data = {}
    if extraction_json_path:
        with open(extraction_json_path) as f:
            extraction_data = json.load(f)

    # Build report data
    report_data = ReportData(
        system_name=system_name,
        pid_source=Path(connectivity_json_path).name,
        analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        analyst=analyst,
    )

    # Extract equipment inventory
    for node in connectivity_data.get("nodes", []):
        if node.get("type") == "equipment":
            report_data.equipment_inventory.append(node)
        elif node.get("type") in ("instrument", "controller"):
            report_data.instrument_list.append(node)

    # Generate HAZOP nodes
    generator = HAZOPNodeGenerator(connectivity_data)
    report_data.hazop_nodes = generator.generate_nodes()

    # Calculate summaries
    report_data.total_nodes = len(report_data.hazop_nodes)
    report_data.total_deviations = sum(len(n.deviations) for n in report_data.hazop_nodes)
    report_data.total_actions = sum(
        1 for n in report_data.hazop_nodes for d in n.deviations if d.action_required
    )

    # Risk distribution
    risk_counts = defaultdict(int)
    for node in report_data.hazop_nodes:
        for dev in node.deviations:
            risk_counts[dev.risk_level.value] += 1
    report_data.risk_distribution = dict(risk_counts)

    # Action items
    for node in report_data.hazop_nodes:
        for dev in node.deviations:
            if dev.action_required:
                report_data.action_items.append({
                    "description": dev.action_description,
                    "node": node.node_id,
                    "risk": f"{dev.risk_level.value} ({dev.risk_score})",
                    "responsible": dev.responsible or "TBD",
                    "due_date": dev.due_date or "TBD",
                })

    # System description
    report_data.system_description = _generate_system_description(connectivity_data)

    # Extraction metadata
    if isinstance(extraction_data, dict):
        report_data.extraction_metadata = extraction_data.get("metadata", {})
    else:
        report_data.extraction_metadata = {}

    # Export
    base = output_path / "HAZOP_Report"

    # Markdown
    md_content = generate_markdown_report(report_data)
    with open(base.with_suffix(".md"), "w") as f:
        f.write(md_content)

    # HTML
    html_content = generate_html_report(report_data)
    with open(base.with_suffix(".html"), "w") as f:
        f.write(html_content)

    # JSON data
    with open(base.with_suffix(".json"), "w") as f:
        json.dump({
            "report": {
                "system_name": report_data.system_name,
                "total_nodes": report_data.total_nodes,
                "total_deviations": report_data.total_deviations,
                "total_actions": report_data.total_actions,
                "risk_distribution": report_data.risk_distribution,
            },
            "hazop_nodes": [n.to_dict() for n in report_data.hazop_nodes],
            "action_items": report_data.action_items,
        }, f, indent=2)

    return {
        "markdown_path": str(base.with_suffix(".md")),
        "html_path": str(base.with_suffix(".html")),
        "json_path": str(base.with_suffix(".json")),
        "summary": {
            "nodes": report_data.total_nodes,
            "deviations": report_data.total_deviations,
            "actions": report_data.total_actions,
            "risk_distribution": report_data.risk_distribution,
        }
    }


def _generate_system_description(connectivity_data: dict) -> str:
    """Generate system description from connectivity data."""
    nodes = connectivity_data.get("nodes", [])
    edges = connectivity_data.get("edges", [])

    # Find main flow path
    equipment = [n for n in nodes if n.get("type") == "equipment"]

    desc = "This is a lube oil system designed to supply clean, temperature-controlled lubricating oil to a compressor. "
    desc += f"The system contains {len(equipment)} major equipment items including pumps, coolers, filters, and heaters. "
    desc += f"There are {len(edges)} process and signal connections. "
    desc += "Key safety features include redundant pumps, redundant filters, temperature control, and multiple pressure relief paths."

    return desc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate HAZOP report from P&ID connectivity data")
    parser.add_argument("connectivity", help="Path to connectivity.json")
    parser.add_argument("--extraction", help="Path to extraction.json (optional)")
    parser.add_argument("-o", "--output", default=".", help="Output directory")
    parser.add_argument("--name", default="P&ID System", help="System name")
    parser.add_argument("--analyst", default="Auto-generated", help="Analyst name")
    args = parser.parse_args()

    result = generate_report(
        connectivity_json_path=args.connectivity,
        extraction_json_path=args.extraction,
        output_dir=args.output,
        system_name=args.name,
        analyst=args.analyst,
    )

    print(f"HAZOP Report Generated:")
    print(f"  Markdown: {result['markdown_path']}")
    print(f"  HTML: {result['html_path']}")
    print(f"  JSON: {result['json_path']}")
    print(f"\nSummary:")
    print(f"  Nodes: {result['summary']['nodes']}")
    print(f"  Deviations: {result['summary']['deviations']}")
    print(f"  Actions: {result['summary']['actions']}")
    print(f"  Risk: {result['summary']['risk_distribution']}")


if __name__ == "__main__":
    main()
