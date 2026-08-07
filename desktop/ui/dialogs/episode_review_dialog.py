from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend.episodes import EpisodeReviewStore


class EpisodeReviewDialog(QDialog):
    """Review, edit, approve, regenerate or skip planned Hindi episodes."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.store = EpisodeReviewStore(project.root)
        self._episode_ids: list[str] = []

        self.setWindowTitle("Episode Review")
        self.resize(1050, 700)

        root = QVBoxLayout(self)
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        splitter = QSplitter(self)
        root.addWidget(splitter, 1)

        self.episode_list = QListWidget(splitter)
        self.episode_list.currentRowChanged.connect(self._load_row)

        editor = QWidget(splitter)
        editor_layout = QVBoxLayout(editor)
        editor_layout.addWidget(QLabel("Episode title", editor))
        self.title_edit = QLineEdit(editor)
        editor_layout.addWidget(self.title_edit)

        self.meta_label = QLabel(editor)
        self.meta_label.setWordWrap(True)
        editor_layout.addWidget(self.meta_label)

        editor_layout.addWidget(QLabel("Hindi narration script", editor))
        self.script_edit = QTextEdit(editor)
        self.script_edit.setAcceptRichText(False)
        editor_layout.addWidget(self.script_edit, 1)

        actions = QHBoxLayout()
        self.save_button = QPushButton("Save Edit", editor)
        self.approve_button = QPushButton("Approve", editor)
        self.regenerate_button = QPushButton("Regenerate", editor)
        self.skip_button = QPushButton("Skip", editor)
        actions.addWidget(self.save_button)
        actions.addWidget(self.approve_button)
        actions.addWidget(self.regenerate_button)
        actions.addWidget(self.skip_button)
        editor_layout.addLayout(actions)

        self.save_button.clicked.connect(self._save_edit)
        self.approve_button.clicked.connect(self._approve)
        self.regenerate_button.clicked.connect(self._regenerate)
        self.skip_button.clicked.connect(self._skip)

        footer = QHBoxLayout()
        footer.addStretch(1)
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        root.addLayout(footer)

        self.refresh()

    def _selected_id(self) -> str | None:
        row = self.episode_list.currentRow()
        if 0 <= row < len(self._episode_ids):
            return self._episode_ids[row]
        return None

    def refresh(self, keep_episode_id: str | None = None) -> None:
        payload = self.store.load()
        episodes = list(payload.get("episodes", []))
        self._episode_ids = [str(item.get("episode_id", "")) for item in episodes]
        self.episode_list.clear()

        selected_row = 0
        for index, episode in enumerate(episodes):
            episode_id = str(episode.get("episode_id", ""))
            status = str(episode.get("status", "planned"))
            approved = bool(episode.get("approved", False))
            marker = "✓" if approved else ("—" if status == "skipped" else "○")
            title = str(episode.get("title", episode_id))
            minutes = float(episode.get("estimated_minutes", 0.0) or 0.0)
            self.episode_list.addItem(
                f"{marker} {episode_id} · {minutes:.1f} min · {title} [{status}]"
            )
            if keep_episode_id == episode_id:
                selected_row = index

        pending = len(self.store.pending()) if episodes else 0
        if not episodes:
            self.status_label.setText("No planned episodes were found.")
        elif pending:
            self.status_label.setText(
                f"{len(episodes)} episode(s) planned; {pending} still require approval or Skip. "
                "F5-TTS and video generation remain gated until review is complete."
            )
        else:
            self.status_label.setText(
                f"Review complete for {len(episodes)} episode(s). Media generation can proceed."
            )

        has = bool(episodes)
        for widget in (
            self.title_edit,
            self.script_edit,
            self.save_button,
            self.approve_button,
            self.regenerate_button,
            self.skip_button,
        ):
            widget.setEnabled(has)
        if has:
            self.episode_list.setCurrentRow(selected_row)
        else:
            self.title_edit.clear()
            self.script_edit.clear()
            self.meta_label.clear()

    def _load_row(self, row: int) -> None:
        if not (0 <= row < len(self._episode_ids)):
            return
        episode_id = self._episode_ids[row]
        try:
            episode = self.store.get(episode_id)
            text = self.store.script(episode_id)
        except Exception as exc:
            QMessageBox.critical(self, "Episode Review", str(exc))
            return

        self.title_edit.setText(str(episode.get("title", episode_id)))
        self.script_edit.setPlainText(text)
        self.meta_label.setText(
            "Estimated duration: "
            f"{float(episode.get('estimated_minutes', 0.0) or 0.0):.2f} min  |  "
            f"Words: {int(episode.get('word_count', 0) or 0)}  |  "
            f"Status: {episode.get('status', 'planned')}"
        )

    def _save_edit(self) -> bool:
        episode_id = self._selected_id()
        if not episode_id:
            return False
        try:
            self.store.edit(
                episode_id,
                title=self.title_edit.text(),
                text=self.script_edit.toPlainText(),
            )
            self.refresh(episode_id)
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Unable to Save Episode", str(exc))
            return False

    def _approve(self) -> None:
        episode_id = self._selected_id()
        if not episode_id:
            return
        if not self._save_edit():
            return
        try:
            self.store.approve(episode_id)
            self.refresh(episode_id)
        except Exception as exc:
            QMessageBox.critical(self, "Unable to Approve Episode", str(exc))

    def _skip(self) -> None:
        episode_id = self._selected_id()
        if not episode_id:
            return
        try:
            self.store.skip(episode_id)
            self.refresh(episode_id)
        except Exception as exc:
            QMessageBox.critical(self, "Unable to Skip Episode", str(exc))

    def _regenerate(self) -> None:
        episode_id = self._selected_id()
        if not episode_id:
            return
        source = self.script_edit.toPlainText().strip()
        if not source:
            QMessageBox.warning(self, "Regenerate Episode", "The episode script is empty.")
            return

        try:
            from backend.ai import AIConfig, AIManager

            provider = str(self.project.get_setting("ai_provider", "ollama") or "ollama")
            model = str(self.project.get_setting("ai_model", "") or "")
            manager = AIManager(
                config=AIConfig(default_provider=provider, default_model=model)
            )
            response = manager.execute_prompt(
                "script_generation",
                {
                    "text": source,
                    "language": str(self.project.language or "hi"),
                    "tone": str(
                        self.project.get_setting(
                            "ai_script_style", "natural Hindi podcast narration"
                        )
                    ),
                },
                provider_id=provider,
                model=model,
            )
            regenerated = str(response.text or "").strip()
            if not regenerated:
                raise RuntimeError("The local AI provider returned an empty script.")
            self.store.replace_regenerated_text(episode_id, regenerated)
            self.store.request_regeneration(episode_id)
            self.refresh(episode_id)
            self.script_edit.setPlainText(regenerated)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Episode Regeneration Failed",
                "Unable to regenerate with the configured local AI provider.\n\n" + str(exc),
            )
