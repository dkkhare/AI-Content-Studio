from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QComboBox,
    QSizePolicy,
    QMessageBox,
)

from desktop.controllers.tts_controller import (
    TTSController,
)

from desktop.ui.dialogs.tts_progress_dialog import (
    TTSProgressDialog,
)


class NarrationPanel(QWidget):
    """
    AI narration generation panel.

    Features:
    - Reference voice selection
    - Transcript input
    - Narration editor
    - TTS generation
    - Progress monitoring
    - Output management
    """


    narration_started = Signal()

    narration_finished = Signal(str)

    narration_failed = Signal(str)


    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )


        # --------------------------------------
        # Controller
        # --------------------------------------

        self.controller = TTSController(
            self
        )


        self.progress_dialog = None


        # --------------------------------------
        # State
        # --------------------------------------

        self.reference_audio = ""

        self.output_directory = (
            "output/tts"
        )


        self._recent_outputs = []

        self._audio_player = None


        self._building = False


        # --------------------------------------
        # UI
        # --------------------------------------

        self._build_ui()


        self._connect_controller()


        self.enable_drag_drop()


        self.refresh_voice_profiles()

    # --------------------------------------------------
    # UI Construction
    # --------------------------------------------------

    def _build_ui(self):

        root = QVBoxLayout(
            self
        )

        root.setSpacing(
            12
        )

        root.setContentsMargins(
            12,
            12,
            12,
            12,
        )


        title = QLabel(
            "AI Narration"
        )

        title.setObjectName(
            "title"
        )


        root.addWidget(
            title
        )


        self._create_reference_group(
            root
        )


        self._create_text_group(
            root
        )


        self._create_button_bar(
            root
        )


        root.addStretch()



    # --------------------------------------------------
    # Reference Voice Group
    # --------------------------------------------------

    def _create_reference_group(
        self,
        layout,
    ):

        group = QGroupBox(
            "Reference Voice"
        )


        grid = QGridLayout(
            group
        )


        grid.addWidget(
            QLabel(
                "Reference Audio"
            ),
            0,
            0,
        )


        self.reference_audio_edit = QLineEdit()


        self.reference_audio_edit.setReadOnly(
            True
        )


        grid.addWidget(
            self.reference_audio_edit,
            0,
            1,
        )


        self.browse_button = QPushButton(
            "Browse..."
        )


        grid.addWidget(
            self.browse_button,
            0,
            2,
        )


        grid.addWidget(
            QLabel(
                "Voice Profile"
            ),
            1,
            0,
        )


        self.voice_combo = QComboBox()


        self.voice_combo.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )


        grid.addWidget(
            self.voice_combo,
            1,
            1,
            1,
            2,
        )


        layout.addWidget(
            group
        )



    # --------------------------------------------------
    # Narration Text Group
    # --------------------------------------------------

    def _create_text_group(
        self,
        layout,
    ):

        group = QGroupBox(
            "Narration Text"
        )


        box = QVBoxLayout(
            group
        )


        box.addWidget(
            QLabel(
                "Reference Transcript"
            )
        )


        self.reference_text = QTextEdit()


        self.reference_text.setPlaceholderText(
            "Reference transcript..."
        )


        self.reference_text.setMinimumHeight(
            100
        )


        box.addWidget(
            self.reference_text
        )



        box.addWidget(
            QLabel(
                "Narration"
            )
        )


        self.narration_text = QTextEdit()


        self.narration_text.setPlaceholderText(
            "Enter narration text..."
        )


        self.narration_text.setMinimumHeight(
            250
        )


        box.addWidget(
            self.narration_text
        )


        layout.addWidget(
            group
        )



    # --------------------------------------------------
    # Button Bar
    # --------------------------------------------------

    def _create_button_bar(
        self,
        layout,
    ):

        row = QHBoxLayout()


        self.generate_button = QPushButton(
            "Generate Narration"
        )


        self.cancel_button = QPushButton(
            "Cancel"
        )


        self.cancel_button.setEnabled(
            False
        )


        row.addStretch()


        row.addWidget(
            self.generate_button
        )


        row.addWidget(
            self.cancel_button
        )


        layout.addLayout(
            row
        )

    # --------------------------------------------------
    # Controller Connections
    # --------------------------------------------------

    def _connect_controller(
        self,
    ):

        self.browse_button.clicked.connect(
            self.browse_reference_audio
        )


        self.generate_button.clicked.connect(
            self.generate_narration
        )


        self.cancel_button.clicked.connect(
            self.cancel_generation
        )


        self.controller.generation_started.connect(
            self._generation_started
        )


        self.controller.generation_progress.connect(
            self._update_progress
        )


        self.controller.generation_finished.connect(
            self._generation_finished
        )


        self.controller.generation_failed.connect(
            self._generation_failed
        )


        self.controller.generation_cancelled.connect(
            self._generation_cancelled
        )



    # --------------------------------------------------
    # Browse Reference Audio
    # --------------------------------------------------

    def browse_reference_audio(
        self,
    ):

        filename, _ = QFileDialog.getOpenFileName(

            self,

            "Select Reference Audio",

            "",

            "Audio Files (*.wav *.mp3 *.flac *.ogg)",

        )


        if not filename:

            return


        self.reference_audio = filename


        self.reference_audio_edit.setText(
            filename
        )



    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_inputs(
        self,
    ):

        if not self.reference_audio:

            QMessageBox.warning(

                self,

                "Reference Audio",

                "Please select a reference audio file."

            )

            return False



        if not Path(
            self.reference_audio
        ).exists():

            QMessageBox.warning(

                self,

                "Reference Audio",

                "Reference audio file does not exist."

            )

            return False



        if not self.reference_text.toPlainText().strip():

            QMessageBox.warning(

                self,

                "Reference Text",

                "Reference transcript is required."

            )

            return False



        if not self.narration_text.toPlainText().strip():

            QMessageBox.warning(

                self,

                "Narration",

                "Narration text is required."

            )

            return False



        return True



    # --------------------------------------------------
    # Progress Dialog
    # --------------------------------------------------

    def _create_progress_dialog(
        self,
    ):

        self.progress_dialog = TTSProgressDialog(
            self
        )


        self.progress_dialog.set_controller(
            self.controller
        )



    def _update_progress(
        self,
        progress,
    ):

        if self.progress_dialog:

            if hasattr(
                self.progress_dialog,
                "update_progress",
            ):

                self.progress_dialog.update_progress(
                    progress
                )



    # --------------------------------------------------
    # Generate
    # --------------------------------------------------

    def generate_narration(
        self,
    ):

        if not self.validate_inputs():

            return



        if self.controller.is_running():

            QMessageBox.information(

                self,

                "Narration",

                "Generation is already running."

            )

            return



        self._create_progress_dialog()


        try:

            self.controller.generate(

                reference_audio=self.reference_audio,

                reference_text=(
                    self.reference_text
                    .toPlainText()
                ),

                text=(
                    self.narration_text
                    .toPlainText()
                ),

                output_directory=self.output_directory,

            )


        except Exception as exc:


            QMessageBox.critical(

                self,

                "Narration Error",

                str(exc),

            )

            return



        self.progress_dialog.show()



    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def cancel_generation(
        self,
    ):

        if self.controller.is_running():

            self.controller.cancel()
    # --------------------------------------------------
    # Controller Events
    # --------------------------------------------------

    def _generation_started(
        self,
    ):

        self.generate_button.setEnabled(
            False
        )

        self.cancel_button.setEnabled(
            True
        )

        self.narration_started.emit()



    def _generation_finished(
        self,
        session,
    ):

        self.generate_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )


        if self.progress_dialog:

            self.progress_dialog.close()


        if session:

            output = getattr(
                session,
                "output_file",
                "",
            )


            if output:

                self.add_recent_output(
                    output
                )


                self.narration_finished.emit(
                    output
                )


        self.refresh_voice_profiles()



    def _generation_failed(
        self,
        message,
    ):

        self.generate_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )


        if self.progress_dialog:

            self.progress_dialog.close()


        QMessageBox.critical(

            self,

            "Narration Failed",

            message,

        )


        self.narration_failed.emit(
            message
        )



    def _generation_cancelled(
        self,
    ):

        self.generate_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )


        if self.progress_dialog:

            self.progress_dialog.close()


        QMessageBox.information(

            self,

            "Narration",

            "Narration generation cancelled."

        )



    # --------------------------------------------------
    # Voice Profiles
    # --------------------------------------------------

    def load_voice_profiles(
        self,
        profiles,
    ):

        self.voice_combo.clear()


        for profile in profiles:

            self.voice_combo.addItem(
                profile
            )



    def selected_voice(
        self,
    ):

        return (
            self.voice_combo.currentText()
        )



    def refresh_voice_profiles(
        self,
    ):

        self.voice_combo.clear()


        manager = getattr(
            self.controller,
            "manager",
            None,
        )


        if manager is None:

            return


        try:

            profiles = (
                manager.available_speakers()
            )


        except Exception:

            profiles = []


        self.load_voice_profiles(
            profiles
        )



    def selected_voice_profile(
        self,
    ):

        return (
            self.voice_combo.currentText()
        )



    def apply_selected_profile(
        self,
    ):

        profile = (
            self.selected_voice_profile()
        )


        if not profile:

            return


        manager = getattr(
            self.controller,
            "manager",
            None,
        )


        if manager is None:

            return


        try:

            manager.load_speaker(
                profile
            )


        except Exception as exc:

            QMessageBox.warning(

                self,

                "Voice Profile",

                str(exc),

            )

    # --------------------------------------------------
    # Playback
    # --------------------------------------------------

    def play_output(
        self,
    ):

        output = self.controller.output_file()


        if not output:

            QMessageBox.information(

                self,

                "Playback",

                "No generated narration available."

            )

            return



        output_path = Path(
            output
        )


        if not output_path.exists():

            QMessageBox.warning(

                self,

                "Playback",

                "Generated audio file not found."

            )

            return



        try:

            from backend.audio.player import (
                AudioPlayer
            )


        except ImportError:

            QMessageBox.warning(

                self,

                "Playback",

                "Audio player is not available."

            )

            return



        if self._audio_player is None:

            self._audio_player = AudioPlayer()



        try:

            self._audio_player.play(
                str(output_path)
            )


        except Exception as exc:

            QMessageBox.warning(

                self,

                "Playback",

                str(exc),

            )



    def stop_playback(
        self,
    ):

        if self._audio_player:

            try:

                self._audio_player.stop()

            except Exception:

                pass



    # --------------------------------------------------
    # Output Folder
    # --------------------------------------------------

    def open_output_folder(
        self,
    ):

        directory = Path(
            self.output_directory
        )


        directory.mkdir(

            parents=True,

            exist_ok=True,

        )


        try:

            from PySide6.QtGui import (
                QDesktopServices
            )

            from PySide6.QtCore import (
                QUrl
            )


            QDesktopServices.openUrl(

                QUrl.fromLocalFile(

                    str(directory)

                )

            )


        except Exception as exc:


            QMessageBox.warning(

                self,

                "Output Folder",

                str(exc),

            )



    # --------------------------------------------------
    # Recent Outputs
    # --------------------------------------------------

    def add_recent_output(
        self,
        filename,
    ):

        if not filename:

            return



        if filename in self._recent_outputs:

            self._recent_outputs.remove(
                filename
            )



        self._recent_outputs.insert(

            0,

            filename,

        )



        self._recent_outputs = (

            self._recent_outputs[:10]

        )



    def recent_outputs(
        self,
    ):

        return list(
            self._recent_outputs
        )



    def clear_recent_outputs(
        self,
    ):

        self._recent_outputs.clear()

    # --------------------------------------------------
    # Drag & Drop
    # --------------------------------------------------

    def enable_drag_drop(
        self,
    ):

        self.setAcceptDrops(
            True
        )


    def dragEnterEvent(
        self,
        event,
    ):

        if event.mimeData().hasUrls():

            event.acceptProposedAction()

        else:

            event.ignore()



    def dragMoveEvent(
        self,
        event,
    ):

        if event.mimeData().hasUrls():

            event.acceptProposedAction()

        else:

            event.ignore()



    def dropEvent(
        self,
        event,
    ):

        urls = event.mimeData().urls()


        if not urls:

            return



        file_path = urls[0].toLocalFile()


        if not file_path:

            return



        suffix = Path(
            file_path
        ).suffix.lower()



        supported = (

            ".wav",

            ".mp3",

            ".flac",

            ".ogg",

        )


        if suffix not in supported:


            QMessageBox.warning(

                self,

                "Reference Audio",

                "Unsupported audio format."

            )

            return



        self.reference_audio = file_path


        self.reference_audio_edit.setText(

            file_path

        )


        event.acceptProposedAction()



    # --------------------------------------------------
    # Keyboard Shortcuts
    # --------------------------------------------------

    def keyPressEvent(
        self,
        event,
    ):


        if event.modifiers() == Qt.ControlModifier:


            if event.key() == Qt.Key_Return:

                self.generate_narration()

                return



            if event.key() == Qt.Key_O:

                self.browse_reference_audio()

                return



            if event.key() == Qt.Key_P:

                self.play_output()

                return



        if event.key() == Qt.Key_Escape:

            self.cancel_generation()

            return



        super().keyPressEvent(
            event
        )



    # --------------------------------------------------
    # Session State
    # --------------------------------------------------

    def save_state(
        self,
    ):

        return {

            "reference_audio":
                self.reference_audio,


            "reference_text":
                self.reference_text.toPlainText(),


            "narration":
                self.narration_text.toPlainText(),


            "voice":
                self.selected_voice(),


            "output_directory":
                self.output_directory,


            "recent_outputs":
                self.recent_outputs(),

        }



    def restore_state(
        self,
        state,
    ):

        if not state:

            return



        self.reference_audio = state.get(

            "reference_audio",

            "",

        )


        self.reference_audio_edit.setText(

            self.reference_audio

        )


        self.reference_text.setPlainText(

            state.get(

                "reference_text",

                "",

            )

        )


        self.narration_text.setPlainText(

            state.get(

                "narration",

                "",

            )

        )


        self.output_directory = state.get(

            "output_directory",

            self.output_directory,

        )



        self._recent_outputs = state.get(

            "recent_outputs",

            [],

        )



        voice = state.get(

            "voice",

            "",

        )


        index = self.voice_combo.findText(

            voice

        )


        if index >= 0:

            self.voice_combo.setCurrentIndex(

                index

            )



    # --------------------------------------------------
    # Clear Panel
    # --------------------------------------------------

    def clear(
        self,
    ):

        self.reference_audio = ""


        self.reference_audio_edit.clear()


        self.reference_text.clear()


        self.narration_text.clear()


        self.voice_combo.setCurrentIndex(
            -1
        )



    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup(
        self,
    ):

        try:

            self.cancel_generation()


        except Exception:

            pass



        try:

            self.stop_playback()


        except Exception:

            pass



        try:

            self.controller.cleanup()


        except Exception:

            pass

    # --------------------------------------------------
    # Refresh UI
    # --------------------------------------------------

    def refresh(
        self,
    ):
        """
        Refresh narration panel state.
        """

        self.refresh_voice_profiles()


        if self.controller.is_running():

            self.generate_button.setEnabled(
                False
            )

            self.cancel_button.setEnabled(
                True
            )

        else:

            self.generate_button.setEnabled(
                True
            )

            self.cancel_button.setEnabled(
                False
            )



    # --------------------------------------------------
    # Controller State
    # --------------------------------------------------

    def is_generating(
        self,
    ):

        return self.controller.is_running()



    def current_session(
        self,
    ):

        return self.controller.session()



    def statistics(
        self,
    ):

        return self.controller.statistics()



    # --------------------------------------------------
    # Close Event
    # --------------------------------------------------

    def closeEvent(
        self,
        event,
    ):

        try:

            self.cleanup()


        except Exception:

            pass


        event.accept()



    # --------------------------------------------------
    # Debug Information
    # --------------------------------------------------

    def debug_info(
        self,
    ):

        return {

            "reference_audio":
                self.reference_audio,


            "output_directory":
                self.output_directory,


            "running":
                self.is_generating(),


            "recent_outputs":
                len(
                    self._recent_outputs
                ),

        }