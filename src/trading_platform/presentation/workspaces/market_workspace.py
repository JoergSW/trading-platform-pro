from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


@dataclass(frozen=True, slots=True)
class MarketWorkspaceData:
    """Presentation state for the read-only Market workspace."""

    state: str
    market_status: str
    data_source: str
    last_update: datetime | None
    detail: str

    @classmethod
    def unavailable(cls) -> MarketWorkspaceData:
        return cls(
            state="UNAVAILABLE",
            market_status="UNAVAILABLE",
            data_source="NOT CONFIGURED",
            last_update=None,
            detail=(
                "No market data source is configured. Market values are not "
                "estimated or reused."
            ),
        )

    @classmethod
    def no_data(cls, data_source: str) -> MarketWorkspaceData:
        return cls(
            state="NO DATA",
            market_status="NO DATA",
            data_source=data_source,
            last_update=None,
            detail=(
                "The configured source has not provided market state data. "
                "No fallback value is displayed."
            ),
        )

    @classmethod
    def ready(
        cls,
        market_status: str,
        data_source: str,
        last_update: datetime,
    ) -> MarketWorkspaceData:
        return cls(
            state="READY",
            market_status=market_status,
            data_source=data_source,
            last_update=last_update,
            detail="Market state data is available from the configured source.",
        )


class MarketWorkspaceWidget(QWidget):
    """Display read-only market availability without inventing market values."""

    def __init__(
        self,
        data: MarketWorkspaceData | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("marketWorkspaceWidget")
        self._data = data or MarketWorkspaceData.unavailable()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Market Overview", self)
        title.setObjectName("marketWorkspaceTitle")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        state = QLabel(self._data.state, self)
        state.setObjectName("marketWorkspaceState")
        state.setProperty("marketState", self._data.state.lower().replace(" ", "_"))
        header_layout.addWidget(state)
        layout.addLayout(header_layout)

        detail = QLabel(self._data.detail, self)
        detail.setObjectName("marketWorkspaceDetail")
        detail.setWordWrap(True)
        layout.addWidget(detail)

        cards_layout = QHBoxLayout()
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(12)
        cards_layout.addWidget(
            self._status_card(
                "Market Status",
                self._data.market_status,
                "marketWorkspaceMarketStatus",
            )
        )
        cards_layout.addWidget(
            self._status_card(
                "Data Source",
                self._data.data_source,
                "marketWorkspaceDataSource",
            )
        )
        cards_layout.addWidget(
            self._status_card(
                "Last Update",
                _format_last_update(self._data.last_update),
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
    def data(self) -> MarketWorkspaceData:
        return self._data

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


def _format_last_update(last_update: datetime | None) -> str:
    if last_update is None:
        return "Never"
    if last_update.tzinfo is None or last_update.utcoffset() is None:
        return "Invalid timestamp"
    return last_update.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
