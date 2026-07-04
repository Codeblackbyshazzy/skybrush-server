"""Extension that tracks whether the local server clock is synchronized to
real-world wall clock time based on timestamps reported by other extensions.
"""

from .extension import (
    TimeSource,
    TimeSyncExtension,
    TimeSyncExtensionAPI,
    TimeSyncManager,
    TimeSyncSnapshot,
    TimeSyncState,
)
from .schema import schema

__all__ = (
    "TimeSource",
    "TimeSyncExtensionAPI",
    "TimeSyncManager",
    "TimeSyncSnapshot",
    "TimeSyncState",
    "construct",
    "description",
    "schema",
)

construct = TimeSyncExtension
description = "Wall clock synchronization state tracker for other extensions"
