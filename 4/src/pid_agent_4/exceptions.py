"""Custom exceptions for the P&ID agent."""


class PIDAgentError(Exception):
    """Base exception for P&ID agent errors."""


class InvalidPDFError(PIDAgentError):
    """Raised when the PDF cannot be processed (e.g. scanned/raster)."""


class SplitError(PIDAgentError):
    """Raised when a split operation fails."""


class LLMCallError(PIDAgentError):
    """Raised when an LLM call fails after retries."""
