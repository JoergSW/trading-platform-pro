from __future__ import annotations

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContext,
    InstrumentContextListener,
    InstrumentContextService,
    InstrumentContextState,
)


class AnalysisWorkspaceWidget(QWidget):
    """Follow and display the shared Application-owned instrument context."""

    def __init__(
        self,
        instrument_context_service: InstrumentContextService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("analysisWorkspaceWidget")
        self._instrument_context_service = instrument_context_service
        self._context_listener: InstrumentContextListener = (
            self._on_instrument_context_changed
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QGridLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setHorizontalSpacing(12)

        title = QLabel("Instrument Analysis", self)
        title.setObjectName("analysisWorkspaceTitle")
        header.addWidget(title, 0, 0)
        header.setColumnStretch(0, 1)

        self._state_label = QLabel(self)
        self._state_label.setObjectName("analysisWorkspaceState")
        header.addWidget(self._state_label, 0, 1)
        layout.addLayout(header)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(12)

        symbol_card, self._symbol_label = self._status_card(
            "Active Symbol",
            "analysisWorkspaceActiveSymbol",
        )
        cards.addWidget(symbol_card, 0, 0)

        source_card, self._source_label = self._status_card(
            "Context Source",
            "analysisWorkspaceContextSource",
        )
        cards.addWidget(source_card, 0, 1)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)
        layout.addLayout(cards)

        self._detail_label = QLabel(self)
        self._detail_label.setObjectName("analysisWorkspaceDetail")
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)
        layout.addStretch(1)

        safety_note = QLabel(
            "Read-only context view. The active instrument is supplied by an "
            "explicit compatible workspace selection. No market-data request, "
            "broker connection, order action or trading action is performed.",
            self,
        )
        safety_note.setObjectName("analysisWorkspaceSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        self._instrument_context_service.subscribe(self._context_listener)

    @property
    def instrument_context(self) -> InstrumentContext:
        return self._instrument_context_service.context

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._instrument_context_service.unsubscribe(self._context_listener)
        super().closeEvent(event)

    def _on_instrument_context_changed(self, context: InstrumentContext) -> None:
        if context.state is InstrumentContextState.SELECTED:
            self._set_state("SELECTED", "selected")
            self._symbol_label.setText(context.symbol or "NO SELECTION")
            self._source_label.setText(context.source or "NOT AVAILABLE")
            self._detail_label.setText(
                "The active instrument follows the explicit "
                f"{context.source or 'compatible workspace'} selection."
            )
            return

        self._set_state("NO SELECTION", "no_selection")
        self._symbol_label.setText("NO SELECTION")
        self._source_label.setText(context.source or "NOT AVAILABLE")
        self._detail_label.setText(
            "Select a compatible Scanner result to establish instrument context."
        )

    def _set_state(self, text: str, state: str) -> None:
        self._state_label.setText(text)
        self._state_label.setProperty("instrumentContextState", state)
        self._state_label.style().unpolish(self._state_label)
        self._state_label.style().polish(self._state_label)

    def _status_card(
        self,
        title_text: str,
        value_object_name: str,
    ) -> tuple[QFrame, QLabel]:
        card = QFrame(self)
        card.setObjectName("analysisWorkspaceCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(title_text, card)
        title.setObjectName("analysisWorkspaceCardTitle")
        layout.addWidget(title)

        value = QLabel(card)
        value.setObjectName(value_object_name)
        value.setWordWrap(True)
        layout.addWidget(value)
        layout.addStretch(1)

        return card, value
