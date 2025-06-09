from app.api.common.errors.base import (
    BaseError,
    ErrorSchema,
)


class BaseBadGatewayError(BaseError):
    """
    Сервер, выступая в роли шлюза или прокси-сервера,
    получил недействительное ответное сообщение от вышестоящего сервера.
    """

    domain: str | None = None

    def __init__(self, msg: str | None = None, domain: str | None = None):
        self.domain = domain or self.domain
        self.msg = msg or self.msg
        self.type = "BadGateway"


class BadGatewayErrorSchema(ErrorSchema):
    domain: str | None


class BaseGatewayTimeoutError(BaseError):
    """
    Шлюз не отвечает.
    """

    domain: str | None = None

    def __init__(self, msg: str | None = None, domain: str | None = None):
        self.domain = domain or self.domain
        self.msg = msg or self.msg
        self.type = "GatewayTimeout"


class GatewayTimeoutErrorSchema(ErrorSchema):
    domain: str | None


class BaseConflictError(BaseError):
    """
    Ошибка конфликта с текущим состояние сервера.
    """


class BaseForbiddenError(BaseError):
    """
    Ошибка доступа.
    """


class BaseLockedError(BaseError):
    """
    Доступ к ресурсу заблокирован.
    """


class BaseNotFoundError(BaseError):
    """
    Ошибка отсутствующего ресурса.
    """


class BaseUnauthorizedError(BaseError):
    """
    Ошибка авторизации.
    """


class BaseUnprocessableEntityError(BaseError):
    """
    Сервер успешно принял запрос, однако имеется логическая ошибка из-за которой
    невозможно произвести операцию над ресурсом.
    """


class BaseValidationError(BaseError):
    """
    Синтаксическая ошибка запроса клиента.
    """

    loc: tuple[str | None] = (None,)

    def __init__(self, msg: str | None = None, loc: tuple | None = None):
        self.loc = loc or self.loc
        self.msg = msg or self.msg
        self.type = "ServerValidation"


class ValidationErrorSchema(ErrorSchema):
    location: tuple[str | int, ...]
