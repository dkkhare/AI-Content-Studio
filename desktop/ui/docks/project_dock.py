from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem


class ProjectDock(QDockWidget):
    """Project explorer dock synchronized with the active project root."""

    def __init__(self, parent=None):
        super().__init__("Project", parent)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Current Project")
        self.setWidget(self.tree)

        self._project_path: Path | None = None
        self.show_empty_state()

    def load_project(self, project_path: str | Path) -> None:
        path = Path(project_path).resolve()
        self._project_path = path
        self.tree.clear()

        root_item = QTreeWidgetItem([path.name or str(path)])
        root_item.setToolTip(0, str(path))
        self.tree.addTopLevelItem(root_item)

        self._populate_directory(path, root_item, depth=0, max_depth=2)
        root_item.setExpanded(True)

    def _populate_directory(
        self,
        directory: Path,
        parent_item: QTreeWidgetItem,
        depth: int,
        max_depth: int,
    ) -> None:
        if depth >= max_depth or not directory.exists():
            return

        try:
            entries = sorted(
                directory.iterdir(),
                key=lambda item: (not item.is_dir(), item.name.lower()),
            )
        except OSError:
            return

        for entry in entries:
            # Hide transient autosave internals from the normal explorer.
            if entry.name == ".autosave":
                continue

            item = QTreeWidgetItem([entry.name])
            item.setToolTip(0, str(entry))
            parent_item.addChild(item)

            if entry.is_dir():
                self._populate_directory(
                    entry,
                    item,
                    depth=depth + 1,
                    max_depth=max_depth,
                )

    def show_empty_state(self) -> None:
        self._project_path = None
        self.tree.clear()
        self.tree.addTopLevelItem(QTreeWidgetItem(["No project loaded"]))

    def clear(self) -> None:
        self.show_empty_state()

    def refresh(self, project_path=None) -> None:
        path = Path(project_path).resolve() if project_path else self._project_path

        if path is None or not path.exists():
            self.show_empty_state()
            return

        self.load_project(path)
