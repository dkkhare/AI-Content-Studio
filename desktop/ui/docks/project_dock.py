from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDockWidget,
    QTreeWidget,
    QTreeWidgetItem,
)


class ProjectDock(QDockWidget):
    """
    Project explorer dock.

    Responsibilities:
    - Display current project structure
    - Refresh when project changes
    - Clear when project closes

    Project operations are handled by
    ProjectController.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            "Project",
            parent,
        )


        self.tree = QTreeWidget()

        self.tree.setHeaderLabel(
            "Current Project"
        )


        self.setWidget(
            self.tree
        )


        self.show_empty_state()


    # --------------------------------------------------
    # Project Display
    # --------------------------------------------------

    def load_project(
        self,
        project_path: str | Path,
    ):

        self.tree.clear()


        root = QTreeWidgetItem(
            [
                str(project_path)
            ]
        )


        self.tree.addTopLevelItem(
            root
        )


        self.tree.expandAll()



    def show_empty_state(
        self,
    ):

        self.tree.clear()


        item = QTreeWidgetItem(
            [
                "No project loaded"
            ]
        )


        self.tree.addTopLevelItem(
            item
        )



    def clear(
        self,
    ):

        self.show_empty_state()



    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh(
        self,
        project_path=None,
    ):

        if project_path:

            self.load_project(
                project_path
            )

        else:

            self.show_empty_state()