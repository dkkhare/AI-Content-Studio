from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QFileIconProvider,
    QDockWidget,
    QInputDialog,
    QMenu,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
)


class ProjectDock(QDockWidget):
    """Interactive project explorer synchronized with the active project."""

    fileActivated = Signal(object)

    def __init__(self, parent=None):
        super().__init__("Project", parent)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Current Project")
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.setWidget(self.tree)

        self._project_path: Path | None = None
        self._icon_provider = QFileIconProvider()
        self.show_empty_state()

    def load_project(self, project_path: str | Path) -> None:
        path = Path(project_path).resolve()
        self._project_path = path
        self.tree.clear()

        root_item = self._make_item(path, path.name or str(path))
        self.tree.addTopLevelItem(root_item)
        self._populate_directory(path, root_item)
        root_item.setExpanded(True)

    def _make_item(self, path: Path, label: str | None = None) -> QTreeWidgetItem:
        item = QTreeWidgetItem([label or path.name])
        item.setToolTip(0, str(path))
        item.setData(0, Qt.UserRole, str(path))
        item.setIcon(0, self._icon_provider.icon(path))
        return item

    def _populate_directory(self, directory: Path, parent_item: QTreeWidgetItem) -> None:
        if not directory.exists() or not directory.is_dir():
            return

        try:
            entries = sorted(
                directory.iterdir(),
                key=lambda item: (not item.is_dir(), item.name.lower()),
            )
        except OSError:
            return

        for entry in entries:
            if entry.name == ".autosave":
                continue

            item = self._make_item(entry)
            parent_item.addChild(item)
            if entry.is_dir():
                self._populate_directory(entry, item)

    def show_empty_state(self) -> None:
        self._project_path = None
        self.tree.clear()
        item = QTreeWidgetItem(["No project loaded"])
        item.setDisabled(True)
        self.tree.addTopLevelItem(item)

    def clear(self) -> None:
        self.show_empty_state()

    def refresh(self, project_path=None) -> None:
        path = Path(project_path).resolve() if project_path else self._project_path
        if path is None or not path.exists():
            self.show_empty_state()
            return
        self.load_project(path)

    def _path_for_item(self, item: QTreeWidgetItem | None) -> Path | None:
        if item is None:
            return None
        value = item.data(0, Qt.UserRole)
        return Path(value) if value else None

    def _on_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        path = self._path_for_item(item)
        if path is None or not path.exists():
            return

        if path.is_dir():
            item.setExpanded(not item.isExpanded())
            return

        self.fileActivated.emit(path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _show_context_menu(self, position) -> None:
        item = self.tree.itemAt(position)
        path = self._path_for_item(item)
        if path is None or not path.exists():
            return

        menu = QMenu(self.tree)
        open_action = QAction("Open", menu)
        reveal_action = QAction("Reveal in Explorer", menu)
        refresh_action = QAction("Refresh", menu)

        open_action.triggered.connect(lambda: self._open_path(path))
        reveal_action.triggered.connect(lambda: self._reveal_path(path))
        refresh_action.triggered.connect(self.refresh)

        menu.addAction(open_action)
        menu.addAction(reveal_action)
        menu.addSeparator()
        menu.addAction(refresh_action)

        # Protect the project root from rename/delete operations.
        if self._project_path is not None and path.resolve() != self._project_path.resolve():
            rename_action = QAction("Rename", menu)
            delete_action = QAction("Delete", menu)
            rename_action.triggered.connect(lambda: self._rename_path(path))
            delete_action.triggered.connect(lambda: self._delete_path(path))
            menu.addSeparator()
            menu.addAction(rename_action)
            menu.addAction(delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _open_path(self, path: Path) -> None:
        self.fileActivated.emit(path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _reveal_path(self, path: Path) -> None:
        target = path if path.is_dir() else path.parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _rename_path(self, path: Path) -> None:
        name, ok = QInputDialog.getText(
            self,
            "Rename",
            "New name:",
            text=path.name,
        )
        name = name.strip()
        if not ok or not name or name == path.name:
            return

        destination = path.with_name(name)
        if destination.exists():
            QMessageBox.warning(self, "Rename", "A file or folder with that name already exists.")
            return

        try:
            path.rename(destination)
            self.refresh()
        except OSError as exc:
            QMessageBox.critical(self, "Rename Failed", str(exc))

    def _delete_path(self, path: Path) -> None:
        result = QMessageBox.warning(
            self,
            "Delete",
            f"Permanently delete '{path.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            self.refresh()
        except OSError as exc:
            QMessageBox.critical(self, "Delete Failed", str(exc))
