from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QProgressBar,
    QPushButton,
)

from trading_platform.presentation.app.main import (
    _show_startup_step,
    create_qt_application,
)
from trading_platform.presentation.app.startup_status import StartupStatusDialog


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


def test_startup_status_dialog_has_initial_state(
    qt_application: QApplication,
) -> None:
    dialog = StartupStatusDialog()
    status_message = dialog.findChild(QLabel, "startupStatusMessage")
    progress_bar = dialog.findChild(QProgressBar, "startupProgressBar")
    retry_button = dialog.findChild(QPushButton, "startupRetryButton")
    continue_button = dialog.findChild(QPushButton, "startupContinueButton")

    assert status_message is not None
    assert status_message.text() == "Preparing startup..."
    assert progress_bar is not None
    assert progress_bar.minimum() == 0
    assert progress_bar.maximum() == 3
    assert progress_bar.value() == 0
    assert retry_button is not None
    assert not retry_button.isVisible()
    assert continue_button is not None
    assert not continue_button.isVisible()

    dialog.close()


def test_show_startup_step_displays_current_operation(
    qt_application: QApplication,
) -> None:
    dialog = StartupStatusDialog()

    _show_startup_step(
        qt_application,
        dialog,
        "Generating Project Analysis report...",
        2,
    )

    status_message = dialog.findChild(QLabel, "startupStatusMessage")
    progress_bar = dialog.findChild(QProgressBar, "startupProgressBar")

    assert dialog.isVisible()
    assert status_message is not None
    assert status_message.text() == "Generating Project Analysis report..."
    assert progress_bar is not None
    assert progress_bar.value() == 2

    dialog.close()


def test_startup_status_dialog_exposes_error_actions(
    qt_application: QApplication,
) -> None:
    dialog = StartupStatusDialog()
    retry_requested = False
    continue_requested = False

    def record_retry() -> None:
        nonlocal retry_requested
        retry_requested = True

    def record_continue() -> None:
        nonlocal continue_requested
        continue_requested = True

    dialog.retry_requested.connect(record_retry)
    dialog.continue_requested.connect(record_continue)
    dialog.show()
    dialog.show_error("Project Analysis report generation failed.")

    status_message = dialog.findChild(QLabel, "startupStatusMessage")
    retry_button = dialog.findChild(QPushButton, "startupRetryButton")
    continue_button = dialog.findChild(QPushButton, "startupContinueButton")

    assert status_message is not None
    assert status_message.text() == (
        "Startup failed: Project Analysis report generation failed."
    )
    assert retry_button is not None
    assert retry_button.isVisible()
    assert continue_button is not None
    assert continue_button.isVisible()

    retry_button.click()
    continue_button.click()

    assert retry_requested
    assert continue_requested

    dialog.close()


def test_status_update_hides_error_actions(
    qt_application: QApplication,
) -> None:
    dialog = StartupStatusDialog()
    dialog.show()
    dialog.show_error("Controlled error.")

    dialog.update_status("Generating Project Analysis report...", 2)

    retry_button = dialog.findChild(QPushButton, "startupRetryButton")
    continue_button = dialog.findChild(QPushButton, "startupContinueButton")

    assert retry_button is not None
    assert not retry_button.isVisible()
    assert continue_button is not None
    assert not continue_button.isVisible()

    dialog.close()


def test_startup_status_dialog_rejects_invalid_step(
    qt_application: QApplication,
) -> None:
    dialog = StartupStatusDialog()

    with pytest.raises(ValueError, match="Startup step must be between 0 and 3"):
        dialog.update_status("Invalid", 4)

    dialog.close()
