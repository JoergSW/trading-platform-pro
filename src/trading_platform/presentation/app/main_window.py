from __future__ import annotations

from pathlib import Path

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

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
)
from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotService,
)
from trading_platform.application.market_data.market_snapshot_freshness import (
    DEFAULT_MARKET_SNAPSHOT_FRESH_SECONDS,
    DEFAULT_MARKET_SNAPSHOT_STALE_SECONDS,
)
from trading_platform.application.market_data.price_history import (
    PriceHistoryService,
)
from trading_platform.application.scanner.scanner_history_csv_export import (
    ScannerHistoryCsvExportService,
)
from trading_platform.application.scanner.scanner_results import (
    ScannerResults,
    ScannerResultsService,
)
from trading_platform.application.watchlists.session_watchlist import (
    SessionWatchlistService,
)
from trading_platform.presentation.widgets.project_dashboard import ProjectAnalysisData
from trading_platform.presentation.widgets.session_watchlist import (
    SessionWatchlistWidget,
)
from trading_platform.presentation.workspaces.cockpit_workspace import (
    WORKSPACE_PAGE_NAMES,
    CockpitWorkspaceWidget,
)

NAVIGATION_ITEMS = WORKSPACE_PAGE_NAMES

QUICK_INFO_ITEMS = (
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
QLabel#workspaceTitle,
QLabel#workspacePlaceholderTitle,
QLabel#projectDashboardWidgetTitle,
QLabel#projectDashboardCardTitle,
QLabel#marketWorkspaceTitle,
QLabel#marketWorkspaceCardTitle,
QLabel#marketWorkspaceHistoryTitle,
QLabel#scannerWorkspaceTitle,
QLabel#scannerWorkspaceCardTitle,
QLabel#scannerWorkspaceTableTitle,
QLabel#scannerWorkspaceResultDetailsTitle,
QLabel#scannerWorkspaceSymbolHistoryTitle {
    font-weight: 700;
}
QLabel#analysisWorkspaceTitle,
QLabel#analysisWorkspaceCardTitle,
QLabel#analysisPriceHistoryTitle {
    font-weight: 700;
}
QLabel#workspacePlaceholderTitle,
QLabel#projectDashboardWidgetTitle,
QLabel#marketWorkspaceTitle,
QLabel#marketWorkspaceHistoryTitle,
QLabel#scannerWorkspaceTitle,
QLabel#scannerWorkspaceTableTitle,
QLabel#scannerWorkspaceResultDetailsTitle,
QLabel#scannerWorkspaceSymbolHistoryTitle {
    font-size: 18px;
}
QLabel#analysisWorkspaceTitle {
    font-size: 18px;
}
QLabel#workspacePlaceholderDescription {
    color: #9ca3af;
}
QPushButton#projectDashboardRefreshButton,
QPushButton#marketWorkspaceRefreshButton,
QPushButton#scannerWorkspaceRefreshButton,
QPushButton#scannerWorkspaceClearFiltersButton,
QPushButton#scannerWorkspaceExportSelectedHistoryButton,
QPushButton#scannerWorkspaceExportSessionHistoryButton {
    background: #374151;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton#projectDashboardRefreshButton:hover,
QPushButton#marketWorkspaceRefreshButton:hover,
QPushButton#scannerWorkspaceRefreshButton:hover,
QPushButton#scannerWorkspaceClearFiltersButton:hover,
QPushButton#scannerWorkspaceExportSelectedHistoryButton:hover,
QPushButton#scannerWorkspaceExportSessionHistoryButton:hover {
    background: #4b5563;
}
QPushButton#projectDashboardRefreshButton:disabled,
QPushButton#marketWorkspaceRefreshButton:disabled,
QPushButton#scannerWorkspaceRefreshButton:disabled,
QPushButton#scannerWorkspaceClearFiltersButton:disabled,
QPushButton#scannerWorkspaceExportSelectedHistoryButton:disabled,
QPushButton#scannerWorkspaceExportSessionHistoryButton:disabled {
    color: #6b7280;
    background: #27272a;
}
QLabel#projectDashboardState {
    background: #374151;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#projectDashboardState[analysisState="available"] {
    background: #14532d;
}
QLabel#projectDashboardState[analysisState="error"] {
    background: #7f1d1d;
}
QLabel#projectDashboardState[analysisState="unavailable"] {
    background: #374151;
}
QLabel#marketWorkspaceState {
    background: #374151;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#marketWorkspaceState[marketState="ready"] {
    background: #14532d;
}
QLabel#marketWorkspaceState[marketState="no_data"] {
    background: #78350f;
}
QLabel#marketWorkspaceState[marketState="unavailable"] {
    background: #374151;
}
QLabel#marketWorkspaceState[marketState="stale"] {
    background: #7c2d12;
}
QLabel#marketWorkspaceRefreshStatus {
    background: #27272a;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#marketWorkspaceRefreshStatus[refreshState="success"] {
    background: #14532d;
}
QLabel#marketWorkspaceRefreshStatus[refreshState="unchanged"] {
    background: #374151;
}
QLabel#marketWorkspaceRefreshStatus[refreshState="loading"] {
    background: #1e3a8a;
}
QLabel#marketWorkspaceRefreshStatus[refreshState="error"] {
    background: #7f1d1d;
}
QLabel#marketWorkspaceRefreshStatus[refreshState="unavailable"] {
    background: #374151;
}
QLabel#marketWorkspaceFreshness {
    background: #374151;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#marketWorkspaceFreshness[freshnessState="fresh"] {
    background: #14532d;
}
QLabel#marketWorkspaceFreshness[freshnessState="aging"] {
    background: #78350f;
}
QLabel#marketWorkspaceFreshness[freshnessState="stale"] {
    background: #7f1d1d;
}
QLabel#marketWorkspaceFreshness[freshnessState="unavailable"] {
    background: #374151;
}
QLabel#scannerWorkspaceState {
    background: #374151;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#scannerWorkspaceState[scannerState="ready"] {
    background: #14532d;
}
QLabel#scannerWorkspaceState[scannerState="no_data"] {
    background: #78350f;
}
QLabel#scannerWorkspaceState[scannerState="unavailable"] {
    background: #374151;
}
QLabel#scannerWorkspaceState[scannerState="stale"] {
    background: #7c2d12;
}
QLabel#scannerWorkspaceRefreshStatus {
    background: #27272a;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#scannerWorkspaceRefreshStatus[refreshState="success"] {
    background: #14532d;
}
QLabel#scannerWorkspaceRefreshStatus[refreshState="unchanged"] {
    background: #374151;
}
QLabel#scannerWorkspaceRefreshStatus[refreshState="loading"] {
    background: #1e3a8a;
}
QLabel#scannerWorkspaceRefreshStatus[refreshState="error"] {
    background: #7f1d1d;
}
QLabel#scannerWorkspaceRefreshStatus[refreshState="unavailable"] {
    background: #374151;
}
QLabel#scannerWorkspaceHistoryExportStatus {
    background: #27272a;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#scannerWorkspaceHistoryExportStatus[exportState="success"] {
    background: #14532d;
}
QLabel#scannerWorkspaceHistoryExportStatus[exportState="error"] {
    background: #7f1d1d;
}
QLabel#scannerWorkspaceHistoryExportStatus[exportState="cancelled"],
QLabel#scannerWorkspaceHistoryExportStatus[exportState="ready"],
QLabel#scannerWorkspaceHistoryExportStatus[exportState="unavailable"] {
    background: #374151;
}
QLabel#analysisWorkspaceState {
    background: #374151;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#analysisWorkspaceState[instrumentContextState="selected"] {
    background: #14532d;
}
QLabel#analysisWorkspaceState[instrumentContextState="no_selection"] {
    background: #374151;
}
QLabel#analysisPriceHistoryState {
    background: #374151;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#analysisPriceHistoryState[priceHistoryState="ready"] {
    background: #14532d;
}
QLabel#analysisPriceHistoryState[priceHistoryState="error"] {
    background: #7f1d1d;
}
QLabel#analysisPriceHistoryState[priceHistoryState="loading"] {
    background: #1e3a8a;
}
QLabel[metricDeltaDirection="positive"] {
    color: #86efac;
}
QLabel[metricDeltaDirection="negative"] {
    color: #fca5a5;
}
QLabel[metricDeltaDirection="unchanged"],
QLabel[metricDeltaDirection="unavailable"] {
    color: #9ca3af;
}
QFrame#projectDashboardCard,
QFrame#marketWorkspaceCard,
QFrame#scannerWorkspaceCard {
    background: #1b1f24;
    border: 1px solid #374151;
    border-radius: 6px;
}
QFrame#analysisWorkspaceCard,
QFrame#analysisPriceHistoryPanel {
    background: #1b1f24;
    border: 1px solid #374151;
    border-radius: 6px;
}
QFrame#scannerWorkspaceFilters,
QFrame#scannerWorkspaceResultDetails {
    background: #1b1f24;
    border: 1px solid #374151;
    border-radius: 6px;
}
QLineEdit#scannerWorkspaceSymbolFilter,
QLineEdit#scannerWorkspaceMinimumScoreFilter,
QComboBox#scannerWorkspaceSignalFilter {
    background: #171717;
    color: #f3f4f6;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 5px 7px;
    min-width: 120px;
}
QComboBox#scannerWorkspaceSignalFilter QAbstractItemView {
    background: #171717;
    color: #f3f4f6;
    selection-background-color: #374151;
}
QLabel#scannerWorkspaceFilterLabel,
QLabel#scannerWorkspaceResultDetailsLabel {
    color: #d1d5db;
    font-weight: 700;
}
QLabel#scannerWorkspaceSelectedSymbol,
QLabel#scannerWorkspaceSelectedSignal,
QLabel#scannerWorkspaceSelectedScore,
QLabel#scannerWorkspaceSelectedObservedAt,
QLabel#scannerWorkspaceSelectedSource,
QLabel#scannerWorkspaceSelectedChange {
    color: #f3f4f6;
}
QLabel#projectDashboardMetricLabel,
QLabel#projectDashboardRoot,
QLabel#projectDashboardSourcePath,
QLabel#projectDashboardLastSuccessfulLoad,
QLabel#projectDashboardUnavailableMessage,
QLabel#marketWorkspaceDetail,
QLabel#marketWorkspaceCardTitle,
QLabel#marketWorkspaceHistoryEmpty,
QLabel#marketWorkspaceSafetyNote,
QLabel#scannerWorkspaceDetail,
QLabel#scannerWorkspaceCardTitle,
QLabel#scannerWorkspaceEmpty,
QLabel#scannerWorkspaceSymbolHistoryEmpty,
QLabel#scannerWorkspaceHistoryExportDetail,
QLabel#scannerWorkspaceSafetyNote {
    color: #9ca3af;
}
QLabel#analysisWorkspaceDetail,
QLabel#analysisWorkspaceSafetyNote,
QLabel#analysisPriceHistoryDetail,
QLabel#analysisPriceHistoryMetadataTitle {
    color: #9ca3af;
}
QListWidget {
    background: transparent;
    border: 0;
    outline: 0;
}
QListWidget#projectDashboardHotspots {
    background: #171717;
    border: 1px solid #374151;
    border-radius: 4px;
}
QTableWidget#marketWorkspaceHistoryTable {
    background: #171717;
    border: 1px solid #374151;
    border-radius: 4px;
    gridline-color: #374151;
}
QTableWidget#marketWorkspaceHistoryTable QHeaderView::section {
    background: #27272a;
    color: #d1d5db;
    border: 0;
    border-right: 1px solid #374151;
    border-bottom: 1px solid #374151;
    padding: 6px;
    font-weight: 700;
}
QTableWidget#marketWorkspaceHistoryTable::item {
    padding: 5px;
}
QTableWidget#scannerWorkspaceTable {
    background: #171717;
    border: 1px solid #374151;
    border-radius: 4px;
    gridline-color: #374151;
}
QTableWidget#scannerWorkspaceTable QHeaderView::section {
    background: #27272a;
    color: #d1d5db;
    border: 0;
    border-right: 1px solid #374151;
    border-bottom: 1px solid #374151;
    padding: 6px;
    font-weight: 700;
}
QTableWidget#scannerWorkspaceTable::item {
    padding: 5px;
}
QTableWidget#scannerWorkspaceSymbolHistoryTable {
    background: #171717;
    border: 1px solid #374151;
    border-radius: 4px;
    gridline-color: #374151;
}
QTableWidget#scannerWorkspaceSymbolHistoryTable QHeaderView::section {
    background: #27272a;
    color: #d1d5db;
    border: 0;
    border-right: 1px solid #374151;
    border-bottom: 1px solid #374151;
    padding: 6px;
    font-weight: 700;
}
QTableWidget#scannerWorkspaceSymbolHistoryTable::item {
    padding: 5px;
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
QLabel#sessionWatchlistTitle,
QLabel#quickInfoPlannedTitle {
    font-weight: 700;
}
QPushButton#scannerWorkspaceAddToWatchlistButton,
QPushButton#sessionWatchlistRemoveButton,
QPushButton#analysisPriceHistoryRefreshButton {
    background: #374151;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton#scannerWorkspaceAddToWatchlistButton:hover,
QPushButton#sessionWatchlistRemoveButton:hover,
QPushButton#analysisPriceHistoryRefreshButton:hover {
    background: #4b5563;
}
QPushButton#scannerWorkspaceAddToWatchlistButton:disabled,
QPushButton#sessionWatchlistRemoveButton:disabled,
QPushButton#analysisPriceHistoryRefreshButton:disabled {
    color: #6b7280;
    background: #27272a;
}
QLabel#scannerWorkspaceWatchlistStatus,
QLabel#sessionWatchlistState,
QLabel#sessionWatchlistActionStatus {
    background: #374151;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 700;
}
QLabel#scannerWorkspaceWatchlistStatus[watchlistState="success"] {
    background: #14532d;
}
QLabel#sessionWatchlistEmpty,
QLabel#sessionWatchlistDetail {
    color: #9ca3af;
}
QListWidget#sessionWatchlistList {
    background: #171717;
    border: 1px solid #374151;
    border-radius: 4px;
}
"""


class CockpitMainWindow(QMainWindow):
    """Minimal, presentation-only Trading Cockpit application shell."""

    def __init__(
        self,
        project_analysis: ProjectAnalysisData | None = None,
        project_analysis_report_path: Path | None = None,
        market_snapshot: MarketSnapshot | None = None,
        market_snapshot_service: MarketSnapshotService | None = None,
        market_snapshot_auto_refresh_seconds: int | None = None,
        market_snapshot_fresh_seconds: int = DEFAULT_MARKET_SNAPSHOT_FRESH_SECONDS,
        market_snapshot_stale_seconds: int = DEFAULT_MARKET_SNAPSHOT_STALE_SECONDS,
        price_history_service: PriceHistoryService | None = None,
        scanner_results: ScannerResults | None = None,
        scanner_results_service: ScannerResultsService | None = None,
        scanner_results_auto_refresh_seconds: int | None = None,
        scanner_history_csv_export_service: ScannerHistoryCsvExportService
        | None = None,
        instrument_context_service: InstrumentContextService | None = None,
        session_watchlist_service: SessionWatchlistService | None = None,
    ) -> None:
        super().__init__()
        self._project_analysis_report_path = project_analysis_report_path
        self._project_analysis = project_analysis or ProjectAnalysisData.unavailable(
            "No Project Analysis Agent report is available."
        )
        self._market_snapshot = market_snapshot or MarketSnapshot.unavailable()
        self._market_snapshot_service = market_snapshot_service
        self._market_snapshot_auto_refresh_seconds = (
            market_snapshot_auto_refresh_seconds
        )
        self._market_snapshot_fresh_seconds = market_snapshot_fresh_seconds
        self._market_snapshot_stale_seconds = market_snapshot_stale_seconds
        self._price_history_service = price_history_service
        self._scanner_results = scanner_results or ScannerResults.unavailable()
        self._scanner_results_service = scanner_results_service
        self._scanner_results_auto_refresh_seconds = (
            scanner_results_auto_refresh_seconds
        )
        self._scanner_history_csv_export_service = scanner_history_csv_export_service
        self._instrument_context_service = (
            instrument_context_service or InstrumentContextService()
        )
        self._session_watchlist_service = (
            session_watchlist_service or SessionWatchlistService()
        )
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
        layout.setContentsMargins(0, 0, 0, 0)

        self._workspace = CockpitWorkspaceWidget(
            self._project_analysis,
            self._project_analysis_report_path,
            panel,
            market_snapshot=self._market_snapshot,
            market_snapshot_service=self._market_snapshot_service,
            market_snapshot_auto_refresh_seconds=(
                self._market_snapshot_auto_refresh_seconds
            ),
            market_snapshot_fresh_seconds=self._market_snapshot_fresh_seconds,
            market_snapshot_stale_seconds=self._market_snapshot_stale_seconds,
            price_history_service=self._price_history_service,
            scanner_results=self._scanner_results,
            scanner_results_service=self._scanner_results_service,
            scanner_results_auto_refresh_seconds=(
                self._scanner_results_auto_refresh_seconds
            ),
            scanner_history_csv_export_service=(
                self._scanner_history_csv_export_service
            ),
            instrument_context_service=self._instrument_context_service,
            session_watchlist_service=self._session_watchlist_service,
        )
        layout.addWidget(self._workspace)
        return panel

    def _build_quick_info_panel(self) -> QFrame:
        panel = self._panel("quickInfoPanel")
        panel.setMinimumWidth(200)
        panel.setMaximumWidth(320)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(self._panel_title("Quick Info", panel))

        watchlist_title = QLabel("Watchlist", panel)
        watchlist_title.setObjectName("sessionWatchlistTitle")
        layout.addWidget(watchlist_title)

        watchlist = SessionWatchlistWidget(
            self._session_watchlist_service,
            self._instrument_context_service,
            panel,
        )
        layout.addWidget(watchlist, 2)

        planned_title = QLabel("Planned", panel)
        planned_title.setObjectName("quickInfoPlannedTitle")
        layout.addWidget(planned_title)

        quick_info = QListWidget(panel)
        quick_info.setObjectName("quickInfoList")
        quick_info.addItems(QUICK_INFO_ITEMS)
        quick_info.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(quick_info, 1)

        return panel

    def _show_workspace(self, navigation_item: str) -> None:
        if navigation_item:
            self._workspace.show_page(navigation_item)

    def _panel(self, object_name: str) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName(object_name)
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        return panel

    def _panel_title(self, text: str, parent: QWidget) -> QLabel:
        title = QLabel(text, parent)
        title.setObjectName("panelTitle")
        return title
