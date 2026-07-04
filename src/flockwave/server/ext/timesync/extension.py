"""Core implementation of the `timesync` extension."""

from __future__ import annotations

from typing import Any, ContextManager, Protocol

from flockwave.server.ext.base import Extension
from flockwave.server.model.log import Severity

from .constants import (
    DEFAULT_OFFSET_LOG_THRESHOLD,
    DEFAULT_SOURCE_EXPIRY_THRESHOLD,
    DEFAULT_SYNC_THRESHOLD,
)
from .manager import TimeSource, TimeSyncManager
from .model import TimeSyncSnapshot
from .types import TimeSyncState

__all__ = (
    "TimeSource",
    "TimeSyncExtension",
    "TimeSyncExtensionAPI",
    "TimeSyncSnapshot",
    "TimeSyncState",
)


class TimeSyncExtension(Extension):
    """Extension that tracks server wall-clock synchronization status."""

    _manager: TimeSyncManager
    """Manager instance that stores the source state and computes snapshots."""

    def __init__(self):
        """Constructor."""
        super().__init__()
        self._manager = TimeSyncManager()

    def configure(self, configuration: dict[str, Any]) -> None:
        """Updates the extension configuration from the extension settings."""
        super().configure(configuration)
        self._manager.configure(
            sync_threshold=float(
                configuration.get("sync_threshold", DEFAULT_SYNC_THRESHOLD)
            ),
            source_expiry_threshold=float(
                configuration.get(
                    "source_expiry_threshold", DEFAULT_SOURCE_EXPIRY_THRESHOLD
                )
            ),
            offset_log_threshold=float(
                configuration.get("offset_log_threshold", DEFAULT_OFFSET_LOG_THRESHOLD)
            ),
            log=self.log,
        )

    def exports(self) -> dict[str, Any]:
        """Returns the API exposed by the extension to other extensions."""
        return {
            "get_status": self.get_status,
            "use_time_source": self.use_time_source,
        }

    def get_status(self) -> TimeSyncSnapshot:
        """Returns the current synchronization status snapshot."""
        return self._manager.get_status()

    def use_time_source(
        self, id: str, *, priority: int = 0
    ) -> ContextManager[TimeSource]:
        """Registers a time source for the duration of a context."""
        return self._manager.use_time_source(id, priority=priority)

    async def run(self) -> None:
        with self._manager.sync_status_changed.connected_to(
            self._maybe_send_status_change_message, sender=self._manager
        ):
            await self._manager.run()

    def _maybe_send_status_change_message(
        self, sender, current: TimeSyncSnapshot, previous: TimeSyncSnapshot
    ) -> None:
        # TODO(ntamas): also do this when a new client connects

        if not self.app:
            return

        if current.state == previous.state:
            return

        if current.state == "sync" and previous.state == "unknown":
            # Don't send a message when the server starts up and the first time source
            # reports a valid timestamp, because that is expected behavior.
            return

        send_message = self.app.request_to_send_SYS_MSG_message
        match current.state:
            case "sync":
                send_message("World clock and server clock are now in sync.")

            case "unsync":
                send_message(
                    "Server clock is not synchronized to world clock. Please sync "
                    "the date and time on the server to a reliable time source.",
                    severity=Severity.WARNING,
                )

            case "error":
                send_message(
                    "Cannot determine server clock synchronization state: all reporting "
                    "time sources indicated errors.",
                    severity=Severity.WARNING,
                )


class TimeSyncExtensionAPI(Protocol):
    """Interface specification for the API exposed by the `timesync` extension."""

    def get_status(self) -> TimeSyncSnapshot: ...
    def use_time_source(
        self, id: str, *, priority: int = 0
    ) -> ContextManager[TimeSource]: ...
