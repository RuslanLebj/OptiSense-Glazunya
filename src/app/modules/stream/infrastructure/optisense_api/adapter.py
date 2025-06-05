import aiohttp

from app.modules.stream.infrastructure.optisense_api.abstract import AbstractAPIAdapter
from app.modules.stream.application.schemas import Record, Camera


class OptisenseAPIAdapter(AbstractAPIAdapter):
    """
    Адаптер API Optisense.
    """

    def __init__(
        self,
        optisense_api_url: str,
        optisense_api_key: str,
    ):
        self._url = optisense_api_url
        self._headers = {"Authorization": f"API-KEY {optisense_api_key}"}

    async def create_record(self, record: Record) -> None:
        """
        Отправить записи по показателям.
        """
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.post(
                    f"{self._url}/records/",
                    json=record.model_dump(mode="json"),
            ) as resp:
                resp.raise_for_status()


    async def get_cameras(self) -> list[Camera]:
        """
        Получить список камер.
        """
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.get(f"{self._url}/cameras/") as resp:
                resp.raise_for_status()
                data = await resp.json()

        return [Camera(**camera) for camera in data]

