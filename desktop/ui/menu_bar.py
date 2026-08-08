from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar


def build_menu(
    window,
):
    """
    Build application menu.

    Menu actions delegate work to MainWindow.
    No business logic should exist here.
    """

    menu_bar = QMenuBar(
        window
    )

    window.setMenuBar(
        menu_bar
    )


    # --------------------------------------------------
    # File Menu
    # --------------------------------------------------

    file_menu = menu_bar.addMenu(
        "File"
    )


    # New Project

    new_action = QAction(
        "New Project",
        window,
    )

    new_action.triggered.connect(
        window.new_project
    )


    file_menu.addAction(
        new_action
    )


    # Open Project

    open_action = QAction(
        "Open Project",
        window,
    )

    open_action.triggered.connect(
        window.open_project
    )


    file_menu.addAction(
        open_action
    )


    file_menu.addSeparator()


    # Save

    save_action = QAction(
        "Save",
        window,
    )

    save_action.triggered.connect(
        window.save_project
    )


    window.saveAction = (
        save_action
    )


    file_menu.addAction(
        save_action
    )
    # --------------------------------------------------
    # Save As
    # --------------------------------------------------

    save_as_action = QAction(
        "Save As",
        window,
    )

    save_as_action.triggered.connect(
        window.save_project_as
    )


    window.saveAsAction = (
        save_as_action
    )


    file_menu.addAction(
        save_as_action
    )


    file_menu.addSeparator()


    # --------------------------------------------------
    # Close Project
    # --------------------------------------------------

    close_action = QAction(
        "Close Project",
        window,
    )

    close_action.triggered.connect(
        window.close_project
    )


    window.closeProjectAction = (
        close_action
    )


    file_menu.addAction(
        close_action
    )


    file_menu.addSeparator()


    # --------------------------------------------------
    # Recent Projects
    # --------------------------------------------------

    recent_menu = file_menu.addMenu(
        "Recent Projects"
    )


    window.recentProjectsMenu = (
        recent_menu
    )


    file_menu.addSeparator()


    # --------------------------------------------------
    # Exit
    # --------------------------------------------------

    exit_action = QAction(
        "Exit",
        window,
    )

    exit_action.triggered.connect(
        window.close
    )


    file_menu.addAction(
        exit_action
    )


    # --------------------------------------------------
    # Edit Menu
    # --------------------------------------------------

    edit_menu = menu_bar.addMenu(
        "Edit"
    )


    refresh_action = QAction(
        "Refresh",
        window,
    )

    refresh_action.triggered.connect(
        window.refresh_project_ui
    )


    edit_menu.addAction(
        refresh_action
    )


    # --------------------------------------------------
    # View Menu
    # --------------------------------------------------

    view_menu = menu_bar.addMenu(
        "View"
    )


    dashboard_action = QAction(
        "Dashboard",
        window,
    )

    dashboard_action.triggered.connect(
        window.show_dashboard
    )


    view_menu.addAction(
        dashboard_action
    )


    workspace_action = QAction(
        "Workspace",
        window,
    )

    workspace_action.triggered.connect(
        window.show_workspace
    )


    view_menu.addAction(
        workspace_action
    )


    # --------------------------------------------------
    # AI Menu
    # --------------------------------------------------

    ai_menu = menu_bar.addMenu("AI")
    workbench_action = QAction("AI Workbench", window)
    workbench_action.triggered.connect(window.show_ai_workbench)
    ai_menu.addAction(workbench_action)
    ai_menu.addSeparator()
    window.aiWorkbenchAction = workbench_action

    ai_settings_action = QAction("Provider Settings", window)
    ai_settings_action.triggered.connect(window.open_ai_settings)
    ai_menu.addAction(ai_settings_action)
    window.aiSettingsAction = ai_settings_action

    # --------------------------------------------------
    # Help Menu
    # --------------------------------------------------

    help_menu = menu_bar.addMenu(
        "Help"
    )


    about_action = QAction(
        "About AI Content Studio",
        window,
    )


    help_menu.addAction(
        about_action
    )


    return menu_bar