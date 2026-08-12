"""Node graph construction from entities."""

from __future__ import annotations

import uuid

from pid_extractor.models import Entity, Node


def _node_id() -> str:
    return f"node_{uuid.uuid4().hex[:12]}"


class NodeBuilder:
    """Build process nodes from detected entities."""

    def build_nodes(self, entities: list[Entity]) -> list[Node]:
        nodes: list[Node] = []

        for entity in entities:
            if entity.type in ("annotation",) and entity.subtype in ("note", "unit", "specification"):
                continue  # Annotations are not process nodes

            node_type = self._map_entity_to_node_type(entity)
            nodes.append(Node(
                id=_node_id(),
                entity_id=entity.id,
                type=node_type,
                tag=entity.tag,
                label=entity.label,
                page=entity.page,
                bbox=entity.bbox,
                center=entity.center,
                confidence=entity.confidence,
            ))

        return nodes

    def _map_entity_to_node_type(self, entity: Entity) -> str:
        mapping = {
            "equipment": entity.subtype or "equipment",
            "instrument": entity.subtype or "instrument",
            "valve": entity.subtype or "valve",
            "line": "pipe",
            "process_object": entity.subtype or "process_object",
        }
        return mapping.get(entity.type, entity.type)

    def index_by_tag(self, nodes: list[Node]) -> dict[str, Node]:
        index: dict[str, Node] = {}
        for node in nodes:
            if node.tag:
                key = node.tag.upper()
                if key not in index:
                    index[key] = node
        return index

    def index_by_id(self, nodes: list[Node]) -> dict[str, Node]:
        return {n.id: n for n in nodes}
