from PySide6.QtGui import QAction


def build_menu(window):

    menu = window.menuBar()

    # --------------------------------------------------
    # Menus
    # --------------------------------------------------

    file_menu = menu.addMenu("&File")

    project_menu = menu.addMenu("&Project")

    ai_menu = menu.addMenu("&AI")

    tools_menu = menu.addMenu("&Tools")

    help_menu = menu.addMenu("&Help")

    # --------------------------------------------------
    # File Actions
    # --------------------------------------------------

    new_project_action = QAction(

        "New Project",

        window,

    )

    open_project_action = QAction(

        "Open Project",

        window,

    )

    save_project_action = QAction(

        "Save Project",

        window,

    )

    save_as_action = QAction(

        "Save Project As...",

        window,

    )

    close_project_action = QAction(

        "Close Project",

        window,

    )

    exit_action = QAction(

        "Exit",

        window,

    )

    file_menu.addAction(

        new_project_action

    )

    file_menu.addAction(

        open_project_action

    )

    file_menu.addSeparator()

    file_menu.addAction(

        save_project_action

    )

    file_menu.addAction(

        save_as_action

    )

    file_menu.addSeparator()

    file_menu.addAction(

        close_project_action

    )

    file_menu.addSeparator()

    # --------------------------------------------------
    # Recent Projects
    # --------------------------------------------------

    recent_projects_menu = file_menu.addMenu(

        "Recent Projects"

    )

    file_menu.addSeparator()

    file_menu.addAction(

        exit_action

    )

    # --------------------------------------------------
    # Connections
    # --------------------------------------------------

    new_project_action.triggered.connect(

        window.new_project

    )

    open_project_action.triggered.connect(

        window.open_project

    )

    save_project_action.triggered.connect(

        window.save_project

    )

    save_as_action.triggered.connect(

        window.save_project_as

    )

    close_project_action.triggered.connect(

        window.close_project

    )

    exit_action.triggered.connect(

        window.close

    )

    # --------------------------------------------------
    # Store References
    # --------------------------------------------------

    window.file_menu = file_menu

    window.recent_projects_menu = recent_projects_menu

    window.action_new_project = new_project_action

    window.action_open_project = open_project_action

    window.action_save_project = save_project_action

    window.action_save_project_as = save_as_action

    window.action_close_project = close_project_action

    window.action_exit = exit_action