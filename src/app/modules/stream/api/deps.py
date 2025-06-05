from functools import lru_cache
import numpy as np

from app.modules.stream.infrastructure.optisense_api.adapter import OptisenseAPIAdapter
from app.modules.stream.application.pipelines.queue_length_pipeline import QueueLengthPipeline
from app.config import settings

def get_optisense_api_adapter() -> OptisenseAPIAdapter:
    """
    Получить адаптер API OptiSense.
    """

    return OptisenseAPIAdapter(
        optisense_api_url=settings.OPTISENSE_API_URL,
        optisense_api_key=settings.OPTISENSE_API_KEY
    )


@lru_cache(maxsize=1)
def get_queue_length_pipeline(roi: list[np.ndarray] | None = None) -> QueueLengthPipeline:
    return QueueLengthPipeline(
        model_path=settings.MODEL_PATH,
        roi=roi,
    )