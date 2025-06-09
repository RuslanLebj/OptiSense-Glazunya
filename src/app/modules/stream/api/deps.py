from functools import lru_cache
import numpy as np

from app.modules.stream.infrastructure.optisense_api.adapter import OptisenseAPIAdapter
from app.modules.stream.application.pipelines.queue_length_pipeline import QueueLengthPipeline
from app.config import settings
from app.modules.stream.infrastructure.yandex_object_storage.client import YandexObjectStorageClient
from app.modules.stream.infrastructure.yandex_object_storage.systems import YS3RecordPhotosSystem


def get_optisense_api_adapter() -> OptisenseAPIAdapter:
    """
    Получить адаптер API OptiSense.
    """

    return OptisenseAPIAdapter(
        optisense_api_url=settings.OPTISENSE_API_URL,
        optisense_api_key=settings.OPTISENSE_API_KEY
    )

def _get_yandex_storage_adapter() -> YandexObjectStorageClient:
    """
    Получить адаптер облачного хранилища Яндекса.
    """

    return YandexObjectStorageClient(
        access_key_id=settings.STORAGE_ACCESS_KEY_ID,
        secret_key=settings.STORAGE_SECRET_ACCESS_KEY,
        bucket_name=settings.STORAGE_BUCKET_NAME,
        region_name=settings.STORAGE_REGION_NAME,
        endpoint_url=settings.STORAGE_ENDPOINT_URL,
    )


def get_storage_photos_system() -> YS3RecordPhotosSystem:
    """
    Получить систему хранения фотографий в облаке.
    """

    return YS3RecordPhotosSystem(client=_get_yandex_storage_adapter())


@lru_cache(maxsize=1)
def get_queue_length_pipeline(roi: list[np.ndarray] | None = None) -> QueueLengthPipeline:
    return QueueLengthPipeline(
        model_path=settings.MODEL_PATH,
        roi=roi,
    )