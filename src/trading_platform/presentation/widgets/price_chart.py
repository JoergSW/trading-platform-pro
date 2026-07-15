from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from trading_platform.application.market_data.price_history import (
    PriceHistory,
    PriceHistoryState,
)


class PriceChartWidget(QWidget):
    """Presentation-only OHLCV chart for one validated price-history result."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("analysisPriceChartCanvas")
        self.setMinimumHeight(300)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._history: PriceHistory | None = None

    @property
    def history(self) -> PriceHistory | None:
        return self._history

    def set_history(self, history: PriceHistory | None) -> None:
        if history is not None and not isinstance(history, PriceHistory):
            raise TypeError("history must be PriceHistory or None")
        self._history = history
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#171717"))

        history = self._history
        if history is None or history.state is not PriceHistoryState.READY:
            painter.setPen(QColor("#9ca3af"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No validated price history to display.",
            )
            return

        bars = history.bars
        chart_rect = QRectF(self.rect()).adjusted(56.0, 18.0, -16.0, -28.0)
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        volume_height = max(52.0, chart_rect.height() * 0.22)
        gap = 14.0
        price_rect = QRectF(
            chart_rect.left(),
            chart_rect.top(),
            chart_rect.width(),
            chart_rect.height() - volume_height - gap,
        )
        volume_rect = QRectF(
            chart_rect.left(),
            price_rect.bottom() + gap,
            chart_rect.width(),
            volume_height,
        )

        low_price = min(bar.low_price for bar in bars)
        high_price = max(bar.high_price for bar in bars)
        price_span = high_price - low_price
        if price_span == Decimal("0"):
            price_span = max(high_price * Decimal("0.01"), Decimal("0.01"))
            low_price -= price_span / Decimal("2")
            high_price += price_span / Decimal("2")
            price_span = high_price - low_price

        max_volume = max(bar.volume for bar in bars)
        x_step = price_rect.width() / max(len(bars), 1)
        candle_width = max(3.0, min(12.0, x_step * 0.58))

        painter.setPen(QPen(QColor("#374151"), 1.0))
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = price_rect.top() + price_rect.height() * fraction
            painter.drawLine(
                QPointF(price_rect.left(), y), QPointF(price_rect.right(), y)
            )

        for index, bar in enumerate(bars):
            x = price_rect.left() + x_step * (index + 0.5)
            high_y = _price_y(bar.high_price, low_price, price_span, price_rect)
            low_y = _price_y(bar.low_price, low_price, price_span, price_rect)
            open_y = _price_y(bar.open_price, low_price, price_span, price_rect)
            close_y = _price_y(bar.close_price, low_price, price_span, price_rect)
            rising = bar.close_price >= bar.open_price
            candle_color = QColor("#22c55e" if rising else "#ef4444")

            painter.setPen(QPen(candle_color, 1.2))
            painter.drawLine(QPointF(x, high_y), QPointF(x, low_y))

            body_top = min(open_y, close_y)
            body_height = max(2.0, abs(close_y - open_y))
            body_rect = QRectF(
                x - candle_width / 2,
                body_top,
                candle_width,
                body_height,
            )
            painter.fillRect(body_rect, candle_color)

            if max_volume > 0 and bar.volume > 0:
                volume_ratio = bar.volume / max_volume
                volume_bar_height = volume_rect.height() * volume_ratio
                volume_bar = QRectF(
                    x - candle_width / 2,
                    volume_rect.bottom() - volume_bar_height,
                    candle_width,
                    volume_bar_height,
                )
                painter.fillRect(
                    volume_bar,
                    QColor(
                        candle_color.red(),
                        candle_color.green(),
                        candle_color.blue(),
                        150,
                    ),
                )

        painter.setPen(QColor("#d1d5db"))
        painter.drawText(
            QRectF(0.0, price_rect.top() - 8.0, 50.0, 20.0),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            _format_decimal(high_price),
        )
        painter.drawText(
            QRectF(0.0, price_rect.bottom() - 10.0, 50.0, 20.0),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            _format_decimal(low_price),
        )
        painter.drawText(
            QRectF(
                price_rect.left(),
                volume_rect.bottom() + 4.0,
                price_rect.width(),
                20.0,
            ),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            bars[0].observed_at.strftime("%Y-%m-%d"),
        )
        painter.drawText(
            QRectF(
                price_rect.left(),
                volume_rect.bottom() + 4.0,
                price_rect.width(),
                20.0,
            ),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            bars[-1].observed_at.strftime("%Y-%m-%d"),
        )


def _price_y(
    value: Decimal,
    low_price: Decimal,
    price_span: Decimal,
    rect: QRectF,
) -> float:
    ratio = float((value - low_price) / price_span)
    return rect.bottom() - rect.height() * ratio


def _format_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")
