from desktop.controllers.project_controller import ProjectController


class AppContext:

    def __init__(self):

        self.project = ProjectController()


app_context = AppContext()