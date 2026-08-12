"""Detection package init."""

from pid_extractor.detection.entities import EntityDetector
from pid_extractor.detection.tags import TagParser
from pid_extractor.detection.visual import VisualAnalyzer

__all__ = ["EntityDetector", "TagParser", "VisualAnalyzer"]
