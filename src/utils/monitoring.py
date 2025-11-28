from typing import Any, Optional
from contextlib import contextmanager
import time

from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WandbMonitor:
    """Weights & Biases monitoring integration."""

    def __init__(self):
        self._run = None
        self._enabled = settings.wandb_enabled and bool(settings.wandb_api_key)

    def init(self, run_name: Optional[str] = None, config: Optional[dict] = None) -> None:
        """Initialize a W&B run."""
        if not self._enabled:
            logger.debug("W&B monitoring disabled")
            return

        try:
            import wandb

            self._run = wandb.init(
                project=settings.wandb_project,
                name=run_name,
                config=config or {},
                reinit=True,
            )
            logger.info(f"W&B run initialized: {self._run.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize W&B: {e}")
            self._enabled = False

    def log(self, metrics: dict[str, Any], step: Optional[int] = None) -> None:
        """Log metrics to W&B."""
        if not self._enabled or not self._run:
            return

        try:
            import wandb

            wandb.log(metrics, step=step)
        except Exception as e:
            logger.warning(f"Failed to log to W&B: {e}")

    def log_call_metrics(
        self,
        call_sid: str,
        duration: float,
        transcription_latency: float,
        llm_latency: float,
        tts_latency: float,
    ) -> None:
        """Log call-specific metrics."""
        self.log(
            {
                "call/duration": duration,
                "latency/transcription": transcription_latency,
                "latency/llm": llm_latency,
                "latency/tts": tts_latency,
                "latency/total": transcription_latency + llm_latency + tts_latency,
            }
        )

    @contextmanager
    def timer(self, metric_name: str):
        """Context manager to time operations."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.log({metric_name: elapsed})

    def finish(self) -> None:
        """Finish the current W&B run."""
        if self._run:
            try:
                import wandb

                wandb.finish()
                logger.info("W&B run finished")
            except Exception as e:
                logger.warning(f"Failed to finish W&B run: {e}")
            finally:
                self._run = None


monitor = WandbMonitor()

