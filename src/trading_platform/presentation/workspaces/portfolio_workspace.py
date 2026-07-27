from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
    InstrumentContextState,
)
from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotService,
    PortfolioSnapshotState,
)
from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioPosition,
    PortfolioSnapshot,
)

PORTFOLIO_CONTEXT_SOURCE = "Portfolio"


class PortfolioWorkspaceWidget(QWidget):
    """Display one read-only portfolio snapshot and publish position context."""

    refresh_finished = Signal()

    def __init__(
        self,
        result: PortfolioSnapshotResult | None = None,
        parent: QWidget | None = None,
        *,
        snapshot_service: PortfolioSnapshotService | None = None,
        instrument_context_service: InstrumentContextService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("portfolioWorkspaceWidget")
        self._result = result or PortfolioSnapshotResult.unavailable()
        self._snapshot_service = snapshot_service
        self._instrument_context_service = (
            instrument_context_service or InstrumentContextService()
        )
        self._positions: tuple[PortfolioPosition, ...] = ()
        self._selected_symbol: str | None = None
        self._refresh_pending = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Portfolio Overview", self)
        title.setObjectName("portfolioWorkspaceTitle")
        header_layout.addWidget(title)

        self._state_label = QLabel(self)
        self._state_label.setObjectName("portfolioWorkspaceState")
        header_layout.addWidget(self._state_label)
        header_layout.addStretch(1)

        self._refresh_status = QLabel(self)
        self._refresh_status.setObjectName("portfolioWorkspaceRefreshStatus")
        header_layout.addWidget(self._refresh_status)

        self._refresh_button = QPushButton("Refresh", self)
        self._refresh_button.setObjectName("portfolioWorkspaceRefreshButton")
        self._refresh_button.setEnabled(snapshot_service is not None)
        self._refresh_button.clicked.connect(self.refresh_snapshot)
        header_layout.addWidget(self._refresh_button)
        layout.addLayout(header_layout)

        self._detail_label = QLabel(self)
        self._detail_label.setObjectName("portfolioWorkspaceDetail")
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)

        account_cards = QHBoxLayout()
        account_cards.setContentsMargins(0, 0, 0, 0)
        account_cards.setSpacing(12)
        account_card, self._account_reference_label = self._status_card(
            "Account Reference",
            "portfolioWorkspaceAccountReference",
        )
        account_cards.addWidget(account_card)
        currency_card, self._currency_label = self._status_card(
            "Currency",
            "portfolioWorkspaceCurrency",
        )
        account_cards.addWidget(currency_card)
        source_card, self._source_label = self._status_card(
            "Data Source",
            "portfolioWorkspaceSource",
        )
        account_cards.addWidget(source_card)
        observed_card, self._observed_at_label = self._status_card(
            "Observed UTC",
            "portfolioWorkspaceObservedAt",
        )
        account_cards.addWidget(observed_card)
        layout.addLayout(account_cards)

        financial_cards = QHBoxLayout()
        financial_cards.setContentsMargins(0, 0, 0, 0)
        financial_cards.setSpacing(12)
        cash_card, self._cash_label = self._status_card(
            "Cash",
            "portfolioWorkspaceCash",
        )
        financial_cards.addWidget(cash_card)
        net_liquidation_card, self._net_liquidation_label = self._status_card(
            "Net Liquidation Value",
            "portfolioWorkspaceNetLiquidationValue",
        )
        financial_cards.addWidget(net_liquidation_card)
        pnl_card, self._unrealized_pnl_label = self._status_card(
            "Unrealized P&L",
            "portfolioWorkspaceUnrealizedPnl",
        )
        financial_cards.addWidget(pnl_card)
        layout.addLayout(financial_cards)

        positions_title = QLabel("Current Positions", self)
        positions_title.setObjectName("portfolioWorkspacePositionsTitle")
        layout.addWidget(positions_title)

        self._positions_empty_label = QLabel(self)
        self._positions_empty_label.setObjectName("portfolioWorkspacePositionsEmpty")
        self._positions_empty_label.setWordWrap(True)
        layout.addWidget(self._positions_empty_label)

        self._positions_table = QTableWidget(0, 7, self)
        self._positions_table.setObjectName("portfolioWorkspacePositionsTable")
        self._positions_table.setHorizontalHeaderLabels(
            (
                "Symbol",
                "Quantity",
                "Average Price",
                "Current Price",
                "Current Value",
                "Unrealized P&L",
                "Observed UTC",
            )
        )
        self._positions_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._positions_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._positions_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._positions_table.verticalHeader().setVisible(False)
        self._positions_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._positions_table.setMinimumHeight(220)
        self._positions_table.itemSelectionChanged.connect(
            self._publish_selected_position
        )
        layout.addWidget(self._positions_table, 1)

        safety_note = QLabel(
            "Read-only local snapshot. No broker connection, position mutation, "
            "P&L calculation, order preparation, trading or LIVE action.",
            self,
        )
        safety_note.setObjectName("portfolioWorkspaceSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        self._set_refresh_status(
            "READY" if snapshot_service is not None else "UNAVAILABLE",
            "ready" if snapshot_service is not None else "unavailable",
        )
        self._apply_result(self._result)

    def refresh_snapshot(self) -> None:
        if self._snapshot_service is None or self._refresh_pending:
            return

        self._refresh_pending = True
        self._refresh_button.setEnabled(False)
        self._set_refresh_status("LOADING", "loading")
        loading_result = PortfolioSnapshotResult.loading(self._result.source_name)
        self._set_state(loading_result.state)
        self._detail_label.setText(loading_result.detail)
        try:
            result = self._snapshot_service.load_snapshot()
        except Exception as exc:
            result = PortfolioSnapshotResult.error(
                detail=f"Portfolio snapshot refresh raised {type(exc).__name__}.",
                source_name=self._result.source_name,
            )
        self._apply_result(result)
        if result.state in {
            PortfolioSnapshotState.READY,
            PortfolioSnapshotState.EMPTY,
            PortfolioSnapshotState.STALE,
        }:
            self._set_refresh_status("UPDATED", "success")
        else:
            self._set_refresh_status("ERROR", "error")
        self._refresh_pending = False
        self._refresh_button.setEnabled(True)
        self.refresh_finished.emit()

    def _apply_result(self, result: PortfolioSnapshotResult) -> None:
        if not isinstance(result, PortfolioSnapshotResult):
            raise TypeError("result must be PortfolioSnapshotResult")
        self._result = result
        self._set_state(result.state)
        self._detail_label.setText(result.detail)

        snapshot = result.snapshot
        if snapshot is None:
            self._render_unavailable_account(result.source_name)
            self._render_positions(None)
            return

        self._render_account(snapshot)
        self._render_positions(snapshot)

    def _render_account(self, snapshot: PortfolioSnapshot) -> None:
        account = snapshot.account
        self._account_reference_label.setText(account.account_reference)
        self._currency_label.setText(account.currency)
        self._source_label.setText(snapshot.source_name)
        self._observed_at_label.setText(_format_timestamp(snapshot.observed_at))
        self._cash_label.setText(_format_money(account.cash, account.currency))
        self._net_liquidation_label.setText(
            _format_money(account.net_liquidation_value, account.currency)
        )
        self._unrealized_pnl_label.setText(
            _format_money(account.unrealized_pnl, account.currency)
        )

    def _render_unavailable_account(self, source_name: str | None) -> None:
        self._account_reference_label.setText("UNAVAILABLE")
        self._currency_label.setText("UNAVAILABLE")
        self._source_label.setText(source_name or "NOT CONFIGURED")
        self._observed_at_label.setText("UNAVAILABLE")
        self._cash_label.setText("UNAVAILABLE")
        self._net_liquidation_label.setText("UNAVAILABLE")
        self._unrealized_pnl_label.setText("UNAVAILABLE")

    def _render_positions(self, snapshot: PortfolioSnapshot | None) -> None:
        context = self._instrument_context_service.context
        context_symbol = (
            context.symbol
            if context.state is InstrumentContextState.SELECTED
            and context.source == PORTFOLIO_CONTEXT_SOURCE
            else None
        )
        self._positions = snapshot.positions if snapshot is not None else ()
        currency = snapshot.account.currency if snapshot is not None else None
        observed_at = snapshot.observed_at if snapshot is not None else None

        self._positions_table.blockSignals(True)
        self._positions_table.clearSelection()
        self._positions_table.setRowCount(len(self._positions))
        selected_row: int | None = None
        for row, position in enumerate(self._positions):
            values = (
                position.symbol,
                _format_decimal(position.quantity),
                _format_money(position.average_price, currency),
                _format_money(position.current_price, currency),
                _format_money(position.current_value, currency),
                _format_money(position.unrealized_pnl, currency),
                _format_timestamp(observed_at),
            )
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._positions_table.setItem(row, column, item)
            if position.symbol == self._selected_symbol:
                selected_row = row
            elif self._selected_symbol is None and position.symbol == context_symbol:
                selected_row = row
                self._selected_symbol = position.symbol

        if selected_row is not None:
            self._positions_table.selectRow(selected_row)
        else:
            self._selected_symbol = None
            if context_symbol is not None:
                self._instrument_context_service.clear_instrument(
                    PORTFOLIO_CONTEXT_SOURCE
                )
        self._positions_table.blockSignals(False)

        has_positions = bool(self._positions)
        self._positions_table.setVisible(has_positions)
        self._positions_empty_label.setVisible(not has_positions)
        if snapshot is None:
            self._positions_empty_label.setText(
                "Portfolio positions are unavailable. No values are inferred."
            )
        elif not snapshot.positions:
            self._positions_empty_label.setText(
                "The configured source contains no current positions."
            )

    def _publish_selected_position(self) -> None:
        selected_rows = self._positions_table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_symbol = None
            context = self._instrument_context_service.context
            if context.source == PORTFOLIO_CONTEXT_SOURCE:
                self._instrument_context_service.clear_instrument(
                    PORTFOLIO_CONTEXT_SOURCE
                )
            return
        row = selected_rows[0].row()
        if row < 0 or row >= len(self._positions):
            self._selected_symbol = None
            return
        position = self._positions[row]
        self._selected_symbol = position.symbol
        self._instrument_context_service.select_instrument(
            position.symbol,
            PORTFOLIO_CONTEXT_SOURCE,
        )

    def _set_state(self, state: PortfolioSnapshotState) -> None:
        self._state_label.setText(state.value)
        state_property = state.value.lower().replace(" ", "_")
        _set_dynamic_property(self._state_label, "portfolioState", state_property)

    def _set_refresh_status(self, text: str, state: str) -> None:
        self._refresh_status.setText(text)
        _set_dynamic_property(self._refresh_status, "refreshState", state)

    def _status_card(
        self,
        title_text: str,
        value_object_name: str,
    ) -> tuple[QFrame, QLabel]:
        card = QFrame(self)
        card.setObjectName("portfolioWorkspaceCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(title_text, card)
        title.setObjectName("portfolioWorkspaceCardTitle")
        layout.addWidget(title)

        value = QLabel(card)
        value.setObjectName(value_object_name)
        value.setWordWrap(True)
        layout.addWidget(value)
        layout.addStretch(1)
        return card, value


def _set_dynamic_property(widget: QWidget, name: str, value: str) -> None:
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "UNAVAILABLE"
    return format(value, "f")


def _format_money(value: Decimal | None, currency: str | None) -> str:
    if value is None or currency is None:
        return "UNAVAILABLE"
    return f"{format(value, 'f')} {currency}"


def _format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "UNAVAILABLE"
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
