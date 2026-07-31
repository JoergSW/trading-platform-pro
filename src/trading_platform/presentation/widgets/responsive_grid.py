from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QResizeEvent, QShowEvent
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget


class ResponsiveGridWidget(QWidget):
    """Reflow child widgets into a bounded number of readable columns."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        min_column_width: int = 280,
        max_columns: int = 2,
        spacing: int = 12,
    ) -> None:
        super().__init__(parent)
        if min_column_width <= 0:
            raise ValueError("min_column_width must be positive")
        if max_columns <= 0:
            raise ValueError("max_columns must be positive")
        if spacing < 0:
            raise ValueError("spacing must be non-negative")

        self._min_column_width = min_column_width
        self._max_columns = max_columns
        self._spacing = spacing
        self._widgets: list[QWidget] = []
        self._column_count = 1

        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(spacing)
        self._grid.setVerticalSpacing(spacing)
        self.setProperty("responsiveColumns", self._column_count)

    @property
    def column_count(self) -> int:
        return self._column_count

    def add_widget(self, widget: QWidget) -> None:
        if not isinstance(widget, QWidget):
            raise TypeError("widget must be QWidget")
        widget.setParent(self)
        widget.setMinimumWidth(0)
        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._widgets.append(widget)
        self._reflow(self.width())

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        hint = super().minimumSizeHint()
        return QSize(0, hint.height())

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return self._grid.hasHeightForWidth()

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        return self._grid.heightForWidth(width)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        self._reflow(event.size().width())
        super().resizeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        self._reflow(self.width())
        super().showEvent(event)

    def _reflow(self, available_width: int) -> None:
        columns = self._desired_columns(available_width)
        if columns == self._column_count and self._grid.count() == len(self._widgets):
            return

        for widget in self._widgets:
            self._grid.removeWidget(widget)
        for column in range(self._max_columns):
            self._grid.setColumnStretch(column, 0)
            self._grid.setColumnMinimumWidth(column, 0)

        for index, widget in enumerate(self._widgets):
            self._grid.addWidget(widget, index // columns, index % columns)
        for column in range(columns):
            self._grid.setColumnStretch(column, 1)

        self._column_count = columns
        self.setProperty("responsiveColumns", columns)
        self._grid.invalidate()
        self.updateGeometry()

    def _desired_columns(self, available_width: int) -> int:
        width = max(0, available_width)
        columns = (width + self._spacing) // (self._min_column_width + self._spacing)
        return min(self._max_columns, max(1, columns))
