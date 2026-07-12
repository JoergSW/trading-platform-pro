from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

STARTUP_STEP_COUNT = 3

STARTUP_STATUS_STYLE_SHEET = """
QDialog#startupStatusDialog {
    background: #171717;
    color: #f3f4f6;
    border: 1px solid #4b5563;
}
QLabel#startupApplicationTitle {
    font-size: 20px;
    font-weight: 700;
}
QLabel#startupStatusMessage {
    color: #d1d5db;
}
QProgressBar#startupProgressBar {
    background: #222222;
    border: 1px solid #4b5563;
    border-radius: 4px;
    height: 10px;
}
QProgressBar#startupProgressBar::chunk {
    background: #2563eb;
    border-radius: 3px;
}
QPushButton#startupRetryButton,
QPushButton#startupContinueButton {
    background: #374151;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 6px 14px;
}
QPushButton#startupRetryButton:hover,
QPushButton#startupContinueButton:hover {
    background: #4b5563;
}
"""


class StartupStatusDialog(QDialog):
    """Dialog exposing deterministic startup progress and recoverable errors."""

    retry_requested = Signal()
    continue_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("startupStatusDialog")
        self.setWindowTitle("Trading Cockpit")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(False)
        self.setFixedSize(480, 220)
        self.setStyleSheet(STARTUP_STATUS_STYLE_SHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(18)

        title = QLabel("Trading Cockpit", self)
        title.setObjectName("startupApplicationTitle")
        layout.addWidget(title)

        self._status_message = QLabel("Preparing startup...", self)
        self._status_message.setObjectName("startupStatusMessage")
        self._status_message.setWordWrap(True)
        layout.addWidget(self._status_message)

        self._progress_bar = QProgressBar(self)
        self._progress_bar.setObjectName("startupProgressBar")
        self._progress_bar.setRange(0, STARTUP_STEP_COUNT)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        layout.addWidget(self._progress_bar)

        actions = QHBoxLayout()
        actions.addStretch(1)

        self._retry_button = QPushButton("Retry", self)
        self._retry_button.setObjectName("startupRetryButton")
        self._retry_button.clicked.connect(self.retry_requested.emit)
        actions.addWidget(self._retry_button)

        self._continue_button = QPushButton("Continue", self)
        self._continue_button.setObjectName("startupContinueButton")
        self._continue_button.clicked.connect(self.continue_requested.emit)
        actions.addWidget(self._continue_button)

        layout.addLayout(actions)
        self._set_error_actions_visible(False)

    def update_status(self, message: str, step: int) -> None:
        if not 0 <= step <= STARTUP_STEP_COUNT:
            raise ValueError(
                f"Startup step must be between 0 and {STARTUP_STEP_COUNT}."
            )

        self._set_error_actions_visible(False)
        self._status_message.setText(message)
        self._progress_bar.setValue(step)

    def show_error(self, detail: str) -> None:
        """Keep startup visible and expose explicit recovery actions."""
        self._status_message.setText(f"Startup failed: {detail}")
        self._set_error_actions_visible(True)

    def _set_error_actions_visible(self, visible: bool) -> None:
        self._retry_button.setVisible(visible)
        self._continue_button.setVisible(visible)
