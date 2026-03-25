"""Base service protocol for all long-running services."""

from __future__ import annotations

from typing import Protocol


class Service(Protocol):
    @property
    def name(self) -> str: ...

    async def start(self) -> None:
        """Initialize resources (model loading, connections, etc.)."""
        ...

    async def run(self) -> None:
        """Main loop. Called inside TaskGroup."""
        ...

    async def stop(self) -> None:
        """Cleanup resources."""
        ...
