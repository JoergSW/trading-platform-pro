from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from trading_platform.application.market_data.market_snapshot import MarketSnapshot


class MarketWorkspaceWidget(QWidget):
    """Display one read-only Application-owned market snapshot."""

    def __init__(
        self,
        snapshot: MarketSnapshot | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("marketWorkspaceWidget")
        self._snapshot = snapshot or MarketSnapshot.unavailable()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Market Overview", self)
        title.setObjectName("marketWorkspaceTitle")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        state = QLabel(self._snapshot.state.value, self)
        state.setObjectName("marketWorkspaceState")
        state.setProperty(
            "marketState",
            self._snapshot.state.value.lower().replace(" ", "_"),
        )
        header_layout.addWidget(state)
        layout.addLayout(header_layout)

        detail = QLabel(self._snapshot.detail, self)
        detail.setObjectName("marketWorkspaceDetail")
        detail.setWordWrap(True)
        layout.addWidget(detail)

        cards_layout = QHBoxLayout()
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(12)
        cards_layout.addWidget(
            self._status_card(
                "Market Status",
                _market_status_text(self._snapshot),
                "marketWorkspaceMarketStatus",
            )
        )
        cards_layout.addWidget(
            self._status_card(
                "Data Source",
                _source_text(self._snapshot),
                "marketWorkspaceDataSource",
            )
        )
        cards_layout.addWidget(
            self._status_card(
                "Last Update",
                _format_last_update(self._snapshot.observed_at),
                "marketWorkspaceLastUpdate",
            )
        )
        layout.addLayout(cards_layout)

        safety_note = QLabel(
            "Read-only view. No external connections or executable actions.",
            self,
        )
        safety_note.setObjectName("marketWorkspaceSafetyNote")
        safety_note.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(safety_note)
        layout.addStretch(1)

    @property
    def snapshot(self) -> MarketSnapshot:
        return self._snapshot

    def _status_card(
        self,
        title_text: str,
        value_text: str,
        value_object_name: str,
    ) -> QFrame:
        card = QFrame(self)
        card.setObjectName("marketWorkspaceCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(title_text, card)
        title.setObjectName("marketWorkspaceCardTitle")
        layout.addWidget(title)

        value = QLabel(value_text, card)
        value.setObjectName(value_object_name)
        value.setWordWrap(True)
        layout.addWidget(value)
        layout.addStretch(1)

        return card


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
