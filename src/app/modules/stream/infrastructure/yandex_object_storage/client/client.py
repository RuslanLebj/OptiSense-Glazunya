from http import HTTPStatus
from io import BytesIO
from urllib.parse import urljoin

import boto3

from .exceptions import (
    ObjectDeleteError,
    EmptyDirectoryDeleteError,
)


class YandexObjectStorageClient:
    """
    Клиент сервиса Yandex Object Storage.

    Args:
        access_key_id: Ключ доступа к ресурсу.
        secret_key: Секретный ключ.
        endpoint_url: Полный URL-адрес ресурса.
        bucket_name: Название хранилища.
        region_name: Название региона, связанного с клиентом.

    Attributes:
        _endpoint (str): Полный URL-адрес ресурса.
        _bucket_name (str): Название хранилища.
        _bucket (boto3.resources.factory.s3.Bucket): Хранилище объектов.
    """

    _SERVICE_NAME = "s3"
    _PUBLIC_READ_ACL = "public-read"

    def __init__(
        self,
        access_key_id: str,
        secret_key: str,
        bucket_name: str,
        region_name: str = None,
        endpoint_url: str = None,
    ):
        _service = boto3.resource(
            self._SERVICE_NAME,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name=region_name,
        )

        self._endpoint = endpoint_url
        self._bucket_name = bucket_name
        self._bucket = _service.Bucket(bucket_name)

    def upload_file(
        self,
        file_path: str,
        file_name: str,
        file_content: BytesIO,
    ):
        """
        Загрузить файл в хранилище.

        Args:
            file_path: Путь к файлу в хранилище.
            file_name: Название файла.
            file_content: Тело загружаемого файла.
        """

        bucket_object = self._bucket.Object(key=f"{file_path}/{file_name}")
        file_content.seek(0)
        bucket_object.put(
            Body=file_content,
            ACL=self._PUBLIC_READ_ACL,
        )

    def delete_object(self, path: str):
        """
        Удалить папку со всем содержимым.

        Args:
            path: Путь к папке в хранилище.

        Raises:
            EmptyDirectoryDeleteError: Отсутствует удаляемая директория.
            ObjectDeleteError: Ошибка удаления объекта из хранилища.
        """
        delete_result = self._bucket.objects.filter(Prefix=f"{path}").delete()

        if not delete_result:
            raise EmptyDirectoryDeleteError("Отсутствует удаляемая директория.")

        delete_status = self._get_response_status_code(delete_result)
        if delete_status != HTTPStatus.OK:
            raise ObjectDeleteError(f"Не известный статус удаления: {delete_status}.")

    @staticmethod
    def _get_response_status_code(response: dict | list) -> int | None:
        """
        Извлечь статус из ответа.

        Args:
            response: ответ сервиса Yandex Object Storage.
        """
        if isinstance(response, list):
            response = response[0]

        return response.get("ResponseMetadata", {}).get("HTTPStatusCode")

    def get_storage_endpoint(self) -> str:
        """
        Получить точку входа хранилища.
        """
        return urljoin(self._endpoint, self._bucket_name)
