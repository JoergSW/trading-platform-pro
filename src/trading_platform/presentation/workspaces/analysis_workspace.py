from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContext,
    InstrumentContextListener,
    InstrumentContextService,
    InstrumentContextState,
)
from trading_platform.application.market_data.price_history import (
    DEFAULT_PRICE_HISTORY_TIMEFRAME,
    PriceHistory,
    PriceHistoryService,
    PriceHistoryState,
)
from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateAddResult,
    TradingCandidateService,
)
from trading_platform.presentation.widgets.price_chart import PriceChartWidget


class AnalysisWorkspaceWidget(QWidget):
    """Follow shared instrument context and render read-only historical prices."""

    def __init__(
        self,
        instrument_context_service: InstrumentContextService,
        parent: QWidget | None = None,
        *,
        price_history_service: PriceHistoryService | None = None,
        trading_candidate_service: TradingCandidateService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("analysisWorkspaceWidget")
        self._instrument_context_service = instrument_context_service
        self._price_history_service = price_history_service
        self._trading_candidate_service = trading_candidate_service
        self._price_history: PriceHistory | None = None
        self._load_generation = 0
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

        candidate_actions = QHBoxLayout()
        candidate_actions.setContentsMargins(0, 0, 0, 0)
        candidate_actions.setSpacing(10)

        self._add_candidate_button = QPushButton("Add to Decision Center", self)
        self._add_candidate_button.setObjectName(
            "analysisWorkspaceAddToDecisionCenterButton"
        )
        self._add_candidate_button.clicked.connect(self.add_to_decision_center)
        candidate_actions.addWidget(self._add_candidate_button)

        self._candidate_intake_status = QLabel(self)
        self._candidate_intake_status.setObjectName(
            "analysisWorkspaceCandidateIntakeStatus"
        )
        candidate_actions.addWidget(self._candidate_intake_status)
        candidate_actions.addStretch(1)
        layout.addLayout(candidate_actions)

        price_panel = QFrame(self)
        price_panel.setObjectName("analysisPriceHistoryPanel")
        price_layout = QVBoxLayout(price_panel)
        price_layout.setContentsMargins(14, 12, 14, 14)
        price_layout.setSpacing(10)

        price_header = QHBoxLayout()
        price_header.setContentsMargins(0, 0, 0, 0)
        price_header.setSpacing(10)

        price_title = QLabel("Price History", price_panel)
        price_title.setObjectName("analysisPriceHistoryTitle")
        price_header.addWidget(price_title)
        price_header.addStretch(1)

        self._refresh_button = QPushButton("Refresh", price_panel)
        self._refresh_button.setObjectName("analysisPriceHistoryRefreshButton")
        self._refresh_button.clicked.connect(self.refresh_price_history)
        price_header.addWidget(self._refresh_button)

        self._price_state_label = QLabel(price_panel)
        self._price_state_label.setObjectName("analysisPriceHistoryState")
        price_header.addWidget(self._price_state_label)
        price_layout.addLayout(price_header)

        metadata = QGridLayout()
        metadata.setContentsMargins(0, 0, 0, 0)
        metadata.setHorizontalSpacing(12)
        metadata.setVerticalSpacing(6)

        self._price_source_label = self._metadata_value(
            metadata,
            0,
            0,
            "Data Source",
            "analysisPriceHistorySource",
        )
        self._timeframe_label = self._metadata_value(
            metadata,
            0,
            1,
            "Timeframe",
            "analysisPriceHistoryTimeframe",
        )
        self._bar_count_label = self._metadata_value(
            metadata,
            1,
            0,
            "Bars",
            "analysisPriceHistoryBarCount",
        )
        self._period_label = self._metadata_value(
            metadata,
            1,
            1,
            "Period UTC",
            "analysisPriceHistoryPeriod",
        )
        metadata.setColumnStretch(0, 1)
        metadata.setColumnStretch(1, 1)
        price_layout.addLayout(metadata)

        self._price_detail_label = QLabel(price_panel)
        self._price_detail_label.setObjectName("analysisPriceHistoryDetail")
        self._price_detail_label.setWordWrap(True)
        price_layout.addWidget(self._price_detail_label)

        self._price_chart = PriceChartWidget(price_panel)
        price_layout.addWidget(self._price_chart, 1)
        layout.addWidget(price_panel, 1)

        safety_note = QLabel(
            "Read-only analysis view. Historical OHLCV data is loaded only from "
            "an explicitly configured local source. No broker connection, Trading "
            "Decision, order action, trading action or LIVE "
            "action is performed. Candidate intake writes only to an explicitly "
            "configured local database.",
            self,
        )
        safety_note.setObjectName("analysisWorkspaceSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        self._instrument_context_service.subscribe(self._context_listener)

    @property
    def instrument_context(self) -> InstrumentContext:
        return self._instrument_context_service.context

    @property
    def price_history(self) -> PriceHistory | None:
        return self._price_history

    def refresh_price_history(self) -> None:
        context = self._instrument_context_service.context
        if (
            context.state is not InstrumentContextState.SELECTED
            or context.symbol is None
        ):
            return
        self._request_price_history(context.symbol)

    def add_to_decision_center(self) -> None:
        context = self._instrument_context_service.context
        if (
            self._trading_candidate_service is None
            or context.state is not InstrumentContextState.SELECTED
            or context.symbol is None
            or context.source not in {"Scanner", "Watchlist"}
        ):
            self._update_candidate_intake_state(context)
            return

        outcome = self._trading_candidate_service.add_candidate(
            context.symbol,
            context.source,
        )
        if outcome.result is TradingCandidateAddResult.ADDED:
            self._set_candidate_intake_state("ADDED", "success")
            self._add_candidate_button.setEnabled(False)
        elif outcome.result is TradingCandidateAddResult.ALREADY_EXISTS:
            self._set_candidate_intake_state("ALREADY EXISTS", "unchanged")
            self._add_candidate_button.setEnabled(False)
        else:
            self._set_candidate_intake_state("ERROR", "error")
            self._add_candidate_button.setEnabled(True)
        self._candidate_intake_status.setToolTip(outcome.detail)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._load_generation += 1
        self._instrument_context_service.unsubscribe(self._context_listener)
        super().closeEvent(event)

    def _on_instrument_context_changed(self, context: InstrumentContext) -> None:
        if context.state is InstrumentContextState.SELECTED:
            self._set_context_state("SELECTED", "selected")
            self._symbol_label.setText(context.symbol or "NO SELECTION")
            self._source_label.setText(context.source or "NOT AVAILABLE")
            self._detail_label.setText(
                "The active instrument follows the explicit "
                f"{context.source or 'compatible workspace'} selection."
            )
            self._update_candidate_intake_state(context)
            assert context.symbol is not None
            self._request_price_history(context.symbol)
            return

        self._load_generation += 1
        self._set_context_state("NO SELECTION", "no_selection")
        self._symbol_label.setText("NO SELECTION")
        self._source_label.setText(context.source or "NOT AVAILABLE")
        self._detail_label.setText(
            "Select a compatible Scanner result or Watchlist Symbol to establish "
            "instrument context."
        )
        self._price_history = None
        self._price_chart.set_history(None)
        self._set_price_state("NO SELECTION", "no_selection")
        self._set_price_metadata(
            source="NOT AVAILABLE",
            timeframe="NOT AVAILABLE",
            bar_count="0",
            period="NOT AVAILABLE",
        )
        self._price_detail_label.setText(
            "Select an instrument before historical price data can be loaded."
        )
        self._refresh_button.setEnabled(False)
        self._update_candidate_intake_state(context)

    def _request_price_history(self, symbol: str) -> None:
        self._load_generation += 1
        generation = self._load_generation
        self._price_history = None
        self._price_chart.set_history(None)
        self._set_price_state("LOADING", "loading")
        self._set_price_metadata(
            source="LOADING",
            timeframe=DEFAULT_PRICE_HISTORY_TIMEFRAME,
            bar_count="0",
            period="LOADING",
        )
        self._price_detail_label.setText(
            f"Loading validated historical price data for {symbol}."
        )
        self._refresh_button.setEnabled(False)

        if self._price_history_service is None:
            self._apply_price_history(
                PriceHistory.unavailable(symbol),
                generation,
            )
            return

        QTimer.singleShot(
            0,
            lambda: self._load_price_history(symbol, generation),
        )

    def _load_price_history(self, symbol: str, generation: int) -> None:
        if not self._is_current_request(symbol, generation):
            return
        assert self._price_history_service is not None

        try:
            history = self._price_history_service.load_history(symbol)
        except Exception as exc:  # defensive Application-boundary translation
            history = PriceHistory.error(
                symbol,
                detail=(
                    "Historical price loading failed at the Application boundary: "
                    f"{type(exc).__name__}."
                ),
            )
        self._apply_price_history(history, generation)

    def _apply_price_history(
        self,
        history: PriceHistory,
        generation: int,
    ) -> None:
        if not self._is_current_request(history.symbol, generation):
            return

        self._price_history = history
        self._refresh_button.setEnabled(self._price_history_service is not None)
        self._price_source_label.setText(history.source_name or "NOT AVAILABLE")
        self._timeframe_label.setText(history.timeframe)
        self._price_detail_label.setText(history.detail)

        if history.state is PriceHistoryState.READY:
            self._set_price_state("READY", "ready")
            self._bar_count_label.setText(str(len(history.bars)))
            self._period_label.setText(
                f"{_format_utc_date(history.bars[0].observed_at)} → "
                f"{_format_utc_date(history.bars[-1].observed_at)}"
            )
            self._price_chart.set_history(history)
            return

        self._price_chart.set_history(None)
        self._bar_count_label.setText("0")
        self._period_label.setText("NOT AVAILABLE")
        if history.state is PriceHistoryState.NO_DATA:
            self._set_price_state("NO DATA", "no_data")
        elif history.state is PriceHistoryState.ERROR:
            self._set_price_state("ERROR", "error")
        else:
            self._set_price_state("UNAVAILABLE", "unavailable")

    def _is_current_request(self, symbol: str, generation: int) -> bool:
        context = self._instrument_context_service.context
        return (
            generation == self._load_generation
            and context.state is InstrumentContextState.SELECTED
            and context.symbol == symbol
        )

    def _set_context_state(self, text: str, state: str) -> None:
        self._state_label.setText(text)
        self._state_label.setProperty("instrumentContextState", state)
        self._repolish(self._state_label)

    def _set_price_state(self, text: str, state: str) -> None:
        self._price_state_label.setText(text)
        self._price_state_label.setProperty("priceHistoryState", state)
        self._repolish(self._price_state_label)

    def _update_candidate_intake_state(self, context: InstrumentContext) -> None:
        self._candidate_intake_status.setToolTip("")
        if context.state is not InstrumentContextState.SELECTED:
            self._add_candidate_button.setEnabled(False)
            self._set_candidate_intake_state("NO SELECTION", "unavailable")
            return
        if self._trading_candidate_service is None:
            self._add_candidate_button.setEnabled(False)
            self._set_candidate_intake_state("UNAVAILABLE", "unavailable")
            return
        if context.source == "Decision Center":
            self._add_candidate_button.setEnabled(False)
            self._set_candidate_intake_state("ALREADY EXISTS", "unchanged")
            return
        if context.source not in {"Scanner", "Watchlist"}:
            self._add_candidate_button.setEnabled(False)
            self._set_candidate_intake_state("NOT AVAILABLE", "unavailable")
            return

        self._add_candidate_button.setEnabled(True)
        self._set_candidate_intake_state("READY", "ready")

    def _set_candidate_intake_state(self, text: str, state: str) -> None:
        self._candidate_intake_status.setText(text)
        self._candidate_intake_status.setProperty("candidateIntakeState", state)
        self._repolish(self._candidate_intake_status)

    def _set_price_metadata(
        self,
        *,
        source: str,
        timeframe: str,
        bar_count: str,
        period: str,
    ) -> None:
        self._price_source_label.setText(source)
        self._timeframe_label.setText(timeframe)
        self._bar_count_label.setText(bar_count)
        self._period_label.setText(period)

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

    def _metadata_value(
        self,
        layout: QGridLayout,
        row: int,
        column: int,
        title_text: str,
        value_object_name: str,
    ) -> QLabel:
        container = QWidget(self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)

        title = QLabel(title_text, container)
        title.setObjectName("analysisPriceHistoryMetadataTitle")
        container_layout.addWidget(title)

        value = QLabel(container)
        value.setObjectName(value_object_name)
        value.setWordWrap(True)
        container_layout.addWidget(value)
        layout.addWidget(container, row, column)
        return value

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)


def _format_utc_date(value: datetime) -> str:
    return value.strftime("%Y-%m-%d UTC")
