from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

NAVIGATION_ITEMS = (
    "Dashboard",
    "Market",
    "Scanner",
    "Analysis",
    "Portfolio",
    "Options",
    "Decision Center",
    "Settings",
)

QUICK_INFO_ITEMS = (
    "Watchlist",
    "Alerts",
    "Calendar",
    "Notes",
)

COCKPIT_STYLE_SHEET = """
QMainWindow, QWidget {
    background: #171717;
    color: #f3f4f6;
    font-size: 14px;
}
QFrame#statusStrip,
QFrame#navigationPanel,
QFrame#workspacePanel,
QFrame#quickInfoPanel {
    background: #222222;
    border: 1px solid #4b5563;
    border-radius: 6px;
}
QLabel#applicationTitle,
QLabel#panelTitle,
QLabel#workspaceTitle {
    font-weight: 700;
}
QListWidget {
    background: transparent;
    border: 0;
    outline: 0;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background: #374151;
}
QSplitter::handle {
    background: #111827;
    width: 4px;
}
"""


class CockpitMainWindow(QMainWindow):
    """Minimal, presentation-only Trading Cockpit application shell."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("cockpitMainWindow")
        self.setWindowTitle("Trading Cockpit")
        self.setMinimumSize(960, 600)
        self.resize(1280, 800)
        self.setStyleSheet(COCKPIT_STYLE_SHEET)
        self.setCentralWidget(self._build_central_widget())

    def _build_central_widget(self) -> QWidget:
        central_widget = QWidget(self)
        central_widget.setObjectName("cockpitCentralWidget")

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self._build_status_strip())
        layout.addWidget(self._build_content_splitter(), 1)

        return central_widget

    def _build_status_strip(self) -> QFrame:
        status_strip = QFrame(self)
        status_strip.setObjectName("statusStrip")

        layout = QHBoxLayout(status_strip)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(18)

        application_title = QLabel("Trading Cockpit", status_strip)
        application_title.setObjectName("applicationTitle")
        layout.addWidget(application_title)
        layout.addStretch(1)
        layout.addWidget(self._status_label("applicationState", "Status: READY"))
        layout.addWidget(self._status_label("environmentState", "Mode: OFFLINE"))
        layout.addWidget(
            self._status_label("connectionState", "Connection: DISCONNECTED")
        )

        return status_strip

    def _status_label(self, object_name: str, text: str) -> QLabel:
        label = QLabel(text, self)
        label.setObjectName(object_name)
        return label

    def _build_content_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("cockpitContentSplitter")
        splitter.setChildrenCollapsible(False)

        navigation_panel = self._build_navigation_panel()
        workspace_panel = self._build_workspace_panel()
        quick_info_panel = self._build_quick_info_panel()

        splitter.addWidget(navigation_panel)
        splitter.addWidget(workspace_panel)
        splitter.addWidget(quick_info_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([190, 820, 240])

        self._navigation.setCurrentRow(0)

        return splitter

    def _build_navigation_panel(self) -> QFrame:
        panel = self._panel("navigationPanel")
        panel.setMinimumWidth(170)
        panel.setMaximumWidth(260)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(self._panel_title("Navigation", panel))

        self._navigation = QListWidget(panel)
        self._navigation.setObjectName("navigationList")
        self._navigation.addItems(NAVIGATION_ITEMS)
        self._navigation.currentTextChanged.connect(self._show_workspace)
        layout.addWidget(self._navigation, 1)

        return panel

    def _build_workspace_panel(self) -> QFrame:
        panel = self._panel("workspacePanel")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        self._workspace_title = self._panel_title("Dashboard", panel)
        self._workspace_title.setObjectName("workspaceTitle")
        layout.addWidget(self._workspace_title)

        self._workspace_placeholder = QLabel(
            "Dashboard workspace placeholder\n"
            "Cockpit widgets will be added as vertical product slices.",
            panel,
        )
        self._workspace_placeholder.setObjectName("workspacePlaceholder")
        self._workspace_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._workspace_placeholder.setWordWrap(True)
        layout.addWidget(self._workspace_placeholder, 1)

        return panel

    def _build_quick_info_panel(self) -> QFrame:
        panel = self._panel("quickInfoPanel")
        panel.setMinimumWidth(200)
        panel.setMaximumWidth(320)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(self._panel_title("Quick Info", panel))

        quick_info = QListWidget(panel)
        quick_info.setObjectName("quickInfoList")
        quick_info.addItems(QUICK_INFO_ITEMS)
        quick_info.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(quick_info, 1)

        return panel

    def _show_workspace(self, navigation_item: str) -> None:
        if not navigation_item:
            return

        self._workspace_title.setText(navigation_item)
        self._workspace_placeholder.setText(
            f"{navigation_item} workspace placeholder\n"
            "Cockpit widgets will be added as vertical product slices."
        )

    def _panel(self, object_name: str) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName(object_name)
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        return panel

    def _panel_title(self, text: str, parent: QWidget) -> QLabel:
        title = QLabel(text, parent)
        title.setObjectName("panelTitle")
        return title
