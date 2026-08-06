from __future__ import annotations

from PySide6.QtGui import QAction


def build_toolbar(
    window,
):
    """
    Build the main application toolbar.

    Toolbar only connects UI actions.
    Business logic remains inside MainWindow
    and ProjectController.
    """

    toolbar = window.addToolBar(
        "Main"
    )


    # --------------------------------------------------
    # Project Actions
    # --------------------------------------------------

    new_action = QAction(
        "New",
        window,
    )

    new_action.triggered.connect(
        window.new_project
    )


    open_action = QAction(
        "Open",
        window,
    )

    open_action.triggered.connect(
        window.open_project
    )


    save_action = QAction(
        "Save",
        window,
    )

    save_action.triggered.connect(
        window.save_project
    )


    save_as_action = QAction(
        "Save As",
        window,
    )

    save_as_action.triggered.connect(
        window.save_project_as
    )


    close_action = QAction(
        "Close",
        window,
    )

    close_action.triggered.connect(
        window.close_project
    )


    # --------------------------------------------------
    # Add Actions
    # --------------------------------------------------

    toolbar.addAction(
        new_action
    )

    toolbar.addAction(
        open_action
    )

    toolbar.addSeparator()

    toolbar.addAction(
        save_action
    )

    toolbar.addAction(
        save_as_action
    )

    toolbar.addSeparator()

    toolbar.addAction(
        close_action
    )


    # --------------------------------------------------
    # Store References
    # --------------------------------------------------

    window.toolbar = toolbar

    window.toolbar_new = new_action

    window.toolbar_open = open_action

    window.toolbar_save = save_action

    window.toolbar_save_as = save_as_action

    window.toolbar_close = close_action


    return toolbar