from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotService,
    PortfolioSnapshotState,
)
from trading_platform.application.risk.portfolio_exposure import (
    PortfolioExposureResult,
    PortfolioExposureState,
    PortfolioPositionExposureResult,
    PortfolioPositionExposureState,
    summarize_portfolio_exposure,
)


class RiskOverviewWorkspaceWidget(QWidget):
    """Display existing read-only Portfolio risk context without risk decisions."""

    refresh_finished = Signal()

    def __init__(
        self,
        result: PortfolioSnapshotResult | None = None,
        parent: QWidget | None = None,
        *,
        snapshot_service: PortfolioSnapshotService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("riskOverviewWorkspaceWidget")
        self._result = result or PortfolioSnapshotResult.unavailable()
        self._snapshot_service = snapshot_service
        self._refresh_pending = False

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("riskOverviewScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget(scroll_area)
        scroll_content.setObjectName("riskOverviewScrollContent")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header_layout = QGridLayout()
        header_layout.setObjectName("riskOverviewHeaderLayout")
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setHorizontalSpacing(8)
        header_layout.setVerticalSpacing(8)

        title = QLabel("Risk Overview", scroll_content)
        title.setObjectName("riskOverviewTitle")
        header_layout.addWidget(title, 0, 0, 1, 2)

        self._refresh_status = QLabel(scroll_content)
        self._refresh_status.setObjectName("riskOverviewRefreshStatus")
        header_layout.addWidget(
            self._refresh_status,
            0,
            2,
            1,
            1,
            Qt.AlignmentFlag.AlignRight,
        )

        self._refresh_button = QPushButton("Refresh", scroll_content)
        self._refresh_button.setObjectName("riskOverviewRefreshButton")
        self._refresh_button.setEnabled(snapshot_service is not None)
        self._refresh_button.clicked.connect(self.refresh_snapshot)
        header_layout.addWidget(self._refresh_button, 0, 3)

        snapshot_state_title = QLabel("Snapshot", scroll_content)
        snapshot_state_title.setObjectName("riskOverviewStateTitle")
        header_layout.addWidget(snapshot_state_title, 1, 0)

        self._snapshot_state_label = QLabel(scroll_content)
        self._snapshot_state_label.setObjectName("riskOverviewSnapshotState")
        header_layout.addWidget(self._snapshot_state_label, 1, 1)

        exposure_state_title = QLabel("Exposure", scroll_content)
        exposure_state_title.setObjectName("riskOverviewStateTitle")
        header_layout.addWidget(exposure_state_title, 1, 2)

        self._exposure_state_label = QLabel(scroll_content)
        self._exposure_state_label.setObjectName("riskOverviewExposureState")
        header_layout.addWidget(self._exposure_state_label, 1, 3)
        header_layout.setColumnStretch(1, 1)
        header_layout.setColumnStretch(3, 1)
        layout.addLayout(header_layout)

        self._detail_label = QLabel(scroll_content)
        self._detail_label.setObjectName("riskOverviewDetail")
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)

        metadata_cards = self._card_grid("riskOverviewMetadataGrid")
        source_card, self._source_label = self._status_card(
            "Data Source",
            "riskOverviewSource",
            scroll_content,
        )
        metadata_cards.addWidget(source_card, 0, 0)
        observed_card, self._observed_at_label = self._status_card(
            "Observed UTC",
            "riskOverviewObservedAt",
            scroll_content,
        )
        metadata_cards.addWidget(observed_card, 0, 1)
        coverage_card, self._coverage_label = self._status_card(
            "Valuation Coverage",
            "riskOverviewValuationCoverage",
            scroll_content,
        )
        metadata_cards.addWidget(coverage_card, 1, 0)
        unvalued_card, self._unvalued_positions_label = self._status_card(
            "Unvalued Positions",
            "riskOverviewUnvaluedPositions",
            scroll_content,
        )
        metadata_cards.addWidget(unvalued_card, 1, 1)
        layout.addLayout(metadata_cards)

        exposure_title = QLabel("Portfolio Exposure", scroll_content)
        exposure_title.setObjectName("riskOverviewExposureTitle")
        layout.addWidget(exposure_title)

        exposure_cards = self._card_grid("riskOverviewExposureGrid")
        long_card, self._long_exposure_label = self._status_card(
            "Long Exposure",
            "riskOverviewLongExposure",
            scroll_content,
        )
        exposure_cards.addWidget(long_card, 0, 0)
        short_card, self._short_exposure_label = self._status_card(
            "Short Exposure",
            "riskOverviewShortExposure",
            scroll_content,
        )
        exposure_cards.addWidget(short_card, 0, 1)
        gross_card, self._gross_exposure_label = self._status_card(
            "Gross Exposure",
            "riskOverviewGrossExposure",
            scroll_content,
        )
        exposure_cards.addWidget(gross_card, 1, 0)
        net_card, self._net_exposure_label = self._status_card(
            "Net Exposure",
            "riskOverviewNetExposure",
            scroll_content,
        )
        exposure_cards.addWidget(net_card, 1, 1)
        layout.addLayout(exposure_cards)

        context_cards = self._card_grid("riskOverviewContextGrid")
        largest_card, self._largest_position_label = self._status_card(
            "Largest Position",
            "riskOverviewLargestPosition",
            scroll_content,
        )
        context_cards.addWidget(largest_card, 0, 0)
        concentration_card, self._concentration_label = self._status_card(
            "Largest Concentration",
            "riskOverviewLargestConcentration",
            scroll_content,
        )
        context_cards.addWidget(concentration_card, 0, 1)
        layout.addLayout(context_cards)

        self._exposure_detail_label = QLabel(scroll_content)
        self._exposure_detail_label.setObjectName("riskOverviewExposureDetail")
        self._exposure_detail_label.setWordWrap(True)
        layout.addWidget(self._exposure_detail_label)

        breakdown_title = QLabel("Position Exposure Breakdown", scroll_content)
        breakdown_title.setObjectName("riskOverviewPositionExposureTitle")
        layout.addWidget(breakdown_title)

        self._position_exposure_empty_label = QLabel(scroll_content)
        self._position_exposure_empty_label.setObjectName(
            "riskOverviewPositionExposureEmpty"
        )
        self._position_exposure_empty_label.setWordWrap(True)
        layout.addWidget(self._position_exposure_empty_label)

        self._position_exposure_table = QTableWidget(0, 6, scroll_content)
        self._position_exposure_table.setObjectName("riskOverviewPositionExposureTable")
        self._position_exposure_table.setHorizontalHeaderLabels(
            (
                "Symbol",
                "Direction",
                "Current Value",
                "Absolute Exposure",
                "Gross Share",
                "Valuation",
            )
        )
        self._position_exposure_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._position_exposure_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self._position_exposure_table.verticalHeader().setVisible(False)
        breakdown_header = self._position_exposure_table.horizontalHeader()
        breakdown_header.setStretchLastSection(False)
        breakdown_header.setMinimumSectionSize(80)
        breakdown_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._position_exposure_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._position_exposure_table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self._position_exposure_table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self._position_exposure_table.setWordWrap(False)
        self._position_exposure_table.setMinimumHeight(220)
        layout.addWidget(self._position_exposure_table, 1)

        safety_note = QLabel(
            "Read-only risk context from the configured Portfolio snapshot. "
            "Missing current values remain unavailable. No risk verdict, limit "
            "evaluation, order gating, broker connection, trading or LIVE action.",
            scroll_content,
        )
        safety_note.setObjectName("riskOverviewSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area)

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
        self._set_snapshot_state(loading_result.state)
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
        self._set_snapshot_state(result.state)
        self._detail_label.setText(result.detail)
        self._render_exposure(summarize_portfolio_exposure(result))

    def _render_exposure(self, result: PortfolioExposureResult) -> None:
        self._set_exposure_state(result.state)
        self._render_position_exposure_breakdown(result)
        summary = result.summary
        if summary is None:
            self._source_label.setText(result.source_name or "NOT CONFIGURED")
            self._observed_at_label.setText("UNAVAILABLE")
            self._coverage_label.setText("UNAVAILABLE")
            self._unvalued_positions_label.setText("UNAVAILABLE")
            self._long_exposure_label.setText("UNAVAILABLE")
            self._short_exposure_label.setText("UNAVAILABLE")
            self._gross_exposure_label.setText("UNAVAILABLE")
            self._net_exposure_label.setText("UNAVAILABLE")
            self._largest_position_label.setText("UNAVAILABLE")
            self._concentration_label.setText("UNAVAILABLE")
            self._exposure_detail_label.setText(result.detail)
            return

        self._source_label.setText(summary.source_name)
        self._observed_at_label.setText(_format_timestamp(summary.observed_at))
        self._coverage_label.setText(
            f"{summary.valued_position_count} / {summary.total_position_count}"
        )
        unvalued_symbols = tuple(
            position.symbol
            for position in result.position_exposures
            if position.state is PortfolioPositionExposureState.UNAVAILABLE
        )
        self._unvalued_positions_label.setText(
            ", ".join(unvalued_symbols) if unvalued_symbols else "NONE"
        )
        self._long_exposure_label.setText(
            _format_money(summary.long_exposure, summary.currency)
        )
        self._short_exposure_label.setText(
            _format_money(summary.short_exposure, summary.currency)
        )
        self._gross_exposure_label.setText(
            _format_money(summary.gross_exposure, summary.currency)
        )
        self._net_exposure_label.setText(
            _format_money(summary.net_exposure, summary.currency)
        )
        self._largest_position_label.setText(
            _format_largest_position(
                summary.largest_position_symbol,
                summary.largest_position_value,
                summary.currency,
            )
        )
        self._concentration_label.setText(
            _format_percentage(summary.largest_position_concentration_pct)
        )
        self._exposure_detail_label.setText(result.detail)

    def _render_position_exposure_breakdown(
        self,
        result: PortfolioExposureResult,
    ) -> None:
        rows = result.position_exposures
        self._position_exposure_table.setRowCount(len(rows))
        for row, position in enumerate(rows):
            values = _position_exposure_values(position)
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._position_exposure_table.setItem(row, column, item)

        has_rows = bool(rows)
        self._position_exposure_table.setVisible(has_rows)
        self._position_exposure_empty_label.setVisible(not has_rows)
        if result.summary is None:
            self._position_exposure_empty_label.setText(
                "Position exposure is unavailable. No values are inferred."
            )
        elif not rows:
            self._position_exposure_empty_label.setText(
                "The configured source contains no current positions."
            )

    def _set_snapshot_state(self, state: PortfolioSnapshotState) -> None:
        self._snapshot_state_label.setText(state.value)
        _set_dynamic_property(
            self._snapshot_state_label,
            "portfolioState",
            state.value.lower().replace(" ", "_"),
        )

    def _set_exposure_state(self, state: PortfolioExposureState) -> None:
        self._exposure_state_label.setText(state.value)
        _set_dynamic_property(
            self._exposure_state_label,
            "exposureState",
            state.value.lower(),
        )

    def _set_refresh_status(self, text: str, state: str) -> None:
        self._refresh_status.setText(text)
        _set_dynamic_property(self._refresh_status, "refreshState", state)

    def _card_grid(self, object_name: str) -> QGridLayout:
        grid = QGridLayout()
        grid.setObjectName(object_name)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 220)
        grid.setColumnMinimumWidth(1, 220)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        return grid

    def _status_card(
        self,
        title_text: str,
        value_object_name: str,
        parent: QWidget,
    ) -> tuple[QFrame, QLabel]:
        card = QFrame(parent)
        card.setObjectName("riskOverviewCard")
        card.setMinimumWidth(220)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(title_text, card)
        title.setObjectName("riskOverviewCardTitle")
        layout.addWidget(title)

        value = QLabel(card)
        value.setObjectName(value_object_name)
        value.setMinimumWidth(0)
        value.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        value.setWordWrap(True)
        layout.addWidget(value)
        layout.addStretch(1)
        return card, value


def _set_dynamic_property(widget: QWidget, name: str, value: str) -> None:
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _format_money(value: Decimal | None, currency: str | None) -> str:
    if value is None or currency is None:
        return "UNAVAILABLE"
    return f"{format(value, 'f')} {currency}"


def _format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "UNAVAILABLE"
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def _position_exposure_values(
    position: PortfolioPositionExposureResult,
) -> tuple[str, str, str, str, str, str]:
    direction = (
        position.direction.value if position.direction is not None else "UNAVAILABLE"
    )
    share = (
        _format_percentage(position.gross_exposure_share_pct)
        if position.gross_exposure_share_pct is not None
        else "UNAVAILABLE"
    )
    return (
        position.symbol,
        direction,
        _format_money(position.signed_current_value, position.currency),
        _format_money(position.absolute_exposure, position.currency),
        share,
        position.state.value,
    )


def _format_largest_position(
    symbol: str | None,
    value: Decimal | None,
    currency: str | None,
) -> str:
    if symbol is None or value is None or currency is None:
        return "NONE"
    return f"{symbol} | {_format_money(value, currency)}"


def _format_percentage(value: Decimal) -> str:
    return f"{format(value, '.2f')} %"
