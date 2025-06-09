from io import BytesIO
from datetime import datetime

import cv2
import numpy as np
from app.modules.stream.infrastructure.yandex_object_storage.client.client import YandexObjectStorageClient


class YS3RecordPhotosSystem:
    """
    Система фотографий обработанных кадров в хранилище Yandex Object Storage.

    Attributes:
        _client: Клиент хранилища Yandex Object Storage.
    """

    def __init__(self, client: YandexObjectStorageClient):
        self._client = client

    def upload_frame(self, camera_id: str, vis_frame: np.ndarray, timestamp: datetime) -> str:
        """
        Кодирует vis_frame в JPEG и загружает в S3.
        Возвращает полный HTTP URL загруженного файла.
        """
        # 1) Эмкодим в JPEG
        success, buf = cv2.imencode('.jpg', vis_frame)
        if not success:
            raise RuntimeError("Failed to encode frame to JPEG")

        # 2) Формируем путь: <camera_id>/YYYY/MM/DD/filename.jpg
        prefix = f"{camera_id}/{timestamp.strftime('%Y/%m/%d')}"
        filename = timestamp.strftime('%Y%m%d_%H%M%S') + ".jpg"

        # 3) Загружаем
        bio = BytesIO(buf.tobytes())
        self._client.upload_file(
            file_path=prefix,
            file_name=filename,
            file_content=bio,
        )

        # 4) Собираем публичный URL
        return f"{self._client.get_storage_endpoint()}/{prefix}/{filename}"