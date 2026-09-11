# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

from abc import ABC, abstractmethod

from .events import AuditEvent


class AbstractSink(ABC):
    """Interface all audit sinks must implement."""

    @abstractmethod
    def write(self, event: AuditEvent) -> None: ...


class NullSink(AbstractSink):
    """Default sink — discards all events."""

    def write(self, event: AuditEvent) -> None:
        pass
