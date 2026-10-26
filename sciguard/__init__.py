"""SciGuard public API. No model required. Omitted space is UNKNOWN, not FAIL."""

from validation.check import check_workflow as validate

__all__ = ["validate"]
__version__ = "0.1.0"
