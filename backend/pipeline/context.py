class PipelineContext:
    """
    Shared data passed between all stages.
    """

    def __init__(self, project):
        self.project = project

        self.ocr_text = ""

        self.cleaned_text = ""

        self.audio_file = ""

        self.avatar_video = ""

        self.subtitle_file = ""

        self.final_video = ""