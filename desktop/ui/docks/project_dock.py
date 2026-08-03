from PySide6.QtWidgets import (
    QDockWidget,
    QTreeWidget,
    QTreeWidgetItem,
)


class ProjectDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Project", parent)

        tree = QTreeWidget()
        tree.setHeaderLabel("Current Project")

        root = QTreeWidgetItem(["No project loaded"])

        tree.addTopLevelItem(root)

        self.setWidget(tree)

        self.tree = tree