from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

DEFAULT_PROJECT_ANALYSIS_REPORT_PATH = Path("temp/project-analysis-agent-report.json")
PROJECT_ANALYSIS_HOTSPOT_SECTIONS = (
    "documentation",
    "architecture",
    "trading_safety",
    "runtime_entrypoints",
    "external_interfaces",
    "cicd_workflows",
    "risk_strategy_decisions",
    "cockpit_ui_surfaces",
    "security_secrets",
    "operations_runbooks",
)
HOTSPOT_FIELD_MARKERS = ("hotspot", "violation", "finding", "parse_error")
DEFAULT_HOTSPOT_LIMIT = 12


@dataclass(frozen=True)
class ProjectAnalysisData:
    state: str
    detail: str
    payload: Mapping[str, object] | None = None

    @classmethod
    def unavailable(cls, detail: str) -> ProjectAnalysisData:
        return cls(state="UNAVAILABLE", detail=detail)


def load_project_analysis_data(path: Path) -> ProjectAnalysisData:
    if not path.is_file():
        return ProjectAnalysisData.unavailable(
            f"Project analysis report not found: {path}"
        )

    try:
        raw_payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return ProjectAnalysisData(
            state="ERROR",
            detail=f"Project analysis report could not be loaded: {type(exc).__name__}",
        )

    if not isinstance(raw_payload, dict):
        return ProjectAnalysisData(
            state="ERROR",
            detail="Project analysis report root must be a JSON object.",
        )

    payload = cast(dict[str, object], raw_payload)
    return ProjectAnalysisData(
        state="AVAILABLE",
        detail=f"Source: {path}",
        payload=payload,
    )


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, dict):
        return cast(dict[str, object], value)

    return {}


def _as_items(value: object) -> tuple[object, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(value)

    return ()


def _format_title(value: str) -> str:
    return value.replace("_", " ").title()


def _format_value(value: object) -> str:
    if isinstance(value, str):
        return value

    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)

    return str(value)


def collect_project_dashboard_hotspots(
    payload: Mapping[str, object],
    limit: int = DEFAULT_HOTSPOT_LIMIT,
) -> tuple[str, ...]:
    hotspots: list[str] = []
    quality_gate = _as_mapping(payload.get("quality_gate"))

    for failure in _as_items(quality_gate.get("critical_failures")):
        hotspots.append(f"Quality Gate: {_format_value(failure)}")

    for section_name in PROJECT_ANALYSIS_HOTSPOT_SECTIONS:
        section = _as_mapping(payload.get(section_name))

        for field_name, field_value in section.items():
            if not any(marker in field_name for marker in HOTSPOT_FIELD_MARKERS):
                continue

            for item in _as_items(field_value):
                hotspots.append(
                    f"{_format_title(section_name)} / "
                    f"{_format_title(field_name)}: {_format_value(item)}"
                )

    return tuple(hotspots[:limit])


class ProjectDashboardWidget(QWidget):
    """Read-only cockpit widget for Project Analysis Agent JSON data."""

    def __init__(
        self,
        analysis_data: ProjectAnalysisData,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("projectDashboardWidget")
        self._analysis_data = analysis_data
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("projectDashboardScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget(scroll_area)
        content.setObjectName("projectDashboardContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        content_layout.addLayout(self._build_header(content))

        if self._analysis_data.payload is None:
            content_layout.addWidget(self._build_unavailable_message(content), 1)
        else:
            content_layout.addWidget(self._build_root_label(content))
            content_layout.addLayout(
                self._build_summary_cards(self._analysis_data.payload, content)
            )
            content_layout.addWidget(
                self._build_hotspot_card(self._analysis_data.payload, content),
                1,
            )

        scroll_area.setWidget(content)
        layout.addWidget(scroll_area, 1)

    def _build_header(self, parent: QWidget) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Project Analysis", parent)
        title.setObjectName("projectDashboardWidgetTitle")
        layout.addWidget(title)
        layout.addStretch(1)

        state = QLabel(self._analysis_data.state, parent)
        state.setObjectName("projectDashboardState")
        state.setProperty("analysisState", self._analysis_data.state.lower())
        state.setToolTip(self._analysis_data.detail)
        layout.addWidget(state)

        return layout

    def _build_unavailable_message(self, parent: QWidget) -> QLabel:
        message = QLabel(self._analysis_data.detail, parent)
        message.setObjectName("projectDashboardUnavailableMessage")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        return message

    def _build_root_label(self, parent: QWidget) -> QLabel:
        payload = self._analysis_data.payload or {}
        root = QLabel(f"Project root: {payload.get('root', 'unknown')}", parent)
        root.setObjectName("projectDashboardRoot")
        root.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return root

    def _build_summary_cards(
        self,
        payload: Mapping[str, object],
        parent: QWidget,
    ) -> QGridLayout:
        quality_gate = _as_mapping(payload.get("quality_gate"))
        file_counts = _as_mapping(payload.get("file_counts"))
        safety = _as_mapping(payload.get("safety"))
        quality_status = "PASSED" if quality_gate.get("passed") is True else "FAILED"

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(
            self._build_metric_card(
                "Quality Gate",
                (
                    (
                        "Status",
                        quality_status,
                        "projectDashboardQualityGate",
                    ),
                    (
                        "Critical failures",
                        len(_as_items(quality_gate.get("critical_failures"))),
                        "projectDashboardCriticalFailures",
                    ),
                ),
                parent,
            ),
            0,
            0,
        )
        layout.addWidget(
            self._build_metric_card(
                "Safety",
                (
                    (
                        "Mode",
                        safety.get("mode", "unknown"),
                        "projectDashboardSafetyMode",
                    ),
                    (
                        "Broker access",
                        safety.get("broker_access", "unknown"),
                        "projectDashboardBrokerAccess",
                    ),
                    (
                        "Trading access",
                        safety.get("trading_access", "unknown"),
                        "projectDashboardTradingAccess",
                    ),
                    (
                        "LIVE access",
                        safety.get("live_access", "unknown"),
                        "projectDashboardLiveAccess",
                    ),
                ),
                parent,
            ),
            0,
            1,
        )
        layout.addWidget(
            self._build_metric_card(
                "File Counts",
                (
                    (
                        "Total files",
                        file_counts.get("total_files", 0),
                        "projectDashboardTotalFiles",
                    ),
                    (
                        "Python files",
                        file_counts.get("python_files", 0),
                        "projectDashboardPythonFiles",
                    ),
                    (
                        "Source files",
                        file_counts.get("source_files", 0),
                        "projectDashboardSourceFiles",
                    ),
                    (
                        "Test files",
                        file_counts.get("test_files", 0),
                        "projectDashboardTestFiles",
                    ),
                    (
                        "Documentation files",
                        file_counts.get("documentation_files", 0),
                        "projectDashboardDocumentationFiles",
                    ),
                ),
                parent,
            ),
            1,
            0,
            1,
            2,
        )
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return layout

    def _build_metric_card(
        self,
        title_text: str,
        metrics: tuple[tuple[str, object, str], ...],
        parent: QWidget,
    ) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("projectDashboardCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel(title_text, card)
        title.setObjectName("projectDashboardCardTitle")
        layout.addWidget(title)

        for label_text, value, object_name in metrics:
            row = QHBoxLayout()
            label = QLabel(label_text, card)
            label.setObjectName("projectDashboardMetricLabel")
            row.addWidget(label)
            row.addStretch(1)

            metric_value = QLabel(_format_value(value), card)
            metric_value.setObjectName(object_name)
            row.addWidget(metric_value)
            layout.addLayout(row)

        layout.addStretch(1)
        return card

    def _build_hotspot_card(
        self,
        payload: Mapping[str, object],
        parent: QWidget,
    ) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("projectDashboardCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel("Important Hotspots", card)
        title.setObjectName("projectDashboardCardTitle")
        layout.addWidget(title)

        hotspot_list = QListWidget(card)
        hotspot_list.setObjectName("projectDashboardHotspots")
        hotspot_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hotspots = collect_project_dashboard_hotspots(payload)

        if hotspots:
            hotspot_list.addItems(hotspots)
        else:
            hotspot_list.addItem("No important hotspots reported.")

        layout.addWidget(hotspot_list, 1)
        return card
