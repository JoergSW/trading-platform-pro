from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from trading_platform.presentation.widgets.project_dashboard import (
    ProjectAnalysisData,
    ProjectDashboardWidget,
)
from trading_platform.presentation.workspaces.market_workspace import (
    MarketWorkspaceWidget,
)

PLACEHOLDER_WORKSPACE_PAGES = (
    (
        "Scanner",
        "scannerWorkspacePage",
        "Scanner workflows will be added as a dedicated vertical product slice.",
    ),
    (
        "Analysis",
        "analysisWorkspacePage",
        (
            "Instrument and strategy analysis will be added as a dedicated "
            "vertical product slice."
        ),
    ),
    (
        "Portfolio",
        "portfolioWorkspacePage",
        (
            "Portfolio and position monitoring will be added as a dedicated "
            "vertical product slice."
        ),
    ),
    (
        "Options",
        "optionsWorkspacePage",
        (
            "Options analysis and strategy tools will be added as a dedicated "
            "vertical product slice."
        ),
    ),
    (
        "Decision Center",
        "decisionCenterWorkspacePage",
        (
            "Trading decision workflows will be added as a dedicated "
            "vertical product slice."
        ),
    ),
    (
        "Settings",
        "settingsWorkspacePage",
        "Cockpit configuration will be added as a dedicated vertical product slice.",
    ),
)

WORKSPACE_PAGE_NAMES = (
    "Dashboard",
    "Market",
    *(page_name for page_name, _, _ in PLACEHOLDER_WORKSPACE_PAGES),
)


class WorkspacePlaceholderPage(QWidget):
    """Presentation-only placeholder for one future cockpit product slice."""

    def __init__(
        self,
        page_name: str,
        description: str,
        object_name: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.addStretch(1)

        title = QLabel(f"{page_name} workspace", self)
        title.setObjectName("workspacePlaceholderTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        detail = QLabel(description, self)
        detail.setObjectName("workspacePlaceholderDescription")
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setWordWrap(True)
        layout.addWidget(detail)

        layout.addStretch(1)


class CockpitWorkspaceWidget(QWidget):
    """Owns cockpit workspace pages and deterministic navigation routing."""

    def __init__(
        self,
        project_analysis: ProjectAnalysisData,
        project_analysis_report_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("cockpitWorkspaceWidget")
        self._pages: dict[str, QWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        self._title = QLabel("Dashboard", self)
        self._title.setObjectName("workspaceTitle")
        layout.addWidget(self._title)

        self._stack = QStackedWidget(self)
        self._stack.setObjectName("workspaceStack")
        layout.addWidget(self._stack, 1)

        dashboard = ProjectDashboardWidget(
            project_analysis,
            project_analysis_report_path,
            self._stack,
        )
        self._register_page("Dashboard", dashboard)
        self._register_page("Market", MarketWorkspaceWidget(parent=self._stack))

        for page_name, object_name, description in PLACEHOLDER_WORKSPACE_PAGES:
            self._register_page(
                page_name,
                WorkspacePlaceholderPage(
                    page_name,
                    description,
                    object_name,
                    self._stack,
                ),
            )

        self.show_page("Dashboard")

    @property
    def page_names(self) -> tuple[str, ...]:
        return tuple(self._pages)

    def page(self, page_name: str) -> QWidget | None:
        return self._pages.get(page_name)

    def show_page(self, page_name: str) -> bool:
        page = self._pages.get(page_name)
        if page is None:
            return False

        self._title.setText(page_name)
        self._stack.setCurrentWidget(page)
        return True

    def _register_page(self, page_name: str, page: QWidget) -> None:
        self._pages[page_name] = page
        self._stack.addWidget(page)
