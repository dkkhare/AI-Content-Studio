from backend.pipeline.pipeline import ProcessingPipeline


class PipelineRunner:

    def __init__(self):

        self.pipeline = ProcessingPipeline()

    def add_stage(self, stage):

        self.pipeline.add_stage(stage)

    def run(self, context):

        self.pipeline.execute(context)