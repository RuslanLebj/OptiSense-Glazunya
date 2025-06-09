from app.api.common.errors.errors import BaseNotFoundError


class BaseYandexObjectStorageClientError(Exception):
    """
    Базовое исключение клиента Yandex Object Storage.
    """


class ObjectDeleteError(BaseYandexObjectStorageClientError):
    """
    Ошибка удаления объекта из хранилища.
    """


class EmptyDirectoryDeleteError(ObjectDeleteError, BaseNotFoundError):
    """
    Отсутствует удаляемая директория.
    """
