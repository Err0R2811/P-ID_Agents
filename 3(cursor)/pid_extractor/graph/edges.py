"""Edge/connection detection between process nodes."""

from __future__ import annotations

import re
import uuid

from pid_extractor.config import LOW_CONFIDENCE, MEDIUM_CONFIDENCE, PipelineConfig
from pid_extractor.graph.spatial import SpatialRelation, SpatialReasoner
from pid_extractor.models import Edge, Entity, LineSegment, Node


def _edge_id() -> str:
    return f"edge_{uuid.uuid4().hex[:12]}"


class EdgeBuilder:
    """Detect connections and relationships between nodes."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self.spatial = SpatialReasoner(config)

    def build_edges_from_spatial(
        self,
        relations: list[SpatialRelation],
        nodes: list[Node],
        node_entity_map: dict[str, str],
    ) -> list[Edge]:
        """Create edges from spatial relations (low confidence)."""
        edges: list[Edge] = []
        node_by_entity = {n.entity_id: n for n in nodes if n.entity_id}

        for rel in relations:
            node_a = node_by_entity.get(rel.entity_a_id)
            node_b = node_by_entity.get(rel.entity_b_id)
            if not node_a or not node_b:
                continue

            relationship = self._infer_relationship(node_a, node_b, rel)
            status = "uncertain" if rel.confidence < 0.5 else "detected"

            edges.append(Edge(
                id=_edge_id(),
                source=node_a.id,
                target=node_b.id,
                relationship=relationship,
                line_tag=None,
                direction=None,
                page=node_a.page,
                confidence=rel.confidence,
                status=status,
                evidence=rel.evidence,
            ))

        return edges

    def build_control_loop_edges(
        self,
        entities: list[Entity],
        nodes: list[Node],
    ) -> list[Edge]:
        """Detect instrument control relationships (e.g., FIC controls FCV)."""
        edges: list[Edge] = []
        node_by_tag = {n.tag.upper(): n for n in nodes if n.tag}

        controllers = [e for e in entities if e.subtype == "controller"]
        control_valves = [e for e in entities if e.subtype and "control" in e.subtype]

        for controller in controllers:
            if not controller.tag:
                continue
            # Extract loop number from tag (e.g., FIC-101 -> 101)
            match = re.search(r"-(\d+)", controller.tag)
            if not match:
                continue
            loop_num = match.group(1)
            prefix = controller.tag[:1]  # F, L, P, T

            valve_map = {"F": "FCV", "L": "LCV", "P": "PCV", "T": "TCV"}
            expected_valve_prefix = valve_map.get(prefix)
            if not expected_valve_prefix:
                continue

            valve_tag = f"{expected_valve_prefix}-{loop_num}"
            controller_node = node_by_tag.get(controller.tag.upper())
            valve_node = node_by_tag.get(valve_tag)

            if controller_node and valve_node:
                edges.append(Edge(
                    id=_edge_id(),
                    source=controller_node.id,
                    target=valve_node.id,
                    relationship="controlled_by",
                    line_tag=None,
                    direction=None,
                    page=controller.page,
                    confidence=MEDIUM_CONFIDENCE,
                    status="detected",
                    evidence=["naming_convention", "control_loop_pattern"],
                ))

            # Transmitter -> Controller (measured_by)
            transmitter_prefix = prefix + "T"
            transmitter_tag = f"{transmitter_prefix}-{loop_num}"
            transmitter_node = node_by_tag.get(transmitter_tag)
            if transmitter_node and controller_node:
                edges.append(Edge(
                    id=_edge_id(),
                    source=transmitter_node.id,
                    target=controller_node.id,
                    relationship="measured_by",
                    line_tag=None,
                    direction=None,
                    page=controller.page,
                    confidence=MEDIUM_CONFIDENCE,
                    status="detected",
                    evidence=["naming_convention", "instrument_loop"],
                ))

        return edges

    def build_line_connections(
        self,
        line_entities: list[Entity],
        equipment_nodes: list[Node],
        line_segments: list[LineSegment],
    ) -> list[Edge]:
        """Connect equipment nodes via shared line tags or proximity to line segments."""
        edges: list[Edge] = []
        line_nodes = [n for n in equipment_nodes if n.type == "pipe"]

        # Connect entities sharing the same line tag
        line_tag_groups: dict[str, list[Node]] = {}
        for node in equipment_nodes:
            if node.tag and node.type == "pipe":
                line_tag_groups.setdefault(node.tag.upper(), []).append(node)

        for tag, group in line_tag_groups.items():
            for i, a in enumerate(group):
                for b in group[i + 1:]:
                    edges.append(Edge(
                        id=_edge_id(),
                        source=a.id,
                        target=b.id,
                        relationship="connected_to",
                        line_tag=tag,
                        direction=None,
                        page=a.page,
                        confidence=MEDIUM_CONFIDENCE,
                        status="detected",
                        evidence=["shared_line_tag"],
                    ))

        return edges

    def build_cross_page_links(
        self,
        all_nodes: list[Node],
        all_entities: list[Entity],
    ) -> list[Edge]:
        """Link entities across pages via matching tags."""
        edges: list[Edge] = []
        tag_pages: dict[str, list[Node]] = {}

        for node in all_nodes:
            if node.tag:
                tag_pages.setdefault(node.tag.upper(), []).append(node)

        for tag, nodes in tag_pages.items():
            if len(nodes) < 2:
                continue
            pages = set(n.page for n in nodes)
            if len(pages) < 2:
                continue

            for i, a in enumerate(nodes):
                for b in nodes[i + 1:]:
                    if a.page != b.page:
                        edges.append(Edge(
                            id=_edge_id(),
                            source=a.id,
                            target=b.id,
                            relationship="continues_on_page",
                            line_tag=tag if a.type == "pipe" else None,
                            direction=None,
                            page=None,
                            confidence=MEDIUM_CONFIDENCE,
                            status="detected",
                            evidence=["cross_page_tag_match"],
                        ))

        return edges

    def _infer_relationship(
        self,
        node_a: Node,
        node_b: Node,
        rel: SpatialRelation,
    ) -> str:
        if rel.relation_type == "tag_symbol_association":
            return "labeled_as"
        if node_a.type in ("controller",) or node_b.type in ("control_valve",):
            return "controlled_by"
        if node_a.type == "pipe" or node_b.type == "pipe":
            return "connected_to"
        return "nearby"
