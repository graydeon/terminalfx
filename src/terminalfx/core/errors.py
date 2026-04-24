from __future__ import annotations


class TerminalFxError(Exception):
    """Base exception for expected terminalfx failures."""


class ConfigError(TerminalFxError):
    """Raised when configuration cannot be parsed or validated."""


class SourceError(TerminalFxError):
    """Raised when a frame source cannot open or read frames."""


class EffectError(TerminalFxError):
    """Raised when an effect cannot be created or applied."""


class RenderError(TerminalFxError):
    """Raised when an export or render job fails."""
