"""Main P&ID extraction pipeline orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from pid_extractor.config import PipelineConfig
from pid_extractor.detection.entities import EntityDetector
from pid_extractor.detection.visual import VisualAnalyzer
from pid_extractor.llm.analyzer import PIDLLMAnalyzer
from pid_extractor.graph.edges import EdgeBuilder
from pid_extractor.graph.nodes import NodeBuilder
from pid_extractor.graph.spatial import SpatialReasoner
from pid_extractor.models import ExtractionResult, PageResult
from pid_extractor.output.formatter import OutputFormatter
from pid_extractor.pdf.extractor import PDFExtractor
from pid_extractor.pdf.renderer import PageRenderer
from pid_extractor.pdf.search import PIDTextSearch
from pid_extractor.validation.validator import ResultValidator


class PIDProcessor:
    """End-to-end P&ID PDF extraction pipeline.

    Pipeline stages:
    PDF → PyMuPDF → Page Extraction → Word Extraction → Block/Line/Span
    → Text Search → Page Rendering → Visual Analysis → Entity Detection
    → Text↔Symbol Association → Node Detection → Connection Detection
    → Spatial Reasoning → Cross-Page Linking → Confidence Scoring
    → Validation → Structured JSON
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self.detector = EntityDetector(self.config)
        self.visual = VisualAnalyzer(self.config)
        self.node_builder = NodeBuilder()
        self.edge_builder = EdgeBuilder(self.config)
        self.spatial = SpatialReasoner(self.config)
        self.validator = ResultValidator()
        self.formatter = OutputFormatter()
        self.llm_analyzer = PIDLLMAnalyzer(self.config) if self.config.llm_active else None

    def process(self, pdf_path: str | Path) -> ExtractionResult:
        pdf_path = Path(pdf_path)
        extractor = PDFExtractor(pdf_path)

        try:
            renderer = PageRenderer(
                extractor.doc,
                output_dir=Path(self.config.output_dir) / "rendered",
                dpi=self.config.dpi,
                cache=self.config.cache_pages,
            )
            searcher = PIDTextSearch(extractor)

            pages: list[PageResult] = []
            all_entities = []
            all_nodes = []

            for page_index in range(extractor.page_count):
                page_number = page_index + 1
                if not self.config.page_filter(page_number):
                    continue

                page_result = self._process_page(
                    extractor, renderer, searcher, page_index
                )
                pages.append(page_result)
                all_entities.extend(page_result.entities)
                all_nodes.extend(page_result.nodes)

            # Global deduplication
            global_entities = self.detector.deduplicate(all_entities)

            # Cross-page linking
            global_connections = self.edge_builder.build_cross_page_links(
                all_nodes, global_entities
            )

            result = ExtractionResult(
                document={
                    "filename": extractor.filename,
                    "page_count": extractor.page_count,
                    "pages_processed": len(pages),
                    "dpi": self.config.dpi,
                    "llm_enabled": self.config.llm_active,
                    "llm_model": self.config.llm.model if self.config.llm_active else None,
                },
                pages=pages,
                global_entities=global_entities,
                global_connections=global_connections,
            )

            # Validation
            result.validation = self.validator.validate(result)
            result.uncertain_items = self.validator.collect_uncertain_items(result)

            return result

        finally:
            extractor.close()

    def _process_page(
        self,
        extractor: PDFExtractor,
        renderer: PageRenderer,
        searcher: PIDTextSearch,
        page_index: int,
    ) -> PageResult:
        page_number = page_index + 1
        width, height = extractor.get_page_size(page_index)

        # Stage 1: Text extraction
        words = extractor.extract_words(page_index)
        blocks = extractor.extract_layout(page_index)
        has_text = len(words) > 0

        # Stage 2: Text search
        search_hits = searcher.search_page(page_index)

        # Stage 3: Entity detection from text
        entities = self.detector.detect_from_words(words, page_number)
        existing_tags = {e.tag for e in entities if e.tag}
        entities.extend(
            self.detector.detect_from_search_hits(search_hits, existing_tags, page_number)
        )
        entities = self.detector.deduplicate(entities)

        # Stage 4: Visual analysis
        lines = []
        annotations = []
        rendered_path = None

        if self.config.enable_visual:
            rendered_path, _ = renderer.render_page(page_index)

        if self.config.enable_drawings:
            drawing_paths = extractor.extract_drawing_paths(page_index)
            drawings = extractor.extract_drawings(page_index)

            lines = self.visual.extract_line_segments(drawing_paths, page_number)
            arrows = self.visual.detect_arrow_candidates(drawing_paths, page_number)
            annotations.extend(arrows)

            visual_entities = self.visual.build_visual_entities_from_drawings(
                drawings, page_number
            )
            entities = self.visual.associate_tags_with_symbols(
                entities, lines, page_number
            )
            entities.extend(visual_entities)

        # Stage 5: LLM vision analysis (external API — not Cursor agent)
        llm_result: dict = {}
        if self.llm_analyzer and rendered_path:
            try:
                llm_result = self.llm_analyzer.analyze_page(
                    rendered_path,
                    page_number,
                    width,
                    height,
                    words,
                    entities,
                    search_hits,
                )
                entities = self.llm_analyzer.merge_entities(
                    entities, llm_result, page_number, width, height
                )
                entities = self.detector.deduplicate(entities)
                if llm_result.get("notes"):
                    annotations.extend(
                        {"type": "llm_note", "page": page_number, "text": n}
                        for n in llm_result["notes"]
                    )
            except Exception as exc:
                annotations.append({
                    "type": "llm_error",
                    "page": page_number,
                    "text": str(exc),
                    "status": "uncertain",
                })

        # Stage 6: Node building
        nodes = self.node_builder.build_nodes(entities)

        # Stage 7: Spatial reasoning
        spatial_relations = self.spatial.find_proximity_pairs(entities)
        visual_entities = [e for e in entities if "visual" in e.source]
        spatial_relations.extend(
            self.spatial.find_tag_symbol_associations(entities, visual_entities)
        )

        # Stage 8: Edge building
        edges = self.edge_builder.build_edges_from_spatial(spatial_relations, nodes, {})
        edges.extend(self.edge_builder.build_control_loop_edges(entities, nodes))
        line_entities = [e for e in entities if e.type == "line"]
        edges.extend(
            self.edge_builder.build_line_connections(line_entities, nodes, lines)
        )
        if self.llm_analyzer and llm_result:
            edges.extend(
                self.llm_analyzer.build_edges_from_llm(llm_result, nodes, page_number)
            )

        return PageResult(
            page_number=page_number,
            width=width,
            height=height,
            words=words,
            blocks=blocks,
            entities=entities,
            nodes=nodes,
            edges=edges,
            lines=lines,
            annotations=annotations,
            rendered_path=rendered_path,
            has_text_layer=has_text,
        )

    def extract_and_save(
        self,
        pdf_path: str | Path,
        output_path: str | Path | None = None,
        mode: str = "STRUCTURED",
    ) -> ExtractionResult:
        result = self.process(pdf_path)

        if output_path:
            self.formatter.save(result, output_path, mode)
        else:
            default_path = Path(self.config.output_dir) / f"{Path(pdf_path).stem}.json"
            self.formatter.save(result, default_path, mode)

        return result
