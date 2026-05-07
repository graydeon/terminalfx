"""Custom Textual widgets for the terminalfx TUI."""

from textual.widgets import Static


class TextPanel(Static):
    """A read-only text panel that supports external set() updates."""

    def __init__(
        self,
        content: str = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            content,
            expand=expand,
            shrink=shrink,
            markup=False,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

    def set(self, value: str) -> None:
        self.update(value)
