from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QSplitter

from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.app.main_window import (
    NAVIGATION_ITEMS,
    QUICK_INFO_ITEMS,
    CockpitMainWindow,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    application = create_qt_application([])
    return application


def _list_items(widget: QListWidget) -> tuple[str, ...]:
    return tuple(widget.item(index).text() for index in range(widget.count()))


def test_cockpit_shell_contains_target_layout(
    qt_application: QApplication,
) -> None:
    window = CockpitMainWindow()

    splitter = window.findChild(QSplitter, "cockpitContentSplitter")
    navigation = window.findChild(QListWidget, "navigationList")
    quick_info = window.findChild(QListWidget, "quickInfoList")
    application_state = window.findChild(QLabel, "applicationState")
    environment_state = window.findChild(QLabel, "environmentState")
    connection_state = window.findChild(QLabel, "connectionState")

    assert splitter is not None
    assert splitter.count() == 3
    assert navigation is not None
    assert _list_items(navigation) == NAVIGATION_ITEMS
    assert quick_info is not None
    assert _list_items(quick_info) == QUICK_INFO_ITEMS
    assert application_state is not None
    assert application_state.text() == "Status: READY"
    assert environment_state is not None
    assert environment_state.text() == "Mode: OFFLINE"
    assert connection_state is not None
    assert connection_state.text() == "Connection: DISCONNECTED"

    window.close()


def test_navigation_updates_workspace_title(
    qt_application: QApplication,
) -> None:
    window = CockpitMainWindow()
    navigation = window.findChild(QListWidget, "navigationList")
    workspace_title = window.findChild(QLabel, "workspaceTitle")

    assert navigation is not None
    assert workspace_title is not None

    navigation.setCurrentRow(NAVIGATION_ITEMS.index("Scanner"))
    qt_application.processEvents()

    assert workspace_title.text() == "Scanner"

    window.close()


def test_create_qt_application_reuses_existing_application(
    qt_application: QApplication,
) -> None:
    assert create_qt_application([]) is qt_application
