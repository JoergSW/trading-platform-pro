from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
    InstrumentContextState,
)
from trading_platform.application.portfolio.portfolio_pnl import (
    PortfolioPnlResult,
    summarize_portfolio_pnl,
)
from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotService,
)
from trading_platform.application.risk.portfolio_exposure import (
    PortfolioExposureResult,
    summarize_portfolio_exposure,
)
from trading_platform.application.trading_candidate_notes import (
    TradingCandidateNoteAddResult,
    TradingCandidateNotes,
    TradingCandidateNoteService,
)
from trading_platform.application.trading_candidate_tags import (
    TradingCandidateTagAddResult,
    TradingCandidateTagRemoveResult,
    TradingCandidateTags,
    TradingCandidateTagService,
    TradingCandidateTagsState,
)
from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateCollection,
    TradingCandidateCollectionListener,
    TradingCandidateCollectionState,
    TradingCandidateReviewResult,
    TradingCandidateService,
)
from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionAcceptanceResult,
    TradingDecisionDraftCreateResult,
    TradingDecisionDraftLoadResult,
    TradingDecisionHistory,
    TradingDecisionHistoryState,
    TradingDecisionService,
)
from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioPosition,
    PortfolioSnapshot,
)
from trading_platform.domain.trading_candidate_notes.trading_candidate_note import (
    TradingCandidateNote,
)
from trading_platform.domain.trading_candidate_tags import TradingCandidateTag
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateStatus,
)
from trading_platform.domain.trading_decisions.trading_decision import (
    TradingDecision,
    TradingDecisionStatus,
)

DECISION_CENTER_CONTEXT_SOURCE = "Decision Center"


class DecisionCenterWorkspaceWidget(QWidget):
    """Display candidates and explicitly create traceable decision drafts."""

    def __init__(
        self,
        instrument_context_service: InstrumentContextService,
        parent: QWidget | None = None,
        *,
        trading_candidate_service: TradingCandidateService | None = None,
        trading_candidate_note_service: TradingCandidateNoteService | None = None,
        trading_candidate_tag_service: TradingCandidateTagService | None = None,
        trading_decision_service: TradingDecisionService | None = None,
        portfolio_snapshot: PortfolioSnapshotResult | None = None,
        portfolio_snapshot_service: PortfolioSnapshotService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("decisionCenterWorkspaceWidget")
        self._instrument_context_service = instrument_context_service
        self._trading_candidate_service = trading_candidate_service
        self._trading_candidate_note_service = trading_candidate_note_service
        self._trading_candidate_tag_service = trading_candidate_tag_service
        self._trading_decision_service = trading_decision_service
        if portfolio_snapshot is not None and not isinstance(
            portfolio_snapshot,
            PortfolioSnapshotResult,
        ):
            raise TypeError("portfolio_snapshot must be PortfolioSnapshotResult")
        self._portfolio_result = (
            portfolio_snapshot or PortfolioSnapshotResult.unavailable()
        )
        self._portfolio_snapshot_service = portfolio_snapshot_service
        self._portfolio_refresh_pending = False
        self._candidates: tuple[TradingCandidate, ...] = ()
        self._selected_candidate_id: str | None = None
        self._selected_decision: TradingDecision | None = None
        self._candidate_notes: tuple[TradingCandidateNote, ...] = ()
        self._candidate_tags: tuple[TradingCandidateTag, ...] = ()
        self._candidate_tags_state = TradingCandidateTagsState.UNAVAILABLE
        self._decision_history: tuple[TradingDecision, ...] = ()
        self._selected_history_decision_id: str | None = None
        self._collection_listener: TradingCandidateCollectionListener = (
            self._on_collection_changed
        )

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setObjectName("decisionCenterScrollArea")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_content = QWidget(self._scroll_area)
        scroll_content.setObjectName("decisionCenterScrollContent")
        scroll_content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self._scroll_area.setWidget(scroll_content)
        root_layout.addWidget(self._scroll_area)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)

        title = QLabel("Decision Center", self)
        title.setObjectName("decisionCenterWorkspaceTitle")
        header.addWidget(title)
        header.addStretch(1)

        self._refresh_button = QPushButton("Refresh", self)
        self._refresh_button.setObjectName("decisionCenterRefreshButton")
        self._refresh_button.clicked.connect(self.refresh_candidates)
        header.addWidget(self._refresh_button)

        self._state_label = QLabel(self)
        self._state_label.setObjectName("decisionCenterState")
        header.addWidget(self._state_label)
        layout.addLayout(header)

        candidate_panel = QFrame(self)
        candidate_panel.setObjectName("decisionCenterCandidatePanel")
        candidate_layout = QVBoxLayout(candidate_panel)
        candidate_layout.setContentsMargins(14, 12, 14, 14)
        candidate_layout.setSpacing(10)

        review_actions = QHBoxLayout()
        review_actions.setContentsMargins(0, 0, 0, 0)
        review_actions.setSpacing(8)

        self._review_status_label = QLabel(self)
        self._review_status_label.setObjectName("decisionCenterReviewStatus")
        review_actions.addWidget(self._review_status_label)
        review_actions.addStretch(1)

        self._start_review_button = QPushButton("Start Review", candidate_panel)
        self._start_review_button.setObjectName("decisionCenterStartReviewButton")
        self._start_review_button.clicked.connect(self._start_review)
        review_actions.addWidget(self._start_review_button)

        self._reject_button = QPushButton("Reject", candidate_panel)
        self._reject_button.setObjectName("decisionCenterRejectButton")
        self._reject_button.clicked.connect(self._reject)
        review_actions.addWidget(self._reject_button)

        self._archive_button = QPushButton("Archive", candidate_panel)
        self._archive_button.setObjectName("decisionCenterArchiveButton")
        self._archive_button.clicked.connect(self._archive)
        review_actions.addWidget(self._archive_button)
        candidate_layout.addLayout(review_actions)

        self._detail_label = QLabel(candidate_panel)
        self._detail_label.setObjectName("decisionCenterDetail")
        self._detail_label.setWordWrap(True)
        candidate_layout.addWidget(self._detail_label)

        self._table = QTableWidget(candidate_panel)
        self._table.setObjectName("decisionCenterCandidateTable")
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ("Symbol", "Origin", "Status", "Created UTC", "Updated UTC")
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.itemSelectionChanged.connect(self._publish_selected_candidate)
        candidate_layout.addWidget(self._table, 1)
        layout.addWidget(candidate_panel, 1)

        tags_panel = QFrame(self)
        tags_panel.setObjectName("decisionCenterCandidateTagsPanel")
        tags_layout = QVBoxLayout(tags_panel)
        tags_layout.setContentsMargins(14, 12, 14, 14)
        tags_layout.setSpacing(8)

        tags_header = QHBoxLayout()
        tags_title = QLabel("Candidate Tags", tags_panel)
        tags_title.setObjectName("decisionCenterCandidateTagsTitle")
        tags_header.addWidget(tags_title)
        tags_header.addStretch(1)
        self._candidate_tags_state_label = QLabel(tags_panel)
        self._candidate_tags_state_label.setObjectName(
            "decisionCenterCandidateTagsState"
        )
        tags_header.addWidget(self._candidate_tags_state_label)
        self._candidate_tags_refresh_button = QPushButton(
            "Refresh Candidate Tags",
            tags_panel,
        )
        self._candidate_tags_refresh_button.setObjectName(
            "decisionCenterCandidateTagsRefreshButton"
        )
        self._candidate_tags_refresh_button.clicked.connect(self.refresh_candidate_tags)
        tags_header.addWidget(self._candidate_tags_refresh_button)
        tags_layout.addLayout(tags_header)

        self._candidate_tags_detail_label = QLabel(tags_panel)
        self._candidate_tags_detail_label.setObjectName(
            "decisionCenterCandidateTagsDetail"
        )
        self._candidate_tags_detail_label.setWordWrap(True)
        tags_layout.addWidget(self._candidate_tags_detail_label)

        self._candidate_tags_list = QListWidget(tags_panel)
        self._candidate_tags_list.setObjectName("decisionCenterCandidateTagsList")
        self._candidate_tags_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._candidate_tags_list.setMinimumHeight(120)
        self._candidate_tags_list.itemSelectionChanged.connect(
            self._update_candidate_tag_actions
        )
        tags_layout.addWidget(self._candidate_tags_list)

        tag_actions = QHBoxLayout()
        tag_actions.setContentsMargins(0, 0, 0, 0)
        tag_actions.setSpacing(8)
        self._candidate_tag_input = QLineEdit(tags_panel)
        self._candidate_tag_input.setObjectName("decisionCenterCandidateTagInput")
        self._candidate_tag_input.setPlaceholderText("Add a normalized Candidate Tag.")
        self._candidate_tag_input.textChanged.connect(
            self._update_candidate_tag_actions
        )
        tag_actions.addWidget(self._candidate_tag_input, 1)
        self._candidate_tag_add_button = QPushButton("Add Tag", tags_panel)
        self._candidate_tag_add_button.setObjectName(
            "decisionCenterCandidateTagAddButton"
        )
        self._candidate_tag_add_button.clicked.connect(self._add_candidate_tag)
        tag_actions.addWidget(self._candidate_tag_add_button)
        self._candidate_tag_remove_button = QPushButton("Remove Tag", tags_panel)
        self._candidate_tag_remove_button.setObjectName(
            "decisionCenterCandidateTagRemoveButton"
        )
        self._candidate_tag_remove_button.clicked.connect(self._remove_candidate_tag)
        tag_actions.addWidget(self._candidate_tag_remove_button)
        tags_layout.addLayout(tag_actions)
        layout.addWidget(tags_panel)

        notes_panel = QFrame(self)
        notes_panel.setObjectName("decisionCenterCandidateNotesPanel")
        notes_layout = QVBoxLayout(notes_panel)
        notes_layout.setContentsMargins(14, 12, 14, 14)
        notes_layout.setSpacing(8)

        notes_header = QHBoxLayout()
        notes_title = QLabel("Candidate Notes", notes_panel)
        notes_title.setObjectName("decisionCenterCandidateNotesTitle")
        notes_header.addWidget(notes_title)
        notes_header.addStretch(1)
        self._candidate_notes_state_label = QLabel(notes_panel)
        self._candidate_notes_state_label.setObjectName(
            "decisionCenterCandidateNotesState"
        )
        notes_header.addWidget(self._candidate_notes_state_label)
        self._candidate_notes_refresh_button = QPushButton(
            "Refresh Candidate Notes",
            notes_panel,
        )
        self._candidate_notes_refresh_button.setObjectName(
            "decisionCenterCandidateNotesRefreshButton"
        )
        self._candidate_notes_refresh_button.clicked.connect(
            self.refresh_candidate_notes
        )
        notes_header.addWidget(self._candidate_notes_refresh_button)
        notes_layout.addLayout(notes_header)

        self._candidate_notes_detail_label = QLabel(notes_panel)
        self._candidate_notes_detail_label.setObjectName(
            "decisionCenterCandidateNotesDetail"
        )
        self._candidate_notes_detail_label.setWordWrap(True)
        notes_layout.addWidget(self._candidate_notes_detail_label)

        self._candidate_notes_table = QTableWidget(notes_panel)
        self._candidate_notes_table.setObjectName("decisionCenterCandidateNotesTable")
        self._candidate_notes_table.setColumnCount(2)
        self._candidate_notes_table.setHorizontalHeaderLabels(
            ("Created UTC", "Note ID")
        )
        self._candidate_notes_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._candidate_notes_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._candidate_notes_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._candidate_notes_table.setMinimumHeight(150)
        self._candidate_notes_table.verticalHeader().setVisible(False)
        self._candidate_notes_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )
        self._candidate_notes_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self._candidate_notes_table.itemSelectionChanged.connect(
            self._render_selected_candidate_note
        )
        notes_layout.addWidget(self._candidate_notes_table)

        self._candidate_note_selection_label = QLabel(notes_panel)
        self._candidate_note_selection_label.setObjectName(
            "decisionCenterCandidateNoteSelection"
        )
        self._candidate_note_selection_label.setWordWrap(True)
        self._candidate_note_selection_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        notes_layout.addWidget(self._candidate_note_selection_label)

        self._candidate_note_input = QPlainTextEdit(notes_panel)
        self._candidate_note_input.setObjectName("decisionCenterCandidateNoteInput")
        self._candidate_note_input.setPlaceholderText(
            "Add evidence or review context for the selected Candidate."
        )
        self._candidate_note_input.setMaximumHeight(100)
        self._candidate_note_input.textChanged.connect(
            self._update_candidate_note_actions
        )
        notes_layout.addWidget(self._candidate_note_input)

        self._candidate_note_add_button = QPushButton("Add Note", notes_panel)
        self._candidate_note_add_button.setObjectName(
            "decisionCenterCandidateNoteAddButton"
        )
        self._candidate_note_add_button.clicked.connect(self._add_candidate_note)
        notes_layout.addWidget(self._candidate_note_add_button)
        layout.addWidget(notes_panel)

        portfolio_panel = QFrame(self)
        portfolio_panel.setObjectName("decisionCenterPortfolioContextPanel")
        portfolio_layout = QVBoxLayout(portfolio_panel)
        portfolio_layout.setContentsMargins(14, 12, 14, 14)
        portfolio_layout.setSpacing(8)

        portfolio_header = QHBoxLayout()
        portfolio_title = QLabel("Portfolio Context", portfolio_panel)
        portfolio_title.setObjectName("decisionCenterPortfolioContextTitle")
        portfolio_header.addWidget(portfolio_title)
        portfolio_header.addStretch(1)

        self._portfolio_state_label = QLabel(portfolio_panel)
        self._portfolio_state_label.setObjectName("decisionCenterPortfolioContextState")
        portfolio_header.addWidget(self._portfolio_state_label)

        self._portfolio_refresh_button = QPushButton(
            "Refresh Portfolio Context",
            portfolio_panel,
        )
        self._portfolio_refresh_button.setObjectName(
            "decisionCenterPortfolioContextRefreshButton"
        )
        self._portfolio_refresh_button.clicked.connect(self.refresh_portfolio_context)
        portfolio_header.addWidget(self._portfolio_refresh_button)
        portfolio_layout.addLayout(portfolio_header)

        self._portfolio_metadata_label = QLabel(portfolio_panel)
        self._portfolio_metadata_label.setObjectName(
            "decisionCenterPortfolioContextMetadata"
        )
        self._portfolio_metadata_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_metadata_label)

        self._portfolio_financials_label = QLabel(portfolio_panel)
        self._portfolio_financials_label.setObjectName(
            "decisionCenterPortfolioContextFinancials"
        )
        self._portfolio_financials_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_financials_label)

        pnl_header = QHBoxLayout()
        pnl_title = QLabel("P&L Summary", portfolio_panel)
        pnl_title.setObjectName("decisionCenterPortfolioPnlTitle")
        pnl_header.addWidget(pnl_title)
        pnl_header.addStretch(1)
        self._portfolio_pnl_state_label = QLabel(portfolio_panel)
        self._portfolio_pnl_state_label.setObjectName("decisionCenterPortfolioPnlState")
        pnl_header.addWidget(self._portfolio_pnl_state_label)
        portfolio_layout.addLayout(pnl_header)

        self._portfolio_pnl_summary_label = QLabel(portfolio_panel)
        self._portfolio_pnl_summary_label.setObjectName(
            "decisionCenterPortfolioPnlSummary"
        )
        self._portfolio_pnl_summary_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_pnl_summary_label)

        self._portfolio_pnl_detail_label = QLabel(portfolio_panel)
        self._portfolio_pnl_detail_label.setObjectName(
            "decisionCenterPortfolioPnlDetail"
        )
        self._portfolio_pnl_detail_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_pnl_detail_label)

        exposure_header = QHBoxLayout()
        exposure_title = QLabel("Exposure Summary", portfolio_panel)
        exposure_title.setObjectName("decisionCenterPortfolioExposureTitle")
        exposure_header.addWidget(exposure_title)
        exposure_header.addStretch(1)
        self._portfolio_exposure_state_label = QLabel(portfolio_panel)
        self._portfolio_exposure_state_label.setObjectName(
            "decisionCenterPortfolioExposureState"
        )
        exposure_header.addWidget(self._portfolio_exposure_state_label)
        portfolio_layout.addLayout(exposure_header)

        self._portfolio_exposure_summary_label = QLabel(portfolio_panel)
        self._portfolio_exposure_summary_label.setObjectName(
            "decisionCenterPortfolioExposureSummary"
        )
        self._portfolio_exposure_summary_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_exposure_summary_label)

        self._portfolio_exposure_detail_label = QLabel(portfolio_panel)
        self._portfolio_exposure_detail_label.setObjectName(
            "decisionCenterPortfolioExposureDetail"
        )
        self._portfolio_exposure_detail_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_exposure_detail_label)

        self._portfolio_position_status_label = QLabel(portfolio_panel)
        self._portfolio_position_status_label.setObjectName(
            "decisionCenterPortfolioPositionStatus"
        )
        portfolio_layout.addWidget(self._portfolio_position_status_label)

        self._portfolio_position_detail_label = QLabel(portfolio_panel)
        self._portfolio_position_detail_label.setObjectName(
            "decisionCenterPortfolioPositionDetails"
        )
        self._portfolio_position_detail_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_position_detail_label)

        self._portfolio_position_exposure_label = QLabel(portfolio_panel)
        self._portfolio_position_exposure_label.setObjectName(
            "decisionCenterPortfolioPositionExposureContribution"
        )
        self._portfolio_position_exposure_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_position_exposure_label)

        self._portfolio_detail_label = QLabel(portfolio_panel)
        self._portfolio_detail_label.setObjectName(
            "decisionCenterPortfolioContextDetail"
        )
        self._portfolio_detail_label.setWordWrap(True)
        portfolio_layout.addWidget(self._portfolio_detail_label)
        layout.addWidget(portfolio_panel)

        decision_panel = QFrame(self)
        decision_panel.setObjectName("decisionCenterDecisionDraftPanel")
        decision_layout = QVBoxLayout(decision_panel)
        decision_layout.setContentsMargins(14, 12, 14, 14)
        decision_layout.setSpacing(8)

        decision_header = QHBoxLayout()
        decision_title = QLabel("Trading Decision Draft", decision_panel)
        decision_title.setObjectName("decisionCenterDecisionDraftTitle")
        decision_header.addWidget(decision_title)
        decision_header.addStretch(1)
        self._decision_status_label = QLabel(decision_panel)
        self._decision_status_label.setObjectName("decisionCenterDecisionDraftStatus")
        decision_header.addWidget(self._decision_status_label)
        decision_layout.addLayout(decision_header)

        self._decision_metadata_label = QLabel(decision_panel)
        self._decision_metadata_label.setObjectName(
            "decisionCenterDecisionDraftMetadata"
        )
        self._decision_metadata_label.setWordWrap(True)
        decision_layout.addWidget(self._decision_metadata_label)

        rationale_label = QLabel("Required rationale", decision_panel)
        rationale_label.setObjectName("decisionCenterDecisionRationaleLabel")
        decision_layout.addWidget(rationale_label)

        self._decision_rationale = QPlainTextEdit(decision_panel)
        self._decision_rationale.setObjectName("decisionCenterDecisionRationale")
        self._decision_rationale.setPlaceholderText(
            "Document the evidence and reasoning for this Trading Decision draft."
        )
        self._decision_rationale.setMaximumHeight(110)
        self._decision_rationale.textChanged.connect(self._update_decision_draft_action)
        decision_layout.addWidget(self._decision_rationale)

        decision_action_row = QHBoxLayout()
        self._decision_detail_label = QLabel(decision_panel)
        self._decision_detail_label.setObjectName("decisionCenterDecisionDraftDetail")
        self._decision_detail_label.setWordWrap(True)
        decision_action_row.addWidget(self._decision_detail_label, 1)

        self._create_decision_button = QPushButton(
            "Create Decision Draft",
            decision_panel,
        )
        self._create_decision_button.setObjectName(
            "decisionCenterCreateDecisionDraftButton"
        )
        self._create_decision_button.clicked.connect(self._create_decision_draft)
        decision_action_row.addWidget(self._create_decision_button)

        self._accept_decision_button = QPushButton(
            "Accept Decision",
            decision_panel,
        )
        self._accept_decision_button.setObjectName("decisionCenterAcceptDecisionButton")
        self._accept_decision_button.clicked.connect(self._accept_decision)
        decision_action_row.addWidget(self._accept_decision_button)
        decision_layout.addLayout(decision_action_row)
        layout.addWidget(decision_panel)

        history_panel = QFrame(self)
        history_panel.setObjectName("decisionCenterDecisionHistoryPanel")
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(14, 12, 14, 14)
        history_layout.setSpacing(8)

        history_header = QHBoxLayout()
        history_title = QLabel("Decision History", history_panel)
        history_title.setObjectName("decisionCenterDecisionHistoryTitle")
        history_header.addWidget(history_title)
        history_header.addStretch(1)

        self._decision_history_state_label = QLabel(history_panel)
        self._decision_history_state_label.setObjectName(
            "decisionCenterDecisionHistoryState"
        )
        history_header.addWidget(self._decision_history_state_label)

        self._decision_history_refresh_button = QPushButton(
            "Refresh Decision History",
            history_panel,
        )
        self._decision_history_refresh_button.setObjectName(
            "decisionCenterDecisionHistoryRefreshButton"
        )
        self._decision_history_refresh_button.clicked.connect(
            self.refresh_decision_history
        )
        history_header.addWidget(self._decision_history_refresh_button)
        history_layout.addLayout(history_header)

        self._decision_history_detail_label = QLabel(history_panel)
        self._decision_history_detail_label.setObjectName(
            "decisionCenterDecisionHistoryDetail"
        )
        self._decision_history_detail_label.setWordWrap(True)
        history_layout.addWidget(self._decision_history_detail_label)

        self._decision_history_table = QTableWidget(history_panel)
        self._decision_history_table.setObjectName("decisionCenterDecisionHistoryTable")
        self._decision_history_table.setColumnCount(5)
        self._decision_history_table.setHorizontalHeaderLabels(
            (
                "Symbol",
                "Decision Status",
                "Created UTC",
                "Updated UTC",
                "Decision ID",
            )
        )
        self._decision_history_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._decision_history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._decision_history_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._decision_history_table.setAlternatingRowColors(True)
        self._decision_history_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._decision_history_table.setMinimumHeight(220)
        self._decision_history_table.verticalHeader().setVisible(False)
        history_header_view = self._decision_history_table.horizontalHeader()
        for column in range(self._decision_history_table.columnCount()):
            history_header_view.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        self._decision_history_table.itemSelectionChanged.connect(
            self._publish_selected_history_decision
        )
        history_layout.addWidget(self._decision_history_table)

        self._decision_history_selection_metadata_label = QLabel(history_panel)
        self._decision_history_selection_metadata_label.setObjectName(
            "decisionCenterDecisionHistorySelectionMetadata"
        )
        self._decision_history_selection_metadata_label.setWordWrap(True)
        history_layout.addWidget(self._decision_history_selection_metadata_label)

        history_rationale_title = QLabel("Selected rationale", history_panel)
        history_rationale_title.setObjectName(
            "decisionCenterDecisionHistoryRationaleTitle"
        )
        history_layout.addWidget(history_rationale_title)

        self._decision_history_selection_rationale_label = QLabel(history_panel)
        self._decision_history_selection_rationale_label.setObjectName(
            "decisionCenterDecisionHistorySelectionRationale"
        )
        self._decision_history_selection_rationale_label.setWordWrap(True)
        self._decision_history_selection_rationale_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        history_layout.addWidget(self._decision_history_selection_rationale_label)
        layout.addWidget(history_panel)

        safety_note = QLabel(
            "Candidate review and Trading Decision acceptance only. Portfolio P&L "
            "and exposure context are read-only and issue no risk verdict. "
            "Acceptance records the professional decision but does not prepare or "
            "submit an order, connect to a broker or perform a LIVE action.",
            self,
        )
        safety_note.setObjectName("decisionCenterSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        self._set_review_status("NO SELECTION", "idle")
        self._render_portfolio_context()
        self._render_decision_unavailable_or_unselected()
        self._update_review_actions()
        self._render_candidate_tags(
            TradingCandidateTags.unavailable(
                "Select a Trading Candidate to view Candidate Tags."
            )
        )
        self._render_candidate_notes(
            TradingCandidateNotes.unavailable(
                "Select a Trading Candidate to view Candidate Notes."
            )
        )

        if self._trading_candidate_service is None:
            self._refresh_button.setEnabled(False)
            self._render_collection(
                TradingCandidateCollection.unavailable(
                    "No Trading Candidate database was explicitly configured."
                )
            )
        else:
            self._trading_candidate_service.subscribe(self._collection_listener)
            self.refresh_candidates()

        if self._trading_decision_service is None:
            self._decision_history_refresh_button.setEnabled(False)
            self._render_decision_history(
                TradingDecisionHistory.unavailable(
                    "No Trading Decision database was explicitly configured."
                )
            )
        else:
            self.refresh_decision_history()

    @property
    def candidates(self) -> tuple[TradingCandidate, ...]:
        return self._candidates

    @property
    def decision_history(self) -> tuple[TradingDecision, ...]:
        return self._decision_history

    @property
    def candidate_tags(self) -> tuple[TradingCandidateTag, ...]:
        return self._candidate_tags

    @property
    def candidate_tags_state(self) -> TradingCandidateTagsState:
        return self._candidate_tags_state

    def refresh_candidate_tags(self) -> None:
        candidate = self._selected_candidate()
        if candidate is None:
            self._render_candidate_tags(
                TradingCandidateTags.unavailable(
                    "Select a Trading Candidate to view Candidate Tags."
                )
            )
            return
        if self._trading_candidate_tag_service is None:
            self._render_candidate_tags(
                TradingCandidateTags.unavailable(
                    "No Candidate Tag database was explicitly configured."
                )
            )
            return
        self._render_candidate_tags(TradingCandidateTags.loading())
        self._render_candidate_tags(
            self._trading_candidate_tag_service.load_tags(candidate.candidate_id.value)
        )

    def _add_candidate_tag(self) -> None:
        candidate = self._selected_candidate()
        if candidate is None or self._trading_candidate_tag_service is None:
            return
        outcome = self._trading_candidate_tag_service.add_tag(
            candidate.candidate_id.value,
            self._candidate_tag_input.text(),
        )
        self._candidate_tags_detail_label.setText(outcome.detail)
        if outcome.result is TradingCandidateTagAddResult.ADDED:
            self._candidate_tag_input.clear()
            self.refresh_candidate_tags()
        self._update_candidate_tag_actions()

    def _remove_candidate_tag(self) -> None:
        candidate = self._selected_candidate()
        selected_item = self._candidate_tags_list.currentItem()
        if (
            candidate is None
            or selected_item is None
            or self._trading_candidate_tag_service is None
        ):
            return
        outcome = self._trading_candidate_tag_service.remove_tag(
            candidate.candidate_id.value,
            selected_item.text(),
        )
        self._candidate_tags_detail_label.setText(outcome.detail)
        if outcome.result is TradingCandidateTagRemoveResult.REMOVED:
            self.refresh_candidate_tags()
        self._update_candidate_tag_actions()

    def _render_candidate_tags(self, result: TradingCandidateTags) -> None:
        self._candidate_tags = result.tags
        self._candidate_tags_state = result.state
        self._candidate_tags_state_label.setText(result.state.value)
        self._candidate_tags_detail_label.setText(result.detail)
        self._candidate_tags_list.blockSignals(True)
        self._candidate_tags_list.clear()
        self._candidate_tags_list.addItems([tag.value for tag in result.tags])
        self._candidate_tags_list.blockSignals(False)
        self._update_candidate_tag_actions()

    def _update_candidate_tag_actions(self) -> None:
        candidate = self._selected_candidate()
        available = (
            candidate is not None and self._trading_candidate_tag_service is not None
        )
        loaded = self._candidate_tags_state in {
            TradingCandidateTagsState.EMPTY,
            TradingCandidateTagsState.READY,
        }
        editable = (
            available
            and loaded
            and candidate is not None
            and candidate.status
            in {TradingCandidateStatus.NEW, TradingCandidateStatus.REVIEWING}
        )
        self._candidate_tags_refresh_button.setEnabled(
            available
            and self._candidate_tags_state is not TradingCandidateTagsState.LOADING
        )
        self._candidate_tag_input.setEnabled(editable)
        self._candidate_tag_add_button.setEnabled(
            editable and bool(self._candidate_tag_input.text().strip())
        )
        self._candidate_tag_remove_button.setEnabled(
            editable and self._candidate_tags_list.currentItem() is not None
        )

    def refresh_candidate_notes(self) -> None:
        candidate = self._selected_candidate()
        if candidate is None or self._trading_candidate_note_service is None:
            return
        self._render_candidate_notes(TradingCandidateNotes.loading())
        self._render_candidate_notes(
            self._trading_candidate_note_service.load_notes(
                candidate.candidate_id.value
            )
        )

    def _add_candidate_note(self) -> None:
        candidate = self._selected_candidate()
        if candidate is None or self._trading_candidate_note_service is None:
            return
        outcome = self._trading_candidate_note_service.add_note(
            candidate.candidate_id.value,
            self._candidate_note_input.toPlainText(),
        )
        self._candidate_notes_detail_label.setText(outcome.detail)
        if outcome.result is TradingCandidateNoteAddResult.ADDED:
            self._candidate_note_input.clear()
            self.refresh_candidate_notes()
        self._update_candidate_note_actions()

    def _render_candidate_notes(self, result: TradingCandidateNotes) -> None:
        self._candidate_notes = result.notes
        self._candidate_notes_state_label.setText(result.state.value)
        self._candidate_notes_detail_label.setText(result.detail)
        self._candidate_notes_table.blockSignals(True)
        self._candidate_notes_table.clearContents()
        self._candidate_notes_table.setRowCount(len(result.notes))
        for row, note in enumerate(result.notes):
            self._candidate_notes_table.setItem(
                row, 0, QTableWidgetItem(_format_utc_timestamp(note.created_at))
            )
            self._candidate_notes_table.setItem(
                row, 1, QTableWidgetItem(note.note_id.value)
            )
        self._candidate_notes_table.blockSignals(False)
        self._candidate_notes_table.clearSelection()
        self._candidate_note_selection_label.setText(
            "Select a Candidate Note to view its complete stored text."
            if result.notes
            else "No Candidate Note is selected."
        )
        self._update_candidate_note_actions()

    def _render_selected_candidate_note(self) -> None:
        row = self._candidate_notes_table.currentRow()
        if row < 0 or row >= len(self._candidate_notes):
            self._candidate_note_selection_label.setText(
                "No Candidate Note is selected."
            )
            return
        note = self._candidate_notes[row]
        self._candidate_note_selection_label.setText(
            f"Candidate ID: {note.candidate_id.value} | "
            f"Note ID: {note.note_id.value} | "
            f"Created UTC: {_format_utc_timestamp(note.created_at)}\n{note.text}"
        )

    def _update_candidate_note_actions(self) -> None:
        candidate = self._selected_candidate()
        available = (
            candidate is not None and self._trading_candidate_note_service is not None
        )
        self._candidate_notes_refresh_button.setEnabled(available)
        can_add = (
            available
            and candidate.status
            in {TradingCandidateStatus.NEW, TradingCandidateStatus.REVIEWING}
            and bool(self._candidate_note_input.toPlainText().strip())
        )
        self._candidate_note_input.setEnabled(
            available
            and candidate.status
            in {TradingCandidateStatus.NEW, TradingCandidateStatus.REVIEWING}
        )
        self._candidate_note_add_button.setEnabled(can_add)

    def refresh_decision_history(self) -> None:
        if self._trading_decision_service is None:
            return
        selected_decision_id = self._selected_history_decision_id
        self._render_decision_history(TradingDecisionHistory.loading())
        self._selected_history_decision_id = selected_decision_id
        self._render_decision_history(self._trading_decision_service.load_history())

    def refresh_candidates(self) -> None:
        if self._trading_candidate_service is None:
            return
        self._set_state("LOADING", "loading")
        self._detail_label.setText("Loading persistent Trading Candidates.")
        self._trading_candidate_service.refresh()

    def refresh_portfolio_context(self) -> None:
        if (
            self._selected_candidate() is None
            or self._portfolio_snapshot_service is None
            or self._portfolio_refresh_pending
        ):
            return

        self._portfolio_refresh_pending = True
        self._update_portfolio_refresh_action()
        self._set_portfolio_state("LOADING", "loading")
        self._portfolio_detail_label.setText(
            "Loading the configured read-only Portfolio snapshot."
        )
        try:
            result = self._portfolio_snapshot_service.load_snapshot()
        except Exception as exc:
            result = PortfolioSnapshotResult.error(
                detail=(
                    "Portfolio context refresh raised "
                    f"{type(exc).__name__}. Prior values are not reused."
                ),
                source_name=self._portfolio_result.source_name,
            )
        self._portfolio_result = result
        self._portfolio_refresh_pending = False
        self._render_portfolio_context()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._trading_candidate_service is not None:
            self._trading_candidate_service.unsubscribe(self._collection_listener)
        super().closeEvent(event)

    def _on_collection_changed(self, collection: TradingCandidateCollection) -> None:
        self._render_collection(collection)

    def _render_collection(self, collection: TradingCandidateCollection) -> None:
        context = self._instrument_context_service.context
        context_symbol = (
            context.symbol
            if context.state is InstrumentContextState.SELECTED
            and context.source == DECISION_CENTER_CONTEXT_SOURCE
            else None
        )

        self._candidates = collection.candidates
        self._table.blockSignals(True)
        self._table.clearContents()
        self._table.setRowCount(len(self._candidates))

        selected_row: int | None = None
        for row, candidate in enumerate(self._candidates):
            self._set_table_item(row, 0, candidate.symbol)
            self._set_table_item(row, 1, candidate.origin.value)
            self._set_table_item(row, 2, candidate.status.value)
            self._set_table_item(row, 3, _format_utc_timestamp(candidate.created_at))
            self._set_table_item(row, 4, _format_utc_timestamp(candidate.updated_at))
            if candidate.candidate_id.value == self._selected_candidate_id:
                selected_row = row
            elif (
                self._selected_candidate_id is None
                and candidate.symbol == context_symbol
            ):
                selected_row = row
                self._selected_candidate_id = candidate.candidate_id.value

        if selected_row is not None:
            self._table.selectRow(selected_row)
        else:
            self._selected_candidate_id = None
            self._table.clearSelection()
            if context_symbol is not None:
                self._instrument_context_service.clear_instrument(
                    DECISION_CENTER_CONTEXT_SOURCE
                )
        self._table.blockSignals(False)

        self._detail_label.setText(collection.detail)
        if collection.state is TradingCandidateCollectionState.READY:
            self._set_state("READY", "ready")
            if self._selected_candidate_id is None:
                self._set_review_status("NO SELECTION", "idle")
        elif collection.state is TradingCandidateCollectionState.EMPTY:
            self._set_state("EMPTY", "empty")
            self._set_review_status("NO SELECTION", "idle")
        elif collection.state is TradingCandidateCollectionState.ERROR:
            self._set_state("ERROR", "error")
            self._set_review_status("ERROR", "error")
        else:
            self._set_state("UNAVAILABLE", "unavailable")
            self._set_review_status("UNAVAILABLE", "unavailable")
        self._update_review_actions()
        if self._selected_candidate_id is None:
            self._render_candidate_tags(
                TradingCandidateTags.unavailable(
                    "Select a Trading Candidate to view Candidate Tags."
                )
            )
        else:
            self._update_candidate_tag_actions()
        self._render_portfolio_context()
        self._load_selected_decision()

    def _publish_selected_candidate(self) -> None:
        candidate = self._candidate_for_selected_row()
        if candidate is None:
            self._selected_candidate_id = None
            self._set_review_status("NO SELECTION", "idle")
            self._update_review_actions()
            self._render_portfolio_context()
            self._render_candidate_tags(
                TradingCandidateTags.unavailable(
                    "Select a Trading Candidate to view Candidate Tags."
                )
            )
            self._render_candidate_notes(
                TradingCandidateNotes.unavailable(
                    "Select a Trading Candidate to view Candidate Notes."
                )
            )
            self._load_selected_decision()
            return
        self._selected_candidate_id = candidate.candidate_id.value
        self._instrument_context_service.select_instrument(
            candidate.symbol,
            DECISION_CENTER_CONTEXT_SOURCE,
        )
        self._set_review_status("READY", "ready")
        self._detail_label.setText(
            f"{candidate.symbol} is selected with status {candidate.status.value}."
        )
        self._update_review_actions()
        self._render_portfolio_context()
        self.refresh_candidate_tags()
        self.refresh_candidate_notes()
        self._load_selected_decision()

    def _start_review(self) -> None:
        self._transition_selected_candidate(TradingCandidateStatus.REVIEWING)

    def _reject(self) -> None:
        self._transition_selected_candidate(TradingCandidateStatus.REJECTED)

    def _archive(self) -> None:
        self._transition_selected_candidate(TradingCandidateStatus.ARCHIVED)

    def _transition_selected_candidate(
        self,
        target_status: TradingCandidateStatus,
    ) -> None:
        candidate = self._selected_candidate()
        if candidate is None or self._trading_candidate_service is None:
            return
        outcome = self._trading_candidate_service.transition_candidate(
            candidate.candidate_id.value,
            target_status,
        )
        self._detail_label.setText(outcome.detail)
        if outcome.result is TradingCandidateReviewResult.UPDATED:
            self._set_review_status("UPDATED", "success")
        elif outcome.result is TradingCandidateReviewResult.INVALID_TRANSITION:
            self._set_review_status("INVALID TRANSITION", "error")
        elif outcome.result is TradingCandidateReviewResult.NOT_FOUND:
            self._set_review_status("NOT FOUND", "error")
        elif outcome.result is TradingCandidateReviewResult.CONFLICT:
            self._set_review_status("CONFLICT", "error")
        else:
            self._set_review_status("ERROR", "error")
        self._update_review_actions()
        self.refresh_candidate_tags()
        self.refresh_candidate_notes()

    def _render_portfolio_context(self) -> None:
        candidate = self._selected_candidate()
        if candidate is None:
            self._set_portfolio_state("NO SELECTION", "idle")
            self._set_portfolio_metadata(None)
            self._set_portfolio_financials(None)
            self._set_portfolio_pnl(None, selected=False)
            self._set_portfolio_exposure(None, selected=False)
            self._set_portfolio_position(None, currency=None, selected=False)
            self._set_portfolio_position_exposure(None, symbol=None, selected=False)
            self._portfolio_detail_label.setText(
                "Select a Trading Candidate to view its read-only Portfolio context."
            )
            self._update_portfolio_refresh_action()
            return

        result = self._portfolio_result
        self._set_portfolio_state(
            result.state.value,
            result.state.value.lower(),
        )
        self._portfolio_detail_label.setText(result.detail)
        pnl_result = summarize_portfolio_pnl(result)
        exposure_result = summarize_portfolio_exposure(result)
        snapshot = result.snapshot
        if snapshot is None:
            self._set_portfolio_metadata(None, source_name=result.source_name)
            self._set_portfolio_financials(None)
            self._set_portfolio_pnl(pnl_result, selected=True)
            self._set_portfolio_exposure(exposure_result, selected=True)
            self._set_portfolio_position(None, currency=None, selected=True)
            self._set_portfolio_position_exposure(
                exposure_result,
                symbol=candidate.symbol,
                selected=True,
            )
            self._update_portfolio_refresh_action()
            return

        self._set_portfolio_metadata(snapshot)
        self._set_portfolio_financials(snapshot)
        self._set_portfolio_pnl(pnl_result, selected=True)
        self._set_portfolio_exposure(exposure_result, selected=True)
        position = next(
            (
                current
                for current in snapshot.positions
                if current.symbol == candidate.symbol
            ),
            None,
        )
        self._set_portfolio_position(
            position,
            currency=snapshot.account.currency,
            selected=True,
        )
        self._set_portfolio_position_exposure(
            exposure_result,
            symbol=candidate.symbol,
            selected=True,
        )
        self._update_portfolio_refresh_action()

    def _set_portfolio_metadata(
        self,
        snapshot: PortfolioSnapshot | None,
        *,
        source_name: str | None = None,
    ) -> None:
        if snapshot is None:
            self._portfolio_metadata_label.setText(
                "Account: UNAVAILABLE | Currency: UNAVAILABLE | "
                f"Source: {source_name or 'NOT CONFIGURED'} | "
                "Observed UTC: UNAVAILABLE"
            )
            return
        self._portfolio_metadata_label.setText(
            f"Account: {snapshot.account.account_reference} | "
            f"Currency: {snapshot.account.currency} | "
            f"Source: {snapshot.source_name} | "
            f"Observed UTC: {_format_utc_timestamp(snapshot.observed_at)}"
        )

    def _set_portfolio_financials(
        self,
        snapshot: PortfolioSnapshot | None,
    ) -> None:
        if snapshot is None:
            self._portfolio_financials_label.setText(
                "Cash: UNAVAILABLE | Net Liquidation Value: UNAVAILABLE | "
                "Unrealized P&L: UNAVAILABLE"
            )
            return
        account = snapshot.account
        self._portfolio_financials_label.setText(
            f"Cash: {_format_money(account.cash, account.currency)} | "
            "Net Liquidation Value: "
            f"{_format_money(account.net_liquidation_value, account.currency)} | "
            "Unrealized P&L: "
            f"{_format_money(account.unrealized_pnl, account.currency)}"
        )

    def _set_portfolio_exposure(
        self,
        result: PortfolioExposureResult | None,
        *,
        selected: bool,
    ) -> None:
        if not selected:
            self._portfolio_exposure_state_label.setText("NO SELECTION")
            _set_dynamic_property(
                self._portfolio_exposure_state_label,
                "portfolioExposureState",
                "idle",
            )
            self._portfolio_exposure_summary_label.setText(
                "Long: UNAVAILABLE | Short: UNAVAILABLE | Gross: UNAVAILABLE | "
                "Net: UNAVAILABLE | Coverage: UNAVAILABLE"
            )
            self._portfolio_exposure_detail_label.setText(
                "Select a Trading Candidate to view Portfolio exposure context."
            )
            return
        if result is None:
            raise TypeError("selected Portfolio exposure requires a result")

        self._portfolio_exposure_state_label.setText(result.state.value)
        _set_dynamic_property(
            self._portfolio_exposure_state_label,
            "portfolioExposureState",
            result.state.value.lower(),
        )
        summary = result.summary
        if summary is None:
            self._portfolio_exposure_summary_label.setText(
                "Long: UNAVAILABLE | Short: UNAVAILABLE | Gross: UNAVAILABLE | "
                "Net: UNAVAILABLE | Coverage: UNAVAILABLE"
            )
            self._portfolio_exposure_detail_label.setText(result.detail)
            return

        self._portfolio_exposure_summary_label.setText(
            f"Long: {_format_money(summary.long_exposure, summary.currency)} | "
            f"Short: {_format_money(summary.short_exposure, summary.currency)} | "
            f"Gross: {_format_money(summary.gross_exposure, summary.currency)} | "
            f"Net: {_format_money(summary.net_exposure, summary.currency)} | "
            "Coverage: "
            f"{summary.valued_position_count} / {summary.total_position_count}"
        )
        largest_position = _format_largest_position(
            summary.largest_position_symbol,
            summary.largest_position_value,
            summary.currency,
        )
        self._portfolio_exposure_detail_label.setText(
            f"Snapshot State: {result.snapshot_state.value} | "
            f"Largest Position: {largest_position} | "
            "Largest Concentration: "
            f"{_format_percentage(summary.largest_position_concentration_pct)} | "
            f"{result.detail}"
        )

    def _set_portfolio_pnl(
        self,
        result: PortfolioPnlResult | None,
        *,
        selected: bool,
    ) -> None:
        if not selected:
            self._portfolio_pnl_state_label.setText("NO SELECTION")
            _set_dynamic_property(
                self._portfolio_pnl_state_label,
                "portfolioPnlState",
                "idle",
            )
            self._portfolio_pnl_summary_label.setText(
                "Positive: UNAVAILABLE | Loss: UNAVAILABLE | Net: UNAVAILABLE | "
                "P&L Coverage: UNAVAILABLE"
            )
            self._portfolio_pnl_detail_label.setText(
                "Select a Trading Candidate to view Portfolio P&L context."
            )
            return
        if result is None:
            raise TypeError("selected Portfolio P&L requires a result")

        self._portfolio_pnl_state_label.setText(result.state.value)
        _set_dynamic_property(
            self._portfolio_pnl_state_label,
            "portfolioPnlState",
            result.state.value.lower(),
        )
        summary = result.summary
        if summary is None:
            self._portfolio_pnl_summary_label.setText(
                "Positive: UNAVAILABLE | Loss: UNAVAILABLE | Net: UNAVAILABLE | "
                "P&L Coverage: UNAVAILABLE"
            )
            self._portfolio_pnl_detail_label.setText(result.detail)
            return

        self._portfolio_pnl_summary_label.setText(
            "Positive: "
            f"{_format_money(summary.positive_unrealized_pnl, summary.currency)} | "
            "Loss: "
            f"{_format_money(summary.negative_unrealized_pnl, summary.currency)} | "
            f"Net: {_format_money(summary.net_unrealized_pnl, summary.currency)} | "
            "P&L Coverage: "
            f"{summary.reported_position_count} / {summary.total_position_count}"
        )
        largest_winner = _format_largest_position(
            summary.largest_winner_symbol,
            summary.largest_winner_value,
            summary.currency,
        )
        largest_loser = _format_largest_position(
            summary.largest_loser_symbol,
            summary.largest_loser_value,
            summary.currency,
        )
        self._portfolio_pnl_detail_label.setText(
            f"Snapshot State: {result.snapshot_state.value} | "
            f"Largest Winner: {largest_winner} | "
            f"Largest Loser: {largest_loser} | "
            f"{result.detail}"
        )

    def _set_portfolio_position(
        self,
        position: PortfolioPosition | None,
        *,
        currency: str | None,
        selected: bool,
    ) -> None:
        if not selected:
            status = "NO CANDIDATE SELECTED"
            state = "idle"
        elif position is None and self._portfolio_result.snapshot is None:
            status = "UNAVAILABLE"
            state = "unavailable"
        elif position is None:
            status = "NO EXISTING POSITION"
            state = "no_position"
        else:
            status = "EXISTING POSITION"
            state = "existing"
        self._portfolio_position_status_label.setText(status)
        _set_dynamic_property(
            self._portfolio_position_status_label,
            "portfolioPositionState",
            state,
        )

        if position is None:
            self._portfolio_position_detail_label.setText(
                "Quantity: UNAVAILABLE | Average Price: UNAVAILABLE | "
                "Current Price: UNAVAILABLE | Current Value: UNAVAILABLE | "
                "Unrealized P&L: UNAVAILABLE"
            )
            return
        self._portfolio_position_detail_label.setText(
            f"Quantity: {_format_decimal(position.quantity)} | "
            f"Average Price: {_format_money(position.average_price, currency)} | "
            f"Current Price: {_format_money(position.current_price, currency)} | "
            f"Current Value: {_format_money(position.current_value, currency)} | "
            f"Unrealized P&L: {_format_money(position.unrealized_pnl, currency)}"
        )

    def _set_portfolio_position_exposure(
        self,
        result: PortfolioExposureResult | None,
        *,
        symbol: str | None,
        selected: bool,
    ) -> None:
        if not selected:
            self._portfolio_position_exposure_label.setText(
                "Position Exposure: UNAVAILABLE"
            )
            return
        if result is None or symbol is None:
            raise TypeError(
                "selected Portfolio position exposure requires result and symbol"
            )
        if result.summary is None:
            self._portfolio_position_exposure_label.setText(
                "Position Exposure: UNAVAILABLE"
            )
            return

        position = next(
            (
                current
                for current in result.position_exposures
                if current.symbol == symbol
            ),
            None,
        )
        if position is None:
            self._portfolio_position_exposure_label.setText(
                "Position Exposure: NO EXISTING POSITION"
            )
            return

        direction = (
            position.direction.value
            if position.direction is not None
            else "UNAVAILABLE"
        )
        gross_share = (
            _format_percentage(position.gross_exposure_share_pct)
            if position.gross_exposure_share_pct is not None
            else "UNAVAILABLE"
        )
        self._portfolio_position_exposure_label.setText(
            f"Position Exposure: Direction {direction} | "
            "Current Value: "
            f"{_format_money(position.signed_current_value, position.currency)} | "
            "Absolute Exposure: "
            f"{_format_money(position.absolute_exposure, position.currency)} | "
            f"Gross Share: {gross_share} | Valuation: {position.state.value}"
        )

    def _update_portfolio_refresh_action(self) -> None:
        self._portfolio_refresh_button.setEnabled(
            self._portfolio_snapshot_service is not None
            and self._selected_candidate() is not None
            and not self._portfolio_refresh_pending
        )

    def _render_decision_history(self, history: TradingDecisionHistory) -> None:
        self._decision_history = history.decisions
        self._decision_history_table.blockSignals(True)
        self._decision_history_table.clearContents()
        self._decision_history_table.setRowCount(len(self._decision_history))

        selected_row: int | None = None
        for row, decision in enumerate(self._decision_history):
            self._set_history_table_item(row, 0, decision.symbol)
            self._set_history_table_item(row, 1, decision.status.value)
            self._set_history_table_item(
                row,
                2,
                _format_utc_timestamp(decision.created_at),
            )
            self._set_history_table_item(
                row,
                3,
                _format_utc_timestamp(decision.updated_at),
            )
            self._set_history_table_item(row, 4, decision.decision_id.value)
            if decision.decision_id.value == self._selected_history_decision_id:
                selected_row = row

        if selected_row is None:
            self._selected_history_decision_id = None
            self._decision_history_table.clearSelection()
        else:
            self._decision_history_table.selectRow(selected_row)
        self._decision_history_table.blockSignals(False)

        self._set_decision_history_state(
            history.state.value,
            history.state.value.lower(),
        )
        self._decision_history_detail_label.setText(history.detail)
        self._decision_history_refresh_button.setEnabled(
            self._trading_decision_service is not None
            and history.state is not TradingDecisionHistoryState.LOADING
        )
        self._render_selected_history_decision()

    def _publish_selected_history_decision(self) -> None:
        decision = self._history_decision_for_selected_row()
        self._selected_history_decision_id = (
            decision.decision_id.value if decision is not None else None
        )
        self._render_selected_history_decision()

    def _render_selected_history_decision(self) -> None:
        decision = self._selected_history_decision()
        if decision is None:
            self._decision_history_selection_metadata_label.setText(
                "Candidate ID: — | Decision ID: — | Status: —"
            )
            self._decision_history_selection_rationale_label.setText(
                "Select a Decision History row to view its stored rationale."
            )
            return

        self._decision_history_selection_metadata_label.setText(
            f"Candidate ID: {decision.candidate_id.value} | "
            f"Decision ID: {decision.decision_id.value} | "
            f"Status: {decision.status.value} | "
            f"Created UTC: {_format_utc_timestamp(decision.created_at)} | "
            f"Updated UTC: {_format_utc_timestamp(decision.updated_at)}"
        )
        self._decision_history_selection_rationale_label.setText(decision.rationale)

    def _history_decision_for_selected_row(self) -> TradingDecision | None:
        selected_rows = self._decision_history_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        if row < 0 or row >= len(self._decision_history):
            return None
        return self._decision_history[row]

    def _selected_history_decision(self) -> TradingDecision | None:
        if self._selected_history_decision_id is None:
            return None
        return next(
            (
                decision
                for decision in self._decision_history
                if decision.decision_id.value == self._selected_history_decision_id
            ),
            None,
        )

    def _load_selected_decision(self) -> None:
        candidate = self._selected_candidate()
        self._selected_decision = None
        if candidate is None:
            self._render_decision_unavailable_or_unselected()
            return
        if self._trading_decision_service is None:
            self._set_decision_status("UNAVAILABLE", "unavailable")
            self._set_decision_metadata(None)
            self._set_decision_rationale("", editable=False)
            self._decision_detail_label.setText(
                "No Trading Decision persistence service is available."
            )
            self._update_decision_draft_action()
            return

        outcome = self._trading_decision_service.load_draft_for_candidate(
            candidate.candidate_id.value
        )
        self._decision_detail_label.setText(outcome.detail)
        if outcome.result is TradingDecisionDraftLoadResult.READY:
            if outcome.decision is None:
                self._set_decision_status("ERROR", "error")
                self._set_decision_metadata(None)
                self._set_decision_rationale("", editable=False)
                self._decision_detail_label.setText(
                    "Trading Decision load returned no decision."
                )
            else:
                self._render_decision(
                    outcome.decision,
                    status_text=outcome.decision.status.value,
                )
        elif outcome.result is TradingDecisionDraftLoadResult.NO_DRAFT:
            status = (
                "NO DRAFT"
                if candidate.status is TradingCandidateStatus.REVIEWING
                else "NOT AVAILABLE"
            )
            self._set_decision_status(status, "idle")
            self._set_decision_metadata(None)
            self._set_decision_rationale(
                "",
                editable=candidate.status is TradingCandidateStatus.REVIEWING,
            )
            self._update_decision_draft_action()
        elif outcome.result is TradingDecisionDraftLoadResult.NOT_FOUND:
            self._set_decision_status("NOT FOUND", "error")
            self._set_decision_metadata(None)
            self._set_decision_rationale("", editable=False)
            self._update_decision_draft_action()
        else:
            self._set_decision_status("ERROR", "error")
            self._set_decision_metadata(None)
            self._set_decision_rationale("", editable=False)
            self._update_decision_draft_action()

    def _create_decision_draft(self) -> None:
        candidate = self._selected_candidate()
        if candidate is None or self._trading_decision_service is None:
            return
        outcome = self._trading_decision_service.create_draft(
            candidate.candidate_id.value,
            self._decision_rationale.toPlainText(),
        )
        self._decision_detail_label.setText(outcome.detail)
        if outcome.result is TradingDecisionDraftCreateResult.CREATED:
            if outcome.decision is None:
                self._set_decision_status("ERROR", "error")
                self._decision_detail_label.setText(
                    "Trading Decision creation returned no decision."
                )
            else:
                self._render_decision(outcome.decision, status_text="CREATED")
                self.refresh_decision_history()
        elif outcome.result is TradingDecisionDraftCreateResult.ALREADY_EXISTS:
            if outcome.decision is None:
                self._set_decision_status("ERROR", "error")
                self._decision_detail_label.setText(
                    "Existing Trading Decision could not be restored."
                )
            else:
                self._render_decision(
                    outcome.decision,
                    status_text="ALREADY EXISTS",
                )
                self.refresh_decision_history()
        elif outcome.result is TradingDecisionDraftCreateResult.CANDIDATE_NOT_REVIEWING:
            self._set_decision_status("NOT REVIEWING", "error")
            self._update_decision_draft_action()
        elif outcome.result is TradingDecisionDraftCreateResult.NOT_FOUND:
            self._set_decision_status("NOT FOUND", "error")
            self._update_decision_draft_action()
        elif outcome.result is TradingDecisionDraftCreateResult.INVALID_RATIONALE:
            self._set_decision_status("INVALID RATIONALE", "error")
            self._update_decision_draft_action()
        else:
            self._set_decision_status("ERROR", "error")
            self._update_decision_draft_action()

    def _accept_decision(self) -> None:
        candidate = self._selected_candidate()
        decision = self._selected_decision
        if (
            candidate is None
            or decision is None
            or self._trading_decision_service is None
        ):
            return

        outcome = self._trading_decision_service.accept_decision(
            candidate.candidate_id.value
        )
        self._decision_detail_label.setText(outcome.detail)
        if outcome.result is TradingDecisionAcceptanceResult.ACCEPTED:
            if outcome.candidate is None or outcome.decision is None:
                self._set_decision_status("ERROR", "error")
                self._decision_detail_label.setText(
                    "Trading Decision acceptance returned incomplete state."
                )
            else:
                if self._trading_candidate_service is not None:
                    self._trading_candidate_service.refresh()
                self._set_review_status("ACCEPTED", "success")
                self._render_decision(
                    outcome.decision,
                    status_text="ACCEPTED",
                )
                self._decision_detail_label.setText(outcome.detail)
                self.refresh_decision_history()
        elif outcome.result is (
            TradingDecisionAcceptanceResult.CANDIDATE_NOT_REVIEWING
        ):
            self._set_decision_status("NOT REVIEWING", "error")
        elif outcome.result is TradingDecisionAcceptanceResult.DECISION_NOT_DRAFT:
            self._set_decision_status("NOT DRAFT", "error")
        elif outcome.result is TradingDecisionAcceptanceResult.NOT_FOUND:
            self._set_decision_status("NOT FOUND", "error")
        elif outcome.result is TradingDecisionAcceptanceResult.CONFLICT:
            self._set_decision_status("CONFLICT", "error")
            if self._trading_candidate_service is not None:
                self._trading_candidate_service.refresh()
            self.refresh_decision_history()
        else:
            self._set_decision_status("ERROR", "error")
        self._update_review_actions()
        self._update_decision_draft_action()

    def _render_decision(
        self,
        decision: TradingDecision,
        *,
        status_text: str,
    ) -> None:
        self._selected_decision = decision
        self._set_decision_status(status_text, "success")
        self._set_decision_metadata(decision)
        self._set_decision_rationale(decision.rationale, editable=False)
        self._update_decision_draft_action()

    def _render_decision_unavailable_or_unselected(self) -> None:
        if self._trading_decision_service is None:
            status = "UNAVAILABLE"
            detail = "No Trading Decision database was explicitly configured."
        else:
            status = "NO SELECTION"
            detail = "Select a REVIEWING Trading Candidate to create or view a draft."
        self._set_decision_status(
            status, "unavailable" if status == "UNAVAILABLE" else "idle"
        )
        self._set_decision_metadata(None)
        self._set_decision_rationale("", editable=False)
        self._decision_detail_label.setText(detail)
        self._update_decision_draft_action()

    def _set_decision_metadata(self, decision: TradingDecision | None) -> None:
        if decision is None:
            self._decision_metadata_label.setText(
                "Decision ID: — | Status: — | Created UTC: — | Updated UTC: —"
            )
            return
        self._decision_metadata_label.setText(
            f"Decision ID: {decision.decision_id.value} | "
            f"Status: {decision.status.value} | "
            f"Created UTC: {_format_utc_timestamp(decision.created_at)} | "
            f"Updated UTC: {_format_utc_timestamp(decision.updated_at)}"
        )

    def _set_decision_rationale(self, text: str, *, editable: bool) -> None:
        self._decision_rationale.blockSignals(True)
        self._decision_rationale.setPlainText(text)
        self._decision_rationale.setReadOnly(not editable)
        self._decision_rationale.setEnabled(editable or bool(text))
        self._decision_rationale.blockSignals(False)

    def _candidate_for_selected_row(self) -> TradingCandidate | None:
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        if row < 0 or row >= len(self._candidates):
            return None
        return self._candidates[row]

    def _selected_candidate(self) -> TradingCandidate | None:
        if self._selected_candidate_id is None:
            return None
        return next(
            (
                candidate
                for candidate in self._candidates
                if candidate.candidate_id.value == self._selected_candidate_id
            ),
            None,
        )

    def _update_review_actions(self) -> None:
        candidate = self._selected_candidate()
        review_available = (
            self._trading_candidate_service is not None and candidate is not None
        )
        self._start_review_button.setEnabled(
            review_available
            and candidate is not None
            and candidate.can_transition_to(TradingCandidateStatus.REVIEWING)
        )
        self._reject_button.setEnabled(
            review_available
            and candidate is not None
            and candidate.can_transition_to(TradingCandidateStatus.REJECTED)
        )
        self._archive_button.setEnabled(
            review_available
            and candidate is not None
            and candidate.can_transition_to(TradingCandidateStatus.ARCHIVED)
        )

    def _update_decision_draft_action(self) -> None:
        candidate = self._selected_candidate()
        self._create_decision_button.setEnabled(
            self._trading_decision_service is not None
            and candidate is not None
            and candidate.status is TradingCandidateStatus.REVIEWING
            and self._selected_decision is None
            and bool(self._decision_rationale.toPlainText().strip())
        )
        self._accept_decision_button.setEnabled(
            self._trading_decision_service is not None
            and candidate is not None
            and candidate.status is TradingCandidateStatus.REVIEWING
            and self._selected_decision is not None
            and self._selected_decision.status is TradingDecisionStatus.DRAFT
        )

    def _set_history_table_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._decision_history_table.setItem(row, column, item)

    def _set_table_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._table.setItem(row, column, item)

    def _set_state(self, text: str, state: str) -> None:
        self._state_label.setText(text)
        self._state_label.setProperty("decisionCenterState", state)
        self._state_label.style().unpolish(self._state_label)
        self._state_label.style().polish(self._state_label)

    def _set_review_status(self, text: str, state: str) -> None:
        self._review_status_label.setText(text)
        self._review_status_label.setProperty("candidateReviewState", state)
        self._review_status_label.style().unpolish(self._review_status_label)
        self._review_status_label.style().polish(self._review_status_label)

    def _set_decision_history_state(self, text: str, state: str) -> None:
        self._decision_history_state_label.setText(text)
        _set_dynamic_property(
            self._decision_history_state_label,
            "decisionHistoryState",
            state,
        )

    def _set_decision_status(self, text: str, state: str) -> None:
        self._decision_status_label.setText(text)
        self._decision_status_label.setProperty("decisionDraftState", state)
        self._decision_status_label.style().unpolish(self._decision_status_label)
        self._decision_status_label.style().polish(self._decision_status_label)

    def _set_portfolio_state(self, text: str, state: str) -> None:
        self._portfolio_state_label.setText(text)
        _set_dynamic_property(
            self._portfolio_state_label,
            "portfolioContextState",
            state,
        )


def _set_dynamic_property(widget: QWidget, name: str, value: str) -> None:
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "UNAVAILABLE"
    return format(value, "f")


def _format_money(value: Decimal | None, currency: str | None) -> str:
    if value is None or currency is None:
        return "UNAVAILABLE"
    return f"{format(value, 'f')} {currency}"


def _format_largest_position(
    symbol: str | None,
    value: Decimal | None,
    currency: str | None,
) -> str:
    if symbol is None or value is None or currency is None:
        return "NONE"
    return f"{symbol} ({_format_money(value, currency)})"


def _format_percentage(value: Decimal) -> str:
    return f"{format(value, '.2f')} %"


def _format_utc_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")
