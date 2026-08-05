from PySide6.QtGui import QAction


def build_toolbar(window):

    toolbar = window.addToolBar("Main")

    # ------------------------------------------
    # Project
    # ------------------------------------------

    new_action = QAction(

        "New",

        window,

    )

    open_action = QAction(

        "Open",

        window,

    )

    save_action = QAction(

        "Save",

        window,

    )

    toolbar.addAction(

        new_action

    )

    toolbar.addAction(

        open_action

    )

    toolbar.addAction(

        save_action

    )

    new_action.triggered.connect(

        window.new_project

    )

    open_action.triggered.connect(

        window.open_project

    )

    save_action.triggered.connect(

        window.save_project

    )

    window.toolbar = toolbar

    window.toolbar_new = new_action

    window.toolbar_open = open_action

    window.toolbar_save = save_action