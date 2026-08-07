from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar


def build_menu(window):
    """Build application menus and delegate actions to MainWindow."""

    menu_bar = QMenuBar(window)
    window.setMenuBar(menu_bar)

    # --------------------------------------------------
    # File Menu
    # --------------------------------------------------

    file_menu = menu_bar.addMenu("File")

    new_action = QAction("New Project", window)
    new_action.triggered.connect(window.new_project)
    file_menu.addAction(new_action)

    open_action = QAction("Open Project", window)
    open_action.triggered.connect(window.open_project)
    file_menu.addAction(open_action)

    file_menu.addSeparator()

    save_action = QAction("Save", window)
    save_action.triggered.connect(window.save_project)
    window.saveAction = save_action
    file_menu.addAction(save_action)

    save_as_action = QAction("Save As", window)
    save_as_action.triggered.connect(window.save_project_as)
    window.saveAsAction = save_as_action
    file_menu.addAction(save_as_action)

    file_menu.addSeparator()

    # --------------------------------------------------
    # Backup Management
    # --------------------------------------------------

    backup_menu = file_menu.addMenu("Backups")
    window.backupMenu = backup_menu

    create_backup_action = QAction("Create Backup", window)
    create_backup_action.triggered.connect(window.create_project_backup)
    window.createBackupAction = create_backup_action
    backup_menu.addAction(create_backup_action)

    restore_backup_action = QAction("Restore Backup", window)
    restore_backup_action.triggered.connect(window.restore_project_backup)
    window.restoreBackupAction = restore_backup_action
    backup_menu.addAction(restore_backup_action)

    delete_backup_action = QAction("Delete Backup", window)
    delete_backup_action.triggered.connect(window.delete_project_backup)
    window.deleteBackupAction = delete_backup_action
    backup_menu.addAction(delete_backup_action)

    backup_menu.addSeparator()

    cleanup_backup_action = QAction("Cleanup Backups", window)
    cleanup_backup_action.triggered.connect(window.cleanup_project_backups)
    window.cleanupBackupsAction = cleanup_backup_action
    backup_menu.addAction(cleanup_backup_action)

    file_menu.addSeparator()

    close_action = QAction("Close Project", window)
    close_action.triggered.connect(window.close_project)
    window.closeProjectAction = close_action
    file_menu.addAction(close_action)

    file_menu.addSeparator()

    recent_menu = file_menu.addMenu("Recent Projects")
    window.recentProjectsMenu = recent_menu

    file_menu.addSeparator()

    exit_action = QAction("Exit", window)
    exit_action.triggered.connect(window.close)
    file_menu.addAction(exit_action)

    # --------------------------------------------------
    # Edit Menu
    # --------------------------------------------------

    edit_menu = menu_bar.addMenu("Edit")

    refresh_action = QAction("Refresh Project", window)
    refresh_action.triggered.connect(window.refresh_project)
    window.refreshProjectAction = refresh_action
    edit_menu.addAction(refresh_action)

    # --------------------------------------------------
    # View Menu
    # --------------------------------------------------

    view_menu = menu_bar.addMenu("View")

    dashboard_action = QAction("Dashboard", window)
    dashboard_action.triggered.connect(window.show_dashboard)
    view_menu.addAction(dashboard_action)

    workspace_action = QAction("Workspace", window)
    workspace_action.triggered.connect(window.show_workspace)
    view_menu.addAction(workspace_action)

    # --------------------------------------------------
    # Help Menu
    # --------------------------------------------------

    help_menu = menu_bar.addMenu("Help")
    about_action = QAction("About AI Content Studio", window)
    help_menu.addAction(about_action)

    return menu_bar
