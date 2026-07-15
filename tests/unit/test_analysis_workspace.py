from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication, QLabel

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
    InstrumentContextState,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.workspaces.analysis_workspace import (
    AnalysisWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


def _label_text(widget: AnalysisWorkspaceWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def test_analysis_workspace_shows_no_selection_initially(
    qt_application: QApplication,
) -> None:
    service = InstrumentContextService()
    widget = AnalysisWorkspaceWidget(service)

    assert widget.instrument_context.state is InstrumentContextState.NO_SELECTION
    assert _label_text(widget, "analysisWorkspaceState") == "NO SELECTION"
    assert _label_text(widget, "analysisWorkspaceActiveSymbol") == "NO SELECTION"
    assert _label_text(widget, "analysisWorkspaceContextSource") == "NOT AVAILABLE"

    widget.close()


def test_analysis_workspace_follows_selected_instrument_context(
    qt_application: QApplication,
) -> None:
    service = InstrumentContextService()
    widget = AnalysisWorkspaceWidget(service)

    service.select_instrument("AAPL", "Scanner")
    qt_application.processEvents()

    assert _label_text(widget, "analysisWorkspaceState") == "SELECTED"
    assert _label_text(widget, "analysisWorkspaceActiveSymbol") == "AAPL"
    assert _label_text(widget, "analysisWorkspaceContextSource") == "Scanner"

    service.clear_instrument("Scanner")
    qt_application.processEvents()

    assert _label_text(widget, "analysisWorkspaceState") == "NO SELECTION"
    assert _label_text(widget, "analysisWorkspaceActiveSymbol") == "NO SELECTION"
    assert _label_text(widget, "analysisWorkspaceContextSource") == "Scanner"

    widget.close()
