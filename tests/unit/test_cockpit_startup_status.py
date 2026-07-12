from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar

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

    assert status_message is not None
    assert status_message.text() == "Preparing startup..."
    assert progress_bar is not None
    assert progress_bar.minimum() == 0
    assert progress_bar.maximum() == 3
    assert progress_bar.value() == 0

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


def test_startup_status_dialog_rejects_invalid_step(
    qt_application: QApplication,
) -> None:
    dialog = StartupStatusDialog()

    with pytest.raises(ValueError, match="Startup step must be between 0 and 3"):
        dialog.update_status("Invalid", 4)

    dialog.close()
