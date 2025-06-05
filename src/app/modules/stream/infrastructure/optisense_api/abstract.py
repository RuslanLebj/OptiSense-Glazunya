import abc

from app.modules.stream.application.schemas import Record, Camera


class AbstractAPIAdapter(metaclass=abc.ABCMeta):
    """
    Абстрактный адаптер API получения камер и отправки записей по показателям.
    """

    @abc.abstractmethod
    async def create_record(self, record: Record) -> None: ...

    @abc.abstractmethod
    async def get_cameras(self) -> list[Camera]: ...