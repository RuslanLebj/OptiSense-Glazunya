from typing import Final
from zoneinfo import ZoneInfo

import asyncio, time
from datetime import datetime, timedelta

from app.modules.stream.application.pipelines import QueueLengthPipeline
from app.modules.stream.application.schemas import Camera, Record, Indicators
from app.modules.stream.infrastructure.optisense_api.adapter import OptisenseAPIAdapter
from app.modules.stream.infrastructure.stream.adapter import StreamAdapter
from utils.logger import get_logger


class QueueLengthService:

    PERIOD: Final[float] = 1.0
    TIMEZONE = ZoneInfo("Asia/Yekaterinburg")

    def __init__(
        self,
        pipeline: QueueLengthPipeline,
        api_adapter: OptisenseAPIAdapter,
        camera: Camera,
    ):
        self._pipeline = pipeline
        self._api_adapter = api_adapter
        self._camera = camera
        self.logger = get_logger("QueueLengthPipeline")
        self._stream_adapter = StreamAdapter(self._camera.url_address)

    async def run(self) -> None:

        if self._camera.roi_polygons.polygons:
            self._pipeline.roi = self._camera.roi_polygons.as_list()[0]

        await self._wait_until_start()

        self._stream_adapter.start()

        self.logger.info(
            "Start processing camera %s (window: %s–%s)",
            self._camera.name,
            self._camera.start_time,
            self._camera.end_time,
        )

        try:
            self.logger.info("Start processing camera %s", self._camera.name)
            next_tick = time.perf_counter()

            while True:
                now_local = datetime.now(self.TIMEZONE).time()
                if self._camera.end_time and now_local >= self._camera.end_time:
                    self.logger.info(
                        "End time reached for camera %s (%s), stopping",
                        self._camera.name,
                        now_local,
                    )
                    break

                ok, frame = self._stream_adapter.read()
                if not ok:
                    next_tick = time.perf_counter()
                    await asyncio.sleep(self.PERIOD)
                    continue

                queue_length = self._pipeline.process(frame)
                record = Record(
                    camera=self._camera.id,
                    record_time=datetime.now(tz=self.TIMEZONE),
                    indicators_value=Indicators(queue_length=queue_length),
                )

                asyncio.create_task(self._api_adapter.create_record(record))
                self.logger.info("processing result: %s", record)

                next_tick += self.PERIOD
                sleep_time = next_tick - time.perf_counter()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    next_tick = time.perf_counter()

        except Exception as e:
            self.logger.exception(
                "Fatal error in service for camera %s", self._camera.name
            )
            raise
        finally:
            self._stream_adapter.stop()
            self.logger.info("Stop processing camera %s", self._camera.name)

    async def _wait_until_start(self) -> None:
        """
        Если сейчас раньше camera.start_time, ждёт до ближайшего начала.
        Если camera.start_time или camera.end_time не заданы, сразу возвращается.
        """
        now_dt = datetime.now(self.TIMEZONE)
        start = self._camera.start_time
        end = self._camera.end_time

        # Если start_time или end_time не заданы, сразу начинаем
        if start is None or end is None:
            return

        now_t = now_dt.time()
        # Если уже внутри окна [start, end) (учитываем «перевёрнутые» через полночь)
        if self._is_within_window(now_t, start, end):
            return

        # Вычисляем ближайший момент start
        today_start = now_dt.replace(
            hour=start.hour, minute=start.minute, second=start.second, microsecond=0
        )
        if now_dt < today_start:
            wait_delta = today_start - now_dt
        else:
            # дошли до времени past today; ждём до завтра
            tomorrow = (now_dt + timedelta(days=1)).date()
            next_start = datetime.combine(tomorrow, start, tzinfo=self.TIMEZONE)
            wait_delta = next_start - now_dt

        seconds_to_wait = max(wait_delta.total_seconds(), 0.0)
        self.logger.info(
            "Camera %s inactive (now=%s) — sleeping %.0f s until start_time %s",
            self._camera.name,
            now_t,
            seconds_to_wait,
            start,
        )
        await asyncio.sleep(seconds_to_wait)

    @staticmethod
    def _is_within_window(
        now: datetime.time, start: datetime.time, end: datetime.time
    ) -> bool:
        """
        Проверка нахождения внутри рабочего времени.
        """
        if start < end:
            return start <= now < end
        return now >= start or now < end
