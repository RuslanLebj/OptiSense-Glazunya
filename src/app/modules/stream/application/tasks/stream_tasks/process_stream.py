from app.modules.stream.infrastructure.broker import stream_broker
from app.modules.stream.application.schemas import Camera
from app.config import settings
from app.modules.stream.api.deps import (
    get_optisense_api_adapter,
    get_queue_length_pipeline,
    get_storage_photos_system
)
from app.modules.stream.application.services import QueueLengthService
from utils.logger import get_logger

tasks_logger = get_logger("tasks")


@stream_broker.task(
    schedule=[{"cron": "0 0 * * *"}],
    queue_name=settings.QUEUE_NAME,
    task_name="start_processing_stream",
)
async def start_processing_stream():
    api_adapter = get_optisense_api_adapter()
    cameras = await api_adapter.get_cameras()
    tasks_logger.info("Processing %d cameras", len(cameras))
    for camera in cameras:
        await processing_stream_task.kiq(camera=camera)


@stream_broker.task(
    queue_name=settings.QUEUE_NAME,
    task_name="processing_stream_task",
)
async def processing_stream_task(
    camera: Camera,
):
    api_adapter = get_optisense_api_adapter()
    pipeline = get_queue_length_pipeline()
    photo_storage = get_storage_photos_system()
    service = QueueLengthService(pipeline, api_adapter, photo_storage, camera)
    await service.run()