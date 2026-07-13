from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotService,
    MarketSnapshotState,
)
from trading_platform.application.market_data.market_snapshot_freshness import (
    DEFAULT_MARKET_SNAPSHOT_FRESH_SECONDS,
    DEFAULT_MARKET_SNAPSHOT_STALE_SECONDS,
    MarketSnapshotFreshnessPolicy,
)

_FRESHNESS_UPDATE_INTERVAL_MS = 1_000


def _utc_now() -> datetime:
    return datetime.now(UTC)


class MarketWorkspaceWidget(QWidget):
    """Display and refresh one read-only Application-owned market snapshot."""

    refresh_finished = Signal()

    def __init__(
        self,
        snapshot: MarketSnapshot | None = None,
        parent: QWidget | None = None,
        *,
        snapshot_service: MarketSnapshotService | None = None,
        auto_refresh_seconds: int | None = None,
        fresh_seconds: int = DEFAULT_MARKET_SNAPSHOT_FRESH_SECONDS,
        stale_seconds: int = DEFAULT_MARKET_SNAPSHOT_STALE_SECONDS,
        now_provider: Callable[[], datetime] = _utc_now,
    ) -> None:
        super().__init__(parent)
        if auto_refresh_seconds is not None and auto_refresh_seconds <= 0:
            raise ValueError("auto_refresh_seconds must be greater than zero")
        if auto_refresh_seconds is not None and snapshot_service is None:
            raise ValueError("auto refresh requires a market snapshot service")

        self.setObjectName("marketWorkspaceWidget")
        self._snapshot = snapshot or MarketSnapshot.unavailable()
        self._snapshot_service = snapshot_service
        self._auto_refresh_seconds = auto_refresh_seconds
        self._freshness_policy = MarketSnapshotFreshnessPolicy(
            fresh_seconds=fresh_seconds,
            stale_seconds=stale_seconds,
        )
        self._now_provider = now_provider
        self._refresh_pending = False

        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setObjectName("marketSnapshotAutoRefreshTimer")
        self._auto_refresh_timer.setSingleShot(False)
        self._auto_refresh_timer.timeout.connect(self.refresh_snapshot)

        self._freshness_timer = QTimer(self)
        self._freshness_timer.setObjectName("marketSnapshotFreshnessTimer")
        self._freshness_timer.setSingleShot(False)
        self._freshness_timer.setInterval(_FRESHNESS_UPDATE_INTERVAL_MS)
        self._freshness_timer.timeout.connect(self.update_freshness)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Market Overview", self)
        title.setObjectName("marketWorkspaceTitle")
        header_layout.addWidget(title)

        self._state_label = QLabel(self)
        self._state_label.setObjectName("marketWorkspaceState")
        header_layout.addWidget(self._state_label)
        header_layout.addStretch(1)

        self._refresh_status = QLabel(self)
        self._refresh_status.setObjectName("marketWorkspaceRefreshStatus")
        header_layout.addWidget(self._refresh_status)

        self._refresh_button = QPushButton("Refresh", self)
        self._refresh_button.setObjectName("marketWorkspaceRefreshButton")
        self._refresh_button.setEnabled(snapshot_service is not None)
        self._refresh_button.clicked.connect(self.refresh_snapshot)
        header_layout.addWidget(self._refresh_button)
        layout.addLayout(header_layout)

        self._detail_label = QLabel(self)
        self._detail_label.setObjectName("marketWorkspaceDetail")
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)

        cards_layout = QHBoxLayout()
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(12)
        market_status_card, self._market_status_label = self._status_card(
            "Market Status",
            "marketWorkspaceMarketStatus",
        )
        cards_layout.addWidget(market_status_card)
        source_card, self._source_label = self._status_card(
            "Data Source",
            "marketWorkspaceDataSource",
        )
        cards_layout.addWidget(source_card)
        last_update_card, self._last_update_label = self._status_card(
            "Last Update",
            "marketWorkspaceLastUpdate",
        )
        cards_layout.addWidget(last_update_card)
        layout.addLayout(cards_layout)

        freshness_cards_layout = QHBoxLayout()
        freshness_cards_layout.setContentsMargins(0, 0, 0, 0)
        freshness_cards_layout.setSpacing(12)
        snapshot_age_card, self._snapshot_age_label = self._status_card(
            "Snapshot Age",
            "marketWorkspaceSnapshotAge",
        )
        freshness_cards_layout.addWidget(snapshot_age_card)
        freshness_card, self._freshness_label = self._status_card(
            "Data Freshness",
            "marketWorkspaceFreshness",
        )
        freshness_cards_layout.addWidget(freshness_card)
        layout.addLayout(freshness_cards_layout)

        safety_note = QLabel(
            "Read-only view. No external connections or executable actions.",
            self,
        )
        safety_note.setObjectName("marketWorkspaceSafetyNote")
        safety_note.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(safety_note)
        layout.addStretch(1)

        self._apply_snapshot(self._snapshot)
        self._freshness_timer.start()
        if snapshot_service is None:
            self._set_refresh_status("NOT CONFIGURED", "unavailable")
        elif auto_refresh_seconds is None:
            self._set_refresh_status("IDLE", "idle")
        else:
            self._set_refresh_status(
                f"AUTO {auto_refresh_seconds}s",
                "idle",
            )
            self._auto_refresh_timer.start(auto_refresh_seconds * 1_000)

    @property
    def snapshot(self) -> MarketSnapshot:
        return self._snapshot

    @property
    def is_refreshing(self) -> bool:
        return self._refresh_pending

    @property
    def auto_refresh_seconds(self) -> int | None:
        return self._auto_refresh_seconds

    @property
    def fresh_seconds(self) -> int:
        return self._freshness_policy.fresh_seconds

    @property
    def stale_seconds(self) -> int:
        return self._freshness_policy.stale_seconds

    @Slot()
    def refresh_snapshot(self) -> None:
        if self._snapshot_service is None or self._refresh_pending:
            return

        self._refresh_pending = True
        self._refresh_button.setEnabled(False)
        self._set_refresh_status("REFRESHING", "loading")
        QTimer.singleShot(0, self._perform_refresh)

    @Slot()
    def update_freshness(self) -> None:
        snapshot = self._snapshot
        if (
            snapshot.state is not MarketSnapshotState.READY
            or snapshot.observed_at is None
        ):
            self._snapshot_age_label.setText("Not available")
            self._set_freshness_status("NOT AVAILABLE", "unavailable")
            return

        freshness = self._freshness_policy.assess(
            snapshot.observed_at,
            self._now_provider(),
        )
        self._snapshot_age_label.setText(_format_snapshot_age(freshness.age_seconds))
        self._set_freshness_status(
            freshness.state.value,
            freshness.state.value.lower(),
        )

    def wait_for_refresh(self) -> bool:
        return not self._refresh_pending

    def closeEvent(self, event: QCloseEvent) -> None:
        self._auto_refresh_timer.stop()
        self._freshness_timer.stop()
        super().closeEvent(event)

    @Slot()
    def _perform_refresh(self) -> None:
        snapshot_service = self._snapshot_service
        if snapshot_service is None:
            self._finish_refresh()
            return

        try:
            snapshot = snapshot_service.load_snapshot()
        except Exception as exc:
            self._show_refresh_error(
                f"Market snapshot refresh raised {type(exc).__name__}."
            )
        else:
            self._handle_refreshed_snapshot(snapshot)
        finally:
            self._finish_refresh()

    def _handle_refreshed_snapshot(self, snapshot: MarketSnapshot) -> None:
        if not isinstance(snapshot, MarketSnapshot):
            self._show_refresh_error(
                "Market snapshot refresh returned an invalid snapshot."
            )
            return

        if (
            snapshot.state is MarketSnapshotState.UNAVAILABLE
            and self._snapshot.state is not MarketSnapshotState.UNAVAILABLE
        ):
            self._show_refresh_error(snapshot.detail)
            return

        snapshot_changed = not _snapshots_have_same_content(
            self._snapshot,
            snapshot,
        )
        self._apply_snapshot(snapshot)
        if snapshot.state is MarketSnapshotState.UNAVAILABLE:
            self._set_refresh_status("ERROR", "error")
        elif snapshot_changed:
            self._set_refresh_status("UPDATED", "success")
        else:
            self._set_refresh_status("UNCHANGED", "unchanged")

    def _finish_refresh(self) -> None:
        self._refresh_pending = False
        self._refresh_button.setEnabled(self._snapshot_service is not None)
        self.refresh_finished.emit()

    def _show_refresh_error(self, detail: str) -> None:
        if self._snapshot.state is MarketSnapshotState.UNAVAILABLE:
            self._detail_label.setText(detail)
            self._set_refresh_status("ERROR", "error")
            return

        self._set_state_label("STALE", "stale")
        self._detail_label.setText(
            f"Refresh failed: {detail} Previous snapshot retained and may be stale."
        )
        self._set_refresh_status("ERROR", "error")

    def _apply_snapshot(self, snapshot: MarketSnapshot) -> None:
        self._snapshot = snapshot
        self._set_state_label(
            snapshot.state.value,
            snapshot.state.value.lower().replace(" ", "_"),
        )
        self._detail_label.setText(snapshot.detail)
        self._market_status_label.setText(_market_status_text(snapshot))
        self._source_label.setText(_source_text(snapshot))
        self._last_update_label.setText(_format_last_update(snapshot.observed_at))
        self.update_freshness()

    def _set_state_label(self, text: str, state: str) -> None:
        self._state_label.setText(text)
        _set_dynamic_property(self._state_label, "marketState", state)

    def _set_refresh_status(self, text: str, state: str) -> None:
        self._refresh_status.setText(text)
        _set_dynamic_property(self._refresh_status, "refreshState", state)

    def _set_freshness_status(self, text: str, state: str) -> None:
        self._freshness_label.setText(text)
        _set_dynamic_property(self._freshness_label, "freshnessState", state)

    def _status_card(
        self,
        title_text: str,
        value_object_name: str,
    ) -> tuple[QFrame, QLabel]:
        card = QFrame(self)
        card.setObjectName("marketWorkspaceCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(title_text, card)
        title.setObjectName("marketWorkspaceCardTitle")
        layout.addWidget(title)

        value = QLabel(card)
        value.setObjectName(value_object_name)
        value.setWordWrap(True)
        layout.addWidget(value)
        layout.addStretch(1)

        return card, value


def _snapshots_have_same_content(
    previous: MarketSnapshot,
    current: MarketSnapshot,
) -> bool:
    return (
        previous.state,
        previous.market_status,
        previous.source_name,
        previous.observed_at,
    ) == (
        current.state,
        current.market_status,
        current.source_name,
        current.observed_at,
    )


def _set_dynamic_property(widget: QWidget, name: str, value: str) -> None:
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _market_status_text(snapshot: MarketSnapshot) -> str:
    if snapshot.market_status is not None:
        return snapshot.market_status
    return snapshot.state.value


def _source_text(snapshot: MarketSnapshot) -> str:
    if snapshot.source_name is not None:
        return snapshot.source_name
    return "NOT CONFIGURED"


def _format_last_update(observed_at: datetime | None) -> str:
    if observed_at is None:
        return "Never"
    return observed_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def _format_snapshot_age(age_seconds: int) -> str:
    if age_seconds < 60:
        return f"{age_seconds}s"

    minutes, seconds = divmod(age_seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds:02d}s"

    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes:02d}m"

    days, hours = divmod(hours, 24)
    return f"{days}d {hours:02d}h"
