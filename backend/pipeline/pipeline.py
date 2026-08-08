from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .control import PipelineControl
from .exceptions import PipelineCancelled, StageError
from .progress import PipelineProgress
from .state import PipelineState, PipelineStateStore


class ProcessingPipeline:
    """Persisted, resumable sequential processing pipeline."""

    def __init__(self, stages=None):
        self.stages = []
        for stage in stages or []:
            self.add_stage(stage)

    def add_stage(self, stage):
        stage_id = getattr(stage, "stage_id", "")
        if not stage_id:
            raise ValueError("Pipeline stage requires a non-empty stage_id.")
        if any(existing.stage_id == stage_id for existing in self.stages):
            raise ValueError(f"Duplicate pipeline stage_id: {stage_id}")
        self.stages.append(stage)
        return stage

    def clear(self) -> None:
        self.stages.clear()

    def execute(
        self,
        context,
        *,
        control: PipelineControl | None = None,
        progress_callback: Callable[[PipelineProgress], None] | None = None,
        resume: bool = True,
    ) -> PipelineState:
        control = control or PipelineControl()
        store = PipelineStateStore(context.project_root)
        state = store.load() if resume else PipelineState()

        if not resume or state.status == "completed":
            state = PipelineState()
        elif state.data:
            # Resume must work after a full application/process restart, not only
            # when the original in-memory PipelineContext is reused. Explicit
            # values supplied by the new invocation win over checkpoint values.
            restored = dict(state.data)
            restored.update(context.data)
            context.data.clear()
            context.data.update(restored)

        completed = set(state.completed_stage_ids)
        total_weight = sum(max(0.0001, float(stage.weight)) for stage in self.stages) or 1.0
        finished_weight = sum(
            max(0.0001, float(stage.weight))
            for stage in self.stages
            if stage.stage_id in completed
        )

        state.status = "running"
        state.error_message = ""
        state.finished_at = ""
        if not state.started_at:
            state.started_at = datetime.now(timezone.utc).isoformat()
        store.save(state)

        try:
            for index, stage in enumerate(self.stages):
                if stage.stage_id in completed:
                    continue

                control.checkpoint()
                state.current_stage_index = index
                state.current_stage_id = stage.stage_id
                state.record_attempt(stage.stage_id)
                state.data = dict(context.data)
                store.save(state)

                stage_weight = max(0.0001, float(stage.weight))

                def report(stage_percent: int, message: str = "") -> None:
                    control.checkpoint()
                    local = max(0, min(100, int(stage_percent)))
                    overall = int(
                        ((finished_weight + stage_weight * (local / 100.0)) / total_weight)
                        * 100
                    )
                    if progress_callback:
                        progress_callback(
                            PipelineProgress(
                                stage_id=stage.stage_id,
                                current_stage=stage.name,
                                stage_index=index + 1,
                                total_stages=len(self.stages),
                                stage_percent=local,
                                percent=overall,
                                message=message,
                                status="running",
                            )
                        )

                report(0, f"Starting {stage.name}")
                try:
                    result = stage.execute(context, report)
                except PipelineCancelled:
                    raise
                except Exception as exc:
                    state.record_failure(
                        stage_id=stage.stage_id,
                        stage_name=stage.name,
                        error=exc,
                    )
                    state.error_message = f"{stage.name} failed: {exc}"
                    state.data = dict(context.data)
                    store.save(state)
                    raise StageError(state.error_message) from exc

                if isinstance(result, dict):
                    context.update(result)

                completed.add(stage.stage_id)
                state.completed_stage_ids = [
                    item.stage_id for item in self.stages if item.stage_id in completed
                ]
                state.data = dict(context.data)
                finished_weight += stage_weight
                store.save(state)
                report(100, f"Completed {stage.name}")

            state.status = "completed"
            state.current_stage_id = ""
            state.current_stage_index = len(self.stages)
            state.data = dict(context.data)
            state.finished_at = datetime.now(timezone.utc).isoformat()
            store.save(state)

            if progress_callback:
                progress_callback(
                    PipelineProgress(
                        stage_index=len(self.stages),
                        total_stages=len(self.stages),
                        stage_percent=100,
                        percent=100,
                        message="Pipeline completed.",
                        status="completed",
                    )
                )
            return state

        except PipelineCancelled as exc:
            state.status = "cancelled"
            state.error_message = str(exc)
            state.data = dict(context.data)
            store.save(state)
            if progress_callback:
                progress_callback(PipelineProgress(percent=self._overall_percent(state), message=str(exc), status="cancelled"))
            return state

        except Exception as exc:
            state.status = "failed"
            if not state.error_message:
                state.error_message = str(exc)
            state.data = dict(context.data)
            store.save(state)
            if progress_callback:
                progress_callback(PipelineProgress(percent=self._overall_percent(state), message=state.error_message, status="failed"))
            raise

    def _overall_percent(self, state: PipelineState) -> int:
        if not self.stages:
            return 100
        completed = set(state.completed_stage_ids)
        total = sum(max(0.0001, float(stage.weight)) for stage in self.stages)
        done = sum(
            max(0.0001, float(stage.weight))
            for stage in self.stages
            if stage.stage_id in completed
        )
        return int((done / total) * 100) if total else 0
